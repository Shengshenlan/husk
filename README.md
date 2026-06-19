# Husk

> **The husk is the boundary. What runs inside is yours.**

Husk 是一个轻量级 AI 代码沙盒运行时 —— 给 Agent / SDK 提供"创建容器、跑代码、操作文件、做 Git、控制桌面"等高层能力。**MIT 许可、单镜像、单进程、`docker run` 一行启动。**

类比 GitLab → Gitea 的关系：Daytona → Husk。砍掉企业治理 / SaaS 多租户层，保留沙盒生命周期 + Agent toolbox 这两个核心。

---

## 1. 总架构图

```
                                  ┌─── 用户 / Agent ───┐
                                  │                    │
              ┌───────────┬───────┴────────┬───────────┴───────────┐
              │           │                │                       │
          Browser     CLI (husk)     Python SDK             TS / Go SDK
         Dashboard                  husk-client          @husk/client / husk-go
              │           │                │                       │
              └───────────┴────── HTTP / WebSocket ─────────────────┘
                                          │
                                          ▼
   ╔═════════════════════════════════════════════════════════════════════════╗
   ║                                                                          ║
   ║                Husk Control Plane  ·  Python · 单进程 · ~100MB             ║
   ║   ┌──────────────────────────────────────────────────────────────────┐  ║
   ║   │                     FastAPI :8000                                  │  ║
   ║   │   /              → React Dashboard (静态)                           │  ║
   ║   │   /api/...       → REST handlers                                   │  ║
   ║   │   /api/toolbox/  → Reverse Proxy (HTTP + WebSocket)                │  ║
   ║   │   /preview/...   → 容器端口反代                                      │  ║
   ║   └──────────────────────────────────────────────────────────────────┘  ║
   ║                                                                          ║
   ║   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    ║
   ║   │ sandbox/ │ │snapshot/ │ │ volume/  │ │ preview/ │ │ toolbox/ │... ║
   ║   │  router  │ │  router  │ │  router  │ │  router  │ │  router  │    ║
   ║   │  service │ │  service │ │  service │ │  service │ │  proxy   │    ║
   ║   │  models  │ │  models  │ │  models  │ │  models  │ │          │    ║
   ║   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    ║
   ║        │            │             │             │             │       ║
   ║        └────────────┴─────────────┴─────────────┴─────────────┘       ║
   ║                                  ▼                                     ║
   ║                       ┌──────────────────────┐                         ║
   ║                       │  core/  shared infra  │                         ║
   ║                       │  ├ docker_client      │                         ║
   ║                       │  ├ database / deps    │                         ║
   ║                       │  └ config / logging   │                         ║
   ║                       └──────────┬───────────┘                         ║
   ║                                  ▼                                     ║
   ║                            SQLite / Docker socket                     ║
   ║                                                                          ║
   ╚════════════════════════════╤═════════════════════════════════════════════╝
                                │
                                ▼
   ┌──────────────────────────────────────────────────────────────────────────┐
   │                          Docker Engine                                    │
   │                                                                            │
   │   ┌─────────────────────────┐    ┌─────────────────────────┐             │
   │   │ Sandbox Container 1      │    │ Sandbox Container 2     │             │
   │   │ ┌─────────────────────┐  │    │ ┌─────────────────────┐ │             │
   │   │ │ daemon :8080         │  │    │ │ daemon :8080         │ │             │
   │   │ │ ─ /files            │  │    │ │ ─ /files            │ │   ......    │
   │   │ │ ─ /process /pty     │  │    │ │ ─ /process /pty     │ │             │
   │   │ │ ─ /git /lsp         │  │    │ │ ─ /git /lsp         │ │             │
   │   │ │ ─ /computeruse      │  │    │ │ ─ /computeruse      │ │             │
   │   │ └─────────────────────┘  │    │ └─────────────────────┘ │             │
   │   │ user code / agent ...    │    │ user code / agent ...   │             │
   │   └─────────────────────────┘    └─────────────────────────┘             │
   └──────────────────────────────────────────────────────────────────────────┘
```

