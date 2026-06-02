"""
tests/checks/test_run_check_api.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for the quality check run API.

Endpoints tested
────────────────
  POST /api/v1/datasets/{id}/run-check/
  GET  /api/v1/checks/{id}/
  GET  /api/v1/datasets/{id}/checks/

Tests the FULL pipeline: upload → create rules → run check → verify score.
Uses the same CSV as the live PowerShell test to assert exact values.

Known CSV test data
────────────────────
  Row 1: all valid                → PASSES all rules
  Row 2: null age                 → FAILS range_check
  Row 3: null email               → FAILS null_check
  Row 4: age = -5                 → FAILS range_check
  Row 5: id = 5 (duplicate)       → FAILS uniqueness_check
  Row 6: id = 5 (duplicate copy)  → FAILS uniqueness_check

  Union of failed rows: {1, 2, 3, 4, 5} = 5 unique failures
  Quality score: (6-5) / 6 * 100 = 16.67 → round → 17
"""

import io

import pytest
from rest_framework import status

UPLOAD_URL    = "/api/v1/datasets/upload/"
RULES_URL     = lambda did: f"/api/v1/datasets/{did}/rules/"
RUN_CHECK_URL = lambda did: f"/api/v1/datasets/{did}/run-check/"
CHECK_URL     = lambda cid: f"/api/v1/checks/{cid}/"
CHECK_LIST    = lambda did: f"/api/v1/datasets/{did}/checks/"

# Intentional quality issues — matches the live PowerShell test exactly
KNOWN_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"   # all valid
    "2,,bob@test.com,92\n"       # null age → range_check fails
    "3,31,,75\n"                 # null email → null_check fails
    "4,-5,dave@test.com,101\n"   # age=-5 → range_check fails
    "5,40,eve@test.com,60\n"     # id=5 duplicate → uniqueness fails
    "5,45,frank@test.com,55\n"   # id=5 duplicate → uniqueness fails
)

