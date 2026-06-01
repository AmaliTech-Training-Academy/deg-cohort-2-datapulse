<div align="center">
  <h1>DataPulse — Backend</h1>
  <p>Data Quality Monitoring Platform · Django 5 · DRF · PostgreSQL 15 · Docker</p>
</div>

---

## About

| | |
|---|---|
| **Project** | DataPulse — Phase 1 Group Project |
| **Team** | Team 1 · AmaliTech Training Academy |
| **Stack** | Python 3.12 · Django 5.0 · DRF · PostgreSQL 15 · Docker |
| **Purpose** | Starter scaffold — no feature implementations included |

---

## Project Structure

```
backend/
├── config/
│   ├── settings.py      ← all configuration (env-based, fully documented)
│   ├── urls.py          ← root URL router + Swagger + debug toolbar
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                ← shared utilities (used by all apps)
│   ├── models.py        ← TimeStampedModel abstract base
│   ├── views.py         ← GET /health/ liveness probe
│   ├── middleware.py    ← RequestLoggingMiddleware
│   ├── exceptions.py    ← custom_exception_handler (normalised errors)
│   └── urls.py
│
├── accounts/            ← authentication (US-001 to US-004)
│   ├── models.py        ← User(AbstractUser) with email login + role field
│   ├── serializers.py   ← RegisterSerializer, UserProfileSerializer
│   ├── views.py         ← RegisterView, LoginView, RefreshTokenView, MeView
│   ├── permissions.py   ← IsAdminUser
│   ├── exceptions.py
│   └── urls.py          ← /api/v1/auth/ routes
│
├── datasets/            ← file upload (US-005 to US-009)
│   ├── models.py        ← TODO
│   ├── serializers.py   ← TODO
│   ├── views.py         ← TODO
│   ├── permissions.py   ← TODO
│   ├── exceptions.py    ← TODO
│   ├── urls.py
│   └── management/
│       └── commands/
│           └── seed_db.py  ← python manage.py seed_db
│
├── rules/               ← validation rules (US-010 to US-016)
│   ├── models.py        ← TODO
│   ├── serializers.py   ← TODO
│   ├── views.py         ← TODO
│   ├── permissions.py   ← TODO
│   ├── exceptions.py    ← TODO
│   └── urls.py
│
├── checks/              ← validation engine + scoring (US-017 to US-023)
│   ├── models.py        ← TODO
│   ├── serializers.py   ← TODO
│   ├── views.py         ← TODO
│   ├── permissions.py   ← TODO
│   ├── exceptions.py    ← TODO
│   └── urls.py
│
├── reports/             ← quality reports + trends (US-024 to US-029)
│   ├── models.py        ← TODO
│   ├── serializers.py   ← TODO
│   ├── views.py         ← TODO
│   ├── permissions.py   ← TODO
│   ├── exceptions.py    ← TODO
│   └── urls.py
│
├── api/
│   └── urls.py          ← /api/v1/ route registry
│
├── tests/
│   ├── conftest.py      ← shared pytest fixtures (api_client, auth_client, users)
│   ├── test_accounts/
│   ├── test_datasets/
│   ├── test_rules/
│   ├── test_checks/
│   └── test_reports/
│
├── logs/                ← rotating log files (git-ignored)
├── media/               ← uploaded files (git-ignored, Docker volume mounted)
├── .env.example         ← copy to .env and fill in values
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

---

## Quick Start

### Option A — Docker (recommended, no local Python needed)

```bash
# 1. Clone the repo and navigate to the backend folder
cd backend/

# 2. Set up your environment file
cp .env.example .env
# Edit .env — the defaults work with Docker Compose out of the box

# 3. Build and start all services
docker compose up --build

# App:        http://localhost:8000
# Swagger UI: http://localhost:8000/api/docs/
# Health:     http://localhost:8000/health/
```

Docker Compose will automatically:
- Start PostgreSQL and wait for it to be healthy
- Run all migrations
- Run `seed_db` to create the default users
- Start the Django dev server

### Option B — Local (Python virtual environment)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit DB_HOST=localhost and DB_PORT=5432 for local PostgreSQL

# 4. Run migrations and seed
python manage.py migrate
python manage.py seed_db

# 5. Start the server
python manage.py runserver
```

---

## Default Credentials

| Role  | Email                      | Password    |
|-------|----------------------------|-------------|
| Admin | admin@amalitech.com        | password123 |
| User  | user@amalitech.com         | password123 |

> **Note:** Change these in `.env` before any deployment. These are development credentials only.

---

## API Endpoints

### Authentication (`accounts` app)

| Method | Endpoint                     | Description           | Auth |
|--------|------------------------------|-----------------------|------|
| POST   | `/api/v1/auth/register/`     | Create account        | No   |
| POST   | `/api/v1/auth/login/`        | Get JWT tokens        | No   |
| POST   | `/api/v1/auth/refresh/`      | Rotate tokens         | No   |
| GET    | `/api/v1/auth/me/`           | Current user profile  | Yes  |

### To be implemented by the team

| Prefix              | App       | User Stories        |
|---------------------|-----------|---------------------|
| `/api/v1/datasets/` | datasets  | US-005 to US-009    |
| `/api/v1/rules/`    | rules     | US-010 to US-016    |
| `/api/v1/checks/`   | checks    | US-017 to US-023    |
| `/api/v1/reports/`  | reports   | US-024 to US-029    |

### System

| Method | Endpoint        | Description                | Auth |
|--------|-----------------|----------------------------|------|
| GET    | `/health/`      | DB liveness check          | No   |
| GET    | `/api/docs/`    | Swagger UI                 | No   |
| GET    | `/api/schema/`  | Raw OpenAPI schema         | No   |

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run only a specific app's tests
pytest tests/test_accounts/

# Run a single test file
pytest tests/test_accounts/test_register.py
```

---

## Logging

Logs go to both stdout and `logs/app.log` (daily rotation, 7-day retention).
Errors also go to `logs/errors.log` (30-day retention).

```
# Local (DEBUG=True):  human-readable format
2025-01-17 09:00:00 [INFO] core.middleware: POST /api/v1/auth/login/ → 200  (12ms)

# Production (DEBUG=False):  structured JSON
{"asctime":"2025-01-17T09:00:00Z","levelname":"INFO","name":"core.middleware","message":"POST /api/v1/auth/login/ → 200  (12ms)"}
```

Control the log level via `.env`:
```
LOG_LEVEL=DEBUG    # all messages including SQL
LOG_LEVEL=INFO     # default — requests and above
LOG_LEVEL=WARNING  # errors only
```

---

## Key Design Decisions

**Custom User model** — `accounts.User` extends `AbstractUser` with `email` as
the login field and a `role` field for RBAC. This is set before the first
migration (`AUTH_USER_MODEL = "accounts.User"` in settings).

**Normalised error responses** — `core.exceptions.custom_exception_handler`
wraps all DRF error shapes into:
`{"error": {"code": "NOT_FOUND", "message": "...", "fields": {}}}`.
The React frontend only needs to handle one error shape.

**TimeStampedModel** — all concrete models inherit from `core.models.TimeStampedModel`
to get `created_at` and `updated_at` automatically.

**Ownership checks** — every view must filter querysets by `request.user`.
Never return data that belongs to another user. Pattern:
`Dataset.objects.filter(uploaded_by=request.user)`.

**`TODO` markers** — every file that needs implementation contains a `TODO`
comment explaining exactly what to build and how.

---

*Django 5 · DRF · SimpleJWT · drf-spectacular · django-cors-headers · python-json-logger*
