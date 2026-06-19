# Husk —— 项目代码结构

> 文件级别的代码布局，每个文件的职责、依赖、关键内容都列清楚。可以直接照这个 scaffold 出整个 repo。

配套阅读：
- [PLAN.md](./PLAN.md) —— 做什么、什么时候做
- [ARCHITECTURE.md](./ARCHITECTURE.md) —— 长什么样、怎么跑

**风格**：后端采用 [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) 推荐的 **feature-first** —— 每个业务域内聚到一个文件夹，跨域调用通过 service 层显式 import。

---

## 1. 顶层目录

```
husk/                              # GitHub repo 根目录（同时也是 Python 包名）
├── README.md
├── LICENSE                        # MIT
├── NOTICE                         # daemon 二进制 AGPL 声明
├── CHANGELOG.md
├── PLAN.md / ARCHITECTURE.md / CODE_STRUCTURE.md
│
├── pyproject.toml                 # 控制面工程定义（uv 管理）
├── uv.lock
├── alembic.ini                    # alembic 迁移配置
├── .python-version                # 3.12
├── .gitignore
├── .editorconfig
├── ruff.toml                      # lint 规则
│
├── husk/                          # 【后端】Python 控制面源码（详见 §2）
├── frontend/                      # 【前端】React Dashboard（详见 §3）
├── sdks/                          # 【SDK】三语言 thin client（详见 §4）
│
├── embedded/                      # 构建时打包的二进制
│   ├── daemon-amd64
│   ├── daemon-arm64
│   └── .gitignore                 # 二进制不入库（CI 拉取）
│
├── tests/                         # 后端测试（详见 §5）
├── docker/                        # 镜像构建（详见 §6）
├── scripts/                       # 工具脚本（详见 §7）
├── docs/                          # 用户文档（详见 §8）
└── .github/                       # CI / Issue 模板（详见 §9）
```

---

## 2. 后端 `husk/`（Python · FastAPI · Feature-first）

### 2.1 完整目录

