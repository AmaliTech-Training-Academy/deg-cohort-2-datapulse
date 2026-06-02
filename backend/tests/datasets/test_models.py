"""
tests/datasets/test_models.py
Tests for the Dataset model.
"""

import pytest
from datasets.models import Dataset


@pytest.mark.django_db
class TestDatasetModel:
    def test_str_uses_file_title(self, regular_user):
        d = Dataset.objects.create(
            user=regular_user,
            file_name="data.csv",
            file_type="csv",
            file_path="/tmp/data.csv",
            file_title="My Dataset",
        )
        assert str(d) == "My Dataset (csv)"

    def test_str_falls_back_to_file_name(self, regular_user):
        d = Dataset.objects.create(
            user=regular_user,
            file_name="data.csv",
            file_type="csv",
            file_path="/tmp/data.csv",
            file_title="",
        )
        assert str(d) == "data.csv (csv)"

    def test_columns_defaults_to_empty_list(self, regular_user):
        d = Dataset.objects.create(
            user=regular_user,
            file_name="data.csv",
            file_type="csv",
            file_path="/tmp/data.csv",
        )
        assert d.columns == []

    def test_uuid_primary_key(self, regular_user):
        d = Dataset.objects.create(
            user=regular_user,
            file_name="data.csv",
            file_type="csv",
            file_path="/tmp/data.csv",
        )
        assert d.id is not None
        assert len(str(d.id)) == 36  # UUID format

    def test_ordering_most_recent_first(self, regular_user):
        d1 = Dataset.objects.create(
            user=regular_user, file_name="a.csv", file_type="csv", file_path="/a"
        )
        d2 = Dataset.objects.create(
            user=regular_user, file_name="b.csv", file_type="csv", file_path="/b"
        )
        qs = Dataset.objects.filter(user=regular_user)
        assert qs[0].id == d2.id
        assert qs[1].id == d1.id

    def test_cascade_delete_with_user(self, regular_user):
        Dataset.objects.create(
            user=regular_user, file_name="d.csv", file_type="csv", file_path="/d"
        )
        regular_user.delete()
        assert Dataset.objects.count() == 0
