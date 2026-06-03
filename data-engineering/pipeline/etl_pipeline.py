"""ETL Pipeline for DataPulse analytics (DB → DB version)."""

import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_models import (
    AnalyticsBase,
    DimDataset,
    DimRule,
    DimDate,
    FactQualityCheck,
    FactTrendMetric,
)

load_dotenv()


class ETLPipeline:
    def __init__(self, target_url=None):

        # ─────────────────────────────────────────────
        # SOURCE DB (origin system)
        # ─────────────────────────────────────────────
        self.source_url = os.getenv("SOURCE_DB_URL")
        if not self.source_url:
            raise ValueError("SOURCE_DB_URL is not set in .env")

        self.source_engine = create_engine(self.source_url)

        # ─────────────────────────────────────────────
        # TARGET DB (analytics warehouse)
        # ─────────────────────────────────────────────
        self.target_url = target_url or os.getenv("TARGET_DB_URL")
        if not self.target_url:
            raise ValueError("TARGET_DB_URL is not set in .env")

        self.target_engine = create_engine(self.target_url)

        # raw data
        self.raw_datasets = None
        self.raw_rules = None
        self.raw_reports = None
        self.raw_findings = None
        self.raw_trends = None

        self.transformed_data = None

        # create analytics schema if not exists
        AnalyticsBase.metadata.create_all(self.target_engine)

    # ─────────────────────────────────────────────
    # EXTRACT (DIRECT DB READ)
    # ─────────────────────────────────────────────
    def extract(self):
        """Extract data from SOURCE PostgreSQL DB."""

        self.raw_datasets = pd.read_sql("SELECT * FROM datasets", self.source_engine)

        self.raw_rules = pd.read_sql(
            "SELECT * FROM validation_rules",
            self.source_engine
        )

        self.raw_reports = pd.read_sql(
            "SELECT * FROM quality_reports",
            self.source_engine
        )

        self.raw_findings = pd.read_sql(
            "SELECT * FROM rule_findings",
            self.source_engine
        )

        self.raw_trends = pd.read_sql(
            "SELECT * FROM trend_metrics",
            self.source_engine
        )

        print("Extract completed:")
        print(f"- datasets: {len(self.raw_datasets)}")
        print(f"- rules: {len(self.raw_rules)}")
        print(f"- reports: {len(self.raw_reports)}")
        print(f"- findings: {len(self.raw_findings)}")
        print(f"- trends: {len(self.raw_trends)}")

        return (
            self.raw_findings,
            self.raw_rules,
            self.raw_reports,
            self.raw_datasets,
            self.raw_trends,
        )

    # ─────────────────────────────────────────────
    # TRANSFORM
    # ─────────────────────────────────────────────
    def transform(self):

        df = (
            self.raw_findings
            .merge(self.raw_rules, left_on="rule_id", right_on="id", suffixes=("", "_rule"))
            .merge(self.raw_reports, left_on="report_id", right_on="id", suffixes=("", "_report"))
            .merge(self.raw_datasets, left_on="dataset_id", right_on="id", suffixes=("", "_dataset"))
        )

        # ── derived metrics (BEFORE any renames) ─────
        df["passed"] = df["failure_percentage"] == 0
        df["score"] = (1 - df["failure_percentage"] / 100).clip(0, 1)

        def extract_severity(cfg):
            if isinstance(cfg, dict):
                return cfg.get("severity", "medium")
            return "medium"

        df["severity"] = df["rule_config"].apply(extract_severity)
        df["checked_at"] = pd.to_datetime(df["generated_at"], utc=True)

        # ── DIM DATASETS ─────────────────────────────
        dim_datasets = (
            df[["dataset_id", "file_name", "file_type", "row_count", "created_at_dataset"]]
            .drop_duplicates(subset="dataset_id")
            .rename(columns={
                "dataset_id": "source_id",
                "file_name": "name",
                "created_at_dataset": "uploaded_at"
            })
        )

        # ── DIM RULES ────────────────────────────────
        dim_rules = (
            df[["rule_id", "column_name", "rule_type", "severity"]]
            .drop_duplicates(subset="rule_id")
            .rename(columns={
                "rule_id": "source_id",
                "column_name": "field_name",
            })
        )
        dim_rules["name"] = dim_rules["field_name"]

        # ── DIM DATE ──────────────────────────────────
        dates = df["checked_at"].dt.date.unique()

        dim_date = pd.DataFrame([
            {
                "date_key": int(d.strftime("%Y%m%d")),
                "full_date": d,
                "day_of_week": datetime.combine(d, datetime.min.time()).weekday(),
                "month": d.month,
                "year": d.year,
            }
            for d in dates
        ])

        # ── FACT QUALITY CHECKS ───────────────────────
        fact_checks = df[[
            "dataset_id", "rule_id", "rule_type",
            "passed", "rows_failed", "rows_checked",
            "score", "severity", "checked_at"
        ]].rename(columns={
            "rows_failed": "failed_rows",
            "rows_checked": "total_rows"
        })

        # ── FACT TREND ────────────────────────────────
        fact_trends = self.raw_trends.copy()
        fact_trends["snapshot_date"] = pd.to_datetime(
            fact_trends["snapshot_date"]
        ).dt.date

        fact_trends = fact_trends.rename(columns={"id": "source_id"})

        self.transformed_data = {
            "dim_datasets": dim_datasets,
            "dim_rules": dim_rules,
            "dim_date": dim_date,
            "fact_checks": fact_checks,
            "fact_trends": fact_trends,
        }

        print("Transform completed")
        return self.transformed_data

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────
    def load(self):

        session = sessionmaker(bind=self.target_engine)()

        try:
            # clear facts only (dims use upsert)
            session.execute(text("TRUNCATE fact_quality_checks RESTART IDENTITY"))
            session.execute(text("TRUNCATE fact_trend_metrics RESTART IDENTITY"))

            # ── DIM DATASETS
            dataset_map = {}
            for _, r in self.transformed_data["dim_datasets"].iterrows():
                obj = session.query(DimDataset).filter_by(source_id=r["source_id"]).first()
                if not obj:
                    obj = DimDataset(
                        source_id=r["source_id"],
                        name=r["name"],
                        file_type=r["file_type"],
                        row_count=r["row_count"],
                        uploaded_at=r["uploaded_at"],
                    )
                    session.add(obj)
                    session.flush()
                dataset_map[r["source_id"]] = obj.id

            # ── DIM RULES
            rule_map = {}
            for _, r in self.transformed_data["dim_rules"].iterrows():
                obj = session.query(DimRule).filter_by(source_id=r["source_id"]).first()
                if not obj:
                    obj = DimRule(
                        source_id=r["source_id"],
                        name=r["name"],
                        field_name=r["field_name"],
                        rule_type=r["rule_type"],
                        severity=r["severity"],
                    )
                    session.add(obj)
                    session.flush()
                rule_map[r["source_id"]] = obj.id

            # ── DIM DATE
            for _, r in self.transformed_data["dim_date"].iterrows():
                session.merge(DimDate(**r.to_dict()))

            # ── FACT QUALITY
            for _, r in self.transformed_data["fact_checks"].iterrows():
                d_id = dataset_map.get(r["dataset_id"])
                r_id = rule_map.get(r["rule_id"])

                if not d_id or not r_id:
                    continue

                session.add(FactQualityCheck(
                    dataset_id=d_id,
                    rule_id=r_id,
                    rule_type=r["rule_type"],
                    passed=bool(r["passed"]),
                    failed_rows=r["failed_rows"],
                    total_rows=r["total_rows"],
                    score=float(r["score"]),
                    severity=r["severity"],
                    checked_at=r["checked_at"],
                ))

            # ── FACT TREND
            for _, r in self.transformed_data["fact_trends"].iterrows():
                d_id = dataset_map.get(r["dataset_id"])
                if not d_id:
                    continue

                session.add(FactTrendMetric(
                    dataset_id=d_id,
                    source_id=r["source_id"],
                    snapshot_date=r["snapshot_date"],
                    aggregated_score=int(r["aggregated_score"]),
                ))

            session.commit()
            print("Load completed successfully")

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ─────────────────────────────────────────────
    # RUN
    # ─────────────────────────────────────────────
    def run(self):
        print(f"ETL started at {datetime.now()}")
        self.extract()
        self.transform()
        self.load()
        print(f"ETL finished at {datetime.now()}")


if __name__ == "__main__":
    ETLPipeline().run()