"""
DataPulse – Django settings
────────────────────────────────────────────────────────────────────────────────
All runtime values are read from environment variables (or a .env file via
python-decouple).  See .env.example for the full list of required variables.

Pattern borrowed from Emmanuel's URL-shortener settings (shared by team):
  • python-decouple for typed env reads with fail-fast validation
  • Structured JSON logging (pythonjsonlogger) with daily rotation
  • Explicit REST_FRAMEWORK, SIMPLE_JWT, SPECTACULAR_SETTINGS blocks
  • CorsMiddleware placed before CommonMiddleware (required by django-cors-headers)
"""

from datetime import timedelta
from pathlib import Path

from decouple import Csv, UndefinedValueError, config

# ── Base directory ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Fail-fast secret key validation ──────────────────────────────────────────
# Raises a clear RuntimeError instead of a cryptic Django error when the key
# is missing.  CI environments skip this check via the CI env variable.
try:
    SECRET_KEY: str = config("SECRET_KEY")
except UndefinedValueError:
    import os

    if os.environ.get("CI") or os.environ.get("PRE_COMMIT"):
        SECRET_KEY = "ci-dummy-secret-key-not-for-production"
    else:
        raise RuntimeError(
            "SECRET_KEY is not set.  Add it to your .env file.\n"
            'Quick fix: echo SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(50))") >> .env'
        )

# ── Core Django settings ──────────────────────────────────────────────────────
DEBUG: bool = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS: list[str] = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv(),
)

# ── Application registry ──────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    # django.contrib.admin is intentionally excluded from the MVP.
    # Add it back if you need the Django admin panel.
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # enables logout / token revocation
    "drf_spectacular",
    "corsheaders",
    "debug_toolbar",  # dev only – remove in production
]

LOCAL_APPS = [
    "core",  # TimeStampedModel, health check endpoint
    "accounts",  # Custom User model + JWT auth views
    "datasets",  # CSV/JSON file upload and metadata
    "rules",  # Validation rule management (null, type, range, unique)
    "checks",  # Validation engine + quality score calculation
    "reports",  # Quality report generation and retrieval
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── IMPORTANT: must point to the custom User model BEFORE any migration ───────
AUTH_USER_MODEL = "accounts.User"

# ── Middleware ────────────────────────────────────────────────────────────────
# CorsMiddleware MUST come before CommonMiddleware (django-cors-headers docs).
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # ← before CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "core.middleware.RequestLoggingMiddleware",  # structured per-request logging
]

if DEBUG:
    # django-debug-toolbar must be after SecurityMiddleware
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")

# ── URL routing ───────────────────────────────────────────────────────────────
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ── Templates (minimal – DRF does not need template rendering) ────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# ── Database ──────────────────────────────────────────────────────────────────
# Reads individual DB_* vars (same pattern as Emmanuel's settings).
# DB_HOST should be "db" inside Docker Compose and "localhost" locally.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="datapulse"),
        "USER": config("DB_USER", default="datapulse_user"),
        "PASSWORD": config("DB_PASSWORD", default="datapulse_pass"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Static and media files ────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = config("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / config("MEDIA_ROOT", default="media")

# ── Internationalisation (minimal) ───────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Auto-schema class for drf-spectacular (OpenAPI 3)
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # JWT as the only authentication method
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Every endpoint requires authentication unless the view sets AllowAny
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Basic throttling — tighten values for production
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/minute",  # used by LoginRateThrottle in accounts app
    },
    # Pagination — all list endpoints return max 20 items per page
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Normalised error responses — implemented in core/exceptions.py
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ─────────────────────────────────────────────────────────────────────────────
# Simple JWT
# ─────────────────────────────────────────────────────────────────────────────
_JWT_ACCESS_HOURS: int = config("JWT_ACCESS_TOKEN_HOURS", default=24, cast=int)
_JWT_REFRESH_DAYS: int = config("JWT_REFRESH_TOKEN_DAYS", default=7, cast=int)

SIMPLE_JWT = {
    # Token lifetimes — read from .env so they can be changed per environment
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=_JWT_ACCESS_HOURS),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=_JWT_REFRESH_DAYS),
    # Rotate refresh tokens on every use and blacklist the old one.
    # Requires rest_framework_simplejwt.token_blacklist in INSTALLED_APPS.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Standard Bearer token header: Authorization: Bearer <token>
    "AUTH_HEADER_TYPES": ("Bearer",),
    # The response field names returned by the login view
    "ACCESS_TOKEN": "access",
    "REFRESH_TOKEN": "refresh",
}

# ─────────────────────────────────────────────────────────────────────────────
# drf-spectacular  (OpenAPI / Swagger)
# ─────────────────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "DataPulse API",
    "DESCRIPTION": (
        "Data Quality Monitoring Platform — REST API.\n\n"
        "Upload CSV/JSON datasets, define validation rules, run quality checks, "
        "generate reports, and track quality trends over time."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # hide raw schema from Swagger UI itself
    # Show a BearerAuth button in Swagger so testers can paste tokens
    "SECURITY": [{"BearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CORS  (django-cors-headers)
# ─────────────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS: list[str] = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)

# Required when the React frontend uses credentials: "include" in fetch calls
CORS_ALLOW_CREDENTIALS = True

# Forward the Authorization header — needed for JWT in browser fetch requests
CORS_EXPOSE_HEADERS = ["Authorization"]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ─────────────────────────────────────────────────────────────────────────────
# Debug Toolbar (development only)
# ─────────────────────────────────────────────────────────────────────────────
if DEBUG:
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

# ─────────────────────────────────────────────────────────────────────────────
# Structured JSON Logging
# Pattern from Emmanuel's settings: JSON in production, verbose locally,
# daily-rotating file handlers, separate error log file.
# ─────────────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")

# Detect whether python-json-logger is available (graceful fallback)
try:
    import pythonjsonlogger.jsonlogger  # noqa: F401

    _json_available = True
except ImportError:
    _json_available = False

# Ensure the logs directory exists at startup
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # ── Formatters ────────────────────────────────────────────────────────────
    "formatters": {
        # Human-readable format for local development (DEBUG=True)
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        # Structured JSON for staging/production (DEBUG=False).
        # Falls back to verbose if python-json-logger is not installed.
        "json": (
            {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            }
            if _json_available
            else {
                "format": "{asctime} [{levelname}] {name}: {message}",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        ),
    },
    # ── Handlers ──────────────────────────────────────────────────────────────
    "handlers": {
        # Console: JSON in production, verbose locally
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
        # Daily-rotating application log (7-day retention)
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "when": "midnight",
            "backupCount": 7,
            "formatter": "json" if not DEBUG else "verbose",
            "encoding": "utf-8",
        },
        # Separate error log with 30-day retention — always JSON
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "errors.log"),
            "when": "midnight",
            "backupCount": 30,
            "formatter": "json",
            "encoding": "utf-8",
            "level": "ERROR",
        },
    },
    # ── Root logger: catches everything not handled by a named logger ─────────
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
    # ── Per-app loggers ───────────────────────────────────────────────────────
    "loggers": {
        # Each DataPulse app gets its own logger so log messages are easy to
        # trace back to their source.  Import with:
        #   import logging
        #   logger = logging.getLogger(__name__)
        "accounts": {
            "handlers": ["console", "file", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "datasets": {
            "handlers": ["console", "file", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "rules": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "checks": {
            "handlers": ["console", "file", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "reports": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "core": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Django internals — only warnings and above to reduce noise
        "django.request": {
            "handlers": ["console", "file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # change to DEBUG to see all SQL queries
            "propagate": False,
        },
    },
}
