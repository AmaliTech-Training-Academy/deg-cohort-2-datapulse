"""
accounts/urls.py
────────────────────────────────────────────────────────────────────────────────
Auth routes — all mounted under /api/v1/auth/ via api/urls.py.

POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/refresh/
GET    /api/v1/auth/me/
POST   /api/v1/auth/verify-email/
POST   /api/v1/auth/resend-verification/
POST   /api/v1/auth/forgot-password/
POST   /api/v1/auth/reset-password/
"""

from django.urls import path

from .views import (
    ForgotPasswordView,
    LoginView,
    MeView,
    RefreshTokenView,
    RegisterView,
    ResendVerificationView,
    ResetPasswordView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="auth-resend-verification"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
]
