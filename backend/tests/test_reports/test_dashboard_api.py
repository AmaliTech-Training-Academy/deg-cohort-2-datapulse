"""
tests/test_reports/test_dashboard_api.py
Tests for GET /api/v1/dashboard/

Covers:
  - Response shape (pagination envelope + summary counts)
  - total_datasets and total_active_datasets counts
  - Per-dataset fields: status, latest_score, latest_score_date, latest_report, dataset
  - trend absent from response
  - Filter: ?status=healthy|warning|failing
  - Filter: ?search= (file_title and file_name)
  - Filter: ?date_from= / ?date_to=
  - Pagination: ?page_size= / ?page=
  - Auth enforcement (401)
  - Ownership isolation (no cross-user data)
"""

import io
from datetime import date, timedelta

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"
DASHBOARD_URL = "/api/v1/dashboard/"

VALID_CSV = b"id,age,email\n" b"1,25,alice@test.com\n" b"2,30,bob@test.com\n"


def csv_file(name="data.csv"):
    f = io.BytesIO(VALID_CSV)
    f.name = name
    return f


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


def run_check_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/run-check/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    """Upload a dataset with an explicit title."""
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(
        UPLOAD_URL,
        {
            "file": csv_file(),
            "file_title": "Employee Data",
            "description": "Test dataset",
        },
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def with_report(auth_client, uploaded):
    """Upload, add a null_check rule, run check — produces a healthy report (score=100)."""
    did = uploaded["id"]
    auth_client.post(
        rules_url(did),
        {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        format="json",
    )
    resp = auth_client.post(run_check_url(did))
    assert resp.status_code == 201
    return {"dataset": uploaded, "report": resp.json()}


# ── Response shape ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardShape:
    def test_returns_200(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.status_code == 200

    def test_top_level_fields_present(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        data = resp.json()
        for field in (
            "total_datasets",
            "total_active_datasets",
            "count",
            "next",
            "previous",
            "results",
        ):
            assert field in data

    def test_results_is_list(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert isinstance(resp.json()["results"], list)

    def test_per_dataset_fields_present(self, auth_client, with_report):
        resp = auth_client.get(DASHBOARD_URL)
        block = resp.json()["results"][0]
        for field in (
            "dataset",
            "status",
            "latest_score",
            "latest_score_date",
            "latest_report",
        ):
            assert field in block

    def test_dataset_block_contains_title_and_description(
        self, auth_client, with_report
    ):
        resp = auth_client.get(DASHBOARD_URL)
        ds = resp.json()["results"][0]["dataset"]
        assert ds["file_title"] == "Employee Data"
        assert ds["description"] == "Test dataset"

    def test_trend_not_in_response(self, auth_client, with_report):
        """trend is removed from dashboard — use /trends/ endpoint instead."""
        resp = auth_client.get(DASHBOARD_URL)
        block = resp.json()["results"][0]
        assert "trend" not in block


# ── Summary counts ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardCounts:
    def test_total_datasets_counts_all(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["total_datasets"] == 1

    def test_total_active_datasets_zero_without_reports(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["total_active_datasets"] == 0

    def test_total_active_datasets_increments_after_run_check(
        self, auth_client, with_report
    ):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["total_active_datasets"] == 1

    def test_count_reflects_filtered_results(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["count"] == 1


# ── Per-dataset quality fields ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardQualityFields:
    def test_status_is_null_without_report(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["status"] is None

    def test_latest_score_is_null_without_report(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["latest_score"] is None

    def test_latest_score_date_is_null_without_report(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["latest_score_date"] is None

    def test_latest_report_is_null_without_report(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["latest_report"] is None

    def test_status_set_after_run_check(self, auth_client, with_report):
        resp = auth_client.get(DASHBOARD_URL)
        # clean data, score=100 → healthy
        assert resp.json()["results"][0]["status"] == "healthy"

    def test_latest_score_set_after_run_check(self, auth_client, with_report):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["latest_score"] == 100

    def test_latest_score_date_set_after_run_check(self, auth_client, with_report):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["results"][0]["latest_score_date"] is not None

    def test_latest_report_block_fields(self, auth_client, with_report):
        resp = auth_client.get(DASHBOARD_URL)
        report = resp.json()["results"][0]["latest_report"]
        for field in (
            "id",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "generated_at",
        ):
            assert field in report


# ── Filters ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardFilters:
    def test_filter_status_healthy(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?status=healthy")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["status"] == "healthy"

    def test_filter_status_warning_no_match(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?status=warning")
        assert resp.json()["count"] == 0

    def test_filter_status_failing_no_match(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?status=failing")
        assert resp.json()["count"] == 0

    def test_search_matches_file_title(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?search=employee")
        assert resp.json()["count"] == 1

    def test_search_is_case_insensitive(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?search=EMPLOYEE")
        assert resp.json()["count"] == 1

    def test_search_no_match(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?search=nonexistent")
        assert resp.json()["count"] == 0

    def test_date_from_includes_today(self, auth_client, with_report):
        today = date.today().isoformat()
        resp = auth_client.get(f"{DASHBOARD_URL}?date_from={today}")
        assert resp.json()["count"] == 1

    def test_date_from_future_excludes_all(self, auth_client, with_report):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{DASHBOARD_URL}?date_from={tomorrow}")
        assert resp.json()["count"] == 0

    def test_date_to_includes_today(self, auth_client, with_report):
        today = date.today().isoformat()
        resp = auth_client.get(f"{DASHBOARD_URL}?date_to={today}")
        assert resp.json()["count"] == 1

    def test_date_to_past_excludes_all(self, auth_client, with_report):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{DASHBOARD_URL}?date_to={yesterday}")
        assert resp.json()["count"] == 0

    def test_combined_status_and_search(self, auth_client, with_report):
        resp = auth_client.get(f"{DASHBOARD_URL}?status=healthy&search=employee")
        assert resp.json()["count"] == 1

    def test_status_filter_excludes_datasets_without_reports(
        self, auth_client, settings, tmp_path, with_report
    ):
        """A dataset with no report should never appear in status-filtered results."""
        settings.MEDIA_ROOT = str(tmp_path)
        f = io.BytesIO(VALID_CSV)
        f.name = "second.csv"
        auth_client.post(
            UPLOAD_URL,
            {"file": f, "file_title": "Second Dataset"},
            format="multipart",
        )
        # total_datasets=2, but only 1 has a report
        resp = auth_client.get(f"{DASHBOARD_URL}?status=healthy")
        assert resp.json()["total_datasets"] == 2
        assert resp.json()["count"] == 1


# ── Pagination ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardPagination:
    def test_next_is_none_on_single_page(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["next"] is None

    def test_previous_is_none_on_first_page(self, auth_client, uploaded):
        resp = auth_client.get(DASHBOARD_URL)
        assert resp.json()["previous"] is None

    def test_page_size_limits_results(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        for i in range(3):
            f = io.BytesIO(VALID_CSV)
            f.name = f"data_{i}.csv"
            auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get(f"{DASHBOARD_URL}?page_size=2")
        assert len(resp.json()["results"]) == 2
        assert resp.json()["count"] == 3
        assert resp.json()["next"] is not None

    def test_page_2_returns_remaining(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        for i in range(3):
            f = io.BytesIO(VALID_CSV)
            f.name = f"data_{i}.csv"
            auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get(f"{DASHBOARD_URL}?page_size=2&page=2")
        assert len(resp.json()["results"]) == 1
        assert resp.json()["previous"] is not None


# ── Auth and ownership ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDashboardAuth:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(DASHBOARD_URL)
        assert resp.status_code == 401

    def test_other_user_sees_empty_dashboard(
        self, auth_client, uploaded, api_client, admin_user
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(DASHBOARD_URL)
        assert resp.json()["total_datasets"] == 0
        assert resp.json()["results"] == []
