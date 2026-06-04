"""
checks/views.py
────────────────────────────────────────────────────────────────────────────────
RunCheckView  POST  /api/v1/datasets/<dataset_id>/run-check/

This is the only view in the checks app — it triggers a validation run.
All report retrieval views (list, detail, trends, dashboard) live in
reports/views.py.

The validation logic lives in checks/services/check_service.py and is shared
with DatasetFileUpdateView (auto-check after file replacement).

Flow:
  1. Verify dataset ownership
  2. Verify dataset has at least one rule
  3. Delegate to run_quality_check() → QualityReport
  4. Return serialized report
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets.models import Dataset
from reports.serializers import QualityReportSerializer
from rules.models import ValidationRule

from .services.check_service import run_quality_check

logger = logging.getLogger(__name__)


class RunCheckView(APIView):
    """
    POST /api/v1/datasets/<dataset_id>/run-check/

    Triggers a full validation run on the dataset.
    Returns 201 with the completed QualityReport on success.
    Returns 400 if no rules are defined.
    Returns 404 if dataset not found.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            201: QualityReportSerializer,
            400: None,
            404: None,
        },
        summary="Run a quality check on a dataset",
        description=(
            "Triggers a full validation run against all rules defined for the dataset. "
            "Returns the completed QualityReport with per-rule findings and an overall score (0–100). "
            "Requires at least one rule to exist."
        ),
    )
    def post(self, request: Request, dataset_id: str) -> Response:
        # 1. Ownership check
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=request.user)
        except Dataset.DoesNotExist:
            raise NotFound("Dataset not found.")

        # 2. Require at least one rule
        if not ValidationRule.objects.filter(dataset=dataset).exists():
            raise ValidationError(
                "No validation rules defined for this dataset. "
                "Add at least one rule before running a check."
            )

        # 3. Run the check — all ACID logic is inside run_quality_check()
        report = run_quality_check(dataset)

        # 4. Surface engine failures as 500 (report exists but scored as failing)
        if report.error_message:
            return Response(
                {
                    "error": {
                        "code": "CHECK_FAILED",
                        "message": f"Validation run failed: {report.error_message}",
                        "fields": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            QualityReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )
