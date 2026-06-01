"""
rules/exceptions.py
────────────────────────────────────────────────────────────────────────────────
TODO: define rules-specific exceptions here.

Custom exceptions let you raise domain-level errors and have them
translated into appropriate HTTP responses by core.exceptions.custom_exception_handler.

Example:
    from rest_framework.exceptions import APIException
    from rest_framework import status

    class DatasetNotReadyError(APIException):
        status_code = status.HTTP_409_CONFLICT
        default_code = "dataset_not_ready"
        default_detail = "Dataset is not ready for validation."
"""

# Placeholder — no custom exceptions yet.
