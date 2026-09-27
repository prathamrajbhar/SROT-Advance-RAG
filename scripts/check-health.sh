#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Checking SROT system readiness via http://localhost:8000/api/v1/ready..."
curl -s -f http://localhost:8000/api/v1/ready || {
  echo "Backend is not currently responding on http://localhost:8000"
  exit 1
}
echo ""
