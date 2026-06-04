"""
accounts/admin_urls.py
────────────────────────────────────────────────────────────────────────────────
Admin-only routes — all mounted under /api/v1/admin/ via api/urls.py.

GET  /api/v1/admin/users/    — paginated user list with dataset counts and status
GET  /api/v1/admin/datasets/ — paginated dataset list with latest report info
"""

from django.urls import path

from .views import AdminDatasetListView, AdminUserListView

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("datasets/", AdminDatasetListView.as_view(), name="admin-dataset-list"),
]
