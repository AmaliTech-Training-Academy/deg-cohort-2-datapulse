"""ETL Pipeline for DataPulse analytics."""

import os
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

from models import AnalyticsBase, DimDataset, DimRule, DimDate, FactQualityCheck

load_dotenv()


class ETLPipeline:
    def __init__(self, source_url=None, target_url=None):
        self.source_url = source_url or os.getenv("SOURCE_DB_URL",
            "postgresql://datapulse:datapulse@localhost:5432/datapulse")
        self.target_url = target_url or os.getenv("TARGET_DB_URL",
            self.source_url)
        self.source_engine = create_engine(self.source_url)
        self.target_engine = create_engine(self.target_url)
        self.raw_data = None
        self.transformed_data = None

        # Ensure analytics tables exist in target DB
        AnalyticsBase.metadata.create_all(self.target_engine)

    # ------------------------------------------------------------------
    # EXTRACT
    # ------------------------------------------------------------------

    def extract(self):
        """Extract check results from app DB using the source schema."""
        query = """
            SELECT
                rf.id,
                rf.report_id,
                rf.rule_id,
                rf.rows_checked,
                rf.rows_failed,
                rf.failure_percentage,
                rf.error_details,
                vr.rule_type,
                vr.column_name    AS field_name,
                vr.rule_config,
                vr.dataset_id     AS vr_dataset_id,
                d.id              AS dataset_uuid,
                d.file_name       AS dataset_name,
                d.file_type,
                d.row_count,
                d.created_at      AS dataset_created_at,
                qr.generated_at   AS checked_at
            FROM rule_findings rf
            JOIN validation_rules vr  ON rf.rule_id    = vr.id
            JOIN quality_reports  qr  ON rf.report_id  = qr.id
            JOIN datasets         d   ON qr.dataset_id = d.id
        """
        self.raw_data = pd.read_sql(query, self.source_engine)
        print(f"Extracted {len(self.raw_data)} records")
        return self.raw_data

    # ------------------------------------------------------------------
    # TRANSFORM
    # ------------------------------------------------------------------

    def transform(self):
        """Transform extracted data into analytics-ready structures."""
        if self.raw_data is None:
            print("No data to transform. Run extract() first.")
            return None

        df = self.raw_data.copy()

        # --- Derive pass/fail and quality score ----------------------
        df["passed"] = df["failure_percentage"] == 0
        df["score"]  = (1 - df["failure_percentage"] / 100).clip(0, 1)

        # --- Extract severity from rule_config JSON ------------------
        # rule_config is a JSON column; severity key may or may not exist
        def extract_severity(cfg):
            if isinstance(cfg, dict):
                return cfg.get("severity", "medium")
            return "medium"

        df["severity"] = df["rule_config"].apply(extract_severity)

        # --- Build dim_datasets (unique datasets) --------------------
        dim_datasets = (
            df[["dataset_uuid", "dataset_name", "file_type", "row_count", "dataset_created_at"]]
            .drop_duplicates(subset="dataset_uuid")
            .rename(columns={
                "dataset_uuid":     "source_id",
                "dataset_name":     "name",
                "dataset_created_at": "uploaded_at",
            })
        )

        # --- Build dim_rules (unique rules) --------------------------
        dim_rules = (
            df[["rule_id", "field_name", "rule_type", "severity"]]
            .drop_duplicates(subset="rule_id")
            .rename(columns={"rule_id": "source_id"})
        )
        dim_rules["name"] = dim_rules["field_name"]  # human-readable name

        # --- Build dim_date (all distinct dates in checked_at) -------
        distinct_dates = pd.to_datetime(df["checked_at"]).dt.date.unique()
        dim_date_rows = []
        for d_val in distinct_dates:
            dt = datetime.combine(d_val, datetime.min.time())
            dim_date_rows.append({
                "date_key":    int(dt.strftime("%Y%m%d")),
                "full_date":   d_val,
                "day_of_week": dt.weekday(),   # 0=Monday … 6=Sunday
                "month":       dt.month,
                "year":        dt.year,
            })
        dim_date = pd.DataFrame(dim_date_rows)

        # --- Build fact_quality_checks -------------------------------
        fact = df[[
            "dataset_uuid", "rule_id", "rule_type",
            "passed", "rows_failed", "rows_checked",
            "score", "severity", "checked_at",
        ]].rename(columns={
            "rows_failed":   "failed_rows",
            "rows_checked":  "total_rows",
        })

        self.transformed_data = {
            "dim_datasets": dim_datasets,
            "dim_rules":    dim_rules,
            "dim_date":     dim_date,
            "fact":         fact,
        }

        print(
            f"Transform complete — "
            f"{len(dim_datasets)} datasets, "
            f"{len(dim_rules)} rules, "
            f"{len(dim_date)} dates, "
            f"{len(fact)} fact rows"
        )
        return self.transformed_data

    # ------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------

    def load(self):
        """Load transformed data into analytics tables."""
        if self.transformed_data is None:
            print("No data to load. Run transform() first.")
            return

        Session = sessionmaker(bind=self.target_engine)
        session = Session()

        try:
            # ---- 1. Upsert dim_datasets -----------------------------
            dataset_source_id_to_pk = {}
            for _, row in self.transformed_data["dim_datasets"].iterrows():
                existing = (
                    session.query(DimDataset)
                    .filter_by(source_id=row["source_id"])
                    .first()
                )
                if existing:
                    existing.name       = row["name"]
                    existing.file_type  = row["file_type"]
                    existing.row_count  = row["row_count"]
                    existing.uploaded_at = row["uploaded_at"]
                    obj = existing
                else:
                    obj = DimDataset(
                        source_id   = row["source_id"],
                        name        = row["name"],
                        file_type   = row["file_type"],
                        row_count   = row["row_count"],
                        uploaded_at = row["uploaded_at"],
                    )
                    session.add(obj)
                session.flush()
                dataset_source_id_to_pk[str(row["source_id"])] = obj.id

            # ---- 2. Upsert dim_rules --------------------------------
            rule_source_id_to_pk = {}
            for _, row in self.transformed_data["dim_rules"].iterrows():
                existing = (
                    session.query(DimRule)
                    .filter_by(source_id=row["source_id"])
                    .first()
                )
                if existing:
                    existing.name       = row["name"]
                    existing.field_name = row["field_name"]
                    existing.rule_type  = row["rule_type"]
                    existing.severity   = row["severity"]
                    obj = existing
                else:
                    obj = DimRule(
                        source_id  = row["source_id"],
                        name       = row["name"],
                        field_name = row["field_name"],
                        rule_type  = row["rule_type"],
                        severity   = row["severity"],
                    )
                    session.add(obj)
                session.flush()
                rule_source_id_to_pk[str(row["source_id"])] = obj.id

            # ---- 3. Upsert dim_date ---------------------------------
            for _, row in self.transformed_data["dim_date"].iterrows():
                existing = session.get(DimDate, int(row["date_key"]))
                if not existing:
                    session.add(DimDate(
                        date_key    = int(row["date_key"]),
                        full_date   = row["full_date"],
                        day_of_week = int(row["day_of_week"]),
                        month       = int(row["month"]),
                        year        = int(row["year"]),
                    ))

            # ---- 4. Insert fact_quality_checks ----------------------
            for _, row in self.transformed_data["fact"].iterrows():
                dataset_pk = dataset_source_id_to_pk.get(str(row["dataset_uuid"]))
                rule_pk    = rule_source_id_to_pk.get(str(row["rule_id"]))

                if dataset_pk is None or rule_pk is None:
                    print(f"Skipping fact row — missing FK for dataset={row['dataset_uuid']} rule={row['rule_id']}")
                    continue

                session.add(FactQualityCheck(
                    dataset_id = dataset_pk,
                    rule_id    = rule_pk,
                    rule_type  = row["rule_type"],
                    passed     = bool(row["passed"]),
                    failed_rows = int(row["failed_rows"]),
                    total_rows  = int(row["total_rows"]),
                    score      = float(row["score"]),
                    severity   = row["severity"],
                    checked_at = row["checked_at"],
                ))

            session.commit()
            print("Load complete — all records committed.")

        except Exception as e:
            session.rollback()
            print(f"Load failed, rolled back: {e}")
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # RUN
    # ------------------------------------------------------------------

    def run(self):
        """Run the full ETL pipeline."""
        print(f"ETL started at {datetime.now()}")
        self.extract()
        self.transform()
        self.load()
        print(f"ETL completed at {datetime.now()}")


if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()