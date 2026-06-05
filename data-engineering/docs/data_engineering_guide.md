# Data Engineering Guide

## Overview

This guide covers the data engineering deliverables for DataPulse:
- Sample datasets for testing the full system
- Data generator script
- Analytics queries for quality trend analysis
- Streamlit dashboard for internal monitoring
- Test suite covering all data engineering code

---

## Sample Datasets

### What each dataset represents

| File | Rows | Score | Description |
|---|---|---|---|
| `clean_data.csv` | 100 | ~95 | Well-maintained employee data,almost all rows valid |
| `messy_data.csv` | 100 | ~40 | Poorly maintained, nulls, wrong types, out of range values |
| `mixed_data.csv` | 100 | ~70 | Realistic mix, some rows clean, some with problems |
| `large_clean_data.csv` | 500 | ~95 | Large clean dataset for scale testing |
| `large_messy_data.csv` | 500 | ~40 | Large messy dataset for scale testing |
| `large_mixed_data.csv` | 500 | ~70 | Large mixed dataset for scale testing |

### Dataset columns

```
id, name, email, age, department, salary, hire_date
```

### Quality score formula

Matches the backend `QualityScoreCalculator` exactly:

```
score = (total_rows - len(failed_union)) / total_rows × 100
```

Where `failed_union` = set union of all failed row indexes across all rules.
A row failing 3 rules counts as **one** failed row — not three.

### Validation rules applied

| Rule | Column | Condition |
|---|---|---|
| not_null | name | Must not be null or empty |
| not_null | email | Must not be null or empty |
| not_null | department | Must not be null or empty |
| value_range | age | Must be between 18 and 65 |
| value_range | salary | Must be greater than 0 |
| date_valid | hire_date | Must be a valid date |

### Who uses the sample data

| Team | How they use it |
|---|---|
| Backend | Upload via API to test file upload and validation engine |
| QA | Verify quality scores match expected targets |
| Data Engineering | ETL pipeline processes quality results into analytics DB |
| Data Engineering | Analytics queries and dashboard verification |
| Frontend | Manual testing of upload UI and dashboard charts |

---

## Generating Sample Data

### Run the generator

```bash
cd sample_data
python generate_samples.py
```

Generates all 6 CSV files with correct quality scores.

### Custom datasets

```python
from generate_samples import generate_dataset

# 200 rows with 10% error rate
generate_dataset(
    num_rows=200,
    error_rate=0.10,
    output_path="custom_data.csv"
)
```

### Error rate to score mapping

| error_rate | Expected score |
|---|---|
| 0.00 | ~100 |
| 0.05 | ~95 |
| 0.30 | ~70 |
| 0.60 | ~40 |

---

## Analytics Queries

### Run analytics queries

```bash
docker compose --profile pipeline run --rm pipeline python pipeline/analytics.py
```

### Available functions

| Function | Returns |
|---|---|
| `score_summary()` | Quality score per dataset — sorted best to worst |
| `rule_failure_rates()` | Failure rate per rule type across all datasets |
| `quality_trend(dataset, days)` | Score trend over last N days for a dataset |
| `worst_datasets(n)` | N datasets with lowest quality scores |
| `monthly_summary()` | Average quality score per dataset per month |

### SQL queries for Dashboard API

`sql/analytics_queries.sql` contains 7 queries used by the backend
for `GET /api/v1/dashboard/`:

| Query | Business question answered |
|---|---|
| Overall quality score per dataset | Which dataset has best/worst quality? |
| Quality score over time | Is quality improving or declining? |
| Most common failing rule types | Which rules fail most often? |
| Datasets with declining quality | Which datasets need urgent attention? |
| Rule performance per dataset | How does each rule perform per dataset? |
| Monthly quality summary | How does quality change month by month? |
| Top 5 worst datasets | Which datasets need immediate attention? |

---

## Streamlit Dashboard

The Streamlit dashboard is an **internal monitoring tool** for the data engineering team.
It is not the end-user dashboard, that is the React frontend at port 4200.

### Run the dashboard

```bash
# Development
docker compose --profile streamlit up
```

Open `http://localhost:8501` or `http://localhost/analytics/` (via nginx proxy).

### Dashboard sections

| Section | Description |
|---|---|
| Overview KPIs | Average score, total rows, failed rows, best dataset |
| Dataset Quality Scores | Horizontal bar chart: score per dataset |
| Rule Failure Rates | Bar chart:  which rules fail most often |
| Quality Score Trend | Line chart: score over time for selected dataset |
| Monthly Quality Trends | Multi-line chart: all datasets month by month |
| Datasets Needing Attention | Top 3 datasets with lowest scores |
| Dataset Comparison Table | Full breakdown with Good/Fair/Poor status |

### How the dashboard gets updated

```
User uploads CSV via React frontend
         ↓
Backend runs validation and stores results in PostgreSQL
         ↓
ETL pipeline runs (manual or scheduled)
         ↓
Analytics DB updated
         ↓
Dashboard shows new data on next refresh
```

---

## Running Tests

### Run all tests inside Docker

```bash
docker compose --profile pipeline run --rm pipeline python -m pytest tests/ -v
```

Expected result: **86 passed, 0 failed**

### Test files

| File | What it tests |
|---|---|
| `test_sample_data.py` | Files exist, correct columns, row counts, quality scores hit targets |
| `test_analytics.py` | Analytics functions return correct results, scoring formula |
| `test_dashboard.py` | Dashboard imports and all required files exist |
| `test_data_models.py` | SQLAlchemy models, table names, columns, foreign keys |
| `test_etl_pipeline.py` | ETL transform logic, score formula, severity extraction |

### Where tests fit in the pipeline

```
test_sample_data.py   → verifies input data before entering the system
test_etl_pipeline.py  → verifies ETL transforms data correctly
test_data_models.py   → verifies DB schema is correct
test_analytics.py     → verifies analytics queries return correct results
test_dashboard.py     → verifies dashboard can load and visualize
```

---

## Data Flow

```
sample_data/*.csv
      ↓
User uploads via React frontend (port 4200)
      ↓
Backend API validates and stores (port 8000)
      ↓
Quality reports saved to PostgreSQL (port 5433)
      ↓
ETL pipeline extracts and transforms
      ↓
Analytics DB populated (port 5437)
      ↓
analytics.py queries analytics DB
      ↓
Streamlit dashboard (port 8501)  internal monitoring
Backend Dashboard API  serves React admin panel
      ↓
React frontend shows quality trends to users (port 4200)
```

---

## Environment Variables

| Variable | Description | Used by |
|---|---|---|
| `SOURCE_DB_URL` | Backend PostgreSQL connection | ETL pipeline |
| `TARGET_DB_URL` | Analytics DB connection (Docker internal) | ETL pipeline, dashboard in Docker |
| `TARGET_DB_URL_LOCAL` | Analytics DB connection (local access) | Tests, local development |
| `STREAMLIT_PORT` | Streamlit port (default 8501) | Docker compose |

---

*DataPulse — DE Cohort 2 — Team 1*