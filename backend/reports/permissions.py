"""
reports/permissions.py
────────────────────────────────────────────────────────────────────────────────
TODO: define any reports-specific permission classes here.

Most views will use the global IsAuthenticated default from settings.py.
Add custom permission classes here only when you need object-level checks
(e.g. verifying the requesting user owns the object).

Example:
    from rest_framework.permissions import BasePermission, SAFE_METHODS

    class IsOwner(BasePermission):
        message = "You do not have permission to access this resource."

        def has_object_permission(self, request, view, obj) -> bool:
            return obj.uploaded_by == request.user
"""

# Placeholder — no custom permissions yet.