```
husk/
├── __init__.py                    # 暴露 __version__
├── main.py                        # FastAPI app 装配 + 启动入口
│
├── core/                          # 【横切】跨业务的基础设施
│   ├── __init__.py
│   ├── config.py                  # pydantic-settings：环境变量 → Settings
│   ├── database.py                # async engine / Base / session factory
│   ├── docker_client.py           # docker-py 封装；唯一访问 Docker 的地方
│   ├── logging.py                 # 结构化日志配置
│   ├── exceptions.py              # 通用异常基类 + 全局 handler
│   └── deps.py                    # 通用 Depends（db_session、docker_client、settings）
│
├── auth/                          # 【域】鉴权
│   ├── __init__.py
│   ├── router.py                  # /api/api-keys/*
│   ├── models.py                  # ApiKey ORM
│   ├── schemas.py                 # CreateApiKeyRequest, ApiKeyResponse
│   ├── service.py                 # 生成 / hash / 校验 / 撤销
│   ├── repository.py
│   ├── dependencies.py            # current_apikey() FastAPI Depends
│   └── exceptions.py
│
├── sandbox/                       # 【域】沙盒（核心，文件最多）
│   ├── __init__.py
│   ├── router.py                  # /api/sandbox/*
│   ├── models.py                  # Sandbox ORM
│   ├── schemas.py                 # CreateRequest, SandboxResponse, ResizeRequest, ...
│   ├── service.py                 # 生命周期编排（create/start/stop/destroy/resize/...）
│   ├── repository.py              # SQLAlchemy 查询封装
│   ├── dependencies.py            # sandbox_service() Depends 工厂
│   ├── daemon_inject.py           # 注入 daemon 二进制 + chmod + exec
│   ├── netrules.py                # iptables / docker network 规则
│   ├── reaper.py                  # DB ↔ docker ps 对齐
│   ├── auto_stop.py               # last-activity 心跳触发停止
│   ├── exceptions.py
│   └── constants.py               # 状态枚举（CREATING/STARTED/STOPPED/...）
│
├── snapshot/                      # 【域】镜像快照
│   ├── __init__.py
│   ├── router.py                  # /api/snapshots/*
│   ├── models.py
│   ├── schemas.py
│   ├── service.py                 # pull / activate / delete
│   ├── repository.py
│   ├── dependencies.py
│   └── exceptions.py
│
├── volume/                        # 【域】卷
│   ├── __init__.py
│   ├── router.py                  # /api/volumes/*
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
│   ├── repository.py
│   └── exceptions.py
│
├── preview/                       # 【域】预览 URL
│   ├── __init__.py
│   ├── router.py                  # /preview/<token>/*  +  签发 endpoint
│   ├── service.py                 # JWT 签发 / 解析 / TTL
│   ├── proxy.py                   # 反代到容器端口
│   ├── schemas.py
│   ├── repository.py              # PreviewToken 表查询
│   ├── models.py
│   └── exceptions.py
│
├── toolbox/                       # 【域】Toolbox 反代
│   ├── __init__.py
│   ├── router.py                  # /api/toolbox/:sandboxId/*
│   ├── http_proxy.py              # httpx.AsyncClient 流式
│   └── ws_proxy.py                # 双向 WebSocket pump
│
├── stub/                          # 【域】上游兼容 stub
│   ├── __init__.py
│   └── router.py                  # /api/users/me, /api/organizations, /api/config
│
├── health/                        # 【域】健康检查
│   ├── __init__.py
│   └── router.py                  # /api/health, /api/health/ready
│
├── tasks/                         # 【横切】asyncio 周期任务
│   ├── __init__.py
│   ├── scheduler.py               # 注册 + 启停所有周期任务
│   ├── auto_stop.py               # 调 sandbox.auto_stop
│   └── reaper.py                  # 调 sandbox.reaper
│
├── cli/                           # 【横切】typer CLI
│   ├── __init__.py
│   ├── main.py                    # 顶层 typer.App
│   ├── serve.py                   # `husk serve`
│   ├── migrate.py                 # `husk migrate`
│   ├── sandbox.py                 # `husk sandbox new/list/exec/...`，调 sandbox.service
│   ├── apikey.py                  # `husk apikey create/list/revoke`，调 auth.service
│   └── version.py                 # `husk version`
│
├── migrations/                    # alembic 自动生成
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
│
└── static/                        # 嵌入资源
    ├── .gitignore                 # dashboard/ 不入库（CI 构建）
    └── dashboard/                 # ← Phase 1.5：前端 build 产物注入处
        └── (build 产物)
```

### 2.2 每个业务域的标准 6-8 件套

每个 feature 文件夹按需有这些文件，没用到的就不建：

| 文件 | 职责 | 是否必需 |
|---|---|---|
| `router.py` | FastAPI APIRouter，所有 endpoint | ✅ 必需 |
| `schemas.py` | pydantic 输入输出模型 | ✅ 必需 |
| `service.py` | 业务逻辑（不知道 HTTP） | ✅ 必需 |
| `models.py` | SQLAlchemy ORM | △ 大多需要 |
| `repository.py` | DB 查询封装 | △ 大多需要 |
| `dependencies.py` | FastAPI Depends 工厂 | △ 视情况 |
| `exceptions.py` | 域专有异常 | △ 视情况 |
| `constants.py` | 状态枚举、固定值 | △ 视情况 |

业务域内可以再加专门子模块（如 sandbox 的 `daemon_inject.py`、`netrules.py`、`reaper.py`），不强制。

### 2.3 跨域依赖规则

```
sandbox/router.py     ──→  sandbox/service.py             ✅ 同域内 router→service
sandbox/router.py     ──→  sandbox/repository.py          ✗ router 永远不直连 DB
sandbox/service.py    ──→  snapshot/service.py            ✅ 跨域必须走对方 service
sandbox/service.py    ──→  snapshot/repository.py         ✗ 不允许跨域读对方 DB
任何域                ──→  core/*                         ✅ 共享基础设施
core/*                ──→  任何域                          ✗ 基础设施不知道业务
cli/sandbox.py        ──→  sandbox/service.py             ✅ 横切复用 service
tasks/auto_stop.py    ──→  sandbox/service.py             ✅ 同上
```

