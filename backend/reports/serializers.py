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
    """
    Per-dataset block returned by the dashboard endpoint.

    Includes all existing dataset fields plus a flattened latest_report
    summary.  trend is intentionally excluded — use GET /trends/ for
    chart data.

    Fields:
        dataset             — full dataset object (id, file_name, file_title,
                              description, file_type, row_count, columns,
                              file_version, created_at, updated_at)
        status              — quality band of the latest report
                              (healthy | warning | failing | null)
        latest_score        — overall_score from the most recent report (null
                              if no report exists)
        latest_score_date   — generated_at of the most recent report (null
                              if no report exists)
        latest_report       — full latest report summary block (id, status,
                              overall_score, total_rows_passed,
                              total_rows_failed, generated_at) or null
    """

    dataset = DatasetResponseSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    latest_score = serializers.SerializerMethodField()
    latest_score_date = serializers.SerializerMethodField()
    latest_report = serializers.SerializerMethodField()

    def get_status(self, obj) -> str | None:
        report = obj.get("latest_report")
        return report.status if report else None

    def get_latest_score(self, obj) -> int | None:
        report = obj.get("latest_report")
        return report.overall_score if report else None

    def get_latest_score_date(self, obj):
        report = obj.get("latest_report")
        return report.generated_at if report else None

    def get_latest_report(self, obj):
        report = obj.get("latest_report")
        if report is None:
            return None
        return {
            "id": str(report.id),
            "status": report.status,
            "overall_score": report.overall_score,
            "total_rows_passed": report.total_rows_passed,
            "total_rows_failed": report.total_rows_failed,
            "generated_at": report.generated_at,
        }


class DashboardSerializer(serializers.Serializer):
    """
    Top-level dashboard response.

    Fields:
        total_datasets          — total datasets owned by the user
        total_active_datasets   — datasets that have at least one quality report
        count                   — total items in the current filtered + paginated view
        next                    — URL of the next page (null on last page)
        previous                — URL of the previous page (null on first page)
        results                 — paginated list of DashboardDatasetSerializer blocks
    """

    total_datasets = serializers.IntegerField()
    total_active_datasets = serializers.IntegerField()
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = DashboardDatasetSerializer(many=True)
