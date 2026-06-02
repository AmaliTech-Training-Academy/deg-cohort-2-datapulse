"""
tests/datasets/test_models.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for the Dataset model.

Covers
──────
  • Dataset creation with all required fields
  • UUID primary key is auto-generated
  • file_type choices enforced (csv, json)
  • __str__ returns file_title when set, file_name otherwise
  • Ordering defaults to most recent first (-created_at)
  • user FK cascade: deleting user deletes their datasets
  • columns field stores list correctly as JSONField
  • created_at and updated_at timestamps are set automatically
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="datauser",
        email="datauser@test.com",
        password="TestPass123!",
        role="user",
    )


@pytest.fixture
def dataset(user):
    from datasets.models import Dataset

    return Dataset.objects.create(
        user=user,
        file_name="sales.csv",
        file_type="csv",
        file_path="/media/uploads/1/abc123.csv",
        row_count=100,
        columns=["id", "amount", "date"],
        file_title="Sales Q1",
        description="Quarterly sales data",
    )


@pytest.mark.django_db
class TestDatasetModel:

    def test_dataset_created_successfully(self, dataset):
        assert dataset.pk is not None

    def test_uuid_primary_key_auto_generated(self, dataset):
        assert isinstance(dataset.id, uuid.UUID)

    def test_file_type_csv(self, dataset):
        assert dataset.file_type == "csv"

    def test_file_type_json(self, user):
        from datasets.models import Dataset

        d = Dataset.objects.create(
            user=user,
            file_name="data.json",
            file_type="json",
            file_path="/media/uploads/1/def456.json",
        )
        assert d.file_type == "json"

    def test_str_returns_file_title_when_set(self, dataset):
        assert "Sales Q1" in str(dataset)

    def test_str_returns_file_name_when_no_title(self, user):
        from datasets.models import Dataset

        d = Dataset.objects.create(
            user=user,
            file_name="raw.csv",
            file_type="csv",
            file_path="/media/uploads/1/raw.csv",
        )
        assert "raw.csv" in str(d)

    def test_columns_stored_as_list(self, dataset):
        assert dataset.columns == ["id", "amount", "date"]

    def test_columns_empty_by_default(self, user):
        from datasets.models import Dataset

        d = Dataset.objects.create(
            user=user,
            file_name="empty.csv",
            file_type="csv",
            file_path="/media/uploads/1/empty.csv",
        )
        assert d.columns == []

    def test_row_count_nullable(self, user):
        from datasets.models import Dataset

        d = Dataset.objects.create(
            user=user,
            file_name="pending.csv",
            file_type="csv",
            file_path="/media/uploads/1/pending.csv",
        )
        assert d.row_count is None

    def test_created_at_set_automatically(self, dataset):
        assert dataset.created_at is not None
        assert dataset.created_at <= timezone.now()

    def test_updated_at_set_automatically(self, dataset):
        assert dataset.updated_at is not None

    def test_cascade_delete_on_user_delete(self, user, dataset):
        from datasets.models import Dataset

        dataset_id = dataset.id
        user.delete()
        assert not Dataset.objects.filter(id=dataset_id).exists()

    def test_user_fk_references_auth_user_model(self, dataset, user):
        assert dataset.user == user
        assert dataset.user.email == user.email

    def test_ordering_most_recent_first(self, user):
        from datasets.models import Dataset

        d1 = Dataset.objects.create(
            user=user, file_name="a.csv", file_type="csv", file_path="/a.csv"
        )
        d2 = Dataset.objects.create(
            user=user, file_name="b.csv", file_type="csv", file_path="/b.csv"
        )
        datasets = list(Dataset.objects.filter(user=user))
        # Most recently created (d2) should come first
        assert datasets[0].id == d2.id
