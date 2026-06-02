"""
tests/checks/test_scoring_service.py
Tests for QualityScoreCalculator.
"""

import pytest

from checks.services.scoring_service import QualityScoreCalculator


class TestQualityScoreCalculator:
    def setup_method(self):
        self.calc = QualityScoreCalculator()

    def test_all_rows_pass_score_100(self):
        result = self.calc.calculate(total_rows=10, failed_union=set())
        assert result.overall_score == 100
        assert result.total_rows_passed == 10
        assert result.total_rows_failed == 0

    def test_all_rows_fail_score_0(self):
        result = self.calc.calculate(total_rows=5, failed_union={0, 1, 2, 3, 4})
        assert result.overall_score == 0
        assert result.total_rows_passed == 0
        assert result.total_rows_failed == 5

    def test_half_rows_fail_score_50(self):
        result = self.calc.calculate(total_rows=10, failed_union={0, 1, 2, 3, 4})
        assert result.overall_score == 50

    def test_score_rounds_to_nearest_integer(self):
        # 1/6 * 100 = 16.67 → rounds to 17
        result = self.calc.calculate(total_rows=6, failed_union={0, 1, 2, 3, 4})
        assert result.overall_score == 17

    def test_score_clamped_to_0(self):
        # Defensive: more failed than total should not go below 0
        result = self.calc.calculate(total_rows=3, failed_union={0, 1, 2, 3, 4})
        assert result.overall_score == 0

    def test_empty_dataset_returns_100(self):
        result = self.calc.calculate(total_rows=0, failed_union=set())
        assert result.overall_score == 100
        assert result.total_rows_passed == 0
        assert result.total_rows_failed == 0

    def test_union_deduplication_counts_once(self):
        # Row 0 fails 3 rules but union has it once — only 1 failed row
        result = self.calc.calculate(total_rows=5, failed_union={0})
        assert result.total_rows_failed == 1
        assert result.total_rows_passed == 4

    def test_score_result_repr(self):
        result = self.calc.calculate(total_rows=10, failed_union={0, 1})
        assert "80" in repr(result)

    def test_test_data_csv_score(self):
        # Matches the worked example from the API flow doc:
        # 6 rows, 5 failed (rows 2,3,4,5,6), 1 passed → score = 17
        result = self.calc.calculate(total_rows=6, failed_union={1, 2, 3, 4, 5})
        assert result.overall_score == 17
        assert result.total_rows_passed == 1
        assert result.total_rows_failed == 5
