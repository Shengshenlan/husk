# Husk —— 实施计划

> **Husk** 是一个轻量级 AI 代码沙盒运行时。
> 给 Agent / SDK 提供"创建容器、跑代码、操作文件、做 Git、控制桌面"等高层能力，单机一键起，MIT 许可。

> **状态：v0.5.0 完成 ✓** — 本计划已落地。M0-M9、Phase 1.5、Phase 1.7、Phase 2
> 核心子集全部交付。运行时 100% MIT。后续工作请见 CHANGELOG.md "Unreleased"。

---

## 0. 一页摘要

- **代号**：Husk
- **定位**：Daytona 之于 Gitea 的位置 —— 砍掉企业治理 / SaaS 多租户，保留沙盒生命周期 + Agent toolbox 这两块核心
- **形态**：单 Python 服务 + 直连 Docker，1 个 Go daemon 二进制嵌入容器
- **许可**：仓库代码 100% MIT；从 v0.5 起运行时也 100% MIT（自写 Go daemon）
- **依赖**：仅需要本机 Docker，无需 Postgres / Redis / Kafka / OIDC / S3
- **资源**：278MB 镜像，~100MB 内存
- **部署**：`docker run -v /var/run/docker.sock:/var/run/docker.sock husk/husk` 即可
- **API 兼容**：上游 daytona Python / TS SDK 可无感切换
- **当前状态**：v0.1 → v0.5 全部完成。SDK 自动生成跑通，前端 dashboard build 进单镜像，自写 daemon 在容器内可执行 Python/shell/files。

---

## 1. 为什么做 Husk

### 1.1 Daytona 的问题
上游 Daytona 是 SaaS 多租户云架构，单机自托管时：
- 默认 19 个 docker compose 服务（Postgres / Redis / Kafka / OpenSearch / ClickHouse / Dex / MinIO / Jaeger / OTel / Svix / pgAdmin / MailDev / Registry / Registry-UI / api / proxy / runner / dashboard / ssh-gateway）
- 冷启 ~3-4GB 内存
- 控制面是 NestJS + 200+ npm 包
- 220+ HTTP endpoint，90% 是组织 / 配额 / 审计 / Webhook / 计费等企业功能
- AGPL-3.0 服务端许可

### 1.2 Husk 的目标
| 维度 | 上游 Daytona | Husk |
|---|---|---|
| 二进制数 | 9 | 2（控制面 + daemon） |
| Compose 服务数 | 19 | 0（直接 docker run） |
| 必需外部依赖 | Postgres、Redis、OIDC、Registry、S3 | 仅 Docker |
| 默认数据库 | Postgres | SQLite |
| 冷启内存 | ~3-4GB | ~100MB |
| 镜像大小 | 数 GB | <100MB |
| HTTP endpoint 数 | 220+ | ~30 (Phase 1) |
| 一键安装 | docker compose up | `docker run` |
| 仓库许可 | AGPL-3.0 | **MIT** |

### 1.3 不在范围
Husk 显式不做以下事，要这些请用上游 Daytona：
- 多租户组织、配额、计费
- 多 runner / 多地域调度
- 审计 Kafka 通道、OpenSearch 全文搜
- Svix Webhook 平台
- OIDC / SAML / SCIM
- 容器备份到 S3
- Warm Pool（预热池）
- 声明式镜像构建器

---

## 2. 架构

### 2.1 Phase 1（v0.1，~5 周）

```
┌──────────────────────────────────────────┐
│  Husk 控制面 (Python, MIT)               │
│   FastAPI + SQLite + docker-py           │
│   :8000 HTTP/WS                          │
│   嵌入：daytona daemon 二进制 (AGPL)        │
└──────────────┬───────────────────────────┘
               │ Docker socket
               ▼
┌──────────────────────────────────────────┐
│  Sandbox 容器 (用户的 OCI 镜像)            │
│   ──注入──> /opt/husk/daemon            │
│             :8080 toolbox API            │
└──────────────────────────────────────────┘
```

**关键设计**：控制面**直接调 docker socket**，不经过中间 runner 层。这是单机部署的合理简化 —— 上游 runner 80% 的代码是给多机调度用的，单机用不上。

### 2.2 Phase 2（v0.5，可选，+6 周）—— 100% MIT 运行时

把嵌入的 daemon 替换成自写的 Go daemon (MIT)，不依赖任何 AGPL 二进制。

### 2.3 Phase 3（远期）—— 多机

```
control plane ──HTTP──▶ remote runner ──▶ Docker
```

90% 用户不需要。需要时可以直接用 Docker remote API over TLS（零代码），或写一个 thin Go runner。**不在当前计划范围**。

---

## 3. 技术栈

### 3.1 控制面（Husk 主进程）

