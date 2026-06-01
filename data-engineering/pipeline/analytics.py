# data-engineering/pipeline/analytics.py
#
# DE2 (Odile) owns this file.
# Python analytics queries for DataPulse quality trends.
# These functions read from the sample CSV files and produce
# analytics results that feed the dashboard.
#
# Usage:
#   from pipeline.analytics import (
#       score_summary, quality_trend, rule_failure_rates,
#       worst_datasets, monthly_summary
#   )

import os
import pandas as pd
from datetime import datetime, timedelta

# Sample data paths 
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")

DATASETS = {
    "good_data":   os.path.join(SAMPLE_DIR, "good_data.csv"),
    "bad_data":    os.path.join(SAMPLE_DIR, "bad_data.csv"),
    "mixed_data":  os.path.join(SAMPLE_DIR, "mixed_data.csv"),
    "large_clean": os.path.join(SAMPLE_DIR, "large_clean.csv"),
    "large_dirty": os.path.join(SAMPLE_DIR, "large_dirty.csv"),
    "large_mixed": os.path.join(SAMPLE_DIR, "large_mixed.csv"),
}


# Core scoring function

def score_dataframe(df: pd.DataFrame) -> dict:
    """
    Compute quality score for a dataframe.
    Score = % of rows passing ALL rules.
    Rules: not_null, age_range, salary_range, hire_date_valid
    """
    total = len(df)
    if total == 0:
        return {"score": 0, "total_rows": 0, "passed_rows": 0,
                "failed_rows": 0, "rule_results": {}}

    rules = {
        "not_null_name":    df["name"].isnull() | (df["name"].astype(str).str.strip() == ""),
        "not_null_email":   df["email"].isnull() | (df["email"].astype(str).str.strip() == ""),
        "not_null_dept":    df["department"].isnull() | (df["department"].astype(str).str.strip() == ""),
        "age_range":        ~pd.to_numeric(df["age"], errors="coerce").between(18, 65),
        "salary_positive":  ~pd.to_numeric(df["salary"], errors="coerce").gt(0),
        "hire_date_valid":  pd.to_datetime(df["hire_date"], errors="coerce").isnull(),
    }

    # Row passes only if it passes ALL rules
    fail_any = pd.Series([False] * total, index=df.index)
    rule_results = {}

    for rule_name, fail_mask in rules.items():
        failed_rows = int(fail_mask.sum())
        rule_results[rule_name] = {
            "failed_rows": failed_rows,
            "passed":      failed_rows == 0,
            "pass_rate":   round((total - failed_rows) / total * 100, 2)
        }
        fail_any = fail_any | fail_mask

    passed_rows = int((~fail_any).sum())
    score       = round(passed_rows / total * 100, 2)

    return {
        "score":        score,
        "total_rows":   total,
        "passed_rows":  passed_rows,
        "failed_rows":  total - passed_rows,
        "rule_results": rule_results,
    }


# Query 1: Score summary across all datasets 

def score_summary() -> pd.DataFrame:
    """
    Returns a summary of quality scores for all datasets.
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


# Query 2: Rule failure rates across all datasets

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
            ) if data["total_rows"] > 0 else 0
        })

    return pd.DataFrame(rows).sort_values("failure_rate_pct", ascending=False)


# ── Query 3: Quality trend simulation ────────────────────────────────────────

def quality_trend(dataset_name: str = "mixed_data", days: int = 7) -> pd.DataFrame:
    """
    Simulates quality score trend over the past N days for a dataset.
    In production this reads from the DB — here it uses sample data.
    Answers: is quality improving or declining?
    """
    path = DATASETS.get(dataset_name)
    if not path or not os.path.exists(path):
        return pd.DataFrame()

    df    = pd.read_csv(path)
    total = len(df)
    rows  = []

    # Simulate trend by checking random subsets over time
    import random
    random.seed(42)

    for i in range(days):
        date      = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        # Slightly vary the sample to simulate change over time
        sample    = df.sample(n=min(total, max(10, total - random.randint(0, 5))),
                              random_state=i)
        result    = score_dataframe(sample)
        rows.append({
            "date":    date,
            "dataset": dataset_name,
            "score":   result["score"],
            "checked_rows": result["total_rows"],
        })

    return pd.DataFrame(rows)


# Query 4: Worst datasets 

def worst_datasets(top_n: int = 3) -> pd.DataFrame:
    """
    Returns the N datasets with the lowest quality scores.
    Answers: which datasets need the most attention?
    """
    summary = score_summary()
    return summary.nsmallest(top_n, "score")


# Query 5: Monthly summary 

def monthly_summary() -> pd.DataFrame:
    """
    Simulates a monthly quality summary across datasets.
    In production this reads from the DB.
    """
    rows = []
    months = ["2024-10", "2024-11", "2024-12", "2025-01"]

    import random
    random.seed(99)

    for dataset_name, path in DATASETS.items():
        if not os.path.exists(path):
            continue
        df     = pd.read_csv(path)
        result = score_dataframe(df)
        base   = result["score"]

        for month in months:
            # Simulate slight variation month over month
            variation = random.uniform(-5, 5)
            score     = round(min(100, max(0, base + variation)), 2)
            rows.append({
                "month":   month,
                "dataset": dataset_name,
                "score":   score,
            })

    return pd.DataFrame(rows).sort_values(["dataset", "month"])


# Quick test

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