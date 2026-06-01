"""
DataPulse – /api/v1/ route registry
────────────────────────────────────────────────────────────────────────────────
All application routes are versioned under /api/v1/.
Each app owns its own urls.py; this file only wires them together.

Route prefixes:
  auth/        → accounts app  (register, login, refresh, me)
  datasets/    → datasets app  (upload, list, detail, delete)
  rules/       → rules app     (CRUD validation rules per dataset)
  checks/      → checks app    (run check, poll status)
  reports/     → reports app   (fetch quality reports, trend, dashboard)
"""

from django.urls import include, path

urlpatterns = [
    path("auth/",     include("accounts.urls")),
    path("datasets/", include("datasets.urls")),
    path("rules/",    include("rules.urls")),
    path("checks/",   include("checks.urls")),
    path("reports/",  include("reports.urls")),
]