**核心边界**：控制面 ↔ 容器 之间**只有 HTTP**。daemon 在容器内独立运行，与控制面进程隔离 —— 这是 100% MIT 控制面 + AGPL daemon 容器能并存的法律根据（聚合而非衍生）。

---

## 2. Monorepo 结构图

```
husk/                              GitHub repo (MIT)
│
├── husk/                          ─── Python 控制面 (FastAPI)
├── husk/                          ─── Python 控制面 (FastAPI · feature-first)
│   ├── core/        ─── 共享基础设施（docker / db / config）
│   ├── sandbox/     ─── 沙盒域（router/service/models/...）
│   ├── snapshot/    ─── 快照域
│   ├── volume/  preview/  toolbox/  auth/  stub/  health/
│   ├── tasks/  cli/                 横切
│   └── static/dashboard/             前端 build 产物注入处
│
├── frontend/                      ─── React Dashboard (Phase 1.5)
│   ├── src/routes/                    7 个页面
│   ├── src/components/                shadcn/ui · xterm.js
│   └── src/api/_generated/            从 OpenAPI 自动生成
│
├── sdks/                          ─── 多语言 SDK (Phase 1.7)
│   ├── python/      → PyPI:    husk-client
│   ├── typescript/  → npm:     @husk/client
│   └── go/          → modules: github.com/<org>/husk-go
│
├── embedded/                      ─── 构建时打包
│   └── daemon-{amd64,arm64}           Phase 1: 上游 AGPL / Phase 2: 自写 MIT
│
├── tests/                         ─── 单元 + 集成 + 上游兼容
├── docs/                          ─── 用户文档
├── docker/Dockerfile              ─── 多阶段：前端 + daemon + python
└── .github/workflows/release.yml  ─── tag → 镜像 + 3 SDK 同步发布
```

**Monorepo 的核心好处**：一次 `git tag v0.3.0` 同时产出：

```
git tag v0.3.0  ──▶  GitHub Actions
                     ├── docker push  husk/husk:0.3.0
                     ├── pip publish  husk-client==0.3.0
                     ├── npm publish  @husk/client@0.3.0
                     └── go release   husk-go v0.3.0
```

后端 schema、前端调用、3 种 SDK 永不漂移。

---

## 3. 阶段路线图

```
M0 验证 (3 天)                  打通 daemon 注入路径
   │
   ▼
Phase 1   (5 周)   v0.1.0     控制面 + CLI + SDK 兼容上游
   │                          ── docker run 一行起、~80MB 镜像
   ▼
Phase 1.5 (1.5 周) v0.2.0     + Web Dashboard
   │                          ── 7 个页面、Web Terminal、文件浏览器
   ▼
Phase 1.7 (1 周)   v0.3.0     + Python / TS / Go SDK
   │                          ── 自动生成 thin client，同 monorepo 同版本
   ▼
Phase 2   (6 周)   v0.5.0     自写 daemon
   │                          ── 100% MIT 运行时
   ▼
Phase 3   (远期)   v1.x       多机集群（90% 用户用不到）
```

**到 v0.3.0 累计 ~7.5 周**，交付物为：MIT 控制面 + 前端 + CLI + 3 语言 SDK + 上游 SDK 兼容。

---

## 4. 文档导航

