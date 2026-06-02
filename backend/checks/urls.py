"""checks/urls.py — only the run-check trigger endpoint lives here."""

from django.urls import path

from .views import RunCheckView

urlpatterns = [
    path(
        "datasets/<uuid:dataset_id>/run-check/",
        RunCheckView.as_view(),
        name="run-check",
    ),
]
