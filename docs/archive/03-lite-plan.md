# Daytona-Lite 实施计划（Gitea 路线）

> **类比**：GitLab → Gitea 的重构哲学：
> - 单二进制 / 单 Docker 镜像
> - 默认 SQLite，可选 Postgres / MySQL
> - 砍掉企业治理（CI/CD pipeline、Kubernetes runner 编排、SAML/SCIM、计费等）
> - 保留 90% 个人/小团队会用的核心能力（git、issues、PR、webhook、API）
> - 性能 / 内存占用降低一个数量级
>
> 我们对 Daytona 做同样的事，目标：**单机一键起，<300MB 内存常驻，3 个二进制**。

代号建议：**`daytona-lite`** 或 **`sandbox-lite`**。

---

## 1. 范围裁剪

### 1.1 保留（核心价值）

| Daytona 模块 | 为什么保留 |
|---|---|
| **Sandbox 生命周期**：create / start / stop / destroy / resize / fork | 这是产品本体 |
| **Snapshot (pull)**：直接拉 OCI image | Agent 必须能选环境 |
| **Toolbox API**：files / process / session / pty / git / interpreter | 真正给 LLM 用的差异化 API |
| **Computer-use** | 单机 Agent 想用桌面控制 |
| **Preview URL（简化）** | 暴露容器端口 |
| **API Key 鉴权** | 替代 OIDC |
| **CLI** | 用户体验 |
| **Python / TS SDK** | 与上游 SDK 兼容很重要 |

### 1.2 砍掉（企业 / SaaS 特性）

| 模块 | 替代方案 |
|---|---|
| Organization、Quota、Usage、Billing | 删除（单租户无意义） |
| Stripe / PostHog / LaunchDarkly / Svix | 删除 |
| OIDC (Dex / Auth0) | 改 API Key + 可选 basic auth |
| Audit (Kafka 通道) | 改为 SQLite 表 + 可选 JSON 文件输出 |
| OpenSearch | 改 SQL `LIKE` |
| ClickHouse + Sandbox-Telemetry | 改本地 JSON Lines 文件，按需读 |
| OTel + Jaeger + otel-collector | 删除（保留 stdout 结构化日志） |
| Snapshot declarative builder | 删除 (v1)，仅保留 image pull |
| Snapshot-from-sandbox（commit） | 改为直接调 `docker commit`，合并入 runner |
| Sandbox backup / volume snapshot | 删除 (v1)，靠卷挂载 |
| Sandbox warm-pool | 删除 (v1)，按需创建 |
| Multi-runner / region | 单 runner，无地域 |
| snapshot-manager 独立服务 | 合进 runner |
| ssh-gateway 独立服务 | 合进 api（监听独立端口） |
| proxy 独立服务 | 合进 api（同进程 reverse proxy） |
| MinIO / S3 | 删除（v1 不要 backup） |
| MailDev / SMTP | 删除（无邀请流程） |
| pgAdmin / docker-registry-ui | 删除 |
| Internal OCI registry | 用 Docker Hub / 用户已有 registry |
| Webhook (Svix) | 改为本机配置的 outgoing webhook（HTTP POST） |

### 1.3 简化（保留思路但实现极简）

| 模块 | 简化方式 |
|---|---|
| Database | **默认 SQLite**（用 `better-sqlite3`），可选 Postgres |
| Cache / 锁 | **进程内**（无 Redis） |
| Pub/Sub | **EventEmitter**（无 Redis Adapter） |
| Object storage | 直接用 **本地文件系统** 替代 S3 |
| WebSocket | 单进程不需要 Socket.IO Redis Adapter |

---

## 2. 目标架构

```
                    +-----------------+
   user CLI / SDK ──▶  daytona-lite   │  ← 单二进制：API + Proxy + SSH gateway
                    │  (Go, ~30MB)    │     一进程，多端口（HTTP / WS / SSH）
                    +────────┬────────+
                             │ HTTP (单密钥)
                             ▼
                    +-----------------+
                    │  runner-lite    │  ← 单二进制：管 Docker，包含 snapshot-manager
                    │  (Go, ~20MB)    │
                    +────────┬────────+
                             │ Docker socket
                             ▼
                    +-----------------+
                    │  sandbox 容器    │
                    │   含 daemon 注入 │  ← 与上游 daemon 二进制 100% 兼容
                    +-----------------+

存储：SQLite 单文件 + 一个 ./data 目录（构建上下文 / 构建日志）
```

**部署形态**：

- **方案 A：单进程**：`daytona-lite serve` 在一台机器上同时跑控制面 + runner（开发首选）
- **方案 B：双进程**：`daytona-lite api` + `daytona-lite runner`，runner 部署到执行机（生产）
- **Docker Compose**：3 个服务（api、runner、用户自带 docker daemon）

可选额外服务（懒加载、不影响主流程）：
- Postgres（替换 SQLite）
- 自带 OCI registry（用户想自托管时）

---

## 3. 技术栈选择

