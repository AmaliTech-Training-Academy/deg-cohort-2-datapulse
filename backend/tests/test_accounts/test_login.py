"""
tests/test_accounts/test_login.py
────────────────────────────────────────────────────────────────────────────────
Login endpoint tests.
POST /api/v1/auth/login/
"""

import pytest
from django.urls import reverse

from .conftest import VALID_PASSWORD

URL = reverse("auth-login")


@pytest.mark.django_db
class TestLoginSuccess:
    def test_returns_200(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        assert response.status_code == 200

    def test_access_token_returned(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        assert "access" in response.data

    def test_refresh_token_returned(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        assert "refresh" in response.data

    def test_user_profile_embedded_in_response(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        user_data = response.data["user"]
        assert user_data["email"] == verified_user.email
        assert user_data["role"] == "user"
        assert user_data["is_email_verified"] is True

    def test_password_not_in_response(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        assert "password" not in response.data
        assert "password" not in response.data.get("user", {})


@pytest.mark.django_db
class TestLoginFailure:
    def test_wrong_password_returns_401(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email, "password": "WrongPass@1"})
        assert response.status_code == 401

    def test_nonexistent_email_returns_401(self, api_client):
        response = api_client.post(URL, {"email": "nobody@example.com", "password": VALID_PASSWORD})
        assert response.status_code == 401

    def test_unverified_email_returns_400(self, api_client, unverified_user):
        # 400 not 401 — credentials are correct but our custom check blocks the login
        response = api_client.post(URL, {"email": unverified_user.email, "password": VALID_PASSWORD})
        assert response.status_code == 400

    def test_unverified_error_message_is_clear(self, api_client, unverified_user):
        response = api_client.post(URL, {"email": unverified_user.email, "password": VALID_PASSWORD})
        assert "verify" in str(response.data).lower()

    def test_inactive_user_returns_401(self, api_client, inactive_user):
        response = api_client.post(URL, {"email": inactive_user.email, "password": VALID_PASSWORD})
        assert response.status_code == 401

    def test_missing_email_returns_400(self, api_client):
        assert api_client.post(URL, {"password": VALID_PASSWORD}).status_code == 400

    def test_missing_password_returns_400(self, api_client, verified_user):
        assert api_client.post(URL, {"email": verified_user.email}).status_code == 400
