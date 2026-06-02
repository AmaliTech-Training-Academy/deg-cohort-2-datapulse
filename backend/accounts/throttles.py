"""
accounts/throttles.py
────────────────────────────────────────────────────────────────────────────────
Custom throttle classes for sensitive auth endpoints.
Rates are configured in settings.py → REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
"""

from rest_framework.throttling import AnonRateThrottle


class ForgotPasswordThrottle(AnonRateThrottle):
    """3 requests per hour per IP for forgot-password."""

    scope = "forgot_password"


class ResendVerificationThrottle(AnonRateThrottle):
    """3 requests per hour per IP for resend-verification."""

    scope = "resend_verification"
