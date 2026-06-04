"""
accounts/admin_urls.py
────────────────────────────────────────────────────────────────────────────────
Admin-only routes — all mounted under /api/v1/admin/ via api/urls.py.

GET  /api/v1/admin/users/   — paginated user list with dataset counts and status
"""

from django.urls import path

from .views import AdminUserListView

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
]
