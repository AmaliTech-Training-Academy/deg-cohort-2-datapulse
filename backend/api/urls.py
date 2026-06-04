"""
api/urls.py — /api/v1/ route registry
────────────────────────────────────────────────────────────────────────────────
All routes are versioned under /api/v1/.

Endpoint map:
  POST   /api/v1/auth/register/
  POST   /api/v1/auth/login/
  POST   /api/v1/auth/refresh/
  GET    /api/v1/auth/me/

  GET    /api/v1/datasets/
  POST   /api/v1/datasets/upload/
  GET    /api/v1/datasets/<id>/
  PATCH  /api/v1/datasets/<id>/
  DELETE /api/v1/datasets/<id>/
  PATCH  /api/v1/datasets/<id>/file/

  GET    /api/v1/datasets/<id>/rules/
  POST   /api/v1/datasets/<id>/rules/
  POST   /api/v1/datasets/<id>/rules/batch/
  GET    /api/v1/rules/<id>/
  PATCH  /api/v1/rules/<id>/
  DELETE /api/v1/rules/<id>/

  POST   /api/v1/datasets/<id>/run-check/

  GET    /api/v1/datasets/<id>/reports/
  GET    /api/v1/reports/<id>/
  GET    /api/v1/datasets/<id>/trends/
  GET    /api/v1/dashboard/

  GET    /api/v1/admin/users/
  GET    /api/v1/admin/datasets/
"""

from django.urls import include, path

from checks.urls import urlpatterns as check_urls
from rules.urls import urlpatterns as rule_urls

urlpatterns = [
    path("auth/", include("accounts.urls")),
    path("admin/", include("accounts.admin_urls")),
    path("datasets/", include("datasets.urls")),
    # Rules and checks use nested dataset URLs — include directly
    path("", include(rule_urls)),
    path("", include(check_urls)),
    # Reports, trends, and dashboard
    path("", include("reports.urls")),
]