| 类别 | 选型 | 许可 |
|---|---|---|
| Web 框架 | FastAPI 0.115+ | MIT |
| ASGI | uvicorn | BSD |
| ORM | SQLAlchemy 2.x | MIT |
| 迁移 | Alembic | MIT |
| DB 驱动 | aiosqlite（默认）/ asyncpg（可选） | BSD / MIT |
| HTTP 客户端 / 反代 | httpx + websockets | BSD |
| Docker 客户端 | docker-py | Apache 2.0 |
| DTO / 配置 | pydantic 2.x | MIT |
| CLI | typer | MIT |
| 包管理 | uv | Apache 2.0 |
| 测试 | pytest + testcontainers | MIT / Apache 2.0 |

**全部 MIT/BSD/Apache 2.0**，无传染性 license。

### 3.2 daemon（嵌入二进制）

| 阶段 | 来源 | 许可 |
|---|---|---|
| Phase 1 | 上游 daytonaio/daemon 二进制 | AGPL-3.0（仅运行时） |
| Phase 2 | 自写 Go daemon | MIT |

### 3.3 数据存储

- 默认：单 SQLite 文件（`/data/husk.db`）
- 可选：Postgres（单 env 切换）
- 文件存储：本地 `./data/`（构建上下文 / 构建日志 / 录屏）

### 3.4 鉴权

- API Key（`Authorization: Bearer pk_<random>`）
- 启动时自动生成 root key 打到 stdout
- 多 key、可吊销，按 SQLite 表存

---

## 4. 仓库结构

> **单 repo（monorepo）**：控制面、前端、SDK、文档全部一个仓库一个版本号，避免漂移。

```
husk/
├── README.md
├── LICENSE                       # MIT
├── NOTICE                        # 列出 AGPL daemon 二进制来源
├── pyproject.toml                # 控制面 Python 工程（uv 管理）
├── Dockerfile                    # 单镜像（含嵌入 daemon + 前端 dist）
├── compose.yaml                  # 本地开发用
│
├── docs/
│   ├── architecture.md           # = ARCHITECTURE.md
│   ├── api.md                    # Husk 自身的 OpenAPI
│   ├── compatibility.md          # 与上游 daytona SDK 的兼容矩阵
│   └── upgrade-from-daytona.md
│
├── husk/                         # 控制面源码（Python，feature-first）
│   ├── __init__.py
│   ├── main.py                   # FastAPI app 装配 + 启动
│   │
│   ├── core/                     # 【横切】共享基础设施
│   │   ├── config.py             # pydantic-settings
│   │   ├── database.py           # async engine / Base / session 工厂
│   │   ├── docker_client.py      # docker-py 封装；唯一访问 Docker 处
│   │   ├── deps.py               # 通用 Depends
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── auth/                     # 【域】鉴权 (router/service/models/...)
│   ├── sandbox/                  # 【域】沙盒（核心，含 daemon_inject/reaper/auto_stop）
│   ├── snapshot/                 # 【域】镜像快照
│   ├── volume/                   # 【域】卷
│   ├── preview/                  # 【域】预览 URL（JWT 签发 + 端口反代）
│   ├── toolbox/                  # 【域】Toolbox 反代（HTTP + WS）
│   ├── stub/                     # 【域】上游兼容 stub
│   ├── health/                   # 【域】健康检查
│   │
│   ├── tasks/                    # 【横切】asyncio 周期任务
│   ├── cli/                      # 【横切】typer CLI
│   ├── migrations/               # alembic
│   └── static/dashboard/         # ← Phase 1.5：前端 build 产物
│   #
│   # 每个业务域的标准文件：router.py / service.py / repository.py /
│   # models.py / schemas.py / dependencies.py / exceptions.py
│   # 详见 CODE_STRUCTURE.md §2
│
├── frontend/                     # ← Phase 1.5：React Dashboard
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── public/
│   ├── src/                      # 见 ARCHITECTURE.md §4 / CODE_STRUCTURE.md §3
│   └── tests/
│
├── sdks/                         # ← Phase 1.7：多语言 SDK
│   ├── README.md
│   ├── python/                   # husk-client (PyPI)
│   ├── typescript/               # @husk/client (npm)
│   └── go/                       # husk-go (Go modules)
│
├── embedded/                     # 构建时拷入容器镜像
│   ├── daemon-amd64              # Phase 1: 拷自上游镜像
│   └── daemon-arm64
│
├── tests/
│   ├── unit/
│   ├── integration/              # testcontainers
│   └── compat/                   # 用上游 daytona-sdk 跑兼容验收
│
├── scripts/
│   ├── pull-upstream-daemon.sh   # 从上游 daemon 镜像拷二进制
│   ├── build-image.sh
│   └── gen-sdk-clients.sh        # ← Phase 1.7：从 OpenAPI 生成三种 SDK
│
└── .github/workflows/
    ├── test.yml                  # backend pytest + frontend lint/test
    ├── compat.yml                # 上游 daytona SDK 兼容矩阵
    └── release.yml               # 一次 tag → 镜像 + 3 SDK 同步发布
```

