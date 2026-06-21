# 配置说明

所有配置均通过环境变量传入，前缀为 `HUSK_`。默认值针对"单 Docker 容器、无外部服务"场景调优。

## 存储

| 变量 | 默认值 | 说明 |
|---|---|---|
| `HUSK_DATA_DIR` | `/data` | 数据目录，建议挂载为卷以持久化 |
| `HUSK_DB_URL` | `sqlite+aiosqlite:////data/husk.db` | 可切换为 `postgresql+asyncpg://...` 使用 Postgres |

## HTTP

| 变量 | 默认值 |
|---|---|
| `HUSK_LISTEN_HOST` | `0.0.0.0` |
| `HUSK_LISTEN_PORT` | `8000` |
| `HUSK_LOG_LEVEL` | `info` |

## Docker

| 变量 | 默认值 |
|---|---|
| `HUSK_DOCKER_HOST` | `unix:///var/run/docker.sock` |
| `HUSK_DEFAULT_NETWORK` | `bridge` |
| `HUSK_DEFAULT_IMAGE` | `python:3.12` |

## Daemon

| 变量 | 默认值 |
|---|---|
| `HUSK_DAEMON_BIN` | `/app/embedded/daemon-amd64` |
| `HUSK_DAEMON_PORT` | `8080` |
| `HUSK_DAEMON_TARGET` | `/opt/husk/daemon` |

## 定时任务

| 变量 | 默认值 |
|---|---|
| `HUSK_AUTO_STOP_ENABLED` | `true` |
| `HUSK_AUTO_STOP_CHECK_INTERVAL` | `30`（秒） |
| `HUSK_REAPER_INTERVAL` | `60`（秒） |

## 认证

| 变量 | 默认值 | 说明 |
|---|---|---|
| `HUSK_ADMIN_USERNAME` | `admin` | Dashboard 登录用户名 |
| `HUSK_ADMIN_PASSWORD` | — | **必须设置**。Dashboard 登录密码，未设置时启动会报错 |
| `HUSK_PREVIEW_JWT_SECRET` | （自动生成） | 多实例部署时请持久化该值 |