| 文档 | 作用 | 何时看 |
|---|---|---|
| **[PLAN.md](./PLAN.md)** | 实施计划：阶段、里程碑、任务清单、决策点 | 知道"做什么、什么时候做" |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 架构详解：分层、请求生命周期、网络、存储 | 知道"长什么样、怎么跑起来" |
| **[CODE_STRUCTURE.md](./CODE_STRUCTURE.md)** | 项目代码结构：每个文件的职责、依赖、内容速览 | 知道"代码怎么放、scaffold 怎么写" |
| [research/upstream-features.md](./research/upstream-features.md) | 上游 Daytona 功能/模块逐一拆解 | 想理解为什么砍这个保那个 |
| [research/upstream-apis.md](./research/upstream-apis.md) | 上游 220+ HTTP 接口完整清单 | 想确认某个 endpoint 我们做不做 |
| [archive/](./archive/) | 早期中间稿（带 runner / 不带 runner 两版） | 一般不看；想回顾决策演进时翻 |

---

## 5. 关键决策一览

| 决策 | 选择 | 影响 |
|---|---|---|
| 控制面语言 | **Python (FastAPI)** | 与目标用户(Agent 开发者)同语言；省 NestJS 200+ 包体积 |
| 中间 runner 层 | **砍掉，控制面直连 Docker** | 二进制数 3 → 2，部署 19 服务 → 1 服务 |
| Phase 1 daemon | **嵌入上游 AGPL 二进制（HTTP 边界不传染）** | 5 周即可发 v0.1，不耗时自写 |
| Phase 2 daemon | **自写 Go (MIT)** | 6 周后达成 100% MIT 运行时 |
| Multi-runner 字段 | **保留（写常量 "default"）** | 0 成本可扩展性 |
| Dashboard | **Phase 1.5 独立 React（同 repo）** | 单镜像内含、无外部 CDN |
| SDK | **Tier 0 上游兼容 + Tier 1 自动生成 Python/TS/Go** | 用户可选用上游 SDK 或 Husk-branded |
| 仓库形态 | **Monorepo** | 控制面 + 前端 + 3 SDK 同版本号 |
| 数据库 | **SQLite 默认 / Postgres 可选** | 单文件备份、零外部依赖 |
| 仓库许可 | **MIT** | 商用友好 |

锁定决策详见 [PLAN.md §13](./PLAN.md)。

---

## 6. 资源占用对比

| 维度 | 上游 Daytona | Husk |
|---|---|---|
| 二进制数 | 9 | 2（Phase 1）/ 1（Phase 2 起，daemon 自写嵌入） |
| Compose 服务数 | 19 | 0（直接 docker run） |
| 必需外部依赖 | Postgres、Redis、OIDC、Registry、S3 | 仅 Docker |
| 默认数据库 | Postgres | SQLite |
| 冷启内存 | ~3-4 GB | ~100 MB |
| 镜像大小 | 数 GB | ~80 MB |
| HTTP endpoint 数 | 220+ | ~30 (Phase 1) |
| 一键安装 | docker compose up（19 容器） | `docker run` 一行 |
| 仓库许可 | AGPL-3.0 | **MIT** |
| Phase 1 工期 | — | 5 周 |
| 完整路线 | — | ~13 周到 v0.5.0 |

---

## 7. 不在范围

要这些请用上游 Daytona：

- 多租户组织、配额、计费
- 多 runner / 多地域调度
- 审计 Kafka 通道、OpenSearch 全文搜
- Svix Webhook 平台
- OIDC / SAML / SCIM
- 容器备份到 S3
- Warm Pool（预热池）
- 声明式镜像构建器
- Computer-use（屏幕/鼠标/键盘控制） —— 永远后置

---

## 8. 当前状态

- ✅ 上游分析完成（[research/](./research/)）
- ✅ 实施计划定稿（[PLAN.md](./PLAN.md)）
- ✅ 架构设计完成（[ARCHITECTURE.md](./ARCHITECTURE.md)）
- ⏭️ **下一步：M0 验证**（3 天，PLAN.md §12 的 docker 命令）

---

## 9. 许可

仓库代码：MIT（见 LICENSE）
Phase 1 运行时：含 1 个上游 AGPL daemon 容器/二进制（HTTP 边界不传染）
Phase 2 起运行时：100% MIT
