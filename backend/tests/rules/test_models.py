"""
tests/rules/test_models.py
Tests for the ValidationRule model.
"""

import pytest
from django.db import IntegrityError

from datasets.models import Dataset
from rules.models import ValidationRule


@pytest.fixture
def dataset(db, regular_user):
    return Dataset.objects.create(
        user=regular_user,
        file_name="data.csv",
        file_type="csv",
        file_path="/tmp/data.csv",
        columns=["id", "age", "email", "score"],
    )


@pytest.mark.django_db
class TestValidationRuleModel:
    def test_create_null_check(self, dataset):
        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="email",
            rule_type="null_check",
            rule_config={},
        )
        assert rule.id is not None
        assert rule.rule_type == "null_check"

    def test_str_representation(self, dataset):
        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="age",
            rule_type="range_check",
            rule_config={"min": 0, "max": 120},
        )
        assert "range_check" in str(rule)
        assert "age" in str(rule)

    def test_rule_config_defaults_to_empty_dict(self, dataset):
        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="email",
            rule_type="null_check",
        )
        assert rule.rule_config == {}

    def test_unique_constraint_same_column_and_type(self, dataset):
        ValidationRule.objects.create(
            dataset=dataset, column_name="email", rule_type="null_check"
        )
        with pytest.raises(IntegrityError):
            ValidationRule.objects.create(
                dataset=dataset, column_name="email", rule_type="null_check"
            )

    def test_same_column_different_rule_type_allowed(self, dataset):
        ValidationRule.objects.create(
            dataset=dataset, column_name="age", rule_type="null_check"
        )
        rule2 = ValidationRule.objects.create(
            dataset=dataset,
            column_name="age",
            rule_type="range_check",
            rule_config={"min": 0, "max": 100},
        )
        assert rule2.id is not None

    def test_cascade_delete_with_dataset(self, dataset):
        ValidationRule.objects.create(
            dataset=dataset, column_name="email", rule_type="null_check"
        )
        dataset.delete()
        assert ValidationRule.objects.count() == 0

    def test_uuid_primary_key(self, dataset):
        rule = ValidationRule.objects.create(
            dataset=dataset, column_name="id", rule_type="uniqueness_check"
        )
        assert len(str(rule.id)) == 36
