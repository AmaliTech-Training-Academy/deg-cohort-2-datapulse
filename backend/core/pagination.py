"""
core/pagination.py
────────────────────────────────────────────────────────────────────────────────
Shared pagination class used by all DataPulse list endpoints.

Response shape:
    {
        "count":    <total items across all pages>,
        "next":     <URL of next page | null>,
        "previous": <URL of previous page | null>,
        "results":  [...]
    }

Query parameters:
    ?page=<n>       — page number (1-based, default 1)
    ?page_size=<n>  — items per page (default 20, max 100)

Usage in a view:
    paginator = DataPulsePagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_class(page, many=True).data)
"""

from rest_framework.pagination import PageNumberPagination


class DataPulsePagination(PageNumberPagination):
    """
    Standard pagination for all DataPulse list endpoints.

    Clients can override the page size up to PAGE_SIZE_MAX via ?page_size=N.
    Exceeding the max silently clamps to PAGE_SIZE_MAX — never raises an error.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
