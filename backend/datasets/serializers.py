"""
datasets/serializers.py
────────────────────────────────────────────────────────────────────────────────
DatasetUploadSerializer          — validates the multipart upload request
DatasetResponseSerializer        — shapes the API response (never exposes file_path)
DatasetMetadataUpdateSerializer  — validates PATCH body for metadata-only update
DatasetFileUpdateSerializer      — validates multipart file replacement request
DatasetFileReplaceResponseSerializer — file replacement response with stale_rule_columns
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
            "file_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DatasetMetadataUpdateSerializer(serializers.Serializer):
    """
    Validates the JSON body for PATCH /api/v1/datasets/<id>/.

    Both fields are optional individually — but at least one must be provided.
    Omitted fields are left unchanged on the dataset record.

    file_title   — human-readable name (max 255 chars)
    description  — freeform notes
    """

    file_title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field (file_title or description) must be provided."
            )
        return attrs


class DatasetFileUpdateSerializer(serializers.Serializer):
    """
    Validates the multipart/form-data body for PATCH /api/v1/datasets/<id>/file/.

    Only the file itself is required — title and description are left unchanged
    unless the client explicitly includes them.
    """

    file = serializers.FileField(
        help_text="Replacement CSV or JSON file. Maximum 10 MB, 50,000 rows.",
    )


class DatasetFileReplaceResponseSerializer(serializers.ModelSerializer):
    """
    Response shape for a successful file replacement.

    Adds stale_rule_columns — the list of column names that existed in the
    previous file but are absent from the new one.  Any ValidationRule
    targeting one of these columns will no longer match a real column and
    should be reviewed or deleted before the next run-check.
    """

    stale_rule_columns = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text=(
            "Column names from the previous file that no longer exist in the "
            "new file. ValidationRules targeting these columns should be "
            "reviewed before running the next quality check."
        ),
    )

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
            "file_version",
            "stale_rule_columns",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
