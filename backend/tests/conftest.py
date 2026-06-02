"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────────
Shared pytest fixtures.

These fixtures are available in every test file without importing.
Add new shared fixtures here; app-specific fixtures go in each app's
own test directory.

Available fixtures:
    api_client        — unauthenticated DRF APIClient
    auth_client       — APIClient pre-authenticated as a regular user
    admin_client      — APIClient pre-authenticated as an admin user
    regular_user      — a User instance with role="user"
    admin_user        — a User instance with role="admin"

Usage in a test:
    def test_something(auth_client, regular_user):
        response = auth_client.get("/api/v1/datasets/")
        assert response.status_code == 200
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ── Database access ───────────────────────────────────────────────────────────
# All fixtures that touch the database must declare db or transactional_db.


@pytest.fixture
def api_client() -> APIClient:
    """An unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def regular_user(db) -> User:
    """
    A regular user (role='user') for use in tests.

    TODO: update field values once User.objects.create_user() is implemented.
    """
    return User.objects.create_user(
        username="testuser",
        email="testuser@datapulse.com",
        password="TestPass123!",
        role="user",
    )


@pytest.fixture
def admin_user(db) -> User:
    """
    An admin user (role='admin') for use in tests.

    TODO: update field values once the User model is fully implemented.
    """
    return User.objects.create_user(
        username="adminuser",
        email="admin@datapulse.com",
        password="AdminPass123!",
        role="admin",
    )


@pytest.fixture
def auth_client(api_client: APIClient, regular_user: User) -> APIClient:
    """
    An APIClient pre-authenticated as a regular user.

    Uses SimpleJWT to generate a real access token — no mocking needed.
    The Authorization: Bearer header is set automatically for every request.
    """
    token = RefreshToken.for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client: APIClient, admin_user: User) -> APIClient:
    """An APIClient pre-authenticated as an admin user."""
    token = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client
