"""
datasets/models.py
────────────────────────────────────────────────────────────────────────────────
Dataset model — matches the 'datasets' table in the project schema.

Stores metadata extracted from the uploaded file. The physical file lives at:
    MEDIA_ROOT/uploads/<user_id>/<uuid>.<ext>

file_path is never returned in API responses — it is an internal server path.
"""

import uuid

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Dataset(TimeStampedModel):

    class FileType(models.TextChoices):
        CSV = "csv", "CSV"
        JSON = "json", "JSON"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="datasets",
        db_column="user_id",
    )
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_path = models.CharField(max_length=500)
    row_count = models.IntegerField(null=True, blank=True)
    columns = models.JSONField(default=list, blank=True)
    file_title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "datasets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"], name="idx_dataset_user_created"
            ),
        ]

    def __str__(self):
        return f"{self.file_title or self.file_name} ({self.file_type})"
