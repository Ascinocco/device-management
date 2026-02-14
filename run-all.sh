#!/usr/bin/env bash
# Run all services and the worker in parallel with prefixed logs.
# From repo root: ./run-all.sh  (or: make run)
# Requires: pnpm, uv

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Dependency checks ───────────────────────────────────────────
for cmd in pnpm uv node; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not found in PATH" >&2
    exit 1
  fi
done

# ── Graceful shutdown ───────────────────────────────────────────
PIDS=()

cleanup() {
  echo ""
  echo "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  echo "All services stopped."
}

trap cleanup SIGINT SIGTERM EXIT

# ── Helpers ─────────────────────────────────────────────────────
run_prefixed() {
  local label="$1"
  shift
  ("$@") 2>&1 | sed "s/^/[$label] /" &
  PIDS+=($!)
}

cd "$ROOT"

# ── Start services ──────────────────────────────────────────────
run_prefixed "api-gateway"     bash -c 'cd api-gateway     && pnpm exec tsx src/main.ts'
run_prefixed "device-service"  bash -c 'cd device-service  && uv run dev'
run_prefixed "device-ui"       bash -c 'cd device-ui       && pnpm run dev'
run_prefixed "device-worker"   bash -c 'cd device-worker   && PYTHONUNBUFFERED=1 uv run python -m worker.main'
run_prefixed "tenancy-service" bash -c 'cd tenancy-service && pnpm run start:dev'

wait
