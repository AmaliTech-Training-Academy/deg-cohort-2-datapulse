"""
reports/migrations/0001_initial.py
────────────────────────────────────────────────────────────────────────────────
Moves QualityReport + RuleFinding ownership from checks → reports (state only,
no DB changes — the tables already exist from checks/0001_initial.py).

Creates the new trend_metrics table for real.
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("checks", "0001_initial"),
        ("datasets", "0001_initial"),
        ("rules", "0001_initial"),
    ]

    operations = [
        # ── State-only transfer ──────────────────────────────────────────────
        # quality_reports and rule_findings already exist as DB tables
        # (created by checks/0001_initial.py).  We update Django's ORM state
        # to move model ownership to this app without touching the database.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="QualityReport",
                    fields=[
                        (
                            "id",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("pending", "Pending"),
                                    ("running", "Running"),
                                    ("completed", "Completed"),
                                    ("failed", "Failed"),
                                ],
                                default="pending",
                                max_length=20,
                            ),
                        ),
                        ("overall_score", models.IntegerField(blank=True, null=True)),
                        (
                            "total_rows_passed",
                            models.IntegerField(blank=True, null=True),
                        ),
                        (
                            "total_rows_failed",
                            models.IntegerField(blank=True, null=True),
                        ),
                        ("error_message", models.TextField(blank=True)),
                        ("generated_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "dataset",
                            models.ForeignKey(
                                db_column="dataset_id",
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="reports",
                                to="datasets.dataset",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "quality_reports",
                        "ordering": ["-generated_at"],
                    },
                ),
                migrations.CreateModel(
                    name="RuleFinding",
                    fields=[
                        (
                            "id",
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ("rows_checked", models.IntegerField()),
                        ("rows_failed", models.IntegerField()),
                        ("failure_percentage", models.FloatField()),
                        ("error_details", models.JSONField(default=list)),
                        (
                            "quality_report",
                            models.ForeignKey(
                                db_column="report_id",
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="findings",
                                to="reports.qualityreport",
                            ),
                        ),
                        (
                            "rule",
                            models.ForeignKey(
                                db_column="rule_id",
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="findings",
                                to="rules.validationrule",
                            ),
                        ),
                    ],
                    options={"db_table": "rule_findings"},
                ),
            ],
            database_operations=[],
        ),
        # ── Real DB operation — create trend_metrics ─────────────────────────
        migrations.CreateModel(
            name="TrendMetric",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("snapshot_date", models.DateField()),
                ("aggregated_score", models.IntegerField()),
                (
                    "dataset",
                    models.ForeignKey(
                        db_column="dataset_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trend_metrics",
                        to="datasets.dataset",
                    ),
                ),
            ],
            options={
                "db_table": "trend_metrics",
                "ordering": ["snapshot_date"],
            },
        ),
        migrations.AddConstraint(
            model_name="trendmetric",
            constraint=models.UniqueConstraint(
                fields=["dataset", "snapshot_date"], name="unique_trend_per_day"
            ),
        ),
        migrations.AddIndex(
            model_name="trendmetric",
            index=models.Index(
                fields=["dataset", "snapshot_date"], name="idx_trend_dataset_date"
            ),
        ),
    ]
