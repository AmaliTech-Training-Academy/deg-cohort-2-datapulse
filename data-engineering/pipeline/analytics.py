# data-engineering/pipeline/analytics_db.py
#
# DE2 (Odile) owns this file.
# Reads from the real analytics DB populated by DE1's ETL pipeline.
# Replaces CSV-based analytics once ETL is running.
#
# Usage:
#   from pipeline.analytics_db import (
#       score_summary, quality_trend, rule_failure_rates,
#       worst_datasets, monthly_summary
#   )

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# DB connection 

def get_engine():
    """Connect to the analytics DB."""
    url = os.getenv("TARGET_DB_URL")
    if not url:
        raise ValueError("TARGET_DB_URL is not set in .env")
    return create_engine(url)


# Query 1: Score summary 

def score_summary() -> pd.DataFrame:
    """
    Returns quality score summary per dataset.
    Reads from dim_datasets + fact_quality_checks.
    """
    query = """
        SELECT
            d.name                              AS dataset,
            SUM(f.total_rows)                   AS total_rows,
            SUM(f.total_rows - f.failed_rows)   AS passed_rows,
            SUM(f.failed_rows)                  AS failed_rows,
            ROUND(AVG(f.score) * 100)           AS score
        FROM fact_quality_checks f
        JOIN dim_datasets d ON f.dataset_id = d.id
        GROUP BY d.name
        ORDER BY score DESC
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


# Query 2: Rule failure rates 

def rule_failure_rates() -> pd.DataFrame:
    """
    Returns failure rate per rule type.
    Reads from fact_quality_checks.
    """
    query = """
        SELECT
            rule_type                               AS rule,
            SUM(total_rows)                         AS total_rows,
            SUM(failed_rows)                        AS total_failed,
            ROUND(
                SUM(failed_rows)::NUMERIC /
                NULLIF(SUM(total_rows), 0) * 100, 2
            )                                       AS failure_rate_pct
        FROM fact_quality_checks
        GROUP BY rule_type
        ORDER BY failure_rate_pct DESC
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


# Query 3: Quality trend 

def quality_trend(dataset_name: str = None, days: int = 7) -> pd.DataFrame:
    """
    Returns quality score trend from fact_trend_metrics.
    """
    query = """
        SELECT
            t.snapshot_date     AS date,
            d.name              AS dataset,
            t.aggregated_score  AS score
        FROM fact_trend_metrics t
        JOIN dim_datasets d ON t.dataset_id = d.id
        {where}
        ORDER BY t.snapshot_date
    """
    where = f"WHERE d.name = :name" if dataset_name else ""
    query = query.format(where=where)

    with get_engine().connect() as conn:
        if dataset_name:
            df = pd.read_sql(text(query), conn, params={"name": dataset_name})
        else:
            df = pd.read_sql(text(query), conn)

    # filter to last N days
    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"])
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df["date"] >= cutoff]
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df


# Query 4: Worst datasets 

def worst_datasets(top_n: int = 3) -> pd.DataFrame:
    """Returns N datasets with lowest quality scores."""
    return score_summary().nsmallest(top_n, "score")


# Query 5: Monthly summary 

def monthly_summary() -> pd.DataFrame:
    """
    Returns monthly average quality scores per dataset.
    Reads from fact_trend_metrics grouped by month.
    """
    query = """
        SELECT
            TO_CHAR(t.snapshot_date, 'YYYY-MM') AS month,
            d.name                              AS dataset,
            ROUND(AVG(t.aggregated_score))      AS score
        FROM fact_trend_metrics t
        JOIN dim_datasets d ON t.dataset_id = d.id
        GROUP BY TO_CHAR(t.snapshot_date, 'YYYY-MM'), d.name
        ORDER BY d.name, month
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


# Quick test

if __name__ == "__main__":
    print("\n=== Score Summary (from analytics DB) ===")
    print(score_summary().to_string(index=False))

    print("\n=== Rule Failure Rates ===")
    print(rule_failure_rates().to_string(index=False))

    print("\n=== Quality Trend ===")
    print(quality_trend(days=30).to_string(index=False))

    print("\n=== Worst Datasets ===")
    print(worst_datasets(3).to_string(index=False))

    print("\n=== Monthly Summary ===")
    print(monthly_summary().to_string(index=False))