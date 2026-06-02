"""
datasets/views.py
────────────────────────────────────────────────────────────────────────────────
DatasetUploadView   POST   /api/v1/datasets/
DatasetListView     GET    /api/v1/datasets/
DatasetDetailView   GET    /api/v1/datasets/<id>/
DatasetDeleteView   DELETE /api/v1/datasets/<id>/

MultiPartParser is declared on the upload view so DRF knows to expect a
multipart/form-data body. All other views use the default JSON parser.
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
from .serializers import DatasetResponseSerializer, DatasetUploadSerializer
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
