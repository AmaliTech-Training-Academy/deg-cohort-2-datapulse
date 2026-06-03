"""
tests/checks/test_validation_engine.py
Tests for ValidationEngine — all 4 rule checkers + union logic.
"""

import pandas as pd
import pytest

from checks.services.validation_engine import ValidationEngine


def make_engine(data: dict) -> ValidationEngine:
    return ValidationEngine(pd.DataFrame(data))


class FakeRule:
    def __init__(self, rule_id, column_name, rule_type, rule_config=None):
        self.id = rule_id
        self.column_name = column_name
        self.rule_type = rule_type
        self.rule_config = rule_config or {}


# ── Null check ────────────────────────────────────────────────────────────────


class TestNullCheck:
    def test_no_nulls_passes_all(self):
        eng = make_engine({"email": ["a@b.com", "c@d.com"]})
        failed, _ = eng._check_null("email", {})
        assert failed == []

    def test_null_value_fails(self):
        eng = make_engine({"email": [None, "a@b.com"]})
        failed, _ = eng._check_null("email", {})
        assert 0 in failed

    def test_empty_string_fails(self):
        eng = make_engine({"email": ["", "a@b.com"]})
        failed, _ = eng._check_null("email", {})
        assert 0 in failed

    def test_whitespace_only_fails(self):
        eng = make_engine({"email": ["   ", "a@b.com"]})
        failed, _ = eng._check_null("email", {})
        assert 0 in failed

    def test_error_details_populated(self):
        eng = make_engine({"email": [None, "a@b.com"]})
        _, details = eng._check_null("email", {})
        assert len(details) == 1
        assert details[0]["reason"] == "null or empty value"
        assert details[0]["row"] == 1  # 1-indexed


# ── Type check ────────────────────────────────────────────────────────────────


class TestTypeCheck:
    def test_integer_valid_values_pass(self):
        eng = make_engine({"age": [1, 2, 3]})
        failed, _ = eng._check_type("age", {"expected_type": "integer"})
        assert failed == []

    def test_integer_rejects_float_with_fraction(self):
        eng = make_engine({"age": [1.5, 2.0]})
        failed, _ = eng._check_type("age", {"expected_type": "integer"})
        assert 0 in failed  # 1.5 fails
        assert 1 not in failed  # 2.0 is whole — passes

    def test_integer_accepts_whole_number_float(self):
        eng = make_engine({"age": [3.0, 10.0]})
        failed, _ = eng._check_type("age", {"expected_type": "integer"})
        assert failed == []

    def test_integer_accepts_scientific_notation(self):
        eng = make_engine({"age": ["1e2"]})
        failed, _ = eng._check_type("age", {"expected_type": "integer"})
        assert failed == []

    def test_integer_rejects_text(self):
        eng = make_engine({"age": ["abc", "1"]})
        failed, _ = eng._check_type("age", {"expected_type": "integer"})
        assert 0 in failed
        assert 1 not in failed

    def test_float_valid_values_pass(self):
        eng = make_engine({"score": [1.1, 2.5, 3.0]})
        failed, _ = eng._check_type("score", {"expected_type": "float"})
        assert failed == []

    def test_float_rejects_text(self):
        eng = make_engine({"score": ["abc", "1.5"]})
        failed, _ = eng._check_type("score", {"expected_type": "float"})
        assert 0 in failed

    def test_boolean_valid_values_pass(self):
        eng = make_engine({"active": ["true", "false", "1", "0", "yes", "no"]})
        failed, _ = eng._check_type("active", {"expected_type": "boolean"})
        assert failed == []

    def test_boolean_rejects_invalid(self):
        eng = make_engine({"active": ["maybe", "true"]})
        failed, _ = eng._check_type("active", {"expected_type": "boolean"})
        assert 0 in failed
        assert 1 not in failed

    def test_string_only_rejects_null(self):
        eng = make_engine({"name": ["Alice", None, "Bob"]})
        failed, _ = eng._check_type("name", {"expected_type": "string"})
        assert 1 in failed
        assert 0 not in failed


# ── Range check ───────────────────────────────────────────────────────────────


