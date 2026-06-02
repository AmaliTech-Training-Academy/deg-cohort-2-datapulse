"""
checks/models.py
────────────────────────────────────────────────────────────────────────────────
QualityCheck — top-level record for one check run.
Maps to quality_reports + rule_findings tables in the schema.

The engine produces one QualityCheck per run, with nested RuleFindings
(one per rule). These are the same as quality_reports and rule_findings
in the schema — the checks app owns their creation.
"""

import uuid

from django.db import models


class QualityCheck(models.Model):
    """
    Mirrors quality_reports in the schema.
    Created by the check run endpoint. Updated by the engine when done.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="checks",
        db_column="dataset_id",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
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
            models.Index(fields=["dataset", "-generated_at"], name="idx_check_dataset"),
        ]

    def __str__(self):
        return f"Check {self.id} — {self.status} (score={self.overall_score})"


class RuleFinding(models.Model):
    """Mirrors rule_findings in the schema. One per rule per check run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quality_check = models.ForeignKey(
        QualityCheck,
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
            models.Index(fields=["quality_check"], name="idx_finding_check"),
        ]

    def __str__(self):
        return f"Finding rule={self.rule_id} failed={self.rows_failed}"
