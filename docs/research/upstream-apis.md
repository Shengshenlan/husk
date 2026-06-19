# Daytona 接口清单

> 本清单从控制器源码逐一提取，包含 **Control Plane API**（`apps/api`）、**Runner API**（`apps/runner`）、**Toolbox API**（`apps/daemon`）三层。

路径前缀：

- Control Plane：`https://<api>/api`
- Runner：`http://<runner>:3003`（默认）
- Toolbox：容器内 daemon 端口（由 runner 注入）

---

## A. Control Plane API（NestJS / `apps/api/src`）

### A.1 Sandbox 沙盒生命周期 `Controller('sandbox')`
源：`sandbox/controllers/sandbox.controller.ts`

| Method | Path | 用途 |
|---|---|---|
| GET | `/sandbox` | 列所有 sandbox |
| GET | `/sandbox/paginated` | 分页 |
| POST | `/sandbox` | 创建 |
| GET | `/sandbox/for-runner` | runner 调用，分配未指派的 |
| GET | `/sandbox/:id` | 详情 (id 或 name) |
| DELETE | `/sandbox/:id` | 销毁 |
| POST | `/sandbox/:id/start` | 启动 |
| POST | `/sandbox/:id/stop` | 停止 |
| POST | `/sandbox/:id/recover` | 恢复 |
| POST | `/sandbox/:id/resize` | 改 CPU/内存/磁盘 |
| PUT | `/sandbox/:id/labels` | 改 labels |
| PUT | `/sandbox/:id/state` | runner 回调状态 |
| POST | `/sandbox/:id/backup` | 触发备份 |
| POST | `/sandbox/:id/snapshot` | 由当前 sandbox 创建 snapshot |
| POST | `/sandbox/:id/fork` | fork |
| GET | `/sandbox/:id/forks` | 列子 |
| GET | `/sandbox/:id/parent` | 取父 |
| GET | `/sandbox/:id/ancestors` | 链路 |
| POST | `/sandbox/:id/public/:isPublic` | 设公开/私有 |
| POST | `/sandbox/:id/last-activity` | 心跳（auto-stop 用） |
| POST | `/sandbox/:id/autostop/:interval` | 设自动停止 |
| POST | `/sandbox/:id/autoarchive/:interval` | 自动归档 |
| POST | `/sandbox/:id/autodelete/:interval` | 自动删除 |
| POST | `/sandbox/:id/network-settings` | 网络出站规则 |
| POST | `/sandbox/:id/archive` | 立即归档 |
| GET | `/sandbox/:id/ports/:port/preview-url` | 预览 URL |
| GET | `/sandbox/:id/ports/:port/signed-preview-url` | 签名 URL |
| POST | `/sandbox/:id/ports/:port/signed-preview-url/:token/expire` | 失效 |
| GET | `/sandbox/:id/build-logs` | 构建日志 |
| GET | `/sandbox/:id/build-logs-url` | 构建日志 URL |
| POST | `/sandbox/:id/ssh-access` | 创 SSH access token |
| DELETE | `/sandbox/:id/ssh-access` | 撤 |
| GET | `/sandbox/ssh-access/validate` | gateway 校验 token |
| GET | `/sandbox/:id/toolbox-proxy-url` | 取 toolbox 代理 URL |
| GET | `/sandbox/:id/organization` | 反查 org |
| GET | `/sandbox/:id/region-quota` | 配额 |

### A.2 Runner 节点管理 `Controller('runners')`
源：`sandbox/controllers/runner.controller.ts`

| Method | Path | 用途 |
|---|---|---|
| POST | `/runners` | 注册 runner |
| GET | `/runners/me` | runner 自查（带 token） |
| GET | `/runners/by-sandbox/:id` | 反查 |
| GET | `/runners/by-snapshot-ref` | 找带指定 snapshot 的 runner |
| GET | `/runners/:id` / `/runners/:id/full` | 详情 |
| GET | `/runners` | 列表 |
| PATCH | `/runners/:id/scheduling` | 启停调度 |
| PATCH | `/runners/:id/draining` | 排空模式 |
| DELETE | `/runners/:id` | 摘除 |
| POST | `/runners/healthcheck` | 心跳 |