**核心原则**：
1. router 永远只调本域 service
2. 跨域只走对方 service，不读对方 DB
3. service 之间允许互调，依赖在 dependencies.py 里组装

### 2.4 关键文件示例

#### `husk/main.py`（应用装配，~60 行）

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from husk import __version__
from husk.core.database import init_db
from husk.tasks.scheduler import start_scheduler, stop_scheduler

from husk.auth.router      import router as auth_router
from husk.sandbox.router   import router as sandbox_router
from husk.snapshot.router  import router as snapshot_router
from husk.volume.router    import router as volume_router
from husk.toolbox.router   import router as toolbox_router
from husk.preview.router   import router as preview_router
from husk.stub.router      import router as stub_router
from husk.health.router    import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler = await start_scheduler()
    yield
    await stop_scheduler(scheduler)


app = FastAPI(title="Husk", version=__version__, lifespan=lifespan)

app.include_router(auth_router,     prefix="/api/api-keys", tags=["auth"])
app.include_router(sandbox_router,  prefix="/api/sandbox",  tags=["sandbox"])
app.include_router(snapshot_router, prefix="/api/snapshots", tags=["snapshot"])
app.include_router(volume_router,   prefix="/api/volumes",  tags=["volume"])
app.include_router(toolbox_router,  prefix="/api/toolbox",  tags=["toolbox"])
app.include_router(preview_router,  prefix="/preview",      tags=["preview"])
app.include_router(stub_router,     prefix="/api",          tags=["compat"])
app.include_router(health_router,   prefix="/api/health",   tags=["health"])

app.mount("/", StaticFiles(directory="husk/static/dashboard", html=True))
```

#### `husk/core/config.py`（环境变量，~40 行）

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUSK_")

    data_dir: str = "/data"
    db_url: str = "sqlite+aiosqlite:////data/husk.db"
    listen_host: str = "0.0.0.0"
    listen_port: int = 8000
    log_level: str = "info"

    docker_host: str = "unix:///var/run/docker.sock"
    default_network: str = "bridge"
    default_image: str = "python:3.12"

    daemon_bin: str = "/app/embedded/daemon-amd64"
    daemon_port: int = 8080
    daemon_target: str = "/opt/husk/daemon"

    auto_stop_enabled: bool = True
    auto_stop_check_interval: int = 30
    reaper_interval: int = 60

    root_api_key: str | None = None
    preview_jwt_secret: str | None = None  # 启动时若未设则自动生成


settings = Settings()
```

#### `husk/core/deps.py`（通用 Depends 工厂）

```python
from typing import AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings, Settings
from .database import session_factory
from .docker_client import DockerClient


def get_settings() -> Settings:
    return settings


async def db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


_docker_singleton: DockerClient | None = None


def docker_client(s: Settings = Depends(get_settings)) -> DockerClient:
    global _docker_singleton
    if _docker_singleton is None:
        _docker_singleton = DockerClient(s.docker_host)
    return _docker_singleton
```

#### `husk/sandbox/router.py`（HTTP 入口）

```python
from fastapi import APIRouter, Depends, status

from husk.auth.dependencies import current_apikey

from .schemas import CreateRequest, SandboxResponse, ResizeRequest
from .service import SandboxService
from .dependencies import sandbox_service


router = APIRouter(dependencies=[Depends(current_apikey)])


@router.post("", response_model=SandboxResponse, status_code=status.HTTP_201_CREATED)
async def create_sandbox(
    body: CreateRequest,
    service: SandboxService = Depends(sandbox_service),
):
    sb = await service.create(body)
    return SandboxResponse.model_validate(sb)


@router.get("", response_model=list[SandboxResponse])
async def list_sandboxes(service: SandboxService = Depends(sandbox_service)):
    return [SandboxResponse.model_validate(s) for s in await service.list()]


@router.get("/{sandbox_id}", response_model=SandboxResponse)
async def get_sandbox(sandbox_id: str, service: SandboxService = Depends(sandbox_service)):
    return SandboxResponse.model_validate(await service.get(sandbox_id))


@router.post("/{sandbox_id}/start", response_model=SandboxResponse)
async def start_sandbox(...): ...

@router.post("/{sandbox_id}/stop", response_model=SandboxResponse)
async def stop_sandbox(...): ...

@router.delete("/{sandbox_id}", status_code=204)
async def delete_sandbox(...): ...
```

