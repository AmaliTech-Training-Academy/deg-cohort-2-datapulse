"""
accounts/views.py
────────────────────────────────────────────────────────────────────────────────
Authentication views with full OpenAPI schema annotations so Swagger shows
all request/response bodies correctly.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models import Count, F, OuterRef, Subquery
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.emails import send_password_reset_email, send_verification_email
from accounts.permissions import IsAdminUser
from accounts.throttles import (
    ForgotPasswordThrottle,
    LoginThrottle,
    ResendVerificationThrottle,
)
from accounts.serializers import (
    AdminDatasetListSerializer,
    AdminUserListSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from datasets.models import Dataset
from reports.models import QualityReport
from .tokens import make_email_verification_token, password_reset_token_generator

User = get_user_model()

logger = logging.getLogger(__name__)

_TAG = ["Authentication"]


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=_TAG,
        summary="Register a new user account",
        request=RegisterSerializer,
        responses={
            201: UserProfileSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g. passwords don't match, email taken)"
            ),
        },
        examples=[
            OpenApiExample(
                name="Regular User",
                summary="Register a standard user account",
                description=(
                    "Creates a user with role=user. "
                    "A verification email is sent — the account cannot log in until verified."
                ),
                value={
                    "email": "alice@company.com",
                    "first_name": "Alice",
                    "last_name": "Mbeki",
                    "password": "SecurePass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Admin User",
                summary="Register an admin account",
                description=(
                    "Creates a user with role=admin. "
                    "Admin accounts have elevated permissions within the platform."
                ),
                value={
                    "email": "admin@company.com",
                    "first_name": "Bob",
                    "last_name": "Kagabo",
                    "password": "AdminPass456!",
                    "role": "admin",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            token = make_email_verification_token(user.email)
            send_verification_email(user, token)
            message = "Registration successful. Please check your email to verify your account."
        except Exception:
            logger.exception("Failed to send verification email to %s", user.email)
            message = (
                "Registration successful, but the verification email could not be sent. "
                "Use /resend-verification/ to request a new link."
            )

        logger.info("New user registered: %s", user.email)
        return Response(
            {"message": message, "user": UserProfileSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=_TAG,
        summary="Login — get JWT access and refresh tokens",
        responses={
            200: OpenApiResponse(description="JWT tokens + user profile"),
            400: OpenApiResponse(
                description="Invalid credentials or email not verified"
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=_TAG,
        summary="Refresh — exchange a refresh token for a new token pair",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=_TAG,
        summary="Me — return the current authenticated user's profile",
        responses={200: UserProfileSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(UserProfileSerializer(request.user).data)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=_TAG,
        summary="Verify email — confirm the signed token from the verification email",
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Token invalid or expired"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Email verified for user: %s", user.email)
        return Response({"message": "Email verified successfully. You can now log in."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationThrottle]

    @extend_schema(
        tags=_TAG,
        summary="Resend verification email",
        request=ResendVerificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Email sent if address is registered and unverified"
            )
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        if user is not None:
            try:
                token = make_email_verification_token(user.email)
                send_verification_email(user, token)
            except Exception:
                logger.exception(
                    "Failed to resend verification email to %s", user.email
                )
        return Response(
            {
                "message": "If that email is registered and unverified, a new verification link has been sent."
            }
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ForgotPasswordThrottle]

    @extend_schema(
        tags=_TAG,
        summary="Forgot password — send a password reset link",
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Reset email sent if address is registered"
            )
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        if user is not None:
            try:
                token = password_reset_token_generator.make_token(user)
                send_password_reset_email(user, token)
            except Exception:
                logger.exception(
                    "Failed to send password reset email to %s", user.email
                )
        return Response(
            {
                "message": "If an account with that email exists, a password reset link has been sent."
            }
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=_TAG,
        summary="Reset password — set a new password using the token from the reset email",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(
                description="Invalid/expired token or passwords don't match"
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Password reset for user: %s", user.email)
        return Response(
            {
                "message": "Password reset successful. You can now log in with your new password."
            }
        )


_ADMIN_TAG = ["Admin"]

_VALID_ORDERINGS = {
    "created_at",
    "-created_at",
    "last_login",
    "-last_login",
    "datasets_count",
    "-datasets_count",
}


class AdminUserListView(generics.ListAPIView):
    """
    GET /api/v1/admin/users/

    Returns a paginated list of all users. Admin-only.

    Query params:
      role        — filter by "admin" or "user"
      status      — filter by "active" or "suspended"
      ordering    — one of: created_at, -created_at (default), last_login,
                    -last_login, datasets_count, -datasets_count
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserListSerializer

    @extend_schema(
        tags=_ADMIN_TAG,
        summary="Admin — list all users",
        parameters=[
            OpenApiParameter("role", str, description="Filter by role: admin | user"),
            OpenApiParameter(
                "status", str, description="Filter by status: active | suspended"
            ),
            OpenApiParameter(
                "ordering",
                str,
                description=(
                    "Sort field: created_at, -created_at (default), "
                    "last_login, -last_login, datasets_count, -datasets_count"
                ),
            ),
        ],
        responses={200: AdminUserListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = User.objects.annotate(datasets_count=Count("dataset")).order_by(
            "-created_at"
        )

        role = self.request.query_params.get("role")
        if role in (User.Role.USER, User.Role.ADMIN):
            qs = qs.filter(role=role)

        status_param = self.request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(is_active=True)
        elif status_param == "suspended":
            qs = qs.filter(is_active=False)

        ordering = self.request.query_params.get("ordering")
        if ordering in _VALID_ORDERINGS:
            qs = qs.order_by(ordering)

        return qs


_DATASET_ORDERING_MAP = {
    "created_at": "created_at",
    "-created_at": "-created_at",
    # NULLs (datasets with no checks yet) always sink to the bottom
    "last_check": F("last_check").asc(nulls_last=True),
    "-last_check": F("last_check").desc(nulls_last=True),
    "reports_count": "reports_count",
    "-reports_count": "-reports_count",
}


class AdminDatasetListView(generics.ListAPIView):
    """
    GET /api/v1/admin/datasets/

    Returns a paginated list of all datasets with their latest report info.
    Admin-only.

    Query params:
      ordering  — one of: created_at, -created_at (default), last_check,
                  -last_check, reports_count, -reports_count
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminDatasetListSerializer

    @extend_schema(
        tags=_ADMIN_TAG,
        summary="Admin — list all datasets with latest report info",
        parameters=[
            OpenApiParameter(
                "ordering",
                str,
                description=(
                    "Sort field: created_at, -created_at (default), "
                    "last_check, -last_check, reports_count, -reports_count"
                ),
            ),
        ],
        responses={200: AdminDatasetListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Subquery: pick fields from the single most-recent report for each dataset
        latest_report = QualityReport.objects.filter(dataset=OuterRef("pk")).order_by(
            "-generated_at"
        )

        qs = (
            Dataset.objects.select_related("user")
            .annotate(
                reports_count=Count("reports"),
                latest_score=Subquery(latest_report.values("overall_score")[:1]),
                latest_status=Subquery(latest_report.values("status")[:1]),
                last_check=Subquery(latest_report.values("generated_at")[:1]),
            )
            .order_by("-created_at")
        )

        ordering = self.request.query_params.get("ordering")
        if ordering in _DATASET_ORDERING_MAP:
            qs = qs.order_by(_DATASET_ORDERING_MAP[ordering])

        return qs
