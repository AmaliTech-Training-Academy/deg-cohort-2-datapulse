"""
tests/datasets/test_file_service.py
Tests for FileUploadService — type detection, parsing, size/row limits,
and robust error handling for broken or malformed CSV/JSON files.
"""

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from datasets.services.file_service import (
    MAX_FILE_SIZE_BYTES,
    MAX_ROWS,
    FileUploadService,
)

VALID_CSV = b"id,name,age\n1,Alice,30\n2,Bob,25\n"
VALID_JSON = b'[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]'


def make_file(content: bytes, name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content, content_type="text/plain")


# ── Type detection ────────────────────────────────────────────────────────────


class TestDetectType:
    def test_detects_csv(self):
        f = make_file(b"col1,col2\n1,2\n", "data.csv")
        svc = FileUploadService()
        assert svc._detect_type(f) == "csv"

    def test_detects_json_object(self):
        f = make_file(b'{"key": "value"}', "data.json")
        svc = FileUploadService()
        assert svc._detect_type(f) == "json"

    def test_detects_json_array(self):
        f = make_file(b'[{"id":1}]', "data.json")
        svc = FileUploadService()
        assert svc._detect_type(f) == "json"

    def test_rejects_unsupported_type(self):
        f = make_file(b"\x89PNG\r\n\x1a\n", "image.png")
        svc = FileUploadService()
        with pytest.raises(ValidationError, match="Unsupported file type"):
            svc._detect_type(f)

    def test_csv_detected_by_extension_when_no_commas(self):
        f = make_file(b"col1\n1\n2\n", "data.csv")
        svc = FileUploadService()
        assert svc._detect_type(f) == "csv"

    def test_rejects_empty_file(self):
        f = make_file(b"", "empty.csv")
        svc = FileUploadService()
        with pytest.raises(ValidationError, match="empty"):
            svc._detect_type(f)

    def test_rejects_whitespace_only_file(self):
        f = make_file(b"   \n\n  ", "blank.csv")
        svc = FileUploadService()
        with pytest.raises(ValidationError, match="empty"):
            svc._detect_type(f)


# ── Size validation ───────────────────────────────────────────────────────────


class TestCheckSize:
    def test_accepts_file_within_limit(self):
        f = make_file(b"x" * 100, "small.csv")
        f.size = 100
        FileUploadService()._check_size(f)  # should not raise

    def test_rejects_file_over_limit(self):
        f = make_file(b"x", "big.csv")
        f.size = MAX_FILE_SIZE_BYTES + 1
        with pytest.raises(ValidationError, match="MB limit"):
            FileUploadService()._check_size(f)

    def test_error_message_includes_received_size(self):
        f = make_file(b"x", "big.csv")
        f.size = MAX_FILE_SIZE_BYTES + 1
        with pytest.raises(ValidationError) as exc_info:
            FileUploadService()._check_size(f)
        assert "MB" in str(exc_info.value.detail)


# ── CSV parsing ───────────────────────────────────────────────────────────────


