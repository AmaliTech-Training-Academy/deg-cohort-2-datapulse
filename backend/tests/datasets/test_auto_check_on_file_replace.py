"""
tests/datasets/test_auto_check_on_file_replace.py

Tests for the automatic quality check triggered when a dataset file is replaced
via PATCH /api/v1/datasets/<id>/file/.

The background thread is patched to run synchronously in tests because SQLite
does not support concurrent writes.  Production behaviour (async thread) is
covered by the _dispatch_auto_check method on the view class.

Covers:
  - auto_check block present in response when rules exist
  - auto_check is null when no rules exist
  - report_id in auto_check references a real QualityReport
  - report is scored correctly after synchronous patch
  - report stores file title and version snapshots
  - file replacement still succeeds (200) regardless of check outcome
  - second file replacement creates a second report (history preserved)
"""

import io

import pytest

from checks.services.check_service import run_quality_check_on_report
from datasets.models import Dataset
from datasets.views import DatasetFileUpdateView
from reports.models import QualityReport

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    b"id,age,email\n"
    b"1,25,alice@test.com\n"
    b"2,30,bob@test.com\n"
    b"3,35,carol@test.com\n"
)

REPLACEMENT_CSV = (
    b"id,age,email\n"
    b"10,40,dave@test.com\n"
    b"11,45,eve@test.com\n"
    b"12,50,frank@test.com\n"
    b"13,55,grace@test.com\n"
)


def csv_file(content=VALID_CSV, name="data.csv"):
    f = io.BytesIO(content)
    f.name = name
    return f


def file_update_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/file/"


def rules_url(dataset_id):
    return f"/api/v1/datasets/{dataset_id}/rules/"


@pytest.fixture
def sync_auto_check(monkeypatch):
    """
    Replace the async thread dispatch with a synchronous call.

    SQLite does not support concurrent writes; running the check in a
    background thread during tests causes 'database table is locked'.
    This fixture makes the auto-check run inline so tests can assert
    on the completed report without polling.
    """

    def _sync_dispatch(self, dataset_id, report_id):
        _dataset = Dataset.objects.get(id=dataset_id)
        _report = QualityReport.objects.get(id=report_id)
        run_quality_check_on_report(_dataset, _report)

    monkeypatch.setattr(DatasetFileUpdateView, "_dispatch_auto_check", _sync_dispatch)


@pytest.fixture
def uploaded(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    resp = auth_client.post(
        UPLOAD_URL,
        {"file": csv_file(), "file_title": "Employee Data"},
        format="multipart",
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def with_rules(auth_client, uploaded):
    auth_client.post(
        rules_url(uploaded["id"]),
        {"column_name": "email", "rule_type": "null_check", "rule_config": {}},
        format="json",
    )
    auth_client.post(
        rules_url(uploaded["id"]),
        {"column_name": "id", "rule_type": "uniqueness_check", "rule_config": {}},
        format="json",
    )
    return uploaded


# ── auto_check block in response ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAutoCheckResponse:
    def test_auto_check_null_when_no_rules(self, auth_client, uploaded):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.json()["auto_check"] is None

    def test_auto_check_present_when_rules_exist(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.json()["auto_check"] is not None

    def test_auto_check_contains_report_id(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        auto_check = resp.json()["auto_check"]
        assert "report_id" in auto_check
        assert auto_check["report_id"] is not None

    def test_auto_check_contains_status_queued(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        # "queued" is the status at response time — the thread runs it after
        assert resp.json()["auto_check"]["status"] == "queued"

    def test_auto_check_contains_poll_message(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        message = resp.json()["auto_check"]["message"]
        assert "Poll" in message or "poll" in message


# ── Report is scored correctly (sync patch) ──────────────────────────────────


@pytest.mark.django_db
class TestAutoCheckReport:
    def test_report_created_in_db(self, auth_client, with_rules, sync_auto_check):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        assert QualityReport.objects.filter(id=report_id).exists()

    def test_report_scored_after_sync_check(
        self, auth_client, with_rules, sync_auto_check
    ):
        """Clean data → score=100 → healthy."""
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        report = QualityReport.objects.get(id=report_id)
        assert report.overall_score == 100
        assert report.status == QualityReport.Status.HEALTHY

    def test_report_poll_endpoint_returns_200(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        poll = auth_client.get(f"/api/v1/reports/{report_id}/")
        assert poll.status_code == 200
        assert poll.json()["id"] == report_id

    def test_report_snapshots_file_title(
        self, auth_client, with_rules, sync_auto_check
    ):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        report = QualityReport.objects.get(id=report_id)
        assert report.dataset_file_title == "Employee Data"

    def test_report_snapshots_file_version(
        self, auth_client, with_rules, sync_auto_check
    ):
        """File replace increments version to 2; report should store v2."""
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        report = QualityReport.objects.get(id=report_id)
        assert report.dataset_file_version == 2

    def test_findings_persisted(self, auth_client, with_rules, sync_auto_check):
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        report_id = resp.json()["auto_check"]["report_id"]
        report = QualityReport.objects.get(id=report_id)
        # 2 rules → 2 findings
        assert report.findings.count() == 2


# ── File replacement still succeeds regardless of check ──────────────────────


@pytest.mark.django_db
class TestFileReplaceUnaffected:
    def test_file_version_incremented_regardless_of_rules(
        self, auth_client, uploaded
    ):
        resp = auth_client.patch(
            file_update_url(uploaded["id"]),
            {"file": csv_file(REPLACEMENT_CSV, "new.csv")},
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.json()["file_version"] == 2

    def test_second_replace_creates_second_report(
        self, auth_client, with_rules, sync_auto_check
    ):
        """Each file replacement creates a new report — history is preserved."""
        for name in ("replace1.csv", "replace2.csv"):
            auth_client.patch(
                file_update_url(with_rules["id"]),
                {"file": csv_file(REPLACEMENT_CSV, name)},
                format="multipart",
            )
        reports = auth_client.get(
            f"/api/v1/datasets/{with_rules['id']}/reports/"
        ).json()
        assert reports["count"] == 2

    def test_stale_rule_columns_still_returned(
        self, auth_client, with_rules, sync_auto_check
    ):
        """Drop the age column — stale_rule_columns should list it if a rule targets it."""
        minimal = b"id,email\n1,a@test.com\n2,b@test.com\n"
        resp = auth_client.patch(
            file_update_url(with_rules["id"]),
            {"file": csv_file(minimal, "minimal.csv")},
            format="multipart",
        )
        assert resp.status_code == 200
        # age is not in the new file but also not in the rules we set up —
        # only id and email rules exist, so stale_rule_columns is empty here
        assert isinstance(resp.json()["stale_rule_columns"], list)