#### `husk/sandbox/service.py`（业务核心）

```python
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient
from husk.snapshot.service import SnapshotService    # 跨域 import 显式

from . import models, schemas, exceptions
from .repository import SandboxRepository
from .daemon_inject import inject_daemon


class SandboxService:
    def __init__(
        self,
        db: AsyncSession,
        docker: DockerClient,
        snapshots: SnapshotService,
    ):
        self._repo = SandboxRepository(db)
        self._docker = docker
        self._snapshots = snapshots

    async def create(self, req: schemas.CreateRequest) -> models.Sandbox:
        snapshot = await self._snapshots.get_or_pull(req.snapshot_id)
        sandbox = await self._repo.insert(
            state="creating", cpu=req.cpu, memory_mb=req.memory_mb, ...
        )
        try:
            container = await self._docker.run(
                image=snapshot.image_ref, cpu=req.cpu, mem=req.memory_mb
            )
            await inject_daemon(container)
            await self._wait_daemon_ready(container)
            return await self._repo.update(
                sandbox.id, container_id=container.id, state="started"
            )
        except Exception as e:
            await self._repo.update(sandbox.id, state="error")
            raise exceptions.SandboxCreateFailed() from e
```

#### `husk/sandbox/dependencies.py`（DI 组装）

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.deps import db_session, docker_client
from husk.core.docker_client import DockerClient
from husk.snapshot.dependencies import snapshot_service
from husk.snapshot.service import SnapshotService

from .service import SandboxService


async def sandbox_service(
    db: AsyncSession = Depends(db_session),
    docker: DockerClient = Depends(docker_client),
    snapshots: SnapshotService = Depends(snapshot_service),
) -> SandboxService:
    return SandboxService(db, docker, snapshots)
```

#### `husk/sandbox/models.py`（ORM）

```python
from datetime import datetime
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base


class Sandbox(Base):
    __tablename__ = "sandbox"

    id:               Mapped[str] = mapped_column(String, primary_key=True)
    name:             Mapped[str] = mapped_column(String, unique=True)
    snapshot_id:      Mapped[str | None]
    container_id:     Mapped[str | None]
    state:            Mapped[str]
    cpu:              Mapped[int]
    memory_mb:        Mapped[int]
    disk_gb:          Mapped[int]
    labels:           Mapped[dict] = mapped_column(JSON, default=dict)
    runner_id:        Mapped[str] = mapped_column(String, default="default")
    region:           Mapped[str] = mapped_column(String, default="default")
    auto_stop_interval: Mapped[int | None]
    last_activity_at: Mapped[datetime | None]
    created_at:       Mapped[datetime]
    updated_at:       Mapped[datetime]
