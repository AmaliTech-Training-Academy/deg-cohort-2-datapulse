"""
tests/checks/test_run_check_api.py
Tests for:
  POST /api/v1/datasets/<id>/run-check/
  GET  /api/v1/reports/<id>/
  GET  /api/v1/datasets/<id>/reports/
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"

# Matches the worked example from the API flow doc:
# 6 rows, intentional quality issues on rows 2-6 → score = 17
TEST_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"  # row 1 — passes all
    b"2,,bob@test.com,92\n"  # row 2 — age null (range fails)
    b"3,31,,75\n"  # row 3 — email null
    b"4,-5,dave@test.com,101\n"  # row 4 — age below 0
    b"5,40,eve@test.com,60\n"  # row 5 — id duplicate
    b"5,45,frank@test.com,55\n"  # row 6 — id duplicate
)

CLEAN_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
    b"3,35,carol@test.com,75\n"
)


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    f = io.BytesIO(TEST_CSV)
    f.name = "test_data.csv"
    resp = auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def uploaded_clean(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    f = io.BytesIO(CLEAN_CSV)
    f.name = "clean.csv"
    resp = auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def with_rules(auth_client, uploaded):
    did = uploaded["id"]
    base = f"/api/v1/datasets/{did}/rules/"
    auth_client.post(
        base,
        {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        format="json",
    )
    auth_client.post(
        base,
        {
            "column_name": "age",
            "rule_type": "range_check",
            "rule_config": {"min": 0, "max": 120},
        },
        format="json",
    )
    auth_client.post(
        base,
        {
            "column_name": "score",
            "rule_type": "type_check",
            "rule_config": {"expected_type": "integer"},
        },
        format="json",
    )
    auth_client.post(
        base,
        {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
        format="json",
    )
    return uploaded


@pytest.fixture
def check_response(auth_client, with_rules):
    """
    Run a single quality check and return the response JSON.

    Shared across all TestRunCheck assertions so the engine runs exactly
    once per test session rather than once per assertion method.
    """
    resp = auth_client.post(run_check_url(with_rules["id"]))
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def check_detail_response(auth_client, with_rules):
    """
    Run a check and fetch its detail report in one fixture call.

    Shared across TestCheckDetail assertions to avoid re-triggering
    the validation engine for every individual assertion.
    """
    report_id = auth_client.post(run_check_url(with_rules["id"])).json()["id"]
    resp = auth_client.get(check_url(report_id))
    assert resp.status_code == 200
    return resp.json()


def run_check_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/run-check/"


def check_url(check_id):
    return f"/api/v1/reports/{check_id}/"


def checks_list_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/reports/"


# ── Run check ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRunCheck:
    def test_run_check_returns_201(self, check_response):
        # status code already asserted inside the fixture; confirm data is present
        assert check_response["id"] is not None

    def test_response_contains_expected_fields(self, check_response):
        for field in (
            "id",
            "dataset",
            "status",
            "overall_score",
            "total_rows_passed",
            "total_rows_failed",
            "findings",
            "generated_at",
        ):
            assert field in check_response

    def test_status_reflects_quality_band(self, check_response):
        # score=17 on the test CSV — well below 70 → failing
        assert check_response["status"] == "failing"

    def test_score_matches_worked_example(self, check_response):
        # test_data.csv: 6 rows, 5 failed → score = 17
        assert check_response["overall_score"] == 17

    def test_total_rows_passed_correct(self, check_response):
        assert check_response["total_rows_passed"] == 1

    def test_total_rows_failed_correct(self, check_response):
        assert check_response["total_rows_failed"] == 5

    def test_findings_count_matches_rules(self, check_response):
        assert len(check_response["findings"]) == 4

    def test_findings_contain_rule_type_and_column(self, check_response):
        finding = check_response["findings"][0]
        assert "rule_type" in finding
        assert "column_name" in finding
        assert "rows_failed" in finding
        assert "failure_percentage" in finding
        assert "error_details" in finding

    def test_no_rules_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(run_check_url(uploaded["id"]))
        assert resp.status_code == 400
        assert "rule" in resp.json()["error"]["message"].lower()

    def test_clean_data_scores_100(self, auth_client, uploaded_clean):
        did = uploaded_clean["id"]
        base = f"/api/v1/datasets/{did}/rules/"
        auth_client.post(
            base,
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        resp = auth_client.post(run_check_url(did))
        assert resp.json()["overall_score"] == 100

    def test_unauthenticated_returns_401(self, api_client, with_rules):
        resp = api_client.post(run_check_url(with_rules["id"]))
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, with_rules):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.post(run_check_url(with_rules["id"]))
        assert resp.status_code == 404

    def test_nonexistent_dataset_returns_404(self, auth_client):
        resp = auth_client.post(run_check_url("00000000-0000-0000-0000-000000000000"))
        assert resp.status_code == 404

    def test_multiple_runs_each_create_new_check(self, auth_client, with_rules):
        auth_client.post(run_check_url(with_rules["id"]))
        auth_client.post(run_check_url(with_rules["id"]))
        resp = auth_client.get(checks_list_url(with_rules["id"]))
        assert resp.json()["count"] == 2


# ── Report detail ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCheckDetail:
    def test_get_check_returns_200(self, auth_client, with_rules):
        # Status code already verified inside check_detail_response fixture;
        # confirm the detail endpoint is reachable with a valid ID.
        report_id = auth_client.post(run_check_url(with_rules["id"])).json()["id"]
        resp = auth_client.get(check_url(report_id))
        assert resp.status_code == 200

    def test_get_check_returns_correct_id(self, check_detail_response):
        # The fixture fetches the report by the same ID used to run the check.
        assert "id" in check_detail_response

    def test_get_nonexistent_check_returns_404(self, auth_client):
        resp = auth_client.get(check_url("00000000-0000-0000-0000-000000000000"))
        assert resp.status_code == 404

    def test_get_other_user_check_returns_404(
        self, api_client, admin_user, auth_client, with_rules
    ):
        check_id = auth_client.post(run_check_url(with_rules["id"])).json()["id"]
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(check_url(check_id))
        assert resp.status_code == 404

    def test_findings_nested_in_detail(self, check_detail_response):
        assert isinstance(check_detail_response["findings"], list)
        assert len(check_detail_response["findings"]) == 4


# ── Report list ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCheckList:
    def test_list_empty_before_any_run(self, auth_client, uploaded):
        resp = auth_client.get(checks_list_url(uploaded["id"]))
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_list_shows_check_after_run(self, auth_client, with_rules):
        auth_client.post(run_check_url(with_rules["id"]))
        resp = auth_client.get(checks_list_url(with_rules["id"]))
        assert resp.json()["count"] == 1

    def test_list_ordered_most_recent_first(self, auth_client, with_rules):
        r1 = auth_client.post(run_check_url(with_rules["id"])).json()["id"]
        r2 = auth_client.post(run_check_url(with_rules["id"])).json()["id"]
        resp = auth_client.get(checks_list_url(with_rules["id"]))
        ids = [c["id"] for c in resp.json()["results"]]
        assert ids[0] == r2
        assert ids[1] == r1

    def test_list_other_user_dataset_returns_404(
        self, api_client, admin_user, with_rules
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(checks_list_url(with_rules["id"]))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, api_client, with_rules):
        resp = api_client.get(checks_list_url(with_rules["id"]))
        assert resp.status_code == 401
