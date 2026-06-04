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
    ?status=healthy|warning|failing
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
    ReportDetailSerializer,
    ReportListSerializer,
    TrendMetricSerializer,
)

from django.db.models import Avg, Sum
from rules.models import ValidationRule

logger = logging.getLogger(__name__)


def _get_dataset_for_user(dataset_id, user) -> Dataset:
    try:
        return Dataset.objects.get(id=dataset_id, user=user)
    except Dataset.DoesNotExist:
        raise NotFound("Dataset not found.")


class ReportListView(APIView):
    """
    GET /api/v1/datasets/<dataset_id>/reports/

    Returns a paginated list of quality reports for a dataset, newest first.
    Findings are excluded from the list response — use GET /reports/<id>/ for
    the full report with nested findings.

    Top-level summary fields (computed from ALL reports, unaffected by filters):
        total_active_reports   — total reports ever generated for this dataset
        total_active_rules     — current number of validation rules on the dataset
        last_rule_check_time   — generated_at of the most recent report
        average_score          — mean score across all completed reports
        total_passing_rows     — sum of total_rows_passed across all completed reports
        total_passing_columns  — number of columns in the current dataset file

    Per-report fields add:
        dataset_file_title     — file title snapshot at check time
        dataset_file_version   — file version snapshot at check time
        file_rows_analyzed     — total_rows_passed + total_rows_failed
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by quality status.",
                required=False,
                enum=["healthy", "warning", "failing"],
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
        responses={200: ReportListSerializer},
        summary="List quality reports for a dataset",
        description=(
            "Returns a paginated list of quality reports enriched with dataset-level "
            "summary statistics. Findings are excluded — use GET /reports/<id>/ for "
            "the full report with nested findings."
        ),
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)

        # ── Summary stats — computed from ALL reports, never filtered ─────────
        all_reports_qs = QualityReport.objects.filter(dataset=dataset)
        completed_qs = all_reports_qs.exclude(overall_score=None)

        total_active_reports = all_reports_qs.count()
        total_active_rules = ValidationRule.objects.filter(dataset=dataset).count()

        latest = all_reports_qs.order_by("-generated_at").first()
        last_rule_check_time = latest.generated_at if latest else None

        agg = completed_qs.aggregate(
            avg_score=Avg("overall_score"),
            sum_passing=Sum("total_rows_passed"),
        )
        average_score = (
            round(agg["avg_score"], 2) if agg["avg_score"] is not None else None
        )
        total_passing_rows = agg["sum_passing"] or 0
        total_passing_columns = len(dataset.columns or [])

        # ── Filtered queryset for paginated results ───────────────────────────
        queryset = all_reports_qs

        # Filter: ?status=healthy|warning|failing
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

        # ── Paginate ──────────────────────────────────────────────────────────
        paginator = DataPulsePagination()
        page = paginator.paginate_queryset(queryset, request)

        from .serializers import ReportListItemSerializer

        payload = {
            "total_active_reports": total_active_reports,
            "total_active_rules": total_active_rules,
            "last_rule_check_time": last_rule_check_time,
            "average_score": average_score,
            "total_passing_rows": total_passing_rows,
            "total_passing_columns": total_passing_columns,
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": ReportListItemSerializer(page, many=True).data,
        }

        return Response(ReportListSerializer(payload).data)


class ReportDetailView(APIView):
    """
    GET /api/v1/reports/<report_id>/

    Returns a single quality report with all findings nested, enriched with:
        dataset_file_name   — human-readable title of the file that was checked
        rules_applied       — number of validation rules that ran
        rows_analyzed       — total rows inspected (passed + failed)
        rule_type_scores    — per-rule-type average pass rate (0-100):
                              { null_check, type_check, range_check,
                                uniqueness_check } — null when not checked
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ReportDetailSerializer},
        summary="Retrieve a quality report by ID",
        description=(
            "Returns a single quality report with all rule findings nested. "
            "Includes dataset_file_name, rules_applied, rows_analyzed, and "
            "per-rule-type average pass scores for all 4 rule types."
        ),
    )
    def get(self, request: Request, report_id: str) -> Response:
        try:
            report = QualityReport.objects.prefetch_related("findings__rule").get(
                id=report_id, dataset__user=request.user
            )
        except QualityReport.DoesNotExist:
            raise NotFound("Report not found.")

        return Response(ReportDetailSerializer(report).data)


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

    Paginated aggregate view for the frontend dashboard.

    Returns a paginated list of the user's datasets, each enriched with:
      • status              — quality band of the latest report
      • latest_score        — overall_score of the most recent report
      • latest_score_date   — generated_at of the most recent report
      • latest_report       — full latest report summary block
      (trend is excluded — use GET /datasets/<id>/trends/ for chart data)

    Top-level summary fields (always present, unaffected by filters/pagination):
      • total_datasets          — all datasets owned by the user
      • total_active_datasets   — datasets that have at least one quality report

    Filters (all optional, combinable):
        ?status=healthy|warning|failing   filter by latest report quality band
        ?search=<str>                     case-insensitive match on file_title or file_name
        ?date_from=YYYY-MM-DD             datasets whose latest report was generated on or after
        ?date_to=YYYY-MM-DD               datasets whose latest report was generated on or before

    Pagination:
        ?page=<n>           page number (default 1)
        ?page_size=<n>      items per page (default 20, max 100)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by latest report quality band.",
                required=False,
                enum=["healthy", "warning", "failing"],
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Case-insensitive substring match on file_title or file_name.",
                required=False,
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Only include datasets whose latest report was generated on or after this date (YYYY-MM-DD).",  # noqa: E501
                required=False,
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Only include datasets whose latest report was generated on or before this date (YYYY-MM-DD).",  # noqa: E501
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
        responses={200: DashboardSerializer},
        summary="Retrieve the quality dashboard",
        description=(
            "Returns a paginated list of the user's datasets enriched with their "
            "latest quality report summary. Supports filtering by status, search, "
            "and date range. Trend data is excluded — use GET /datasets/<id>/trends/ "
            "for chart data."
        ),
    )
    def get(self, request: Request) -> Response:
        from django.db.models import OuterRef, Subquery

        # ── Base queryset — all datasets for this user ────────────────────────
        base_qs = Dataset.objects.filter(user=request.user)
        total_datasets = base_qs.count()

        # ── Annotate each dataset with its latest report via subquery ─────────
        # Using Subquery instead of prefetch so we can filter on report fields
        # without a costly Python-side loop.
        latest_report_subquery = (
            QualityReport.objects.filter(dataset=OuterRef("pk"))
            .order_by("-generated_at")
            .values("id")[:1]
        )
        datasets_with_report = base_qs.prefetch_related(
            Prefetch(
                "reports",
                queryset=QualityReport.objects.order_by("-generated_at"),
                to_attr="all_reports",
            )
        ).annotate(latest_report_id=Subquery(latest_report_subquery))

        # ── Build dataset blocks — resolve latest report per dataset ──────────
        all_blocks = []
        for dataset in datasets_with_report:
            latest_report = dataset.all_reports[0] if dataset.all_reports else None
            all_blocks.append(
                {
                    "dataset": dataset,
                    "latest_report": latest_report,
                }
            )

        # total_active_datasets — datasets that have at least one report
        total_active = sum(1 for b in all_blocks if b["latest_report"] is not None)

        # ── Apply filters in Python (after prefetch, avoids extra queries) ────

        # ?status=healthy|warning|failing
        status_filter = request.query_params.get("status")
        if status_filter:
            all_blocks = [
                b
                for b in all_blocks
                if b["latest_report"] is not None
                and b["latest_report"].status == status_filter
            ]

        # ?search=<str> — match file_title or file_name
        search = request.query_params.get("search", "").strip().lower()
        if search:
            all_blocks = [
                b
                for b in all_blocks
                if search in (b["dataset"].file_title or "").lower()
                or search in b["dataset"].file_name.lower()
            ]

        # ?date_from=YYYY-MM-DD — latest report generated on or after
        date_from = request.query_params.get("date_from")
        if date_from:
            try:
                from datetime import date as date_type

                df_date = date_type.fromisoformat(date_from)
                all_blocks = [
                    b
                    for b in all_blocks
                    if b["latest_report"] is not None
                    and b["latest_report"].generated_at.date() >= df_date
                ]
            except ValueError:
                raise ValidationError(
                    {"date_from": "Invalid date format. Use YYYY-MM-DD."}
                )

        # ?date_to=YYYY-MM-DD — latest report generated on or before
        date_to = request.query_params.get("date_to")
        if date_to:
            try:
                from datetime import date as date_type

                dt_date = date_type.fromisoformat(date_to)
                all_blocks = [
                    b
                    for b in all_blocks
                    if b["latest_report"] is not None
                    and b["latest_report"].generated_at.date() <= dt_date
                ]
            except ValueError:
                raise ValidationError(
                    {"date_to": "Invalid date format. Use YYYY-MM-DD."}
                )

        # ── Paginate the filtered list ────────────────────────────────────────
        paginator = DataPulsePagination()
        page = paginator.paginate_queryset(all_blocks, request)

        payload = {
            "total_datasets": total_datasets,
            "total_active_datasets": total_active,
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": page,
        }

        return Response(DashboardSerializer(payload).data)
