"""datasets/urls.py — mounted at /api/v1/datasets/ via api/urls.py"""

from django.urls import path

from .views import (
    DatasetDetailView,
    DatasetFileUpdateView,
    DatasetListView,
    DatasetUploadView,
)

urlpatterns = [
    path("", DatasetListView.as_view(), name="dataset-list"),
    path("upload/", DatasetUploadView.as_view(), name="dataset-upload"),
    path("<uuid:dataset_id>/", DatasetDetailView.as_view(), name="dataset-detail"),
    path(
        "<uuid:dataset_id>/file/",
        DatasetFileUpdateView.as_view(),
        name="dataset-file-update",
    ),
]