**单仓库的好处**：
- 一次 `git tag v0.3.0` 触发 `release.yml`，自动产出镜像 + Python SDK + TS SDK + Go SDK，全部同版本号
- 改 schema 时前后端 + 三种 SDK 在一次 PR 里改完，避免漂移
- 用户读源码时一处看全局，不用跨 repo 跳转

---

## 5. Phase 1 路线图

### M0 — 可行性验证（3 天，必须先做）

**目标**：证明"无 runner 直连 docker + 注入上游 daemon"可行。

任务：
- [ ] `docker pull daytonaio/daemon:vX`，从镜像中拷出 daemon 二进制
- [ ] 起一个干净 ubuntu 容器，把 daemon 拷进去，跑 `daemon serve`
- [ ] 不调控制面，不传 organization / region 参数，看它能否启动并响应 toolbox API
- [ ] Python 用 docker-py：`run` 容器 → `put_archive` 注入二进制 → `exec` 启动 daemon → `httpx` 调容器 IP:8080 拿到 `/files` 响应

**通过条件**：上述端到端能跑通。
**失败处理**：daemon 强依赖某个 control plane endpoint 时，实现该 stub 即可，不会阻塞。

### M1 — Skeleton + Sandbox CRUD（1 周）

- [ ] FastAPI 项目骨架，pyproject.toml，uv lock
- [ ] SQLAlchemy + alembic：sandbox / snapshot / api_key / preview_token 表
- [ ] API Key 中间件，启动自动生成 root key
- [ ] `POST /api/sandbox` → docker run + 注入 daemon
- [ ] `GET /api/sandbox`、`GET /api/sandbox/:id`
- [ ] `DELETE /api/sandbox/:id` → docker rm -fv
- [ ] `POST /api/sandbox/:id/start` / `stop`
- [ ] CLI 命令：`husk sandbox create/list/start/stop/delete`
- [ ] 单元测试：docker_client.py 全覆盖（用 testcontainers）

**M1 验收**：用 CLI 能完成一个 sandbox 的创建—启动—销毁全流程。

### M2 — Toolbox 反代 + Preview（1 周）

- [ ] `ANY /api/toolbox/:sandboxId/*path` HTTP 反代到 daemon
- [ ] WebSocket 反代（PTY、build log 流）
- [ ] Preview token：表 + 签名 + 解析
- [ ] `GET /api/sandbox/:id/ports/:port/preview-url`
- [ ] 端口反代：`/preview/:token/...` → 容器内端口
- [ ] 集成测试：用 `daytona-sdk-python` 调 `process.code_run("print(1)")` 走完反代链路

**M2 验收**：上游 SDK 调任意 toolbox API 都能成功，包括 PTY WebSocket。

### M3 — Snapshot pull + 自动停止（3 天）

- [ ] `POST /api/snapshots`：image pull 类型，调 `client.images.pull()`
- [ ] `GET /api/snapshots`、`DELETE`
- [ ] `last-activity` 心跳表
- [ ] asyncio 周期任务扫描，超过 autostop interval 自动 stop

### M4 — Lifecycle Polish（1 周）

- [ ] `POST /api/sandbox/:id/resize` → docker update
- [ ] `POST /api/sandbox/:id/snapshot` → docker commit
- [ ] `POST /api/sandbox/:id/network-settings` → iptables / docker network 出站规则
- [ ] 容器异常清理 reaper：启动时扫描 DB ↔ docker ps 对齐
- [ ] 简单 audit log（可关）

### M5 — SDK 兼容 + 打包（5 天）

- [ ] 跑上游 `libs/sdk-python` quickstart 全流程
- [ ] Stub endpoint：`/api/users/me`、`/api/organizations`、`/api/config`
- [ ] Dockerfile：多阶段构建，最终 `python:3.12-slim` + husk + 嵌入的 daemon 二进制
- [ ] Compose 文件（开发用）
- [ ] 文档：README + architecture.md + compatibility.md
- [ ] GitHub Actions：lint / test / build image / 跑 SDK 兼容测试
- [ ] 发版 v0.1.0：`husk/husk:0.1.0`

**Phase 1 交付物总检**：
- ✅ ~80MB Docker 镜像
- ✅ ~100MB 内存常驻
- ✅ 1 个进程
- ✅ `docker run` 一行启动
- ✅ 上游 daytona Python SDK 兼容
- ✅ 仓库 100% MIT
- ✅ 运行时含 1 个 AGPL 二进制（透明声明）

---

## 5.5 Phase 1.5 路线图：Web Dashboard（~1.5 周）

**目标**：M5 之后追加一个独立 React 前端，作为可视化管理界面。

### 5.5.1 技术栈

| 类别 | 选型 | 理由 |
|---|---|---|
| 构建工具 | Vite 5 | 快、零配置 |
| 框架 | React 18 + TypeScript | 主流、社区资源充足 |
| 路由 | TanStack Router | 类型安全、嵌套路由清爽 |
| 数据层 | TanStack Query | 缓存 / 轮询 / 失效策略成熟 |
| UI 组件 | shadcn/ui + Tailwind v4 | 复制即用、定制度高 |
| 终端 | xterm.js + WebSocket | 标准 web terminal 选型 |
| 表单 | react-hook-form + zod | 类型 + 校验一站 |
| API 客户端 | OpenAPI 生成（`openapi-typescript-codegen`） | 与控制面 schema 同步 |
| 状态 | TanStack Query 足够，必要时 Zustand | 不引 Redux |

