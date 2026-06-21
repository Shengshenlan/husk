# Husk —— 项目架构

> 与 PLAN.md 配套阅读。PLAN.md 讲"做什么、什么时候做"，本文讲"长什么样、怎么跑起来"。

---

## 1. 一图概览（v0.2 / Phase 1 + 1.5）

```
                        ┌────────────────────────────┐
                        │       用户 / Agent          │
                        └─────┬──────────┬─────────┬──┘
                              │ Browser  │ CLI/SDK │ HTTP
                              ▼          ▼         ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │              Husk 控制面 (单进程)                                  │
   │   Python 3.12 · FastAPI · uvicorn · ~100MB                       │
   │  ┌────────────────────────────────────────────────────────────┐ │
   │  │  HTTP 8000                                                  │ │
   │  │   ├─ /            → React Dashboard (静态)                   │ │
   │  │   ├─ /api/...     → 业务域 router                            │ │
   │  │   ├─ /api/toolbox → Reverse Proxy → daemon                  │ │
   │  │   └─ /preview/... → Reverse Proxy → 容器端口                  │ │
   │  └────────────────────────────────────────────────────────────┘ │
   │                                                                  │
   │   Feature-first 业务域：                                           │
   │   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐ │
   │   │sandbox/││snapshot││ volume ││preview/││toolbox/││ auth/  │ │
   │   └────┬───┘└────┬───┘└────┬───┘└────┬───┘└────┬───┘└────┬───┘ │
   │        └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘     │
   │             ▼         ▼         ▼         ▼         ▼           │
   │   ┌────────────────────────────────────────────────────────┐   │
   │   │  core/   shared infrastructure                           │   │
   │   │   ├─ docker_client.py   ── docker-py                     │   │
   │   │   ├─ database.py        ── async session 工厂            │   │
   │   │   ├─ deps.py            ── 通用 Depends                   │   │
   │   │   └─ config / logging / exceptions                       │   │
   │   └────────────────────────────┬───────────────────────────┘   │
   │   ┌──────────────┐    ┌───────────────┐    ┌──────┐            │
   │   │  tasks/       │    │   migrations/  │    │ cli/ │            │
   │   │  周期任务      │    │    alembic     │    │typer │            │
   │   └──────────────┘    └───────────────┘    └──────┘            │
   └────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴────────┐
                ▼                        ▼
       ┌──────────────┐         /var/run/docker.sock
       │  ./data/      │                │
       │   husk.db     │                ▼
       │   logs/       │      ┌──────────────────────────────────┐
       │   daemon-bin  │      │       Docker Engine               │
       └──────────────┘      │ ┌──────────────────────────────┐ │
                              │ │ sandbox 容器（用户镜像）       │ │
                              │ │  ┌─────────────────────────┐ │ │
                              │ │  │ /opt/husk/daemon         │ │ │
                              │ │  │  (Phase 1: AGPL 上游)     │ │ │
                              │ │  │  :8080 toolbox API       │ │ │
                              │ │  │  /files /process /git ...│ │ │
                              │ │  └─────────────────────────┘ │ │
                              │ │  用户进程 / Agent 代码 ...      │ │
                              │ └──────────────────────────────┘ │
                              └──────────────────────────────────┘
```

**核心边界**：Husk 控制面与每个 sandbox 容器之间**只有 HTTP**，daemon 在容器内独立运行 —— 这是 100% MIT 代码 + AGPL daemon 容器能并存的法律根据。

---

## 2. 部署形态

### 2.1 开发模式（默认）

**单进程、单镜像、单端口** —— Gitea 风格。

```
docker run -d \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v husk-data:/data \
  husk/husk:0.2.0
```

进程内同时跑：
- FastAPI HTTP 服务（端口 8000）
- 静态文件服务（`/dashboard` 提供 React build）
- Toolbox 反代（HTTP + WebSocket）
- Preview URL 反代
- Auto-stop scheduler（asyncio 周期任务）
- Reaper（定时同步 docker ps ↔ DB）

### 2.2 生产模式（可选，Phase 3 之后）

