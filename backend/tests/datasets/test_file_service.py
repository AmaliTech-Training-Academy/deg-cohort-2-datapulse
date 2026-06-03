"""
tests/datasets/test_file_service.py
Tests for FileUploadService — type detection, parsing, size/row limits.
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


class TestParse:
    def test_parses_valid_csv(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_bytes(VALID_CSV)
        df = FileUploadService()._parse(str(p), "csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "age"]

    def test_parses_valid_json(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_bytes(VALID_JSON)
        df = FileUploadService()._parse(str(p), "json")
        assert len(df) == 2

    def test_rejects_empty_csv(self, tmp_path):
        p = tmp_path / "empty.csv"
        p.write_text("id,name\n")
        with pytest.raises(ValueError, match="no data rows"):
            FileUploadService()._parse(str(p), "csv")

    def test_rejects_json_array_of_arrays(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_bytes(b"[[1,2],[3,4]]")
        with pytest.raises(ValueError, match="array of objects"):
            FileUploadService()._parse(str(p), "json")

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
        settings.MEDIA_ROOT = str(tmp_path)
        bad = b"[[1,2],[3,4]]"
        f = SimpleUploadedFile("bad.json", bad, content_type="application/json")
        f.size = len(bad)
        with pytest.raises(ValidationError):
            FileUploadService().upload(file=f, user=regular_user)
        # No leftover files in upload dir
        upload_dir = tmp_path / "uploads" / str(regular_user.id)
        if upload_dir.exists():
            assert list(upload_dir.iterdir()) == []
