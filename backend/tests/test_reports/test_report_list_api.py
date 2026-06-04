"""
tests/test_reports/test_report_list_api.py
Tests for GET /api/v1/datasets/<id>/reports/

Covers the enhanced response envelope:
  - Summary fields: total_active_reports, total_active_rules, last_rule_check_time,
    average_score, total_passing_rows, total_passing_columns
  - Per-report fields: dataset_file_title, dataset_file_version, file_rows_analyzed
  - Findings excluded from list (present only in detail)
  - Existing: pagination, filters (status, date_from, date_to)
  - Auth and ownership
"""

import io
from datetime import date, timedelta

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    b"id,age,email\n"
    b"1,25,alice@test.com\n"
    b"2,30,bob@test.com\n"
    b"3,35,carol@test.com\n"
)


def csv_file(name="data.csv"):
    f = io.BytesIO(VALID_CSV)
    f.name = name
    return f


def reports_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/reports/"


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


def run_check_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/run-check/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(
        UPLOAD_URL,
        {"file": csv_file(), "file_title": "Employee Data", "description": "Test"},
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def with_rules(auth_client, uploaded):
    for col, rt, rc in [
        ("email", "null_check", {}),
        ("id", "uniqueness_check", {}),
    ]:
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": col, "rule_type": rt, "rule_config": rc},
            format="json",
        )
    return uploaded


@pytest.fixture
def with_report(auth_client, with_rules):
    resp = auth_client.post(run_check_url(with_rules["id"]))
    assert resp.status_code == 201
    return {"dataset": with_rules, "report": resp.json()}


# ── Response envelope shape ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestReportListShape:
    def test_returns_200(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.status_code == 200

    def test_all_summary_fields_present(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        data = resp.json()
        for field in (
            "total_active_reports",
            "total_active_rules",
            "last_rule_check_time",
            "average_score",
            "total_passing_rows",
            "total_passing_columns",
            "count",
            "next",
            "previous",
            "results",
        ):
            assert field in data, f"Missing field: {field}"

    def test_results_is_list(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert isinstance(resp.json()["results"], list)

    def test_per_report_fields_present(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        report = resp.json()["results"][0]
        for field in (
            "id",
            "dataset",
            "dataset_file_title",
            "dataset_file_version",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "file_rows_analyzed",
            "generated_at",
        ):
            assert field in report, f"Missing report field: {field}"

    def test_findings_excluded_from_list(self, auth_client, with_report):
        """findings must NOT appear in the list — use GET /reports/<id>/ for that."""
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        report = resp.json()["results"][0]
        assert "findings" not in report


# ── Summary fields — zero state ───────────────────────────────────────────────


@pytest.mark.django_db
class TestSummaryZeroState:
    def test_total_active_reports_zero_initially(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.json()["total_active_reports"] == 0

    def test_total_active_rules_zero_initially(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.json()["total_active_rules"] == 0

    def test_last_rule_check_time_null_initially(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.json()["last_rule_check_time"] is None

    def test_average_score_null_initially(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.json()["average_score"] is None

    def test_total_passing_rows_zero_initially(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        assert resp.json()["total_passing_rows"] == 0

    def test_total_passing_columns_reflects_dataset(self, auth_client, uploaded):
        """Even with no reports, column count comes from the dataset file."""
        resp = auth_client.get(reports_url(uploaded["id"]))
        # VALID_CSV has 3 columns: id, age, email
        assert resp.json()["total_passing_columns"] == 3


# ── Summary fields — after run check ─────────────────────────────────────────


@pytest.mark.django_db
class TestSummaryAfterCheck:
    def test_total_active_reports_increments(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        assert resp.json()["total_active_reports"] == 1

    def test_total_active_rules_reflects_rule_count(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        assert resp.json()["total_active_rules"] == 2

    def test_last_rule_check_time_set_after_run(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        assert resp.json()["last_rule_check_time"] is not None

    def test_average_score_equals_score_for_single_report(
        self, auth_client, with_report
    ):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        # Clean data → score 100; average of one report is 100.0
        assert resp.json()["average_score"] == 100.0

    def test_total_passing_rows_equals_report_rows_passed(
        self, auth_client, with_report
    ):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        report_rows_passed = with_report["report"]["total_rows_passed"]
        assert resp.json()["total_passing_rows"] == report_rows_passed

    def test_total_passing_columns_still_reflects_dataset(
        self, auth_client, with_report
    ):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        assert resp.json()["total_passing_columns"] == 3


# ── Per-report fields ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPerReportFields:
    def test_dataset_file_title_snapshot(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        report = resp.json()["results"][0]
        assert report["dataset_file_title"] == "Employee Data"

    def test_dataset_file_version_snapshot(self, auth_client, with_report):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        report = resp.json()["results"][0]
        assert report["dataset_file_version"] == 1

    def test_file_rows_analyzed_is_sum_of_passed_and_failed(
        self, auth_client, with_report
    ):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        r = resp.json()["results"][0]
        assert r["file_rows_analyzed"] == r["total_rows_passed"] + r["total_rows_failed"]

    def test_file_rows_analyzed_equals_dataset_row_count(
        self, auth_client, with_report
    ):
        resp = auth_client.get(reports_url(with_report["dataset"]["id"]))
        # VALID_CSV has 3 rows
        assert resp.json()["results"][0]["file_rows_analyzed"] == 3


# ── Summary is unaffected by filters ─────────────────────────────────────────


@pytest.mark.django_db
class TestSummaryUnaffectedByFilters:
    def test_total_active_reports_unaffected_by_status_filter(
        self, auth_client, with_report
    ):
        """total_active_reports counts all reports, not just filtered ones."""
        resp = auth_client.get(
            f"{reports_url(with_report['dataset']['id'])}?status=failing"
        )
        # count=0 (no failing reports) but total_active_reports=1 (all reports)
        assert resp.json()["count"] == 0
        assert resp.json()["total_active_reports"] == 1

    def test_average_score_unaffected_by_date_filter(
        self, auth_client, with_report
    ):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = auth_client.get(
            f"{reports_url(with_report['dataset']['id'])}?date_from={tomorrow}"
        )
        assert resp.json()["count"] == 0
        assert resp.json()["average_score"] == 100.0


# ── Auth ──────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestReportListAuth:
    def test_unauthenticated_returns_401(self, api_client, uploaded):
        resp = api_client.get(reports_url(uploaded["id"]))
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(reports_url(uploaded["id"]))
        assert resp.status_code == 404