```

---

## 3. 前端 `frontend/`（React + Vite）

### 3.1 完整目录

```
frontend/
├── package.json
├── pnpm-lock.yaml
├── vite.config.ts                 # 关键：proxy /api → localhost:8000 (dev)
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.cjs
├── eslint.config.js
├── .prettierrc
├── index.html
│
├── public/                        # 不经构建的静态资源
│   ├── favicon.svg
│   └── logo.svg
│
├── src/
│   ├── main.tsx                   # ReactDOM.createRoot 入口
│   ├── App.tsx                    # Router + Providers (QueryClient, Theme)
│   ├── env.d.ts                   # Vite import.meta.env 类型
│   │
│   ├── routes/                    # 页面（TanStack Router 文件路由）
│   │   ├── __root.tsx             # 根布局：侧边栏 + 顶部 + Outlet
│   │   ├── index.tsx              # 重定向 → /sandboxes
│   │   ├── login.tsx              # API Key 输入页
│   │   ├── sandboxes/
│   │   │   ├── index.tsx          # 列表页
│   │   │   ├── new.tsx            # 创建表单
│   │   │   └── $id.tsx            # 详情（含 5 Tab 子路由）
│   │   ├── snapshots.tsx          # Snapshot 列表 + Pull
│   │   ├── api-keys.tsx           # API Key 管理
│   │   └── settings.tsx           # 设置 + 关于
│   │
│   ├── components/
│   │   ├── ui/                    # shadcn/ui 复制的组件（Button、Dialog、Table...）
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── sandbox/
│   │   │   ├── SandboxTable.tsx
│   │   │   ├── SandboxStateBadge.tsx
│   │   │   ├── ResourcePicker.tsx
│   │   │   └── ActionButtons.tsx
│   │   ├── terminal/
│   │   │   └── Terminal.tsx       # xterm.js 组件 + WS 集成
│   │   ├── files/
│   │   │   ├── FileTree.tsx
│   │   │   └── FileViewer.tsx
│   │   ├── logs/
│   │   │   └── LogStream.tsx
│   │   └── common/
│   │       ├── ConfirmDialog.tsx
│   │       ├── EmptyState.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── hooks/                     # TanStack Query 包装
│   │   ├── useSandboxes.ts        # list / get / create / start / stop / delete
│   │   ├── useSnapshots.ts
│   │   ├── useApiKeys.ts
│   │   ├── useToolbox.ts          # 通过 /api/toolbox/:id/* 反代调用
│   │   └── useTerminal.ts         # PTY WebSocket
│   │
│   ├── api/
│   │   ├── _generated/            # 自动生成自 OpenAPI（不要手改）
│   │   │   ├── client.ts
│   │   │   ├── schemas.ts
│   │   │   └── README.md          # "运行 pnpm gen:api 重新生成"
│   │   ├── client.ts              # 包装：注入 Auth header、错误转换
│   │   └── ws.ts                  # WebSocket helper
│   │
│   ├── lib/
│   │   ├── auth.ts                # API Key localStorage 读写
│   │   ├── format.ts              # bytes / duration / state → text
│   │   ├── time.ts                # relative time（"2 minutes ago"）
│   │   └── cn.ts                  # tailwind 合并 helper
│   │
│   ├── stores/                    # Zustand（仅当 TanStack Query 不够用）
│   │   └── theme.ts
│   │
│   └── styles/
│       └── globals.css            # Tailwind v4 入口
│
└── tests/
    ├── setup.ts
    ├── routes/
    │   └── login.test.tsx
    └── components/
        └── SandboxTable.test.tsx
```

### 3.2 vite.config.ts 关键片段

```typescript
export default defineConfig({
  plugins: [react(), tailwindcss(), TanStackRouterVite()],
  server: {
    proxy: {
      '/api':     { target: 'http://localhost:8000', ws: true, changeOrigin: true },
      '/preview': { target: 'http://localhost:8000', ws: true, changeOrigin: true },
    },
  },
  build: {
    outDir: '../husk/static/dashboard',  // ← 直接 build 到后端的静态目录
    emptyOutDir: true,
  },
})
```

### 3.3 一键脚本（package.json）

```json
{
  "scripts": {
    "dev":     "vite",
    "build":   "tsc -b && vite build",
    "lint":    "eslint .",
    "format":  "prettier --write .",
    "test":    "vitest",
    "gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/_generated/schemas.ts"
  }
}
```

---

## 4. SDK `sdks/`（Python · TypeScript · Go）

### 4.1 总目录

```
sdks/
├── README.md                      # 三种语言的选哪个、quickstart 链接
├── python/                        # PyPI: husk-client
├── typescript/                    # npm: @husk/client
└── go/                            # Go modules: github.com/<org>/husk-go
```

### 4.2 `sdks/python/`

```
sdks/python/
├── pyproject.toml
├── README.md                      # quickstart + API 概览
├── LICENSE                        # MIT
├── husk_client/
│   ├── __init__.py                # 导出 Client, AuthenticatedClient, sync_get, ...
│   ├── _generated/                # 由 scripts/gen-sdk-clients.sh 生成
│   │   ├── api/
│   │   │   ├── sandbox/           # create_sandbox.py, list_sandboxes.py, ...
│   │   │   ├── snapshot/
│   │   │   └── ...
│   │   ├── models/                # CreateSandboxRequest.py, ...
│   │   ├── client.py              # AuthenticatedClient
│   │   └── README.md              # "Auto-generated. Do not edit."
│   └── ergonomic.py               # Phase 2.x 手写高层 API 占位
├── examples/
│   └── quickstart.py
└── tests/
    └── test_quickstart.py         # 起 Husk testcontainer，跑端到端
