"""
accounts/emails.py
Plain-text transactional emails for authentication flows.

In development (DEBUG=True) emails are printed to the console.
In production set EMAIL_BACKEND + SMTP env vars in .env.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_verification_email(user, token: str) -> None:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your DataPulse email address"
    message = (
        f"Hi {user.first_name or user.email},\n\n"
        f"Click the link below to verify your email address:\n\n"
        f"  {verify_url}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you did not create a DataPulse account, you can safely ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    logger.info("Verification email sent to %s", user.email)


def send_password_reset_email(user, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={user.pk}&token={token}"
    subject = "Reset your DataPulse password"
    message = (
        f"Hi {user.first_name or user.email},\n\n"
        f"Click the link below to reset your password:\n\n"
        f"  {reset_url}\n\n"
        "This link expires in 1 hour.\n\n"
        "If you did not request a password reset, you can safely ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    logger.info("Password reset email sent to %s", user.email)
