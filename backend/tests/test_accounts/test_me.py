"""
tests/test_accounts/test_me.py
────────────────────────────────────────────────────────────────────────────────
Me endpoint tests.
GET /api/v1/auth/me/
"""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta, timezone

URL = reverse("auth-me")


@pytest.mark.django_db
class TestMeEndpoint:
    def test_authenticated_user_returns_200(self, verified_client):
        assert verified_client.get(URL).status_code == 200

    def test_returns_correct_user_data(self, api_client, verified_user):
        token = AccessToken.for_user(verified_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.get(URL)
        assert response.data["email"] == verified_user.email
        assert response.data["first_name"] == verified_user.first_name
        assert response.data["role"] == verified_user.role
        assert response.data["is_email_verified"] is True

    def test_password_not_in_response(self, verified_client):
        response = verified_client.get(URL)
        assert "password" not in response.data

    def test_unauthenticated_returns_401(self, api_client):
        assert api_client.get(URL).status_code == 401

    def test_invalid_jwt_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.jwt.token")
        assert api_client.get(URL).status_code == 401

    def test_malformed_authorization_header_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="NotBearer sometoken")
        assert api_client.get(URL).status_code == 401

    def test_expired_jwt_returns_401(self, api_client, verified_user):
        token = AccessToken.for_user(verified_user)
        token.payload["exp"] = int(
            (datetime.now(tz=timezone.utc) - timedelta(hours=1)).timestamp()
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")
        assert api_client.get(URL).status_code == 401
