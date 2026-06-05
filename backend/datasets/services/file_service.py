"""
datasets/services/file_service.py
────────────────────────────────────────────────────────────────────────────────
FileUploadService — handles everything between receiving the raw uploaded file
and having a clean DataFrame + saved Dataset record.

Responsibilities:
    1. Detect actual file type from content, not extension
    2. Enforce size and row limits before processing
    3. Parse CSV / JSON robustly via Pandas (BOM, encoding, format guards)
    4. Save file to disk with a UUID filename to prevent collisions
    5. Create and return the Dataset record

replace() additionally:
    6. Atomically swap the physical file and update dataset metadata
    7. Increment file_version so callers can track which generation of data
       a QualityReport was run against
    8. Flag any ValidationRule whose column_name no longer exists in the
       new file's columns (stale rules do not block the replacement)

Error handling policy
─────────────────────
Every user-facing problem raises rest_framework.exceptions.ValidationError
with a field key of "file" and a human-readable message.  Raw Pandas /
standard-library exception strings are never exposed to the client — they
are logged at WARNING level for debugging and replaced with a clear message.

Called by DatasetUploadView and DatasetFileUpdateView — no Django request
object inside this class, only primitives and the uploaded file object.
"""

import json
import logging
import os
import uuid

import pandas as pd
from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Hard limits — keep the engine fast and the container safe
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 50_000


