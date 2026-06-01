"""
checks/serializers.py
────────────────────────────────────────────────────────────────────────────────
RuleFindingSerializer  — per-rule results nested inside check response
QualityCheckSerializer — full check run response
"""

from rest_framework import serializers

from .models import QualityCheck, RuleFinding


class RuleFindingSerializer(serializers.ModelSerializer):
    rule_type = serializers.CharField(source="rule.rule_type", read_only=True)
    column_name = serializers.CharField(source="rule.column_name", read_only=True)

    class Meta:
        model = RuleFinding
        fields = [
            "id",
            "rule",
            "rule_type",
            "column_name",
            "rows_checked",
            "rows_failed",
            "failure_percentage",
            "error_details",
        ]
        read_only_fields = fields


class QualityCheckSerializer(serializers.ModelSerializer):
    findings = RuleFindingSerializer(many=True, read_only=True)

    class Meta:
        model = QualityCheck
        fields = [
            "id",
            "dataset",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "findings",
            "error_message",
            "generated_at",
        ]
        read_only_fields = fields
