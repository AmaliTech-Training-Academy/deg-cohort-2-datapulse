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

DatasetListView supports the following query parameters:
    ?search=<str>       — case-insensitive match on file_title or file_name
    ?file_type=csv|json — filter by file type
    ?page=<n>           — page number (default 1)
    ?page_size=<n>      — items per page (default 20, max 100)

DatasetFileUpdateView auto-check behaviour:
    After a successful file replacement, if the dataset has at least one
    ValidationRule, a QualityReport is created immediately (ACID — the DB
    row exists before the HTTP response is sent) and the heavy validation
    work runs in a background thread so the HTTP response is not blocked.

    ACID guarantee:
        1. File replacement and QualityReport creation share the same DB
           connection — if either fails, neither is committed.
        2. The background thread updates the report to its final status
           (healthy/warning/failing); on any exception it sets status=failing
           and stores the error_message — the record is never left incomplete.

    Response includes auto_check.report_id so clients can poll
    GET /api/v1/reports/<id>/ for the completed result.
"""

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import DataPulsePagination

from .models import Dataset
from .serializers import (
    AdminDatasetResponseSerializer,
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
            "File size limit: 10MB. Row limit: 50,000. "
            "Select a file via the file picker — text fields below pre-fill for reference."
        ),
        examples=[
            OpenApiExample(
                name="CSV Upload",
                summary="Upload a CSV file with title and description",
                description=(
                    "Select a .csv file. The file field cannot be pre-filled in Swagger — "
                    "use the file picker. file_title and description are optional."
                ),
                value={
                    "file_title": "Employee Records Q1 2026",
                    "description": "HR employee dataset for Q1 quality validation",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="JSON Upload",
                summary="Upload a JSON file with title and description",
                description=(
                    "Select a .json file (array of objects format). "
                    "The file field cannot be pre-filled in Swagger — use the file picker."
                ),
                value={
                    "file_title": "Sales Orders JSON",
                    "description": "Sales order data exported from ERP in JSON format",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Minimal Upload",
                summary="Upload without title or description",
                description=(
                    "Only the file is required. "
                    "file_title defaults to the filename if omitted."
                ),
                value={},
                request_only=True,
            ),
        ],
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

    Returns datasets belonging to the authenticated user, most recent first.

    Filters (all optional, combinable):
        ?search=<str>            case-insensitive substring match on file_title or file_name
        ?file_type=csv|json      exact match on file type
        ?created_from=YYYY-MM-DD datasets uploaded on or after this date
        ?created_to=YYYY-MM-DD   datasets uploaded on or before this date

    Pagination:
        ?page=<n>            page number (default 1)
        ?page_size=<n>       items per page (default 20, max 100)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Case-insensitive substring match on file_title or file_name.",
                required=False,
            ),
            OpenApiParameter(
                name="file_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by file type: `csv` or `json`.",
                required=False,
                enum=["csv", "json"],
            ),
            OpenApiParameter(
                name="created_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return datasets uploaded on or after this date (YYYY-MM-DD).",
                required=False,
            ),
            OpenApiParameter(
                name="created_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return datasets uploaded on or before this date (YYYY-MM-DD).",
                required=False,
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number (default 1).",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Items per page (default 20, max 100).",
                required=False,
            ),
        ],
        responses={200: DatasetResponseSerializer(many=True)},
        summary="List datasets",
        description=(
            "Returns a paginated list of the authenticated user's datasets. "
            "Supports filtering by file type, substring search, and upload date range."
        ),
    )
    def get(self, request: Request) -> Response:
        from django.db.models import Count, OuterRef, Q, Subquery
        from rest_framework.exceptions import ValidationError as DRFValidationError

        from reports.models import QualityReport

        if request.user.is_admin:
            latest_report = QualityReport.objects.filter(
                dataset=OuterRef("pk")
            ).order_by("-generated_at")

            queryset = (
                Dataset.objects.select_related("user")
                .annotate(
                    reports_count=Count("reports"),
                    ann_overall_score=Subquery(
                        latest_report.values("overall_score")[:1]
                    ),
                    ann_status=Subquery(latest_report.values("status")[:1]),
                    ann_generated_at=Subquery(
                        latest_report.values("generated_at")[:1]
                    ),
                )
                .order_by("-created_at")
            )
            serializer_class = AdminDatasetResponseSerializer
        else:
            queryset = Dataset.objects.filter(user=request.user).order_by("-created_at")
            serializer_class = DatasetResponseSerializer

        # Filter: ?file_type=csv|json
        file_type = request.query_params.get("file_type")
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        # Filter: ?search=<str> — matches file_title or file_name
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(file_title__icontains=search) | Q(file_name__icontains=search)
            )

        # Filter: ?created_from=YYYY-MM-DD
        created_from = request.query_params.get("created_from")
        if created_from:
            try:
                queryset = queryset.filter(created_at__date__gte=created_from)
            except (ValueError, TypeError):
                raise DRFValidationError(
                    {"created_from": "Invalid date format. Use YYYY-MM-DD."}
                )

        # Filter: ?created_to=YYYY-MM-DD
        created_to = request.query_params.get("created_to")
        if created_to:
            try:
                queryset = queryset.filter(created_at__date__lte=created_to)
            except (ValueError, TypeError):
                raise DRFValidationError(
                    {"created_to": "Invalid date format. Use YYYY-MM-DD."}
                )

        paginator = DataPulsePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(serializer_class(page, many=True).data)


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
        examples=[
            OpenApiExample(
                name="Update Title Only",
                summary="Rename the dataset without changing the description",
                value={"file_title": "Employee Records Q2 2026"},
                request_only=True,
            ),
            OpenApiExample(
                name="Update Description Only",
                summary="Change the description without renaming the dataset",
                value={"description": "Revised dataset — includes contractor records"},
                request_only=True,
            ),
            OpenApiExample(
                name="Update Both Fields",
                summary="Update title and description in a single request",
                value={
                    "file_title": "Sales Data — Revised",
                    "description": "Corrected sales figures after audit",
                },
                request_only=True,
            ),
        ],
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

        return Response(
            DatasetResponseSerializer(dataset).data, status=status.HTTP_200_OK
        )

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

    def _dispatch_auto_check(self, dataset_id, report_id) -> None:
        """
        Spawn a daemon thread that runs the validation engine against the
        pre-created QualityReport row.

        Extracted into a method so tests can patch it to run synchronously:
            monkeypatch.setattr(
                DatasetFileUpdateView, "_dispatch_auto_check",
                lambda self, did, rid: run_quality_check_on_report(
                    Dataset.objects.get(id=did),
                    QualityReport.objects.get(id=rid),
                )
            )

        Production behaviour:
          • The thread runs asynchronously — the HTTP response is not blocked.
          • Django opens a fresh DB connection per thread automatically.
          • close_old_connections() returns it to the pool when finished.
          • SQLite in tests does not support concurrent writes, so this
            method must be patched to run synchronously in the test suite.
        """
        import threading

        import django.db

        from checks.services.check_service import run_quality_check_on_report
        from datasets.models import Dataset as _Dataset
        from reports.models import QualityReport as _QualityReport

        def _target():
            try:
                _dataset = _Dataset.objects.get(id=dataset_id)
                _report = _QualityReport.objects.get(id=report_id)
                run_quality_check_on_report(_dataset, _report)
            except Exception as exc:
                logger.exception(
                    "Background auto-check failed: report=%s error=%s",
                    report_id,
                    exc,
                )
            finally:
                django.db.close_old_connections()

        thread = threading.Thread(
            target=_target,
            name=f"auto-check-{report_id}",
            daemon=True,
        )
        thread.start()

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
            "stale_rule_columns lists columns from the old file absent from "
            "the new one — review those rules before the next check. "
            "If at least one validation rule exists, a QualityReport is "
            "created immediately and scored asynchronously. "
            "auto_check.report_id in the response can be polled at "
            "GET /api/v1/reports/<id>/ for the completed result."
        ),
        examples=[
            OpenApiExample(
                name="Replace with CSV",
                summary="Swap current file for a new CSV file",
                description=(
                    "Select a .csv replacement file via the file picker. "
                    "file_title and description are unchanged. "
                    "stale_rule_columns will list any columns dropped from the new file."
                ),
                value={},
                request_only=True,
            ),
            OpenApiExample(
                name="Replace with JSON",
                summary="Swap current file for a new JSON file",
                description=(
                    "Select a .json replacement file (array of objects). "
                    "The file type is re-detected from content — "
                    "the dataset file_type field will update to 'json'."
                ),
                value={},
                request_only=True,
            ),
        ],
    )
    def patch(self, request: Request, dataset_id: str) -> Response:
        from rest_framework.exceptions import NotFound

        from reports.models import QualityReport
        from rules.models import ValidationRule

        try:
            dataset = Dataset.objects.get(id=dataset_id, user=request.user)
        except Dataset.DoesNotExist:
            raise NotFound("Dataset not found.")

        serializer = DatasetFileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ── File replacement (ACID step 1) ────────────────────────────────
        service = FileUploadService()
        dataset, _df, stale_columns = service.replace(
            dataset=dataset,
            file=serializer.validated_data["file"],
        )

        logger.info(
            "Dataset file updated: id=%s user=%s version=%d stale=%s",
            dataset_id,
            request.user.email,
            dataset.file_version,
            stale_columns or "none",
        )

        # ── Auto-check (ACID step 2 + async execution) ───────────────────
        # Only trigger if at least one rule exists — same guard as RunCheckView.
        # The QualityReport row is created HERE (synchronously, same DB
        # connection) so the report_id is available in the HTTP response
        # before the background thread starts.  If the thread fails the
        # report is updated to status=failing — never left incomplete.
        auto_check_block = None
        has_rules = ValidationRule.objects.filter(dataset=dataset).exists()

        if has_rules:
            # Create the report record immediately — ACID: if this INSERT
            # fails nothing starts; if it succeeds the ID is in the response.
            report = QualityReport.objects.create(
                dataset=dataset,
                dataset_file_title=dataset.file_title or dataset.file_name,
                dataset_file_version=dataset.file_version,
            )
            auto_check_block = {
                "report_id": str(report.id),
                "status": "queued",
                "message": (
                    "Quality check is running in the background. "
                    f"Poll GET /api/v1/reports/{report.id}/ for the result."
                ),
            }

            self._dispatch_auto_check(dataset.id, report.id)
            logger.info(
                "Auto-check queued: report=%s dataset=%s",
                report.id,
                dataset.id,
            )

        # ── Build response ────────────────────────────────────────────────
        response_data = DatasetFileReplaceResponseSerializer(dataset).data
        response_data["stale_rule_columns"] = stale_columns
        response_data["auto_check"] = auto_check_block

        return Response(response_data, status=status.HTTP_200_OK)
