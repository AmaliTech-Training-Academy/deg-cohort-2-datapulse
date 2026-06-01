"""
tests/test_accounts/test_register.py
────────────────────────────────────────────────────────────────────────────────
Register endpoint tests.
POST /api/v1/auth/register/
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .conftest import VALID_REGISTER_PAYLOAD

User = get_user_model()
URL = reverse("auth-register")


# ── Success ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterSuccess:
    def test_returns_201(self, api_client):
        response = api_client.post(URL, VALID_REGISTER_PAYLOAD)
        assert response.status_code == 201

    def test_user_is_created_in_db(self, api_client):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        assert User.objects.filter(email=VALID_REGISTER_PAYLOAD["email"]).exists()

    def test_response_contains_user_data(self, api_client):
        response = api_client.post(URL, VALID_REGISTER_PAYLOAD)
        user_data = response.data["user"]
        assert user_data["email"] == VALID_REGISTER_PAYLOAD["email"]
        assert user_data["first_name"] == VALID_REGISTER_PAYLOAD["first_name"]
        assert user_data["last_name"] == VALID_REGISTER_PAYLOAD["last_name"]

    def test_password_is_not_in_response(self, api_client):
        response = api_client.post(URL, VALID_REGISTER_PAYLOAD)
        assert "password" not in response.data
        assert "password" not in response.data.get("user", {})

    def test_password_is_hashed_in_db(self, api_client):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        user = User.objects.get(email=VALID_REGISTER_PAYLOAD["email"])
        plain = VALID_REGISTER_PAYLOAD["password"]
        assert user.password != plain          # not stored as plaintext
        assert "$" in user.password            # hashed — all Django hashers use $ delimiter
        assert user.check_password(plain)      # hash verifies correctly

    def test_user_is_not_verified_yet(self, api_client):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        user = User.objects.get(email=VALID_REGISTER_PAYLOAD["email"])
        assert user.is_email_verified is False

    def test_verification_email_is_sent(self, api_client, mailoutbox):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [VALID_REGISTER_PAYLOAD["email"]]

    def test_verification_email_contains_token_link(self, api_client, mailoutbox):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        assert "verify-email?token=" in mailoutbox[0].body

    def test_user_role_defaults_to_user(self, api_client):
        api_client.post(URL, VALID_REGISTER_PAYLOAD)
        user = User.objects.get(email=VALID_REGISTER_PAYLOAD["email"])
        assert user.role == "user"


# ── Validation failures ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterValidation:
    def test_missing_email_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "email": ""}
        assert api_client.post(URL, data).status_code == 400

    def test_invalid_email_format_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "email": "not-an-email"}
        assert api_client.post(URL, data).status_code == 400

    def test_duplicate_email_returns_400(self, api_client, verified_user):
        data = {**VALID_REGISTER_PAYLOAD, "email": verified_user.email}
        assert api_client.post(URL, data).status_code == 400

    def test_missing_password_returns_400(self, api_client):
        data = {k: v for k, v in VALID_REGISTER_PAYLOAD.items() if k != "password"}
        assert api_client.post(URL, data).status_code == 400

    def test_password_too_short_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "password": "Ab1!"}
        assert api_client.post(URL, data).status_code == 400

    def test_password_no_uppercase_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "password": "secure@123"}
        assert api_client.post(URL, data).status_code == 400

    def test_password_no_lowercase_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "password": "SECURE@123"}
        assert api_client.post(URL, data).status_code == 400

    def test_password_no_digit_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "password": "Secure@abc"}
        assert api_client.post(URL, data).status_code == 400

    def test_password_no_special_char_returns_400(self, api_client):
        data = {**VALID_REGISTER_PAYLOAD, "password": "Secure123"}
        assert api_client.post(URL, data).status_code == 400
