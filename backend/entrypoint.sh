#!/bin/sh
# entrypoint.sh — DataPulse container startup script
#
# Controls:
#   SEED_DB=true   (default) — run seed_db after migrations
#   SEED_DB=false            — skip seeding (CI, staging, production)
#
# Usage in .env:
#   SEED_DB=true    ← development / demo
#   SEED_DB=false   ← CI pipelines, staging, production

set -e

echo "=== DataPulse startup ==="

echo ">>> Running migrations..."
python manage.py migrate --noinput

if [ "${SEED_DB:-true}" = "true" ]; then
    echo ">>> Seeding database..."
    python manage.py seed_db
else
    echo ">>> Skipping seed (SEED_DB=${SEED_DB})"
fi

echo ">>> Starting server..."
exec python manage.py runserver 0.0.0.0:8000
