"""
checks/services/validation_engine.py
────────────────────────────────────────────────────────────────────────────────
ValidationEngine — runs all 4 rule types against a Pandas DataFrame and
returns per-rule results plus a union set of all failed row indexes.

Architecture decision — union of failed rows:
    A row that fails 3 different rules is counted ONCE in the overall
    quality score. This requires maintaining a set union across all rules
    rather than summing per-rule failure counts.

    failed_union: set[int] accumulates every row index that fails ANY rule.
    The quality score is then: (total - len(failed_union)) / total * 100

Rule checker methods all follow the same contract:
    Input:  df (full DataFrame), column (str), config (dict)
    Output: list[int] — row indexes (0-based) that failed
            list[dict] — error_details with row, value, reason (up to 5)
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Maximum number of error examples stored per rule finding
MAX_ERROR_SAMPLES = 5


class RuleResult:
    """Value object returned by each rule checker."""

    __slots__ = (
        "rule_id",
        "rule_type",
        "column_name",
        "rows_checked",
        "rows_failed",
        "failure_percentage",
        "error_details",
        "failed_indexes",  # full set — used for union, not persisted
    )

    def __init__(
        self,
        rule_id,
        rule_type: str,
        column_name: str,
        rows_checked: int,
        failed_indexes: list,
        error_details: list,
    ):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.column_name = column_name
        self.rows_checked = rows_checked
        self.failed_indexes = set(failed_indexes)
        self.rows_failed = len(failed_indexes)
        self.failure_percentage = (
            round((self.rows_failed / rows_checked) * 100, 2)
            if rows_checked > 0
            else 0.0
        )
        self.error_details = error_details


class ValidationEngine:
    """
    Executes all active rules for a dataset against a DataFrame.

    Usage:
        engine = ValidationEngine(df)
        results, failed_union = engine.run(rules_queryset)
    """

    def __init__(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("Cannot validate an empty DataFrame.")
        self.df = df
        self.total_rows = len(df)

    def run(self, rules) -> tuple[list[RuleResult], set]:
        """
        Run all rules. Return (list[RuleResult], set of all failed row indexes).

        Parameters
        ----------
        rules : QuerySet or iterable of ValidationRule instances

        Returns
        -------
        results     : list[RuleResult] — one entry per rule
        failed_union: set[int]         — union of all failed indexes
        """
        results: list[RuleResult] = []
        failed_union: set[int] = set()

        for rule in rules:
            col = rule.column_name

            # Guard: column no longer exists in the file after a re-upload
            if col not in self.df.columns:
                logger.warning(
                    "Rule %s skipped — column '%s' not found in DataFrame", rule.id, col
                )
                continue

            result = self._run_one(rule)
            results.append(result)
            failed_union.update(result.failed_indexes)  # union accumulates here

        logger.info(
            "Engine run complete: %d rules, %d/%d rows failed (union)",
            len(results),
            len(failed_union),
            self.total_rows,
        )

        return results, failed_union

    def _run_one(self, rule) -> RuleResult:
        """Dispatch to the correct checker based on rule_type."""
        dispatch = {
            "null_check": self._check_null,
            "type_check": self._check_type,
            "range_check": self._check_range,
            "uniqueness_check": self._check_uniqueness,
        }
        checker = dispatch.get(rule.rule_type)
        if checker is None:
            raise ValueError(f"Unknown rule type: {rule.rule_type}")

        failed_indexes, error_details = checker(
            col=rule.column_name,
            config=rule.rule_config or {},
        )

        return RuleResult(
            rule_id=rule.id,
            rule_type=rule.rule_type,
            column_name=rule.column_name,
            rows_checked=self.total_rows,
            failed_indexes=failed_indexes,
            error_details=error_details,
        )

    # ── The 4 rule checkers ───────────────────────────────────────────────────

    def _check_null(self, col: str, config: dict) -> tuple[list, list]:
        """
        Null check — fails rows where the column value is null, NaN,
        or an empty string after stripping whitespace.
        """
        series = self.df[col]
        null_mask = series.isnull()
        empty_mask = series.astype(str).str.strip() == ""
        combined_mask = null_mask | empty_mask

        failed_indexes = self.df[combined_mask].index.tolist()
        error_details = self._build_errors(
            failed_indexes, col, reason="null or empty value"
        )
        return failed_indexes, error_details

    def _check_type(self, col: str, config: dict) -> tuple[list, list]:
        """
        Type check — fails rows where the value cannot be converted to
        the expected_type specified in rule_config.

        Supported types: integer, float, string, boolean
        """
        expected_type = config.get("expected_type", "string")
        series = self.df[col]

        if expected_type == "integer":
            bad_mask = series.apply(
                lambda x: pd.isnull(x) or not str(x).strip().lstrip("-").isdigit()
            )
        elif expected_type == "float":
            numeric = pd.to_numeric(series, errors="coerce")
            bad_mask = numeric.isnull() & series.notna()
        elif expected_type == "boolean":
            valid_bools = {"true", "false", "1", "0", "yes", "no"}
            bad_mask = series.apply(
                lambda x: pd.isnull(x) or str(x).strip().lower() not in valid_bools
            )
        else:
            # "string" — every non-null value is a valid string
            bad_mask = series.isnull()

        failed_indexes = self.df[bad_mask].index.tolist()
        error_details = self._build_errors(
            failed_indexes, col, reason=f"expected type '{expected_type}'"
        )
        return failed_indexes, error_details

    def _check_range(self, col: str, config: dict) -> tuple[list, list]:
        """
        Range check — fails rows where the numeric value is outside
        [min, max] or cannot be converted to a number.

        Non-numeric values are coerced to NaN by pd.to_numeric and
        treated as range failures.
        """
        min_val = config.get("min")
        max_val = config.get("max")

        numeric = pd.to_numeric(self.df[col], errors="coerce")

        bad_mask = numeric.isnull()  # non-numeric values always fail
        if min_val is not None:
            bad_mask = bad_mask | (numeric < min_val)
        if max_val is not None:
            bad_mask = bad_mask | (numeric > max_val)

        failed_indexes = self.df[bad_mask].index.tolist()
        error_details = []

        for idx in failed_indexes[:MAX_ERROR_SAMPLES]:
            raw_val = self.df.at[idx, col]
            num_val = numeric.at[idx]

            if pd.isnull(num_val):
                reason = "not a valid number"
            elif min_val is not None and num_val < min_val:
                reason = f"below minimum ({min_val})"
            else:
                reason = f"above maximum ({max_val})"

            error_details.append(
                {"row": int(idx) + 1, "value": str(raw_val), "reason": reason}
            )

        return failed_indexes, error_details

    def _check_uniqueness(self, col: str, config: dict) -> tuple[list, list]:
        """
        Uniqueness check — fails ALL copies of any value that appears
        more than once. keep=False ensures both the first and subsequent
        occurrences are flagged, not just the duplicates.
        """
        # keep=False marks every occurrence of a duplicate value
        dup_mask = self.df[col].duplicated(keep=False)
        failed_indexes = self.df[dup_mask].index.tolist()
        error_details = self._build_errors(
            failed_indexes, col, reason="duplicate value"
        )
        return failed_indexes, error_details

    # ── Helper ────────────────────────────────────────────────────────────────

    def _build_errors(self, failed_indexes: list, col: str, reason: str) -> list:
        """Build up to MAX_ERROR_SAMPLES error detail dicts."""
        details = []
        for idx in failed_indexes[:MAX_ERROR_SAMPLES]:
            raw_val = self.df.at[idx, col]
            details.append(
                {
                    "row": int(idx) + 1,  # 1-indexed for human readability
                    "value": None if pd.isnull(raw_val) else str(raw_val),
                    "reason": reason,
                }
            )
        return details