```

### 4.3 `sdks/typescript/`

```
sdks/typescript/
├── package.json
├── tsconfig.json
├── tsup.config.ts                 # build → cjs + esm + d.ts
├── README.md
├── LICENSE
├── src/
│   ├── index.ts                   # createClient export
│   ├── _generated/
│   │   ├── schemas.d.ts           # openapi-typescript 输出
│   │   └── README.md
│   ├── client.ts                  # 包装 createClient + auth
│   └── ergonomic.ts               # Phase 2.x 占位
├── examples/
│   └── quickstart.ts
└── tests/
    └── quickstart.test.ts
```

### 4.4 `sdks/go/`

```
sdks/go/
├── go.mod                         # module github.com/<org>/husk-go
├── go.sum
├── README.md
├── LICENSE
├── client/
│   ├── _generated/                # oapi-codegen 输出
│   │   ├── client.gen.go
│   │   └── types.gen.go
│   ├── client.go                  # 包装 NewClient + auth
│   └── doc.go
├── examples/
│   └── quickstart/
│       └── main.go
└── tests/
    └── client_test.go
```

---

## 5. 测试 `tests/`（feature-first，与 husk/ 镜像同构）

```
tests/
├── conftest.py                    # 全局 fixtures：app / db / docker / api_key
│
├── unit/                          # 单元测试，秒级
│   ├── auth/
│   │   ├── test_service.py
│   │   └── test_dependencies.py
│   ├── sandbox/
│   │   ├── test_service.py
│   │   ├── test_repository.py
│   │   ├── test_daemon_inject.py
│   │   └── test_auto_stop.py
│   ├── snapshot/
│   │   └── test_service.py
│   ├── volume/
│   │   └── test_service.py
│   ├── preview/
│   │   ├── test_service.py        # JWT 签发解析
│   │   └── test_proxy.py
│   ├── toolbox/
│   │   ├── test_http_proxy.py
│   │   └── test_ws_proxy.py
│   └── core/
│       ├── test_docker_client.py  # Mock Docker SDK
│       └── test_config.py
│
├── integration/                   # testcontainers：真起 Docker、起 Husk
│   ├── conftest.py
│   ├── test_sandbox_lifecycle.py    # create → start → exec → stop → destroy
│   ├── test_toolbox_e2e.py          # 真起 daemon，调 /files
│   ├── test_pty_websocket.py
│   └── test_preview_url.py
│
└── compat/                        # 上游 SDK 兼容性验收
    ├── test_daytona_sdk_python.py    # 用 daytona-sdk-python 跑 quickstart
    └── test_daytona_sdk_typescript.spec.ts
```

测试目录结构与 `husk/` 镜像同构 —— 改一个域时所有相关测试一起改。

测试运行：

```bash
uv run pytest tests/unit/         # 单元，秒级
uv run pytest tests/integration/  # 集成，分钟级（要 Docker）
uv run pytest tests/compat/       # 兼容，分钟级
```

---

## 6. Docker `docker/`

```
docker/
├── Dockerfile                     # 多阶段构建：前端 + daemon + python
├── compose.dev.yaml               # 开发：源码挂载、热重载
├── compose.example.yaml           # 用户参考用
└── entrypoint.sh                  # 启动前 alembic upgrade，然后 husk serve
```

### Dockerfile 多阶段示意

```dockerfile
# Stage 1: build frontend
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm build                       # 输出到 ../husk/static/dashboard

