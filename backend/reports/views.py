"""
reports/views.py
────────────────────────────────────────────────────────────────────────────────
ReportListView    GET  /api/v1/datasets/<dataset_id>/reports/
ReportDetailView  GET  /api/v1/reports/<report_id>/
TrendView         GET  /api/v1/datasets/<dataset_id>/trends/
DashboardView     GET  /api/v1/dashboard/

All views require authentication and enforce ownership — a user can only
see reports and trends for their own datasets.

ReportListView supports:
    ?status=pending|running|completed|failed
    ?date_from=YYYY-MM-DD   — reports generated on or after this date
    ?date_to=YYYY-MM-DD     — reports generated on or before this date
    ?page=<n>               — page number (default 1)
    ?page_size=<n>          — items per page (default 20, max 100)

TrendView supports:
    ?date_from=YYYY-MM-DD   — snapshots on or after this date
    ?date_to=YYYY-MM-DD     — snapshots on or before this date
"""

import logging

from django.db.models import Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import DataPulsePagination

from datasets.models import Dataset

from .models import QualityReport, TrendMetric
from .serializers import (
    DashboardSerializer,
    QualityReportSerializer,
    TrendMetricSerializer,
)

logger = logging.getLogger(__name__)


def _get_dataset_for_user(dataset_id, user) -> Dataset:
    try:
        return Dataset.objects.get(id=dataset_id, user=user)
    except Dataset.DoesNotExist:
        raise NotFound("Dataset not found.")


class ReportListView(APIView):
    """
    GET /api/v1/datasets/<dataset_id>/reports/

    Returns all quality reports for a dataset, newest first.
    Findings are NOT nested here to keep the list response lightweight.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by report status.",
                required=False,
                enum=["pending", "running", "completed", "failed"],
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return reports generated on or after this date (YYYY-MM-DD).",
                required=False,
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return reports generated on or before this date (YYYY-MM-DD).",
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
        responses={200: QualityReportSerializer(many=True)},
        summary="List quality reports for a dataset",
        description=(
            "Returns a paginated list of quality reports for a dataset, newest first. "
            "Findings are not nested in the list response. "
            "Supports filtering by status and date range."
        ),
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)
        queryset = QualityReport.objects.filter(dataset=dataset)

        # Filter: ?status=pending|running|completed|failed
        report_status = request.query_params.get("status")
        if report_status:
            queryset = queryset.filter(status=report_status)

        # Filter: ?date_from=YYYY-MM-DD
        date_from = request.query_params.get("date_from")
        if date_from:
            try:
                queryset = queryset.filter(generated_at__date__gte=date_from)
            except (ValueError, TypeError):
                raise ValidationError(
                    {"date_from": "Invalid date format. Use YYYY-MM-DD."}
                )

        # Filter: ?date_to=YYYY-MM-DD
        date_to = request.query_params.get("date_to")
        if date_to:
            try:
                queryset = queryset.filter(generated_at__date__lte=date_to)
            except (ValueError, TypeError):
                raise ValidationError(
                    {"date_to": "Invalid date format. Use YYYY-MM-DD."}
                )

        paginator = DataPulsePagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            QualityReportSerializer(page, many=True).data
        )


class ReportDetailView(APIView):
    """
    GET /api/v1/reports/<report_id>/

    Returns a single quality report with all findings nested.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: QualityReportSerializer},
        summary="Retrieve a quality report by ID",
        description="Returns a single quality report with all rule findings nested.",
    )
    def get(self, request: Request, report_id: str) -> Response:
        try:
            report = QualityReport.objects.prefetch_related("findings__rule").get(
                id=report_id, dataset__user=request.user
            )
        except QualityReport.DoesNotExist:
            raise NotFound("Report not found.")

        return Response(QualityReportSerializer(report).data)


class TrendView(APIView):
    """
    GET /api/v1/datasets/<dataset_id>/trends/

    Returns all trend_metrics rows for a dataset, ordered oldest → newest.
    Each entry is one date + score snapshot — used to draw the trend chart.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return snapshots on or after this date (YYYY-MM-DD).",
                required=False,
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Return snapshots on or before this date (YYYY-MM-DD).",
                required=False,
            ),
        ],
        responses={200: TrendMetricSerializer(many=True)},
        summary="List trend metrics for a dataset",
        description=(
            "Returns daily quality score snapshots for a dataset, ordered oldest to newest. "
            "Supports date range filtering via date_from and date_to (YYYY-MM-DD). "
            "Not paginated — trend data is consumed whole by the frontend chart."
        ),
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)
        queryset = TrendMetric.objects.filter(dataset=dataset).order_by("snapshot_date")

        # Filter: ?date_from=YYYY-MM-DD
        date_from = request.query_params.get("date_from")
        if date_from:
            try:
                queryset = queryset.filter(snapshot_date__gte=date_from)
            except (ValueError, TypeError):
                raise ValidationError(
                    {"date_from": "Invalid date format. Use YYYY-MM-DD."}
                )

        # Filter: ?date_to=YYYY-MM-DD
        date_to = request.query_params.get("date_to")
        if date_to:
            try:
                queryset = queryset.filter(snapshot_date__lte=date_to)
            except (ValueError, TypeError):
                raise ValidationError(
                    {"date_to": "Invalid date format. Use YYYY-MM-DD."}
                )

        return Response(TrendMetricSerializer(queryset, many=True).data)


class DashboardView(APIView):
    """
    GET /api/v1/dashboard/

    Aggregate view for the frontend dashboard. Returns every dataset the
    user owns together with:
      • latest_report — most recent quality report (score, status, date)
      • trend         — all trend_metric snapshots ordered by date

    Uses prefetch_related to avoid N+1 queries.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DashboardSerializer},
        summary="Retrieve the quality dashboard",
        description=(
            "Returns all datasets for the authenticated user, each with their latest "
            "quality report summary and full trend history. Optimised with prefetch_related "
            "to avoid N+1 queries."
        ),
    )
    def get(self, request: Request) -> Response:
        datasets = Dataset.objects.filter(user=request.user).prefetch_related(
            Prefetch(
                "reports",
                queryset=QualityReport.objects.order_by("-generated_at"),
                to_attr="all_reports",
            ),
            Prefetch(
                "trend_metrics",
                queryset=TrendMetric.objects.order_by("snapshot_date"),
                to_attr="trends",
            ),
        )

        dataset_blocks = []
        for dataset in datasets:
            latest_report = dataset.all_reports[0] if dataset.all_reports else None
            dataset_blocks.append(
                {
                    "dataset": dataset,
                    "latest_report": latest_report,
                    "trend": dataset.trends,
                }
            )

        payload = {
            "total_datasets": len(dataset_blocks),
            "datasets": dataset_blocks,
        }

        return Response(DashboardSerializer(payload).data)