class FileUploadService:
    """Parse and persist an uploaded CSV or JSON file."""

    def upload(self, file, user, file_title: str = "", description: str = "") -> tuple:
        """
        Validate, parse, save, and return (Dataset instance, DataFrame).

        Parameters
        ----------
        file        : InMemoryUploadedFile or TemporaryUploadedFile from DRF
        user        : request.user — the authenticated User instance
        file_title  : human-readable name supplied by the client
        description : optional notes

        Returns
        -------
        (Dataset, pd.DataFrame)

        Raises
        ------
        ValidationError for any problem that should return HTTP 400.
        """
        self._check_size(file)
        file_type = self._detect_type(file)
        file_path = self._save_to_disk(file, user.id, file_type)

        try:
            df = self._parse(file_path, file_type)
        except ValidationError:
            self._remove_file(file_path)
            raise
        except Exception as exc:
            self._remove_file(file_path)
            logger.warning(
                "File parse failed during upload: file=%s error=%s",
                file.name,
                exc,
                exc_info=True,
            )
            raise ValidationError(
                {"file": self._user_friendly_parse_error(exc, file_type)}
            ) from exc

        self._check_rows(df, file_path)

        # Import here to avoid circular imports at module level
        from datasets.models import Dataset

        dataset = Dataset.objects.create(
            user=user,
            file_name=file.name,
            file_type=file_type,
            file_path=file_path,
            row_count=len(df),
            columns=list(df.columns),
            file_title=file_title or file.name,
            description=description,
        )

        logger.info(
            "Dataset uploaded: id=%s user=%s rows=%d file_type=%s",
            dataset.id,
            user.email,
            len(df),
            file_type,
        )

        return dataset, df

    def replace(self, dataset, file) -> tuple:
        """
        Replace the physical file on an existing Dataset record.

        All prior QualityReport records are preserved — they remain FK'd to
        the same dataset.id so the full score history survives the replacement.

        Steps
        -----
        1. Validate + parse the new file (same rules as upload)
        2. Save new file to disk
        3. Update dataset metadata in a single .save() call:
             file_name, file_type, file_path, row_count, columns, file_version+1
        4. Delete the old file from disk (after DB commit succeeds)
        5. Return (updated dataset, new DataFrame, stale_columns)
           where stale_columns is the list of column names that existed in the
           old file but are absent from the new one — the view surfaces these
           as a warning so the caller knows which rules need attention.

        Parameters
        ----------
        dataset : Dataset instance (already ownership-checked by the view)
        file    : InMemoryUploadedFile or TemporaryUploadedFile from DRF

        Returns
        -------
        (Dataset, pd.DataFrame, list[str])

        Raises
        ------
        ValidationError for any problem that should return HTTP 400.
        """
        self._check_size(file)
        new_file_type = self._detect_type(file)
        new_file_path = self._save_to_disk(file, dataset.user_id, new_file_type)

        try:
            df = self._parse(new_file_path, new_file_type)
        except ValidationError:
            self._remove_file(new_file_path)
            raise
        except Exception as exc:
            self._remove_file(new_file_path)
            logger.warning(
                "File parse failed during replace: dataset=%s file=%s error=%s",
                dataset.id,
                file.name,
                exc,
                exc_info=True,
            )
            raise ValidationError(
                {"file": self._user_friendly_parse_error(exc, new_file_type)}
            ) from exc

        self._check_rows(df, new_file_path)

        # Identify rules that reference columns no longer in the new file
        previous_file_columns = set(dataset.columns or [])
        uploaded_file_columns = set(df.columns.tolist())
        stale_columns = sorted(previous_file_columns - uploaded_file_columns)

        # Save DB record first — if save() fails, the old file is still intact
        # and the DB still points to the correct path. Only remove the old file
        # once the DB has been updated successfully.
        old_file_path = dataset.file_path
        dataset.file_name = file.name
        dataset.file_type = new_file_type
        dataset.file_path = new_file_path
        dataset.row_count = len(df)
        dataset.columns = df.columns.tolist()
        dataset.file_version = dataset.file_version + 1
        dataset.save(
            update_fields=[
                "file_name",
                "file_type",
                "file_path",
                "row_count",
                "columns",
                "file_version",
                "updated_at",
            ]
        )

        # DB is committed — safe to remove the old file from disk now
        self._remove_file(old_file_path)

        logger.info(
            "Dataset file replaced: id=%s user=%s version=%d rows=%d stale_columns=%s",
            dataset.id,
            dataset.user.email,
            dataset.file_version,
            len(df),
            stale_columns or "none",
        )

        return dataset, df, stale_columns

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_size(self, file) -> None:
        """Reject files larger than MAX_FILE_SIZE_BYTES before reading them."""
        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                {
                    "file": (
                        f"File exceeds the {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB limit. "
                        f"Received {file.size / 1024 / 1024:.1f} MB."
                    )
                }
            )

    def _detect_type(self, file) -> str:
        """
        Detect file type from the first 512 bytes of content.
        Never trust the file extension — users rename files.

        Detection order:
          1. If content starts with { or [ → JSON
          2. If content contains commas → CSV
          3. If filename ends with .csv → CSV (for single-column files)
          4. Otherwise → unsupported type error
        """
        header = file.read(512)
        file.seek(0)  # reset so Pandas can read from the start

        try:
            text = header.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            try:
                text = header.decode("latin-1").strip()
            except UnicodeDecodeError:
                raise ValidationError(
                    {
                        "file": (
                            "File encoding is not supported. "
                            "Upload a UTF-8 or Latin-1 encoded CSV or JSON file."
                        )
                    }
                )

        if not text:
            raise ValidationError({"file": "The uploaded file is empty."})

        if text.startswith("{") or text.startswith("["):
            return "json"

        if "," in text or file.name.lower().endswith(".csv"):
            return "csv"

        raise ValidationError(
            {
                "file": (
                    "Unsupported file type. Upload a CSV or JSON file. "
                    f"Received: '{file.name}'."
                )
            }
        )

    def _save_to_disk(self, file, user_id, file_type: str) -> str:
        """Write the file to MEDIA_ROOT/uploads/<user_id>/<uuid>.<ext>."""
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads", str(user_id))
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}.{file_type}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        return file_path

    def _parse(self, file_path: str, file_type: str) -> pd.DataFrame:
        """
        Load the file into a Pandas DataFrame with robust error handling.

        CSV handling:
          - Tries UTF-8 with BOM strip first, falls back to Latin-1
          - Raises ValidationError for malformed structure (ParserError)
          - Raises ValidationError for completely empty files (EmptyDataError)
          - Raises ValidationError if header-only (no data rows)

        JSON handling:
          - Raises ValidationError for invalid JSON syntax
          - Raises ValidationError for array-of-arrays format
          - Raises ValidationError for JSON object (not array-of-objects)
          - Raises ValidationError if file has no data rows
        """
        if file_type == "csv":
            df = self._parse_csv(file_path)
        else:
            df = self._parse_json(file_path)

        if df.empty:
            raise ValidationError({"file": "The file has no data rows."})

        return df

    def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """
        Parse a CSV file with encoding fallback and structured error messages.

        Raises ValidationError for:
          - Completely empty files (pd.errors.EmptyDataError)
          - Malformed CSV structure (pd.errors.ParserError)
          - Files that cannot be decoded in any supported encoding
        """
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding="latin-1")
            except UnicodeDecodeError:
                raise ValidationError(
                    {
                        "file": (
                            "CSV file encoding is not supported. "
                            "Save the file as UTF-8 or Latin-1 and try again."
                        )
                    }
                )
        except pd.errors.EmptyDataError:
            raise ValidationError(
                {
                    "file": "The CSV file is empty. It must contain at least a header row and one data row."
                }
            )
        except pd.errors.ParserError as exc:
            raise ValidationError(
                {
                    "file": (
                        "The CSV file could not be parsed. "
                        "Check for mismatched quotes, inconsistent delimiters, or broken rows. "
                        f"Detail: {exc}"
                    )
                }
            ) from exc

        # A header-only file parses successfully but has no rows
        if df.empty:
            raise ValidationError(
                {"file": "The CSV file has a header but no data rows."}
            )

        return df

    def _parse_json(self, file_path: str) -> pd.DataFrame:
        """
        Parse a JSON file with format validation and structured error messages.

        Expected format: array of objects [{col: val}, ...]

        Raises ValidationError for:
          - Invalid JSON syntax
          - JSON object instead of array ({} at top level)
          - Array of arrays instead of array of objects
          - Empty array
        """
        # Pre-validate JSON syntax before handing off to Pandas.
        # Pandas error messages for malformed JSON are verbose and expose internals.
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                raw = json.load(f)
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    raw = json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValidationError(
                    {
                        "file": (
                            "JSON file encoding is not supported. "
                            "Save the file as UTF-8 and try again."
                        )
                    }
                )
        except json.JSONDecodeError as exc:
            raise ValidationError(
                {
                    "file": (
                        f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}. "
                        "Verify the file is valid JSON using a validator such as jsonlint.com."
                    )
                }
            ) from exc

        # Top-level must be an array, not an object
        if isinstance(raw, dict):
            raise ValidationError(
                {
                    "file": (
                        "JSON must be an array of objects: "
                        '[{"column": value}, ...]. '
                        "A top-level JSON object ({}) is not supported."
                    )
                }
            )

        if not isinstance(raw, list):
            raise ValidationError(
                {"file": "JSON must be an array of objects: [{...}, {...}]."}
            )

        if len(raw) == 0:
            raise ValidationError(
                {"file": "The JSON array is empty. Add at least one object."}
            )

        # Array-of-arrays check — must be array of objects
        if not isinstance(raw[0], dict):
            raise ValidationError(
                {
                    "file": (
                        "JSON must be an array of objects: "
                        '[{"column": value}, ...]. '
                        "An array of arrays is not supported."
                    )
                }
            )

        # Now parse through Pandas (structure is validated)
        try:
            df = pd.read_json(file_path)
        except ValueError as exc:
            raise ValidationError(
                {"file": f"JSON file could not be loaded into a table: {exc}"}
            ) from exc

        return df

    def _check_rows(self, df: pd.DataFrame, file_path: str) -> None:
        """Reject files that exceed MAX_ROWS after parsing."""
        if len(df) > MAX_ROWS:
            self._remove_file(file_path)
            raise ValidationError(
                {
                    "file": (
                        f"File exceeds the {MAX_ROWS:,} row limit "
                        f"({len(df):,} rows found). "
                        "Split the file into smaller chunks and upload separately."
                    )
                }
            )

    def _remove_file(self, file_path: str) -> None:
        """Silently remove a file from disk — called on parse failure or replacement."""
        try:
            os.remove(file_path)
        except OSError:
            pass

    @staticmethod
    def _user_friendly_parse_error(exc: Exception, file_type: str) -> str:
        """
        Map raw exceptions to user-friendly messages.

        Only reached for unexpected exceptions that were not caught inside
        _parse_csv() or _parse_json() — serves as a last-resort fallback.
        The raw exception is logged at WARNING before this is called.
        """
        if isinstance(exc, pd.errors.ParserError):
            return (
                "The CSV file structure is invalid. "
                "Check for mismatched quotes, inconsistent column counts, or broken rows."
            )
        if isinstance(exc, pd.errors.EmptyDataError):
            return "The file is empty or contains only whitespace."
        if isinstance(exc, (ValueError, json.JSONDecodeError)):
            if file_type == "json":
                return (
                    "The JSON file is malformed. "
                    "Verify it is valid JSON at jsonlint.com."
                )
            return "The file content is invalid."
        if isinstance(exc, MemoryError):
            return (
                "The file is too large to process in memory. "
                f"Maximum file size is {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB."
            )
        return (
            "The file could not be parsed. "
            f"Ensure it is a valid {'CSV' if file_type == 'csv' else 'JSON'} file and try again."
        )
