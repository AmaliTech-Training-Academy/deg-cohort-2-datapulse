"""
rules/views.py
────────────────────────────────────────────────────────────────────────────────
RuleListCreateView    GET / POST  /api/v1/datasets/<dataset_id>/rules/
RuleDetailView        GET / PATCH / DELETE  /api/v1/rules/<id>/

Ownership is enforced at every level:
  - dataset must belong to request.user
  - rule must belong to a dataset owned by request.user

RuleListCreateView GET supports the following query parameters:
    ?rule_type=null_check|type_check|range_check|uniqueness_check
    ?column_name=<str>   — exact match on column name
    ?page=<n>            — page number (default 1)
    ?page_size=<n>       — items per page (default 20, max 100)

RuleListCreateView GET response includes dataset-level summary fields:
    total_failing_rows  — sum of rows_failed across all findings for this dataset
    total_passing_rows  — sum of (rows_checked - rows_failed) across all findings
    rule_type_scores    — per-rule-type average pass rate (0-100) for all 4 types

Per-rule items add:
    last_failing_rows   — rows_failed from the most recent finding for this rule
    last_passing_rows   — passing rows from the most recent finding
    average_score       — average pass rate across all findings for this rule
"""

import logging

from django.db import IntegrityError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import DataPulsePagination

from datasets.models import Dataset

from .models import ValidationRule
from .serializers import (
    RuleListItemSerializer,
    RuleListSerializer,
    RuleUpdateSerializer,
    ValidationRuleSerializer,
)

logger = logging.getLogger(__name__)


def _get_dataset_for_user(dataset_id: str, user) -> Dataset:
    """Fetch a dataset owned by the user or raise 404."""
    try:
        return Dataset.objects.get(id=dataset_id, user=user)
    except Dataset.DoesNotExist:
        raise NotFound("Dataset not found.")


def _get_rule_for_user(rule_id: str, user) -> ValidationRule:
    """Fetch a rule whose dataset is owned by the user or raise 404."""
    try:
        return ValidationRule.objects.select_related("dataset").get(
            id=rule_id,
            dataset__user=user,
        )
    except ValidationRule.DoesNotExist:
        raise NotFound("Rule not found.")


class RuleListCreateView(APIView):
    """
    GET  /api/v1/datasets/<dataset_id>/rules/  — list all rules for a dataset
    POST /api/v1/datasets/<dataset_id>/rules/  — create a new rule
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="rule_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by rule type.",
                required=False,
                enum=["null_check", "type_check", "range_check", "uniqueness_check"],
            ),
            OpenApiParameter(
                name="column_name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Exact match on column name.",
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
        responses={200: RuleListSerializer},
        summary="List validation rules for a dataset",
        description=(
            "Returns a paginated list of validation rules enriched with per-rule "
            "performance stats (last_failing_rows, last_passing_rows, average_score). "
            "Top-level summary includes total_failing_rows, total_passing_rows, and "
            "rule_type_scores for all 4 rule types. "
            "Supports filtering by rule_type and column_name."
        ),
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        from reports.models import RuleFinding

        dataset = _get_dataset_for_user(dataset_id, request.user)

        # ── Dataset-level summary — all findings, never filtered ──────────────
        # Fetch all RuleFindings for rules belonging to this dataset.
        all_findings = RuleFinding.objects.filter(
            rule__dataset=dataset
        ).select_related("rule")

        total_failing_rows = sum(f.rows_failed for f in all_findings)
        total_passing_rows = sum(
            f.rows_checked - f.rows_failed for f in all_findings
        )

        ALL_RULE_TYPES = [
            "null_check",
            "type_check",
            "range_check",
            "uniqueness_check",
        ]
        rates_by_type: dict[str, list[float]] = {rt: [] for rt in ALL_RULE_TYPES}
        for finding in all_findings:
            rt = finding.rule.rule_type
            if rt in rates_by_type:
                rates_by_type[rt].append(100.0 - finding.failure_percentage)

        rule_type_scores = {}
        for rt in ALL_RULE_TYPES:
            rates = rates_by_type[rt]
            rule_type_scores[rt] = round(sum(rates) / len(rates)) if rates else None

        # ── Filtered queryset — prefetch findings for per-rule stats ──────────
        queryset = (
            ValidationRule.objects.filter(dataset=dataset)
            .prefetch_related("findings")
            .order_by("created_at")
        )

        # Filter: ?rule_type=null_check|type_check|range_check|uniqueness_check
        rule_type_filter = request.query_params.get("rule_type")
        if rule_type_filter:
            queryset = queryset.filter(rule_type=rule_type_filter)

        # Filter: ?column_name=<str> — exact match
        column_name = request.query_params.get("column_name", "").strip()
        if column_name:
            queryset = queryset.filter(column_name=column_name)

        # ── Paginate ──────────────────────────────────────────────────────────
        paginator = DataPulsePagination()
        page = paginator.paginate_queryset(queryset, request)

        payload = {
            "total_failing_rows": total_failing_rows,
            "total_passing_rows": total_passing_rows,
            "rule_type_scores": rule_type_scores,
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": RuleListItemSerializer(page, many=True).data,
        }

        return Response(RuleListSerializer(payload).data)

    @extend_schema(
        request=ValidationRuleSerializer,
        responses={201: ValidationRuleSerializer, 409: None},
        summary="Create a validation rule for a dataset",
        description=(
            "Supported rule_type values: `null_check`, `type_check`, `range_check`, `uniqueness_check`.\n\n"
            "rule_config per type:\n"
            "- `null_check`: `{}`\n"
            '- `type_check`: `{"expected_type": "integer|float|string|boolean"}`\n'
            '- `range_check`: `{"min": 0, "max": 100}`\n'
            "- `uniqueness_check`: `{}`"
        ),
    )
    def post(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)

        # Inject the dataset into the data so the serializer can validate columns
        data = {**request.data, "dataset": str(dataset.id)}
        serializer = ValidationRuleSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            rule = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": (
                            f"A {request.data.get('rule_type')} rule already exists "
                            f"for column '{request.data.get('column_name')}'."
                        ),
                        "fields": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        logger.info("Rule created: %s on dataset %s", rule.id, dataset.id)
        return Response(
            ValidationRuleSerializer(rule).data, status=status.HTTP_201_CREATED
        )


class RuleDetailView(APIView):
    """
    GET    /api/v1/rules/<id>/  — retrieve one rule
    PATCH  /api/v1/rules/<id>/  — update rule_config only
    DELETE /api/v1/rules/<id>/  — delete a rule
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ValidationRuleSerializer},
        summary="Retrieve a validation rule",
    )
    def get(self, request: Request, rule_id: str) -> Response:
        rule = _get_rule_for_user(rule_id, request.user)
        return Response(ValidationRuleSerializer(rule).data)

    @extend_schema(
        request=RuleUpdateSerializer,
        responses={200: ValidationRuleSerializer},
        summary="Update rule_config (column and type are immutable)",
    )
    def patch(self, request: Request, rule_id: str) -> Response:
        rule = _get_rule_for_user(rule_id, request.user)
        serializer = RuleUpdateSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ValidationRuleSerializer(rule).data)

    @extend_schema(
        responses={204: None},
        summary="Delete a validation rule",
    )
    def delete(self, request: Request, rule_id: str) -> Response:
        rule = _get_rule_for_user(rule_id, request.user)
        rule_id_log = str(rule.id)
        rule.delete()
        logger.info("Rule deleted: %s", rule_id_log)
        return Response(status=status.HTTP_204_NO_CONTENT)
