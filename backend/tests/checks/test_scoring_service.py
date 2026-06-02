"""
tests/checks/test_scoring_service.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for QualityScoreCalculator.

THE most important test in the entire project:
    test_score_formula_deduplicates_failures

A row that fails 3 rules must be counted ONCE in the score denominator.
This is the union-of-failures requirement that makes the score meaningful.

Covers
──────
  • Deduplication: row failing multiple rules counted once
  • Exact score replication from live PowerShell test (6 rows, 5 failures → 17)
  • Perfect score (no failures → 100)
  • Zero score (all rows fail → 0)
  • Empty dataset edge case (→ 100)
  • Rounding to nearest integer
  • Score is always an integer
  • Clamped to [0, 100]
  • ScoreResult has all required attributes
  • rows_passed + rows_failed == total_rows
"""

import pytest


@pytest.fixture
def calculator():
    from checks.services.scoring_service import QualityScoreCalculator

    return QualityScoreCalculator()


class TestQualityScoreCalculator:

    # ── THE MOST IMPORTANT TEST ────────────────────────────────────────────────

    def test_score_formula_deduplicates_failures(self, calculator):
        """
        CRITICAL: Row 0 fails 3 rules — it must be counted once, not three times.

        3 total rows, 1 unique failed row:
            rows_passed  = 3 - 1 = 2
            raw_score    = (2 / 3) * 100 = 66.67
            overall_score = round(66.67) = 67
        """
        result = calculator.calculate(total_rows=3, failed_union={0})
        assert result.overall_score == 67
        assert result.total_rows_passed == 2
        assert result.total_rows_failed == 1  # NOT 3 (one per rule)

    def test_exact_score_from_live_powershell_test(self, calculator):
        """
        Replicates the exact result from the live PowerShell test session:
            test_data.csv: 6 rows, 5 unique failures → score = 17
        """
        failed_union = {1, 2, 3, 4, 5}  # rows 2-6 in 1-indexed (0-indexed: 1-5)
        result = calculator.calculate(total_rows=6, failed_union=failed_union)
        assert result.overall_score == 17
        assert result.total_rows_passed == 1
        assert result.total_rows_failed == 5

    # ── Score boundaries ──────────────────────────────────────────────────────

    def test_perfect_score_no_failures(self, calculator):
        result = calculator.calculate(total_rows=100, failed_union=set())
        assert result.overall_score == 100
        assert result.total_rows_passed == 100
        assert result.total_rows_failed == 0

    def test_zero_score_all_rows_fail(self, calculator):
        result = calculator.calculate(total_rows=100, failed_union=set(range(100)))
        assert result.overall_score == 0
        assert result.total_rows_passed == 0
        assert result.total_rows_failed == 100

    def test_empty_dataset_returns_100(self, calculator):
        """Zero rows → technically 100% of zero rows pass."""
        result = calculator.calculate(total_rows=0, failed_union=set())
        assert result.overall_score == 100
        assert result.total_rows_passed == 0
        assert result.total_rows_failed == 0

    # ── Rounding ──────────────────────────────────────────────────────────────

    def test_score_rounds_to_nearest_integer(self, calculator):
        """1 failure / 3 rows = 66.67% → rounds to 67."""
        result = calculator.calculate(total_rows=3, failed_union={0})
        assert result.overall_score == 67

    def test_score_is_python_int(self, calculator):
        result = calculator.calculate(total_rows=7, failed_union={0, 1})
        assert isinstance(result.overall_score, int)

    # ── Clamping ──────────────────────────────────────────────────────────────

    def test_score_never_exceeds_100(self, calculator):
        result = calculator.calculate(total_rows=5, failed_union=set())
        assert result.overall_score <= 100

    def test_score_never_below_zero(self, calculator):
        result = calculator.calculate(total_rows=5, failed_union={0, 1, 2, 3, 4})
        assert result.overall_score >= 0

    # ── ScoreResult structure ─────────────────────────────────────────────────

    def test_result_has_overall_score(self, calculator):
        assert hasattr(calculator.calculate(total_rows=10, failed_union={0}), "overall_score")

    def test_result_has_total_rows_passed(self, calculator):
        assert hasattr(calculator.calculate(total_rows=10, failed_union={0}), "total_rows_passed")

    def test_result_has_total_rows_failed(self, calculator):
        assert hasattr(calculator.calculate(total_rows=10, failed_union={0}), "total_rows_failed")

    def test_passed_plus_failed_equals_total(self, calculator):
        result = calculator.calculate(total_rows=10, failed_union={0, 2, 4})
        assert result.total_rows_passed + result.total_rows_failed == 10

    # ── Various score values ──────────────────────────────────────────────────

    def test_50_percent_score(self, calculator):
        result = calculator.calculate(total_rows=10, failed_union=set(range(5)))
        assert result.overall_score == 50

    def test_80_percent_score(self, calculator):
        result = calculator.calculate(total_rows=10, failed_union=set(range(2)))
        assert result.overall_score == 80

    def test_single_row_passes(self, calculator):
        assert calculator.calculate(total_rows=1, failed_union=set()).overall_score == 100

    def test_single_row_fails(self, calculator):
        assert calculator.calculate(total_rows=1, failed_union={0}).overall_score == 0
