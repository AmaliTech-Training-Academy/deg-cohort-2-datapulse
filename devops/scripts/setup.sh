#!/bin/bash
set -e
echo "=== DataPulse Setup ==="

if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker first."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — update SECRET_KEY before deploying to production."
fi

docker compose up --build -d

echo ""
echo "Waiting for backend to be ready..."
until curl -sf http://localhost:8000/health > /dev/null; do sleep 2; done

echo ""
echo "DataPulse is running:"
echo "  Backend API : http://localhost:8000"
echo "  API Docs    : http://localhost:8000/docs"
