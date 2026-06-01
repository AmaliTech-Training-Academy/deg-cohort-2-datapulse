"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────────
Shared pytest fixtures available in every test file without importing.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


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
