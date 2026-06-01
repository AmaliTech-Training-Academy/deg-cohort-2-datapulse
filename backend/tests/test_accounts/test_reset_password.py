"""
tests/test_accounts/test_reset_password.py
────────────────────────────────────────────────────────────────────────────────
Reset password endpoint tests.
POST /api/v1/auth/reset-password/
"""

import pytest
from django.urls import reverse

from accounts.tokens import password_reset_token_generator
from .conftest import NEW_PASSWORD, VALID_PASSWORD

URL = reverse("auth-reset-password")
LOGIN_URL = reverse("auth-login")


def reset_payload(verified_user, password_reset_token, password=NEW_PASSWORD):
    return {
        "uid": str(verified_user.pk),
        "token": password_reset_token,
        "password": password,
    }


@pytest.mark.django_db
class TestResetPasswordSuccess:
    def test_returns_200(self, api_client, verified_user, password_reset_token):
        response = api_client.post(URL, reset_payload(verified_user, password_reset_token))
        assert response.status_code == 200

    def test_password_is_changed(self, api_client, verified_user, password_reset_token):
        api_client.post(URL, reset_payload(verified_user, password_reset_token))
        verified_user.refresh_from_db()
        assert verified_user.check_password(NEW_PASSWORD)

    def test_old_password_no_longer_works(self, api_client, verified_user, password_reset_token):
        api_client.post(URL, reset_payload(verified_user, password_reset_token))
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": VALID_PASSWORD})
        assert response.status_code == 401  # wrong credentials → 401

    def test_can_login_with_new_password(self, api_client, verified_user, password_reset_token):
        api_client.post(URL, reset_payload(verified_user, password_reset_token))
        response = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": NEW_PASSWORD})
        assert response.status_code == 200

    def test_token_is_invalidated_after_use(self, api_client, verified_user, password_reset_token):
        api_client.post(URL, reset_payload(verified_user, password_reset_token))
        # Try to use the same token again with a different password
        response = api_client.post(URL, reset_payload(verified_user, password_reset_token, "Another@789"))
        assert response.status_code == 400


@pytest.mark.django_db
class TestResetPasswordFailure:
    def test_invalid_token_returns_400(self, api_client, verified_user):
        payload = {"uid": str(verified_user.pk), "token": "invalid-token", "password": NEW_PASSWORD}
        assert api_client.post(URL, payload).status_code == 400

    def test_invalid_uid_returns_400(self, api_client, password_reset_token):
        import uuid
        payload = {"uid": str(uuid.uuid4()), "token": password_reset_token, "password": NEW_PASSWORD}
        assert api_client.post(URL, payload).status_code == 400

    def test_expired_token_returns_400(self, api_client, verified_user, settings):
        settings.PASSWORD_RESET_TIMEOUT = 1  # 1 second
        token = password_reset_token_generator.make_token(verified_user)
        import time; time.sleep(2)
        payload = {"uid": str(verified_user.pk), "token": token, "password": NEW_PASSWORD}
        assert api_client.post(URL, payload).status_code == 400

    def test_weak_password_returns_400(self, api_client, verified_user, password_reset_token):
        payload = {"uid": str(verified_user.pk), "token": password_reset_token, "password": "weak"}
        assert api_client.post(URL, payload).status_code == 400

    def test_missing_uid_returns_400(self, api_client, password_reset_token):
        assert api_client.post(URL, {"token": password_reset_token, "password": NEW_PASSWORD}).status_code == 400

    def test_missing_token_returns_400(self, api_client, verified_user):
        assert api_client.post(URL, {"uid": str(verified_user.pk), "password": NEW_PASSWORD}).status_code == 400
