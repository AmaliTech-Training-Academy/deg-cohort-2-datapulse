"""
accounts/validators.py
────────────────────────────────────────────────────────────────────────────────
Password strength validation used by both registration and password reset.
"""

import re

from rest_framework import serializers


def validate_password_strength(password: str) -> str:
    """
    Enforces:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
    """
    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least one digit (0-9)")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>?/\\|`~]", password):
        errors.append("at least one special character (!@#$%^&*...)")

    if errors:
        raise serializers.ValidationError(
            f"Password must contain: {', '.join(errors)}."
        )

    return password