### A.3 Snapshot 镜像 `Controller('snapshots')`

| Method | Path | 用途 |
|---|---|---|
| POST | `/snapshots` | 创建 (pull / build) |
| GET | `/snapshots` | 列 |
| GET | `/snapshots/:id` | 详情 |
| DELETE | `/snapshots/:id` | 删 |
| GET | `/snapshots/:id/build-logs` | 构建日志 |
| GET | `/snapshots/:id/build-logs-url` | 日志 URL |
| POST | `/snapshots/:id/activate` | 激活 |
| POST | `/snapshots/:id/deactivate` | 反激活 |

### A.4 Volume 卷 `Controller('volumes')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/volumes` | 列 |
| POST | `/volumes` | 创建 |
| GET | `/volumes/:id` | 详情 |
| GET | `/volumes/by-name/:name` | 按名查 |
| DELETE | `/volumes/:id` | 删 |

### A.5 Job 异步任务 `Controller('jobs')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/jobs` | 列 |
| GET | `/jobs/poll` | 长轮询取下一任务 |
| GET | `/jobs/:id` | 详情 |
| POST | `/jobs/:id/status` | 上报状态 |

### A.6 Preview & 子路由 `Controller('preview')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/preview/:sandboxId/public` | 是否公开 |
| GET | `/preview/:sandboxId/validate/:authToken` | 校验 |
| GET | `/preview/:sandboxId/access` | 取访问元信息 |
| GET | `/preview/:signedPreviewToken/:port/sandbox-id` | 通过签名解出 sandbox |

### A.7 Toolbox 代理（已弃用）`Controller('toolbox')`
旧版控制面直接代理 toolbox 调用，新版改为客户端直连 daemon，故不展开。

### A.8 Organization 组织 `Controller('organizations')`

| Method | Path | 用途 |
|---|---|---|
| GET / POST / DELETE | `/organizations`, `/organizations/:id` | CRUD |
| GET | `/organizations/invitations`、`/invitations/count` | 我收到的邀请 |
| POST | `/organizations/invitations/:id/accept` / `decline` | 接受/拒绝 |
| PATCH | `/organizations/:id/default-region` | 默认地域 |
| GET | `/organizations/:id/usage` | 用量 |
| PATCH | `/organizations/:id/quota` / `/quota/:regionId` | 配额 |
| POST | `/organizations/:id/leave` / `suspend` / `unsuspend` | 状态 |
| GET / PUT / DELETE | `/organizations/:id/otel-config` | OTel 配置 |
| GET | `/organizations/otel-config/by-sandbox-auth-token/:token` | 内部反查 |
| POST | `/organizations/:id/sandbox-default-limited-network-egress` | 网络默认 |
| PUT | `/organizations/:id/experimental-config` | feature flags |

子路由：
- `Controller('organizations/:organizationId/invitations')` — 创建/列/取消/PUT 邀请
- `Controller('organizations/:organizationId/roles')` — Role CRUD
- `Controller('organizations/:organizationId/users')` — 成员、access、移除

### A.9 Region `Controller('regions')` / `Controller('shared-regions')`
单 endpoint：`GET /regions`，`Organization-Region` CRUD 在 `organization-region.controller.ts`。

### A.10 User `Controller('users')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/users/me` | 自身信息 |
| GET | `/users/account-providers` | 已绑定的第三方 |
| POST | `/users/linked-accounts` | 绑定 |
| DELETE | `/users/linked-accounts/:provider/:providerUserId` | 解绑 |
| POST | `/users/mfa/sms/enroll` | MFA |

### A.11 API Key `Controller('api-keys')`

| Method | Path | 用途 |
|---|---|---|
| POST / GET | `/api-keys` | 创建 / 列出 |
| GET | `/api-keys/current` | 当前用的 |
| GET | `/api-keys/:name` | 详情 |
| DELETE | `/api-keys/:name` 或 `/:userId/:name` | 删 |

### A.12 Docker Registry `Controller('docker-registry')`

| Method | Path | 用途 |
|---|---|---|
| POST / GET | `/docker-registry` | 添加 / 列 |
| GET | `/docker-registry/registry-push-access` | 取推送临时凭证 |
| GET / PATCH / DELETE | `/docker-registry/:id` | CRUD |

