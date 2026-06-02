"""datasets/urls.py — mounted at /api/v1/datasets/ via api/urls.py"""

from django.urls import path

from .views import DatasetDetailView, DatasetListView, DatasetUploadView

urlpatterns = [
    path("", DatasetListView.as_view(), name="dataset-list"),
    path("upload/", DatasetUploadView.as_view(), name="dataset-upload"),
    path("<uuid:dataset_id>/", DatasetDetailView.as_view(), name="dataset-detail"),
]
