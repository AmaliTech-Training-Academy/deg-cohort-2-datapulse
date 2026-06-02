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

Called by DatasetUploadView — no Django request object inside this class,
only primitives and the InMemoryUploadedFile / TemporaryUploadedFile object
that DRF passes from MultiPartParser.
"""

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
        except Exception as exc:
            self._remove_file(file_path)
            raise ValidationError({"file": f"Could not parse file: {exc}"}) from exc

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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_size(self, file) -> None:
        """Reject files larger than MAX_FILE_SIZE_BYTES before reading them."""
        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                {
                    "file": f"File exceeds the {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB limit."
                }
            )

    def _detect_type(self, file) -> str:
        """
        Detect file type from the first 512 bytes of content.
        Never trust the file extension — users rename files.
        """
        header = file.read(512)
        file.seek(0)  # reset so Pandas can read from the start

        try:
            text = header.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            text = header.decode("latin-1").strip()

        if text.startswith("{") or text.startswith("["):
            return "json"

        # CSV: has commas or the filename ends with .csv
        if "," in text or file.name.lower().endswith(".csv"):
            return "csv"

        raise ValidationError(
            {"file": "Unsupported file type. Upload a CSV or JSON file."}
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
        Load the file into a Pandas DataFrame.

        CSV: tries UTF-8 with BOM strip first, falls back to Latin-1.
        JSON: expects array-of-objects [{col: val}, ...].
              Rejects array-of-arrays (produces integer column names).
        """
        if file_type == "csv":
            try:
                df = pd.read_csv(file_path, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin-1")

        else:  # json
            df = pd.read_json(file_path)
            # Guard against array-of-arrays format
            if all(isinstance(c, int) for c in df.columns):
                raise ValueError(
                    "JSON must be an array of objects "
                    '[{"col": value}, ...], not an array of arrays.'
                )

        if df.empty:
            raise ValueError("File has no data rows.")

        return df

    def _check_rows(self, df: pd.DataFrame, file_path: str) -> None:
        """Reject files that exceed MAX_ROWS after parsing."""
        if len(df) > MAX_ROWS:
            self._remove_file(file_path)
            raise ValidationError(
                {
                    "file": f"File exceeds the {MAX_ROWS:,} row limit ({len(df):,} rows found)."
                }
            )

    def _remove_file(self, file_path: str) -> None:
        """Silently remove a file from disk on parse failure."""
        try:
            os.remove(file_path)
        except OSError:
            pass