### A.13 Object Storage `Controller('object-storage')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/object-storage/push-access` | 取 STS 临时凭证 |

### A.14 Audit `Controller('audit')`

| Method | Path | 用途 |
|---|---|---|
| GET | `/audit/organizations/:organizationId` | 查审计日志 |

另：`Controller('kafka-audit')` 是 Kafka consumer 内部接口。

### A.15 Sandbox Telemetry `Controller('sandbox')` 子路径
源：`sandbox-telemetry/controllers/sandbox-telemetry.controller.ts`

| Method | Path | 用途 |
|---|---|---|
| GET | `/sandbox/:id/telemetry/logs` | 容器日志 |
| GET | `/sandbox/:id/telemetry/traces` | trace 列表 |
| GET | `/sandbox/:id/telemetry/traces/:traceId` | trace 详情 |
| GET | `/sandbox/:id/telemetry/metrics` | 指标 |

### A.16 Webhook `Controller('webhooks')`

| Method | Path | 用途 |
|---|---|---|
| POST | `/webhooks/organizations/:id/app-portal-access` | Svix portal token |
| GET | `/webhooks/organizations/:id/initialization-status` | Svix app 初始化状态 |
| POST | `/webhooks/organizations/:id/initialize` / `/refresh-endpoints` | 初始化、刷新 |

### A.17 Health & Config

- `GET /health`、`GET /health/ready`
- `GET /config` —— 给前端的运行时配置

### A.18 Admin 后台 `Controller('admin/*')`
- `admin/audit`, `admin/docker-registry`, `admin/organizations`, `admin/runners`, `admin/sandbox`, `admin/snapshots`, `admin/users`, `admin/webhooks`
- 通常按内部管理员权限放行

### A.19 WebSocket / 通知
NestJS Gateway，事件类：sandbox 状态变化、build log 流、notification。Socket.IO + Redis Adapter 多实例。

---

## B. Runner API（Go / `apps/runner/pkg/api/server.go`）

| Method | Path | Handler |
|---|---|---|
| GET | `/` | HealthCheck |
| GET | `/api/*any` | Swagger |
| GET | `/metrics` | Prometheus |
| GET | `/info` | RunnerInfo |
| POST | `/sandboxes` | Create |
| GET | `/sandboxes/:sandboxId` | Info |
| POST | `/sandboxes/:sandboxId/destroy` | Destroy |
| POST | `/sandboxes/:sandboxId/start` | Start |
| POST | `/sandboxes/:sandboxId/stop` | Stop |
| POST | `/sandboxes/:sandboxId/backup` | CreateBackup |
| POST | `/sandboxes/:sandboxId/snapshot-from-sandbox` | SnapshotFromSandbox |
| POST | `/sandboxes/:sandboxId/resize` | Resize |
| POST | `/sandboxes/:sandboxId/recover` | Recover |
| POST | `/sandboxes/:sandboxId/is-recoverable` | IsRecoverable |
| POST | `/sandboxes/:sandboxId/network-settings` | UpdateNetworkSettings |
| POST | `/snapshots/pull` | Pull |
| POST | `/snapshots/build` | Build |
| POST | `/snapshots/tag` | TagImage |
| GET | `/snapshots/exists` | Exists |
| GET | `/snapshots/info` | Info |
| POST | `/snapshots/remove` | Remove |
| GET | `/snapshots/logs` | BuildLogs |
| POST | `/snapshots/inspect` | InspectInRegistry |

鉴权：`Authorization: Bearer <RUNNER_API_KEY>`（只一对密钥）。

---

## C. Toolbox API（Go / `apps/daemon/pkg/toolbox/server.go`）

容器内 daemon 暴露给 Agent / SDK 的高层 API。

### C.1 元信息 / 初始化
| Path | 说明 |
|---|---|
| `POST /init` | 写入 org、region、snapshot 元信息 |
| `GET /version` | 版本 |
| `GET /project-dir`、`GET /user-home-dir`、`GET /work-dir` | 路径查询 |

### C.2 文件系统 `/files`
`GET /files`、`GET /files/`（兼容）、`GET /files/download`、`POST /files/bulk-download`、`GET /files/find`、`GET /files/info`、`GET /files/search`、`POST /files/folder`、`POST /files/move`、`POST /files/permissions`、`POST /files/replace`、`POST /files/upload`、`POST /files/bulk-upload`、`DELETE /files`

