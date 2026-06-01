"""
accounts/serializers.py
────────────────────────────────────────────────────────────────────────────────
Serializers for user registration and profile retrieval.

RegisterSerializer
    Validates and creates a new User.
    Enforces:
        • password minimum length (8 chars)
        • password confirmation match
        • unique email (handled by model + UniqueValidator)

UserProfileSerializer
    Read-only — returns safe user fields.
    Used by the /auth/me/ endpoint and embedded in login responses.

TODO (implement during your sprint):
    • Implement RegisterSerializer.create() — call User.objects.create_user()
    • Add any custom validation rules your team needs
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.

    Accepts: email, password, password2 (confirmation), first_name, last_name
    Returns: id, email, role  (password is write-only, never echoed back)
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Minimum 8 characters.",
    )
    password2 = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Must match the password field.",
    )

    class Meta:
        model  = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs: dict) -> dict:
        """Confirm the two password fields match."""
        # TODO: implement password validation
        raise NotImplementedError(
            "RegisterSerializer.validate() is not implemented yet. "
            "Check attrs['password'] == attrs['password2'] and raise "
            "serializers.ValidationError if they differ."
        )

    def create(self, validated_data: dict) -> User:
        """
        Create and return a new User.

        TODO: implement this method.
        Steps:
            1. Remove 'password2' from validated_data (not a model field)
            2. Call User.objects.create_user(**validated_data)
               create_user() handles password hashing automatically
            3. Return the created user instance
        """
        raise NotImplementedError(
            "RegisterSerializer.create() is not implemented yet."
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for returning safe user data.

    Used by:
        • GET /api/v1/auth/me/     — current user profile
        • POST /api/v1/auth/login/ — embedded in the login response
    """

    class Meta:
        model  = User
        fields = ["id", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = fields
