"""
reports/serializers.py
────────────────────────────────────────────────────────────────────────────────
RuleFindingSerializer    — per-rule results nested inside a report
QualityReportSerializer  — full report response (used by run-check + report API)
TrendMetricSerializer    — single trend point (date + score)
DashboardDatasetSerializer — per-dataset summary for the dashboard
DashboardSerializer        — top-level dashboard response
"""

from rest_framework import serializers

from datasets.serializers import DatasetResponseSerializer

from .models import QualityReport, RuleFinding, TrendMetric


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


class QualityReportSerializer(serializers.ModelSerializer):
    findings = RuleFindingSerializer(many=True, read_only=True)

    class Meta:
        model = QualityReport
        fields = [
            "id",
            "dataset",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "error_message",
            "findings",
            "generated_at",
        ]
        read_only_fields = fields


class TrendMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendMetric
        fields = ["snapshot_date", "aggregated_score"]
        read_only_fields = fields


class DashboardDatasetSerializer(serializers.Serializer):
    """Per-dataset block returned by the dashboard endpoint."""

    dataset = DatasetResponseSerializer(read_only=True)
    latest_report = serializers.SerializerMethodField()
    trend = TrendMetricSerializer(many=True, read_only=True)

    def get_latest_report(self, obj):
        report = obj.get("latest_report")
        if report is None:
            return None
        return {
            "id": str(report.id),
            "status": report.status,
            "overall_score": report.overall_score,
            "generated_at": report.generated_at,
        }


class DashboardSerializer(serializers.Serializer):
    """Top-level dashboard response."""

    total_datasets = serializers.IntegerField()
    datasets = DashboardDatasetSerializer(many=True)
