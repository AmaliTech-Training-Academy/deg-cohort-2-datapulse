"""
tests/datasets/test_file_service.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for FileUploadService.

Tests the file parsing and validation layer directly — no HTTP requests.

Covers
──────
  • CSV upload happy path — creates Dataset, returns DataFrame
  • JSON upload happy path
  • BOM-encoded CSV (Excel export) — columns must not contain BOM character
  • File size limit enforcement (10MB)
  • Row limit enforcement (50,000 rows)
  • Empty file rejection
  • PDF/binary file rejection
  • JSON array-of-arrays rejection
  • UUID filename generation (prevents collisions)
  • Two uploads of the same file get different filenames
  • file_path is never returned by the response serializer
  • file_title and description stored correctly
"""

import io
import os
import uuid

import pandas as pd
import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

VALID_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"
    "2,30,bob@test.com,92\n"
    "3,35,carol@test.com,75\n"
)

VALID_JSON = (
    '[{"id":1,"age":25,"email":"alice@test.com"},'
    '{"id":2,"age":30,"email":"bob@test.com"}]'
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_csv_file(content: str, name: str = "test.csv"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


def make_json_file(content: str, name: str = "test.json"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="application/json")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def service():
    from datasets.services.file_service import FileUploadService

    return FileUploadService()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="uploader",
        email="uploader@test.com",
        password="TestPass123!",
        role="user",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CSV UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCSVUpload:

    def test_valid_csv_creates_dataset(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, df = service.upload(file=make_csv_file(VALID_CSV), user=user)
        assert dataset.id is not None
        assert dataset.file_type == "csv"
        assert dataset.row_count == 3
        assert dataset.user == user

    def test_valid_csv_columns_extracted(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(file=make_csv_file(VALID_CSV), user=user)
        assert dataset.columns == ["id", "age", "email", "score"]

    def test_csv_file_title_stored(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(
            file=make_csv_file(VALID_CSV), user=user, file_title="My Dataset"
        )
        assert dataset.file_title == "My Dataset"

    def test_csv_description_stored(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(
            file=make_csv_file(VALID_CSV), user=user, description="For testing"
        )
        assert dataset.description == "For testing"

    def test_csv_file_saved_to_disk(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(file=make_csv_file(VALID_CSV), user=user)
        assert os.path.exists(dataset.file_path)

    def test_csv_filename_is_uuid(self, service, user, settings, tmp_path):
        """Uploaded files must use UUID names to prevent collisions."""
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(file=make_csv_file(VALID_CSV, name="my_data.csv"), user=user)
        basename = os.path.basename(dataset.file_path)
        name_part = basename.replace(".csv", "")
        uuid.UUID(name_part)  # raises ValueError if not a valid UUID

    def test_csv_two_uploads_different_filenames(self, service, user, settings, tmp_path):
        """Two uploads of the same content must not overwrite each other."""
        settings.MEDIA_ROOT = str(tmp_path)
        d1, _ = service.upload(file=make_csv_file(VALID_CSV), user=user)
        d2, _ = service.upload(file=make_csv_file(VALID_CSV), user=user)
        assert d1.file_path != d2.file_path

    def test_csv_returns_dataframe(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        _, df = service.upload(file=make_csv_file(VALID_CSV), user=user)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_bom_encoded_csv_columns_clean(self, service, user, settings, tmp_path):
        """CSV files exported from Excel include a UTF-8 BOM marker (0xEF 0xBB 0xBF).
        The first column name must NOT contain the BOM character after parsing."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        settings.MEDIA_ROOT = str(tmp_path)
        bom_content = b"\xef\xbb\xbfid,age,email\n1,25,a@b.com\n2,30,c@d.com\n"
        file = SimpleUploadedFile("bom.csv", bom_content, content_type="text/csv")
        dataset, _ = service.upload(file=file, user=user)
        assert dataset.columns[0] == "id"
        assert "\ufeff" not in dataset.columns[0]


# ═══════════════════════════════════════════════════════════════════════════════
# JSON UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestJSONUpload:

    def test_valid_json_creates_dataset(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(file=make_json_file(VALID_JSON), user=user)
        assert dataset.file_type == "json"
        assert dataset.row_count == 2
        assert "id" in dataset.columns

    def test_json_array_of_arrays_rejected(self, service, user, settings, tmp_path):
        """JSON array-of-arrays produces integer column names and must be rejected."""
        settings.MEDIA_ROOT = str(tmp_path)
        with pytest.raises(ValidationError) as exc:
            service.upload(file=make_json_file("[[1,2,3],[4,5,6]]"), user=user)
        assert "array of objects" in str(exc.value).lower()

    def test_json_returns_dataframe(self, service, user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        _, df = service.upload(file=make_json_file(VALID_JSON), user=user)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION GUARDS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestUploadValidation:

    def test_empty_csv_rejected(self, service, user, settings, tmp_path):
        """A CSV with a header row but no data rows must be rejected."""
        settings.MEDIA_ROOT = str(tmp_path)
        with pytest.raises(ValidationError) as exc:
            service.upload(file=make_csv_file("id,age,email\n"), user=user)
        assert "no data rows" in str(exc.value).lower()

    def test_file_exceeding_size_limit_rejected(self, service, user, settings, tmp_path):
        """Files larger than 10MB must be rejected before parsing."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        settings.MEDIA_ROOT = str(tmp_path)
        large_data = b"x" * (11 * 1024 * 1024)  # 11 MB
        file = SimpleUploadedFile("big.csv", large_data, content_type="text/csv")
        with pytest.raises(ValidationError) as exc:
            service.upload(file=file, user=user)
        assert "limit" in str(exc.value).lower()

    def test_unsupported_file_type_rejected(self, service, user, settings, tmp_path):
        """A PDF or binary file must be rejected with a clear error."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        settings.MEDIA_ROOT = str(tmp_path)
        file = SimpleUploadedFile(
            "report.pdf",
            b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
        )
        with pytest.raises(ValidationError) as exc:
            service.upload(file=file, user=user)
        assert "unsupported" in str(exc.value).lower()

    def test_file_path_excluded_from_serializer(self, service, user, settings, tmp_path):
        """file_path is internal — must never appear in the API response."""
        from datasets.serializers import DatasetResponseSerializer

        settings.MEDIA_ROOT = str(tmp_path)
        dataset, _ = service.upload(file=make_csv_file(VALID_CSV), user=user)
        data = DatasetResponseSerializer(dataset).data
        assert "file_path" not in data

    def test_row_limit_enforced(self, service, user, settings, tmp_path):
        """Files exceeding MAX_ROWS must be rejected after parsing."""
        from datasets.services.file_service import MAX_ROWS

        settings.MEDIA_ROOT = str(tmp_path)
        rows = ["id,value"] + [f"{i},{i * 2}" for i in range(MAX_ROWS + 1)]
        content = "\n".join(rows)
        file = make_csv_file(content, name="huge.csv")

        # Bypass size check so we can test the row limit independently
        original_check = service._check_size
        service._check_size = lambda f: None
        try:
            with pytest.raises(ValidationError) as exc:
                service.upload(file=file, user=user)
            assert "row limit" in str(exc.value).lower()
        finally:
            service._check_size = original_check
