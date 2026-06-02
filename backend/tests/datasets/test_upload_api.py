"""
tests/datasets/test_upload_api.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for the dataset upload and management API.

Endpoints tested
────────────────
  POST   /api/v1/datasets/upload/
  GET    /api/v1/datasets/
  GET    /api/v1/datasets/{id}/
  DELETE /api/v1/datasets/{id}/

Every request uses a real JWT token via auth_client from conftest.
Files are uploaded with multipart/form-data exactly as a real client would.
"""

import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

UPLOAD_URL = "/api/v1/datasets/upload/"
LIST_URL   = "/api/v1/datasets/"
DETAIL_URL = lambda id: f"/api/v1/datasets/{id}/"

VALID_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"
    "2,30,bob@test.com,92\n"
    "3,35,carol@test.com,75\n"
)


def csv_upload(client, content=VALID_CSV, name="data.csv", extra=None):
    """POST a CSV to the upload endpoint using multipart/form-data."""
    payload = {"file": io.BytesIO(content.encode()), **(extra or {})}
    payload["file"].name = name
    return client.post(UPLOAD_URL, payload, format="multipart")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD — happy paths
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDatasetUpload:

    def test_upload_csv_returns_201(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        assert csv_upload(auth_client).status_code == status.HTTP_201_CREATED

    def test_upload_csv_response_has_required_fields(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        data = csv_upload(auth_client).json()
        for field in ["id", "file_type", "row_count", "columns", "created_at"]:
            assert field in data, f"Missing field: {field}"

    def test_upload_csv_row_count_correct(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        assert csv_upload(auth_client).json()["row_count"] == 3

    def test_upload_csv_columns_correct(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        assert csv_upload(auth_client).json()["columns"] == ["id", "age", "email", "score"]

    def test_upload_csv_file_path_absent_from_response(self, auth_client, settings, tmp_path):
        """file_path is a server path — must never be exposed to the client."""
        settings.MEDIA_ROOT = str(tmp_path)
        assert "file_path" not in csv_upload(auth_client).json()

    def test_upload_with_file_title(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        payload = {
            "file": io.BytesIO(VALID_CSV.encode()),
            "file_title": "Customer Records Q1",
        }
        payload["file"].name = "data.csv"
        response = auth_client.post(UPLOAD_URL, payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["file_title"] == "Customer Records Q1"

    def test_upload_json_returns_201(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        json_content = '[{"id":1,"age":25,"email":"a@b.com"},{"id":2,"age":30,"email":"c@d.com"}]'
        payload = {"file": io.BytesIO(json_content.encode())}
        payload["file"].name = "data.json"
        response = auth_client.post(UPLOAD_URL, payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["file_type"] == "json"
        assert response.json()["row_count"] == 2

    def test_upload_requires_authentication(self, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        payload = {"file": io.BytesIO(VALID_CSV.encode())}
        payload["file"].name = "data.csv"
        response = api_client.post(UPLOAD_URL, payload, format="multipart")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD — validation errors
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDatasetUploadValidation:

    def test_no_file_returns_400(self, auth_client):
        assert auth_client.post(UPLOAD_URL, {}, format="multipart").status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_csv_returns_400(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        assert csv_upload(auth_client, content="id,age,email\n").status_code == status.HTTP_400_BAD_REQUEST

    def test_json_array_of_arrays_returns_400(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        payload = {"file": io.BytesIO(b"[[1,2],[3,4]]")}
        payload["file"].name = "data.json"
        assert auth_client.post(UPLOAD_URL, payload, format="multipart").status_code == status.HTTP_400_BAD_REQUEST

    def test_bom_csv_succeeds_and_columns_clean(self, auth_client, settings, tmp_path):
        """BOM-encoded CSV must parse without error and columns must be clean."""
        settings.MEDIA_ROOT = str(tmp_path)
        bom_csv = b"\xef\xbb\xbfid,age,email\n1,25,a@b.com\n"
        payload = {"file": io.BytesIO(bom_csv)}
        payload["file"].name = "bom.csv"
        response = auth_client.post(UPLOAD_URL, payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["columns"][0] == "id"


# ═══════════════════════════════════════════════════════════════════════════════
# LIST DATASETS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDatasetList:

    def test_list_returns_200(self, auth_client):
        assert auth_client.get(LIST_URL).status_code == status.HTTP_200_OK

    def test_list_empty_for_new_user(self, auth_client):
        results = auth_client.get(LIST_URL).json().get("results", auth_client.get(LIST_URL).json())
        assert results == []

    def test_list_shows_uploaded_dataset(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        csv_upload(auth_client)
        results = auth_client.get(LIST_URL).json().get("results", auth_client.get(LIST_URL).json())
        assert len(results) == 1

    def test_list_shows_only_own_datasets(self, auth_client, api_client, regular_user, settings, tmp_path):
        """User A must not see User B's datasets."""
        settings.MEDIA_ROOT = str(tmp_path)
        csv_upload(auth_client)

        other_user = User.objects.create_user(
            username="other", email="other@test.com", password="pass", role="user"
        )
        other_token = RefreshToken.for_user(other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token.access_token}")
        payload = {"file": io.BytesIO(VALID_CSV.encode())}
        payload["file"].name = "other.csv"
        api_client.post(UPLOAD_URL, payload, format="multipart")

        # Regular user must only see their own dataset
        results = auth_client.get(LIST_URL).json().get("results", auth_client.get(LIST_URL).json())
        assert len(results) == 1

    def test_list_requires_authentication(self, api_client):
        assert api_client.get(LIST_URL).status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET DETAIL
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDatasetDetail:

    def test_get_own_dataset_returns_200(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        assert auth_client.get(DETAIL_URL(upload_id)).status_code == status.HTTP_200_OK

    def test_get_own_dataset_id_matches(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        assert auth_client.get(DETAIL_URL(upload_id)).json()["id"] == upload_id

    def test_get_other_users_dataset_returns_404(self, auth_client, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        other_user = User.objects.create_user(
            username="other2", email="other2@test.com", password="pass", role="user"
        )
        other_token = RefreshToken.for_user(other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token.access_token}")
        assert api_client.get(DETAIL_URL(upload_id)).status_code == status.HTTP_404_NOT_FOUND

    def test_get_nonexistent_dataset_returns_404(self, auth_client):
        assert auth_client.get(DETAIL_URL("00000000-0000-0000-0000-000000000000")).status_code == status.HTTP_404_NOT_FOUND


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE DATASET
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDatasetDelete:

    def test_delete_own_dataset_returns_204(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        assert auth_client.delete(DETAIL_URL(upload_id)).status_code == status.HTTP_204_NO_CONTENT

    def test_deleted_dataset_not_in_list(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        auth_client.delete(DETAIL_URL(upload_id))
        results = auth_client.get(LIST_URL).json().get("results", auth_client.get(LIST_URL).json())
        assert upload_id not in [d["id"] for d in results]

    def test_deleted_dataset_returns_404_on_get(self, auth_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        auth_client.delete(DETAIL_URL(upload_id))
        assert auth_client.get(DETAIL_URL(upload_id)).status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_users_dataset_returns_404(self, auth_client, api_client, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        upload_id = csv_upload(auth_client).json()["id"]
        other_user = User.objects.create_user(
            username="del_other", email="del_other@test.com", password="pass", role="user"
        )
        other_token = RefreshToken.for_user(other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token.access_token}")
        assert api_client.delete(DETAIL_URL(upload_id)).status_code == status.HTTP_404_NOT_FOUND
