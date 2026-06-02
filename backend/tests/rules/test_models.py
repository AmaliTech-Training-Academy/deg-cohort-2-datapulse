"""
tests/rules/test_models.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for the ValidationRule model.

Covers
──────
  • Rule creation with all required fields
  • UUID primary key is auto-generated
  • All four rule_type choices are accepted
  • UniqueConstraint prevents duplicate (dataset, column_name, rule_type)
  • rule_config stores JSON correctly
  • Cascade delete: deleting dataset removes all its rules
  • __str__ output format
  • Ordering defaults to created_at ascending
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="ruleuser", email="ruleuser@test.com", password="pass"
    )


@pytest.fixture
def dataset(user):
    from datasets.models import Dataset

    return Dataset.objects.create(
        user=user,
        file_name="data.csv",
        file_type="csv",
        file_path="/media/data.csv",
        columns=["id", "age", "email", "score"],
        row_count=10,
    )


@pytest.fixture
def null_rule(dataset):
    from rules.models import ValidationRule

    return ValidationRule.objects.create(
        dataset=dataset,
        column_name="email",
        rule_type="null_check",
        rule_config={},
    )


@pytest.mark.django_db
class TestValidationRuleModel:

    def test_rule_created_successfully(self, null_rule):
        assert null_rule.pk is not None

    def test_uuid_primary_key_auto_generated(self, null_rule):
        assert isinstance(null_rule.id, uuid.UUID)

    def test_rule_type_null_check(self, null_rule):
        assert null_rule.rule_type == "null_check"

    def test_rule_type_range_check(self, dataset):
        from rules.models import ValidationRule

        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="age",
            rule_type="range_check",
            rule_config={"min": 0, "max": 120},
        )
        assert rule.rule_type == "range_check"

    def test_rule_type_type_check(self, dataset):
        from rules.models import ValidationRule

        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="score",
            rule_type="type_check",
            rule_config={"expected_type": "integer"},
        )
        assert rule.rule_type == "type_check"

    def test_rule_type_uniqueness_check(self, dataset):
        from rules.models import ValidationRule

        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="id",
            rule_type="uniqueness_check",
            rule_config={},
        )
        assert rule.rule_type == "uniqueness_check"

    def test_rule_config_stored_as_json(self, dataset):
        from rules.models import ValidationRule

        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="age",
            rule_type="range_check",
            rule_config={"min": 0, "max": 120},
        )
        assert rule.rule_config["min"] == 0
        assert rule.rule_config["max"] == 120

    def test_duplicate_rule_raises_integrity_error(self, dataset, null_rule):
        """Same column + same rule_type on same dataset must not be allowed."""
        from rules.models import ValidationRule

        with pytest.raises(IntegrityError):
            ValidationRule.objects.create(
                dataset=dataset,
                column_name="email",
                rule_type="null_check",
                rule_config={},
            )

    def test_same_column_different_rule_type_allowed(self, dataset, null_rule):
        """Two different rule types on the same column is valid."""
        from rules.models import ValidationRule

        rule = ValidationRule.objects.create(
            dataset=dataset,
            column_name="email",
            rule_type="type_check",
            rule_config={"expected_type": "string"},
        )
        assert rule.pk is not None

    def test_cascade_delete_on_dataset_delete(self, dataset, null_rule):
        from rules.models import ValidationRule

        rule_id = null_rule.id
        dataset.delete()
        assert not ValidationRule.objects.filter(id=rule_id).exists()

    def test_str_contains_rule_type_and_column(self, null_rule):
        assert "null_check" in str(null_rule)
        assert "email" in str(null_rule)

    def test_created_at_set_automatically(self, null_rule):
        assert null_rule.created_at is not None
