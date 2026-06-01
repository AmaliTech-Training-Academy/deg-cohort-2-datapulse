"""
accounts/models.py
────────────────────────────────────────────────────────────────────────────────
Custom User model — matches the schema.pdf users table exactly:
    id uuid, email, password, role, created_at
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    DataPulse custom user.

    Differences from Django's default User:
    - UUID primary key (matches schema)
    - email is the login field (not username)
    - role field for RBAC
    - is_email_verified for the email confirmation flow
    - created_at replaces date_joined to match schema naming
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        help_text="Primary identifier used to log in.",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        help_text="Controls what the user can access.",
    )

    is_email_verified = models.BooleanField(
        default=False,
        help_text="True after the user clicks the verification link.",
    )

    # Rename date_joined → created_at to match the schema
    date_joined = None
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["role"], name="idx_user_role"),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN
