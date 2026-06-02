"""
accounts/models.py
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    DataPulse custom user.
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
