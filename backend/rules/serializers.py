"""
rules/serializers.py
────────────────────────────────────────────────────────────────────────────────
ValidationRuleSerializer  — create and read rules
RuleUpdateSerializer      — update rule_config only (type and column are immutable)

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


class RuleUpdateSerializer(serializers.ModelSerializer):
    """
    Only rule_config can be updated — column_name and rule_type are
    immutable once created to preserve the integrity of past findings.
    """

    class Meta:
        model = ValidationRule
        fields = ["rule_config"]
