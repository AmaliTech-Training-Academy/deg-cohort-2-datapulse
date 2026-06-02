"""
accounts/tokens.py
Stateless token helpers for email verification and password reset.
"""

import logging

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.signing import BadSignature, SignatureExpired, dumps, loads

logger = logging.getLogger(__name__)

_EMAIL_VERIFY_SALT = "datapulse-email-verify"
_EMAIL_VERIFY_MAX_AGE = 86400  # 24 hours in seconds


def make_email_verification_token(email: str) -> str:
    return dumps(email, salt=_EMAIL_VERIFY_SALT)


def decode_email_verification_token(token: str) -> str | None:
    """Returns the email address, or None if the token is invalid or expired."""
    try:
        return loads(token, salt=_EMAIL_VERIFY_SALT, max_age=_EMAIL_VERIFY_MAX_AGE)
    except SignatureExpired:
        logger.info("Email verification token expired")
        return None
    except BadSignature:
        logger.warning("Invalid email verification token received")
        return None


class _PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Including the password hash ensures the token is single-use:
        # it becomes invalid as soon as the password is changed.
        return f"{user.pk}{timestamp}{user.password}{user.is_email_verified}"


password_reset_token_generator = _PasswordResetTokenGenerator()