**全部 MIT/Apache 2.0。**

### 5.5.2 部署形态

两种模式二选一：

- **模式 A（推荐）**：前端 build 产物（约 500KB gzip）embed 进 Husk Python 镜像，FastAPI 用 `StaticFiles` 在 `/dashboard` 路径下提供。**单镜像、单端口、单进程**。
- **模式 B**：前端独立部署（Vercel / Netlify / 自托管），通过 CORS 调 API。适合不想升级 Husk 镜像就能独立迭代前端的场景。

v1 默认用 A，仓库结构里同时支持 B。

### 5.5.3 页面清单（v1 含 7 个页面）

| # | 页面 | 路由 | 必做 |
|---|---|---|---|
| 1 | **登录 / API Key 输入** | `/login` | ✅ |
| 2 | **Sandboxes 列表（主页）** | `/sandboxes` | ✅ |
| 3 | **Sandbox 详情** | `/sandboxes/:id` | ✅ |
| 4 | **创建 Sandbox** | `/sandboxes/new` | ✅ |
| 5 | **Snapshots 管理** | `/snapshots` | ✅ |
| 6 | **API Keys 管理** | `/api-keys` | ✅ |
| 7 | **设置 / 关于** | `/settings` | ✅ |

### 5.5.4 各页面的功能点

#### ① 登录 / API Key 输入
- 单个输入框：粘贴 `hk_xxx` API Key
- "记住我"（写 localStorage）
- "如何获取 API Key" 帮助链接 → 显示 `husk apikey create my-key` CLI 命令
- 校验通过后跳 `/sandboxes`

#### ② Sandboxes 列表（主页）
- 表格列：名字 / 镜像 / 状态徽章 / CPU·内存 / 创建时间 / 最近活动 / 操作
- 状态色：running 绿、stopped 灰、creating 蓝、error 红
- 搜索框：按 name / label 过滤
- 状态筛选：All / Running / Stopped
- 行内操作（icon 按钮）：▶ 启动 / ⏸ 停止 / 🖥 终端 / 🌐 预览 / 🗑 删除
- 顶部"+ New Sandbox"按钮 → 跳 `/sandboxes/new`
- 自动刷新（5s 轮询，可暂停）

#### ③ Sandbox 详情
左侧 Tab 切换：

**Overview Tab**
- 基本信息：id / name / image / state / labels / 创建时间
- 资源：CPU / 内存 / 磁盘（带进度条）
- 网络：容器 IP / 暴露端口 / 预览 URL（一键复制）
- Auto-stop 倒计时
- 顶部操作栏：启动 / 停止 / 重启 / 创建 Snapshot / 删除

**Terminal Tab**
- 全尺寸 xterm.js
- WebSocket 连到 `/api/toolbox/:id/process/pty/.../connect`
- 自动 resize 跟随窗口
- 复制粘贴快捷键

**Files Tab**
- 左侧文件树（懒加载）
- 右侧文件预览（小文件直接显示，大文件提示下载）
- 操作：上传 / 新建文件夹 / 重命名 / 删除 / 下载
- 路径面包屑

**Logs Tab**
- 容器 stdout / stderr 实时滚动
- 时间戳 / 关键字过滤
- 一键复制全部 / 下载

**Settings Tab**
- 修改 labels（可视化 chip 编辑）
- Auto-stop interval slider
- 网络出站规则（规则列表 + 添加表单）
- Resize（重启生效）

#### ④ 创建 Sandbox
- Step 1：选 Snapshot（下拉选已有，或粘贴 image ref 临时拉取）
- Step 2：资源配置（CPU 1-8 / Mem 1-32 GB / Disk 1-100 GB，带预设套餐）
- Step 3：Labels / Auto-stop / 初始命令（可选）
- 顶部"创建并打开"vs"创建"两按钮
- 创建后跳详情页或列表页

#### ⑤ Snapshots 管理
- 列表：名字 / image ref / 状态（pulling / active / failed） / 大小 / 创建时间
- "+ Pull Image"按钮 → 弹窗输入 image ref → 后台拉取，进度条
- 操作：激活 / 反激活 / 删除（有占用时禁用）

#### ⑥ API Keys 管理
- 列表：名字 / 创建时间 / 最近使用
- "+ Create Key"弹窗 → 输入名字 → 生成后**只显示一次**（带复制按钮 + "我已保存"勾选才能关闭）
- 删除（带二次确认）

#### ⑦ 设置 / 关于
- Server info：Husk 版本 / 启动时间 / 容器总数 / 剩余 CPU·内存
- Docker info：Docker daemon 版本 / 镜像数 / 卷数
- Theme：Light / Dark / System
- 主题色：单色（默认 zinc / slate）
- 关于：链接到 GitHub / 文档 / License / 上游 Daytona 说明