### C.3 进程 `/process`

**单次 / 代码执行**
- `POST /process/execute` — shell 命令
- `POST /process/code-run` — Python/JS 直接跑

**Session（带状态的 shell）**
- `GET/POST /process/session`
- `GET /process/session/entrypoint`、`/entrypoint/logs`
- `POST /process/session/:sessionId/exec`
- `GET /process/session/:sessionId`
- `DELETE /process/session/:sessionId`
- `GET /process/session/:sessionId/command/:commandId`
- `POST /process/session/:sessionId/command/:commandId/input`
- `GET /process/session/:sessionId/command/:commandId/logs`

**PTY**
- `GET/POST /process/pty`
- `GET/DELETE /process/pty/:sessionId`
- `GET /process/pty/:sessionId/connect` (WebSocket)
- `POST /process/pty/:sessionId/resize`

**持久 Interpreter (类 Jupyter)**
- `POST /process/interpreter/context`、`GET /process/interpreter/context`、`DELETE /process/interpreter/context/:id`
- `GET /process/interpreter/execute`

### C.4 Git `/git`
`branches` (GET/POST/DELETE)、`history`、`status`、`add`、`checkout`、`clone`、`commit`、`pull`、`push`

### C.5 LSP `/lsp`
`start`、`stop`、`completions`、`did-open`、`did-close`、`document-symbols`、`workspacesymbols`

### C.6 Computer Use `/computeruse`
- `status` / `start` / `stop`
- 进程管理：`process-status`、`process/:name/status|restart|logs|errors`
- 截屏：`screenshot`、`screenshot/region`、`screenshot/compressed`、`screenshot/region/compressed`
- 鼠标：`mouse/position`、`mouse/move`、`mouse/click`、`mouse/drag`、`mouse/scroll`
- 键盘：`keyboard/type`、`keyboard/key`、`keyboard/hotkey`
- 显示：`display/info`、`display/windows`
- 可访问性 a11y：`a11y/tree`、`a11y/find`、`a11y/node/focus|invoke|value`

### C.7 录屏 `/computeruse/recordings`
`POST /start`、`POST /stop`、`GET /`（list）、`GET /:id`、`GET /:id/download`、`DELETE /:id`

### C.8 终端、录屏看板（独立服务）
`apps/daemon/pkg/terminal` 和 `apps/daemon/pkg/recordingdashboard` 提供 xterm.js 后端 + 录像回放页。

---

## D. SSH Gateway / Proxy

- `ssh-gateway`：SSH 协议。客户端 `ssh <token>@gateway -p 2222` → 网关 `Validate token` (调 A.1 ssh-access/validate) → 反代到 sandbox 容器内 daemon SSH。
- `proxy`：HTTP 反代。`https://{port}-{sandboxId}.proxy.example.com` → 控制面查 `preview/...` 拿目标 → 转发到 daemon 端口。

---

## E. Webhook / 事件流

- 平台事件通过 **Svix** 推送给租户配置的 endpoint，事件类型包含 sandbox.created/started/stopped/destroyed、snapshot.built 等。
- 内部 NestJS EventEmitter 在控制面不同 service 间用，跨进程则走 Redis Pub/Sub 或 Kafka。

---

## F. 鉴权矩阵

| 入口 | 方式 |
|---|---|
| Dashboard / SDK 用户态 | OIDC bearer (Dex/Auth0) |
| SDK 自动化态 | API Key (`X-Daytona-API-Key` 或 `Authorization: Bearer dt_...`) |
| Runner ↔ API | RUNNER_API_KEY 共享密钥 |
| API ↔ Runner | 同上 |
| Proxy ↔ API | PROXY_API_KEY |
| SSH-Gateway ↔ API | SSH_GATEWAY_API_KEY |
| 容器内 daemon | sandbox 启动时注入的 token，仅对授权连接放行 |

---

> 路径数量统计：A 段 ~115 个、B 段 ~22 个、C 段 ~80 个，总计 **220+ 个 HTTP endpoint**（不含 admin）。这是衡量"重"的一个直接指标。
