"""
datasets/views.py
────────────────────────────────────────────────────────────────────────────────
DatasetUploadView      POST   /api/v1/datasets/upload/
DatasetListView        GET    /api/v1/datasets/
DatasetDetailView      GET    /api/v1/datasets/<id>/
DatasetDetailView      PATCH  /api/v1/datasets/<id>/
DatasetDetailView      DELETE /api/v1/datasets/<id>/
DatasetFileUpdateView  PATCH  /api/v1/datasets/<id>/file/

MultiPartParser is declared on upload and file-update views so DRF knows to
expect a multipart/form-data body. All other views use the default JSON parser.
DatasetDetailView.patch accepts JSON (default parser) — no file involved.
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dataset
from .serializers import (
    DatasetFileReplaceResponseSerializer,
    DatasetFileUpdateSerializer,
    DatasetMetadataUpdateSerializer,
    DatasetResponseSerializer,
    DatasetUploadSerializer,
)
from .services.file_service import FileUploadService

logger = logging.getLogger(__name__)


class DatasetUploadView(APIView):
    """
    POST /api/v1/datasets/

    Accepts multipart/form-data with:
        file        (required) — CSV or JSON file
        file_title  (optional) — human-readable name
        description (optional) — notes

    Returns 201 with the created Dataset object.

    MultiPartParser + FormParser together handle both file fields and
    regular text fields in the same multipart request.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "CSV or JSON file to upload",
                    },
                    "file_title": {
                        "type": "string",
                        "description": "Human-readable name (optional)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Notes about this dataset (optional)",
                    },
                },
                "required": ["file"],
            }
        },
        responses={201: DatasetResponseSerializer},
        summary="Upload a CSV or JSON dataset",
        description=(
            "Upload a CSV or JSON file for validation. "
            "File size limit: 10MB. Row limit: 50,000."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = DatasetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = FileUploadService()
        dataset, _df = service.upload(
            file=serializer.validated_data["file"],
            user=request.user,
            file_title=serializer.validated_data.get("file_title", ""),
            description=serializer.validated_data.get("description", ""),
        )

        return Response(
            DatasetResponseSerializer(dataset).data,
            status=status.HTTP_201_CREATED,
        )


class DatasetListView(APIView):
    """
    GET /api/v1/datasets/

    Returns all datasets belonging to the authenticated user,
    most recent first.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DatasetResponseSerializer(many=True)},
        summary="List all datasets for the authenticated user",
    )
    def get(self, request: Request) -> Response:
        datasets = Dataset.objects.filter(user=request.user).order_by("-created_at")
        serializer = DatasetResponseSerializer(datasets, many=True)
        return Response(serializer.data)


class DatasetDetailView(APIView):
    """
    GET    /api/v1/datasets/<id>/
    PATCH  /api/v1/datasets/<id>/
    DELETE /api/v1/datasets/<id>/
    """

    permission_classes = [IsAuthenticated]

    def _get_dataset(self, dataset_id: str, user) -> Dataset:
        try:
            return Dataset.objects.get(id=dataset_id, user=user)
        except Dataset.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound("Dataset not found.")

    @extend_schema(
        responses={200: DatasetResponseSerializer},
        summary="Retrieve a dataset by ID",
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = self._get_dataset(dataset_id, request.user)
        return Response(DatasetResponseSerializer(dataset).data)

    @extend_schema(
        request=DatasetMetadataUpdateSerializer,
        responses={200: DatasetResponseSerializer},
        summary="Update dataset metadata",
        description=(
            "Update file_title and/or description for an existing dataset. "
            "At least one field must be provided. "
            "File content, columns, row_count, and file_version are not affected."
        ),
    )
    def patch(self, request: Request, dataset_id: str) -> Response:
        dataset = self._get_dataset(dataset_id, request.user)

        serializer = DatasetMetadataUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Only update the fields that were explicitly sent
        if "file_title" in serializer.validated_data:
            dataset.file_title = serializer.validated_data["file_title"]
        if "description" in serializer.validated_data:
            dataset.description = serializer.validated_data["description"]

        dataset.save(update_fields=["file_title", "description", "updated_at"])

        logger.info(
            "Dataset metadata updated: id=%s user=%s fields=%s",
            dataset_id,
            request.user.email,
            list(serializer.validated_data.keys()),
        )

        return Response(DatasetResponseSerializer(dataset).data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={204: None},
        summary="Delete a dataset and remove its file from disk",
    )
    def delete(self, request: Request, dataset_id: str) -> Response:
        dataset = self._get_dataset(dataset_id, request.user)

        # Remove the physical file from disk before deleting the record
        service = FileUploadService()
        service._remove_file(dataset.file_path)

        dataset.delete()

        logger.info("Dataset deleted: id=%s user=%s", dataset_id, request.user.email)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DatasetFileUpdateView(APIView):
    """
    PATCH /api/v1/datasets/<id>/file/

    Replace the physical file for an existing dataset while preserving its
    full QualityReport history.  All prior reports remain attached to the
    same dataset.id — the score history is never lost.

    What changes after a successful replacement:
        file_name     — original filename of the new upload
        file_type     — re-detected from content (csv | json)
        row_count     — row count of the new file
        columns       — column list of the new file
        file_version  — incremented by 1 (starts at 1 on original upload)
        updated_at    — set to now

    What stays the same:
        id            — same UUID, all FK relationships preserved
        file_title    — unchanged (the human-readable name the user gave)
        description   — unchanged
        all QualityReport / RuleFinding / TrendMetric rows

    Response includes stale_rule_columns — any column names that existed in
    the previous file but are absent from the new one.  ValidationRules
    targeting those columns will no longer match a real column and should be
    reviewed or deleted before the next run-check call.

    Returns 200 on success, 400 on file validation failure, 404 if the
    dataset does not belong to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Replacement CSV or JSON file",
                    },
                },
                "required": ["file"],
            }
        },
        responses={200: DatasetFileReplaceResponseSerializer},
        summary="Replace the file for an existing dataset",
        description=(
            "Upload a new CSV or JSON file to replace the current one. "
            "All previous quality reports and scores are preserved. "
            "file_version is incremented. "
            "stale_rule_columns in the response lists any columns from the "
            "old file that no longer exist in the new file — review those "
            "validation rules before running the next quality check."
        ),
    )
    def patch(self, request: Request, dataset_id: str) -> Response:
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=request.user)
        except Dataset.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound("Dataset not found.")

        serializer = DatasetFileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = FileUploadService()
        dataset, _df, stale_columns = service.replace(
            dataset=dataset,
            file=serializer.validated_data["file"],
        )

        response_data = DatasetFileReplaceResponseSerializer(dataset).data
        # stale_rule_columns is not a model field — inject it into the response
        response_data["stale_rule_columns"] = stale_columns

        logger.info(
            "Dataset file updated: id=%s user=%s version=%d",
            dataset_id,
            request.user.email,
            dataset.file_version,
        )

        return Response(response_data, status=status.HTTP_200_OK)
