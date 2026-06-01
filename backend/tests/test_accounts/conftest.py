"""
tests/test_accounts/conftest.py
────────────────────────────────────────────────────────────────────────────────
Fixtures specific to authentication tests.
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.tokens import make_email_verification_token, password_reset_token_generator


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Clear the throttle cache before every test so rate limits don't bleed across tests."""
    cache.clear()
    yield
    cache.clear()

User = get_user_model()

# ── Reusable valid payloads ───────────────────────────────────────────────────

VALID_REGISTER_PAYLOAD = {
    "email": "newuser@example.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "password": "Secure@123",
}

VALID_PASSWORD = "Secure@123"
NEW_PASSWORD = "NewPass@456"


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def verified_user(db) -> User:
    return User.objects.create_user(
        username="verified@example.com",
        email="verified@example.com",
        password=VALID_PASSWORD,
        first_name="Jane",
        last_name="Doe",
        is_email_verified=True,
    )


@pytest.fixture
def unverified_user(db) -> User:
    return User.objects.create_user(
        username="unverified@example.com",
        email="unverified@example.com",
        password=VALID_PASSWORD,
        is_email_verified=False,
    )


@pytest.fixture
def inactive_user(db) -> User:
    return User.objects.create_user(
        username="inactive@example.com",
        email="inactive@example.com",
        password=VALID_PASSWORD,
        is_email_verified=True,
        is_active=False,
    )


@pytest.fixture
def verified_client(api_client: APIClient, verified_user: User) -> APIClient:
    token = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


# ── Token fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def email_verification_token(unverified_user: User) -> str:
    return make_email_verification_token(unverified_user.email)


@pytest.fixture
def password_reset_token(verified_user: User) -> str:
    return password_reset_token_generator.make_token(verified_user)


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_token_from_email(body: str) -> str:
    """Pulls the ?token=... value out of an email body."""
    match = re.search(r"\?token=(\S+)", body)
    assert match, f"No token found in email body:\n{body}"
    return match.group(1)


def extract_reset_params(body: str) -> tuple[str, str]:
    """Returns (uid, token) from a password reset email body."""
    uid = re.search(r"uid=([^&\s]+)", body)
    token = re.search(r"token=([^&\s]+)", body)
    assert uid and token, f"Could not parse reset link from:\n{body}"
    return uid.group(1), token.group(1)
