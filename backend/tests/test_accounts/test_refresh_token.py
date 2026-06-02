"""
tests/test_accounts/test_refresh_token.py
────────────────────────────────────────────────────────────────────────────────
Token refresh endpoint tests.
POST /api/v1/auth/refresh/
"""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

URL = reverse("auth-refresh")


@pytest.mark.django_db
class TestRefreshToken:
    def test_valid_refresh_token_returns_200(self, api_client, verified_user):
        refresh = RefreshToken.for_user(verified_user)
        response = api_client.post(URL, {"refresh": str(refresh)})
        assert response.status_code == 200

    def test_new_access_token_is_returned(self, api_client, verified_user):
        refresh = RefreshToken.for_user(verified_user)
        response = api_client.post(URL, {"refresh": str(refresh)})
        assert "access" in response.data

    def test_new_refresh_token_is_returned(self, api_client, verified_user):
        # ROTATE_REFRESH_TOKENS=True means a new refresh token is issued each time
        refresh = RefreshToken.for_user(verified_user)
        response = api_client.post(URL, {"refresh": str(refresh)})
        assert "refresh" in response.data

    def test_blacklisted_token_returns_401(self, api_client, verified_user):
        refresh = RefreshToken.for_user(verified_user)
        # First use rotates and blacklists the original token
        api_client.post(URL, {"refresh": str(refresh)})
        # Second use of the same token must fail
        response = api_client.post(URL, {"refresh": str(refresh)})
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, api_client):
        response = api_client.post(URL, {"refresh": "not-a-valid-token"})
        assert response.status_code == 401

    def test_missing_token_returns_400(self, api_client):
        assert api_client.post(URL, {}).status_code == 400
