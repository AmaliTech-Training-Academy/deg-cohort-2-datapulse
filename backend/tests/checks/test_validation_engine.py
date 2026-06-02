"""
tests/checks/test_validation_engine.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for ValidationEngine — the core Pandas-based rule execution layer.

Tests the engine directly (no HTTP) by constructing DataFrames and
lightweight rule objects in memory using SimpleNamespace.

Covers
──────
  null_check
    • null value fails
    • NaN fails
    • empty string after strip fails
    • all valid values pass
    • all-null column fails all rows
    • error details capped at 5
    • error detail structure (row, value, reason)

  range_check
    • value below min fails
    • value above max fails
    • boundary values pass (inclusive)
    • non-numeric string coerced to NaN and fails
    • null value fails (cannot confirm in-range)
    • all in-range values pass
    • error detail reason: "below minimum" / "above maximum"

  type_check
    • integer — valid values pass, strings fail, floats fail
    • float — valid values pass
    • boolean — valid values pass, invalid fails
    • string — everything non-null passes

  uniqueness_check
    • all unique values pass
    • BOTH copies of duplicate are flagged (keep=False)
    • three copies all flagged
    • multiple duplicate values flagged

  engine.run()
    • missing column skipped gracefully
    • empty DataFrame raises ValueError
    • returns list[RuleResult] and set of failed indexes
    • union deduplication: row failing 2 rules counted once
"""

from types import SimpleNamespace

import pandas as pd
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_rule(rule_type, column_name, rule_config=None, rule_id="rule-1"):
    """Lightweight rule object that mimics a ValidationRule instance."""
    return SimpleNamespace(
        id=rule_id,
        rule_type=rule_type,
        column_name=column_name,
        rule_config=rule_config or {},
    )


@pytest.fixture
def engine_cls():
    from checks.services.validation_engine import ValidationEngine

    return ValidationEngine


# ═══════════════════════════════════════════════════════════════════════════════
# NULL CHECK
# ═══════════════════════════════════════════════════════════════════════════════


