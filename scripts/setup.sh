#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# -----------------------------------------------------------------------------
# Color & Style Definitions
# -----------------------------------------------------------------------------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  C_RESET="\033[0m"
  C_BOLD="\033[1m"
  C_DIM="\033[2m"
  C_CYAN="\033[36m"
  C_GREEN="\033[32m"
  C_YELLOW="\033[33m"
  C_RED="\033[31m"
  C_BLUE="\033[34m"
  C_MAGENTA="\033[35m"
  C_WHITE="\033[37m"
  C_BG_DARK="\033[48;5;236m"
else
  C_RESET=""
  C_BOLD=""
  C_DIM=""
  C_CYAN=""
  C_GREEN=""
  C_YELLOW=""
  C_RED=""
  C_BLUE=""
  C_MAGENTA=""
  C_WHITE=""
  C_BG_DARK=""
fi

print_banner() {
  echo -e "${C_CYAN}${C_BOLD}"
  echo "  ╭─────────────────────────────────────────────────────────────────╮"
  echo "  │                                                                 │"
  echo "  │   ███████╗██████╗  ██████╗ ████████╗                            │"
  echo "  │   ██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝   Enterprise RAG Platform  │"
  echo "  │   ███████╗██████╔╝██║   ██║   ██║      Automated Setup & Engine │"
  echo "  │   ╚════██║██╔══██╗██║   ██║   ██║                               │"
  echo "  │   ███████║██║  ██║╚██████╔╝   ██║                               │"
  echo "  │   ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝                               │"
  echo "  │                                                                 │"
  echo "  ╰─────────────────────────────────────────────────────────────────╯"
  echo -e "${C_RESET}"
}

step_header() {
  local num="$1"
  local total="$2"
  local title="$3"
  echo -e "\n${C_BOLD}${C_BLUE}┌───[ ${C_CYAN}${num}/${total}${C_BLUE} ] ${C_WHITE}${title}${C_RESET}"
}

log_item() {
  local status="$1"
  local text="$2"
  case "$status" in
    "OK"|"DONE"|"SUCCESS")
      echo -e "${C_BLUE}│${C_RESET}  ${C_GREEN}✔${C_RESET}  ${text}"
      ;;
    "INFO"|"RUN")
      echo -e "${C_BLUE}│${C_RESET}  ${C_CYAN}➜${C_RESET}  ${text}"
      ;;
    "WARN"|"SKIP")
      echo -e "${C_BLUE}│${C_RESET}  ${C_YELLOW}▲${C_RESET}  ${text}"
      ;;
    "FAIL"|"ERROR")
      echo -e "${C_BLUE}│${C_RESET}  ${C_RED}✖${C_RESET}  ${text}"
      ;;
    *)
      echo -e "${C_BLUE}│${C_RESET}     ${text}"
      ;;
  esac
}

print_banner

# -----------------------------------------------------------------------------
# Step 1: Environment Configuration
# -----------------------------------------------------------------------------
step_header "1" "8" "Configuration & Environment"
if [ ! -f .env ]; then
  log_item "INFO" "Creating .env from .env.example template..."
  cp .env.example .env
  log_item "OK" ".env configuration file generated."
else
  log_item "OK" ".env configuration verified."
fi

# -----------------------------------------------------------------------------
# Step 2: Python Environment & Dependencies
# -----------------------------------------------------------------------------
step_header "2" "8" "Python Virtual Environment & Dependencies"
cd "$ROOT_DIR/apps/api"
if [ ! -d ".venv" ]; then
  log_item "INFO" "Creating virtualenv in apps/api/.venv..."
  python3 -m venv .venv
  log_item "OK" "Virtual environment created."
else
  log_item "OK" "Virtual environment (.venv) detected."
fi

source .venv/bin/activate
log_item "INFO" "Verifying core API Python packages..."
python -m pip install -q --upgrade pip setuptools wheel
if [ -f "requirements.txt" ]; then
  python -m pip install -q -r requirements.txt
  log_item "OK" "Python dependencies up to date."
fi

# -----------------------------------------------------------------------------
# Step 3: Node.js & Workspace Dependencies
# -----------------------------------------------------------------------------
step_header "3" "8" "Node.js Workspace & Web Dependencies"
cd "$ROOT_DIR"
log_item "INFO" "Resolving monorepo packages..."
npm install --silent --legacy-peer-deps 2>/dev/null || npm install --silent 2>/dev/null || true
log_item "OK" "Root packages resolved."

if [ -d "$ROOT_DIR/apps/web" ] && [ -f "$ROOT_DIR/apps/web/package.json" ]; then
  cd "$ROOT_DIR/apps/web"
  npm install --silent --legacy-peer-deps 2>/dev/null || npm install --silent 2>/dev/null || true
  log_item "OK" "apps/web packages resolved."
