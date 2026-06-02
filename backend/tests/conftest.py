"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────────
Shared pytest fixtures available across every test module.

Fixtures
────────
api_client      unauthenticated DRF APIClient
auth_client     APIClient authenticated as a regular user (real JWT token)
admin_client    APIClient authenticated as an admin user
regular_user    User(role='user') instance
admin_user      User(role='admin') instance

Usage
─────
    def test_something(auth_client, regular_user):
        response = auth_client.get("/api/v1/datasets/")
        assert response.status_code == 200
"""

import io

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

UPLOAD_URL = "/api/v1/datasets/upload/"

VALID_CSV = (
    "id,age,email,score\n"
    "1,25,alice@test.com,88\n"
    "2,30,bob@test.com,92\n"
    "3,35,carol@test.com,75\n"
)


# ── Base clients ──────────────────────────────────────────────────────────────


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def regular_user(db) -> User:
    """Regular user (role='user')."""
    return User.objects.create_user(
        username="testuser",
        email="testuser@datapulse.com",
        password="TestPass123!",
        role="user",
    )


@pytest.fixture
def admin_user(db) -> User:
    """Admin user (role='admin')."""
    return User.objects.create_user(
        username="adminuser",
        email="admin@datapulse.com",
        password="AdminPass123!",
        role="admin",
    )


@pytest.fixture
def auth_client(db, api_client: APIClient, regular_user: User) -> APIClient:
    """
    APIClient pre-authenticated as a regular user.
    Uses a real JWT token — no mocking needed.
    """
    token = RefreshToken.for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def admin_client(db, api_client: APIClient, admin_user: User) -> APIClient:
    """APIClient pre-authenticated as an admin user."""
    token = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


# ── Shared dataset fixture ────────────────────────────────────────────────────


@pytest.fixture
def uploaded_dataset(auth_client, settings, tmp_path):
    """
    Upload a valid CSV and return the response dict.
    Sets MEDIA_ROOT to tmp_path so files do not persist between tests.
    """
    settings.MEDIA_ROOT = str(tmp_path)
    payload = {"file": io.BytesIO(VALID_CSV.encode())}
    payload["file"].name = "data.csv"
    response = auth_client.post(UPLOAD_URL, payload, format="multipart")
    assert response.status_code == 201, response.json()
    return response.json()