```
       ┌─────────────────────────────────────────┐
       │  Caddy / Nginx (TLS + HTTP/2)            │
       └────┬───────────────┬───────────────┬─────┘
            │ /dashboard    │ /api          │ wss
            ▼               ▼               ▼
       ┌────────────────────────────────────────┐
       │   Husk 控制面 (uvicorn, ASGI)            │
       └────────────────────────────────────────┘
```

控制面不动，只是前置一层 TLS 终端。仍是单进程。

### 2.3 多机模式（远期 Phase 3）

控制面单实例 → 多个执行机 → 每个执行机本地 Docker。届时再设计 runner 协议。**当前不在范围**。

---

## 3. 控制面分层（Python 包结构 · Feature-first）

> 风格：[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
> 每个业务域内聚到一个文件夹；跨域调用通过 service 层显式 import。详见 [CODE_STRUCTURE.md §2](./CODE_STRUCTURE.md)。

```
husk/                                    # 控制面 Python 包
│
├── main.py                ── FastAPI app 装配 + router 总注册
│
├── core/                  ── 【横切】跨业务的基础设施（被任何域共享）
│   ├── config.py          ──   环境变量 / Settings
│   ├── database.py        ──   async engine + Base + session factory
│   ├── docker_client.py   ──   docker-py 封装；唯一访问 Docker 的地方
│   ├── deps.py            ──   通用 Depends（db_session, docker_client, ...）
│   ├── exceptions.py      ──   异常基类 + 全局 handler
│   └── logging.py
│
├── auth/                  ── 【域】鉴权 (router/service/models/repository/...)
├── sandbox/               ── 【域】沙盒生命周期（核心，含 daemon_inject/reaper/auto_stop）
├── snapshot/              ── 【域】镜像快照
├── volume/                ── 【域】卷
├── preview/               ── 【域】预览 URL（含 JWT 签发 + 反代）
├── toolbox/               ── 【域】Toolbox 反代（HTTP + WS 到 daemon）
├── stub/                  ── 【域】上游兼容 stub（/users/me, /organizations）
├── health/                ── 【域】健康检查
│
├── tasks/                 ── 【横切】asyncio 周期任务（调各域 service）
├── cli/                   ── 【横切】typer CLI（调各域 service）
├── migrations/            ── alembic
└── static/dashboard/      ── 前端 build 产物
```

每个业务域固定文件清单：

```
<domain>/
├── router.py        ── FastAPI APIRouter（所有 endpoint）
├── schemas.py       ── pydantic 输入输出
├── service.py       ── 业务逻辑（不知道 HTTP）
├── repository.py    ── DB 查询封装
├── models.py        ── SQLAlchemy ORM
├── dependencies.py  ── DI 工厂（service 组装 + 注入）
└── exceptions.py    ── 域专属异常
```

**跨域依赖规则**：

```
<domain>/router  ──→ <domain>/service           ✅ 同域内
<domain>/router  ──→ <domain>/repository        ✗ router 永不直连 DB
<A>/service      ──→ <B>/service                ✅ 跨域只走对方 service
<A>/service      ──→ <B>/repository             ✗ 不允许跨域读对方 DB
任何域           ──→ core/*                     ✅ 共享基础设施
core/*           ──→ 任何域                      ✗ 基础设施不知道业务
cli/, tasks/     ──→ <domain>/service           ✅ 横切复用 service
```

**核心好处**：
- 改 sandbox 全在 `husk/sandbox/` 一个文件夹内；删一个域 = 删一个文件夹
- 跨域 import 一行写出，耦合显式
- 每个域可独立 ~500 行的小模块，扩展无压力
- service 层单元测试不需要起 HTTP 服务器

---

## 4. 前端架构（Phase 1.5）

```
husk-dashboard/                           # 独立 npm 工程，monorepo 子目录
│
├── src/
│   ├── main.tsx                ── React 入口
│   ├── App.tsx                 ── Router 装配
│   │
│   ├── routes/                 ── 路由 + 页面
│   │   ├── login.tsx
│   │   ├── sandboxes/
│   │   │   ├── index.tsx       ──   列表
│   │   │   ├── new.tsx         ──   创建
│   │   │   └── $id.tsx         ──   详情（含 5 个 Tab）
│   │   ├── snapshots.tsx
│   │   ├── api-keys.tsx
│   │   └── settings.tsx
│   │
│   ├── components/             ── 复用组件
│   │   ├── ui/                 ──   shadcn/ui
│   │   ├── SandboxTable.tsx
│   │   ├── ResourcePicker.tsx
│   │   ├── Terminal.tsx        ──   xterm.js wrapper
│   │   ├── FileBrowser.tsx
│   │   └── LogStream.tsx
│   │
│   ├── api/                    ── OpenAPI 自动生成
│   │   └── client.ts           ──   不要手改
│   │
│   ├── hooks/                  ── TanStack Query 包装
│   │   ├── useSandboxes.ts
│   │   ├── useSnapshots.ts
│   │   └── useApiKeys.ts
│   │
│   ├── lib/
│   │   ├── auth.ts             ──   API Key localStorage
│   │   ├── format.ts           ──   字节 / 时间 / 状态转字符串
│   │   └── ws.ts               ──   WebSocket helper（PTY 用）
│   │
│   └── styles/
│       └── globals.css         ──   Tailwind v4
│
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

**部署**：`pnpm build` → `dist/` → 拷到 Husk 仓库的 `husk/static/dashboard/` → FastAPI 用 `StaticFiles` mount。

---

## 5. 请求生命周期（三种典型场景）

### 场景 A：创建 Sandbox

```
User
  │ POST /api/sandbox  {snapshot:"py-3.12", cpu:2, memory:2}
  ▼
husk/sandbox/router.py
  │ Depends(current_apikey) 验 API Key → 通过
  │ 调 sandbox.service.create(req)
  ▼
husk/sandbox/service.py
  │ ① snapshot.service.get_or_pull("py-3.12")     ← 跨域调 service
  │ ② sandbox.repository.insert(state="creating")
  │ ③ core/docker_client.py  containers.run(image, detach)
  │ ④ sandbox/daemon_inject.py  put_archive + exec daemon
  │ ⑤ httpx.get(container_ip:8080/version)        ← 等 daemon ready
  │ ⑥ sandbox.repository.update(state="started", container_id=...)
  ▼
husk/sandbox/router.py
  │ 序列化 SandboxResponse
  ▼
User  ←  201 Created  {id, name, state:"started", ports:[...]}
```

### 场景 B：Agent 调 toolbox（比如读文件）

```
SDK
  │ GET /api/toolbox/abc123/files?path=/workspace
  ▼
husk/toolbox/router.py
  │ Depends(current_apikey) 通过
  │ 调 sandbox.service.get(id) 取容器 IP + 8080 端口
  ▼
husk/toolbox/http_proxy.py
  │ httpx.AsyncClient 流式转发
  ▼
sandbox 容器 / daemon :8080
  │ /files handler → 返回文件列表 JSON
  ▼
proxy 流式回写 → SDK
```

**关键点**：控制面**不解析**响应内容，只做透传 —— 这样 daemon 协议升级时控制面可以不动。

### 场景 C：浏览器开 Web Terminal

```
Dashboard (browser)
  │ ① POST /api/toolbox/abc123/process/pty  → 创建 PTY session，拿 sessionId
  │ ② new WebSocket("wss://.../api/toolbox/abc123/process/pty/{sid}/connect")
  ▼
husk/toolbox/router.py
  │ 升级到 WebSocket
  ▼
husk/toolbox/ws_proxy.py
  │ 双向 pump：
  │   browser <-- ws --> husk <-- ws --> daemon
  │   daemon stdout → husk → browser xterm.write
  │   browser keystroke → husk → daemon stdin
  ▼
sandbox 容器 / daemon
```

---

## 6. 数据存储布局

```
/data/                              ← Docker volume 挂载点
├── husk.db                         ← SQLite 主库
├── husk.db-wal                     ← WAL 日志
├── husk.db-shm
├── logs/
│   ├── build/<snapshot-id>.log     ← 构建日志（如有）
│   └── audit.jsonl                 ← 审计 JSON Lines（可关）
├── tokens/
│   └── root.txt                    ← 启动自动生成的 root API Key
└── tmp/
    └── upload-<id>/                ← 临时上传缓冲
```

**SQLite 特点**：
- 单文件，备份就 `cp husk.db`
- WAL 模式开启，并发读不阻塞写
- 几万条 sandbox 记录无压力（这场景下 Postgres 是 over-engineering）

---

## 7. 网络拓扑

### 7.1 默认（用 Docker 默认 bridge）

```
host
├── docker0 bridge (172.17.0.1/16)
│   ├── sandbox-1  (172.17.0.10) :8080 daemon
│   ├── sandbox-2  (172.17.0.11) :8080 daemon
│   └── sandbox-N  (172.17.0.12) :8080 daemon
│
└── husk container (172.17.0.2)
    └── 通过 docker0 直接访问每个 sandbox 的 :8080
```

控制面通过容器 IP + 8080 直连 daemon，**不需要把 daemon 端口暴露到宿主**。

### 7.2 出站规则（v1）

由 sandbox/netrules.py 在容器创建后调用：

```python
# 默认完全开放出站
# 受限模式：只允许特定域名/IP
iptables -A FORWARD -s <container_ip> -d <whitelist> -j ACCEPT
iptables -A FORWARD -s <container_ip> -j DROP
```

更安全的做法是给每组 sandbox 用独立 docker network；v1 简化为 iptables 直写。

### 7.3 Preview URL 反代

```
browser → http://localhost:8000/preview/<token>/...
       → husk 解 token 拿 sandbox_id + port
       → httpx 转发到 <container_ip>:<port>
       → 流回 browser
```

子域名形式 `https://{port}-{sandboxId}.preview.example.com` 在 v1 不做（需要 DNS 通配 + TLS），后期支持。

---

## 8. 仓库结构（Monorepo）

> 一个 GitHub repo 装下控制面、前端、三种语言 SDK、文档；同版本号同步发布，避免漂移。

```
husk/                                  # GitHub repo 根
│
├── README.md
├── LICENSE                            # MIT
├── NOTICE                             # daemon 二进制 AGPL 声明
├── CHANGELOG.md
├── PLAN.md                            # 实施计划
├── ARCHITECTURE.md                    # 本文档
│
├── pyproject.toml                     # 控制面 Python 工程
├── uv.lock
├── alembic.ini
│
├── husk/                              # 控制面源码（§3）
│   └── static/dashboard/              ← Phase 1.5 起：前端 build 产物
├── tests/
│   ├── unit/
│   ├── integration/                   # testcontainers
│   └── compat/                        # 上游 daytona-sdk 兼容验收
│
├── frontend/                          # ← Phase 1.5：React Dashboard 源码
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── src/                           # （§4）
│
├── sdks/                              # ← Phase 1.7：多语言 SDK
│   ├── README.md                      ──   选哪个 SDK 的导航
│   ├── python/                        ──   husk-client (PyPI)
│   │   ├── pyproject.toml
│   │   ├── husk_client/
│   │   │   ├── _generated/            ──     OpenAPI 自动生成
│   │   │   └── ergonomic.py           ──     Phase 2.x 手写高层（先空着）
│   │   ├── examples/quickstart.py
│   │   └── tests/
│   ├── typescript/                    ──   @husk/client (npm)
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── _generated/
│   │   │   └── ergonomic.ts
│   │   ├── examples/quickstart.ts
│   │   └── tests/
│   └── go/                            ──   husk-go (Go modules)
│       ├── go.mod
│       ├── client/_generated/
│       ├── examples/quickstart/main.go
│       └── tests/
│
├── embedded/                          # 嵌入资源（构建时拷入）
│   ├── daemon-amd64                   # Phase 1
│   └── daemon-arm64
│
├── docker/
│   ├── Dockerfile                     # 多阶段：构建前端 + 拷 daemon + python
│   ├── compose.dev.yaml               # 开发用（挂载源码）
│   └── compose.example.yaml           # 用户参考
│
├── scripts/
│   ├── pull-upstream-daemon.sh        # 从上游 image 提取 daemon
│   ├── gen-sdk-clients.sh             # ← Phase 1.7：从 OpenAPI 生成三种 SDK
│   ├── gen-frontend-client.sh         # 从 OpenAPI 生成前端 TS client
│   └── build-image.sh
│
├── docs/
│   ├── getting-started.md
│   ├── api.md                         # OpenAPI 渲染
│   ├── compatibility.md               # 与上游 SDK 兼容矩阵
│   ├── sdk-python.md
│   ├── sdk-typescript.md
│   ├── sdk-go.md
│   ├── security.md
│   └── upgrade-from-daytona.md
│
└── .github/
    ├── workflows/
    │   ├── test.yml                   # backend pytest + frontend lint/test
    │   ├── compat.yml                 # 跑上游 SDK 兼容矩阵
    │   ├── build.yml                  # 多架构镜像
    │   └── release.yml                # ← 一次 tag → image + 3 SDK 同步发布
    └── ISSUE_TEMPLATE/
```

**Monorepo 工作方式**：

```
git tag v0.3.0  →  GitHub Actions release.yml
                    ├── build & push  husk/husk:0.3.0
                    ├── publish        husk-client==0.3.0   →  PyPI
                    ├── publish        @husk/client@0.3.0   →  npm
                    └── publish        husk-go v0.3.0       →  Go modules
```

一次 commit 能改 schema + 后端 handler + 前端调用 + 三种 SDK，避免跨 repo 同步。

---

## 9. 构建与发布管线

```
源码 (git push tag v0.2.0)
  │
  ▼
GitHub Actions
  ├─ 跑 pytest + frontend test
  ├─ 跑 compat 矩阵（上游 SDK quickstart）
  │
  ▼
多阶段 Docker 构建：
  Stage 1: node:20  →  pnpm build  →  /dist
  Stage 2: alpine   →  curl 上游 daemon image →  提取二进制
  Stage 3: python:3.12-slim
            COPY --from=1  /dist  →  /app/husk/static/dashboard
            COPY --from=2  /daemon-{amd64,arm64}  →  /app/embedded
            COPY husk/  →  /app/husk
            CMD ["husk", "serve"]
  │
  ▼
推送到：
  docker.io/husk/husk:0.2.0
  ghcr.io/<org>/husk:0.2.0
  │
  ▼
GitHub Release
  ├─ 自动生成 changelog
  ├─ 附 install 脚本
  └─ 附 SBOM
```

镜像最终大小估算：
- python:3.12-slim：~50MB
- 控制面代码 + deps：~20MB
- 前端 dist：~1MB
- daemon-amd64 + daemon-arm64：~30MB
- **共 ~100MB**

---

## 10. API 契约（跨语言一致性）

```
┌─────────────────────────────────────────────────────────────┐
│  控制面 API 唯一真理源：husk 项目里写的 FastAPI 装饰器        │
└─────────────────────┬───────────────────────────────────────┘
                      │ uvicorn 启动后导出
                      ▼
              /openapi.json (运行时)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   前端 TS client   外部 SDK      docs.md 渲染
   (自动生成)      (用户写)       (Redoc)
```

**Toolbox API 契约**：

```
┌─────────────────────────────────────────────────────────────┐
│  daemon 是 toolbox 协议唯一真理源                             │
└─────────────────────┬───────────────────────────────────────┘
                      │ Phase 1: 上游 daemon 的 OpenAPI
                      │ Phase 2: 自写 daemon 严格对齐上游 schema
                      ▼
        Husk 控制面只做透传（不解析 toolbox 响应）
        SDK 直接调 /api/toolbox/:id/* 即可
```

---

## 11. 配置 / 环境变量

```bash
# ── Husk 控制面 ──
HUSK_DATA_DIR=/data                    # 默认 /data
HUSK_DB_URL=sqlite:////data/husk.db    # 可换 postgres://
HUSK_LISTEN=0.0.0.0:8000
HUSK_LOG_LEVEL=info                    # debug/info/warn/error
HUSK_ROOT_API_KEY=                     # 留空则启动自动生成

# ── Docker ──
DOCKER_HOST=unix:///var/run/docker.sock
HUSK_DEFAULT_NETWORK=bridge
HUSK_DEFAULT_IMAGE=python:3.12         # 默认 sandbox image

# ── Daemon ──
HUSK_DAEMON_BIN=/app/embedded/daemon-amd64
HUSK_DAEMON_PORT=8080
HUSK_DAEMON_TARGET=/opt/husk/daemon

# ── Auto-stop ──
HUSK_AUTO_STOP_ENABLED=true
HUSK_AUTO_STOP_CHECK_INTERVAL=30s

# ── Reaper ──
HUSK_REAPER_INTERVAL=60s
```

---

## 12. 安全模型

| 风险点 | v1 缓解 | v2+ 加强 |
|---|---|---|
| API Key 泄露 | bcrypt hash 存储；前缀 `hk_` 显眼便于扫描 | 加 IP 白名单、过期时间 |
| Docker socket = root | README 明确告警；推荐 docker rootless | socket-proxy + capability 收紧 |
| sandbox 内逃逸 | 默认 `--cap-drop=ALL --security-opt=no-new-privileges` | gVisor / Kata 可选 |
| Toolbox 越权 | 反代时校验 API Key 拥有该 sandbox 权限 | 多用户后细化权限 |
| Preview URL 滥用 | 签名 token，默认 1h 过期 | rate limit |
| daemon 注入完整性 | SHA-256 校验嵌入二进制 | 二进制签名 |
| 数据持久化 | SQLite WAL，但单 host 故障即丢 | Postgres + 备份脚本 |

---

## 13. 与上游 Daytona 的关系图

```
┌─────────────────────────────────────────┐
│            Daytona 上游（AGPL）           │
│  ┌───────────────────────────────────┐  │
│  │  api (NestJS)                      │  │  ← Husk 不用，独立重写 Python
│  │  proxy / ssh-gateway               │  │  ← Husk 不用，合进控制面
│  │  runner (Go)                       │  │  ← Husk 不用，控制面直连 Docker
│  │  snapshot-manager                  │  │  ← Husk 不用
│  │                                    │  │
│  │  daemon (Go) ──── 容器内 toolbox    │──┼──→ Husk Phase 1 直接用二进制
│  │                                    │  │   Husk Phase 2 自写替换
│  │                                    │  │
│  │  libs/sdk-python (Apache 2.0)      │──┼──→ Husk 用户的 SDK 兼容目标
│  │  libs/api-client-* (Apache 2.0)    │──┼──→ 可直接 pip install
│  │  libs/toolbox-api-client-*         │──┼──→ 可直接 pip install
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│             Husk（MIT）                  │
│  ┌───────────────────────────────────┐  │
│  │  控制面（Python, 全新写）           │  │
│  │  ├─ FastAPI                        │  │
│  │  ├─ docker-py                      │  │
│  │  ├─ SQLite                         │  │
│  │  └─ React Dashboard                │  │
│  │                                    │  │
│  │  Phase 2:                          │  │
│  │  └─ 自写 daemon (Go, MIT)           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 14. 一图总结

```
                  +----------------------------+
   ┌──────────────┤  Husk 单镜像 (~100MB)        ├──────────────┐
   │              +----------------------------+              │
   │  ┌─────────────────────────────────────────────────┐     │
   │  │ React Dashboard  (Phase 1.5)                     │     │
   │  ├─────────────────────────────────────────────────┤     │
   │  │ FastAPI 控制面 (feature-first: sandbox/snapshot/...) │     │
   │  ├─────────────────────────────────────────────────┤     │
   │  │ docker-py → Docker Engine                        │     │
   │  ├─────────────────────────────────────────────────┤     │
   │  │ SQLite + ./data                                  │     │
   │  └─────────────────────────────────────────────────┘     │
   │              ↓ 创建 sandbox 时注入                          │
   │  ┌─────────────────────────────────────────────────┐     │
   │  │ daemon binary (Phase 1: AGPL / Phase 2: MIT)     │     │
   │  └─────────────────────────────────────────────────┘     │
   └──────────────────────────────────────────────────────────┘
                                ↓
           docker run -v /var/run/docker.sock husk/husk:0.2.0
```

部署一行；运行一进程；存储一文件；扩容一容器。