### 5.5.5 不在 v1 范围

- 多用户 / 权限管理（单租户无意义）
- 监控图表（CPU/内存历史曲线）—— 后期加
- 操作审计日志可视化 —— 后期加
- 国际化 i18n —— v1 仅英文，后期加中文
- 移动端响应式 —— v1 桌面优先，移动端能看就行

### 5.5.6 里程碑（5.5.x）

| 编号 | 任务 | 工期 |
|---|---|---|
| **M5.1** | Vite + shadcn 骨架，OpenAPI client 生成，登录页 + API Key 验证 | 2 天 |
| **M5.2** | Sandboxes 列表页 + 创建页 + 基础操作 | 2 天 |
| **M5.3** | Sandbox 详情：Overview + Settings Tab | 1 天 |
| **M5.4** | Sandbox 详情：Terminal Tab（xterm.js + WS 反代联调） | 1.5 天 |
| **M5.5** | Sandbox 详情：Files Tab + Logs Tab | 1.5 天 |
| **M5.6** | Snapshots 页 + API Keys 页 + Settings 页 | 1.5 天 |
| **M5.7** | embed 进 Husk Python 镜像，发布 v0.2.0 | 0.5 天 |

**累计 ~10 天 ≈ 1.5 周。**

### 5.5.7 Phase 1.5 交付物

- ✅ 单镜像内含前端（无外部 CDN 依赖）
- ✅ 7 个核心页面全功能
- ✅ Web Terminal（关键差异化）
- ✅ 文件浏览器（关键差异化）
- ✅ 暗色主题
- ✅ 响应式（桌面优先）

---

## 5.7 Phase 1.7 路线图：多语言 SDK（~1 周）

**目标**：让 Python / TypeScript / Go 三种语言的开发者都能用 Husk 写 Agent / 自动化脚本，与上游 Daytona SDK 体验对齐。

### 5.7.1 三层 SDK 策略

```
Tier 0：兼容上游（Phase 1 M5 已含，零额外工作量）
   pip install daytona / npm install @daytona/sdk
   → 改一个 base_url 就能调 Husk

Tier 1：自动生成的 thin client（Phase 1.7，~1 周）
   pip install husk / npm install @husk/client / go get husk-go
   → OpenAPI 自动生成，函数级 API（低层）

Tier 2：手写 ergonomic SDK（Phase 2.x，~2 周）
   高层 API：sandbox.exec("python script.py").wait()
   类似上游 daytona-sdk 的开发者体验
```

**v1 默认走 Tier 0 + Tier 1**。Tier 2 看用户反馈再启动。

### 5.7.2 语言优先级

| 语言 | Tier 1 自动生成 | Tier 2 手写 | 理由 |
|---|---|---|---|
| **Python** | ✅ M5.8 | ✅ Phase 2.x | 主用户群（AI Agent 开发） |
| **TypeScript** | ✅ M5.8 | ✅ Phase 2.x | 前端 + Node Agent |
| **Go** | ✅ M5.8 | △ 按需 | Cloud native 用户 |
| Rust | △ 按需 | ✗ | 增长中但小众 |
| Java | △ 按需 | ✗ | ROI 低 |
| Ruby | ✗ | ✗ | 不做 |

> 用户要其他语言时，可以让他用 `openapi-generator` 自己生成；我们只发布前 3 种。

### 5.7.3 自动生成工具链

| 语言 | 生成工具 | 输出包名 | 发布到 |
|---|---|---|---|
| Python | `openapi-python-client` | `husk-client` | PyPI |
| TypeScript | `openapi-typescript` + `openapi-fetch` | `@husk/client` | npm |
| Go | `oapi-codegen` | `github.com/<org>/husk-go/client` | Go modules |

**统一规则**：
- 生成入口是 Husk 控制面在运行时导出的 `/openapi.json`
- CI 在 release 时执行 `scripts/gen-sdk-clients.sh`，把三种语言的 client 同步生成
- 每个 SDK 仓库目录自带 README + 一个 quickstart 示例

### 5.7.4 SDK 仓库结构（仍在主 monorepo 内）

```
husk/
├── sdks/
│   ├── python/                        # husk-client (Python)
│   │   ├── pyproject.toml
│   │   ├── husk_client/
│   │   │   ├── __init__.py
│   │   │   ├── _generated/            # 自动生成，不要手改
│   │   │   └── ergonomic.py           # Phase 2.x 手写高层（先空着）
│   │   ├── examples/
│   │   │   └── quickstart.py
│   │   └── tests/
│   │
│   ├── typescript/                    # @husk/client (TS)
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── _generated/
│   │   │   ├── client.ts
│   │   │   └── ergonomic.ts           # Phase 2.x 留空
│   │   ├── examples/
│   │   │   └── quickstart.ts
│   │   └── tests/
│   │
│   ├── go/                            # husk-go
│   │   ├── go.mod
│   │   ├── client/
│   │   │   └── _generated/
│   │   ├── examples/
│   │   │   └── quickstart/main.go
│   │   └── tests/
│   │
│   └── README.md                      # SDK 总览 + 选哪个
│
└── scripts/
    └── gen-sdk-clients.sh             # 一键重新生成所有 SDK
```

