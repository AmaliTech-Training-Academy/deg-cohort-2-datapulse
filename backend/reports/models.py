"""
reports/models.py
────────────────────────────────────────────────────────────────────────────────
QualityReport  — one record per check run  (db: quality_reports)
RuleFinding    — one record per rule per run (db: rule_findings)
TrendMetric    — daily quality snapshot per dataset (db: trend_metrics)

QualityReport and RuleFinding were originally scaffolded in the checks app.
They are owned here (reports app) because report generation, retrieval,
and trend tracking are Backend Developer 2 deliverables.

The checks app still owns the RunCheckView that triggers a run and writes
to these tables — it imports from this module.

QualityReport.status values:
    healthy  — check completed, overall_score > 85
    warning  — check completed, 70 < overall_score ≤ 85
    failing  — check completed, overall_score ≤ 70
"""

import uuid

from django.db import models


class QualityReport(models.Model):

    class Status(models.TextChoices):
        HEALTHY = "healthy", "Healthy"  # score > 85
        WARNING = "warning", "Warning"  # 70 < score ≤ 85
        FAILING = "failing", "Failing"  # score ≤ 70

    # Thresholds used by RunCheckView to derive the status from the score
    HEALTHY_THRESHOLD = 85
    WARNING_THRESHOLD = 70

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="reports",
        db_column="dataset_id",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.FAILING,
    )
    overall_score = models.IntegerField(null=True, blank=True)
    total_rows_passed = models.IntegerField(null=True, blank=True)
    total_rows_failed = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quality_reports"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(
                fields=["dataset", "-generated_at"], name="idx_report_dataset"
            ),
        ]

    def __str__(self):
        return f"Report {self.id} — {self.status} (score={self.overall_score})"

    @classmethod
    def status_from_score(cls, score: int) -> str:
        """Derive the quality status from a completed overall_score."""
        if score > cls.HEALTHY_THRESHOLD:
            return cls.Status.HEALTHY
        if score > cls.WARNING_THRESHOLD:
            return cls.Status.WARNING
        return cls.Status.FAILING


class RuleFinding(models.Model):
    """One finding per rule per report run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quality_report = models.ForeignKey(
        QualityReport,
        on_delete=models.CASCADE,
        related_name="findings",
        db_column="report_id",
    )
    rule = models.ForeignKey(
        "rules.ValidationRule",
        on_delete=models.CASCADE,
        related_name="findings",
        db_column="rule_id",
    )
    rows_checked = models.IntegerField()
    rows_failed = models.IntegerField()
    failure_percentage = models.FloatField()
    error_details = models.JSONField(default=list)

    class Meta:
        db_table = "rule_findings"
        indexes = [
            models.Index(fields=["quality_report"], name="idx_finding_report"),
        ]

    def __str__(self):
        return f"Finding rule={self.rule_id} failed={self.rows_failed}"


class TrendMetric(models.Model):
    """
    One row per dataset per day — the quality score snapshot for that day.
    Upserted by the check runner after every successful run.
    Powers the trend chart on the dashboard.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="trend_metrics",
        db_column="dataset_id",
    )
    snapshot_date = models.DateField()
    aggregated_score = models.IntegerField()

    class Meta:
        db_table = "trend_metrics"
        ordering = ["snapshot_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "snapshot_date"],
                name="unique_trend_per_day",
            )
        ]
        indexes = [
            models.Index(
                fields=["dataset", "snapshot_date"], name="idx_trend_dataset_date"
            ),
        ]

    def __str__(self):
        return f"Trend {self.dataset_id} {self.snapshot_date} score={self.aggregated_score}"
