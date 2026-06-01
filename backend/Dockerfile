# ─────────────────────────────────────────────────────────────────────────────
# DataPulse — Dockerfile
# Multi-stage build for a lean, production-friendly image.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-alpine AS builder

# Build tools required by some Python packages (psycopg2-binary, numpy)
RUN apk add --no-cache gcc musl-dev libpq-dev

WORKDIR /app

# Copy and install dependencies into a separate directory so Docker layer
# caching kicks in — this layer only rebuilds when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-alpine AS runtime

# Install libpq (runtime dependency for psycopg2)
RUN apk add --no-cache libpq

# Create a non-root user — never run Django as root in a container
RUN addgroup -S datapulse && adduser -S datapulse -G datapulse

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=datapulse:datapulse . .

# Create media and logs directories with correct ownership
RUN mkdir -p media logs && chown -R datapulse:datapulse media logs

# Switch to non-root user
USER datapulse

# Expose the Django dev server port
EXPOSE 8000

# Container liveness probe — checks DB connectivity
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python manage.py check --database default || exit 1

# Default command — overridden by docker-compose.yml
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
