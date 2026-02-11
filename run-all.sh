#!/usr/bin/env bash
# Run all services and the worker in parallel with prefixed logs.
# From repo root: ./run-all.sh  (or: make run)
# Requires: pnpm, uv. For api-gateway: pnpm add -D tsx in api-gateway if tsx is not available.

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
trap 'kill 0' EXIT

run_prefixed() {
  local label="$1"
  shift
  ("$@") 2>&1 | sed "s/^/[$label] /"
}

cd "$ROOT"

# Start each service and the web client; prefixed logs so all show in terminal.
run_prefixed "api-gateway"     bash -c 'cd api-gateway     && pnpm exec tsx src/main.ts' &
run_prefixed "device-service"  bash -c 'cd device-service  && uv run dev' &
run_prefixed "device-ui"       bash -c 'cd device-ui       && pnpm run dev' &
run_prefixed "device-worker"   bash -c 'cd device-worker   && PYTHONUNBUFFERED=1 uv run python -m worker.main' &
run_prefixed "tenancy-service" bash -c 'cd tenancy-service && pnpm run start:dev' &

wait
