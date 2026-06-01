"""
checks/services/scoring_service.py
────────────────────────────────────────────────────────────────────────────────
QualityScoreCalculator — computes the 0-100 quality score from engine results.

Formula:
    quality_score = (rows_passed / total_rows) * 100

Where:
    rows_passed = total_rows - len(failed_union)
    failed_union = set union of all failed row indexes across all rules

Why union and not sum:
    A row that fails 3 rules is ONE bad row, not three.
    Summing per-rule failures would give a score below 0 in extreme cases
    and always overstates the problem.

The score is rounded to the nearest integer to match the schema:
    quality_reports.overall_score  INTEGER
"""

import logging

logger = logging.getLogger(__name__)


class QualityScoreCalculator:
    """
    Stateless calculator. Accepts engine output, returns score + counts.

    Usage:
        calculator = QualityScoreCalculator()
        result = calculator.calculate(total_rows=100, failed_union={3, 5, 17})
        # result.overall_score    → 97
        # result.total_rows_passed → 97
        # result.total_rows_failed → 3
    """

    def calculate(self, total_rows: int, failed_union: set) -> "ScoreResult":
        """
        Compute the quality score.

        Parameters
        ----------
        total_rows   : int  — total number of rows in the dataset
        failed_union : set  — union of all failed row indexes (0-based)

        Returns
        -------
        ScoreResult
        """
        if total_rows == 0:
            # Empty dataset — technically 100% of zero rows pass
            return ScoreResult(
                overall_score=100,
                total_rows_passed=0,
                total_rows_failed=0,
            )

        unique_failed = len(failed_union)
        rows_passed = total_rows - unique_failed

        # Clamp to [0, 100] — defensive guard against edge cases
        raw_score = (rows_passed / total_rows) * 100
        overall_score = max(0, min(100, round(raw_score)))

        logger.info(
            "Quality score: %d/100 (%d passed, %d failed out of %d total)",
            overall_score,
            rows_passed,
            unique_failed,
            total_rows,
        )

        return ScoreResult(
            overall_score=overall_score,
            total_rows_passed=rows_passed,
            total_rows_failed=unique_failed,
        )


class ScoreResult:
    """Value object returned by QualityScoreCalculator.calculate()."""

    __slots__ = ("overall_score", "total_rows_passed", "total_rows_failed")

    def __init__(
        self,
        overall_score: int,
        total_rows_passed: int,
        total_rows_failed: int,
    ):
        self.overall_score = overall_score
        self.total_rows_passed = total_rows_passed
        self.total_rows_failed = total_rows_failed

    def __repr__(self) -> str:
        return (
            f"ScoreResult(overall_score={self.overall_score}, "
            f"passed={self.total_rows_passed}, "
            f"failed={self.total_rows_failed})"
        )
