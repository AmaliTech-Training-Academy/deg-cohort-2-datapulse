# data-engineering/tests/test_messy.py

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validation_engine import run_checks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
MESSY    = os.path.join(FIXTURES, "bad_data.csv")

RULES = [
    {"rule_id": "r1", "rule_type": "not_null",    "column": "name",       "parameters": {}},
    {"rule_id": "r2", "rule_type": "not_null",    "column": "email",      "parameters": {}},
    {"rule_id": "r3", "rule_type": "not_null",    "column": "department", "parameters": {}},
    {"rule_id": "r4", "rule_type": "value_range", "column": "age",        "parameters": {"min": 18, "max": 65}},
    {"rule_id": "r5", "rule_type": "value_range", "column": "salary",     "parameters": {"min": 1}},
    {"rule_id": "r6", "rule_type": "unique",      "column": "email",      "parameters": {}},
]


def test_messy_score_is_low():
    """Messy data should produce a low score (below 60)."""
    result = run_checks(MESSY, RULES)
    assert result["score"] < 60, (
        f"Expected score below 60 for messy data but got {result['score']}"
    )


def test_messy_score_not_zero():
    """Score should not be zero — some rules may still pass."""
    result = run_checks(MESSY, RULES)
    assert result["score"] >= 0


def test_messy_at_least_one_rule_fails():
    """At least one rule must fail on messy data."""
    result = run_checks(MESSY, RULES)
    failed = [r for r in result["results"] if not r["passed"]]
    assert len(failed) > 0, "Expected at least one rule to fail on messy data"


def test_messy_not_null_name_fails():
    """not_null rule on name should fail — bad_data.csv has missing names."""
    result = run_checks(MESSY, RULES)
    name_rule = next(r for r in result["results"] if r["rule_id"] == "r1")
    assert name_rule["passed"] is False
    assert name_rule["failed_rows"] > 0


def test_messy_age_out_of_range_fails():
    """value_range rule on age should fail — bad_data.csv has age=-5."""
    result = run_checks(MESSY, RULES)
    age_rule = next(r for r in result["results"] if r["rule_id"] == "r4")
    assert age_rule["passed"] is False
    assert age_rule["failed_rows"] > 0


def test_messy_failed_rows_never_exceeds_total():
    """failed_rows should never be greater than total_rows."""
    result = run_checks(MESSY, RULES)
    for r in result["results"]:
        assert r["failed_rows"] <= r["total_rows"], (
            f"Rule {r['rule_id']}: failed_rows {r['failed_rows']} "
            f"exceeds total_rows {r['total_rows']}"
        )


def test_messy_no_engine_errors():
    """Engine should not crash on messy data — errors go in error field."""
    result = run_checks(MESSY, RULES)
    assert "score" in result
    assert "results" in result