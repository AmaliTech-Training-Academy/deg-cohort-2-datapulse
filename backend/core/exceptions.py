"""
core/exceptions.py
────────────────────────────────────────────────────────────────────────────────
Custom DRF exception handler.

Normalises all error responses to a single predictable shape so the React
frontend never has to handle multiple error formats.

Standard DRF produces at least three different shapes:
    {"detail": "Not found."}                        (404/403)
    {"email": ["This field is required."]}          (validation)
    {"non_field_errors": ["Passwords don't match"]} (non-field)

After this handler, every error looks like:
    {
        "error": {
            "code":    "NOT_FOUND",
            "message": "No dataset with id=99 found.",
            "fields":  {}
        }
    }

Wire this up in settings.py:
    REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    }
"""

import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

# Maps HTTP status codes to short machine-readable codes used by the frontend
_STATUS_CODES: dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    429: "RATE_LIMITED",
    500: "SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Wraps DRF's default exception handler output in a consistent error envelope.

    Returns None for non-DRF exceptions (Django will return a 500 page).
    Returns a normalised Response for all DRF exceptions.
    """
    # Let DRF handle the exception first so we get a Response object
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — Django's 500 handler takes over
        logger.exception("Unhandled exception in view %s", context.get("view"))
        return None

    # Extract a human-readable message from whatever shape DRF returned
    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = str(response.data["detail"])
        else:
            # Validation errors: pick the first field's first message
            first_key = next(iter(response.data))
            first_val = response.data[first_key]
            if isinstance(first_val, list):
                message = f"{first_key}: {first_val[0]}"
            else:
                message = f"{first_key}: {first_val}"
    else:
        message = str(response.data)

    code = _STATUS_CODES.get(response.status_code, "ERROR")

    # Overwrite the response data with the normalised shape
    response.data = {
        "error": {
            "code": code,
            "message": message,
            # Keep the original field-level errors for form validation on the frontend
            "fields": response.data if isinstance(response.data, dict) else {},
        }
    }

    logger.warning(
        "API error %s: %s (status=%s)",
        code,
        message,
        response.status_code,
    )

    return response
