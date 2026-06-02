"""
tests/test_accounts/test_security.py
────────────────────────────────────────────────────────────────────────────────
Security-focused tests.
These verify that the auth system doesn't leak data, doesn't allow token reuse,
and properly protects all sensitive operations.
"""

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from datetime import datetime, timedelta, timezone

from accounts.tokens import password_reset_token_generator
from .conftest import NEW_PASSWORD, VALID_PASSWORD

REGISTER_URL = reverse("auth-register")
LOGIN_URL = reverse("auth-login")
ME_URL = reverse("auth-me")
REFRESH_URL = reverse("auth-refresh")
FORGOT_URL = reverse("auth-forgot-password")
RESET_URL = reverse("auth-reset-password")


@pytest.mark.django_db
class TestPasswordSecurity:
    def test_password_is_hashed_not_plaintext(self, api_client):
        plain = "Secure@123"
        api_client.post(
            REGISTER_URL,
            {
                "email": "sec@example.com",
                "password": plain,
                "first_name": "Test",
                "last_name": "User",
            },
        )
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(email="sec@example.com")
        # Password must not be stored as plaintext — works with any hasher
        assert user.password != plain
        assert "$" in user.password  # all Django hashers use $ as delimiter
        assert user.check_password(plain)  # but the hash must still verify correctly

    def test_password_never_returned_in_any_response(self, api_client, verified_user):
        # login response
        login = api_client.post(
            LOGIN_URL, {"email": verified_user.email, "password": VALID_PASSWORD}
        )
        assert "password" not in str(login.data)

        # me response
        token = AccessToken.for_user(verified_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = api_client.get(ME_URL)
        assert "password" not in str(me.data)


@pytest.mark.django_db
class TestTokenSecurity:
    def test_reset_token_is_single_use(self, api_client, verified_user):
        token = password_reset_token_generator.make_token(verified_user)
        api_client.post(
            RESET_URL,
            {"uid": str(verified_user.pk), "token": token, "password": NEW_PASSWORD},
        )
        # Second use must fail because the password hash changed
        response = api_client.post(
            RESET_URL,
            {"uid": str(verified_user.pk), "token": token, "password": "Another@789"},
        )
        assert response.status_code == 400

    def test_refresh_token_blacklisted_after_rotation(self, api_client, verified_user):
        refresh = RefreshToken.for_user(verified_user)
        api_client.post(REFRESH_URL, {"refresh": str(refresh)})
        response = api_client.post(REFRESH_URL, {"refresh": str(refresh)})
        assert response.status_code == 401

    def test_invalid_jwt_cannot_access_protected_endpoint(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer fake.jwt.token")
        assert api_client.get(ME_URL).status_code == 401

    def test_malformed_jwt_cannot_access_protected_endpoint(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer notevenjwt")
        assert api_client.get(ME_URL).status_code == 401

    def test_expired_jwt_cannot_access_protected_endpoint(
        self, api_client, verified_user
    ):
        token = AccessToken.for_user(verified_user)
        token.payload["exp"] = int(
            (datetime.now(tz=timezone.utc) - timedelta(hours=1)).timestamp()
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")
        assert api_client.get(ME_URL).status_code == 401


@pytest.mark.django_db
class TestEmailEnumerationPrevention:
    """Forgot-password and resend-verification must return 200 for unknown emails
    so attackers cannot enumerate which emails are registered."""

    def test_forgot_password_unknown_email_returns_200(self, api_client):
        response = api_client.post(FORGOT_URL, {"email": "ghost@example.com"})
        assert response.status_code == 200

    def test_resend_verification_unknown_email_returns_200(self, api_client):
        response = api_client.post(
            reverse("auth-resend-verification"), {"email": "ghost@example.com"}
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestRateLimiting:
    def setup_method(self):
        cache.clear()

    def test_forgot_password_rate_limited(self, api_client, settings):
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][
            "forgot_password"
        ] = "2/minute"
        for _ in range(2):
            api_client.post(FORGOT_URL, {"email": "test@example.com"})
        response = api_client.post(FORGOT_URL, {"email": "test@example.com"})
        assert response.status_code == 429

    def test_resend_verification_rate_limited(self, api_client, settings):
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][
            "resend_verification"
        ] = "2/minute"
        for _ in range(2):
            api_client.post(
                reverse("auth-resend-verification"), {"email": "test@example.com"}
            )
        response = api_client.post(
            reverse("auth-resend-verification"), {"email": "test@example.com"}
        )
        assert response.status_code == 429
