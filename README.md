# DataPulse

Upload datasets, define quality rules, run checks, and track trends — all in one place.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django / DRF / PostgreSQL |
| Frontend | Angular |
| Data Pipeline | Python / Pandas / SQLAlchemy |
| Analytics Dashboard | Streamlit / Plotly |
| Infrastructure | Docker, Docker Compose, GitHub Actions, AWS ECR + EC2 |

---

## Quick Start

**1. Copy environment file**
```bash
cp .env.example .env
```

**2. Start backend + database**
```bash
docker-compose up db backend
```

**3. Start frontend**
```bash
docker-compose --profile frontend up frontend
# http://localhost:4200
```

**4. Start ETL pipeline**
```bash
docker-compose --profile pipeline up pipeline
```

**5. Start analytics dashboard**
```bash
docker-compose --profile streamlit up streamlit
# http://localhost:8501/analytics/
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/datasets/upload` | Upload dataset |
| GET | `/api/datasets` | List datasets |
| POST | `/api/rules` | Create rule |
| GET | `/api/rules` | List rules |
| PUT | `/api/rules/{id}` | Update rule |
| DELETE | `/api/rules/{id}` | Delete rule |
| POST | `/api/checks/run/{id}` | Run quality check |
| GET | `/api/checks/results/{id}` | Get check results |
| GET | `/api/reports/{id}` | Get report |
| GET | `/api/reports/trends` | Get trend data |

Full interactive docs: `http://localhost:8000/api/docs/`

---

## Deployment

See [devops/deployment.md](devops/deployment.md) for the full deployment guide.
