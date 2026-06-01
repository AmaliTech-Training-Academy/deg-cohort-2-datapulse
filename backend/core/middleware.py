"""
core/middleware.py
────────────────────────────────────────────────────────────────────────────────
RequestLoggingMiddleware
    Logs every incoming HTTP request and its response status code using the
    structured logger.  Produces one log line per request so the team can
    trace issues in the logs without adding print() statements.

Log format (JSON in production, verbose locally):
    INFO  core.middleware  POST /api/v1/datasets/ → 201  (42ms)
    INFO  core.middleware  GET  /health/           → 200  (3ms)
    WARN  core.middleware  POST /api/v1/auth/login/ → 401  (8ms)

Wire this up in settings.py MIDDLEWARE list (after SecurityMiddleware):
    "core.middleware.RequestLoggingMiddleware",
"""

import logging
import time

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Lightweight request/response logger.

    Does NOT log request bodies (to avoid leaking passwords or file contents).
    Only logs method, path, status code, and duration.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000)
        level = logging.WARNING if response.status_code >= 400 else logging.INFO

        logger.log(
            level,
            "%s %s → %s  (%dms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )

        return response