# Stage 2: extract upstream daemon
FROM alpine AS daemon
RUN apk add --no-cache curl
COPY scripts/pull-upstream-daemon.sh /pull.sh
RUN /pull.sh                          # 输出 daemon-amd64, daemon-arm64

# Stage 3: runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev
COPY husk/ ./husk/
COPY --from=frontend /app/dist ./husk/static/dashboard
COPY --from=daemon /out/ ./embedded/
COPY docker/entrypoint.sh /entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["husk", "serve"]
```

---

## 7. 脚本 `scripts/`

```
scripts/
├── pull-upstream-daemon.sh        # docker pull → cp → 输出 daemon-amd64/arm64
├── gen-sdk-clients.sh             # 三种语言 SDK 一键生成
├── gen-frontend-client.sh         # 前端 TS schema 生成
├── build-image.sh                 # 本地构建 husk:dev 镜像
├── release.sh                     # 本地手动发版（CI 平时用）
└── dev.sh                         # 开发联调：起后端 + 前端 watch
```

`gen-sdk-clients.sh` 关键行：

```bash
# Python
openapi-python-client generate --url http://localhost:8000/openapi.json \
    --output-path sdks/python/husk_client/_generated --overwrite

# TypeScript
openapi-typescript http://localhost:8000/openapi.json \
    -o sdks/typescript/src/_generated/schemas.d.ts

# Go
oapi-codegen -package generated -generate types,client \
    -o sdks/go/client/_generated/client.gen.go \
    http://localhost:8000/openapi.json
```

---

## 8. 文档 `docs/`

```
docs/
├── getting-started.md             # 5 分钟跑通 quickstart
├── installation.md                # Docker / 源码 / Helm
├── configuration.md               # 环境变量大全
├── api.md                         # Husk OpenAPI 渲染（Redoc）
├── compatibility.md               # 与上游 daytona SDK 兼容矩阵
├── upgrade-from-daytona.md        # 上游用户迁移指南
├── security.md                    # 安全模型 + 部署建议
├── architecture.md                # = ../ARCHITECTURE.md 的精简版
├── sdks/
│   ├── python.md
│   ├── typescript.md
│   └── go.md
└── faq.md
```

---

## 9. CI `.github/`

```
.github/
├── workflows/
│   ├── test.yml                   # PR：lint + pytest unit + frontend test
│   ├── integration.yml            # PR：integration tests (with Docker)
│   ├── compat.yml                 # nightly：上游 SDK 兼容矩阵
│   ├── build.yml                  # main 推送：构建多架构镜像（不发布）
│   └── release.yml                # tag v*：构建 + 发布镜像 + 发布 3 SDK
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   └── feature_request.md
└── PULL_REQUEST_TEMPLATE.md
```

`release.yml` 核心 jobs：

```yaml
jobs:
  docker:    # build + push husk/husk:$VERSION
  pypi:      # publish husk-client==$VERSION
  npm:       # publish @husk/client@$VERSION
  github:    # release notes + assets
```

---

## 10. 命名约定

| 对象 | 约定 | 例 |
|---|---|---|
| Python 模块 | snake_case | `service.py`, `daemon_inject.py` |
| Python 类 | PascalCase | `SandboxService` |
| Python 函数 | snake_case | `create_sandbox` |
| Feature 文件夹 | 单数 snake_case | `sandbox/`, `snapshot/`, `api_key/` |
| TypeScript 文件 | PascalCase 组件 / camelCase 工具 | `SandboxTable.tsx`, `useSandboxes.ts` |
| TypeScript 函数 | camelCase | `createSandbox` |
| Go 包 | 全小写 | `package client` |
| Go 函数 | PascalCase 导出 / camelCase 私有 | `CreateSandbox` |
| Docker 镜像 tag | semver | `husk/husk:0.3.0` |
| API path | kebab-case | `/api/api-keys`, `/api/network-settings` |
| Sandbox id | `sb_<random>` | `sb_a1b2c3d4` |
| API Key | `hk_<random>` | `hk_xxxxxxxxx...` |
| Snapshot id | `sn_<random>` | `sn_a1b2c3d4` |

---

## 11. 关键依赖速查表

### 后端（pyproject.toml）

```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.4",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "aiosqlite>=0.20",
    "asyncpg>=0.29",            # 可选 Postgres
    "docker>=7.1",
    "httpx>=0.27",
    "websockets>=13",
    "python-jose[cryptography]>=3.3",  # JWT for preview tokens
    "argon2-cffi>=23",          # API Key hash
    "typer>=0.12",
    "loguru>=0.7",
]

