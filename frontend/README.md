# Husk Dashboard

React + Vite + TanStack Router + Tailwind v4. Built into `../husk/static/dashboard/`
so the backend image serves it directly.

## Setup

```bash
pnpm install
pnpm dev          # http://localhost:5173 (proxies /api and /preview to localhost:8000)
pnpm build        # outputs to ../husk/static/dashboard/
pnpm gen:api      # regenerate OpenAPI types from a running backend
```

## Status

Scaffold only. Real UI lands in Phase 1.5 (M5.1 – M5.7) — see `../PLAN.md` §5.5.
