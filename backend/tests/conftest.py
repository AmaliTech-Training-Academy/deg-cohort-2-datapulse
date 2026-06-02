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

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

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
def auth_client(api_client: APIClient, regular_user: User) -> APIClient:
    token = RefreshToken.for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client: APIClient, admin_user: User) -> APIClient:
    token = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


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
