#!/usr/bin/env bash
# Local dev: start the Husk backend with hot-reload, plus the frontend dev server.
# Requires: uv, pnpm, Docker daemon reachable.

set -euo pipefail

cd "$(dirname "$0")/.."

# Backend
echo "→ starting backend (uvicorn :8000, --reload)"
uv run husk serve --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

# Frontend
if [[ -d frontend/node_modules ]]; then
  echo "→ starting frontend (vite :5173)"
  cd frontend && pnpm dev
else
  echo "  frontend/node_modules missing — run 'cd frontend && pnpm install' first"
  wait $BACKEND_PID
fi
