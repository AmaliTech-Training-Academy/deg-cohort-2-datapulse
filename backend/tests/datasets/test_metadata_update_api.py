"""
tests/datasets/test_metadata_update_api.py
Tests for PATCH /api/v1/datasets/<id>/

Verifies:
  - 200 returned with updated metadata
  - file_title updated when provided
  - description updated when provided
  - both fields updated together
  - omitted field is left unchanged
  - file content fields (file_name, file_type, row_count, columns,
    file_version) are never affected
  - empty string is accepted for file_title and description
  - 400 when request body is empty (no fields provided)
  - 401 for unauthenticated requests
  - 404 when dataset belongs to another user
  - 404 for a nonexistent dataset ID
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"
LIST_URL = "/api/v1/datasets/"

VALID_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
)


def detail_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    """Upload a dataset with an explicit title and description."""
    settings.MEDIA_ROOT = str(tmp_path)
    f = io.BytesIO(VALID_CSV)
    f.name = "data.csv"
    resp = auth_client.post(
        UPLOAD_URL,
        {"file": f, "file_title": "Original Title", "description": "Original description"},
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


# ── Success cases ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMetadataUpdateSuccess:
    def test_returns_200(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.status_code == 200

    def test_file_title_updated(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "Updated Title"},
            format="json",
        )
        assert resp.json()["file_title"] == "Updated Title"

    def test_description_updated(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"description": "Updated description"},
            format="json",
        )
        assert resp.json()["description"] == "Updated description"

    def test_both_fields_updated_together(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title", "description": "New description"},
            format="json",
        )
        assert resp.json()["file_title"] == "New Title"
        assert resp.json()["description"] == "New description"

    def test_omitting_file_title_leaves_it_unchanged(self, auth_client, uploaded):
        auth_client.patch(
            detail_url(uploaded["id"]),
            {"description": "Changed description"},
            format="json",
        )
        resp = auth_client.get(detail_url(uploaded["id"]))
        assert resp.json()["file_title"] == "Original Title"

    def test_omitting_description_leaves_it_unchanged(self, auth_client, uploaded):
        auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "Changed Title"},
            format="json",
        )
        resp = auth_client.get(detail_url(uploaded["id"]))
        assert resp.json()["description"] == "Original description"

    def test_empty_string_accepted_for_file_title(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": ""},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["file_title"] == ""

    def test_empty_string_accepted_for_description(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"description": ""},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == ""

    def test_dataset_id_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["id"] == uploaded["id"]


# ── File content fields are immutable ─────────────────────────────────────────


@pytest.mark.django_db
class TestFileFieldsUnchanged:
    def test_file_name_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["file_name"] == uploaded["file_name"]

    def test_file_type_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["file_type"] == uploaded["file_type"]

    def test_row_count_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["row_count"] == uploaded["row_count"]

    def test_columns_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["columns"] == uploaded["columns"]

    def test_file_version_unchanged(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "New Title"},
            format="json",
        )
        assert resp.json()["file_version"] == uploaded["file_version"]


# ── Validation errors ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMetadataUpdateValidation:
    def test_empty_body_returns_400(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {},
            format="json",
        )
        assert resp.status_code == 400

    def test_file_title_too_long_returns_400(self, auth_client, uploaded):
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "x" * 256},
            format="json",
        )
        assert resp.status_code == 400

    def test_unknown_fields_are_ignored(self, auth_client, uploaded):
        # Extra fields should not raise an error — serializer ignores them
        resp = auth_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "Valid", "unknown_field": "ignored"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["file_title"] == "Valid"


# ── Auth and ownership ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMetadataUpdateAuth:
    def test_unauthenticated_returns_401(self, api_client, uploaded):
        resp = api_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.patch(
            detail_url(uploaded["id"]),
            {"file_title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404

    def test_nonexistent_dataset_returns_404(self, auth_client):
        resp = auth_client.patch(
            detail_url("00000000-0000-0000-0000-000000000000"),
            {"file_title": "Does not exist"},
            format="json",
        )
        assert resp.status_code == 404