**关键决定**：SDK 与控制面**同 repo / 同版本号**。一次 `git tag v0.3.0` 同时发布：
- `husk/husk:0.3.0` Docker 镜像
- `husk-client==0.3.0` Python 包
- `@husk/client@0.3.0` npm 包
- `husk-go v0.3.0` Go module

避免 SDK 与控制面 schema 漂移。

### 5.7.5 Tier 1 SDK 体感（quickstart 对比）

**Python（自动生成的）**

```python
from husk_client import Client, AuthenticatedClient
from husk_client.api.sandbox import create_sandbox, list_sandboxes
from husk_client.models import CreateSandboxRequest

client = AuthenticatedClient(
    base_url="http://localhost:8000",
    token="hk_xxx",
)
sb = create_sandbox.sync(
    client=client,
    body=CreateSandboxRequest(snapshot_id="py-3.12", cpu=2, memory_mb=2048)
)
print(sb.id, sb.state)
```

**TypeScript**

```typescript
import createClient from "openapi-fetch";
import type { paths } from "@husk/client";

const client = createClient<paths>({
  baseUrl: "http://localhost:8000",
  headers: { Authorization: "Bearer hk_xxx" },
});

const { data } = await client.POST("/api/sandbox", {
  body: { snapshotId: "py-3.12", cpu: 2, memoryMb: 2048 },
});
console.log(data.id, data.state);
```

**Go**

```go
import "github.com/<org>/husk-go/client"

c, _ := client.NewClient("http://localhost:8000",
    client.WithAuthToken("hk_xxx"))
sb, _ := c.CreateSandbox(ctx, client.CreateSandboxRequest{
    SnapshotID: "py-3.12", CPU: 2, MemoryMB: 2048,
})
fmt.Println(sb.ID, sb.State)
```

**Tier 2 体感（Python，目标 ergonomic API，Phase 2.x）**：

```python
from husk import Husk

hk = Husk(base_url="http://localhost:8000", api_key="hk_xxx")
sb = hk.sandboxes.create(snapshot="py-3.12", cpu=2, memory="2GB")
result = sb.process.exec("python -c 'print(1+1)'")
print(result.stdout)            # "2\n"
sb.files.write("/tmp/x.txt", "hello")
sb.git.clone("https://github.com/x/y")
sb.destroy()
```

——这正是上游 `daytona-sdk` 的风格。Tier 2 在 Phase 2.x 才动手，避开 Phase 1.7 范围。

### 5.7.6 Toolbox 客户端

**Tier 0**：直接用 `daytona-toolbox-api-client-python`（Apache 2.0），通过 Husk 的 `/api/toolbox/:id/*` 反代。

**Tier 1**：暂不单独发包；toolbox 调用通过 thin client 的 `proxy_request` helper 发出。

**Tier 2**：Husk 高层 SDK（如 `sb.process.exec(...)`）内部封装 toolbox 调用 —— 用户感受不到 toolbox 的存在。

### 5.7.7 里程碑（M5.8 - M5.10）

| 编号 | 任务 | 工期 |
|---|---|---|
| **M5.8** | 写 `gen-sdk-clients.sh`，从 OpenAPI 自动生成 Python / TS / Go client | 2 天 |
| **M5.9** | 三种语言各写 quickstart + 完整 e2e 测试（CI 跑） | 2 天 |
| **M5.10** | 发布 v0.3.0：4 个产物（image + 3 SDK 包）一键 release | 1 天 |

**累计 ~5 天 ≈ 1 周。**

### 5.7.8 Phase 1.7 交付物

- ✅ `pip install husk-client`、`npm install @husk/client`、`go get husk-go` 全部可用
- ✅ 三种语言 quickstart 示例 + CI e2e 测试
- ✅ 一次 git tag → 4 个产物同时发布（镜像 + 3 SDK）
- ✅ `docs/compatibility.md` 记录 Husk SDK 与上游 daytona SDK 的差异矩阵

---

## 6. Phase 2 路线图（可选，达成 100% MIT 运行时）

**前置**：Phase 1 v0.1 上线、收到至少 5 个真实用户反馈。

### 6.1 范围裁剪

按上游 daemon 80 个 endpoint 排优先级，先做 Agent 真正最常用的：

| 模块 | endpoint 数 | 工期 | Phase 2 含吗 |
|---|---|---|---|
| 文件系统 | 14 | 1 周 | ✅ |
| 进程 execute / code-run | 2 | 3 天 | ✅ |
| Session（带状态 shell） | 9 | 1 周 | ✅ |
| Git wrapper | 11 | 3 天 | ✅ |
| LSP 桥 | 7 | 1 周 | △ |
| PTY | 6 | 1 周 | △ |
| Interpreter | 4 | 1 周 | △ |
| Computer-use | 24 | 3-4 周 | ✗ 永远后置 |
| 录屏 | 6 | 1 周 | ✗ |

