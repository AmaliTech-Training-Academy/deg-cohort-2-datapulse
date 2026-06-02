"""
reports/views.py
────────────────────────────────────────────────────────────────────────────────
ReportListView    GET  /api/v1/datasets/<dataset_id>/reports/
ReportDetailView  GET  /api/v1/reports/<report_id>/
TrendView         GET  /api/v1/datasets/<dataset_id>/trends/
DashboardView     GET  /api/v1/dashboard/

All views require authentication and enforce ownership — a user can only
see reports and trends for their own datasets.
"""

import logging

from django.db.models import Prefetch
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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

    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)
        reports = QualityReport.objects.filter(dataset=dataset)
        return Response(QualityReportSerializer(reports, many=True).data)


class ReportDetailView(APIView):
    """
    GET /api/v1/reports/<report_id>/

    Returns a single quality report with all findings nested.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, report_id: str) -> Response:
        try:
            report = (
                QualityReport.objects
                .prefetch_related("findings__rule")
                .get(id=report_id, dataset__user=request.user)
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

    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)
        trends = TrendMetric.objects.filter(dataset=dataset).order_by("snapshot_date")
        return Response(TrendMetricSerializer(trends, many=True).data)


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
