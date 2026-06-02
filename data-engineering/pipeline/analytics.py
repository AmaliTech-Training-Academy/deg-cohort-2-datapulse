# data-engineering/pipeline/analytics.py
#
# Python analytics queries for DataPulse quality trends.
# These functions read from the sample CSV files and produce
# analytics results that feed the dashboard.
#
# Usage:
#   from pipeline.analytics import (
#       score_summary, quality_trend, rule_failure_rates,
#       worst_datasets, monthly_summary
#   )

# data-engineering/pipeline/analytics.py
#
# DE2 (Odile) owns this file.
# Scoring formula matches backend's QualityScoreCalculator exactly:
#   score = (total_rows - len(failed_union)) / total_rows * 100
# Where failed_union = set union of all failed row indexes across all rules.
# A row failing 3 rules counts as ONE failed row — not three.

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random

# ── Sample data paths ─────────────────────────────────────────────────────────
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")

DATASETS = {
    "clean_data":       os.path.join(SAMPLE_DIR, "clean_data.csv"),
    "messy_data":       os.path.join(SAMPLE_DIR, "messy_data.csv"),
    "mixed_data":       os.path.join(SAMPLE_DIR, "mixed_data.csv"),
    "large_clean_data": os.path.join(SAMPLE_DIR, "large_clean_data.csv"),
    "large_messy_data": os.path.join(SAMPLE_DIR, "large_messy_data.csv"),
    "large_mixed_data": os.path.join(SAMPLE_DIR, "large_mixed_data.csv"),
}


# ── Core scoring function — matches backend QualityScoreCalculator ────────────

def score_dataframe(df: pd.DataFrame) -> dict:
    """
    Compute quality score matching backend's QualityScoreCalculator formula.

    Formula:
        score = (total_rows - len(failed_union)) / total_rows * 100

    Where:
        failed_union = set union of all failed row indexes across all rules
        A row failing 3 rules counts as ONE failed row — not three.

    Score is rounded to nearest integer — matches quality_reports.overall_score
    """
    total = len(df)

    if total == 0:
        return {
            "score":        100,
            "total_rows":   0,
            "passed_rows":  0,
            "failed_rows":  0,
            "rule_results": {},
        }

    # ── Build failed row index per rule ───────────────────────────────────────
    rules = {
        "not_null_name": df[
            df["name"].isnull() |
            (df["name"].astype(str).str.strip() == "")
        ].index,

        "not_null_email": df[
            df["email"].isnull() |
            (df["email"].astype(str).str.strip() == "")
        ].index,

        "not_null_department": df[
            df["department"].isnull() |
            (df["department"].astype(str).str.strip() == "")
        ].index,

        "age_range": df[
            ~pd.to_numeric(df["age"], errors="coerce").between(18, 65)
        ].index,

        "salary_positive": df[
            ~pd.to_numeric(df["salary"], errors="coerce").gt(0)
        ].index,

        "hire_date_valid": df[
            pd.to_datetime(df["hire_date"], errors="coerce").isnull()
        ].index,
    }

    # ── Union of all failed row indexes ───────────────────────────────────────
    failed_union = set()
    rule_results = {}

    for rule_name, failed_index in rules.items():
        failed_union.update(failed_index)   # union — not sum
        failed_count = len(failed_index)
        rule_results[rule_name] = {
            "failed_rows": failed_count,
            "passed":      failed_count == 0,
            "pass_rate":   round((total - failed_count) / total * 100, 2),
        }

    # ── Final score ───────────────────────────────────────────────────────────
    unique_failed = len(failed_union)
    passed_rows   = total - unique_failed
    raw_score     = (passed_rows / total) * 100
    score         = max(0, min(100, round(raw_score)))

    return {
        "score":        score,
        "total_rows":   total,
        "passed_rows":  passed_rows,
        "failed_rows":  unique_failed,
        "rule_results": rule_results,
    }


# ── Query 1: Score summary across all datasets ────────────────────────────────

