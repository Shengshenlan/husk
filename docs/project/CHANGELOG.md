# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

## [0.5.0] — Phase 2: 100% MIT runtime

### Added
- **Husk daemon** (`daemon/`): MIT-licensed Go reimplementation of the
  toolbox API. Replaces the upstream Daytona daemon (AGPL) entirely.
  - 13 endpoints covering files, process execution, code execution
  - ~7.9 MB stripped static Go binary, no glibc dependency
  - amd64 + arm64 cross-compiled
- Dockerfile now builds the daemon from source as part of the image.
- End-to-end verified: control plane → docker run → daemon injection →
  toolbox proxy → daemon executes Python / shell inside sandbox.

### Changed
- NOTICE: upstream daemon mentioned only as an optional compatibility fallback.

## [0.3.0] — Phase 1.7: SDK auto-generation

### Added
- `sdks/python/husk_client/_generated/`: full OpenAPI-generated Python client.
- `sdks/typescript/src/_generated/schemas.ts`: full TypeScript path/operation types.
- `scripts/gen-sdk-clients.sh`: one-command regeneration from running server or
  offline OpenAPI dump.
- `attrs` runtime dependency (used by generated Python client).

## [0.2.0] — Phase 1.5: Web Dashboard

### Added
- React 18 + Vite 5 + TanStack Query single-page dashboard.
- Pages: Sandboxes (list, create, detail, start/stop/destroy), Snapshots
  (pull image, delete), API Keys (create with one-time plaintext, revoke),
  Settings.
- localStorage-based API key auth.
- Built into `husk/static/dashboard/` and served by the backend at `/`.
- Single-port deployment (port 8000): `/` = dashboard, `/api` = REST.

## [0.1.0] — Phase 1: M1-M5 control plane

### Added
- **M1** Sandbox lifecycle: create → docker run → daemon inject → started.
  start / stop / destroy / resize / commit-to-snapshot. Explicit state
  machine. Hardening defaults (cap_drop=ALL, no-new-privileges).
- **M1** API Key with argon2 hashing, prefix-indexed verification, root
  bootstrap (env var or auto-generated on first run).
- **M1** CLI: `husk sandbox new/list/get/start/stop/rm`, `husk apikey
  list/create/revoke`, `husk serve`, `husk version`.
- **M2** Toolbox HTTP/WS reverse proxy `/api/toolbox/{id}/*`.
- **M2** Preview signed URLs `/preview/{jwt}/*` with HS256 + DB-backed revocation.
- **M3** Snapshot pull (real `docker pull`) + DB tracking + `get_or_pull`
  resolution from SandboxService.create.
- **M3** Auto-stop scheduler: stops idle sandboxes when `last_activity_at`
  exceeds `auto_stop_interval`.
- **M4** Reaper: reconciles DB ↔ docker ps each tick (orphans removed,
  phantoms marked).
- **M5** Volume CRUD (Docker named volumes 1:1).
- **M5** Docker image: multi-stage build (frontend, daemon, runtime),
  ~278 MB, single port, single volume, single env var to start.
- **M5** Stub endpoints `/api/users/me`, `/api/organizations`, `/api/config`
  for upstream Daytona SDK compatibility.

### Tech
- Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 async, alembic, pydantic v2
- Feature-first project layout (per zhanymkanov/fastapi-best-practices)
- 45+ unit tests, 3 real-Docker integration tests, all green
- ruff clean, pytest config, GitHub Actions test/build/release workflows

### License
- Source: MIT
- Runtime (v0.5+): 100% MIT
- Runtime (v0.1 – v0.4): MIT control plane + optional AGPL daemon binary
  (HTTP-isolated, not linked)

## [Unreleased]

Future: LSP, PTY, persistent interpreter sessions, git endpoints in daemon;
Phase 3 multi-runner (no current plan).
