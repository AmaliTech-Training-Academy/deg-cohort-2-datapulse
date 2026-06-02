"""
checks/views.py
────────────────────────────────────────────────────────────────────────────────
RunCheckView    POST  /api/v1/datasets/<dataset_id>/run-check/
CheckDetailView GET   /api/v1/checks/<id>/

Flow:
  1. Verify dataset ownership
  2. Verify dataset has at least one rule
  3. Create QualityCheck record (status=running)
  4. Load file into Pandas via FileUploadService.load_dataframe()
  5. Run ValidationEngine
  6. Compute score via QualityScoreCalculator
  7. Save RuleFinding per rule
  8. Update QualityCheck to status=completed
  9. Return full serialized result

Any uncaught exception sets status=failed so the record is never stuck
at 'running'.
"""

import logging

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets.models import Dataset
from datasets.services.file_service import FileUploadService
from rules.models import ValidationRule

from .models import QualityCheck, RuleFinding
from .serializers import QualityCheckSerializer
from .services.scoring_service import QualityScoreCalculator
from .services.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class RunCheckView(APIView):
    """
    POST /api/v1/datasets/<dataset_id>/run-check/

    Triggers a full validation run on the dataset. Returns the completed
    QualityCheck object with all RuleFindings nested.

    Returns 201 on success, 400 if no rules exist, 404 if dataset not found.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, dataset_id: str) -> Response:
        # 1. Ownership check
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=request.user)
        except Dataset.DoesNotExist:
            raise NotFound("Dataset not found.")

        # 2. Require at least one rule
        rules = ValidationRule.objects.filter(dataset=dataset)
        if not rules.exists():
            return Response(
                {
                    "error": {
                        "code": "NO_RULES",
                        "message": "No validation rules defined for this dataset. "
                        "Add at least one rule before running a check.",
                        "fields": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Create check record — status=running immediately
        check = QualityCheck.objects.create(
            dataset=dataset, status=QualityCheck.Status.RUNNING
        )

        try:
            # 4. Load the file into a DataFrame
            service = FileUploadService()
            df = service._parse(dataset.file_path, dataset.file_type)

            # 5. Run the validation engine
            engine = ValidationEngine(df)
            results, failed_union = engine.run(rules)

            # 6. Compute quality score
            calculator = QualityScoreCalculator()
            score_result = calculator.calculate(
                total_rows=len(df),
                failed_union=failed_union,
            )

            # 7. Persist one RuleFinding per rule result
            findings = [
                RuleFinding(
                    quality_check=check,
                    rule_id=result.rule_id,
                    rows_checked=result.rows_checked,
                    rows_failed=result.rows_failed,
                    failure_percentage=result.failure_percentage,
                    error_details=result.error_details,
                )
                for result in results
            ]
            RuleFinding.objects.bulk_create(findings)

            # 8. Mark check as completed
            check.status = QualityCheck.Status.COMPLETED
            check.overall_score = score_result.overall_score
            check.total_rows_passed = score_result.total_rows_passed
            check.total_rows_failed = score_result.total_rows_failed
            check.save()

            logger.info(
                "Check completed: id=%s dataset=%s score=%d",
                check.id,
                dataset.id,
                check.overall_score,
            )

        except Exception as exc:
            # Always mark failed — never leave status=running
            check.status = QualityCheck.Status.FAILED
            check.error_message = str(exc)
            check.save()
            logger.exception("Check failed: id=%s error=%s", check.id, exc)
            return Response(
                {
                    "error": {
                        "code": "CHECK_FAILED",
                        "message": f"Validation run failed: {exc}",
                        "fields": {},
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 9. Return completed check with all findings
        serializer = QualityCheckSerializer(check, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CheckDetailView(APIView):
    """GET /api/v1/checks/<id>/ — retrieve a single check run with findings."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, check_id: str) -> Response:
        try:
            check = QualityCheck.objects.prefetch_related("findings__rule").get(
                id=check_id, dataset__user=request.user
            )
        except QualityCheck.DoesNotExist:
            raise NotFound("Check not found.")

        return Response(QualityCheckSerializer(check).data)


class CheckListView(APIView):
    """GET /api/v1/datasets/<dataset_id>/checks/ — list all checks for a dataset."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, dataset_id: str) -> Response:
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=request.user)
        except Dataset.DoesNotExist:
            raise NotFound("Dataset not found.")

        checks = QualityCheck.objects.filter(dataset=dataset).order_by("-generated_at")
        return Response(QualityCheckSerializer(checks, many=True).data)
