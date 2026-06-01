"""
core/views.py
────────────────────────────────────────────────────────────────────────────────
Health check endpoint.

GET /health/
    Returns 200 if the database is reachable.
    Returns 503 if the database connection fails.

This is intentionally unauthenticated (AllowAny) so Docker health checks,
load balancers, and CI pipelines can call it without a JWT token.

Response shape:
    {"status": "ok",    "db": "reachable"}   →  HTTP 200
    {"status": "error", "db": "unreachable"} →  HTTP 503
"""

import logging

from django.db import OperationalError, connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Unauthenticated liveness probe.

    Checks PostgreSQL connectivity by issuing a lightweight
    connection.ensure_connection() call.  No data is read or written.
    """

    permission_classes = [AllowAny]
    # Exclude from drf-spectacular schema (internal endpoint)
    schema = None

    def get(self, request: Request) -> Response:
        try:
            connection.ensure_connection()
            db_status = "reachable"
            http_status = status.HTTP_200_OK
            logger.debug("Health check passed — database reachable.")
        except OperationalError as exc:
            db_status = "unreachable"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            logger.error("Health check failed — database unreachable: %s", exc)

        return Response(
            {"status": "ok" if db_status == "reachable" else "error", "db": db_status},
            status=http_status,
        )