**Phase 2 范围**：files + process + session + git，约 36 endpoint。

### 6.2 实现要点

- 语言：Go（容器内静态二进制）
- 框架：Gin
- 严格按上游 daemon 的 OpenAPI schema → 用户的 toolbox-api-client 无感切换

### 6.3 里程碑

- M6（1 周）：Go skeleton + files API 全套
- M7（2 周）：process / session
- M8（1 周）：git wrapper
- M9（1 周）：替换 Phase 1 注入的二进制，跑通 SDK quickstart
- M10（按需）：LSP / PTY / Interpreter

---

## 7. API 子集设计（Phase 1）

> 路径与字段保持**与上游兼容**，让 daytona SDK 用户改个 baseURL 就能用。

### 7.1 必做（Phase 1）

```
# Sandbox
POST   /api/sandbox
GET    /api/sandbox
GET    /api/sandbox/:id
DELETE /api/sandbox/:id
POST   /api/sandbox/:id/start
POST   /api/sandbox/:id/stop
POST   /api/sandbox/:id/resize
POST   /api/sandbox/:id/snapshot
POST   /api/sandbox/:id/last-activity
POST   /api/sandbox/:id/autostop/:interval
POST   /api/sandbox/:id/network-settings
GET    /api/sandbox/:id/ports/:port/preview-url

# Snapshots (仅 image pull)
POST   /api/snapshots
GET    /api/snapshots
GET    /api/snapshots/:id
DELETE /api/snapshots/:id

# API Keys
POST   /api/api-keys
GET    /api/api-keys
DELETE /api/api-keys/:name

# Toolbox 反代
ANY    /api/toolbox/:sandboxId/*path

# 兼容 stub
GET    /api/users/me
GET    /api/organizations
GET    /api/config
GET    /api/health
GET    /api/health/ready

# Preview 反代（独立 host/path）
GET    /preview/:token/*path
```

约 30 个 endpoint，覆盖上游 SDK quickstart 全流程。

### 7.2 不做（永远不做或后期再说）

- `/runners/*` —— 单进程无 runner
- `/jobs/*` —— 无 job 队列
- `/regions`、`/shared-regions` —— 无地域
- `/organizations/:id/*` —— 单租户
- `/audit/*`、`/webhooks/*` —— v1 不做
- `/sandbox/:id/fork`、`/forks`、`/parent`、`/ancestors` —— v1 不做
- `/sandbox/:id/backup` —— v1 不做
- `/admin/*` —— 单用户
- `/object-storage/*` —— 不需要 S3

---

## 8. 数据模型（SQLite，Phase 1）

```sql
-- 沙盒
CREATE TABLE sandbox (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    snapshot_id TEXT,
    container_id TEXT,
    state TEXT,                 -- creating/started/stopped/destroyed
    cpu INTEGER,
    memory_mb INTEGER,
    disk_gb INTEGER,
    labels TEXT,                -- json
    public BOOLEAN DEFAULT 0,
    auto_stop_interval INTEGER,
    last_activity_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);

-- 镜像快照（仅 image ref）
CREATE TABLE snapshot (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    image_ref TEXT,
    state TEXT,                 -- pulling/active/failed
    created_at DATETIME
);

-- 卷（v1 简单映射 docker named volume）
CREATE TABLE volume (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    docker_volume TEXT,
    created_at DATETIME
);

-- API Key
CREATE TABLE api_key (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    key_hash TEXT,
    created_at DATETIME,
    last_used_at DATETIME
);

-- Preview 签名 token
CREATE TABLE preview_token (
    id TEXT PRIMARY KEY,
    sandbox_id TEXT,
    port INTEGER,
    token TEXT UNIQUE,
    expires_at DATETIME
);

-- 审计（可选）
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME,
    actor TEXT,
    action TEXT,
    target TEXT,
    meta TEXT                   -- json
);
```

---

## 9. 法律 / 许可 / 合规

### 9.1 仓库

- LICENSE：MIT
- NOTICE：列出运行时 AGPL 依赖（daemon 二进制来源）
- 不 vendor 任何 AGPL 源码
- 不抄上游 controller 的源码（OpenAPI 路径名是事实性表达，独立实现 OK）

### 9.2 第三方依赖

全部 MIT / BSD / Apache 2.0（见 §3.1）。

### 9.3 运行时

| 阶段 | AGPL 组件 | 边界 |
|---|---|---|
| Phase 1 | 上游 daytona daemon 二进制 | HTTP / 进程隔离，不传染 |
| Phase 2 之后 | 无 | 全 MIT |

### 9.4 README 必备段落

