# syntax=docker/dockerfile:1.7

# ───── Stage 1: build the React dashboard ─────
FROM node:22-alpine AS frontend
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.8.0 --activate
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
ENV PNPM_ALLOW_BUILD_SCRIPTS=esbuild
RUN pnpm config set node-linker hoisted && \
    pnpm install --frozen-lockfile --ignore-scripts || pnpm install --ignore-scripts
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
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:$PATH"

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl iptables \
 && rm -rf /var/lib/apt/lists/*

# uv via official installer (avoids needing PyPI access for the bootstrap)
ADD https://astral.sh/uv/install.sh /tmp/uv-install.sh
RUN sh /tmp/uv-install.sh && rm /tmp/uv-install.sh

WORKDIR /app

COPY pyproject.toml uv.lock ./
# Install dependencies WITHOUT the project itself first (cacheable layer).
RUN uv sync --frozen --no-dev --no-install-project

COPY husk/ ./husk/
COPY alembic.ini README.md ./
COPY --from=frontend /app/../husk/static/dashboard ./husk/static/dashboard
COPY --from=daemon /out/daemon-amd64 /out/daemon-arm64 ./embedded/

# Now sync once more to install the project itself (using copied source).
RUN uv sync --frozen --no-dev

VOLUME ["/data"]
EXPOSE 8000

# Ensure /data exists for the SQLite file even when no volume is mounted.
RUN mkdir -p /data

# Run migrations on boot, then serve.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run husk serve --host 0.0.0.0 --port 8000"]
