# data-engineering/tests/test_mixed.py
# Tests that the engine produces realistic mid-range scores on mixed data.

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validation_engine import run_checks

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
MIXED    = os.path.join(FIXTURES, "mixed_data.csv")

RULES = [
    {"rule_id": "r1", "rule_type": "not_null",    "column": "name",       "parameters": {}},
    {"rule_id": "r2", "rule_type": "not_null",    "column": "email",      "parameters": {}},
    {"rule_id": "r3", "rule_type": "not_null",    "column": "department", "parameters": {}},
    {"rule_id": "r4", "rule_type": "value_range", "column": "age",        "parameters": {"min": 18, "max": 65}},
    {"rule_id": "r5", "rule_type": "value_range", "column": "salary",     "parameters": {"min": 1}},
    {"rule_id": "r6", "rule_type": "unique",      "column": "email",      "parameters": {}},
]


def test_mixed_score_between_30_and_90():
    """Mixed data should produce a mid-range score between 30 and 90."""
    result = run_checks(MIXED, RULES)
    assert 30 <= result["score"] <= 90, (
        f"Expected score between 30-90 for mixed data but got {result['score']}"
    )


def test_mixed_some_rules_pass():
    """At least one rule should pass on mixed data."""
    result = run_checks(MIXED, RULES)
    passed = [r for r in result["results"] if r["passed"]]
    assert len(passed) > 0, "Expected at least one rule to pass on mixed data"


def test_mixed_some_rules_fail():
    """At least one rule should fail on mixed data."""
    result = run_checks(MIXED, RULES)
    failed = [r for r in result["results"] if not r["passed"]]
    assert len(failed) > 0, "Expected at least one rule to fail on mixed data"


def test_mixed_score_matches_passed_rules():
    """Score should equal passed_rules / total_rules * 100."""
    result = run_checks(MIXED, RULES)
    expected = round(result["passed_rules"] / result["total_rules"] * 100, 2)
    assert result["score"] == expected, (
        f"Score {result['score']} does not match "
        f"passed_rules/total_rules calculation {expected}"
    )


def test_mixed_result_count_matches_rules():
    """Number of results should equal number of rules."""
    result = run_checks(MIXED, RULES)
    assert len(result["results"]) == len(RULES)


def test_mixed_total_rows_consistent():
    """All rule results should report the same total_rows."""
    result = run_checks(MIXED, RULES)
    total_rows = result["total_rows"]
    for r in result["results"]:
        assert r["total_rows"] == total_rows, (
            f"Rule {r['rule_id']} reports {r['total_rows']} total rows "
            f"but expected {total_rows}"
        )