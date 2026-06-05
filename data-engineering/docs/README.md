# DataPulse — Data Engineering

## Quick Start

All services are managed from a single Docker Compose file at the repo root.
Set up your environment and start the core stack:

```bash
# From repo root
cp .env.example .env
docker compose up --build -d
```

This gives you PostgreSQL on `localhost:5433` and the Django API on `localhost:8000`.

Then start the pipeline and analytics DB:

```bash
docker compose --profile pipeline up --build -d
```

---

## Running Pipeline Scripts

Once the stack is running, use these commands from the repo root:

**Run the ETL pipeline (extract → transform → load):**
```bash
docker compose --profile pipeline up --build
```

**Run analytics queries:**
```bash
docker compose --profile pipeline run --rm pipeline python pipeline/analytics.py
```

**Generate sample data:**
```bash
docker compose --profile pipeline run --rm pipeline python sample_data/generate_samples.py
```

**Run the quality dashboard:**
```bash
docker compose --profile pipeline run --rm pipeline python dashboards/quality_dashboard.py
```

**Open an interactive shell inside the container:**
```bash
docker compose --profile pipeline run --rm pipeline bash
```

---

## Connecting to the Database Directly

The PostgreSQL database is exposed on your machine at:

```
Host:     localhost
Port:     5433
Database: datapulse
User:     datapulse_user
Password: datapulse_pass
```

Connect with any SQL client (DBeaver, TablePlus, psql):

```bash
psql -h localhost -p 5433 -U datapulse_user -d datapulse
```

---

## Accessing the Backend API

The Django API runs at `http://localhost:8000`. Use it to:
- Upload datasets via `POST /api/v1/datasets/`
- Trigger quality checks via `POST /api/v1/checks/run/{id}/`
- Fetch reports via `GET /api/v1/reports/{id}/`

Full API docs: `http://localhost:8000/api/docs/`

---

## Project Structure

```
data-engineering/
├── Dockerfile
├── requirements.txt
├── pipeline/
│   ├── etl_pipeline.py      ← main ETL job (extract → transform → load)
│   ├── analytics.py         ← trend and distribution queries
│   └── data_models.py       ← SQLAlchemy analytics table definitions
├── dashboards/
│   └── quality_dashboard.py ← quality score visualisations
├── sample_data/
│   ├── generate_samples.py  ← generates clean, messy and mixed datasets
│   ├── clean_data.csv
│   ├── messy_data.csv
│   └── mixed_data.csv
└── sql/
    ├── analytics_schema.sql ← analytics table DDL
    └── analytics_queries.sql← trend and report queries
```

## Documentation

For full schema reference — all tables, columns, indexes, ETL flow, and validation rule types — see [`docs/data_dictionary.md`](docs/data_dictionary.md).
