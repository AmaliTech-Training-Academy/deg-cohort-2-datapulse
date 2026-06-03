# data-engineering/tests/test_sample_data.py
#
# DE2 (Odile) owns this file.
# Tests that sample datasets are correct and hit target quality scores.

import os
import pytest
import pandas as pd

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")

REQUIRED_COLUMNS = ["id", "name", "email", "age", "department", "salary", "hire_date"]


def score_csv(path: str) -> int:
    """Score a CSV file using the union formula matching backend."""
    df = pd.read_csv(path)
    total = len(df)
    if total == 0:
        return 0

    failed_union = set()

    rules = {
        "not_null_name":    df[df["name"].isnull() | (df["name"].astype(str).str.strip() == "")].index,
        "not_null_email":   df[df["email"].isnull() | (df["email"].astype(str).str.strip() == "")].index,
        "not_null_dept":    df[df["department"].isnull() | (df["department"].astype(str).str.strip() == "")].index,
        "age_range":        df[~pd.to_numeric(df["age"], errors="coerce").between(18, 65)].index,
        "salary_positive":  df[~pd.to_numeric(df["salary"], errors="coerce").gt(0)].index,
        "hire_date_valid":  df[pd.to_datetime(df["hire_date"], errors="coerce").isnull()].index,
    }

    for _, failed_index in rules.items():
        failed_union.update(failed_index)

    return max(0, min(100, round((total - len(failed_union)) / total * 100)))


# File existence tests 

def test_clean_data_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "clean_data.csv"))

def test_messy_data_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "messy_data.csv"))

def test_mixed_data_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "mixed_data.csv"))

def test_large_clean_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "large_clean_data.csv"))

def test_large_messy_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "large_messy_data.csv"))

def test_large_mixed_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "large_mixed_data.csv"))

def test_generator_exists():
    assert os.path.exists(os.path.join(SAMPLE_DIR, "generate_samples.py"))


# Column structure tests

@pytest.mark.parametrize("filename", [
    "clean_data.csv", "messy_data.csv", "mixed_data.csv",
    "large_clean_data.csv", "large_messy_data.csv", "large_mixed_data.csv"
])
def test_required_columns_present(filename):
    df = pd.read_csv(os.path.join(SAMPLE_DIR, filename))
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Column '{col}' missing from {filename}"


# Row count tests

@pytest.mark.parametrize("filename", [
    "clean_data.csv", "messy_data.csv", "mixed_data.csv"
])
def test_small_datasets_have_100_rows(filename):
    df = pd.read_csv(os.path.join(SAMPLE_DIR, filename))
    assert len(df) == 100, f"{filename} should have 100 rows, got {len(df)}"

@pytest.mark.parametrize("filename", [
    "large_clean_data.csv", "large_messy_data.csv", "large_mixed_data.csv"
])
def test_large_datasets_have_500_rows(filename):
    df = pd.read_csv(os.path.join(SAMPLE_DIR, filename))
    assert len(df) == 500, f"{filename} should have 500 rows, got {len(df)}"


# Quality score tests 

def test_clean_data_score_above_90():
    score = score_csv(os.path.join(SAMPLE_DIR, "clean_data.csv"))
    assert score >= 90, f"clean_data score should be ~95, got {score}"

def test_messy_data_score_below_60():
    score = score_csv(os.path.join(SAMPLE_DIR, "messy_data.csv"))
    assert score <= 60, f"messy_data score should be ~40, got {score}"

def test_mixed_data_score_between_50_and_85():
    score = score_csv(os.path.join(SAMPLE_DIR, "mixed_data.csv"))
    assert 50 <= score <= 85, f"mixed_data score should be ~70, got {score}"

def test_large_clean_score_above_90():
    score = score_csv(os.path.join(SAMPLE_DIR, "large_clean_data.csv"))
    assert score >= 90, f"large_clean score should be ~95, got {score}"

def test_large_messy_score_below_60():
    score = score_csv(os.path.join(SAMPLE_DIR, "large_messy_data.csv"))
    assert score <= 60, f"large_messy score should be ~40, got {score}"


# Generator tests

def test_generator_produces_correct_columns(tmp_path):
    """Run generator and verify output has correct columns."""
    import sys
    sys.path.insert(0, SAMPLE_DIR)
    from generate_samples import generate_dataset

    output = str(tmp_path / "test_output.csv")
    generate_dataset(num_rows=10, error_rate=0.0, output_path=output)

    df = pd.read_csv(output)
    assert len(df) == 10
    for col in REQUIRED_COLUMNS:
        assert col in df.columns

def test_generator_zero_error_rate_gives_high_score(tmp_path):
    """Zero error rate should produce near perfect data."""
    import sys
    sys.path.insert(0, SAMPLE_DIR)
    from generate_samples import generate_dataset

    output = str(tmp_path / "clean.csv")
    generate_dataset(num_rows=100, error_rate=0.0, output_path=output)
    score = score_csv(output)
    assert score >= 95, f"Zero error rate should give score >= 95, got {score}"