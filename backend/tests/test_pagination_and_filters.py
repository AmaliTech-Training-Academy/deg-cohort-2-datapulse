"""
tests/test_pagination_and_filters.py

Tests for pagination and filtering across:
  GET /api/v1/datasets/
  GET /api/v1/datasets/<id>/rules/
  GET /api/v1/datasets/<id>/reports/
  GET /api/v1/datasets/<id>/trends/
"""

import io
from datetime import date, timedelta

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    b"id,age,email,score\n" b"1,25,alice@test.com,88\n" b"2,30,bob@test.com,92\n"
)


def csv_file(name="data.csv"):
    f = io.BytesIO(VALID_CSV)
    f.name = name
    return f


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


def reports_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/reports/"


def trends_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/trends/"


def run_check_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/run-check/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(
        UPLOAD_URL,
        {"file": csv_file(), "file_title": "My Dataset"},
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


# ── Pagination shape ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPaginationShape:
    def test_dataset_list_returns_paginated_shape(self, auth_client, uploaded):
        resp = auth_client.get("/api/v1/datasets/")
        data = resp.json()
        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_rules_list_returns_paginated_shape(self, auth_client, uploaded):
        resp = auth_client.get(rules_url(uploaded["id"]))
        data = resp.json()
        assert "count" in data
        assert "results" in data

    def test_reports_list_returns_paginated_shape(self, auth_client, uploaded):
        resp = auth_client.get(reports_url(uploaded["id"]))
        data = resp.json()
        assert "count" in data
        assert "results" in data

    def test_trends_list_not_paginated(self, auth_client, uploaded):
        resp = auth_client.get(trends_url(uploaded["id"]))
        # TrendView returns a plain list — no pagination envelope
        assert isinstance(resp.json(), list)

    def test_count_reflects_total_items(self, auth_client, uploaded):
        resp = auth_client.get("/api/v1/datasets/")
        assert resp.json()["count"] == 1

    def test_next_is_none_when_single_page(self, auth_client, uploaded):
        resp = auth_client.get("/api/v1/datasets/")
        assert resp.json()["next"] is None

    def test_previous_is_none_on_first_page(self, auth_client, uploaded):
        resp = auth_client.get("/api/v1/datasets/")
        assert resp.json()["previous"] is None


# ── page_size parameter ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPageSize:
    def test_page_size_limits_results(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        # Upload 3 datasets
        for i in range(3):
            f = io.BytesIO(VALID_CSV)
            f.name = f"data_{i}.csv"
            auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get("/api/v1/datasets/?page_size=2")
        assert len(resp.json()["results"]) == 2
        assert resp.json()["count"] == 3
        assert resp.json()["next"] is not None

    def test_page_2_returns_remaining_items(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        for i in range(3):
            f = io.BytesIO(VALID_CSV)
            f.name = f"data_{i}.csv"
            auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get("/api/v1/datasets/?page_size=2&page=2")
        assert len(resp.json()["results"]) == 1
        assert resp.json()["previous"] is not None

    def test_rules_page_size(self, auth_client, uploaded):
        for col in ["id", "age", "email"]:
            auth_client.post(
                rules_url(uploaded["id"]),
                {"column_name": col, "rule_type": "null_check", "rule_config": {}},
                format="json",
            )
        resp = auth_client.get(f"{rules_url(uploaded['id'])}?page_size=2")
        assert len(resp.json()["results"]) == 2
        assert resp.json()["count"] == 3


# ── Dataset filters ───────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDatasetFilters:
    def test_filter_by_file_type_csv(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        # Upload CSV
        auth_client.post(UPLOAD_URL, {"file": csv_file()}, format="multipart")
        # Upload JSON
        f = io.BytesIO(b'[{"id":1,"name":"Alice"}]')
        f.name = "data.json"
        auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get("/api/v1/datasets/?file_type=csv")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["file_type"] == "csv"

    def test_filter_by_file_type_json(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(UPLOAD_URL, {"file": csv_file()}, format="multipart")
        f = io.BytesIO(b'[{"id":1,"name":"Alice"}]')
        f.name = "data.json"
        auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")

        resp = auth_client.get("/api/v1/datasets/?file_type=json")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["file_type"] == "json"

    def test_search_matches_file_title(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(
            UPLOAD_URL,
            {"file": csv_file(), "file_title": "Sales Report Q1"},
            format="multipart",
        )
        auth_client.post(
            UPLOAD_URL,
            {"file": csv_file("other.csv"), "file_title": "Employee Records"},
            format="multipart",
        )

        resp = auth_client.get("/api/v1/datasets/?search=sales")
        assert resp.json()["count"] == 1
        assert "Sales" in resp.json()["results"][0]["file_title"]

    def test_search_matches_file_name(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(
            UPLOAD_URL, {"file": csv_file("invoices.csv")}, format="multipart"
        )
        auth_client.post(
            UPLOAD_URL, {"file": csv_file("customers.csv")}, format="multipart"
        )

        resp = auth_client.get("/api/v1/datasets/?search=invoice")
        assert resp.json()["count"] == 1

    def test_search_is_case_insensitive(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(
            UPLOAD_URL,
            {"file": csv_file(), "file_title": "SALES DATA"},
            format="multipart",
        )
        resp = auth_client.get("/api/v1/datasets/?search=sales")
        assert resp.json()["count"] == 1

    def test_no_match_returns_empty(self, auth_client, uploaded):
        resp = auth_client.get("/api/v1/datasets/?search=nonexistent")
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_combined_filter_and_search(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(
            UPLOAD_URL,
            {"file": csv_file(), "file_title": "Sales CSV"},
            format="multipart",
        )
        f = io.BytesIO(b'[{"id":1}]')
        f.name = "sales.json"
        auth_client.post(
            UPLOAD_URL,
            {"file": f, "file_title": "Sales JSON"},
            format="multipart",
        )

        resp = auth_client.get("/api/v1/datasets/?search=sales&file_type=csv")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["file_type"] == "csv"


# ── Rule filters ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRuleFilters:
    def test_filter_by_rule_type(self, auth_client, uploaded):
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "range_check",
                "rule_config": {"min": 0, "max": 120},
            },
            format="json",
        )

        resp = auth_client.get(f"{rules_url(uploaded['id'])}?rule_type=null_check")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["rule_type"] == "null_check"

    def test_filter_by_column_name(self, auth_client, uploaded):
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
            format="json",
        )

        resp = auth_client.get(f"{rules_url(uploaded['id'])}?column_name=email")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["column_name"] == "email"

    def test_no_match_returns_empty(self, auth_client, uploaded):
        resp = auth_client.get(f"{rules_url(uploaded['id'])}?rule_type=type_check")
        assert resp.json()["count"] == 0

    def test_combined_rule_type_and_column(self, auth_client, uploaded):
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "id", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )

        resp = auth_client.get(
            f"{rules_url(uploaded['id'])}?rule_type=null_check&column_name=email"
        )
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["column_name"] == "email"


# ── Report filters ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestReportFilters:
    @pytest.fixture
    def with_rule(self, auth_client, uploaded):
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        return uploaded

    def test_filter_by_status_completed(self, auth_client, with_rule):
        auth_client.post(run_check_url(with_rule["id"]))
        resp = auth_client.get(f"{reports_url(with_rule['id'])}?status=completed")
        assert resp.json()["count"] == 1
        assert resp.json()["results"][0]["status"] == "completed"

    def test_filter_by_status_no_match(self, auth_client, with_rule):
        auth_client.post(run_check_url(with_rule["id"]))
        resp = auth_client.get(f"{reports_url(with_rule['id'])}?status=failed")
        assert resp.json()["count"] == 0

    def test_date_from_filters_reports(self, auth_client, with_rule):
        auth_client.post(run_check_url(with_rule["id"]))
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{reports_url(with_rule['id'])}?date_from={tomorrow}")
        assert resp.json()["count"] == 0

    def test_date_to_filters_reports(self, auth_client, with_rule):
        auth_client.post(run_check_url(with_rule["id"]))
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{reports_url(with_rule['id'])}?date_to={yesterday}")
        assert resp.json()["count"] == 0

    def test_date_range_includes_today(self, auth_client, with_rule):
        auth_client.post(run_check_url(with_rule["id"]))
        today = date.today().isoformat()
        resp = auth_client.get(
            f"{reports_url(with_rule['id'])}?date_from={today}&date_to={today}"
        )
        assert resp.json()["count"] == 1


# ── Trend filters ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTrendFilters:
    @pytest.fixture
    def with_trend(self, auth_client, uploaded):
        """Run a check to generate a TrendMetric for today."""
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        auth_client.post(run_check_url(uploaded["id"]))
        return uploaded

    def test_trends_returns_list(self, auth_client, with_trend):
        resp = auth_client.get(trends_url(with_trend["id"]))
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1

    def test_date_from_excludes_past(self, auth_client, with_trend):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{trends_url(with_trend['id'])}?date_from={tomorrow}")
        assert resp.json() == []

    def test_date_to_excludes_future(self, auth_client, with_trend):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = auth_client.get(f"{trends_url(with_trend['id'])}?date_to={yesterday}")
        assert resp.json() == []

    def test_date_range_includes_today(self, auth_client, with_trend):
        today = date.today().isoformat()
        resp = auth_client.get(
            f"{trends_url(with_trend['id'])}?date_from={today}&date_to={today}"
        )
        assert len(resp.json()) == 1
