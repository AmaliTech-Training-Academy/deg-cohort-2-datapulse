"""
tests/rules/test_rule_batch_create.py
Tests for POST /api/v1/datasets/<id>/rules/batch/

Covers:
  - 201 when all rules created successfully
  - Response shape: created, skipped, errors, summary
  - All 4 rule types in a single batch
  - Duplicate rules go to 'skipped', rest still created
  - Validation errors go to 'errors', rest still created
  - 422 when nothing was created (all duplicates / all errors)
  - 400 for non-list body
  - 400 for empty list
  - Auth enforcement (401)
  - Ownership (404 for other user's dataset)
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"
VALID_CSV = (
    b"id,age,name,email,salary\n"
    b"1,25,Alice,alice@test.com,50000.0\n"
    b"2,30,Bob,bob@test.com,60000.0\n"
)


def csv_file(name="data.csv"):
    f = io.BytesIO(VALID_CSV)
    f.name = name
    return f


def batch_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/batch/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(UPLOAD_URL, {"file": csv_file()}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


ALL_FOUR_RULES = [
    {"column_name": "name", "rule_type": "null_check", "rule_config": {}},
    {
        "column_name": "age",
        "rule_type": "range_check",
        "rule_config": {"min": 18, "max": 65},
    },
    {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
    {
        "column_name": "salary",
        "rule_type": "type_check",
        "rule_config": {"expected_type": "float"},
    },
]


# ── Response shape ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateShape:
    def test_returns_201(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        assert resp.status_code == 201

    def test_response_has_all_top_level_keys(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        data = resp.json()
        for key in ("created", "skipped", "errors", "summary"):
            assert key in data

    def test_summary_has_all_count_keys(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        summary = resp.json()["summary"]
        for key in ("total", "created", "skipped", "errors"):
            assert key in summary

    def test_created_items_have_rule_fields(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        rule = resp.json()["created"][0]
        for field in ("id", "dataset", "column_name", "rule_type", "rule_config"):
            assert field in rule


# ── Success cases ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateSuccess:
    def test_all_four_rules_created(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        assert resp.json()["summary"]["created"] == 4
        assert resp.json()["summary"]["total"] == 4
        assert resp.json()["summary"]["skipped"] == 0
        assert resp.json()["summary"]["errors"] == 0

    def test_created_list_length_matches(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        assert len(resp.json()["created"]) == 4

    def test_rule_types_in_created(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json"
        )
        types = {r["rule_type"] for r in resp.json()["created"]}
        assert types == {"null_check", "range_check", "uniqueness_check", "type_check"}

    def test_rules_are_persisted_in_db(self, auth_client, uploaded):
        auth_client.post(batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json")
        rules_resp = auth_client.get(f"/api/v1/datasets/{uploaded['id']}/rules/")
        assert rules_resp.json()["count"] == 4


# ── Duplicate handling ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateDuplicates:
    def test_duplicate_goes_to_skipped(self, auth_client, uploaded):
        # Create one rule first
        auth_client.post(
            f"/api/v1/datasets/{uploaded['id']}/rules/",
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        # Batch includes the same rule
        batch = [
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
        ]
        resp = auth_client.post(batch_url(uploaded["id"]), batch, format="json")
        assert resp.status_code == 201
        assert resp.json()["summary"]["created"] == 1
        assert resp.json()["summary"]["skipped"] == 1

    def test_skipped_entry_has_reason(self, auth_client, uploaded):
        auth_client.post(
            f"/api/v1/datasets/{uploaded['id']}/rules/",
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        batch = [
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        ]
        resp = auth_client.post(batch_url(uploaded["id"]), batch, format="json")
        skipped = resp.json()["skipped"][0]
        assert "reason" in skipped
        assert skipped["column_name"] == "email"

    def test_all_duplicates_returns_422(self, auth_client, uploaded):
        # Create both rules first
        for rule in [
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
        ]:
            auth_client.post(
                f"/api/v1/datasets/{uploaded['id']}/rules/", rule, format="json"
            )
        # Batch repeats the same rules
        resp = auth_client.post(
            batch_url(uploaded["id"]),
            [
                {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
                {
                    "column_name": "id",
                    "rule_type": "uniqueness_check",
                    "rule_config": {},
                },
            ],
            format="json",
        )
        assert resp.status_code == 422


# ── Validation error handling ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateValidationErrors:
    def test_invalid_column_goes_to_errors(self, auth_client, uploaded):
        batch = [
            {
                "column_name": "nonexistent",
                "rule_type": "null_check",
                "rule_config": {},
            },
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        ]
        resp = auth_client.post(batch_url(uploaded["id"]), batch, format="json")
        assert resp.status_code == 201
        assert resp.json()["summary"]["errors"] == 1
        assert resp.json()["summary"]["created"] == 1

    def test_error_entry_has_detail_and_index(self, auth_client, uploaded):
        batch = [
            {
                "column_name": "nonexistent",
                "rule_type": "null_check",
                "rule_config": {},
            },
        ]
        resp = auth_client.post(batch_url(uploaded["id"]), batch, format="json")
        assert resp.status_code == 422
        error = resp.json()["errors"][0]
        assert "index" in error
        assert "detail" in error

    def test_all_errors_returns_422(self, auth_client, uploaded):
        batch = [
            {"column_name": "bad_col", "rule_type": "null_check", "rule_config": {}},
            {
                "column_name": "another_bad",
                "rule_type": "null_check",
                "rule_config": {},
            },
        ]
        resp = auth_client.post(batch_url(uploaded["id"]), batch, format="json")
        assert resp.status_code == 422


# ── Bad request handling ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateBadRequest:
    def test_non_list_body_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(
            batch_url(uploaded["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        assert resp.status_code == 400

    def test_empty_list_returns_400(self, auth_client, uploaded):
        resp = auth_client.post(batch_url(uploaded["id"]), [], format="json")
        assert resp.status_code == 400


# ── Auth and ownership ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBatchCreateAuth:
    def test_unauthenticated_returns_401(self, api_client, uploaded):
        resp = api_client.post(batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json")
        assert resp.status_code == 401

    def test_other_user_dataset_returns_404(self, api_client, admin_user, uploaded):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(admin_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = api_client.post(batch_url(uploaded["id"]), ALL_FOUR_RULES, format="json")
        assert resp.status_code == 404
