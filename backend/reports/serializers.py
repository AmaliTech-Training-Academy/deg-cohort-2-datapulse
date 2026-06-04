"""
reports/serializers.py
────────────────────────────────────────────────────────────────────────────────
RuleFindingSerializer      — per-rule results nested inside a report (detail only)
QualityReportSerializer    — base report response with findings (internal use)
RunCheckResponseSerializer — enriched POST /run-check/ response with average_score,
                             rules_applied, failing_checks, passing_checks,
                             rule_type_scores, and all existing fields
ReportDetailSerializer     — enriched report detail (GET /reports/<id>/) with
                             dataset_file_name, rules_applied, rows_analyzed,
                             and per-rule-type average scores
ReportListItemSerializer   — lightweight report row for list responses (no findings)
ReportListSerializer       — full list envelope with dataset-level summary statistics
TrendMetricSerializer      — single trend point (date + score)
DashboardDatasetSerializer — per-dataset summary for the dashboard
DashboardSerializer        — top-level dashboard response
"""

from rest_framework import serializers

from datasets.serializers import DatasetResponseSerializer

from .models import QualityReport, RuleFinding, TrendMetric


class RuleFindingSerializer(serializers.ModelSerializer):
    rule_type = serializers.CharField(source="rule.rule_type", read_only=True)
    column_name = serializers.CharField(source="rule.column_name", read_only=True)

    class Meta:
        model = RuleFinding
        fields = [
            "id",
            "rule",
            "rule_type",
            "column_name",
            "rows_checked",
            "rows_failed",
            "failure_percentage",
            "error_details",
        ]
        read_only_fields = fields


class QualityReportSerializer(serializers.ModelSerializer):
    findings = RuleFindingSerializer(many=True, read_only=True)

    class Meta:
        model = QualityReport
        fields = [
            "id",
            "dataset",
            "dataset_file_title",
            "dataset_file_version",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "error_message",
            "findings",
            "generated_at",
        ]
        read_only_fields = fields


class RunCheckResponseSerializer(serializers.ModelSerializer):
    """
    Enriched serializer for POST /api/v1/datasets/<id>/run-check/.

    Adds on top of QualityReportSerializer:

        average_score       — overall quality score (0-100), surfaced explicitly
                              as average_score to make the semantic clear.
                              Identical to overall_score.
        rules_applied       — total number of rules that ran in this check
        failing_checks      — number of rules where at least one row failed
        passing_checks      — number of rules where every row passed
        rule_type_scores    — per-rule-type average pass rate (0-100) across
                              all findings in this run.  Always includes all 4
                              keys; null for rule types not present in this check.

                              Example:
                              {
                                "null_check":       92,
                                "type_check":       100,
                                "range_check":      75,
                                "uniqueness_check": null
                              }

    All existing QualityReportSerializer fields are preserved:
        id, dataset, dataset_file_title, dataset_file_version,
        status, overall_score, total_rows_passed, total_rows_failed,
        error_message, findings, generated_at
    """

    findings = RuleFindingSerializer(many=True, read_only=True)
    average_score = serializers.SerializerMethodField()
    rules_applied = serializers.SerializerMethodField()
    failing_checks = serializers.SerializerMethodField()
    passing_checks = serializers.SerializerMethodField()
    rule_type_scores = serializers.SerializerMethodField()

    class Meta:
        model = QualityReport
        fields = [
            # ── Existing fields ───────────────────────────────────────────
            "id",
            "dataset",
            "dataset_file_title",
            "dataset_file_version",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "error_message",
            "findings",
            "generated_at",
            # ── New fields ────────────────────────────────────────────────
            "average_score",
            "rules_applied",
            "failing_checks",
            "passing_checks",
            "rule_type_scores",
        ]
        read_only_fields = fields

    def get_average_score(self, obj) -> int | None:
        """Explicit alias for overall_score with clearer semantic meaning."""
        return obj.overall_score

    def get_rules_applied(self, obj) -> int:
        """Total number of validation rules that ran in this check."""
        return obj.findings.count()

    def get_failing_checks(self, obj) -> int:
        """Number of rules where at least one row failed."""
        return sum(1 for f in obj.findings.all() if f.rows_failed > 0)

    def get_passing_checks(self, obj) -> int:
        """Number of rules where every row passed (rows_failed == 0)."""
        return sum(1 for f in obj.findings.all() if f.rows_failed == 0)

    def get_rule_type_scores(self, obj) -> dict:
        """
        Average pass rate per rule type across findings in this run.

        Pass rate for a finding = 100 - failure_percentage.
        Rounded to nearest integer.  null = that rule type was not checked.
        """
        ALL_RULE_TYPES = [
            "null_check",
            "type_check",
            "range_check",
            "uniqueness_check",
        ]
        rates: dict[str, list[float]] = {rt: [] for rt in ALL_RULE_TYPES}
        for finding in obj.findings.all():
            rt = finding.rule.rule_type
            if rt in rates:
                rates[rt].append(100.0 - finding.failure_percentage)

        return {rt: round(sum(r) / len(r)) if r else None for rt, r in rates.items()}


