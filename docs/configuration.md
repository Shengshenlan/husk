# Configuration

All configuration is via environment variables, prefixed with `HUSK_`.
Defaults are tuned for "single Docker container, no external services".

## Storage

| Var | Default | Notes |
|---|---|---|
| `HUSK_DATA_DIR` | `/data` | Mount this as a volume to persist state |
| `HUSK_DB_URL` | `sqlite+aiosqlite:////data/husk.db` | Switch to `postgresql+asyncpg://...` for Postgres |

## HTTP

| Var | Default |
|---|---|
| `HUSK_LISTEN_HOST` | `0.0.0.0` |
| `HUSK_LISTEN_PORT` | `8000` |
| `HUSK_LOG_LEVEL` | `info` |

## Docker

| Var | Default |
|---|---|
| `HUSK_DOCKER_HOST` | `unix:///var/run/docker.sock` |
| `HUSK_DEFAULT_NETWORK` | `bridge` |
| `HUSK_DEFAULT_IMAGE` | `python:3.12` |

## Daemon

| Var | Default |
|---|---|
| `HUSK_DAEMON_BIN` | `/app/embedded/daemon-amd64` |
| `HUSK_DAEMON_PORT` | `8080` |
| `HUSK_DAEMON_TARGET` | `/opt/husk/daemon` |

## Schedulers

| Var | Default |
|---|---|
| `HUSK_AUTO_STOP_ENABLED` | `true` |
| `HUSK_AUTO_STOP_CHECK_INTERVAL` | `30` (seconds) |
| `HUSK_REAPER_INTERVAL` | `60` (seconds) |

## Auth

| Var | Default |
|---|---|
| `HUSK_ROOT_API_KEY` | (auto-generated on first start, printed to stdout) |
| `HUSK_PREVIEW_JWT_SECRET` | (auto-generated; persist this if running multiple replicas) |
