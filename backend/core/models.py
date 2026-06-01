"""
core/models.py
────────────────────────────────────────────────────────────────────────────────
Shared abstract base models.

TimeStampedModel
    Every concrete model in DataPulse should inherit from this.
    It automatically adds created_at and updated_at timestamps.

Usage:
    from core.models import TimeStampedModel

    class Dataset(TimeStampedModel):
        name = models.CharField(max_length=255)
        # created_at and updated_at are inherited automatically
"""

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base class that adds created_at and updated_at to any model.

    Both fields are managed automatically:
        created_at  — set once when the record is first saved
        updated_at  — updated on every subsequent save
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated.",
    )

    class Meta:
        abstract = True
        # Default ordering: most recently created first
        ordering = ["-created_at"]
