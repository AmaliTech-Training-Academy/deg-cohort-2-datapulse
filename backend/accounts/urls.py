"""
accounts/urls.py
────────────────────────────────────────────────────────────────────────────────
Auth routes — all mounted under /api/v1/auth/ via api/urls.py.

Endpoint map:
    POST   /api/v1/auth/register/   RegisterView
    POST   /api/v1/auth/login/      LoginView
    POST   /api/v1/auth/refresh/    RefreshTokenView
    GET    /api/v1/auth/me/         MeView
"""

from django.urls import path
from .views import LoginView, MeView, RefreshTokenView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
