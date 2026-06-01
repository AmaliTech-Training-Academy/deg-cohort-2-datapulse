"""
DataPulse – Root URL configuration
────────────────────────────────────────────────────────────────────────────────
Route map:
  /api/v1/     → api/urls.py            (all versioned API routes)
  /health/     → core health-check view
  /api/docs/   → Swagger UI
  /api/schema/ → raw OpenAPI JSON schema

Media files are served by Django in development (DEBUG=True).
In production, delegate /media/ to nginx or object storage.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # ── Versioned API ─────────────────────────────────────────────────────────
    path("api/v1/", include("api.urls")),
    # ── Health check (unauthenticated) ────────────────────────────────────────
    path("health/", include("core.urls")),
    # ── OpenAPI schema + Swagger UI ───────────────────────────────────────────
    # /api/schema/ → raw JSON schema (used by codegen tools)
    # /api/docs/   → interactive Swagger UI for manual testing
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# ── Media file serving in development ────────────────────────────────────────
# Django only serves /media/ when DEBUG=True.
# Replace with nginx or a CDN in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Debug toolbar (development only) ─────────────────────────────────────────
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
