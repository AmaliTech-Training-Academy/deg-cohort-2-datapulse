"""
rules/models.py
────────────────────────────────────────────────────────────────────────────────
ValidationRule — one rule per column per rule type per dataset.

rule_config stores rule-type-specific parameters as JSON:
    null_check:       {}
    type_check:       {"expected_type": "integer"}
    range_check:      {"min": 0, "max": 120}
    uniqueness_check: {}

A UniqueConstraint on (dataset, column_name, rule_type) prevents
duplicates — the same check on the same column cannot be added twice.
"""

import uuid

from django.db import models


class ValidationRule(models.Model):

    class RuleType(models.TextChoices):
        NULL_CHECK = "null_check", "Null Check"
        TYPE_CHECK = "type_check", "Type Check"
        RANGE_CHECK = "range_check", "Range Check"
        UNIQUENESS_CHECK = "uniqueness_check", "Uniqueness Check"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="rules",
        db_column="dataset_id",
    )
    column_name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=30, choices=RuleType.choices)
    rule_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "validation_rules"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "column_name", "rule_type"],
                name="unique_rule_per_column_type",
            )
        ]
        indexes = [
            models.Index(fields=["dataset"], name="idx_rule_dataset"),
        ]

    def __str__(self):
        return f"{self.rule_type} on '{self.column_name}'"