### 3.1 重写 vs 保留：建议**控制面用 Go 重写**

理由：
- NestJS 那一摞 (kafka / opensearch / svix / ory / openfeature / aws-sdk / clickhouse / nestjs-microservices) 几乎全要砍，留下来的不到 30%，用 Go 直写比拆 NestJS 快。
- 让 api / runner / daemon 三者**同语言**，可共享 `apps/daemon/pkg/*` 与 `apps/runner/pkg/*` 的现有 Go 代码。
- 单二进制：`daytona-lite` 一个文件分发。
- 内存占用：NestJS 冷启 ~300MB；同等功能的 Go 服务 ~30MB。

> 备选：如果想最大化复用，可以保留 NestJS 但**关掉一切外部依赖**（用 `better-sqlite3` 替换 typeorm-pg、用 `eventemitter2` 替换 redis、删掉 kafka/clickhouse/opensearch/svix/posthog/launchdarkly 各模块）。这条路工作量约为 Go 重写的 30%，但跑时仍是 Node + 200+ 包 ~150MB。**两条路二选一**。

### 3.2 daemon / runner / SDK：**直接复用上游**

- `apps/daemon` —— 几乎不需要改（只把"组织 / 区域"字段从 `/init` 协议里设为可选）
- `apps/runner/pkg/docker` / `pkg/netrules` / `pkg/cache` —— 直接 vendor 进 lite 项目
- `libs/api-client-python`、`libs/sdk-python` —— **保持上游 OpenAPI 兼容**（lite 的 API 是上游的子集），用户切换无感

### 3.3 框架

- HTTP：`gin`（runner / daemon 已经在用）
- DB：`sqlite` (`mattn/go-sqlite3` 或 `modernc.org/sqlite` 纯 Go)，迁移用 `pressly/goose`
- WS：`gorilla/websocket`
- 配置：单 YAML / 环境变量

---

## 4. 数据模型（SQLite）

最少表数：

```sql
sandbox          -- 沙盒
snapshot         -- 镜像引用（仅 pull 类型）
volume           -- 卷（v1 = docker named volume 直映射）
api_key          -- 鉴权
ssh_access       -- 临时 SSH token
preview_token    -- 签名预览 URL
audit_log        -- 单表，可选
build_log        -- 文件路径引用，正文存 ./data/logs/<id>.log
```

去掉的表（对比上游）：
`organization*`, `region*`, `runner*`（单 runner 写死）, `warm_pool`, `sandbox_fork`（v1 不做 fork）, `usage`, `quota`, `linked_account`, `mfa`, `webhook` 表, `kafka_offset`, ...

---

## 5. API 子集（与上游兼容）

> **路径与请求体保持上游一致**，让上游 SDK 直接能用。返回字段中关于 organization / region / runner_id 的部分给 stub 默认值。

### 5.1 Phase 1 必做（最小可用）

```
POST   /api/sandbox                      # 上游兼容
GET    /api/sandbox
GET    /api/sandbox/:id
DELETE /api/sandbox/:id
POST   /api/sandbox/:id/start
POST   /api/sandbox/:id/stop
POST   /api/sandbox/:id/last-activity
POST   /api/sandbox/:id/autostop/:interval
GET    /api/sandbox/:id/ports/:port/preview-url

POST   /api/snapshots                    # 仅支持 image pull
GET    /api/snapshots
DELETE /api/snapshots/:id

GET    /api/api-keys
POST   /api/api-keys
DELETE /api/api-keys/:name

GET    /api/health
GET    /api/config

# Toolbox 透传：让 SDK 通过 api 反代到 daemon（与上游"toolbox-proxy-url"模式一致）
ANY    /api/toolbox/:sandboxId/*path
```

→ **覆盖 `02-apis.md` 列表的约 20 个端点**，已能跑完上游 SDK 的 80% Quickstart。

### 5.2 Phase 2 增强

- `resize`、`fork`、`snapshot-from-sandbox`
- `signed-preview-url`、SSH access
- `volumes` CRUD
- `users/me`（返回 stub 单用户）
- `organizations`（返回 stub `default-org`，让上游 dashboard 不报错）

### 5.3 不做（未来才考虑）

- 多地域 / 多 runner
- 配额 / 计费 / 审计 Kafka
- Webhook 平台 / Svix
- Snapshot declarative builder

---

## 6. 项目骨架

```
daytona-lite/
├── cmd/
│   ├── daytona-lite/        # CLI 入口（serve / api / runner / migrate）
│   └── ...
├── internal/
│   ├── api/                 # Gin 路由 + handler
│   │   ├── sandbox/
│   │   ├── snapshot/
│   │   ├── apikey/
│   │   └── proxy/           # Toolbox 反代
│   ├── runner/              # 内嵌 runner（直接调 docker）
│   │   ├── docker/          # vendor 自上游 apps/runner/pkg/docker
│   │   └── netrules/
│   ├── store/               # SQLite ＋ migration
│   ├── auth/                # API Key middleware
│   ├── preview/             # 反代 + token 签名
│   └── sshgw/               # 内嵌 ssh gateway
├── third_party/
│   └── daemon/              # 复制上游 daemon 二进制构建脚本（保持兼容）
├── docker/
│   ├── Dockerfile.lite      # 全合一镜像
│   └── compose.yaml         # 3 服务版（api/runner/docker-engine 用宿主）
├── docs/
└── README.md
```

