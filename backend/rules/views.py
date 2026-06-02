"""
rules/views.py
────────────────────────────────────────────────────────────────────────────────
RuleListCreateView    GET / POST  /api/v1/datasets/<dataset_id>/rules/
RuleDetailView        GET / PATCH / DELETE  /api/v1/rules/<id>/

Ownership is enforced at every level:
  - dataset must belong to request.user
  - rule must belong to a dataset owned by request.user
"""

import logging

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets.models import Dataset

from .models import ValidationRule
from .serializers import RuleUpdateSerializer, ValidationRuleSerializer

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
        responses={200: ValidationRuleSerializer(many=True)},
        summary="List all validation rules for a dataset",
    )
    def get(self, request: Request, dataset_id: str) -> Response:
        dataset = _get_dataset_for_user(dataset_id, request.user)
        rules = ValidationRule.objects.filter(dataset=dataset).order_by("created_at")
        return Response(ValidationRuleSerializer(rules, many=True).data)

    @extend_schema(
        request=ValidationRuleSerializer,
        responses={201: ValidationRuleSerializer, 409: None},
        summary="Create a validation rule for a dataset",
        description=(
            "Supported rule_type values: `null_check`, `type_check`, `range_check`, `uniqueness_check`.\n\n"
            "rule_config per type:\n"
            "- `null_check`: `{}`\n"
            "- `type_check`: `{\"expected_type\": \"integer|float|string|boolean\"}`\n"
            "- `range_check`: `{\"min\": 0, \"max\": 100}`\n"
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