class TestRangeCheck:
    def test_all_in_range_pass(self):
        eng = make_engine({"age": [10, 50, 100]})
        failed, _ = eng._check_range("age", {"min": 0, "max": 120})
        assert failed == []

    def test_below_min_fails(self):
        eng = make_engine({"age": [-1, 50]})
        failed, details = eng._check_range("age", {"min": 0, "max": 120})
        assert 0 in failed
        assert "below minimum" in details[0]["reason"]

    def test_above_max_fails(self):
        eng = make_engine({"age": [50, 200]})
        failed, details = eng._check_range("age", {"min": 0, "max": 120})
        assert 1 in failed
        assert "above maximum" in details[0]["reason"]

    def test_non_numeric_fails(self):
        eng = make_engine({"age": ["abc", "50"]})
        failed, details = eng._check_range("age", {"min": 0, "max": 120})
        assert 0 in failed
        assert "not a valid number" in details[0]["reason"]

    def test_null_value_fails(self):
        eng = make_engine({"age": [None, 50]})
        failed, _ = eng._check_range("age", {"min": 0, "max": 120})
        assert 0 in failed

    def test_boundary_values_pass(self):
        eng = make_engine({"age": [0, 120]})
        failed, _ = eng._check_range("age", {"min": 0, "max": 120})
        assert failed == []

    def test_only_min_specified(self):
        eng = make_engine({"age": [-1, 0, 999]})
        failed, _ = eng._check_range("age", {"min": 0, "max": None})
        assert 0 in failed
        assert 1 not in failed
        assert 2 not in failed

    def test_only_max_specified(self):
        eng = make_engine({"age": [999, 100]})
        failed, _ = eng._check_range("age", {"min": None, "max": 120})
        assert 0 in failed
        assert 1 not in failed


# ── Uniqueness check ──────────────────────────────────────────────────────────


class TestUniquenessCheck:
    def test_all_unique_passes(self):
        eng = make_engine({"id": [1, 2, 3]})
        failed, _ = eng._check_uniqueness("id", {})
        assert failed == []

    def test_duplicate_flags_both_copies(self):
        eng = make_engine({"id": [1, 2, 1]})
        failed, _ = eng._check_uniqueness("id", {})
        assert 0 in failed
        assert 2 in failed
        assert 1 not in failed

    def test_error_details_show_duplicate_reason(self):
        eng = make_engine({"id": [5, 5]})
        _, details = eng._check_uniqueness("id", {})
        assert all(d["reason"] == "duplicate value" for d in details)

    def test_three_copies_all_flagged(self):
        eng = make_engine({"id": [7, 7, 7]})
        failed, _ = eng._check_uniqueness("id", {})
        assert set(failed) == {0, 1, 2}


# ── Engine run + union ────────────────────────────────────────────────────────


class TestEngineRun:
    def test_run_returns_one_result_per_rule(self):
        eng = make_engine({"age": [25, 30], "email": ["a@b.com", "c@d.com"]})
        rules = [
            FakeRule("r1", "age", "null_check"),
            FakeRule("r2", "email", "null_check"),
        ]
        results, _ = eng.run(rules)
        assert len(results) == 2

    def test_union_deduplicates_failed_rows(self):
        # Row 0 fails both rules — should be counted once
        eng = make_engine({"age": [None, 30], "email": [None, "c@d.com"]})
        rules = [
            FakeRule("r1", "age", "null_check"),
            FakeRule("r2", "email", "null_check"),
        ]
        _, failed_union = eng.run(rules)
        assert len(failed_union) == 1
        assert 0 in failed_union

    def test_skips_missing_column(self):
        eng = make_engine({"age": [25, 30]})
        rules = [FakeRule("r1", "nonexistent_col", "null_check")]
        results, failed_union = eng.run(rules)
        assert results == []
        assert failed_union == set()

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(ValueError, match="empty"):
            ValidationEngine(pd.DataFrame())

    def test_raises_on_unknown_rule_type(self):
        eng = make_engine({"age": [25]})
        rule = FakeRule("r1", "age", "unknown_check")
        with pytest.raises(ValueError, match="Unknown rule type"):
            eng._run_one(rule)

    def test_failure_percentage_calculated(self):
        eng = make_engine({"age": [None, 30, 40]})
        rules = [FakeRule("r1", "age", "null_check")]
        results, _ = eng.run(rules)
        assert results[0].failure_percentage == pytest.approx(33.33, abs=0.1)

    def test_error_details_capped_at_five(self):
        eng = make_engine({"age": [None] * 10})
        rules = [FakeRule("r1", "age", "null_check")]
        results, _ = eng.run(rules)
        assert len(results[0].error_details) == 5
