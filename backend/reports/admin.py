from django.contrib import admin

from .models import QualityReport, RuleFinding, TrendMetric


@admin.register(QualityReport)
class QualityReportAdmin(admin.ModelAdmin):
    list_display = ["id", "dataset", "status", "overall_score", "generated_at"]
    list_filter = ["status"]
    readonly_fields = ["id", "generated_at"]


@admin.register(RuleFinding)
class RuleFindingAdmin(admin.ModelAdmin):
    list_display = ["id", "quality_report", "rule", "rows_failed", "failure_percentage"]
    readonly_fields = ["id"]


@admin.register(TrendMetric)
class TrendMetricAdmin(admin.ModelAdmin):
    list_display = ["dataset", "snapshot_date", "aggregated_score"]
    list_filter = ["snapshot_date"]
