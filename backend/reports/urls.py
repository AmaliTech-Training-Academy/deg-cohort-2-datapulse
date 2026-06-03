"""reports/urls.py — mounted via api/urls.py"""

from django.urls import path

from .views import DashboardView, ReportDetailView, ReportListView, TrendView

urlpatterns = [
    # Quality Report API
    path(
        "datasets/<uuid:dataset_id>/reports/",
        ReportListView.as_view(),
        name="report-list",
    ),
    path(
        "reports/<uuid:report_id>/",
        ReportDetailView.as_view(),
        name="report-detail",
    ),
    # Trend API
    path(
        "datasets/<uuid:dataset_id>/trends/",
        TrendView.as_view(),
        name="trend-list",
    ),
    # Dashboard API
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
]
