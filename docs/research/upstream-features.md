# Daytona 功能分析

> 基于 `/root/daytona` 仓库的实际代码 (apps/, libs/, docker/) 整理，不是基于官方文档。

## 1. 整体架构

Daytona 把自己定位为 **"AI 生成代码的安全弹性运行时"**，给 Agent 跑代码用的沙盒平台。
一句话：**远程 Docker 容器编排 + 给 Agent 用的 SDK/工具箱**。

按官方说法分三层：

| 平面 | 组件 | 职责 |
|---|---|---|
| Interface plane | `cli`, `dashboard`, SDK | 用户/Agent 入口 |
| Control plane | `api`, `proxy`, `ssh-gateway`, `snapshot-manager`, `otel-collector` | 编排、鉴权、计费、路由 |
| Compute plane | `runner`, `daemon` | 真正跑 Docker 容器、在容器内提供 toolbox API |

### 1.1 应用清单 (`apps/`)

| 应用 | 语言 | 角色 | 是否核心 |
|---|---|---|---|
| **api** | TS / NestJS | 控制面主入口；REST + WebSocket；编排所有资源 | ★ 核心 |
| **runner** | Go / Gin | 计算节点；管理本机 Docker 容器；执行 sandbox 生命周期 | ★ 核心 |
| **daemon** | Go / Gin | 注入到每个 sandbox 容器内的 agent；提供 toolbox HTTP API、SSH、PTY、录屏、computer-use | ★ 核心 |
| **cli** | Go / Cobra | 用户 CLI；调用 api | ◯ 非必需 |
| **dashboard** | TS / React | Web UI | ◯ 非必需 |
| **proxy** | Go | 反向代理；签发 sandbox 端口的预览 URL；OIDC 鉴权 | △ 取决于是否要 preview |
| **ssh-gateway** | Go | 独立 SSH 网关；用 token 直连 sandbox | △ 可选 |
| **snapshot-manager** | Go | 协调 snapshot 创建（OCI image build & push） | △ 可合并入 runner |
| **otel-collector** | YAML 配置 | OTel 转发 | ✗ 可去 |
| **docs** | Astro | 文档站 | ✗ 可去 |
| **daytona-e2e** | Playwright | E2E 测试 | ✗ 可去 |

### 1.2 客户端 SDK (`libs/`)

每种语言都有 3 套：
- `sdk-<lang>` —— 包装层
- `api-client-<lang>` —— OpenAPI 生成的控制面客户端
- `toolbox-api-client-<lang>` —— OpenAPI 生成的容器内 daemon 客户端

支持语言：Python, TypeScript, Go, Java, Ruby（每个都有同步/异步两套，所以 libs/ 下有 23 个包）。

---

## 2. 控制面 API (`apps/api`)

NestJS 单体应用，按业务模块拆分。源码在 `apps/api/src/`。

### 2.1 模块清单

| 模块 | 文件夹 | 职责 |
|---|---|---|
| **sandbox** | `src/sandbox/` | 沙盒、运行节点(runner)、快照(snapshot)、卷(volume)、Job(异步任务)、preview URL 签发 |
| **organization** | `src/organization/` | 组织、成员、邀请、角色、配额、地域绑定、OTel 配置 |
| **user** | `src/user/` | 用户、Linked Account、MFA |
| **auth** | `src/auth/` | OIDC (Dex/Auth0)、API Key、Proxy/SSH-Gateway 上下文 |
| **api-key** | `src/api-key/` | 个人/服务 API Key 管理 |
| **region** | `src/region/` | 地域元数据 |
| **docker-registry** | `src/docker-registry/` | 内置/外接 OCI registry 凭证管理 |
| **object-storage** | `src/object-storage/` | S3 STS 签发（用于 build 上下文上传） |
| **webhook** | `src/webhook/` | Svix 推送平台事件 |
| **audit** | `src/audit/` | 审计日志（DB + Kafka 双通道） |
| **notification** | `src/notification/` | WebSocket 推送 |
| **billing** | (libs/billing-api-client) | Stripe 集成（仅 SaaS 闭源版用） |
| **analytics** | `src/analytics/` | PostHog 埋点 |
| **sandbox-telemetry** | `src/sandbox-telemetry/` | 从 ClickHouse 查 sandbox 的 logs/traces/metrics |
| **admin** | `src/admin/` | 管理员后台（影子接口） |
| **health** | `src/health/` | liveness / readiness |
| **config** | `src/config/` | 给前端用的运行时配置 |