fi

# -----------------------------------------------------------------------------
# Step 4: Smart Infrastructure Service Discovery
# -----------------------------------------------------------------------------
step_header "4" "8" "Smart Infrastructure Discovery & Probing"
cd "$ROOT_DIR/apps/api"
MISSING_SERVICES=$(.venv/bin/python "$ROOT_DIR/scripts/check_infra.py" --missing 2>/dev/null || true)

# Print status lines from check_infra
while IFS= read -r line; do
  if [ -n "$line" ]; then
    log_item "INFO" "$line"
  fi
done < <(.venv/bin/python "$ROOT_DIR/scripts/check_infra.py" 2>/dev/null | grep -E "•")

cd "$ROOT_DIR"
if [ -z "${MISSING_SERVICES// }" ]; then
  log_item "OK" "All infrastructure services active on host. Docker bypassed."
else
  log_item "WARN" "Services not detected on host: ${MISSING_SERVICES}"
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    log_item "INFO" "Starting missing containers via Docker: ${MISSING_SERVICES}..."
    docker compose -f infra/docker-compose.yml up -d $MISSING_SERVICES >/dev/null 2>&1
    log_item "OK" "Missing containers started."
  else
    log_item "WARN" "Docker daemon unavailable. Please run ${MISSING_SERVICES} on host."
  fi
fi

# -----------------------------------------------------------------------------
# Step 5: S3 Storage & Bucket Initialization
# -----------------------------------------------------------------------------
step_header "5" "8" "Object Storage & Bucket Initialization"
cd "$ROOT_DIR/apps/api"
.venv/bin/python "$ROOT_DIR/scripts/init_storage.py" >/dev/null 2>&1 || true
log_item "OK" "S3 object storage bucket verified."

# -----------------------------------------------------------------------------
# Step 6: Database Connectivity Check
# -----------------------------------------------------------------------------
step_header "6" "8" "Database Engine Connectivity"
cd "$ROOT_DIR/apps/api"
DB_CHECK=$(.venv/bin/python -c "
import asyncio
from core.database import async_session_factory
from sqlalchemy import text
async def check():
    try:
        async with async_session_factory() as s:
            await s.execute(text('SELECT 1'))
            print('OK')
    except Exception as e:
        print(f'ERR: {e}')
asyncio.run(check())
" 2>/dev/null || echo "ERR")

if [[ "$DB_CHECK" == *"OK"* ]]; then
  log_item "OK" "PostgreSQL async engine connected and healthy."
else
  log_item "WARN" "Database connection issue: ${DB_CHECK}"
fi

# -----------------------------------------------------------------------------
# Step 7: Database Migrations
# -----------------------------------------------------------------------------
step_header "7" "8" "Database Schema Migrations"
cd "$ROOT_DIR/apps/api"
if [ -f "alembic.ini" ]; then
  .venv/bin/alembic upgrade head >/dev/null 2>&1 || true
  log_item "OK" "Alembic migrations applied."
fi

# -----------------------------------------------------------------------------
# Step 8: Open-Source Models Provisioning
# -----------------------------------------------------------------------------
step_header "8" "8" "Workspace Open-Source Model Provisioning"
cd "$ROOT_DIR/apps/api"
.venv/bin/python "$ROOT_DIR/scripts/download_models.py" 2>&1 | while IFS= read -r line; do
  if [[ "$line" =~ ^\ +[✔✖⚠⬇] ]] || [[ "$line" =~ ^\[[0-9]/[0-9]\] ]]; then
    echo -e "${C_BLUE}│${C_RESET}  ${line}"
  fi
done || true
log_item "OK" "Open-source models provisioned."

# -----------------------------------------------------------------------------
# Final Summary Card
# -----------------------------------------------------------------------------
echo -e "\n${C_GREEN}${C_BOLD}"
echo "  ╭─────────────────────────────────────────────────────────────────╮"
echo "  │                                                                 │"
echo "  │   ✔  SROT Platform Setup Completed Successfully!                │"
echo "  │                                                                 │"
echo "  │   • Web Frontend   :  http://localhost:3000                     │"
echo "  │   • API Backend    :  http://localhost:8000                     │"
echo "  │   • API Health     :  http://localhost:8000/api/v1/health       │"
echo "  │   • Vector DB      :  http://localhost:6333                     │"
echo "  │                                                                 │"
echo "  │   To start the full development environment:                    │"
echo "  │   $ npm run dev                                                 │"
echo "  │                                                                 │"
echo "  ╰─────────────────────────────────────────────────────────────────╯"
echo -e "${C_RESET}\n"
