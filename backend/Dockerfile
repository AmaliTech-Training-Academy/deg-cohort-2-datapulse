# ─────────────────────────────────────────────────────────────────────────────
# DataPulse — Dockerfile
# Multi-stage build: builder installs dependencies, runtime runs the app.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-alpine AS builder

WORKDIR /app

# Build tools required by psycopg2-binary on Alpine
RUN apk add --no-cache gcc musl-dev libpq-dev

COPY requirements.txt .

# Install into /install so the runtime stage can copy just the packages,
# not the entire build toolchain. Layer is cached until requirements.txt changes.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-alpine AS runtime

WORKDIR /app

# Runtime dependency for psycopg2
RUN apk add --no-cache libpq

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Prevent .pyc files and enable unbuffered stdout/stderr so logs appear
# immediately in docker compose logs without buffering delay
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run as a non-root user — never run Django as root inside a container
RUN addgroup -S datapulse && adduser -S datapulse -G datapulse

# Copy source with correct ownership
COPY --chown=datapulse:datapulse . .

# Create runtime directories the app writes to at startup
RUN mkdir -p media logs && chown -R datapulse:datapulse media logs

USER datapulse

EXPOSE 8000

# HTTP healthcheck — proves the server is actually serving traffic,
# not just that the process started or the DB is reachable.
# docker-compose depends_on waits for this to pass before marking web healthy.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=4)"

# Default command — overridden by docker-compose.yml command block
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]