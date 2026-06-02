"""
tests/rules/test_rules_api.py
Tests for the Rule Management API:
  POST   /api/v1/datasets/<id>/rules/
  GET    /api/v1/datasets/<id>/rules/
  GET    /api/v1/rules/<id>/
  PATCH  /api/v1/rules/<id>/
  DELETE /api/v1/rules/<id>/
"""

import io

import pytest

from datasets.models import Dataset
from rules.models import ValidationRule

UPLOAD_URL = "/api/v1/datasets/upload/"
VALID_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
)


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    f = io.BytesIO(VALID_CSV)
    f.name = "data.csv"
    resp = auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


def rule_url(rule_id):
    return f"/api/v1/rules/{rule_id}/"


# ── Create (POST) ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateRule:
    def test_create_null_check_returns_201(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 201

    def test_create_range_check_returns_201(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "range_check",
                "rule_config": {"min": 0, "max": 120},
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_create_type_check_returns_201(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "score",
                "rule_type": "type_check",
                "rule_config": {"expected_type": "integer"},
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_create_uniqueness_check_returns_201(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 201

    def test_response_contains_id_and_fields(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        data = resp.json()
        for field in ("id", "column_name", "rule_type", "rule_config", "created_at"):
            assert field in data

    def test_invalid_column_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "nonexistent", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 400

    def test_type_check_invalid_expected_type_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "type_check",
                "rule_config": {"expected_type": "banana"},
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_range_check_missing_min_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "range_check",
                "rule_config": {"max": 100},
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_range_check_min_gte_max_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "range_check",
                "rule_config": {"min": 100, "max": 10},
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_duplicate_rule_returns_409(self, auth_client, uploaded):
        payload = {
            "column_name": "email",
            "rule_type": "null_check",
            "rule_config": {},
        }
        auth_client.post(rules_url(uploaded["id"]), payload, format="json")
        resp = auth_client.post(rules_url(uploaded["id"]), payload, format="json")
        assert resp.status_code == 409

    def test_unauthenticated_returns_401(self, api_client, uploaded):
        resp = api_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 404


# ── List (GET) ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestListRules:
    def test_list_empty_initially(self, auth_client, uploaded):
        resp = auth_client.get(rules_url(uploaded["id"]))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created_rules(self, auth_client, uploaded):
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        resp = auth_client.get(rules_url(uploaded["id"]))
        assert len(resp.json()) == 1

    def test_list_returns_all_rules(self, auth_client, uploaded):
        for col, rt, rc in [
            ("email", "null_check", {}),
            ("age", "range_check", {"min": 0, "max": 120}),
            ("id", "uniqueness_check", {}),
        ]:
            auth_client.post(
                rules_url(uploaded["id"]),
                {"column_name": col, "rule_type": rt, "rule_config": rc},
                format="json",
            )
        resp = auth_client.get(rules_url(uploaded["id"]))
        assert len(resp.json()) == 3

    def test_list_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(rules_url(uploaded["id"]))
        assert resp.status_code == 404


# ── Detail (GET) ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRuleDetail:
    def test_get_rule_returns_200(self, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        resp = auth_client.get(rule_url(rule_id))
        assert resp.status_code == 200
        assert resp.json()["id"] == rule_id

    def test_get_nonexistent_rule_returns_404(self, auth_client):
        resp = auth_client.get(rule_url("00000000-0000-0000-0000-000000000000"))
        assert resp.status_code == 404

    def test_get_other_user_rule_returns_404(self, api_client, admin_user, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.get(rule_url(rule_id))
        assert resp.status_code == 404


# ── Update (PATCH) ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateRule:
    def test_patch_rule_config_returns_200(self, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {
                "column_name": "age",
                "rule_type": "range_check",
                "rule_config": {"min": 0, "max": 120},
            },
            format="json",
        )
        rule_id = create.json()["id"]
        resp = auth_client.patch(
            rule_url(rule_id),
            {"rule_config": {"min": 18, "max": 65}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["rule_config"] == {"min": 18, "max": 65}

    def test_patch_does_not_change_rule_type(self, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        auth_client.patch(rule_url(rule_id), {"rule_type": "type_check"}, format="json")
        resp = auth_client.get(rule_url(rule_id))
        assert resp.json()["rule_type"] == "null_check"

    def test_patch_nonexistent_returns_404(self, auth_client):
        resp = auth_client.patch(
            rule_url("00000000-0000-0000-0000-000000000000"),
            {"rule_config": {}},
            format="json",
        )
        assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDeleteRule:
    def test_delete_returns_204(self, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        resp = auth_client.delete(rule_url(rule_id))
        assert resp.status_code == 204

    def test_delete_removes_rule(self, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        auth_client.delete(rule_url(rule_id))
        resp = auth_client.get(rule_url(rule_id))
        assert resp.status_code == 404

    def test_delete_other_user_rule_returns_404(self, api_client, admin_user, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.delete(rule_url(rule_id))
        assert resp.status_code == 404

    def test_unauthenticated_delete_returns_401(self, api_client, auth_client, uploaded):
        create = auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        rule_id = create.json()["id"]
        resp = api_client.delete(rule_url(rule_id))
        assert resp.status_code == 401
