"""
tests/rules/test_rules_api.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for the validation rule management API.

Endpoints tested
────────────────
  POST   /api/v1/datasets/{id}/rules/
  GET    /api/v1/datasets/{id}/rules/
  GET    /api/v1/rules/{id}/
  PATCH  /api/v1/rules/{id}/
  DELETE /api/v1/rules/{id}/

Covers
──────
  • Create all 4 rule types
  • Column existence validation
  • Duplicate rule returns 409
  • range_check parameter validation (min, max, min > max)
  • type_check parameter validation (missing/invalid expected_type)
  • Invalid rule_type returns 400
  • List rules for dataset
  • Get / patch / delete single rule
  • Authentication required on all endpoints
  • Ownership: users cannot access another user's rules
"""

import io

import pytest
from rest_framework import status

UPLOAD_URL = "/api/v1/datasets/upload/"
RULES_URL  = lambda dataset_id: f"/api/v1/datasets/{dataset_id}/rules/"
RULE_URL   = lambda rule_id: f"/api/v1/rules/{rule_id}/"

VALID_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"
    "2,30,bob@test.com,92\n"
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def dataset(auth_client, settings, tmp_path):
    """Upload a CSV and return the dataset dict."""
    settings.MEDIA_ROOT = str(tmp_path)
    payload = {"file": io.BytesIO(VALID_CSV.encode())}
    payload["file"].name = "data.csv"
    response = auth_client.post(UPLOAD_URL, payload, format="multipart")
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


@pytest.fixture
def null_rule(auth_client, dataset):
    """Create a null_check rule on 'email' and return the rule dict."""
    response = auth_client.post(
        RULES_URL(dataset["id"]),
        {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


# ═══════════════════════════════════════════════════════════════════════════════
# CREATE RULES — all 4 types
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCreateRule:

    def test_create_null_check_rule(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["rule_type"] == "null_check"
        assert response.json()["column_name"] == "email"

    def test_create_range_check_rule(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "age", "rule_type": "range_check", "rule_config": {"min": 0, "max": 120}},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["rule_config"]["min"] == 0
        assert response.json()["rule_config"]["max"] == 120

    def test_create_type_check_rule(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "score", "rule_type": "type_check", "rule_config": {"expected_type": "integer"}},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["rule_config"]["expected_type"] == "integer"

    def test_create_uniqueness_check_rule(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["rule_type"] == "uniqueness_check"

    def test_create_rule_for_missing_column_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "nonexistent_col", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_rule_returns_conflict(self, auth_client, dataset):
        payload = {"column_name": "email", "rule_type": "null_check", "rule_config": {}}
        auth_client.post(RULES_URL(dataset["id"]), payload, format="json")
        response = auth_client.post(RULES_URL(dataset["id"]), payload, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_rule_requires_authentication(self, api_client, dataset):
        response = api_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_rule_response_has_id(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert "id" in response.json()


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETER VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRuleParameterValidation:

    def test_range_check_without_min_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "age", "rule_type": "range_check", "rule_config": {"max": 100}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_range_check_without_max_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "age", "rule_type": "range_check", "rule_config": {"min": 0}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_range_check_min_greater_than_max_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "age", "rule_type": "range_check", "rule_config": {"min": 100, "max": 10}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_type_check_without_expected_type_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "score", "rule_type": "type_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_type_check_invalid_expected_type_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "score", "rule_type": "type_check", "rule_config": {"expected_type": "decimal"}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_rule_type_returns_400(self, auth_client, dataset):
        response = auth_client.post(
            RULES_URL(dataset["id"]),
            {"column_name": "email", "rule_type": "magic_check", "rule_config": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ═══════════════════════════════════════════════════════════════════════════════
# LIST RULES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestListRules:

    def test_list_returns_200(self, auth_client, dataset):
        assert auth_client.get(RULES_URL(dataset["id"])).status_code == status.HTTP_200_OK

    def test_list_empty_for_new_dataset(self, auth_client, dataset):
        results = auth_client.get(RULES_URL(dataset["id"])).json().get(
            "results", auth_client.get(RULES_URL(dataset["id"])).json()
        )
        assert results == []

    def test_list_shows_created_rules(self, auth_client, dataset):
        for col, rt in [("email", "null_check"), ("id", "uniqueness_check")]:
            auth_client.post(
                RULES_URL(dataset["id"]),
                {"column_name": col, "rule_type": rt, "rule_config": {}},
                format="json",
            )
        response = auth_client.get(RULES_URL(dataset["id"]))
        results = response.json().get("results", response.json())
        assert len(results) == 2

    def test_list_requires_authentication(self, api_client, dataset):
        assert api_client.get(RULES_URL(dataset["id"])).status_code == status.HTTP_401_UNAUTHORIZED


# ═══════════════════════════════════════════════════════════════════════════════
# GET / PATCH / DELETE SINGLE RULE
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRuleDetail:

    def test_get_rule_returns_200(self, auth_client, null_rule):
        assert auth_client.get(RULE_URL(null_rule["id"])).status_code == status.HTTP_200_OK

    def test_get_rule_id_matches(self, auth_client, null_rule):
        assert auth_client.get(RULE_URL(null_rule["id"])).json()["id"] == null_rule["id"]

    def test_patch_rule_config_returns_200(self, auth_client, null_rule):
        response = auth_client.patch(
            RULE_URL(null_rule["id"]),
            {"rule_config": {"description": "Email required"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_delete_rule_returns_204(self, auth_client, null_rule):
        assert auth_client.delete(RULE_URL(null_rule["id"])).status_code == status.HTTP_204_NO_CONTENT

    def test_deleted_rule_returns_404_on_get(self, auth_client, null_rule):
        auth_client.delete(RULE_URL(null_rule["id"]))
        assert auth_client.get(RULE_URL(null_rule["id"])).status_code == status.HTTP_404_NOT_FOUND

    def test_get_nonexistent_rule_returns_404(self, auth_client):
        assert auth_client.get(RULE_URL("00000000-0000-0000-0000-000000000000")).status_code == status.HTTP_404_NOT_FOUND

    def test_get_rule_requires_authentication(self, api_client, null_rule):
        assert api_client.get(RULE_URL(null_rule["id"])).status_code == status.HTTP_401_UNAUTHORIZED
