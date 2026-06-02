"""
tests/test_accounts/test_forgot_password.py
────────────────────────────────────────────────────────────────────────────────
Forgot password endpoint tests.
POST /api/v1/auth/forgot-password/
"""

import pytest
from django.urls import reverse

URL = reverse("auth-forgot-password")


@pytest.mark.django_db
class TestForgotPassword:
    def test_known_email_returns_200(self, api_client, verified_user):
        response = api_client.post(URL, {"email": verified_user.email})
        assert response.status_code == 200

    def test_reset_email_is_sent(self, api_client, verified_user, mailoutbox):
        api_client.post(URL, {"email": verified_user.email})
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [verified_user.email]

    def test_reset_email_contains_uid_and_token(
        self, api_client, verified_user, mailoutbox
    ):
        api_client.post(URL, {"email": verified_user.email})
        body = mailoutbox[0].body
        assert "uid=" in body
        assert "token=" in body

    def test_reset_link_contains_correct_uid(
        self, api_client, verified_user, mailoutbox
    ):
        api_client.post(URL, {"email": verified_user.email})
        body = mailoutbox[0].body
        assert str(verified_user.pk) in body

    def test_unknown_email_still_returns_200(self, api_client):
        # Security: must not reveal whether the email is registered
        response = api_client.post(URL, {"email": "ghost@example.com"})
        assert response.status_code == 200

    def test_unknown_email_sends_no_email(self, api_client, mailoutbox):
        api_client.post(URL, {"email": "ghost@example.com"})
        assert len(mailoutbox) == 0

    def test_missing_email_returns_400(self, api_client):
        assert api_client.post(URL, {}).status_code == 400

    def test_invalid_email_format_returns_400(self, api_client):
        assert api_client.post(URL, {"email": "not-an-email"}).status_code == 400