### 2.2 横切关注点

- **数据库**：PostgreSQL (TypeORM)，迁移分 init / pre-deploy / post-deploy 三阶段
- **缓存/锁/Pub-Sub**：Redis (`@nestjs-modules/ioredis`)，配合 Socket.IO 多实例
- **搜索**：OpenSearch（sandbox 列表的全文检索）
- **遥测**：ClickHouse（沙盒内日志/指标）+ OTel + Prometheus + Jaeger
- **消息**：Kafka（审计事件可选输出）
- **对象存储**：S3 + STS（构建上下文、备份）
- **OIDC**：Dex (开发) / Auth0 / Ory（生产）
- **特性开关**：OpenFeature + LaunchDarkly
- **Webhook 推送**：Svix
- **邮件**：SMTP (MailDev / 任意 SMTP)
- **支付**：Stripe（闭源 billing）

---

## 3. 沙盒生命周期与功能

### 3.1 Sandbox 状态机
源码：`apps/api/src/sandbox/managers/sandbox.manager.ts` + `sandbox-actions/*`

支持的动作：`start / stop / archive / destroy / recover / resize / fork / backup / snapshot`。
自动化字段：`autoStop`、`autoArchive`、`autoDelete`（按 last-activity 心跳触发）。

### 3.2 Snapshot 体系

| 类型 | 说明 |
|---|---|
| **拉取式 (pull)** | 直接拉远程 OCI image |
| **声明式 (build)** | 用 declarative builder (类似 buildpacks) 在 runner 上构建 |
| **沙盒快照 (snapshot-from-sandbox)** | 把运行中容器 commit 成新 image |
| **backup** | 定期把容器状态推到 S3，断电可恢复 |

### 3.3 Volume
独立对象，可挂载到 sandbox。简化版可直接复用 Docker 命名卷。

### 3.4 Warm Pool
`sandbox-warm-pool.service.ts` —— 提前预热一批 sandbox 等用户领，把启动时间从秒级压到 ~90ms。

### 3.5 Fork
`sandbox-fork.entity` —— 沙盒可以 fork 出子沙盒，记 parent / ancestors 关系。

---

## 4. 容器内 Toolbox (`apps/daemon`)

每个 sandbox 启动时，runner 会把 `daemon` 二进制放进去，容器内自启一个 HTTP 服务（默认端口由 runner 注入），暴露给 Agent 用：

| 路由组 | 功能 |
|---|---|
| `/init`, `/version`, `/project-dir` 等 | 初始化与元信息 |
| `/files` | 文件 CRUD、上传/下载、批量、find/replace、权限、移动 |
| `/process/execute` | 一次性命令（同步） |
| `/process/code-run` | 直接跑 Python/JS 代码片段 |
| `/process/session/*` | 长连会话（可在同一 shell 里多次 exec） |
| `/process/pty/*` | 真 PTY，含 WS 实时 IO |
| `/process/interpreter/*` | 持久化 Python/JS 解释器上下文（类 Jupyter） |
| `/git/*` | clone/pull/push/commit/branch/checkout/status —— 容器内 git wrapper |
| `/lsp/*` | LSP 桥（completions、symbols、did-open/close 等） |
| `/computeruse/*` | **桌面控制**：截屏、鼠标、键盘、a11y tree、窗口管理 |
| `/computeruse/recordings/*` | 屏幕录制 |

子模块还有 `terminal` (xterm.js websocket 后端) 和 `recordingdashboard`。

> 这一层就是 Daytona 的"差异化"卖点 —— 不只是个 Docker 容器，而是给 LLM Agent 用的"高层 API"。

---

## 5. Runner (`apps/runner`)

