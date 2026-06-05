"""
rules/serializers.py
────────────────────────────────────────────────────────────────────────────────
ValidationRuleSerializer    — create and read rules (also used for POST response)
RuleListItemSerializer      — enriched rule row for GET list (adds per-rule stats)
RuleListSerializer          — full GET list envelope with dataset-level row/score summary
RuleUpdateSerializer        — update rule_config only (type and column are immutable)

Validation rules:
  - column_name must exist in dataset.columns at time of creation
  - rule_config must contain the required keys for each rule_type
  - Duplicate (dataset, column_name, rule_type) returns 409 via the
    UniqueConstraint — caught in the view
"""

from rest_framework import serializers

from .models import ValidationRule

REQUIRED_CONFIG_KEYS = {
    "null_check": [],
    "type_check": ["expected_type"],
    "range_check": ["min", "max"],
    "uniqueness_check": [],
}

VALID_EXPECTED_TYPES = ["integer", "float", "string", "boolean"]


class ValidationRuleSerializer(serializers.ModelSerializer):
    """Used for both creating rules and returning them in responses."""

    class Meta:
        model = ValidationRule
        fields = [
            "id",
            "dataset",
            "column_name",
            "rule_type",
            "rule_config",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        # Disable the auto-generated UniqueTogetherValidator so that duplicate
        # (dataset, column_name, rule_type) combinations are caught by the DB
        # IntegrityError in the view, which returns the proper 409 response.
        validators = []

    def validate(self, attrs):
        rule_type = attrs.get("rule_type")
        rule_config = attrs.get("rule_config", {})
        column_name = attrs.get("column_name", "")
        dataset = attrs.get("dataset")

        # 1. Column must exist in the dataset
        if dataset and column_name not in (dataset.columns or []):
            available = ", ".join(dataset.columns or [])
            raise serializers.ValidationError(
                {
                    "column_name": (
                        f"Column '{column_name}' not found in dataset. "
                        f"Available columns: {available}"
                    )
                }
            )

        # 2. rule_config must contain required keys
        required = REQUIRED_CONFIG_KEYS.get(rule_type, [])
        for key in required:
            if key not in rule_config:
                raise serializers.ValidationError(
                    {"rule_config": f"'{key}' is required for {rule_type}."}
                )

        # 3. type_check — expected_type must be a supported value
        if rule_type == "type_check":
            et = rule_config.get("expected_type", "")
            if et not in VALID_EXPECTED_TYPES:
                raise serializers.ValidationError(
                    {
                        "rule_config": (
                            f"expected_type must be one of: "
                            f"{', '.join(VALID_EXPECTED_TYPES)}. Got '{et}'."
                        )
                    }
                )

        # 4. range_check — min must be less than max
        if rule_type == "range_check":
            min_val = rule_config.get("min")
            max_val = rule_config.get("max")
            if min_val is not None and max_val is not None and min_val >= max_val:
                raise serializers.ValidationError(
                    {"rule_config": "'min' must be less than 'max'."}
                )

        return attrs


class RuleListItemSerializer(serializers.ModelSerializer):
    """
    Enriched rule row returned by GET /api/v1/datasets/<id>/rules/.

    Adds per-rule performance stats computed from all RuleFinding records
    across every quality check run for this rule:

        last_failing_rows   — rows_failed from the most recent finding for
                              this rule (null if the rule has never been run)
        last_passing_rows   — rows_checked - rows_failed from the most recent
                              finding (null if never run)
        average_score       — average pass rate across all findings for this
                              rule, rounded to nearest integer (0–100).
                              Formula: avg(100 - failure_percentage)
                              null if the rule has never been run.

    All existing ValidationRuleSerializer fields are preserved:
        id, dataset, column_name, rule_type, rule_config, created_at
    """

    last_failing_rows = serializers.SerializerMethodField()
    last_passing_rows = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()

    class Meta:
        model = ValidationRule
        fields = [
            "id",
            "dataset",
            "column_name",
            "rule_type",
            "rule_config",
            "created_at",
            "last_failing_rows",
            "last_passing_rows",
            "average_score",
        ]
        read_only_fields = fields

    def _latest_finding(self, obj):
        """Return the most recent RuleFinding for this rule, or None."""
        # findings are ordered by -generated_at on QualityReport, but
        # RuleFinding has no direct timestamp — proxy via quality_report
        return (
            obj.findings.select_related("quality_report")
            .order_by("-quality_report__generated_at")
            .first()
        )

    def get_last_failing_rows(self, obj) -> int | None:
        finding = self._latest_finding(obj)
        return finding.rows_failed if finding else None

    def get_last_passing_rows(self, obj) -> int | None:
        finding = self._latest_finding(obj)
        if finding is None:
            return None
        return finding.rows_checked - finding.rows_failed

    def get_average_score(self, obj) -> int | None:
        rates = [100.0 - f.failure_percentage for f in obj.findings.all()]
        if not rates:
            return None
        return round(sum(rates) / len(rates))


class RuleListSerializer(serializers.Serializer):
    """
    Full envelope returned by GET /api/v1/datasets/<id>/rules/.

    Dataset-level summary (computed from ALL findings across all runs,
    unaffected by filters or pagination):

        total_failing_rows  — sum of rows_failed across every finding ever
                              recorded for this dataset's rules
        total_passing_rows  — sum of (rows_checked - rows_failed) across every
                              finding (i.e. rows that passed a rule check)
        rule_type_scores    — per-rule-type average pass rate (0–100) across
                              all findings of that type.  Always includes all
                              4 keys; null when no findings of that type exist.
                              Example:
                              {
                                "null_check":       92,
                                "type_check":       100,
                                "range_check":      75,
                                "uniqueness_check": null
                              }

    Pagination envelope (reflects current filtered + paginated view):
        count      — total items matching filters
        next       — URL of next page (null on last page)
        previous   — URL of previous page (null on first page)
        results    — list of RuleListItemSerializer objects
    """

    total_failing_rows = serializers.IntegerField()
    total_passing_rows = serializers.IntegerField()
    rule_type_scores = serializers.DictField(
        child=serializers.IntegerField(allow_null=True)
    )
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    # pre-serialized dicts from RuleListItemSerializer
    results = serializers.ListField(child=serializers.DictField())


class RuleUpdateSerializer(serializers.ModelSerializer):
    """
    Only rule_config can be updated — column_name and rule_type are
    immutable once created to preserve the integrity of past findings.
    """

    class Meta:
        model = ValidationRule
        fields = ["rule_config"]