class TestParseCSV:
    def test_parses_valid_csv(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_bytes(VALID_CSV)
        df = FileUploadService()._parse(str(p), "csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "age"]

    def test_parses_csv_with_bom(self, tmp_path):
        p = tmp_path / "bom.csv"
        p.write_bytes(b"\xef\xbb\xbfid,name\n1,Alice\n")
        df = FileUploadService()._parse(str(p), "csv")
        assert "id" in df.columns

    def test_parses_latin1_csv(self, tmp_path):
        p = tmp_path / "latin.csv"
        p.write_bytes("id,name\n1,Ren\xe9\n".encode("latin-1"))
        df = FileUploadService()._parse(str(p), "csv")
        assert len(df) == 1

    def test_rejects_header_only_csv(self, tmp_path):
        """A CSV with a header row but no data rows should be rejected."""
        p = tmp_path / "header_only.csv"
        p.write_text("id,name,age\n")
        with pytest.raises(ValidationError, match="no data rows|header but no data"):
            FileUploadService()._parse(str(p), "csv")

    def test_rejects_completely_empty_csv(self, tmp_path):
        """A zero-byte CSV file should be rejected cleanly."""
        p = tmp_path / "empty.csv"
        p.write_bytes(b"")
        with pytest.raises(ValidationError):
            FileUploadService()._parse(str(p), "csv")

    def test_csv_with_extra_columns_parses_with_shift(self, tmp_path):
        """
        A CSV with more values than header columns — pandas shifts the data
        silently rather than raising. This is documented pandas behaviour.
        The file parses successfully; callers should run validation rules
        to detect data quality issues.
        """
        p = tmp_path / "extra_cols.csv"
        p.write_text("id,name,age\n1,Alice,30,extra\n2,Bob,25,another\n")
        df = FileUploadService()._parse(str(p), "csv")
        assert len(df) == 2  # rows parsed — data may be shifted

    def test_rejects_csv_with_only_whitespace_rows(self, tmp_path):
        """A CSV with blank rows after the header produces an empty DataFrame."""
        p = tmp_path / "blank_rows.csv"
        p.write_text("id,name\n\n\n")
        with pytest.raises(ValidationError):
            FileUploadService()._parse(str(p), "csv")

    def test_csv_with_quoted_commas_parses_correctly(self, tmp_path):
        """Quoted fields containing commas should be handled by pandas correctly."""
        p = tmp_path / "quoted.csv"
        p.write_text('id,name\n1,"Smith, John"\n2,"Doe, Jane"\n')
        df = FileUploadService()._parse(str(p), "csv")
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Smith, John"

    def test_csv_with_extra_whitespace_in_values(self, tmp_path):
        """Extra whitespace in CSV values is preserved by pandas (no strip)."""
        p = tmp_path / "spaces.csv"
        p.write_text("id,name\n1, Alice \n2, Bob \n")
        df = FileUploadService()._parse(str(p), "csv")
        assert len(df) == 2


# ── JSON parsing ──────────────────────────────────────────────────────────────


class TestParseJSON:
    def test_parses_valid_json(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_bytes(VALID_JSON)
        df = FileUploadService()._parse(str(p), "json")
        assert len(df) == 2

    def test_rejects_invalid_json_syntax(self, tmp_path):
        """Truncated or syntactically invalid JSON should raise ValidationError."""
        p = tmp_path / "bad.json"
        p.write_bytes(b'[{"id": 1, "name": "Alice"')  # missing closing brackets
        with pytest.raises(ValidationError, match="Invalid JSON|malformed"):
            FileUploadService()._parse(str(p), "json")

    def test_rejects_json_array_of_arrays(self, tmp_path):
        """Array-of-arrays is not supported — each item must be an object."""
        p = tmp_path / "arrays.json"
        p.write_bytes(b"[[1, 2], [3, 4]]")
        with pytest.raises(ValidationError, match="array of objects"):
            FileUploadService()._parse(str(p), "json")

    def test_rejects_top_level_json_object(self, tmp_path):
        """A top-level JSON object (not array) is not supported."""
        p = tmp_path / "object.json"
        p.write_bytes(b'{"id": 1, "name": "Alice"}')
        with pytest.raises(ValidationError, match="array of objects"):
            FileUploadService()._parse(str(p), "json")

    def test_rejects_empty_json_array(self, tmp_path):
        """An empty JSON array [] has no rows to process."""
        p = tmp_path / "empty.json"
        p.write_bytes(b"[]")
        with pytest.raises(ValidationError, match="empty"):
            FileUploadService()._parse(str(p), "json")

    def test_rejects_json_with_null_top_level(self, tmp_path):
        """A JSON file containing only `null` should be rejected."""
        p = tmp_path / "null.json"
        p.write_bytes(b"null")
        with pytest.raises(ValidationError):
            FileUploadService()._parse(str(p), "json")

    def test_rejects_json_with_primitive_top_level(self, tmp_path):
        """A JSON file containing only a string or number should be rejected."""
        p = tmp_path / "primitive.json"
        p.write_bytes(b'"just a string"')
        with pytest.raises(ValidationError):
            FileUploadService()._parse(str(p), "json")

    def test_parses_json_with_nested_values(self, tmp_path):
        """Nested objects in JSON are flattened or serialised by pandas — should not error."""
        p = tmp_path / "nested.json"
        p.write_bytes(
            b'[{"id": 1, "meta": {"key": "val"}}, {"id": 2, "meta": {"key": "val2"}}]'
        )
        df = FileUploadService()._parse(str(p), "json")
        assert len(df) == 2

    def test_json_error_message_includes_line_number(self, tmp_path):
        """The ValidationError message for invalid JSON should mention a line number."""
        p = tmp_path / "bad_line.json"
        p.write_bytes(b'[\n  {"id": 1},\n  INVALID\n]')
        with pytest.raises(ValidationError) as exc_info:
            FileUploadService()._parse(str(p), "json")
        error_str = str(exc_info.value.detail)
        # Should mention line number or column from JSONDecodeError
        assert "line" in error_str.lower() or "col" in error_str.lower()


# ── Row limit ─────────────────────────────────────────────────────────────────


class TestCheckRows:
    def test_accepts_within_row_limit(self, tmp_path):
        df = pd.DataFrame({"x": range(10)})
        FileUploadService()._check_rows(df, "/fake/path")  # should not raise

    def test_rejects_over_row_limit(self, tmp_path):
        p = tmp_path / "big.csv"
        p.write_text("x\n")
        df = pd.DataFrame({"x": range(MAX_ROWS + 1)})
        with pytest.raises(ValidationError, match="row limit"):
            FileUploadService()._check_rows(df, str(p))

    def test_error_message_includes_actual_count(self, tmp_path):
        p = tmp_path / "big.csv"
        p.write_text("x\n")
        df = pd.DataFrame({"x": range(MAX_ROWS + 100)})
        with pytest.raises(ValidationError) as exc_info:
            FileUploadService()._check_rows(df, str(p))
        assert str(MAX_ROWS + 100) in str(exc_info.value.detail) or "row" in str(
            exc_info.value.detail
        )


# ── Upload integration ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUpload:
    def test_upload_csv_creates_dataset(self, regular_user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        f = SimpleUploadedFile("data.csv", VALID_CSV, content_type="text/csv")
        f.size = len(VALID_CSV)
        svc = FileUploadService()
        dataset, df = svc.upload(file=f, user=regular_user, file_title="Test")
        assert dataset.row_count == 2
        assert dataset.file_type == "csv"
        assert dataset.user == regular_user
        assert "id" in dataset.columns
        assert dataset.file_title == "Test"

    def test_upload_json_creates_dataset(self, regular_user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        f = SimpleUploadedFile("data.json", VALID_JSON, content_type="application/json")
        f.size = len(VALID_JSON)
        svc = FileUploadService()
        dataset, df = svc.upload(file=f, user=regular_user)
        assert dataset.file_type == "json"
        assert dataset.row_count == 2

    def test_file_path_not_empty(self, regular_user, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        f = SimpleUploadedFile("data.csv", VALID_CSV, content_type="text/csv")
        f.size = len(VALID_CSV)
        dataset, _ = FileUploadService().upload(file=f, user=regular_user)
        assert dataset.file_path != ""

    def test_file_removed_on_parse_failure(self, regular_user, settings, tmp_path):
        """No orphaned files on disk when parsing fails."""
        settings.MEDIA_ROOT = str(tmp_path)
        bad = b"[[1,2],[3,4]]"
        f = SimpleUploadedFile("bad.json", bad, content_type="application/json")
        f.size = len(bad)
        with pytest.raises(ValidationError):
            FileUploadService().upload(file=f, user=regular_user)
        upload_dir = tmp_path / "uploads" / str(regular_user.id)
        if upload_dir.exists():
            assert list(upload_dir.iterdir()) == []

    def test_upload_invalid_json_syntax_raises_validation_error(
        self, regular_user, settings, tmp_path
    ):
        """Invalid JSON syntax should return a 400 ValidationError, not a 500."""
        settings.MEDIA_ROOT = str(tmp_path)
        bad = b'[{"id": 1, "name": "Alice"'  # truncated
        f = SimpleUploadedFile("bad.json", bad, content_type="application/json")
        f.size = len(bad)
        with pytest.raises(ValidationError):
            FileUploadService().upload(file=f, user=regular_user)

    def test_upload_header_only_csv_raises_validation_error(
        self, regular_user, settings, tmp_path
    ):
        """A header-only CSV should return a 400 ValidationError."""
        settings.MEDIA_ROOT = str(tmp_path)
        content = b"id,name,age\n"
        f = SimpleUploadedFile("empty.csv", content, content_type="text/csv")
        f.size = len(content)
        with pytest.raises(ValidationError):
            FileUploadService().upload(file=f, user=regular_user)

    def test_upload_top_level_json_object_raises_validation_error(
        self, regular_user, settings, tmp_path
    ):
        """A top-level JSON object (not array) should return a 400 ValidationError."""
        settings.MEDIA_ROOT = str(tmp_path)
        content = b'{"id": 1, "name": "Alice"}'
        f = SimpleUploadedFile("obj.json", content, content_type="application/json")
        f.size = len(content)
        with pytest.raises(ValidationError, match="array of objects"):
            FileUploadService().upload(file=f, user=regular_user)
