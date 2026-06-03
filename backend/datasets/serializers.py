"""
datasets/serializers.py
────────────────────────────────────────────────────────────────────────────────
DatasetUploadSerializer  — validates the multipart upload request
DatasetResponseSerializer — shapes the API response (never exposes file_path)
"""

from rest_framework import serializers

from .models import Dataset


class DatasetUploadSerializer(serializers.Serializer):
    """
    Validates the multipart/form-data upload request.

    file        — required, the CSV or JSON file
    file_title  — optional human-readable name
    description — optional notes
    """

    file = serializers.FileField(
        help_text="CSV or JSON file. Maximum 10 MB, 50,000 rows.",
    )
    file_title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class DatasetResponseSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for dataset API responses.
    file_path is intentionally excluded — it is an internal server path.
    """

    class Meta:
        model = Dataset
        fields = [
            "id",
            "file_name",
            "file_type",
            "file_title",
            "description",
            "row_count",
            "columns",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
