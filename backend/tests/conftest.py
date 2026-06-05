"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────────
Shared pytest fixtures available in every test file without importing.
"""

import io
import os

# Set before Django settings load so decouple never hits the CRLF parsing bug
# where DEBUG=True followed by a comment is read as "True\n# comment".
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("LOG_LEVEL", "INFO")

import pytest  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402


@pytest.fixture(autouse=True)
def disable_auto_check_thread(monkeypatch):
    """
    Replace the background-thread dispatch on DatasetFileUpdateView with a
    no-op for every test.

    SQLite (used by the test suite) does not support concurrent writes, so
    running the validation engine in a background thread causes
    'database table is locked' errors.  Tests that need to assert on the
    auto-check result should use the sync_auto_check fixture defined in
    tests/datasets/test_auto_check_on_file_replace.py, which patches the
    method to run synchronously instead.
    """
    from datasets.views import DatasetFileUpdateView

    monkeypatch.setattr(
        DatasetFileUpdateView,
        "_dispatch_auto_check",
        lambda self, dataset_id, report_id: None,
    )


User = get_user_model()

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    b"id,age,email,score\n"
    b"1,25,alice@test.com,88\n"
    b"2,30,bob@test.com,92\n"
    b"3,35,carol@test.com,75\n"
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def regular_user(db) -> User:
    return User.objects.create_user(
        username="testuser@datapulse.com",
        email="testuser@datapulse.com",
        password="TestPass123!",
        role="user",
        is_email_verified=True,
    )


@pytest.fixture
def admin_user(db) -> User:
    return User.objects.create_user(
        username="admin@datapulse.com",
        email="admin@datapulse.com",
        password="AdminPass123!",
        role="admin",
        is_email_verified=True,
    )


@pytest.fixture
def auth_client(regular_user: User) -> APIClient:
    """Authenticated client — uses its own APIClient so it never aliases api_client."""
    client = APIClient()
    token = RefreshToken.for_user(regular_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def admin_client(admin_user: User) -> APIClient:
    """Authenticated admin client — uses its own APIClient so it never aliases api_client."""
    client = APIClient()
    token = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def uploaded_dataset(auth_client, settings, tmp_path):
    """
    Upload a valid CSV and return the response dict.
    Sets MEDIA_ROOT to tmp_path so files do not persist between tests.
    """
    settings.MEDIA_ROOT = str(tmp_path)
    f = io.BytesIO(VALID_CSV)
    f.name = "data.csv"
    response = auth_client.post(UPLOAD_URL, {"file": f}, format="multipart")
    assert response.status_code == 201, response.json()
    return response.json()