Go + Gin。一台机器跑一个 runner，管这台机器上所有 Docker 容器。
对外的 HTTP API 给 control plane (api) 调：

- `/sandboxes` —— Create / Info / Start / Stop / Destroy / Backup / Resize / Recover / SnapshotFromSandbox / NetworkSettings
- `/snapshots` —— Pull / Build / Tag / Exists / Info / Remove / Logs / Inspect
- `/info` —— 节点能力、剩余资源
- `/metrics` —— Prometheus

内部还包含：
- `pkg/docker/` —— 直接调 Docker daemon
- `pkg/netrules/` —— iptables 写入网络出站规则（按 org 配额）
- `pkg/sshgateway/` —— 把 SSH 流量转发到具体容器
- `pkg/storage/` —— S3 备份/恢复
- `pkg/cache/` —— 镜像/快照本地缓存

---

## 6. 外围组件

- **proxy**：跑预览 URL `https://{port}-{sandboxId}.proxy.example.com`，并 OIDC 鉴权后注入到容器
- **ssh-gateway**：`ssh token@gateway` → 路由到容器内 `daemon` 的 SSH server
- **snapshot-manager**：协调多 runner 之间的镜像构建与推送
- **otel-collector**：OTLP HTTP 接收 → 转发到 Jaeger / Prom / ClickHouse

---

## 7. 依赖外部服务一览（来自 `docker/docker-compose.yaml`，**19 个服务**）

| # | 服务 | 必需性 | 备注 |
|---|---|---|---|
| 1 | api | ✅ | 主控 |
| 2 | proxy | △ | preview URL 用 |
| 3 | runner | ✅ | 计算节点 |
| 4 | ssh-gateway | △ | SSH 直连用 |
| 5 | dashboard | ◯ | UI |
| 6 | postgres | ✅ | 主库 |
| 7 | redis | ✅ | 锁/缓存/Pub-Sub |
| 8 | dex | △ | OIDC；可换成 API Key 直连 |
| 9 | registry | △ | 内部 OCI registry |
| 10 | docker-registry-ui | ✗ | 调试用 |
| 11 | maildev | ✗ | 开发邮件 |
| 12 | minio | △ | S3 存 build context / backup |
| 13 | jaeger | ✗ | tracing |
| 14 | otel-collector | ✗ | 转发器 |
| 15 | pgadmin4 | ✗ | DB UI |
| 16 | (clickhouse) | △ | 沙盒遥测；通过环境配 |
| 17 | (kafka) | ✗ | 审计可选输出 |
| 18 | (opensearch) | △ | sandbox 列表全文搜 |
| 19 | (svix) | ✗ | 闭源 webhook 平台 |

**结论：默认拉起需要 ~10GB 镜像、~3-4GB 运行内存**，这就是用户说的"重"。

---

## 8. 重点信号：哪里"过度工程化"

跑过一遍代码，能明显看出 Daytona 是按 **多租户云 SaaS** 设计的，单机自托管时 90% 功能是浪费：

| 模块 | 单机/小团队是否需要 |
|---|---|
| `organization`, `quota`, `billing`, `usage` | ✗ |
| Kafka 审计 | ✗ |
| OpenSearch 全文搜 | ✗（PG ILIKE 即可） |
| Svix Webhook | ✗（直接发 HTTP 即可） |
| Stripe / PostHog / LaunchDarkly | ✗ |
| OTel + Jaeger + ClickHouse 三件套 | ✗ |
| OIDC (Dex / Auth0) | ✗（API Key 即可） |
| 多 runner / 多地域 | ✗（单机 = 单 runner） |
| Warm Pool | △（小流量没必要） |
| snapshot-manager 独立服务 | ✗（合进 runner） |
| proxy + ssh-gateway 独立服务 | △（合并） |
| Svix-react、posthog-react、Auth0-react 等前端集成 | ✗ |

**真正构成 Daytona 价值的核心**只有两块：
1. **Toolbox API** （daemon 提供给 Agent 的高层接口）
2. **Sandbox 生命周期** （API + Runner + Docker 那条链路）

下一份 `03-lite-plan.md` 就围绕这两块展开。
