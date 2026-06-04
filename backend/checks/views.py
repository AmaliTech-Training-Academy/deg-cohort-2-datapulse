"""
checks/views.py
────────────────────────────────────────────────────────────────────────────────
RunCheckView  POST  /api/v1/datasets/<dataset_id>/run-check/

This is the only view in the checks app — it triggers a validation run.
All report retrieval views (list, detail, trends, dashboard) live in
reports/views.py.

Flow:
  1. Verify dataset ownership
  2. Verify dataset has at least one rule
  3. Create QualityReport (status=running)
  4. Load file into Pandas via FileUploadService
  5. Run ValidationEngine
  6. Compute score via QualityScoreCalculator
  7. Save one RuleFinding per rule
  8. Mark QualityReport as completed
  9. Upsert TrendMetric for today
  10. Return serialized report
"""

import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets.models import Dataset
from datasets.services.file_service import FileUploadService
from reports.models import QualityReport, RuleFinding, TrendMetric
from reports.serializers import QualityReportSerializer
from rules.models import ValidationRule

from .services.scoring_service import QualityScoreCalculator
from .services.validation_engine import ValidationEngine

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
        rules = ValidationRule.objects.filter(dataset=dataset)
        if not rules.exists():
            raise ValidationError(
                "No validation rules defined for this dataset. "
                "Add at least one rule before running a check."
            )

        # 3. Create report record — snapshot file title and version at this moment
        #    so the report permanently records which file it was run against.
        report = QualityReport.objects.create(
            dataset=dataset,
            dataset_file_title=dataset.file_title or dataset.file_name,
            dataset_file_version=dataset.file_version,
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
                    quality_report=report,
                    rule_id=result.rule_id,
                    rows_checked=result.rows_checked,
                    rows_failed=result.rows_failed,
                    failure_percentage=result.failure_percentage,
                    error_details=result.error_details,
                )
                for result in results
            ]
            RuleFinding.objects.bulk_create(findings)

            # 8. Set quality status derived from score:
            #    healthy (>85) / warning (>70) / failing (≤70)
            report.status = QualityReport.status_from_score(score_result.overall_score)
            report.overall_score = score_result.overall_score
            report.total_rows_passed = score_result.total_rows_passed
            report.total_rows_failed = score_result.total_rows_failed
            report.save(
                update_fields=[
                    "status",
                    "overall_score",
                    "total_rows_passed",
                    "total_rows_failed",
                ]
            )

            # 9. Upsert today's trend snapshot
            TrendMetric.objects.update_or_create(
                dataset=dataset,
                snapshot_date=timezone.now().date(),
                defaults={"aggregated_score": score_result.overall_score},
            )

            logger.info(
                "Check completed: report=%s dataset=%s score=%d status=%s",
                report.id,
                dataset.id,
                report.overall_score,
                report.status,
            )

        except Exception as exc:
            # Mark as failing on error — never leave the record in a broken state
            report.status = QualityReport.Status.FAILING
            report.error_message = str(exc)
            report.save(update_fields=["status", "error_message"])
            logger.exception("Check failed: report=%s error=%s", report.id, exc)
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

        # 10. Return completed report with all findings
        serializer = QualityReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
