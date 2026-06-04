# DataPulse — Deployment Guide

## Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [GitHub CLI](https://cli.github.com/) (optional)
- AWS IAM access with ECR and EC2 permissions

---

## Local Development

**1. Copy environment file**
```bash
cp .env.example .env
# Fill in required values
```

**2. Start core services (DB + backend)**
```bash
docker-compose up db backend
```

**3. Start frontend**
```bash
docker-compose --profile frontend up frontend
```

**4. Start ETL pipeline**
```bash
docker-compose --profile pipeline up pipeline
```

**5. Start Streamlit dashboard**
```bash
docker-compose --profile streamlit up streamlit
# Accessible at http://localhost:8501/analytics/
```

> See [Docker Compose profiles docs](https://docs.docker.com/compose/profiles/) for more.

---

## CI/CD Pipeline

Managed via GitHub Actions — see `.github/workflows/ci.yml`.

| Job | Trigger | What it does |
|-----|---------|--------------|
| lint + test | every push | Runs flake8, pytest, Jest |
| docker-build | every push | Validates compose config |
| scan-images | every push | Trivy CVE scan (blocks on fixable CRITICALs) |
| push-to-ecr | every push | Builds and pushes images to ECR |
| deploy-to-staging | push to `dev` only | SSHs into EC2, pulls latest images, restarts stack |

> See [GitHub Actions docs](https://docs.github.com/en/actions) and [Trivy docs](https://trivy.dev/).

---

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | IAM role for OIDC authentication |
| `AWS_REGION` | e.g. `eu-west-1` |
| `ECR_REGISTRY` | e.g. `123456789.dkr.ecr.eu-west-1.amazonaws.com` |
| `STAGING_EC2_HOST` | EC2 public IP |
| `STAGING_EC2_USER` | e.g. `ubuntu` |
| `STAGING_EC2_SSH_KEY` | Private SSH key for EC2 access |

> See [GitHub encrypted secrets docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

---

## EC2 Setup (first time only)

**1. SSH into the instance**
```bash
ssh -i datapulse-staging-key.pem ubuntu@<EC2_IP>
```

**2. Install Docker**
```bash
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
```

**3. Clone the repo and set up environment**
```bash
git clone https://github.com/AmaliTech-Training-Academy/deg-cohort-2-datapulse.git ~/datapulse
cd ~/datapulse
cp .env.example .env
# Fill in production values
```

**4. Authenticate with ECR**
```bash
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin <ECR_REGISTRY>
```

> See [ECR authentication docs](https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry_auth.html).

---

## Manual Deploy (if CI is not available)

```bash
cd ~/datapulse
git pull origin dev
ECR_REGISTRY=<your-registry> docker-compose -f docker-compose.prod.yml pull
ECR_REGISTRY=<your-registry> docker-compose -f docker-compose.prod.yml up -d
docker image prune -f
```

---

## Service URLs (staging)

| Service | URL |
|---------|-----|
| Frontend | `http://<EC2_IP>/` |
| API docs | `http://<EC2_IP>/api/docs/` |
| Streamlit dashboard | `http://<EC2_IP>/analytics/` |

---

## Warning

The EC2 IP changes on every stop/start. Always update:
- GitHub secret `STAGING_EC2_HOST`
- GitHub variable `STAGING_EC2_HOST`
- `ALLOWED_HOSTS` in `.env` on EC2
