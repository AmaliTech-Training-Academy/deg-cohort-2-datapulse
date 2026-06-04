# DataPulse — Data Dictionary

**Project:** DataPulse — Data Quality Monitoring Tool  
**Team:** DE Cohort 2 — Team 1  
**Last Updated:** 2026-06-04  
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Operational Database](#operational-database)
   - [datasets](#table-datasets)
   - [validation_rules](#table-validation_rules)
   - [quality_reports](#table-quality_reports)
   - [rule_findings](#table-rule_findings)
   - [trend_metrics](#table-trend_metrics)
4. [Analytics Database (Star Schema)](#analytics-database-star-schema)
   - [dim_datasets](#table-dim_datasets)
   - [dim_rules](#table-dim_rules)
   - [dim_date](#table-dim_date)
   - [fact_quality_checks](#table-fact_quality_checks)
   - [fact_trend_metrics](#table-fact_trend_metrics)
5. [Index Strategy](#index-strategy)
6. [ETL Pipeline](#etl-pipeline)
7. [Quality Score Formula](#quality-score-formula)
8. [Validation Rule Types](#validation-rule-types)
9. [Sample Datasets](#sample-datasets)
10. [How to Run](#how-to-run)

---

## Overview

DataPulse uses **two separate PostgreSQL databases**:

| Database | Purpose | Managed By |
|---|---|---|
| Operational DB (`datapulse`) | Stores live application data — users, datasets, rules, reports | Django ORM |
| Analytics DB (`datapulse_analytics`) | Stores pre-aggregated quality metrics for dashboard queries | SQLAlchemy / ETL Pipeline |

Data flows **one way**: Operational DB → ETL Pipeline → Analytics DB.  
The ETL is triggered automatically via a Django `post_save` signal every time a new quality report is saved.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  OPERATIONAL DB                      │
│                                                      │
│  datasets → validation_rules → rule_findings         │
│      └──────────── quality_reports ──────────────┘  │
│                         └── trend_metrics            │
└──────────────────────┬──────────────────────────────┘
                       │  ETL Pipeline (triggered by
                       │  Django post_save signal)
                       ▼
┌─────────────────────────────────────────────────────┐
│                  ANALYTICS DB                        │
│                                                      │
│  dim_datasets ──┐                                   │
│  dim_rules   ───┼──► fact_quality_checks             │
│  dim_date    ───┘                                   │
│                                                      │
│  dim_datasets ──► fact_trend_metrics                 │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
            Streamlit Dashboard
            (analytics.py → quality_dashboard.py)
```

---

## Operational Database

The operational database is managed entirely by Django migrations.  
Connection string env var: `SOURCE_DB_URL`

---

### Table: `datasets`

Stores metadata for every file uploaded by a user. The physical file lives at `MEDIA_ROOT/uploads/<user_id>/<uuid>.<ext>`. The `file_path` column is never exposed in API responses.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key. Auto-generated UUID4. |
| `user_id` | UUID (FK) | NO | Foreign key → `accounts_user.id`. The user who uploaded the file. |
| `file_name` | VARCHAR(255) | NO | Original filename as uploaded (e.g. `sales_data.csv`). |
| `file_type` | VARCHAR(10) | NO | File format. Allowed values: `csv`, `json`. |
| `file_path` | VARCHAR(500) | NO | Absolute server path to the stored file. Internal use only. |
| `file_title` | VARCHAR(255) | YES | Optional human-readable title given by the user. |
| `description` | TEXT | YES | Optional description of the dataset. |
| `row_count` | INTEGER | YES | Number of data rows parsed from the file. Populated after upload. |
| `columns` | JSONB | NO | List of column names extracted from the file. Default: `[]`. Example: `["name", "age", "email"]`. |
| `created_at` | TIMESTAMPTZ | NO | Timestamp when the record was created. Auto-set. |
| `updated_at` | TIMESTAMPTZ | NO | Timestamp of last update. Auto-updated. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_dataset_user_created` | `user_id`, `created_at DESC` | Fast lookup of a user's datasets ordered by recency |

**Relationships:**
- One dataset → many `validation_rules`
- One dataset → many `quality_reports`
- One dataset → many `trend_metrics`

---

### Table: `validation_rules`

Stores one rule per column per rule type per dataset. A `UniqueConstraint` on `(dataset_id, column_name, rule_type)` prevents the same check being added twice on the same column.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key. Auto-generated UUID4. |
| `dataset_id` | UUID (FK) | NO | Foreign key → `datasets.id`. The dataset this rule belongs to. |
| `column_name` | VARCHAR(255) | NO | The column in the dataset this rule applies to (e.g. `age`, `email`). |
| `rule_type` | VARCHAR(30) | NO | Type of validation. Allowed values: `null_check`, `type_check`, `range_check`, `uniqueness_check`. |
| `rule_config` | JSONB | NO | Rule-specific configuration parameters. See [Validation Rule Types](#validation-rule-types) for structure. Default: `{}`. |
| `created_at` | TIMESTAMPTZ | NO | Timestamp when the rule was created. Auto-set. |

**Constraints:**
| Constraint | Columns | Description |
|---|---|---|
| `unique_rule_per_column_type` | `dataset_id`, `column_name`, `rule_type` | Prevents duplicate rules on the same column |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_rule_dataset` | `dataset_id` | Fast lookup of all rules for a dataset |

**Relationships:**
- Many rules → one `datasets`
- One rule → many `rule_findings`

---

### Table: `quality_reports`

Stores the result of one quality check run against a dataset. Each time a user triggers a check, one report is created summarising the overall outcome.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key. Auto-generated UUID4. |
| `dataset_id` | UUID (FK) | NO | Foreign key → `datasets.id`. The dataset that was checked. |
| `overall_score` | INTEGER | NO | Quality score from 0 to 100. Computed as `(rows_passed / total_rows) * 100` using union of failed rows across all rules. |
| `total_rows` | INTEGER | NO | Total number of rows in the dataset at time of check. |
| `rows_passed` | INTEGER | NO | Number of rows that passed all rules. |
| `rows_failed` | INTEGER | NO | Number of rows that failed at least one rule (union — not sum). |
| `generated_at` | TIMESTAMPTZ | NO | Timestamp when the report was generated. |
| `status` | VARCHAR(20) | NO | Report status. Typical values: `completed`, `failed`. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_reports_dataset_id` | `dataset_id` | ETL join and dashboard filtering |
| `idx_reports_generated_at` | `generated_at DESC` | Trend queries ordered by time |

**Relationships:**
- One report → many `rule_findings`
- Many reports → one `datasets`

---

### Table: `rule_findings`

Stores the per-rule result for each quality check run. One finding is created per rule per report — so if a dataset has 4 rules and a check is run, 4 findings are created.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key. Auto-generated UUID4. |
| `report_id` | UUID (FK) | NO | Foreign key → `quality_reports.id`. The report this finding belongs to. |
| `rule_id` | UUID (FK) | NO | Foreign key → `validation_rules.id`. The rule that was evaluated. |
| `dataset_id` | UUID (FK) | NO | Foreign key → `datasets.id`. Denormalised for query convenience. |
| `column_name` | VARCHAR(255) | NO | Column the rule was applied to. Denormalised from `validation_rules`. |
| `rule_type` | VARCHAR(30) | NO | Rule type. Denormalised from `validation_rules`. |
| `rows_checked` | INTEGER | NO | Total rows checked (equals `quality_reports.total_rows`). |
| `rows_failed` | INTEGER | NO | Number of rows that failed this specific rule. |
| `failure_percentage` | FLOAT | NO | `(rows_failed / rows_checked) * 100`. Rounded to 2 decimal places. |
| `error_details` | JSONB | YES | Up to 5 sample error rows. Structure: `[{"row": 1, "value": "xyz", "reason": "null or empty value"}]`. |
| `rule_config` | JSONB | YES | Snapshot of the rule config at time of check. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_findings_report_id` | `report_id` | ETL join — fetch all findings for a report |
| `idx_findings_rule_id` | `rule_id` | ETL join — fetch all findings for a rule |
| `idx_findings_dataset_id` | `dataset_id` | Dashboard filtering by dataset |

**Relationships:**
- Many findings → one `quality_reports`
- Many findings → one `validation_rules`

---

### Table: `trend_metrics`

Stores daily aggregated quality scores per dataset. One row per dataset per day. Used by the ETL to populate `fact_trend_metrics` in the analytics warehouse.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | NO | Primary key. Auto-generated UUID4. |
| `dataset_id` | UUID (FK) | NO | Foreign key → `datasets.id`. |
| `snapshot_date` | DATE | NO | The date this snapshot represents. |
| `aggregated_score` | INTEGER | NO | Average quality score across all checks run on this dataset on this date. Range: 0–100. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_trends_dataset_id` | `dataset_id` | ETL join |
| `idx_trends_snapshot_date` | `snapshot_date DESC` | Date range filtering for trend charts |

---

## Analytics Database (Star Schema)

The analytics database uses a **star schema** — a central fact table surrounded by dimension tables. It is optimised for read-heavy dashboard queries, not writes.

Connection string env var: `TARGET_DB_URL`  
Managed by: SQLAlchemy ORM (`data_models.py`)  
Populated by: ETL Pipeline (`etl_pipeline.py`)

### Schema Diagram

```
          dim_date
             │
             │ date_key
             │
dim_datasets ─┬─── fact_quality_checks ───┬─── dim_rules
              │                            │
              └─── fact_trend_metrics ─────┘
```

---

### Table: `dim_datasets`

Dimension table — one row per unique dataset. Sourced from `datasets` in the operational DB.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER | NO | Surrogate primary key. Auto-incremented. |
| `source_id` | UUID | NO | Original UUID from `datasets.id`. Used for upsert matching. Unique. |
| `name` | VARCHAR(255) | YES | Dataset filename. Maps to `datasets.file_name`. |
| `file_type` | VARCHAR(10) | YES | File format: `csv` or `json`. |
| `row_count` | INTEGER | YES | Number of rows in the dataset. |
| `uploaded_at` | DATETIME | YES | When the dataset was uploaded. Maps to `datasets.created_at`. |

---

### Table: `dim_rules`

Dimension table — one row per unique validation rule. Sourced from `validation_rules` in the operational DB.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER | NO | Surrogate primary key. Auto-incremented. |
| `source_id` | UUID | NO | Original UUID from `validation_rules.id`. Used for upsert matching. Unique. |
| `name` | VARCHAR(255) | YES | Rule display name. Maps to `validation_rules.column_name`. |
| `field_name` | VARCHAR(255) | YES | Column the rule applies to. Maps to `validation_rules.column_name`. |
| `rule_type` | VARCHAR(50) | YES | Rule type: `null_check`, `type_check`, `range_check`, `uniqueness_check`. |
| `severity` | VARCHAR(20) | YES | Derived from `rule_config.severity`. Values: `low`, `medium`, `high`. Default: `medium`. |

---

### Table: `dim_date`

Date dimension — one row per calendar date that appears in the fact tables. Enables time-based slicing in dashboard queries.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `date_key` | INTEGER | NO | Primary key. Format: `YYYYMMDD` (e.g. `20260604`). |
| `full_date` | DATE | YES | The actual calendar date. |
| `day_of_week` | INTEGER | YES | Day of week as integer. `0` = Monday, `6` = Sunday. |
| `month` | INTEGER | YES | Month number. Range: 1–12. |
| `year` | INTEGER | YES | Four-digit year. |

---

### Table: `fact_quality_checks`

Central fact table — one row per rule per quality check run. This is the primary table for dashboard aggregations.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER | NO | Surrogate primary key. Auto-incremented. |
| `dataset_id` | INTEGER (FK) | YES | Foreign key → `dim_datasets.id`. |
| `rule_id` | INTEGER (FK) | YES | Foreign key → `dim_rules.id`. |
| `rule_type` | VARCHAR(50) | YES | Denormalised rule type for fast filtering without join. |
| `passed` | BOOLEAN | YES | `TRUE` if `failure_percentage == 0` for this rule in this check. |
| `failed_rows` | INTEGER | YES | Number of rows that failed this rule. Maps to `rule_findings.rows_failed`. |
| `total_rows` | INTEGER | YES | Total rows checked. Maps to `rule_findings.rows_checked`. |
| `score` | FLOAT | YES | Per-rule score derived as `1 - (failed_rows / total_rows)`. Range: 0.0–1.0. |
| `severity` | VARCHAR(20) | YES | Rule severity at time of check. |
| `checked_at` | DATETIME (TZ) | YES | When the check was run. Maps to `quality_reports.generated_at`. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_fqc_dataset_id` | `dataset_id` | Dashboard JOIN on dataset |
| `idx_fqc_rule_id` | `rule_id` | Dashboard JOIN on rule |
| `idx_fqc_checked_at` | `checked_at` | Trend queries filtered by date |
| `idx_fqc_rule_type` | `rule_type` | Rule failure rate queries |
| `idx_fqc_passed` | `passed` | Filter passing vs failing checks |

---

### Table: `fact_trend_metrics`

Fact table — one row per dataset per day. Stores pre-aggregated daily quality scores for efficient trend chart queries.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER | NO | Surrogate primary key. Auto-incremented. |
| `dataset_id` | INTEGER (FK) | NO | Foreign key → `dim_datasets.id`. |
| `source_id` | UUID | NO | Original UUID from `trend_metrics.id`. Unique. Used to prevent duplicate loads. |
| `snapshot_date` | DATE | NO | The date this trend snapshot represents. |
| `aggregated_score` | INTEGER | YES | Daily aggregated quality score. Range: 0–100. |

**Indexes:**
| Index Name | Columns | Purpose |
|---|---|---|
| `idx_ftm_dataset_id` | `dataset_id` | Dashboard JOIN on dataset |
| `idx_ftm_snapshot_date` | `snapshot_date` | Date range filtering for trend charts |

---

## Index Strategy

### Why Indexes Matter Here

The ETL pipeline joins `rule_findings → quality_reports → datasets` in a single multi-table merge. Without indexes on foreign key columns, each join performs a full table scan — acceptable for small datasets but slow at scale.

The dashboard trend query filters by `snapshot_date` and joins on `dataset_id` — both columns need indexes for acceptable query performance.

### Summary

| Database | Table | Column | Index Name | Reason |
|---|---|---|---|---|
| Operational | `datasets` | `user_id`, `created_at` | `idx_dataset_user_created` | User dataset listing |
| Operational | `validation_rules` | `dataset_id` | `idx_rule_dataset` | Rule lookup per dataset |
| Operational | `quality_reports` | `dataset_id` | `idx_reports_dataset_id` | ETL join |
| Operational | `quality_reports` | `generated_at` | `idx_reports_generated_at` | Trend ordering |
| Operational | `rule_findings` | `report_id` | `idx_findings_report_id` | ETL join |
| Operational | `rule_findings` | `rule_id` | `idx_findings_rule_id` | ETL join |
| Operational | `rule_findings` | `dataset_id` | `idx_findings_dataset_id` | Dashboard filter |
| Operational | `trend_metrics` | `dataset_id` | `idx_trends_dataset_id` | ETL join |
| Operational | `trend_metrics` | `snapshot_date` | `idx_trends_snapshot_date` | Date range queries |
| Analytics | `fact_quality_checks` | `dataset_id` | `idx_fqc_dataset_id` | Dashboard JOIN |
| Analytics | `fact_quality_checks` | `rule_id` | `idx_fqc_rule_id` | Dashboard JOIN |
| Analytics | `fact_quality_checks` | `checked_at` | `idx_fqc_checked_at` | Trend filtering |
| Analytics | `fact_quality_checks` | `rule_type` | `idx_fqc_rule_type` | Failure rate queries |
| Analytics | `fact_quality_checks` | `passed` | `idx_fqc_passed` | Pass/fail filtering |
| Analytics | `fact_trend_metrics` | `dataset_id` | `idx_ftm_dataset_id` | Dashboard JOIN |
| Analytics | `fact_trend_metrics` | `snapshot_date` | `idx_ftm_snapshot_date` | Date range filtering |

---

## ETL Pipeline

### Overview

The ETL pipeline (`etl_pipeline.py`) is a Python script that extracts data from the operational DB, transforms it into a star schema shape, and loads it into the analytics DB.

### Trigger

The pipeline is triggered automatically by a Django `post_save` signal whenever a new `QualityReport` is saved. It runs in a **background thread** to avoid blocking the API response.

```
QualityReport saved
      ↓
post_save signal fires (checks/signals.py)
      ↓
Background thread starts
      ↓
ETLPipeline().run()
      ↓
Analytics DB updated
```

### Extract

Reads five tables from the operational DB:

| Source Table | Target Variable | Description |
|---|---|---|
| `datasets` | `raw_datasets` | All uploaded datasets |
| `validation_rules` | `raw_rules` | All validation rules |
| `quality_reports` | `raw_reports` | All quality check reports |
| `rule_findings` | `raw_findings` | Per-rule results |
| `trend_metrics` | `raw_trends` | Daily aggregated scores |

### Transform

Joins `rule_findings → quality_reports → datasets` into a flat DataFrame, then derives:

| Derived Column | Formula |
|---|---|
| `passed` | `failure_percentage == 0` |
| `score` | `1 - (failure_percentage / 100)`, clipped to [0, 1] |
| `severity` | Extracted from `rule_config` JSON. Default: `medium` |
| `checked_at` | Parsed from `quality_reports.generated_at` with UTC timezone |

Then splits into dimension and fact DataFrames for loading.

### Load Strategy

| Table Type | Strategy | Reason |
|---|---|---|
| Dimension tables | Upsert (insert if not exists) | Preserve surrogate keys across runs |
| Fact tables | Truncate then reload | Facts are fully derived — safe to rebuild |

### Environment Variables

| Variable | Description |
|---|---|
| `SOURCE_DB_URL` | PostgreSQL connection string for the operational DB |
| `TARGET_DB_URL` | PostgreSQL connection string for the analytics DB |

---

## Quality Score Formula

The quality score is computed by the `QualityScoreCalculator` in `checks/services/scoring_service.py`.

```
quality_score = (rows_passed / total_rows) * 100

Where:
    rows_passed  = total_rows - len(failed_union)
    failed_union = set union of all failed row indexes across all rules
```

### Why Union and Not Sum

A row that fails 3 different rules is counted **once** as a failed row, not three times. Summing per-rule failure counts would overstate the problem and could produce scores below 0 in extreme cases.

### Example

| Dataset | Total Rows | Failed (union) | Score |
|---|---|---|---|
| `clean_data.csv` | 1000 | 48 | 95 |
| `mixed_data.csv` | 1000 | 298 | 70 |
| `messy_data.csv` | 1000 | 604 | 40 |

---

## Validation Rule Types

All four rule types are implemented in `checks/services/validation_engine.py`.

### `null_check`

Fails rows where the column value is `NULL`, `NaN`, or an empty string after stripping whitespace.

```json
{ }
```

No configuration parameters required.

---

### `type_check`

Fails rows where the value cannot be converted to the expected type.

```json
{ "expected_type": "integer" }
```

| Parameter | Type | Required | Allowed Values |
|---|---|---|---|
| `expected_type` | string | YES | `integer`, `float`, `boolean`, `string` |

**Type rules:**
- `integer` — rejects nulls, non-numeric strings, and fractional numbers (e.g. `3.5`). Whole-number floats like `3.0` are accepted.
- `float` — rejects non-numeric strings.
- `boolean` — accepts `true`, `false`, `1`, `0`, `yes`, `no` (case-insensitive).
- `string` — every non-null value is valid.

---

### `range_check`

Fails rows where the numeric value falls outside `[min, max]`. Non-numeric values are treated as failures.

```json
{ "min": 0, "max": 120 }
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `min` | number | NO | Minimum allowed value (inclusive). Omit to skip lower bound check. |
| `max` | number | NO | Maximum allowed value (inclusive). Omit to skip upper bound check. |

---

### `uniqueness_check`

Fails **all copies** of any value that appears more than once. Both the first occurrence and all duplicates are flagged.

```json
{ }
```

No configuration parameters required.

---

## Sample Datasets

Three tiers of sample data are provided in `data-engineering/sample_data/` for testing and demonstration.

| File | Expected Score | Description |
|---|---|---|
| `clean_data.csv` | ~95 | Minimal nulls, correct types, values in range, no duplicates |
| `mixed_data.csv` | ~70 | Some nulls and type errors, occasional out-of-range values |
| `messy_data.csv` | ~40 | Frequent nulls, wrong types, out-of-range values, many duplicates |
| `large_clean_data.csv` | ~95 | Large-scale version of clean data for performance testing |
| `large_mixed_data.csv` | ~70 | Large-scale version of mixed data |
| `large_messy_data.csv` | ~40 | Large-scale version of messy data |

### Schema of Sample CSV Files

All sample files share the same column structure:

| Column | Type | Validation Rules Applied |
|---|---|---|
| `name` | string | `null_check` |
| `email` | string | `null_check` |
| `department` | string | `null_check` |
| `age` | integer | `range_check` (min: 18, max: 65) |
| `salary` | float | `range_check` (min: 0) |
| `hire_date` | date | `type_check` |

---

## How to Run

### Prerequisites

Ensure both environment variables are set:

```bash
export SOURCE_DB_URL=postgresql://user:pass@localhost:5432/datapulse
export TARGET_DB_URL=postgresql://user:pass@localhost:5432/datapulse_analytics
```

### Initialize the Analytics Database

Run once to create the star schema tables and seed initial data:

```bash
cd data-engineering/pipeline
python init_analytics_db.py
```

### Run the ETL Manually

```bash
cd data-engineering/pipeline
python etl_pipeline.py
```

### Run the Streamlit Dashboard

```bash
cd data-engineering
pip install streamlit plotly pandas sqlalchemy
streamlit run dashboards/quality_dashboard.py
```

### Run via Docker Compose

```bash
docker-compose up --build
```

The ETL will trigger automatically after each quality check run through the Django application. No manual steps required in normal operation.

---

*DataPulse — DE Cohort 2 — Team 1*