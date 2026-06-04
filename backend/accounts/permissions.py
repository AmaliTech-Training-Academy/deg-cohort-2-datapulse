"""
accounts/permissions.py
────────────────────────────────────────────────────────────────────────────────
Custom DRF permission classes for the accounts app.

IsAdminUser
    Grants access only to users with role="admin".
    Used to protect admin-only endpoints such as GET /api/v1/admin/users/.

Usage:
    from accounts.permissions import IsAdminUser

    class AdminUserListView(APIView):
        permission_classes = [IsAuthenticated, IsAdminUser]

TODO (implement during your sprint):
    • Implement has_permission() to check request.user.role == "admin"
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminUser(BasePermission):
    """
    Allows access only to users with role='admin'.
    Returns HTTP 403 for all other authenticated users.
    """

    message = "Admin access required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)