class ReportDetailSerializer(serializers.ModelSerializer):
    """
    Enriched serializer for GET /api/v1/reports/<id>/.

    Adds on top of QualityReportSerializer:

        dataset_file_name   — human-readable title of the file that was checked
                              (snapshot stored on the report at check time)
        rules_applied       — number of validation rules that ran in this check
        rows_analyzed       — total rows inspected (passed + failed)
        rule_type_scores    — per-rule-type average pass rate (0–100), computed
                              from findings.  Only includes rule types that were
                              actually checked.  null for rule types with no
                              findings in this report.

                              Example:
                              {
                                "null_check":       92,
                                "type_check":       100,
                                "range_check":      75,
                                "uniqueness_check": null
                              }

                              Score formula per rule type:
                                avg(100 - failure_percentage) across findings
                                of that type, rounded to nearest integer.

    All existing QualityReportSerializer fields are preserved:
        id, dataset, dataset_file_title, dataset_file_version,
        status, overall_score, total_rows_passed, total_rows_failed,
        error_message, findings, generated_at
    """

    findings = RuleFindingSerializer(many=True, read_only=True)

    # New fields
    dataset_file_name = serializers.SerializerMethodField()
    rules_applied = serializers.SerializerMethodField()
    rows_analyzed = serializers.SerializerMethodField()
    rule_type_scores = serializers.SerializerMethodField()

    class Meta:
        model = QualityReport
        fields = [
            # ── Existing fields ───────────────────────────────────────────
            "id",
            "dataset",
            "dataset_file_title",
            "dataset_file_version",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "error_message",
            "findings",
            "generated_at",
            # ── New fields ────────────────────────────────────────────────
            "dataset_file_name",
            "rules_applied",
            "rows_analyzed",
            "rule_type_scores",
        ]
        read_only_fields = fields

    def get_dataset_file_name(self, obj) -> str:
        """
        Human-readable file title snapshot stored at check time.
        Falls back to the live dataset file_name if the snapshot is blank
        (e.g. reports created before this field was added).
        """
        return obj.dataset_file_title or obj.dataset.file_name

    def get_rules_applied(self, obj) -> int:
        """Number of validation rules that ran in this check."""
        return obj.findings.count()

    def get_rows_analyzed(self, obj) -> int | None:
        """Total rows inspected = passed + failed.  Null if not yet scored."""
        if obj.total_rows_passed is None or obj.total_rows_failed is None:
            return None
        return obj.total_rows_passed + obj.total_rows_failed

    def get_rule_type_scores(self, obj) -> dict:
        """
        Average pass rate per rule type across all findings in this report.

        Pass rate for a finding = 100 - failure_percentage.
        The per-type score is the average of pass rates across all findings
        of that rule type, rounded to the nearest integer.

        Always returns all 4 keys.  A null value means that rule type was
        not included in this check run (no findings of that type exist).
        """
        ALL_RULE_TYPES = [
            "null_check",
            "type_check",
            "range_check",
            "uniqueness_check",
        ]

        # Group findings by rule_type, accumulate pass rates
        scores_by_type: dict[str, list[float]] = {rt: [] for rt in ALL_RULE_TYPES}
        for finding in obj.findings.all():
            rt = finding.rule.rule_type
            if rt in scores_by_type:
                scores_by_type[rt].append(100.0 - finding.failure_percentage)

        result = {}
        for rt in ALL_RULE_TYPES:
            rates = scores_by_type[rt]
            if rates:
                result[rt] = round(sum(rates) / len(rates))
            else:
                result[rt] = None
        return result


class ReportListItemSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for individual reports inside ReportListView.

    Findings are intentionally excluded — use GET /reports/<id>/ for the
    full report with nested findings.

    Adds file_rows_analyzed — the total number of rows inspected during this
    run (total_rows_passed + total_rows_failed).  Null when the report has
    not yet completed (e.g. still queued).
    """

    file_rows_analyzed = serializers.SerializerMethodField()

    class Meta:
        model = QualityReport
        fields = [
            "id",
            "dataset",
            "dataset_file_title",
            "dataset_file_version",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "file_rows_analyzed",
            "error_message",
            "generated_at",
        ]
        read_only_fields = fields

    def get_file_rows_analyzed(self, obj) -> int | None:
        if obj.total_rows_passed is None or obj.total_rows_failed is None:
            return None
        return obj.total_rows_passed + obj.total_rows_failed


class ReportListSerializer(serializers.Serializer):
    """
    Full envelope returned by GET /api/v1/datasets/<id>/reports/.

    Summary fields (computed from ALL reports for the dataset, unaffected
    by filters or pagination):
        total_active_reports   — total number of reports ever generated
        total_active_rules     — current number of validation rules on the dataset
        last_rule_check_time   — generated_at of the most recent report (null if none)
        average_score          — mean overall_score across all completed reports
                                 (null if no completed reports)
        total_passing_rows     — sum of total_rows_passed across all completed reports
        total_passing_columns  — number of distinct columns in the current dataset file

    Pagination envelope (reflects the current filtered + paginated view):
        count      — total items matching the current filters
        next       — URL of the next page (null on last page)
        previous   — URL of the previous page (null on first page)
        results    — list of ReportListItemSerializer objects
    """

    total_active_reports = serializers.IntegerField()
    total_active_rules = serializers.IntegerField()
    last_rule_check_time = serializers.DateTimeField(allow_null=True)
    average_score = serializers.FloatField(allow_null=True)
    total_passing_rows = serializers.IntegerField()
    total_passing_columns = serializers.IntegerField()
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    # results holds already-serialized dicts from ReportListItemSerializer
    results = serializers.ListField(child=serializers.DictField())


class TrendMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendMetric
        fields = ["snapshot_date", "aggregated_score"]
        read_only_fields = fields


class DashboardDatasetSerializer(serializers.Serializer):
    """
    Per-dataset block returned by the dashboard endpoint.

    Includes all existing dataset fields plus a flattened latest_report
    summary.  trend is intentionally excluded — use GET /trends/ for
    chart data.

    Fields:
        dataset             — full dataset object (id, file_name, file_title,
                              description, file_type, row_count, columns,
                              file_version, created_at, updated_at)
        status              — quality band of the latest report
                              (healthy | warning | failing | null)
        latest_score        — overall_score from the most recent report (null
                              if no report exists)
        latest_score_date   — generated_at of the most recent report (null
                              if no report exists)
        latest_report       — full latest report summary block (id, status,
                              overall_score, total_rows_passed,
                              total_rows_failed, generated_at) or null
    """

    dataset = DatasetResponseSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    latest_score = serializers.SerializerMethodField()
    latest_score_date = serializers.SerializerMethodField()
    latest_report = serializers.SerializerMethodField()

    def get_status(self, obj) -> str | None:
        report = obj.get("latest_report")
        return report.status if report else None

    def get_latest_score(self, obj) -> int | None:
        report = obj.get("latest_report")
        return report.overall_score if report else None

    def get_latest_score_date(self, obj):
        report = obj.get("latest_report")
        return report.generated_at if report else None

    def get_latest_report(self, obj):
        report = obj.get("latest_report")
        if report is None:
            return None
        return {
            "id": str(report.id),
            "dataset_file_title": report.dataset_file_title,
            "dataset_file_version": report.dataset_file_version,
            "status": report.status,
            "overall_score": report.overall_score,
            "total_rows_passed": report.total_rows_passed,
            "total_rows_failed": report.total_rows_failed,
            "generated_at": report.generated_at,
        }


class DashboardSerializer(serializers.Serializer):
    """
    Top-level dashboard response.

    Fields:
        total_datasets          — total datasets owned by the user
        total_active_datasets   — datasets that have at least one quality report
        count                   — total items in the current filtered + paginated view
        next                    — URL of the next page (null on last page)
        previous                — URL of the previous page (null on first page)
        results                 — paginated list of DashboardDatasetSerializer blocks
    """

    total_datasets = serializers.IntegerField()
    total_active_datasets = serializers.IntegerField()
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = DashboardDatasetSerializer(many=True)
