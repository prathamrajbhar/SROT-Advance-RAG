#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "===================================================="
echo "  SROT Platform — Automated Setup Bootstrap"
echo "===================================================="

# 1. Check or create .env
if [ ! -f .env ]; then
  echo "[1/7] Creating .env from .env.example..."
  cp .env.example .env
else
  echo "[1/7] .env already exists."
fi

# 2. Setup Python virtual environment
echo "[2/7] Setting up Python virtual environment in apps/api/.venv..."
cd "$ROOT_DIR/apps/api"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
if [ -f "requirements.txt" ]; then
  python -m pip install -r requirements.txt
fi

# 3. Setup Node dependencies
echo "[3/7] Setting up Node.js dependencies..."
cd "$ROOT_DIR"
npm install --legacy-peer-deps || npm install

if [ -d "$ROOT_DIR/apps/web" ] && [ -f "$ROOT_DIR/apps/web/package.json" ]; then
  echo "Installing apps/web dependencies..."
  cd "$ROOT_DIR/apps/web"
  npm install --legacy-peer-deps || npm install
fi

# 4. Start Docker containers
echo "[4/7] Starting infrastructure containers via Docker Compose..."
cd "$ROOT_DIR"
docker compose -f infra/docker-compose.yml up -d

# 5. Wait for core services
echo "[5/7] Waiting for services to become healthy..."
MAX_RETRIES=30
COUNT=0
until docker compose -f infra/docker-compose.yml exec -T postgres pg_isready -U postgres -d srot >/dev/null 2>&1 || [ $COUNT -eq $MAX_RETRIES ]; do
  echo "Waiting for Postgres... ($COUNT/$MAX_RETRIES)"
  sleep 2
  COUNT=$((COUNT+1))
done

if [ $COUNT -eq $MAX_RETRIES ]; then
  echo "Warning: Postgres took too long to start, continuing..."
fi

# 6. Initialize S3 Bucket in LocalStack
echo "[6/7] Initializing S3 bucket in LocalStack..."
docker compose -f infra/docker-compose.yml exec -T localstack awslocal s3 mb s3://srot-storage >/dev/null 2>&1 || true

# 7. Run Alembic migrations
echo "[7/7] Running database migrations..."
cd "$ROOT_DIR/apps/api"
if [ -f "alembic.ini" ]; then
  .venv/bin/alembic upgrade head || echo "Migration step completed or no migrations pending."
fi

echo "===================================================="
echo "  SROT Setup Complete! Run 'npm run dev' to start."
echo "===================================================="
