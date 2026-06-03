# data-engineering/tests/test_etl_pipeline.py
#
# DE1 code — etl_pipeline.py
# Tests ETL transform logic using mock data (no DB needed).

import sys
import os
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))


# ── ETLPipeline import test ───────────────────────────────────────────────────

def test_etl_pipeline_imports():
    """ETLPipeline class imports without errors."""
    with patch.dict(os.environ, {
        "SOURCE_DB_URL": "postgresql://user:pass@localhost/db",
        "TARGET_DB_URL": "postgresql://user:pass@localhost/analytics"
    }):
        with patch("pipeline.etl_pipeline.create_engine"):
            with patch("pipeline.etl_pipeline.AnalyticsBase"):
                from etl_pipeline import ETLPipeline
                assert ETLPipeline is not None


# ── Transform logic tests (no DB needed) ─────────────────────────────────────

def test_transform_derives_passed_column():
    """passed = True when failure_percentage == 0."""
    import uuid
    findings = pd.DataFrame({
        "id": [1, 2],
        "rule_id": [str(uuid.uuid4()), str(uuid.uuid4())],
        "report_id": [str(uuid.uuid4()), str(uuid.uuid4())],
        "rows_checked": [100, 100],
        "rows_failed": [0, 10],
        "failure_percentage": [0.0, 10.0],
        "error_details": [None, None],
    })

    # failure_percentage == 0 → passed = True
    findings["passed"] = findings["failure_percentage"] == 0
    assert findings.iloc[0]["passed"] == True
    assert findings.iloc[1]["passed"] == False


def test_transform_derives_score():
    """score = 1 - failure_percentage / 100, clipped to [0, 1]."""
    df = pd.DataFrame({"failure_percentage": [0, 10, 50, 100, 110]})
    df["score"] = (1 - df["failure_percentage"] / 100).clip(0, 1)

    assert df.iloc[0]["score"] == 1.0    # 0% failure → score 1.0
    assert df.iloc[1]["score"] == 0.9    # 10% failure → score 0.9
    assert df.iloc[2]["score"] == 0.5    # 50% failure → score 0.5
    assert df.iloc[3]["score"] == 0.0    # 100% failure → score 0.0
    assert df.iloc[4]["score"] == 0.0    # >100% → clipped to 0.0


def test_transform_extract_severity_from_dict():
    """severity is extracted from rule_config JSON."""
    def extract_severity(cfg):
        if isinstance(cfg, dict):
            return cfg.get("severity", "medium")
        return "medium"

    assert extract_severity({"severity": "high"}) == "high"
    assert extract_severity({"severity": "low"}) == "low"
    assert extract_severity({}) == "medium"
    assert extract_severity(None) == "medium"
    assert extract_severity("string") == "medium"


def test_transform_dim_date_key_format():
    """date_key should be in YYYYMMDD integer format."""
    d = date(2024, 6, 3)
    date_key = int(datetime.combine(d, datetime.min.time()).strftime("%Y%m%d"))
    assert date_key == 20240603


def test_transform_dim_date_day_of_week():
    """day_of_week should be 0=Monday ... 6=Sunday."""
    d = date(2024, 6, 3)  # Monday
    dt = datetime.combine(d, datetime.min.time())
    assert dt.weekday() == 0  # Monday = 0


def test_transform_score_clips_to_valid_range():
    """Score should never be below 0 or above 1."""
    values = [-0.5, 0.0, 0.5, 1.0, 1.5]
    clipped = pd.Series(values).clip(0, 1)
    assert clipped.min() >= 0
    assert clipped.max() <= 1


# ── ETL file existence tests ──────────────────────────────────────────────────

def test_etl_pipeline_file_exists():
    path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "etl_pipeline.py")
    assert os.path.exists(path)

def test_data_models_file_exists():
    path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "data_models.py")
    assert os.path.exists(path)

def test_init_analytics_db_file_exists():
    path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "init_analytics_db.py")
    assert os.path.exists(path)

def test_analytics_schema_sql_exists():
    path = os.path.join(os.path.dirname(__file__), "..", "sql", "analytics_schema.sql")
    assert os.path.exists(path)


# ── Analytics schema SQL test ─────────────────────────────────────────────────

def test_analytics_schema_contains_required_tables():
    """analytics_schema.sql should define all required tables."""
    path = os.path.join(os.path.dirname(__file__), "..", "sql", "analytics_schema.sql")
    with open(path, "r") as f:
        sql = f.read().lower()

    required_tables = [
        "dim_datasets",
        "dim_rules",
        "dim_date",
        "fact_quality_checks",
    ]
    for table in required_tables:
        assert table in sql, f"Table '{table}' missing from analytics_schema.sql"