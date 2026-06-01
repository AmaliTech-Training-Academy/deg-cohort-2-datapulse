"""checks/urls.py — mounted via api/urls.py"""

from django.urls import path

from .views import CheckDetailView, CheckListView, RunCheckView

urlpatterns = [
    path(
        "datasets/<uuid:dataset_id>/run-check/",
        RunCheckView.as_view(),
        name="run-check",
    ),
    path(
        "datasets/<uuid:dataset_id>/checks/",
        CheckListView.as_view(),
        name="check-list",
    ),
    path(
        "checks/<uuid:check_id>/",
        CheckDetailView.as_view(),
        name="check-detail",
    ),
]
