import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("datasets", "0001_initial"),
        ("rules", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="QualityCheck",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("overall_score", models.IntegerField(blank=True, null=True)),
                ("total_rows_passed", models.IntegerField(blank=True, null=True)),
                ("total_rows_failed", models.IntegerField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("dataset", models.ForeignKey(db_column="dataset_id", on_delete=django.db.models.deletion.CASCADE, related_name="checks", to="datasets.dataset")),
            ],
            options={
                "db_table": "quality_reports",
                "ordering": ["-generated_at"],
            },
        ),
        migrations.CreateModel(
            name="RuleFinding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("rows_checked", models.IntegerField()),
                ("rows_failed", models.IntegerField()),
                ("failure_percentage", models.FloatField()),
                ("error_details", models.JSONField(default=list)),
                ("quality_check", models.ForeignKey(db_column="report_id", on_delete=django.db.models.deletion.CASCADE, related_name="findings", to="checks.qualitycheck")),
                ("rule", models.ForeignKey(db_column="rule_id", on_delete=django.db.models.deletion.CASCADE, related_name="findings", to="rules.validationrule")),
            ],
            options={
                "db_table": "rule_findings",
            },
        ),
        migrations.AddIndex(
            model_name="qualitycheck",
            index=models.Index(fields=["dataset", "-generated_at"], name="idx_check_dataset"),
        ),
        migrations.AddIndex(
            model_name="rulefinding",
            index=models.Index(fields=["quality_check"], name="idx_finding_check"),
        ),
    ]