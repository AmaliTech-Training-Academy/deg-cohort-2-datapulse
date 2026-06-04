"""
accounts/serializers.py
────────────────────────────────────────────────────────────────────────────────
Serializers for all authentication flows.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .tokens import decode_email_verification_token, password_reset_token_generator
from .validators import validate_password_strength

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Min 8 chars, must include uppercase, lowercase, digit, and special character.",
    )

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password"]
        read_only_fields = ["id"]

    def validate_password(self, value: str) -> str:
        return validate_password_strength(value)

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        # AbstractUser still requires a username field; we mirror it from email.
        user = User.objects.create_user(
            username=validated_data["email"],
            password=password,
            **validated_data,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only — safe user fields returned by /me/ and embedded in login responses."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "created_at",
            "is_email_verified",
        ]
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends the standard JWT login response with the user's profile data."""

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise serializers.ValidationError(
                {"email": "Please verify your email address before logging in."}
            )
        data["user"] = UserProfileSerializer(self.user).data
        return data


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value: str) -> str:
        email = decode_email_verification_token(value)
        if email is None:
            raise serializers.ValidationError(
                "This verification link is invalid or has expired."
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "This verification link is invalid or has expired."
            )
        if user.is_email_verified:
            raise serializers.ValidationError("This email address is already verified.")
        self._verified_user = user
        return value

    def save(self) -> User:
        user = self._verified_user
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return user


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            self._user = None
            return value
        if user.is_email_verified:
            raise serializers.ValidationError("This email address is already verified.")
        self._user = user
        return value

    @property
    def user(self):
        return getattr(self, "_user", None)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        try:
            self._user = User.objects.get(email=value)
        except User.DoesNotExist:
            # Intentionally not revealing whether the email is registered.
            self._user = None
        return value

    @property
    def user(self):
        return getattr(self, "_user", None)


class UserListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for GET /api/v1/auth/users/ (admin only).
    Uses real model field names — the frontend maps them for display.
    datasets_count is annotated by the view queryset.
    """

    datasets_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "last_login",
            "created_at",
            "is_email_verified",
            "datasets_count",
        ]
        read_only_fields = fields


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.UUIDField()
    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Min 8 chars, must include uppercase, lowercase, digit, and special character.",
    )

    def validate_password(self, value: str) -> str:
        return validate_password_strength(value)

    def validate(self, attrs: dict) -> dict:
        try:
            user = User.objects.get(pk=attrs["uid"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"token": "Invalid or expired reset link."}
            )

        if not password_reset_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": "Invalid or expired reset link."}
            )

        self._user = user
        return attrs

    def save(self) -> User:
        self._user.set_password(self.validated_data["password"])
        self._user.save(update_fields=["password"])
        return self._user
