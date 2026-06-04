"""
rules/views.py
────────────────────────────────────────────────────────────────────────────────
RuleListCreateView    GET / POST  /api/v1/datasets/<dataset_id>/rules/
RuleBatchCreateView   POST        /api/v1/datasets/<dataset_id>/rules/batch/
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

RuleBatchCreateView POST accepts a JSON array of rule objects and creates all
valid rules atomically.  Duplicate rules (same dataset + column + type) are
reported in the 'skipped' list rather than aborting the whole batch.
"""

import logging

from django.db import IntegrityError, transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
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
        all_findings = RuleFinding.objects.filter(rule__dataset=dataset).select_related(
            "rule"
        )

        total_failing_rows = sum(f.rows_failed for f in all_findings)
        total_passing_rows = sum(f.rows_checked - f.rows_failed for f in all_findings)

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
            "Create a validation rule for a specific column in the dataset.\n\n"
            "Supported rule_type values and their rule_config shapes:\n"
            "- `null_check` — fails null, empty, or whitespace-only values: `{}`\n"
            "- `type_check` — fails values that cannot be cast to the expected type: "
            '`{"expected_type": "integer|float|string|boolean"}`\n'
            "- `range_check` — fails numeric values outside [min, max]: "
            '`{"min": 0, "max": 100}`\n'
            "- `uniqueness_check` — flags all copies of duplicate values: `{}`\n\n"
            "Returns 409 if a rule of the same type already exists for that column."
        ),
        examples=[
            OpenApiExample(
                name="Null Check",
                summary="Reject null or empty values in a column",
                description=(
                    "Fails any row where the column value is null, an empty string, "
                    "or whitespace only."
                ),
                value={
                    "column_name": "name",
                    "rule_type": "null_check",
                    "rule_config": {},
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Range Check",
                summary="Reject values outside a numeric range",
                description=(
                    "Fails rows where the column value is not a number or falls "
                    "outside the specified [min, max] bounds (inclusive)."
                ),
                value={
                    "column_name": "age",
                    "rule_type": "range_check",
                    "rule_config": {"min": 18, "max": 65},
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Uniqueness Check",
                summary="Reject duplicate values in a column",
                description=(
                    "Flags all copies of any value that appears more than once — "
                    "not just the second occurrence."
                ),
                value={
                    "column_name": "id",
                    "rule_type": "uniqueness_check",
                    "rule_config": {},
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Type Check",
                summary="Reject values that cannot be cast to the expected type",
                description=(
                    "Supported expected_type values: integer, float, string, boolean. "
                    "For integer: accepts whole-number floats (3.0) but rejects "
                    "fractional values (3.5). For boolean: accepts true/false/1/0/yes/no."
                ),
                value={
                    "column_name": "salary",
                    "rule_type": "type_check",
                    "rule_config": {"expected_type": "float"},
                },
                request_only=True,
            ),
        ],
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


class RuleBatchCreateView(APIView):
    """
    POST /api/v1/datasets/<dataset_id>/rules/batch/

    Create multiple validation rules in a single request.

    Accepts a JSON array of rule objects.  Each item is validated
    independently.  Rules that fail validation return an error entry;
    duplicate rules (same column + rule_type) are reported in 'skipped'
    rather than aborting the whole batch.

    Response shape:
        {
          "created":  [ ...ValidationRuleSerializer objects... ],
          "skipped":  [ { "column_name", "rule_type", "reason" }, ... ],
          "errors":   [ { "index", "column_name", "rule_type", "detail" }, ... ],
          "summary":  { "total": N, "created": N, "skipped": N, "errors": N }
        }

    Returns 201 when at least one rule was created.
    Returns 400 when the request body is not a non-empty list.
    Returns 422 when every item failed validation or was a duplicate.
    """

    permission_classes = [IsAuthenticated]

    _ALL_RULES_EXAMPLE = [
        {
            "column_name": "name",
            "rule_type": "null_check",
            "rule_config": {},
        },
        {
            "column_name": "age",
            "rule_type": "range_check",
            "rule_config": {"min": 18, "max": 65},
        },
        {
            "column_name": "id",
            "rule_type": "uniqueness_check",
            "rule_config": {},
        },
        {
            "column_name": "salary",
            "rule_type": "type_check",
            "rule_config": {"expected_type": "float"},
        },
    ]

    _NULL_AND_UNIQUE_EXAMPLE = [
        {
            "column_name": "email",
            "rule_type": "null_check",
            "rule_config": {},
        },
        {
            "column_name": "employee_id",
            "rule_type": "uniqueness_check",
            "rule_config": {},
        },
    ]

    @extend_schema(
        request={
            "application/json": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column_name": {
                            "type": "string",
                            "description": "Column name — must exist in the dataset",
                        },
                        "rule_type": {
                            "type": "string",
                            "enum": [
                                "null_check",
                                "type_check",
                                "range_check",
                                "uniqueness_check",
                            ],
                        },
                        "rule_config": {
                            "type": "object",
                            "description": (
                                "Rule-type-specific config: "
                                "{} for null_check / uniqueness_check, "
                                '{"expected_type": "..."} for type_check, '
                                '{"min": N, "max": N} for range_check'
                            ),
                        },
                    },
                    "required": ["column_name", "rule_type", "rule_config"],
                },
                "minItems": 1,
            }
        },
        responses={
            201: {
                "type": "object",
                "properties": {
                    "created": {
                        "type": "array",
                        "description": "Rules that were successfully created",
                    },
                    "skipped": {
                        "type": "array",
                        "description": "Rules skipped because an identical rule already exists",
                    },
                    "errors": {
                        "type": "array",
                        "description": "Rules that failed validation",
                    },
                    "summary": {
                        "type": "object",
                        "description": "Count totals: total, created, skipped, errors",
                    },
                },
            },
            400: None,
            422: None,
        },
        summary="Batch-create multiple validation rules",
        description=(
            "Create multiple validation rules for a dataset in a single request. "
            "Each rule is validated independently. "
            "Duplicate rules (same column + rule_type already exists) are reported "
            "in 'skipped' — the rest of the batch still proceeds. "
            "Returns 201 when at least one rule was created. "
            "Returns 422 when every item in the batch failed or was a duplicate."
        ),
        examples=[
            OpenApiExample(
                name="All 4 Rule Types",
                summary="Create one of each rule type in a single request",
                description=(
                    "Creates null_check on name, range_check on age (18–65), "
                    "uniqueness_check on id, and type_check on salary (float). "
                    "Ideal for setting up a complete validation profile at once."
                ),
                value=_ALL_RULES_EXAMPLE,
                request_only=True,
            ),
            OpenApiExample(
                name="Null + Uniqueness",
                summary="Create two focused rules",
                description=(
                    "Creates a null_check on email and a uniqueness_check on "
                    "employee_id. Useful when only specific columns need validation."
                ),
                value=_NULL_AND_UNIQUE_EXAMPLE,
                request_only=True,
            ),
        ],
    )
    def post(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)

        # ── Validate request body is a non-empty list ──────────────────────────
        if not isinstance(request.data, list) or len(request.data) == 0:
            return Response(
                {
                    "error": {
                        "code": "INVALID_BODY",
                        "message": "Request body must be a non-empty JSON array of rule objects.",
                        "fields": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        skipped = []
        errors = []

        for index, item in enumerate(request.data):
            column_name = item.get("column_name", "")
            rule_type = item.get("rule_type", "")

            # Inject dataset FK for serializer validation
            data = {**item, "dataset": str(dataset.id)}
            serializer = ValidationRuleSerializer(data=data)

            if not serializer.is_valid():
                errors.append(
                    {
                        "index": index,
                        "column_name": column_name,
                        "rule_type": rule_type,
                        "detail": serializer.errors,
                    }
                )
                continue

            try:
                # Use a savepoint so an IntegrityError on this item rolls back
                # only this one save — not the entire request transaction.
                with transaction.atomic():
                    rule = serializer.save()
                created.append(ValidationRuleSerializer(rule).data)
                logger.info(
                    "Batch rule created: %s on dataset %s (index=%d)",
                    rule.id,
                    dataset.id,
                    index,
                )
            except IntegrityError:
                skipped.append(
                    {
                        "index": index,
                        "column_name": column_name,
                        "rule_type": rule_type,
                        "reason": (
                            f"A {rule_type} rule already exists "
                            f"for column '{column_name}'."
                        ),
                    }
                )

        summary = {
            "total": len(request.data),
            "created": len(created),
            "skipped": len(skipped),
            "errors": len(errors),
        }

        logger.info(
            "Batch rule creation on dataset %s: %s",
            dataset.id,
            summary,
        )

        # 422 if nothing was created (all skipped or all errored)
        if len(created) == 0:
            return Response(
                {
                    "error": {
                        "code": "BATCH_NOTHING_CREATED",
                        "message": "No rules were created. Check 'skipped' and 'errors' for details.",
                        "fields": {},
                    },
                    "skipped": skipped,
                    "errors": errors,
                    "summary": summary,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            {
                "created": created,
                "skipped": skipped,
                "errors": errors,
                "summary": summary,
            },
            status=status.HTTP_201_CREATED,
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
