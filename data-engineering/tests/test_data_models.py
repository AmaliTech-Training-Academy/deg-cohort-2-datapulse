# data-engineering/tests/test_data_models.py
#
# DE1 code — data_models.py
# Tests that SQLAlchemy models are correctly defined.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))

from data_models import (
    AnalyticsBase,
    DimDataset,
    DimRule,
    DimDate,
    FactQualityCheck,
    FactTrendMetric,
)


# ── Model existence tests ─────────────────────────────────────────────────────

def test_dim_dataset_model_exists():
    assert DimDataset is not None

def test_dim_rule_model_exists():
    assert DimRule is not None

def test_dim_date_model_exists():
    assert DimDate is not None

def test_fact_quality_check_model_exists():
    assert FactQualityCheck is not None

def test_fact_trend_metric_model_exists():
    assert FactTrendMetric is not None


# ── Table name tests ──────────────────────────────────────────────────────────

def test_dim_dataset_table_name():
    assert DimDataset.__tablename__ == "dim_datasets"

def test_dim_rule_table_name():
    assert DimRule.__tablename__ == "dim_rules"

def test_dim_date_table_name():
    assert DimDate.__tablename__ == "dim_date"

def test_fact_quality_check_table_name():
    assert FactQualityCheck.__tablename__ == "fact_quality_checks"

def test_fact_trend_metric_table_name():
    assert FactTrendMetric.__tablename__ == "fact_trend_metrics"


# ── Column tests ──────────────────────────────────────────────────────────────

def test_dim_dataset_has_required_columns():
    columns = [c.name for c in DimDataset.__table__.columns]
    for col in ["id", "source_id", "name", "file_type", "row_count", "uploaded_at"]:
        assert col in columns, f"Column '{col}' missing from dim_datasets"

def test_dim_rule_has_required_columns():
    columns = [c.name for c in DimRule.__table__.columns]
    for col in ["id", "source_id", "name", "field_name", "rule_type", "severity"]:
        assert col in columns, f"Column '{col}' missing from dim_rules"

def test_dim_date_has_required_columns():
    columns = [c.name for c in DimDate.__table__.columns]
    for col in ["date_key", "full_date", "day_of_week", "month", "year"]:
        assert col in columns, f"Column '{col}' missing from dim_date"

def test_fact_quality_check_has_required_columns():
    columns = [c.name for c in FactQualityCheck.__table__.columns]
    for col in ["id", "dataset_id", "rule_id", "rule_type", "passed",
                "failed_rows", "total_rows", "score", "severity", "checked_at"]:
        assert col in columns, f"Column '{col}' missing from fact_quality_checks"

def test_fact_trend_metric_has_required_columns():
    columns = [c.name for c in FactTrendMetric.__table__.columns]
    for col in ["id", "dataset_id", "source_id", "snapshot_date", "aggregated_score"]:
        assert col in columns, f"Column '{col}' missing from fact_trend_metrics"


# ── Foreign key tests ─────────────────────────────────────────────────────────

def test_fact_quality_check_has_dataset_fk():
    fks = [fk.target_fullname for fk in FactQualityCheck.__table__.foreign_keys]
    assert any("dim_datasets" in fk for fk in fks)

def test_fact_quality_check_has_rule_fk():
    fks = [fk.target_fullname for fk in FactQualityCheck.__table__.foreign_keys]
    assert any("dim_rules" in fk for fk in fks)

def test_fact_trend_metric_has_dataset_fk():
    fks = [fk.target_fullname for fk in FactTrendMetric.__table__.foreign_keys]
    assert any("dim_datasets" in fk for fk in fks)


# ── Analytics base test ───────────────────────────────────────────────────────

def test_all_models_share_same_base():
    """All models should use the same declarative base."""
    assert DimDataset.metadata is AnalyticsBase.metadata
    assert DimRule.metadata is AnalyticsBase.metadata
    assert FactQualityCheck.metadata is AnalyticsBase.metadata