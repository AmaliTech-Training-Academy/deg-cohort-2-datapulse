"""
tests/datasets/test_file_update_api.py
Tests for PATCH /api/v1/datasets/<id>/file/

Verifies:
  - 200 returned with updated metadata
  - file_version incremented
  - columns, row_count, file_name updated to match new file
  - file_path is NOT in the response
  - stale_rule_columns populated when new file drops a column
  - stale_rule_columns empty when all old columns are present in new file
  - previous QualityReports preserved (score history kept)
  - file_title and description unchanged after replacement
  - 400 on missing file
  - 400 on oversized file (via service unit test)
  - 401 for unauthenticated requests
  - 404 when dataset belongs to another user
  - 404 for a nonexistent dataset ID
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"
RUN_CHECK_URL_TPL = "/api/v1/datasets/{}/run-check/"


def file_update_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/file/"


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


# ── CSV fixtures ───────────────────────────────────────────────────────────────

ORIGINAL_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
    b"3,35,carol@test.com,75\n"
)

# Same columns — clean replacement, no stale columns
REPLACEMENT_CSV_SAME_COLS = (
    b"id,age,email,score\n"
    b"10,40,dave@test.com,95\n"
    b"11,45,eve@test.com,70\n"
    b"12,50,frank@test.com,80\n"
    b"13,55,grace@test.com,65\n"
)

# Drops the `score` column — should surface as stale
REPLACEMENT_CSV_FEWER_COLS = (
    b"id,age,email\n" b"10,40,dave@test.com\n" b"11,45,eve@test.com\n"
)

# JSON replacement — same logical columns
REPLACEMENT_JSON = (
    b'[{"id":10,"age":40,"email":"dave@test.com","score":95},'
    b'{"id":11,"age":45,"email":"eve@test.com","score":70}]'
)


def csv_file(content=ORIGINAL_CSV, name="data.csv"):
    f = io.BytesIO(content)
    f.name = name
    return f


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    """Upload the original CSV and return the response dict."""
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(
        UPLOAD_URL,
        {"file": csv_file(), "file_title": "My Dataset", "description": "Original"},
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


# ── Success cases ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestFileUpdateSuccess:
    def test_returns_200(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 200

    def test_file_version_incremented(self, auth_client, uploaded):
        assert uploaded["file_version"] == 1
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.json()["file_version"] == 2

    def test_version_increments_again_on_second_replace(self, auth_client, uploaded):
        auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "v2.csv")},
            format="multipart",
        )
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "v3.csv")},
            format="multipart",
        )
        assert resp.json()["file_version"] == 3

    def test_row_count_updated(self, auth_client, uploaded):
        # Original has 3 rows; replacement has 4
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.json()["row_count"] == 4

    def test_file_name_updated(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "replaced.csv")},
            format="multipart",
        )
        assert resp.json()["file_name"] == "replaced.csv"

    def test_columns_updated(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_FEWER_COLS, "fewer.csv")},
            format="multipart",
        )
        assert set(resp.json()["columns"]) == {"id", "age", "email"}

    def test_file_type_updated_to_json(self, auth_client, uploaded):
        f = io.BytesIO(REPLACEMENT_JSON)
        f.name = "data.json"
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": f},
            format="multipart",
        )
        assert resp.json()["file_type"] == "json"

    def test_file_path_not_in_response(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert "file_path" not in resp.json()

    def test_file_title_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.json()["file_title"] == "My Dataset"

    def test_description_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.json()["description"] == "Original"

    def test_dataset_id_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.json()["id"] == uploaded["id"]


# ── Stale column detection ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestStaleColumns:
    def test_no_stale_columns_when_same_schema(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "same.csv")},
            format="multipart",
        )
        assert resp.json()["stale_rule_columns"] == []

    def test_stale_columns_listed_when_column_dropped(self, auth_client, uploaded):
        # Original has `score`; replacement drops it
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_FEWER_COLS, "fewer.csv")},
            format="multipart",
        )
        assert resp.json()["stale_rule_columns"] == ["score"]

    def test_stale_columns_sorted_alphabetically(self, auth_client, uploaded):
        # Drop `age` and `score` — result should be sorted
        minimal = b"id,email\n1,a@test.com\n"
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(minimal, "min.csv")},
            format="multipart",
        )
        stale = resp.json()["stale_rule_columns"]
        assert stale == sorted(stale)
        assert "age" in stale
        assert "score" in stale


# ── Score history preserved ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestScoreHistoryPreserved:
    def test_prior_reports_still_exist_after_file_replace(
        self, auth_client, uploaded, settings, tmp_path
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        did = uploaded["id"]

        # Create a rule and run a check to generate a QualityReport
        auth_client.post(
            rules_url(did),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        run_resp = auth_client.post(RUN_CHECK_URL_TPL.format(did))
        assert run_resp.status_code == 201
        report_id = run_resp.json()["id"]

        # Replace the file
        auth_client.patch(
            file_update_url(did),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )

        # The original report is still retrievable
        report_resp = auth_client.get(f"/api/v1/reports/{report_id}/")
        assert report_resp.status_code == 200
        assert report_resp.json()["id"] == report_id

    def test_report_list_grows_after_recheck_on_new_file(
        self, auth_client, uploaded, settings, tmp_path
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        did = uploaded["id"]

        auth_client.post(
            rules_url(did),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )

        # First check on original file
        auth_client.post(RUN_CHECK_URL_TPL.format(did))

        # Replace file and run second check
        auth_client.patch(
            file_update_url(did),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        auth_client.post(RUN_CHECK_URL_TPL.format(did))

        reports = auth_client.get(f"/api/v1/datasets/{did}/reports/").json()
        assert reports["count"] == 2


# ── Auth and ownership ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestFileUpdateAuth:
    def test_unauthenticated_returns_401(self, api_client, uploaded):
        resp = api_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 404

    def test_nonexistent_dataset_returns_404(self, auth_client):
        resp = auth_client.patch(
            file_update_url("00000000-0000-0000-0000-000000000000"),
            {"file": csv_file(REPLACEMENT_CSV_SAME_COLS, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 404


# ── Validation errors ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestFileUpdateValidation:
    def test_missing_file_returns_400(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_empty_csv_returns_400(self, auth_client, uploaded):
        f = io.BytesIO(b"id,name\n")  # header only, no data rows
        f.name = "empty.csv"
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": f},
            format="multipart",
        )
        assert resp.status_code == 400
