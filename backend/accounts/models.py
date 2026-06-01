"""
accounts/models.py
────────────────────────────────────────────────────────────────────────────────
Custom User model.

Why a custom User model?
    Django's built-in User uses 'username' as the login field.  DataPulse uses
    'email' as the primary identifier (as per the project spec and the team's
    agreed API contract).  AUTH_USER_MODEL must be set to this model BEFORE
    the first migration is created.

Role field:
    Two roles are supported — "user" (default) and "admin".
    Ownership checks use: dataset.uploaded_by == request.user
    Admin access checks use: request.user.role == "admin"

TODO (implement during your sprint):
    • Add any additional profile fields your team needs here
    • Add Meta indexes if you add fields you'll filter by
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    DataPulse custom user model.

    Extends Django's AbstractUser so we inherit password hashing,
    is_active, date_joined, last_login, and the full auth machinery
    without reimplementing them.

    Login field is email (not username).
    USERNAME_FIELD and REQUIRED_FIELDS are set accordingly.
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    # Override email to make it unique and required — it's the login field
    email = models.EmailField(
        unique=True,
        help_text="Primary identifier used to log in.",
    )

    # Role-based access control
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        help_text="Controls what the user can access.",
    )

    # Use email as the login identifier instead of username
    USERNAME_FIELD = "email"
    # username is still required by AbstractUser but not used for login
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
        """Convenience property — avoids string comparison at call sites."""
        return self.role == self.Role.ADMIN
