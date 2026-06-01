"""
tests/test_accounts/test_integration.py
────────────────────────────────────────────────────────────────────────────────
Full end-to-end flow tests.
These test the COMPLETE user journey, not individual endpoints.

Flow covered:
    register → verify email → login → forgot password → reset password → login with new password
"""

import pytest
from django.urls import reverse

from .conftest import NEW_PASSWORD, VALID_REGISTER_PAYLOAD, extract_reset_params, extract_token_from_email

REGISTER_URL = reverse("auth-register")
LOGIN_URL = reverse("auth-login")
VERIFY_URL = reverse("auth-verify-email")
FORGOT_URL = reverse("auth-forgot-password")
RESET_URL = reverse("auth-reset-password")
ME_URL = reverse("auth-me")


@pytest.mark.django_db
class TestFullAuthFlow:
    def test_register_to_login_flow(self, api_client, mailoutbox):
        # 1. Register
        reg = api_client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD)
        assert reg.status_code == 201
        assert reg.data["user"]["is_email_verified"] is False

        # 2. Cannot login before verifying email
        login_attempt = api_client.post(LOGIN_URL, {
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": VALID_REGISTER_PAYLOAD["password"],
        })
        assert login_attempt.status_code == 400

        # 3. Verify email using token from email
        token = extract_token_from_email(mailoutbox[0].body)
        verify = api_client.post(VERIFY_URL, {"token": token})
        assert verify.status_code == 200

        # 4. Login now succeeds
        login = api_client.post(LOGIN_URL, {
            "email": VALID_REGISTER_PAYLOAD["email"],
            "password": VALID_REGISTER_PAYLOAD["password"],
        })
        assert login.status_code == 200
        assert "access" in login.data
        assert login.data["user"]["is_email_verified"] is True

    def test_full_password_reset_flow(self, api_client, verified_user, mailoutbox):
        # 1. Request password reset
        forgot = api_client.post(FORGOT_URL, {"email": verified_user.email})
        assert forgot.status_code == 200
        assert len(mailoutbox) == 1

        # 2. Extract uid + token from the reset email
        uid, token = extract_reset_params(mailoutbox[0].body)

        # 3. Reset the password
        reset = api_client.post(RESET_URL, {"uid": uid, "token": token, "password": NEW_PASSWORD})
        assert reset.status_code == 200

        # 4. Old password no longer works
        old_login = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": "Secure@123"})
        assert old_login.status_code == 401  # wrong credentials → 401

        # 5. New password works
        new_login = api_client.post(LOGIN_URL, {"email": verified_user.email, "password": NEW_PASSWORD})
        assert new_login.status_code == 200
        assert "access" in new_login.data

    def test_complete_journey(self, api_client, mailoutbox):
        """
        register → verify email → login → forgot password → reset password → login with new password
        """
        email = "journey@example.com"
        password = "Journey@123"

        # 1. Register
        api_client.post(REGISTER_URL, {
            "email": email,
            "first_name": "Journey",
            "last_name": "User",
            "password": password,
        })

        # 2. Verify email
        verify_token = extract_token_from_email(mailoutbox[0].body)
        api_client.post(VERIFY_URL, {"token": verify_token})
        mailoutbox.clear()

        # 3. Login
        login = api_client.post(LOGIN_URL, {"email": email, "password": password})
        assert login.status_code == 200
        access_token = login.data["access"]

        # 4. Access protected endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me = api_client.get(ME_URL)
        assert me.status_code == 200
        assert me.data["email"] == email

        # 5. Forgot password
        api_client.credentials()  # clear auth
        api_client.post(FORGOT_URL, {"email": email})
        uid, reset_token = extract_reset_params(mailoutbox[0].body)

        # 6. Reset password
        api_client.post(RESET_URL, {"uid": uid, "token": reset_token, "password": NEW_PASSWORD})

        # 7. Login with new password
        final_login = api_client.post(LOGIN_URL, {"email": email, "password": NEW_PASSWORD})
        assert final_login.status_code == 200
        assert "access" in final_login.data
