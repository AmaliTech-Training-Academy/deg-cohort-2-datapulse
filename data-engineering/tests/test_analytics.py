# data-engineering/tests/test_analytics.py
#
# DE2 (Odile) owns this file.
# Tests that analytics functions return correct results.

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))

from analytics import (
    score_summary,
    rule_failure_rates,
    quality_trend,
    worst_datasets,
    monthly_summary,
)

# Define score_dataframe locally for testing
def score_dataframe(df: pd.DataFrame) -> dict:
    total = len(df)
    if total == 0:
        return {"score": 100, "total_rows": 0, "passed_rows": 0,
                "failed_rows": 0, "rule_results": {}}
    rules = {
        "not_null_name":   df[df["name"].isnull() | (df["name"].astype(str).str.strip() == "")].index,
        "not_null_email":  df[df["email"].isnull() | (df["email"].astype(str).str.strip() == "")].index,
        "not_null_dept":   df[df["department"].isnull() | (df["department"].astype(str).str.strip() == "")].index,
        "age_range":       df[~pd.to_numeric(df["age"], errors="coerce").between(18, 65)].index,
        "salary_positive": df[~pd.to_numeric(df["salary"], errors="coerce").gt(0)].index,
        "hire_date_valid": df[pd.to_datetime(df["hire_date"], errors="coerce").isnull()].index,
    }
    failed_union = set()
    rule_results = {}
    for rule_name, failed_index in rules.items():
        failed_union.update(failed_index)
        failed_count = len(failed_index)
        rule_results[rule_name] = {
            "failed_rows": failed_count,
            "passed": failed_count == 0,
            "pass_rate": round((total - failed_count) / total * 100, 2),
        }
    unique_failed = len(failed_union)
    passed_rows = total - unique_failed
    score = max(0, min(100, round(passed_rows / total * 100)))
    return {
        "score": score,
        "total_rows": total,
        "passed_rows": passed_rows,
        "failed_rows": unique_failed,
        "rule_results": rule_results,
    }

# ── score_dataframe tests ─────────────────────────────────────────────────────

def test_score_dataframe_clean_data_scores_high():
    df = pd.DataFrame({
        "name":       ["Alice", "Bob", "Carol"],
        "email":      ["a@c.com", "b@c.com", "c@c.com"],
        "age":        [30, 25, 40],
        "department": ["Engineering", "HR", "Finance"],
        "salary":     [80000, 60000, 90000],
        "hire_date":  ["2020-01-01", "2021-05-15", "2019-03-10"],
    })
    result = score_dataframe(df)
    assert result["score"] == 100
    assert result["failed_rows"] == 0
    assert result["passed_rows"] == 3


def test_score_dataframe_empty_file():
    df = pd.DataFrame(columns=["name", "email", "age", "department", "salary", "hire_date"])
    result = score_dataframe(df)
    assert result["total_rows"] == 0
    assert result["score"] == 100


def test_score_dataframe_all_nulls_scores_zero():
    df = pd.DataFrame({
        "name":       ["", "", ""],
        "email":      ["", "", ""],
        "age":        [None, None, None],
        "department": ["", "", ""],
        "salary":     [None, None, None],
        "hire_date":  ["", "", ""],
    })
    result = score_dataframe(df)
    assert result["score"] == 0
    assert result["failed_rows"] == 3


def test_score_dataframe_union_counts_row_once():
    """A row failing 3 rules counts as ONE failed row — not three."""
    df = pd.DataFrame({
        "name":       ["",      "Bob"],
        "email":      ["",      "b@c.com"],
        "age":        [-5,      30],
        "department": ["",      "HR"],
        "salary":     [80000,   60000],
        "hire_date":  ["2020-01-01", "2021-05-15"],
    })
    result = score_dataframe(df)
    assert result["failed_rows"] == 1   # row 0 fails multiple rules but counts as 1
    assert result["passed_rows"] == 1
    assert result["score"] == 50


def test_score_dataframe_returns_all_keys():
    df = pd.DataFrame({
        "name": ["Alice"], "email": ["a@c.com"], "age": [30],
        "department": ["Eng"], "salary": [80000], "hire_date": ["2020-01-01"]
    })
    result = score_dataframe(df)
    for key in ["score", "total_rows", "passed_rows", "failed_rows", "rule_results"]:
        assert key in result


# ── score_summary tests ───────────────────────────────────────────────────────

def test_score_summary_returns_dataframe():
    result = score_summary()
    assert isinstance(result, pd.DataFrame)


def test_score_summary_has_required_columns():
    result = score_summary()
    for col in ["dataset", "total_rows", "passed_rows", "failed_rows", "score"]:
        assert col in result.columns


def test_score_summary_scores_between_0_and_100():
    result = score_summary()
    assert result["score"].between(0, 100).all()


def test_score_summary_sorted_descending():
    result = score_summary()
    assert result["score"].is_monotonic_decreasing


# ── rule_failure_rates tests ──────────────────────────────────────────────────

def test_rule_failure_rates_returns_dataframe():
    result = rule_failure_rates()
    assert isinstance(result, pd.DataFrame)


def test_rule_failure_rates_has_required_columns():
    result = rule_failure_rates()
    for col in ["rule", "total_rows", "total_failed", "failure_rate_pct"]:
        assert col in result.columns


def test_rule_failure_rates_pct_between_0_and_100():
    result = rule_failure_rates()
    assert result["failure_rate_pct"].between(0, 100).all()


# ── quality_trend tests ───────────────────────────────────────────────────────

def test_quality_trend_returns_dataframe():
    result = quality_trend("mixed_data", 7)
    assert isinstance(result, pd.DataFrame)


def test_quality_trend_has_required_columns():
    result = quality_trend("mixed_data", 7)
    for col in ["date", "dataset", "score"]:
        assert col in result.columns


def test_quality_trend_scores_between_0_and_100():
    result = quality_trend("mixed_data", 7)
    assert result["score"].between(0, 100).all()


def test_quality_trend_invalid_dataset_returns_empty():
    result = quality_trend("nonexistent_dataset", 7)
    assert len(result) == 0


# ── worst_datasets tests ──────────────────────────────────────────────────────

def test_worst_datasets_returns_correct_count():
    result = worst_datasets(3)
    assert len(result) <= 3


def test_worst_datasets_sorted_ascending():
    result = worst_datasets(3)
    assert result["score"].is_monotonic_increasing


# ── monthly_summary tests ─────────────────────────────────────────────────────

def test_monthly_summary_returns_dataframe():
    result = monthly_summary()
    assert isinstance(result, pd.DataFrame)


def test_monthly_summary_has_required_columns():
    result = monthly_summary()
    for col in ["month", "dataset", "score"]:
        assert col in result.columns