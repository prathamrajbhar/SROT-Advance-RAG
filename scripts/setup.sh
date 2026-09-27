#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

step() { printf '\n==> %s\n' "$1"; }

step "Environment configuration"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    created .env from .env.example"
else
  echo "    .env already present"
fi

step "Python environment"
cd "$ROOT_DIR/apps/api"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip setuptools wheel
.venv/bin/python -m pip install -q -r requirements.txt
echo "    apps/api dependencies installed"

step "Node workspace"
cd "$ROOT_DIR"
npm install --silent --legacy-peer-deps 2>/dev/null || npm install --silent
echo "    workspace dependencies installed"

step "Infrastructure"
if docker info >/dev/null 2>&1; then
  docker compose -f infra/docker-compose.yml up -d
  echo "    postgres container started"
else
  echo "    docker unavailable, expecting Postgres on the host"
fi

step "Database migrations"
cd "$ROOT_DIR/apps/api"
.venv/bin/alembic upgrade head
echo "    schema is at head"

step "Database connectivity"
.venv/bin/python -c "
import asyncio
from sqlalchemy import text
from core.database import async_session_factory

async def check():
    async with async_session_factory() as session:
        await session.execute(text('SELECT 1'))

asyncio.run(check())
"
echo "    PostgreSQL reachable"

printf '\nSetup complete.\n'
printf '  web      http://localhost:3000\n'
printf '  api      http://localhost:8000\n'
printf '  docs     http://localhost:8000/docs\n'
printf '\n  npm run dev    start both\n'
printf '  npm test       run the test suite\n'