---

## 7. 实施里程碑

> 工作量估计按一个全职熟悉 Go + Docker 的工程师。

### M0 — 验证可行性 (1 周)
- [ ] 抽出 `apps/runner/pkg/docker`、`pkg/netrules`、`pkg/cache` 验证能否独立跑
- [ ] 启动一个上游 `daemon` 二进制，确认它对"无 organization/region 的 init"能正常 work
- [ ] 编译并运行 `apps/cli` 指向自建 stub `/api/sandbox`，确认 SDK 协议层能联通

### M1 — Skeleton + Sandbox CRUD (1.5 周)
- [ ] Go 项目骨架、SQLite 迁移
- [ ] API Key 中间件
- [ ] `POST/GET/DELETE /api/sandbox`、`start`、`stop`
- [ ] runner 内嵌：拉镜像 → `docker run` → 注入 daemon → 写库
- [ ] CLI Quickstart 能 create / exec 一个 sandbox

### M2 — Toolbox 反代 + Preview (1 周)
- [ ] `/api/toolbox/:id/*path` HTTP + WebSocket 反代
- [ ] Preview token 表 + 签名 URL 路由
- [ ] 端口反代（同进程 reverse proxy）
- [ ] 单元测试 + 集成测试

### M3 — Snapshot pull + 自动停止 (0.5 周)
- [ ] Snapshot 表（仅 image ref）
- [ ] `last-activity` 心跳 + auto-stop scheduler

### M4 — Lifecycle Polish (1 周)
- [ ] resize、recover、网络出站规则透传
- [ ] 容器异常清理 reaper
- [ ] 简单 audit log（可关）

### M5 — 兼容 SDK 验收 (1 周)
- [ ] 跑上游 `libs/sdk-python` Quickstart：files、process、git、code-run
- [ ] 给上游 dashboard "minimal mode" 兜底（路径如 `users/me` 返回 stub）

### M6 — 打包发布 (0.5 周)
- [ ] 单 Docker 镜像：`daytona-lite:0.1` ~80MB
- [ ] Compose 文件：3 服务
- [ ] Helm chart 单 chart（可选）
- [ ] `daytona-lite serve` 一行启动 demo

**累计 ~6.5 周可发 v0.1。**

---

## 8. 风险与权衡

| 风险 | 应对 |
|---|---|
| 上游协议演进 → lite 不兼容 | 锁定 SDK minor 版本；CI 跑兼容矩阵 |
| 用户想要的"砍掉的功能"中有他要的 | 设计成插件接口（webhook / audit 出 hook），方便后续加 |
| Docker daemon 多租户安全 | 默认开 `--security-opt`、`--cap-drop`，可选 gVisor |
| 多 runner 需求 | 在 `runner-lite` 里保留客户端拉模式（与 daemon 通信契约不变），未来开 multi-runner 可解锁 |
| daemon 升级跟随上游 | 每个 lite 版本指定一个 daytona daemon 版本号，CI 自动构建并嵌入 |

---

## 9. 决策点（建议在动手前确认）

1. **控制面语言**：Go 重写（推荐） vs 保留 NestJS 改瘦
2. **是否保留 dashboard**：v1 不做（CLI 即可）vs 用上游 dashboard 接 stub 接口
3. **多 runner 初期是否预留**：完全单 runner（更简单）vs 协议保留 runner-id 字段（无后顾之忧）
4. **第一阶段 computer-use 是否包含**：包含会需要 daemon 带 X11/录屏依赖，镜像变大；不包含可后置

这四个点决定第一版的形态，建议依次回答。

---

## 10. 类比 Gitea 的最终形态

| 维度 | Daytona 上游 | daytona-lite (本计划) |
|---|---|---|
| 二进制数 | 9 (api/proxy/runner/daemon/ssh-gw/snapshot-mgr/dashboard/cli/otel) | 3 (lite/runner/daemon) |
| Compose 服务数 | 19 | 2-3 (lite + docker) |
| 必需外部依赖 | Postgres, Redis, OIDC, Registry, S3 | 仅 Docker |
| 默认数据库 | Postgres | SQLite |
| 冷启内存 | ~3-4GB | ~50-100MB |
| 镜像大小 | 数 GB | <100MB |
| API endpoint 数 | 220+ | ~30 (Phase 1)，~60 (Phase 2) |
| 一键安装 | docker compose up（19 容器） | `docker run daytona-lite` |
| SDK 兼容 | 上游全集 | 上游子集（无感切换） |

这与 Gitea 替换 GitLab 的取舍同构：放弃企业级 / SaaS 治理，换来**易部署、易理解、易二次开发**。
