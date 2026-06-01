# data-engineering/tests/test_clean.py

import pytest
import sys
import os

# Add the data-engineering root to path so we can import validation engine
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validation_engine import run_checks

# Path to fixtures
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
CLEAN    = os.path.join(FIXTURES, "good_data.csv")


# Rules matching the clean dataset columns

RULES = [
    {"rule_id": "r1", "rule_type": "not_null",    "column": "name",       "parameters": {}},
    {"rule_id": "r2", "rule_type": "not_null",    "column": "email",      "parameters": {}},
    {"rule_id": "r3", "rule_type": "not_null",    "column": "department", "parameters": {}},
    {"rule_id": "r4", "rule_type": "value_range", "column": "age",        "parameters": {"min": 18, "max": 65}},
    {"rule_id": "r5", "rule_type": "value_range", "column": "salary",     "parameters": {"min": 1}},
    {"rule_id": "r6", "rule_type": "unique",      "column": "email",      "parameters": {}},
]


# Tests

def test_clean_score_is_100():
    """Clean data should produce a perfect score of 100."""
    result = run_checks(CLEAN, RULES)
    assert result["score"] == 100.0, f"Expected 100.0 but got {result['score']}"


def test_clean_all_rules_pass():
    """Every rule should pass on clean data."""
    result = run_checks(CLEAN, RULES)
    for r in result["results"]:
        assert r["passed"] is True, (
            f"Rule {r['rule_id']} ({r['rule_type']} on '{r['column']}') "
            f"failed with {r['failed_rows']} failed rows"
        )


def test_clean_no_failed_rows():
    """No rule should have any failed rows on clean data."""
    result = run_checks(CLEAN, RULES)
    for r in result["results"]:
        assert r["failed_rows"] == 0, (
            f"Rule {r['rule_id']} has {r['failed_rows']} failed rows on clean data"
        )


def test_clean_no_errors():
    """No rule should produce an error on clean data."""
    result = run_checks(CLEAN, RULES)
    for r in result["results"]:
        assert r["error"] is None, (
            f"Rule {r['rule_id']} raised an error: {r['error']}"
        )


def test_clean_total_rules_count():
    """Result should contain exactly as many results as rules passed in."""
    result = run_checks(CLEAN, RULES)
    assert result["total_rules"] == len(RULES)
    assert result["passed_rules"] == len(RULES)


def test_clean_total_rows_correct():
    """Total rows in result should match the actual row count in the file."""
    result = run_checks(CLEAN, RULES)
    assert result["total_rows"] == 10  