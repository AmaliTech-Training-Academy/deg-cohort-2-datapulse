"""
datasets/serializers.py
────────────────────────────────────────────────────────────────────────────────
DatasetUploadSerializer          — validates the multipart upload request
DatasetResponseSerializer        — shapes the API response (never exposes file_path)
DatasetMetadataUpdateSerializer  — validates PATCH body for metadata-only update
DatasetFileUpdateSerializer      — validates multipart file replacement request
DatasetFileReplaceResponseSerializer — file replacement response with stale_rule_columns
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Dataset

User = get_user_model()


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


class DatasetOwnerSerializer(serializers.ModelSerializer):
    """Minimal user info embedded in admin dataset responses."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class AdminDatasetResponseSerializer(DatasetResponseSerializer):
    """
    Extends DatasetResponseSerializer with owner info and latest report summary.
    Used by DatasetListView when the authenticated user has role='admin'.
    Field names match the real model fields on Dataset and QualityReport.
    """

    user = DatasetOwnerSerializer(read_only=True)
    reports_count = serializers.IntegerField(read_only=True)
    # latest_report groups the three QualityReport fields under one key so
    # the frontend knows they belong to the most recent check run.
    latest_report = serializers.SerializerMethodField()

    class Meta(DatasetResponseSerializer.Meta):
        fields = DatasetResponseSerializer.Meta.fields + [
            "user",
            "reports_count",
            "latest_report",
        ]
        read_only_fields = fields

    def get_latest_report(self, obj):
        # ann_* values are annotated by AdminDatasetListView.get_queryset()
        if obj.ann_status is None and obj.ann_overall_score is None:
            return None
        return {
            "overall_score": obj.ann_overall_score,
            "status": obj.ann_status,
            "generated_at": obj.ann_generated_at,
        }


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
