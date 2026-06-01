"""
tests/test_accounts/test_verify_email.py
────────────────────────────────────────────────────────────────────────────────
Email verification endpoint tests.
POST /api/v1/auth/verify-email/
POST /api/v1/auth/resend-verification/
"""

import pytest
from django.urls import reverse
from unittest.mock import patch

VERIFY_URL = reverse("auth-verify-email")
RESEND_URL = reverse("auth-resend-verification")


@pytest.mark.django_db
class TestVerifyEmail:
    def test_valid_token_returns_200(self, api_client, email_verification_token):
        response = api_client.post(VERIFY_URL, {"token": email_verification_token})
        assert response.status_code == 200

    def test_valid_token_marks_user_verified(self, api_client, unverified_user, email_verification_token):
        api_client.post(VERIFY_URL, {"token": email_verification_token})
        unverified_user.refresh_from_db()
        assert unverified_user.is_email_verified is True

    def test_invalid_token_returns_400(self, api_client):
        response = api_client.post(VERIFY_URL, {"token": "completely-invalid-token"})
        assert response.status_code == 400

    def test_expired_token_returns_400(self, api_client):
        with patch("accounts.serializers.decode_email_verification_token", return_value=None):
            response = api_client.post(VERIFY_URL, {"token": "any-token"})
        assert response.status_code == 400

    def test_already_verified_returns_400(self, api_client, verified_user):
        from accounts.tokens import make_email_verification_token
        token = make_email_verification_token(verified_user.email)
        response = api_client.post(VERIFY_URL, {"token": token})
        assert response.status_code == 400

    def test_reused_token_returns_400(self, api_client, unverified_user, email_verification_token):
        # First use succeeds
        api_client.post(VERIFY_URL, {"token": email_verification_token})
        # Second use — user is already verified
        response = api_client.post(VERIFY_URL, {"token": email_verification_token})
        assert response.status_code == 400

    def test_missing_token_returns_400(self, api_client):
        assert api_client.post(VERIFY_URL, {}).status_code == 400


@pytest.mark.django_db
class TestResendVerification:
    def test_known_unverified_email_returns_200(self, api_client, unverified_user, mailoutbox):
        response = api_client.post(RESEND_URL, {"email": unverified_user.email})
        assert response.status_code == 200
        assert len(mailoutbox) == 1

    def test_unknown_email_still_returns_200(self, api_client):
        # Must not reveal whether the email is registered
        response = api_client.post(RESEND_URL, {"email": "nobody@example.com"})
        assert response.status_code == 200

    def test_already_verified_email_returns_400(self, api_client, verified_user):
        response = api_client.post(RESEND_URL, {"email": verified_user.email})
        assert response.status_code == 400
