"""
accounts/views.py
────────────────────────────────────────────────────────────────────────────────
Authentication views.

RegisterView       POST /api/v1/auth/register/   — create account
LoginView          POST /api/v1/auth/login/       — get JWT tokens
TokenRefreshView   POST /api/v1/auth/refresh/     — rotate tokens
MeView             GET  /api/v1/auth/me/           — current user profile

All views except MeView use AllowAny (no token required).
MeView requires a valid Bearer token.

TODO (implement during your sprint):
    • RegisterView.post()  — call RegisterSerializer, return 201
    • LoginView.post()     — call CustomTokenObtainPairSerializer, return tokens + user
    • MeView.get()         — return UserProfileSerializer(request.user).data
"""

import logging

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Create a new user account.

    Request body:
        {
            "email":      "user@example.com",
            "password":   "securepassword",
            "password2":  "securepassword",
            "first_name": "Ada",
            "last_name":  "Lovelace"
        }

    Response 201:
        { "id": 1, "email": "user@example.com", "role": "user" }

    TODO: implement the post() method.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        raise NotImplementedError(
            "RegisterView.post() is not implemented yet.\n"
            "Steps:\n"
            "  1. Validate request.data with RegisterSerializer\n"
            "  2. Call serializer.save() to create the user\n"
            "  3. Return Response(data, status=201)"
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Authenticate with email + password, receive JWT access and refresh tokens.

    Response 200:
        {
            "access":  "<jwt-access-token>",
            "refresh": "<jwt-refresh-token>",
            "user":    { "id": 1, "email": "...", "role": "user" }
        }

    Extends SimpleJWT's TokenObtainPairView.
    To embed user data in the response, create a CustomTokenObtainPairSerializer
    that overrides validate() and adds the user fields.

    TODO: create CustomTokenObtainPairSerializer in serializers.py and
          set serializer_class = CustomTokenObtainPairSerializer here.
    """

    permission_classes = [AllowAny]
    # TODO: set serializer_class = CustomTokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/
    Exchange a valid refresh token for a new access + refresh token pair.

    With ROTATE_REFRESH_TOKENS=True, the old refresh token is blacklisted
    after every successful refresh call.

    No implementation needed — inherits all behaviour from SimpleJWT.
    """

    permission_classes = [AllowAny]


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    Return the profile of the currently authenticated user.

    Used by the React frontend on app load to verify the stored token is
    still valid and to re-hydrate the user context.

    Response 200:
        { "id": 1, "email": "...", "first_name": "Ada", "role": "user" }

    TODO: implement the get() method.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        raise NotImplementedError(
            "MeView.get() is not implemented yet.\n"
            "Steps:\n"
            "  1. Serialize request.user with UserProfileSerializer\n"
            "  2. Return Response(serializer.data)"
        )
