"""
tests/rules/test_rule_list_stats.py
Tests for the enriched GET /api/v1/datasets/<id>/rules/ response.

Covers:
  - Response envelope: total_failing_rows, total_passing_rows, rule_type_scores
  - Per-rule fields: last_failing_rows, last_passing_rows, average_score
  - rule_type_scores always has all 4 keys; null for unchecked types
  - Summary stats unaffected by rule_type / column_name filters
  - Zero state (no checks run yet)
"""

import io

import pytest

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    b"id,age,email\n"
    b"1,25,alice@test.com\n"
    b"2,30,bob@test.com\n"
    b"3,35,carol@test.com\n"
)


def csv_file(name="data.csv"):
    f = io.BytesIO(VALID_CSV)
    f.name = name
    return f


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


def run_check_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/run-check/"


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(UPLOAD_URL, {"file": csv_file()}, format="multipart")
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def with_rules(auth_client, uploaded):
    """Create one null_check and one uniqueness_check rule."""
    for col, rt, rc in [
        ("email", "null_check", {}),
        ("id", "uniqueness_check", {}),
    ]:
        auth_client.post(
            rules_url(uploaded["id"]),
            {"column_name": col, "rule_type": rt, "rule_config": rc},
            format="json",
        )
    return uploaded


@pytest.fixture
def with_run(auth_client, with_rules):
    """Create rules and run one quality check (clean data → score 100)."""
    resp = auth_client.post(run_check_url(with_rules["id"]))
    assert resp.status_code == 201
    return with_rules


# ── Response envelope shape ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestRuleListShape:
    def test_summary_fields_present(self, auth_client, uploaded):
        resp = auth_client.get(rules_url(uploaded["id"]))
        data = resp.json()
        for field in (
            "total_failing_rows",
            "total_passing_rows",
            "rule_type_scores",
            "count",
            "next",
            "previous",
            "results",
        ):
            assert field in data, f"Missing field: {field}"

    def test_rule_type_scores_has_all_four_keys(self, auth_client, uploaded):
        resp = auth_client.get(rules_url(uploaded["id"]))
        scores = resp.json()["rule_type_scores"]
        for rt in ("null_check", "type_check", "range_check", "uniqueness_check"):
            assert rt in scores, f"Missing rule_type_scores key: {rt}"

    def test_per_rule_stats_fields_present(self, auth_client, with_rules):
        resp = auth_client.get(rules_url(with_rules["id"]))
        rule = resp.json()["results"][0]
        for field in ("last_failing_rows", "last_passing_rows", "average_score"):
            assert field in rule, f"Missing per-rule field: {field}"


# ── Zero state (no checks run) ────────────────────────────────────────────────


@pytest.mark.django_db
class TestZeroState:
    def test_total_failing_rows_zero_before_run(self, auth_client, with_rules):
        resp = auth_client.get(rules_url(with_rules["id"]))
        assert resp.json()["total_failing_rows"] == 0

    def test_total_passing_rows_zero_before_run(self, auth_client, with_rules):
        resp = auth_client.get(rules_url(with_rules["id"]))
        assert resp.json()["total_passing_rows"] == 0

    def test_rule_type_scores_all_null_before_run(self, auth_client, with_rules):
        resp = auth_client.get(rules_url(with_rules["id"]))
        scores = resp.json()["rule_type_scores"]
        for rt in ("null_check", "type_check", "range_check", "uniqueness_check"):
            assert scores[rt] is None

    def test_per_rule_stats_null_before_run(self, auth_client, with_rules):
        resp = auth_client.get(rules_url(with_rules["id"]))
        rule = resp.json()["results"][0]
        assert rule["last_failing_rows"] is None
        assert rule["last_passing_rows"] is None
        assert rule["average_score"] is None


# ── After run check ───────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAfterRun:
    def test_total_failing_rows_after_clean_run(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        # Clean data → 0 failures across all rules
        assert resp.json()["total_failing_rows"] == 0

    def test_total_passing_rows_after_clean_run(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        # 2 rules × 3 rows each = 6 total row-checks, all passing
        assert resp.json()["total_passing_rows"] == 6

    def test_rule_type_scores_populated_for_checked_types(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        scores = resp.json()["rule_type_scores"]
        # null_check and uniqueness_check were run → must have scores
        assert scores["null_check"] is not None
        assert scores["uniqueness_check"] is not None

    def test_unchecked_rule_types_remain_null(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        scores = resp.json()["rule_type_scores"]
        # type_check and range_check have no rules → scores must be null
        assert scores["type_check"] is None
        assert scores["range_check"] is None

    def test_clean_run_scores_100_for_checked_types(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        scores = resp.json()["rule_type_scores"]
        assert scores["null_check"] == 100
        assert scores["uniqueness_check"] == 100

    def test_per_rule_last_failing_rows_zero_on_clean(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        for rule in resp.json()["results"]:
            assert rule["last_failing_rows"] == 0

    def test_per_rule_last_passing_rows_equals_row_count(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        for rule in resp.json()["results"]:
            # VALID_CSV has 3 rows; all pass on clean data
            assert rule["last_passing_rows"] == 3

    def test_per_rule_average_score_100_on_clean(self, auth_client, with_run):
        resp = auth_client.get(rules_url(with_run["id"]))
        for rule in resp.json()["results"]:
            assert rule["average_score"] == 100


# ── Summary unaffected by filters ─────────────────────────────────────────────


@pytest.mark.django_db
class TestSummaryUnaffectedByFilters:
    def test_total_passing_rows_unaffected_by_rule_type_filter(
        self, auth_client, with_run
    ):
        """Filtering to null_check only changes results[], not summary."""
        unfiltered = auth_client.get(rules_url(with_run["id"])).json()
        filtered = auth_client.get(
            f"{rules_url(with_run['id'])}?rule_type=null_check"
        ).json()

        # count is filtered (1 rule)
        assert filtered["count"] == 1
        # summary totals are the same
        assert filtered["total_passing_rows"] == unfiltered["total_passing_rows"]
        assert filtered["total_failing_rows"] == unfiltered["total_failing_rows"]

    def test_rule_type_scores_unaffected_by_column_filter(self, auth_client, with_run):
        unfiltered = auth_client.get(rules_url(with_run["id"])).json()
        filtered = auth_client.get(
            f"{rules_url(with_run['id'])}?column_name=email"
        ).json()
        assert filtered["rule_type_scores"] == unfiltered["rule_type_scores"]
