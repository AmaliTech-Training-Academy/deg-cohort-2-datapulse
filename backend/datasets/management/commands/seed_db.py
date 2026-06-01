"""
datasets/management/commands/seed_db.py
────────────────────────────────────────────────────────────────────────────────
Management command: python manage.py seed_db

Creates the default users required for:
    • Local development
    • Docker Compose startup (run automatically by docker-compose.yml)
    • Demo environment

The command is IDEMPOTENT — safe to run multiple times without creating
duplicate records (uses get_or_create throughout).

Default credentials (match PROJECT_DESCRIPTION.md):
    Admin:  admin@amalitech.com  /  password123
    User:   user@amalitech.com   /  password123

TODO (add to this command as you build features):
    • Load sample CSV datasets from tests/fixtures/
    • Create demo validation rules for each dataset
    • Seed historical check runs for the trend dashboard demo
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with default users and demo data."

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding database..."))
        self._seed_users()
        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _seed_users(self) -> None:
        """Create the default admin and regular user accounts."""

        # Admin account
        admin, created = User.objects.get_or_create(
            email="admin@amalitech.com",
            defaults={
                "username": "admin",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("password123")
            admin.save()
            self.stdout.write(f"  Created admin: {admin.email}")
        else:
            self.stdout.write(f"  Skipped admin: {admin.email} (already exists)")

        # Regular user account
        user, created = User.objects.get_or_create(
            email="user@amalitech.com",
            defaults={
                "username": "testuser",
                "role": "user",
            },
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(f"  Created user:  {user.email}")
        else:
            self.stdout.write(f"  Skipped user:  {user.email} (already exists)")