class TestNullCheck:

    def test_null_value_fails(self, engine_cls):
        df = pd.DataFrame({"email": ["a@b.com", None, "c@d.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 1
        assert 1 in result.failed_indexes

    def test_nan_value_fails(self, engine_cls):
        import numpy as np

        df = pd.DataFrame({"email": ["a@b.com", np.nan, "c@d.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 1

    def test_empty_string_after_strip_fails(self, engine_cls):
        """Whitespace-only strings must be treated as null."""
        df = pd.DataFrame({"email": ["a@b.com", "   ", "c@d.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 1

    def test_all_valid_values_pass(self, engine_cls):
        df = pd.DataFrame({"email": ["a@b.com", "c@d.com", "e@f.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 0
        assert result.failure_percentage == 0.0

    def test_all_null_column_fails_all_rows(self, engine_cls):
        df = pd.DataFrame({"email": [None, None, None]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 3

    def test_error_details_capped_at_five(self, engine_cls):
        df = pd.DataFrame({"email": [None] * 10})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.rows_failed == 10
        assert len(result.error_details) <= 5

    def test_error_detail_has_row_value_reason_keys(self, engine_cls):
        df = pd.DataFrame({"email": [None, "a@b.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        detail = result.error_details[0]
        assert "row" in detail
        assert "value" in detail
        assert "reason" in detail

    def test_error_detail_row_is_1_indexed(self, engine_cls):
        """Row numbers in error_details must be 1-indexed for human readability."""
        df = pd.DataFrame({"email": [None, "a@b.com"]})
        result = engine_cls(df)._run_one(make_rule("null_check", "email"))
        assert result.error_details[0]["row"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# RANGE CHECK
# ═══════════════════════════════════════════════════════════════════════════════


class TestRangeCheck:

    def test_value_below_min_fails(self, engine_cls):
        df = pd.DataFrame({"age": [25, -1, 30]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert result.rows_failed == 1
        assert 1 in result.failed_indexes

    def test_value_above_max_fails(self, engine_cls):
        df = pd.DataFrame({"age": [25, 150, 30]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert result.rows_failed == 1
        assert 1 in result.failed_indexes

    def test_boundary_values_pass(self, engine_cls):
        """Min and max are inclusive — boundary values must pass."""
        df = pd.DataFrame({"age": [0, 60, 120]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert result.rows_failed == 0

    def test_non_numeric_string_fails(self, engine_cls):
        """Non-numeric values are coerced to NaN and treated as failures."""
        df = pd.DataFrame({"age": [25, "thirty", 40]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert 1 in result.failed_indexes

    def test_null_value_fails_range(self, engine_cls):
        """Null values cannot be confirmed as in-range — must fail."""
        import numpy as np

        df = pd.DataFrame({"age": [25, np.nan, 40]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert 1 in result.failed_indexes

    def test_all_in_range_passes(self, engine_cls):
        df = pd.DataFrame({"score": [0, 50, 100]})
        result = engine_cls(df)._run_one(make_rule("range_check", "score", {"min": 0, "max": 100}))
        assert result.rows_failed == 0

    def test_error_detail_reason_below_min(self, engine_cls):
        df = pd.DataFrame({"age": [-5, 25]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert "below minimum" in result.error_details[0]["reason"]

    def test_error_detail_reason_above_max(self, engine_cls):
        df = pd.DataFrame({"age": [200, 25]})
        result = engine_cls(df)._run_one(make_rule("range_check", "age", {"min": 0, "max": 120}))
        assert "above maximum" in result.error_details[0]["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE CHECK
# ═══════════════════════════════════════════════════════════════════════════════


class TestTypeCheck:

    def test_integer_valid_values_pass(self, engine_cls):
        df = pd.DataFrame({"score": ["88", "92", "75"]})
        result = engine_cls(df)._run_one(make_rule("type_check", "score", {"expected_type": "integer"}))
        assert result.rows_failed == 0

    def test_integer_string_value_fails(self, engine_cls):
        df = pd.DataFrame({"score": [88, "N/A", 75]})
        result = engine_cls(df)._run_one(make_rule("type_check", "score", {"expected_type": "integer"}))
        assert 1 in result.failed_indexes

    def test_integer_float_fails(self, engine_cls):
        df = pd.DataFrame({"score": [88, 75.5, 90]})
        result = engine_cls(df)._run_one(make_rule("type_check", "score", {"expected_type": "integer"}))
        assert 1 in result.failed_indexes

    def test_float_valid_values_pass(self, engine_cls):
        df = pd.DataFrame({"price": ["9.99", "14.5", "100.0"]})
        result = engine_cls(df)._run_one(make_rule("type_check", "price", {"expected_type": "float"}))
        assert result.rows_failed == 0

    def test_boolean_valid_values_pass(self, engine_cls):
        df = pd.DataFrame({"active": ["true", "false", "1", "0", "yes", "no"]})
        result = engine_cls(df)._run_one(make_rule("type_check", "active", {"expected_type": "boolean"}))
        assert result.rows_failed == 0

    def test_boolean_invalid_value_fails(self, engine_cls):
        df = pd.DataFrame({"active": ["true", "maybe", "false"]})
        result = engine_cls(df)._run_one(make_rule("type_check", "active", {"expected_type": "boolean"}))
        assert 1 in result.failed_indexes

    def test_string_all_values_pass(self, engine_cls):
        """Everything non-null is a valid string — string type only fails on null."""
        df = pd.DataFrame({"name": ["Alice", "123", "True"]})
        result = engine_cls(df)._run_one(make_rule("type_check", "name", {"expected_type": "string"}))
        assert result.rows_failed == 0


# ═══════════════════════════════════════════════════════════════════════════════
# UNIQUENESS CHECK
# ═══════════════════════════════════════════════════════════════════════════════


class TestUniquenessCheck:

    def test_all_unique_values_pass(self, engine_cls):
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        result = engine_cls(df)._run_one(make_rule("uniqueness_check", "id"))
        assert result.rows_failed == 0

    def test_both_copies_of_duplicate_flagged(self, engine_cls):
        """
        CRITICAL: keep=False — when id=5 appears on rows 3 and 4,
        BOTH must be flagged, not just the second occurrence.
        """
        df = pd.DataFrame({"id": [1, 2, 3, 5, 5]})
        result = engine_cls(df)._run_one(make_rule("uniqueness_check", "id"))
        assert result.rows_failed == 2
        assert 3 in result.failed_indexes   # first occurrence
        assert 4 in result.failed_indexes   # second occurrence

    def test_three_copies_all_flagged(self, engine_cls):
        df = pd.DataFrame({"id": [1, 2, 2, 2, 5]})
        result = engine_cls(df)._run_one(make_rule("uniqueness_check", "id"))
        assert result.rows_failed == 3

    def test_multiple_duplicate_values_all_flagged(self, engine_cls):
        df = pd.DataFrame({"id": [1, 1, 2, 2, 3]})
        result = engine_cls(df)._run_one(make_rule("uniqueness_check", "id"))
        assert result.rows_failed == 4

    def test_error_detail_reason_is_duplicate_value(self, engine_cls):
        df = pd.DataFrame({"id": [1, 1, 2]})
        result = engine_cls(df)._run_one(make_rule("uniqueness_check", "id"))
        assert result.error_details[0]["reason"] == "duplicate value"


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINE.RUN() — multi-rule execution
# ═══════════════════════════════════════════════════════════════════════════════


class TestEngineRun:

    def test_empty_dataframe_raises_value_error(self, engine_cls):
        df = pd.DataFrame({"id": pd.Series([], dtype="object")})
        with pytest.raises(ValueError, match="empty"):
            engine_cls(df)

    def test_missing_column_skipped_gracefully(self, engine_cls):
        """A rule referencing a non-existent column is skipped without error."""
        df = pd.DataFrame({"id": [1, 2], "email": ["a@b.com", "c@d.com"]})
        engine = engine_cls(df)
        rules = [
            make_rule("null_check", "email"),
            make_rule("null_check", "phone_number"),  # does not exist
        ]
        results, failed_union = engine.run(rules)
        assert len(results) == 1
        assert results[0].column_name == "email"

    def test_run_returns_results_list_and_failed_set(self, engine_cls):
        df = pd.DataFrame({
            "email": ["a@b.com", None, "c@d.com"],
            "age":   [25, 30, -5],
        })
        results, failed_union = engine_cls(df).run([
            make_rule("null_check",  "email",             rule_id="r1"),
            make_rule("range_check", "age", {"min": 0, "max": 120}, rule_id="r2"),
        ])
        assert len(results) == 2
        assert isinstance(failed_union, set)

    def test_union_deduplicates_rows_failing_multiple_rules(self, engine_cls):
        """
        CRITICAL: A row that fails both null_check AND range_check must appear
        only ONCE in the failed_union — not once per rule.
        """
        # Row 1: null age → fails range_check
        # Row 1 also: null email → fails null_check
        # Row 1 fails 2 rules but must be counted ONCE
        df = pd.DataFrame({
            "email": ["a@b.com", None],
            "age":   [25, None],
        })
        _, failed_union = engine_cls(df).run([
            make_rule("null_check",  "email", rule_id="r1"),
            make_rule("range_check", "age", {"min": 0, "max": 120}, rule_id="r2"),
        ])
        # Row 1 fails both rules but must appear once in the union
        assert 1 in failed_union
        assert len(failed_union) == 1  # only 1 unique failed row

    def test_no_rules_returns_empty_results_and_empty_union(self, engine_cls):
        df = pd.DataFrame({"id": [1, 2, 3]})
        results, failed_union = engine_cls(df).run([])
        assert results == []
        assert failed_union == set()

    def test_rule_result_failure_percentage_correct(self, engine_cls):
        df = pd.DataFrame({"email": [None, "a@b.com", None, "c@d.com"]})
        results, _ = engine_cls(df).run([make_rule("null_check", "email")])
        assert results[0].failure_percentage == 50.0
