"""
config/test_settings.py
────────────────────────────────────────────────────────────────────────────────
Test-only settings. Inherits everything from settings.py and overrides only
what is needed for a fast, dependency-free test run.
"""

import os

# Must be set BEFORE importing settings.py so decouple reads these values
# instead of the .env file (which can have CRLF/comment parsing issues).
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from .settings import *  # noqa: E402, F401, F403

# ── Database ──────────────────────────────────────────────────────────────────
# Use SQLite in-memory so tests run without a running PostgreSQL server.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ── Email ─────────────────────────────────────────────────────────────────────
# pytest-django's mailoutbox fixture captures these automatically.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Password hashing ──────────────────────────────────────────────────────────
# MD5 hasher is intentionally weak but 100x faster than PBKDF2.
# Only used in tests — never in production.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# ── Frontend URL ──────────────────────────────────────────────────────────────
FRONTEND_URL = "http://localhost:3000"

# ── Strip dev-only apps & middleware not installed in the test environment ────
DEBUG = False
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]  # noqa: F405
