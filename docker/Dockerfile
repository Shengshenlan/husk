# syntax=docker/dockerfile:1.7

# ───── Stage 1: build the React dashboard ─────
FROM node:20-alpine AS frontend
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install
COPY frontend/ .
# Output goes into the path the backend will mount as static.
RUN pnpm build

# ───── Stage 2: extract the upstream Daytona daemon binary ─────
# Phase 1: Husk runs the upstream AGPL-3.0 daemon binary inside sandbox
# containers. Husk source code is MIT; HTTP isolation keeps them separate.
# See NOTICE for details.
FROM alpine AS daemon
RUN apk add --no-cache ca-certificates
WORKDIR /out
# In CI we cross-arch this; locally pull whatever the host has.
ARG UPSTREAM_DAEMON_IMAGE=daytonaio/daemon:latest
# (Real binary extraction is done by scripts/pull-upstream-daemon.sh in CI;
# this stage is a placeholder so the layout is correct.)
RUN echo "placeholder" > daemon-amd64 && echo "placeholder" > daemon-arm64

# ───── Stage 3: runtime ─────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HUSK_DATA_DIR=/data \
    HUSK_DB_URL=sqlite+aiosqlite:////data/husk.db \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl iptables \
 && rm -rf /var/lib/apt/lists/*

# Install uv for fast deps install
RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY husk/ ./husk/
COPY alembic.ini ./
COPY --from=frontend /app/../husk/static/dashboard ./husk/static/dashboard
COPY --from=daemon /out/daemon-amd64 /out/daemon-arm64 ./embedded/

VOLUME ["/data"]
EXPOSE 8000

# Run migrations on boot, then serve.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run husk serve --host 0.0.0.0 --port 8000"]