def score_summary() -> pd.DataFrame:
    """
    Returns quality score summary for all datasets.
    Answers: which dataset has the best/worst quality?
    """
    rows = []
    for name, path in DATASETS.items():
        if not os.path.exists(path):
            continue
        df     = pd.read_csv(path)
        result = score_dataframe(df)
        rows.append({
            "dataset":      name,
            "total_rows":   result["total_rows"],
            "passed_rows":  result["passed_rows"],
            "failed_rows":  result["failed_rows"],
            "score":        result["score"],
        })

    return pd.DataFrame(rows).sort_values("score", ascending=False)


# ── Query 2: Rule failure rates across all datasets ───────────────────────────

def rule_failure_rates() -> pd.DataFrame:
    """
    Returns failure rate per rule type across all datasets.
    Answers: which rule fails most often?
    """
    rule_totals = {}

    for name, path in DATASETS.items():
        if not os.path.exists(path):
            continue
        df     = pd.read_csv(path)
        result = score_dataframe(df)
        total  = result["total_rows"]

        for rule, data in result["rule_results"].items():
            if rule not in rule_totals:
                rule_totals[rule] = {"total_rows": 0, "total_failed": 0}
            rule_totals[rule]["total_rows"]   += total
            rule_totals[rule]["total_failed"] += data["failed_rows"]

    rows = []
    for rule, data in rule_totals.items():
        rows.append({
            "rule":             rule,
            "total_rows":       data["total_rows"],
            "total_failed":     data["total_failed"],
            "failure_rate_pct": round(
                data["total_failed"] / data["total_rows"] * 100, 2
            ) if data["total_rows"] > 0 else 0,
        })

    return pd.DataFrame(rows).sort_values("failure_rate_pct", ascending=False)


# ── Query 3: Quality trend simulation ────────────────────────────────────────

def quality_trend(dataset_name: str = "mixed_data", days: int = 7) -> pd.DataFrame:
    """
    Simulates quality score trend over the past N days for a dataset.
    In production this reads from quality_reports table in PostgreSQL.
    Answers: is quality improving or declining?
    """
    path = DATASETS.get(dataset_name)
    if not path or not os.path.exists(path):
        return pd.DataFrame()

    df    = pd.read_csv(path)
    total = len(df)
    rows  = []

    random.seed(42)

    for i in range(days):
        date   = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        sample = df.sample(
            n=min(total, max(10, total - random.randint(0, 5))),
            random_state=i
        )
        result = score_dataframe(sample)
        rows.append({
            "date":         date,
            "dataset":      dataset_name,
            "score":        result["score"],
            "checked_rows": result["total_rows"],
        })

    return pd.DataFrame(rows)


# ── Query 4: Worst datasets ───────────────────────────────────────────────────

def worst_datasets(top_n: int = 3) -> pd.DataFrame:
    """
    Returns the N datasets with the lowest quality scores.
    Answers: which datasets need the most attention?
    """
    return score_summary().nsmallest(top_n, "score")


# ── Query 5: Monthly summary ──────────────────────────────────────────────────

def monthly_summary() -> pd.DataFrame:
    """
    Simulates monthly quality summary across datasets.
    In production this reads from quality_reports table grouped by month.
    """
    rows   = []
    months = ["2024-10", "2024-11", "2024-12", "2025-01"]

    random.seed(99)

    for dataset_name, path in DATASETS.items():
        if not os.path.exists(path):
            continue
        df     = pd.read_csv(path)
        result = score_dataframe(df)
        base   = result["score"]

        for month in months:
            variation = random.uniform(-5, 5)
            score     = max(0, min(100, round(base + variation)))
            rows.append({
                "month":   month,
                "dataset": dataset_name,
                "score":   score,
            })

    return pd.DataFrame(rows).sort_values(["dataset", "month"])


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Score Summary ===")
    print(score_summary().to_string(index=False))

    print("\n=== Rule Failure Rates ===")
    print(rule_failure_rates().to_string(index=False))

    print("\n=== Quality Trend (mixed_data, 7 days) ===")
    print(quality_trend("mixed_data", 7).to_string(index=False))

    print("\n=== Worst Datasets ===")
    print(worst_datasets(3).to_string(index=False))

    print("\n=== Monthly Summary ===")
    print(monthly_summary().to_string(index=False))