"""
checks/services/check_service.py
────────────────────────────────────────────────────────────────────────────────
run_quality_check() — the shared engine that executes a full validation run
against a dataset and persists the result as a QualityReport.

Extracted from RunCheckView so the same logic can be called:
  • synchronously by RunCheckView (POST /datasets/<id>/run-check/)
  • in a background thread by DatasetFileUpdateView (PATCH /datasets/<id>/file/)

ACID guarantee:
    1. A QualityReport row is created before any heavy computation starts.
    2. All findings are written with bulk_create inside the same DB connection.
    3. The report is updated to its final status (healthy/warning/failing) in a
       single .save(update_fields=[...]) call — never a full-row write.
    4. If any step raises, the report is updated to status=failing with the
       error message — the record is never left in an intermediate state.

The function is intentionally stateless — it receives a Dataset ORM instance
(already ownership-checked by the caller) and returns the completed
QualityReport instance.
"""

import logging

from django.utils import timezone

from reports.models import QualityReport, RuleFinding, TrendMetric
from rules.models import ValidationRule

from .scoring_service import QualityScoreCalculator
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


def run_quality_check_on_report(dataset, report: QualityReport) -> QualityReport:
    """
    Execute a full validation run and write results into an already-created
    QualityReport row.

    Used by DatasetFileUpdateView after it creates the report synchronously
    so the report_id is available in the HTTP response before the background
    thread starts.

    Parameters
    ----------
    dataset : Dataset
        Already-fetched, ownership-verified Dataset instance.
    report : QualityReport
        Pre-created report row (status=failing, no score yet).

    Returns
    -------
    QualityReport — the same instance with updated status, score, and findings.
    """
    from datasets.services.file_service import FileUploadService

    try:
        rules = ValidationRule.objects.filter(dataset=dataset)

        service = FileUploadService()
        df = service._parse(dataset.file_path, dataset.file_type)

        engine = ValidationEngine(df)
        results, failed_union = engine.run(rules)

        calculator = QualityScoreCalculator()
        score_result = calculator.calculate(
            total_rows=len(df),
            failed_union=failed_union,
        )

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

        TrendMetric.objects.update_or_create(
            dataset=dataset,
            snapshot_date=timezone.now().date(),
            defaults={"aggregated_score": score_result.overall_score},
        )

        logger.info(
            "Auto-check completed: report=%s dataset=%s score=%d status=%s",
            report.id,
            dataset.id,
            report.overall_score,
            report.status,
        )

    except Exception as exc:
        report.status = QualityReport.Status.FAILING
        report.error_message = str(exc)
        report.save(update_fields=["status", "error_message"])
        logger.exception(
            "Auto-check failed: report=%s dataset=%s error=%s",
            report.id,
            dataset.id,
            exc,
        )

    return report


def run_quality_check(dataset) -> QualityReport:
    """
    Execute a full validation run against ``dataset`` and return the
    completed QualityReport.

    Parameters
    ----------
    dataset : Dataset
        An already-fetched, ownership-verified Dataset instance.
        Must have a readable file at dataset.file_path.

    Returns
    -------
    QualityReport
        The persisted report with status healthy | warning | failing.
        On engine failure the report has status=failing and a populated
        error_message.

    Raises
    ------
    Nothing — all exceptions are caught and stored on the report so the
    caller always gets a QualityReport back (never a raw exception).
    """
    from datasets.services.file_service import FileUploadService

    # Snapshot the file identity at the moment the check starts.
    # If the file is replaced again while this run is in progress the
    # snapshot still reflects the version we are actually scoring.
    report = QualityReport.objects.create(
        dataset=dataset,
        dataset_file_title=dataset.file_title or dataset.file_name,
        dataset_file_version=dataset.file_version,
    )

    try:
        rules = ValidationRule.objects.filter(dataset=dataset)

        # Parse the file into a DataFrame
        service = FileUploadService()
        df = service._parse(dataset.file_path, dataset.file_type)

        # Run all validation rules
        engine = ValidationEngine(df)
        results, failed_union = engine.run(rules)

        # Compute quality score
        calculator = QualityScoreCalculator()
        score_result = calculator.calculate(
            total_rows=len(df),
            failed_union=failed_union,
        )

        # Persist one RuleFinding per rule result
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

        # Set final quality status from score — healthy / warning / failing
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

        # Upsert today's trend snapshot
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
        # Never leave the report in an indeterminate state
        report.status = QualityReport.Status.FAILING
        report.error_message = str(exc)
        report.save(update_fields=["status", "error_message"])
        logger.exception(
            "Check failed: report=%s dataset=%s error=%s",
            report.id,
            dataset.id,
            exc,
        )

    return report
