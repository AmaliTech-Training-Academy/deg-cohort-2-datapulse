# data-engineering/tests/test_dashboard.py
#
# DE2 (Odile) owns this file.
# Tests that the dashboard imports and loads correctly.

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))


def test_analytics_module_imports():
    """analytics.py imports without errors."""
    import analytics
    assert hasattr(analytics, "score_summary")
    assert hasattr(analytics, "rule_failure_rates")
    assert hasattr(analytics, "quality_trend")
    assert hasattr(analytics, "worst_datasets")
    assert hasattr(analytics, "monthly_summary")


def test_score_summary_callable():
    from analytics import score_summary
    assert callable(score_summary)


def test_rule_failure_rates_callable():
    from analytics import rule_failure_rates
    assert callable(rule_failure_rates)


def test_quality_trend_callable():
    from analytics import quality_trend
    assert callable(quality_trend)


def test_worst_datasets_callable():
    from analytics import worst_datasets
    assert callable(worst_datasets)


def test_monthly_summary_callable():
    from analytics import monthly_summary
    assert callable(monthly_summary)


def test_dashboard_file_exists():
    """Dashboard file exists in the correct location."""
    dashboard_path = os.path.join(
        os.path.dirname(__file__), "..", "dashboards", "quality_dashboard.py"
    )
    assert os.path.exists(dashboard_path), "quality_dashboard.py not found"


def test_sample_data_directory_exists():
    """Sample data directory exists."""
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
    assert os.path.isdir(sample_dir)


def test_analytics_queries_sql_exists():
    """SQL analytics queries file exists."""
    sql_path = os.path.join(
        os.path.dirname(__file__), "..", "sql", "analytics_queries.sql"
    )
    assert os.path.exists(sql_path)