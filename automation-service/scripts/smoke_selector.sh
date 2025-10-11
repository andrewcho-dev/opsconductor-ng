#!/usr/bin/env bash
set -euo pipefail
INTENT="${1:-restart app}"
K="${2:-5}"
TRACE="${3:-SMOKE-LOCAL}"
docker compose exec -T automation-service \
  python -m stage_a.selector_bridge --intent "$INTENT" --k "$K" --trace-id "$TRACE"