CLEAN_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"
    "2,30,bob@test.com,92\n"
    "3,35,carol@test.com,75\n"
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def dataset(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    payload = {"file": io.BytesIO(KNOWN_CSV.encode())}
    payload["file"].name = "known.csv"
    r = auth_client.post(UPLOAD_URL, payload, format="multipart")
    assert r.status_code == status.HTTP_201_CREATED
    return r.json()


@pytest.fixture
def dataset_with_4_rules(auth_client, dataset):
    """Dataset with all 4 rule types configured — ready to run."""
    rules = [
        {"column_name": "email",  "rule_type": "null_check",       "rule_config": {}},
        {"column_name": "age",    "rule_type": "range_check",      "rule_config": {"min": 0, "max": 120}},
        {"column_name": "score",  "rule_type": "type_check",       "rule_config": {"expected_type": "integer"}},
        {"column_name": "id",     "rule_type": "uniqueness_check", "rule_config": {}},
    ]
    for rule in rules:
        r = auth_client.post(RULES_URL(dataset["id"]), rule, format="json")
        assert r.status_code == status.HTTP_201_CREATED
    return dataset


@pytest.fixture
def clean_dataset(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    payload = {"file": io.BytesIO(CLEAN_CSV.encode())}
    payload["file"].name = "clean.csv"
    return auth_client.post(UPLOAD_URL, payload, format="multipart").json()


# ═══════════════════════════════════════════════════════════════════════════════
# RUN CHECK — response structure
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRunCheck:

    def test_run_check_returns_201(self, auth_client, dataset_with_4_rules):
        assert auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).status_code == status.HTTP_201_CREATED

    def test_run_check_response_has_required_fields(self, auth_client, dataset_with_4_rules):
        data = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        for field in ["id", "dataset", "status", "overall_score", "total_rows_passed", "total_rows_failed"]:
            assert field in data, f"Missing field in response: {field}"

    def test_run_check_status_is_completed(self, auth_client, dataset_with_4_rules):
        data = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert data["status"] == "completed"

    def test_run_check_requires_authentication(self, api_client, dataset):
        assert api_client.post(RUN_CHECK_URL(dataset["id"])).status_code == status.HTTP_401_UNAUTHORIZED

    def test_run_check_on_nonexistent_dataset_returns_404(self, auth_client):
        assert auth_client.post(RUN_CHECK_URL("00000000-0000-0000-0000-000000000000")).status_code == status.HTTP_404_NOT_FOUND


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY SCORE — exact value verification
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestQualityScore:

    def test_known_csv_score_is_exactly_17(self, auth_client, dataset_with_4_rules):
        """
        THE integration test for the score formula.
        Replicates the live PowerShell session result.

        6 rows, 5 unique failed rows → score = round((1/6)*100) = 17
        """
        data = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert data["overall_score"] == 17
        assert data["total_rows_passed"] == 1
        assert data["total_rows_failed"] == 5

    def test_clean_data_scores_100(self, auth_client, clean_dataset, settings, tmp_path):
        """Clean dataset with a null_check on a fully-populated column → score = 100."""
        settings.MEDIA_ROOT = str(tmp_path)
        auth_client.post(
            RULES_URL(clean_dataset["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        data = auth_client.post(RUN_CHECK_URL(clean_dataset["id"])).json()
        assert data["overall_score"] == 100
        assert data["total_rows_failed"] == 0

    def test_no_rules_scores_100(self, auth_client, dataset):
        """No rules defined → nothing fails → score = 100."""
        data = auth_client.post(RUN_CHECK_URL(dataset["id"])).json()
        assert data["overall_score"] == 100

    def test_score_is_integer(self, auth_client, dataset_with_4_rules):
        score = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["overall_score"]
        assert isinstance(score, int)

    def test_score_within_0_to_100(self, auth_client, dataset_with_4_rules):
        score = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["overall_score"]
        assert 0 <= score <= 100


# ═══════════════════════════════════════════════════════════════════════════════
# FINDINGS — per-rule results
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRuleFindings:

    def test_findings_count_equals_number_of_rules(self, auth_client, dataset_with_4_rules):
        data = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert len(data["findings"]) == 4

    def test_null_check_finding_fails_one_row(self, auth_client, dataset_with_4_rules):
        """Row 3 has null email → null_check must fail exactly 1 row."""
        findings = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["findings"]
        null_finding = next(f for f in findings if f["rule_type"] == "null_check")
        assert null_finding["rows_failed"] == 1
        assert null_finding["column_name"] == "email"

    def test_range_check_finding_fails_two_rows(self, auth_client, dataset_with_4_rules):
        """Row 2 (null age) and Row 4 (age=-5) → range_check fails 2 rows."""
        findings = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["findings"]
        range_finding = next(f for f in findings if f["rule_type"] == "range_check")
        assert range_finding["rows_failed"] == 2

    def test_uniqueness_finding_flags_both_duplicates(self, auth_client, dataset_with_4_rules):
        """Both copies of id=5 (rows 5 and 6) must be flagged."""
        findings = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["findings"]
        uniq_finding = next(f for f in findings if f["rule_type"] == "uniqueness_check")
        assert uniq_finding["rows_failed"] == 2

    def test_type_check_passes_all_rows(self, auth_client, dataset_with_4_rules):
        """All score values in the test CSV are integers → type_check rows_failed = 0."""
        findings = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["findings"]
        type_finding = next(f for f in findings if f["rule_type"] == "type_check")
        assert type_finding["rows_failed"] == 0

    def test_failing_findings_have_error_details(self, auth_client, dataset_with_4_rules):
        findings = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()["findings"]
        for finding in findings:
            if finding["rows_failed"] > 0:
                assert "error_details" in finding
                for detail in finding["error_details"]:
                    assert "row" in detail
                    assert "reason" in detail

    def test_error_details_capped_at_five(self, auth_client, settings, tmp_path):
        """Even if 20 rows fail, only up to 5 error details are returned per rule."""
        settings.MEDIA_ROOT = str(tmp_path)
        rows = ["id,email"] + [f"{i}," for i in range(20)]
        payload = {"file": io.BytesIO("\n".join(rows).encode())}
        payload["file"].name = "nulls.csv"
        ds = auth_client.post(UPLOAD_URL, payload, format="multipart").json()
        auth_client.post(
            RULES_URL(ds["id"]),
            {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
            format="json",
        )
        findings = auth_client.post(RUN_CHECK_URL(ds["id"])).json()["findings"]
        assert findings[0]["rows_failed"] == 20
        assert len(findings[0]["error_details"]) <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK DETAIL AND HISTORY
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCheckDetail:

    def test_get_check_by_id_returns_200(self, auth_client, dataset_with_4_rules):
        check = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert auth_client.get(CHECK_URL(check["id"])).status_code == status.HTTP_200_OK

    def test_get_check_id_matches(self, auth_client, dataset_with_4_rules):
        check = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert auth_client.get(CHECK_URL(check["id"])).json()["id"] == check["id"]

    def test_check_history_contains_all_runs(self, auth_client, dataset_with_4_rules):
        auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"]))
        auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"]))
        response = auth_client.get(CHECK_LIST(dataset_with_4_rules["id"]))
        assert response.status_code == status.HTTP_200_OK
        results = response.json().get("results", response.json())
        assert len(results) >= 2

    def test_get_nonexistent_check_returns_404(self, auth_client):
        assert auth_client.get(CHECK_URL("00000000-0000-0000-0000-000000000000")).status_code == status.HTTP_404_NOT_FOUND

    def test_check_requires_authentication(self, api_client, auth_client, dataset_with_4_rules):
        check = auth_client.post(RUN_CHECK_URL(dataset_with_4_rules["id"])).json()
        assert api_client.get(CHECK_URL(check["id"])).status_code == status.HTTP_401_UNAUTHORIZED