[project.scripts]
husk = "husk.cli.main:app"
```

### 前端（package.json）

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@tanstack/react-router": "^1.50.0",
    "@tanstack/react-query": "^5.50.0",
    "openapi-fetch": "^0.11.0",
    "@xterm/xterm": "^5.5.0",
    "@xterm/addon-fit": "^0.10.0",
    "@xterm/addon-web-links": "^0.11.0",
    "react-hook-form": "^7.52.0",
    "zod": "^3.23.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0",
    "openapi-typescript": "^7.4.0"
  }
}
```

---

## 12. 文件总数估算

| 区块 | 文件数 | 代码行数估算 |
|---|---|---|
| 后端 husk/ | ~70（feature-first 文件多） | ~3500 |
| 前端 frontend/ | ~60 | ~3000 |
| SDK Python | ~20（多数 generated） | ~500 手写 |
| SDK TS | ~15 | ~300 手写 |
| SDK Go | ~15 | ~300 手写 |
| 测试 | ~35 | ~2000 |
| 文档 / 脚本 / CI | ~30 | — |
| **合计** | **~245 个文件** | **~10000 行手写代码** |

—— 这是 5+1.5+1 = ~7.5 周一人能完成的工作量上限。实际写起来 **~6000 行手写**就能跑 v0.3.0，剩下是 CI、文档、generated 代码、测试。

---

## 13. 第一天就可以 scaffold 的命令

```bash
# 1. 创建仓库结构（feature-first）
mkdir -p husk/{core,auth,sandbox,snapshot,volume,preview,toolbox,stub,health,tasks,cli,migrations/versions,static}
mkdir -p frontend/src/{routes/sandboxes,components/{ui,layout,sandbox,terminal,files,logs,common},hooks,api/_generated,lib,stores,styles}
mkdir -p sdks/{python/husk_client/_generated,typescript/src/_generated,go/client/_generated}
mkdir -p tests/{unit/{auth,sandbox,snapshot,volume,preview,toolbox,core},integration,compat}
mkdir -p docker scripts docs/sdks .github/workflows .github/ISSUE_TEMPLATE
mkdir -p embedded

# 2. 初始化后端
uv init --package husk
uv add fastapi uvicorn[standard] pydantic-settings sqlalchemy alembic aiosqlite docker httpx websockets typer loguru argon2-cffi python-jose[cryptography]
uv add --dev pytest pytest-asyncio testcontainers ruff

# 3. 初始化前端
cd frontend
pnpm create vite . --template react-ts
pnpm add @tanstack/react-router @tanstack/react-query openapi-fetch @xterm/xterm @xterm/addon-fit
pnpm add -D tailwindcss@next vitest @vitejs/plugin-react

# 4. 初始化 alembic
cd ..
uv run alembic init husk/migrations

# 5. 占位文件 + 第一次提交
touch husk/__init__.py husk/main.py
touch husk/core/__init__.py husk/core/{config,database,docker_client,deps,exceptions,logging}.py
for d in auth sandbox snapshot volume preview toolbox stub health; do
  touch husk/$d/__init__.py husk/$d/router.py
done
touch tests/conftest.py
echo "MIT License" > LICENSE
git init && git add -A && git commit -m "feat: scaffold husk project structure (feature-first)"
```

跑完这串命令，整个 §1-§9 的目录骨架就全在了，**接下来就是一个域一个域填业务代码**。