```
## License

Husk's source code is licensed under MIT.

Husk v0.x runtime includes the upstream Daytona daemon binary, which is
licensed under AGPL-3.0. Husk loads it as a separate process inside
sandbox containers and communicates over HTTP. This constitutes
aggregation, not derivative work, under FSF guidelines.

In Husk v0.5+, the upstream daemon is replaced with a MIT-licensed
implementation, removing all AGPL components from the runtime.
```

---

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| M0 验证失败：daemon 强依赖某 control plane endpoint | 中 | 中 | 实现该 stub；最坏情况是 Phase 1 + 2 合并 |
| 上游 daemon 升级 schema 变化 | 中 | 中 | 锁定一个 long-term-stable daemon 版本号；CI 跑兼容矩阵 |
| docker-py 高并发性能 | 低 | 低 | v1 单机几十 sandbox 够用；高并发场景应走 Phase 3 |
| 直接挂载 docker socket 安全风险 | 高 | 高 | README 强调用 docker rootless 或 socket-proxy；后续做 capability 收紧 |
| 自写 daemon 工作量超预期 | 中 | 中 | Phase 2 严格分子集，computer-use 永远后置 |
| 上游 SDK 严重不兼容 | 低 | 高 | M5 兼容验收阶段全面跑测试；不兼容点写进 compatibility.md |

---

## 11. 命名 / 视觉

- **项目名**：Husk
- **含义**：外壳 / 谷壳 —— 保护性的隔离层；AI Agent 在这层"外壳"内安全运行
- **核心叙事**："The husk is the boundary. What runs inside is yours."（外壳是边界，里面的事归你）
- **CLI 命令**：`husk`
- **Python 包**：`husk`
- **Docker 镜像**：`husk/husk:0.1.0`（或 `ghcr.io/<org>/husk:0.1.0`）
- **域名建议**（按可用性优先级）：
  - `husk.dev`
  - `husk.run`
  - `gethusk.io`
  - `husklabs.dev`
  - `husk.codes`
- **CLI 体感**：
  ```
  husk new my-box --image python:3.12
  husk exec my-box "pip install foo"
  husk ssh my-box
  husk ps
  husk rm my-box
  ```
- **Logo 方向**：极简轮廓 —— 一个 hexagonal / 圆角方块外壳，里面是空洞或一个抽象代码符号；单色 + 一个强调色

---

## 12. M0 立刻可执行的清单

第一天就可以开始，不需要任何决策再补充：

```bash
# 1. 拉上游 daemon 镜像，提取二进制
docker pull daytonaio/daemon:latest
docker create --name d daytonaio/daemon:latest
docker cp d:/usr/local/bin/daemon ./daemon-amd64
docker rm d

# 2. 起一个空 ubuntu 容器，注入并裸跑
docker run -d --name probe -p 8080:8080 ubuntu:22.04 sleep infinity
docker cp ./daemon-amd64 probe:/opt/daemon
docker exec probe chmod +x /opt/daemon
docker exec -d probe /opt/daemon serve --port 8080

# 3. 调用看是否能 work
curl http://localhost:8080/version
curl http://localhost:8080/files?path=/

# 如果上述都返回数据 → 整个 Phase 1 路径通畅
# 如果不行 → 看 daemon 日志，识别需要 stub 的 control plane 路径
```

---

## 13. 决策已锁定

为避免再回头，本计划已固定以下选择：

| 决策 | 选择 |
|---|---|
| 控制面语言 | Python (FastAPI) |
| 中间 runner 层 | 砍掉，控制面直连 Docker |
| Phase 1 daemon 来源 | 上游 AGPL 二进制（嵌入或 init container 拉） |
| 多 runner 字段保留 | 是，写常量 `"default"` |
| Dashboard | **v1.5 独立 React 前端（Phase 1.5，~1.5 周）** |
| 多语言 SDK | **v1.7 自动生成 Python/TS/Go（Phase 1.7，~1 周）** |
| 仓库形态 | **Monorepo（控制面 + 前端 + SDK 同 repo 同版本）** |
| Computer-use | Phase 2 不做，永远后置 |
| 数据库默认 | SQLite，可切 Postgres |
| 仓库许可 | MIT |
| 项目名 | Husk |

如果某项要重开，再回到本文件修订 §13 即可。

---

## 14. 后续开放问题（不阻塞 M0）

- [ ] 注册 `husk.dev` 域名（建议先查可用性）
- [ ] GitHub 组织名（个人 namespace 还是新建 org）
- [ ] Docker Hub / GHCR 选择
- [ ] 是否给上游 daytona 提一个 issue 说明 Husk 的存在（保持开源生态友好）
- [ ] 第一批 alpha 用户 / dogfood 渠道

---

## 15. 一句话总结

**5 周做出 v0.1（MIT 控制面 + AGPL daemon 容器 + CLI），1.5 周追加 v0.2 Web Dashboard，1 周追加 v0.3 三语言 SDK，6 周后做 v0.5（自写 daemon，运行时也 100% MIT）。所有产物同 monorepo 同版本号，每阶段可独立交付。**
