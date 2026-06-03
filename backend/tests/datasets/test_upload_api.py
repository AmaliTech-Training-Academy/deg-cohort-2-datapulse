"""
tests/datasets/test_upload_api.py
Tests for POST /api/v1/datasets/upload/, GET /api/v1/datasets/,
GET /api/v1/datasets/<id>/, DELETE /api/v1/datasets/<id>/
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"
LIST_URL = "/api/v1/datasets/"

VALID_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
    b"3,35,carol@test.com,75\n"
)


def csv_payload(content=VALID_CSV, name="data.csv"):
    f = io.BytesIO(content)
    f.name = name
    return {"file": f}


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    """Upload a valid CSV and return the response dict."""
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(UPLOAD_URL, csv_payload(), format="multipart")
    assert resp.status_code == 201
    return resp.json()


# ── Upload ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDatasetUpload:
    """
    Upload-specific assertions all share the `uploaded` fixture so MEDIA_ROOT
    is configured and the POST runs exactly once per test, not once per assertion.
    """

    def test_upload_csv_returns_201(self, uploaded):
        # Status code already asserted inside the fixture; confirm data present.
        assert uploaded["id"] is not None

    def test_response_contains_expected_fields(self, uploaded):
        for field in (
            "id",
            "file_name",
            "file_type",
            "row_count",
            "columns",
            "created_at",
        ):
            assert field in uploaded

    def test_file_path_not_in_response(self, uploaded):
        assert "file_path" not in uploaded

    def test_row_count_correct(self, uploaded):
        assert uploaded["row_count"] == 3

    def test_columns_extracted(self, uploaded):
        assert set(uploaded["columns"]) == {"id", "age", "email", "score"}

    def test_upload_json_returns_201(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        content = b'[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]'
        f = io.BytesIO(content)
        f.name = "data.json"
        resp = auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")
        assert resp.status_code == 201
        assert resp.json()["file_type"] == "json"

    def test_upload_with_title_and_description(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        payload = csv_payload()
        payload["file_title"] = "My Dataset"
        payload["description"] = "Test notes"
        resp = auth_client.post(UPLOAD_URL, payload, format="multipart")
        assert resp.json()["file_title"] == "My Dataset"
        assert resp.json()["description"] == "Test notes"

    def test_unauthenticated_upload_returns_401(self, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        resp = api_client.post(UPLOAD_URL, csv_payload(), format="multipart")
        assert resp.status_code == 401

    def test_no_file_returns_400(self, auth_client):
        resp = auth_client.post(UPLOAD_URL, {}, format="multipart")
        assert resp.status_code == 400

    def test_oversized_file_returns_400(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        from unittest.mock import MagicMock

        from datasets.services.file_service import (
            MAX_FILE_SIZE_BYTES,
            FileUploadService,
        )
        from rest_framework.exceptions import ValidationError

        mock_file = MagicMock()
        mock_file.size = MAX_FILE_SIZE_BYTES + 1
        mock_file.name = "big.csv"
        mock_file.read.return_value = b"id,name\n1,x\n"
        mock_file.seek = lambda x: None
        mock_file.chunks.return_value = [b"id,name\n1,x\n"]

        svc = FileUploadService()
        with pytest.raises(ValidationError, match="MB limit"):
            svc._check_size(mock_file)


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDatasetList:
    def test_list_returns_200(self, auth_client):
        resp = auth_client.get(LIST_URL)
        assert resp.status_code == 200

    def test_list_empty_initially(self, auth_client):
        resp = auth_client.get(LIST_URL)
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_list_shows_uploaded_dataset(self, auth_client, uploaded):
        resp = auth_client.get(LIST_URL)
        ids = [d["id"] for d in resp.json()["results"]]
        assert uploaded["id"] in ids

    def test_list_isolated_per_user(
        self, auth_client, uploaded, api_client, admin_user
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(LIST_URL)
        assert resp.json()["count"] == 0
        assert resp.json()["results"] == []

    def test_unauthenticated_list_returns_401(self, api_client):
        resp = api_client.get(LIST_URL)
        assert resp.status_code == 401


# ── Detail ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDatasetDetail:
    def test_get_returns_200(self, auth_client, uploaded):
        resp = auth_client.get(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 200

    def test_get_returns_correct_data(self, auth_client, uploaded):
        resp = auth_client.get(f"{LIST_URL}{uploaded['id']}/")
        assert resp.json()["id"] == uploaded["id"]

    def test_get_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 404

    def test_get_nonexistent_returns_404(self, auth_client):
        resp = auth_client.get(f"{LIST_URL}00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDatasetDelete:
    def test_delete_returns_204(self, auth_client, uploaded):
        resp = auth_client.delete(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 204

    def test_delete_removes_record(self, auth_client, uploaded):
        auth_client.delete(f"{LIST_URL}{uploaded['id']}/")
        resp = auth_client.get(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 404

    def test_delete_other_user_dataset_returns_404(
        self, api_client, admin_user, uploaded
    ):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.delete(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 404

    def test_unauthenticated_delete_returns_401(self, api_client, uploaded):
        resp = api_client.delete(f"{LIST_URL}{uploaded['id']}/")
        assert resp.status_code == 401
