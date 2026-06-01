# DataPulse — Backend

FastAPI + PostgreSQL + SQLAlchemy + Pandas.

## Setup

**With Docker (recommended):**
```bash
cp ../.env.example ../.env
docker compose up --build
```
API runs at http://localhost:8000 — docs at http://localhost:8000/docs

**Without Docker:**
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Code Style

Install the pre-commit hook once after cloning:
```bash
pip install pre-commit
pre-commit install
```
flake8 will run automatically on every `git commit` and block it if there are style errors.

To check manually:
```bash
flake8 app --max-line-length=120
```

## Running Tests
```bash
pytest tests/ -v
```
Tests use SQLite — no database setup needed.

## What Needs to Be Implemented

| File | What to do |
|------|-----------|
| `app/routers/checks.py` | `run_checks` and `get_check_results` endpoints |
| `app/routers/reports.py` | `get_dataset_report` and `get_quality_trends` endpoints |
| `app/routers/rules.py` | `update_rule` and `delete_rule` endpoints |
| `app/services/validation_engine.py` | `type_check`, `range_check`, `unique_check`, `regex_check` |
| `app/services/scoring_service.py` | weighted quality score calculation |

Each function has a TODO docstring with step-by-step instructions.

## Branching

Work on a feature branch, never push directly to `main`:
```bash
git checkout -b feature/your-feature-name
```
Open a PR when done — CI must pass before merging.
