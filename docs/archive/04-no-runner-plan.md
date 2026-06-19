# Daytona-Lite 实施计划（无 Runner / 渐进 MIT 化）

> **修订自 `03-lite-plan.md`**。新方向：**砍掉中间 runner 层**，控制面直连 Docker；分阶段把 AGPL 依赖逐步替换为 MIT 实现。
>
> 终极目标：100% MIT 代码 + 100% MIT 运行时。
> 第一阶段目标：100% MIT 代码 + 极少量 AGPL 容器（daemon），单机一键跑。

---

## 1. 整体架构

### 1.1 三阶段架构图

**Phase 1（v0.1，~5 周）** —— 你的代码 100% MIT，运行时 daemon 仍为上游 AGPL 容器

```
┌──────────────────────────────────────────┐
│  daytona-lite (Python, MIT)              │
│   FastAPI + SQLite + docker-py           │
│   :8000 HTTP/WS                          │
└──────────────┬───────────────────────────┘
               │ Docker socket /var/run/docker.sock
               ▼
┌──────────────────────────────────────────┐
│  Sandbox 容器 (用户的 OCI 镜像)            │
│   ──注入──> /opt/daytona/daemon (AGPL 上游)│
│             :8080 toolbox API            │
└──────────────────────────────────────────┘
```

**Phase 2（v0.5，可选，~6 周追加）** —— 100% MIT 运行时

```
┌──────────────────────────────────────────┐
│  daytona-lite (Python, MIT)              │
└──────────────┬───────────────────────────┘
               │ Docker socket
               ▼
┌──────────────────────────────────────────┐
│  Sandbox 容器                              │
│   ──注入──> lite-daemon (Go, MIT)          │
└──────────────────────────────────────────┘
```

**Phase 3（v1.0，远期）** —— 多机集群（按需）

```
control plane (Python, MIT) ──HTTP──▶ runner-lite (Go, MIT) ──▶ Docker ...
```

### 1.2 Phase 1 vs `03-lite-plan.md` 的区别

| 项 | 旧计划（用上游 runner） | 新计划（无 runner） |
|---|---|---|
| 二进制数 | 3（你 1 + runner + daemon） | 2（你 1 + daemon） |
| 控制面 → 容器路径 | HTTP → runner → docker socket | docker socket（直接） |
| 反调路径要写吗 | 要（~3 天） | 不要 |
| 镜像数 | 3 | 2 |
| 启动复杂度 | compose 3 服务 | docker run 1 服务 |
| Phase 1 总工时 | ~6.5 周 | **~5 周** |

---

## 2. Phase 1 范围

### 2.1 控制面要实现的（Python / FastAPI / MIT）

#### 业务表（SQLite）
```
sandbox          # id, name, snapshot_id, state, labels, ports, created_at, last_activity_at, runner_id="default", region="default"
snapshot         # id, name, image_ref, state
volume           # id, name, docker_volume_name
api_key          # id, name, hash, created_at, last_used_at
ssh_access       # id, sandbox_id, token, expires_at  (Phase 1 可不做)
preview_token    # id, sandbox_id, port, signed_token, expires_at
audit_log        # id, ts, actor, action, target  (可关闭)
```

#### Docker 操作模块（直接调 docker-py，不走 runner）

| 控制面方法 | docker-py 调用 |
|---|---|
| `create_sandbox(snapshot_id, resources)` | `client.images.pull(...) → containers.run(detach=True, name=...)` |
| `start_sandbox(id)` | `containers.get(id).start()` |
| `stop_sandbox(id)` | `containers.get(id).stop(timeout=10)` |
| `destroy_sandbox(id)` | `containers.get(id).remove(force=True, v=True)` |
| `resize_sandbox(id, cpu, mem)` | `containers.get(id).update(cpu_quota=, mem_limit=)` |
| `inject_daemon(id)` | `put_archive('/opt/daytona/', tar(daemon_binary))` |
| `commit_to_snapshot(id, name)` | `containers.get(id).commit(repository=name)` |
| `pull_snapshot(image_ref)` | `client.images.pull(image_ref)` |
| `list_sandboxes()` | `containers.list(all=True, filters={'label':'daytona=true'})` |
| `apply_egress_rules(id, rules)` | `subprocess.run(['iptables', ...])` 或 Docker network |

> **关键认识**：Daytona runner 80% 的代码是封装 Docker SDK 调用 + 多机调度。单机直接用 docker-py，工程量是 runner 的 1/5。

#### HTTP API（与上游兼容子集）

完全照搬 `03-lite-plan.md §5.1`，约 22 个 endpoint。
**`/runners/*` 全部不存在**（控制面就是唯一的执行单元）。
**`/sandbox/for-runner`、`/sandbox/:id/state`、`/jobs/*` 全部不存在**（不需要反调）。

#### Toolbox 反代

`ANY /api/toolbox/:sandboxId/*path` → 控制面查容器 IP + 端口，反代到 daemon。
关键点：daemon 跑在容器内，控制面通过 `containers.get(id).attrs['NetworkSettings']['IPAddress']` 拿到 IP。

#### Preview 反代

`https://{port}-{sandboxId}.preview.example.com` → 控制面反代到 `<container_ip>:{port}`。
v0.1 可以简化为 `http://localhost:8000/preview/<token>/...`，不强求子域名。

### 2.2 daemon 怎么用（Phase 1 仍是上游 AGPL）

**做法**：在控制面创建容器时，在 `containers.run()` 之后立即：
1. `docker cp /lite/embedded/daemon-amd64 <container>:/opt/daytona/daemon`
2. `docker exec <container> chmod +x /opt/daytona/daemon`
3. `docker exec -d <container> /opt/daytona/daemon serve --port 8080`

daemon 二进制从哪里来？
- **方案 A**：构建时 `docker pull daytonaio/daemon:vX.Y.Z` 把里面的二进制拷出来，作为 `embedded/` 目录打进 lite 镜像 → 单镜像可分发
- **方案 B**：运行时 `docker pull daytonaio/daemon:vX.Y.Z` 拿二进制 → 镜像更小但启动慢

**法律边界**：daemon 二进制 AGPL，但你**没修改它**，仅作为运行时二进制嵌入 / 拉取使用。等价于 Linux 发行版打包 GPL 工具链。你的 Python 源码与 daemon 之间是**进程隔离 + HTTP 通信**，不构成衍生作品。

**README 必须声明**：
- 仓库代码：MIT
- 运行时依赖：`daytonaio/daemon` (AGPL-3.0)，链接到上游

### 2.3 鉴权

- **API Key**：`Authorization: Bearer dl_<random>`，存 SQLite，启动时若无则自动生成一个 root key 打到 stdout
- **Toolbox proxy**：通过 control plane 的 API key 鉴权，反代时注入 daemon 的内部 token

---

## 3. Phase 1 里程碑（5 周）

### M0 — 验证可行性（3 天）
- [ ] 起一个上游 daemon 二进制（从 image 拷出来），在普通 ubuntu 容器里裸跑，确认它对"无 organization/region init"能 work
- [ ] Python `docker-py` 起一个容器、`put_archive` 注入二进制、`exec` 启动 daemon、`curl` 容器 IP:8080 拿到 toolbox 响应
- [ ] **如果这步通了，整个项目通了**

### M1 — Skeleton + Sandbox CRUD（1 周）
- [ ] FastAPI 项目骨架，alembic 迁移，SQLite
- [ ] API Key 中间件
- [ ] `POST/GET/DELETE /api/sandbox`、`start`、`stop`
- [ ] docker-py 调用层封装为 `internal/docker.py`
- [ ] daemon 自动注入逻辑
- [ ] 单元测试覆盖 docker-py 模块（用 testcontainers）

### M2 — Toolbox 反代 + Preview（1 周）
- [ ] HTTP / WebSocket 双向反代到 daemon（`httpx` + `websockets`）
- [ ] Preview token 生成、签名、解析
- [ ] 端口反代（同进程）
- [ ] 集成测试：上游 `daytona-sdk` 调用 `process.code_run("print(1)")` 全链路通

### M3 — Snapshot pull + 自动停止（3 天）
- [ ] `POST /api/snapshots`（仅 image pull 类型）
- [ ] `last-activity` 心跳 + asyncio scheduler 自动 stop

### M4 — Lifecycle Polish（1 周）
- [ ] resize、commit-to-snapshot
- [ ] iptables 出站规则（可选简化为 docker network whitelist）
- [ ] 容器异常清理 reaper（启动时扫 DB，孤儿容器/孤儿记录两边对齐）
- [ ] 简单 audit log

### M5 — SDK 兼容 + 打包（5 天）
- [ ] 跑上游 `libs/sdk-python` 的 quickstart 全流程
- [ ] 给上游 dashboard 期待的 stub endpoint：`/users/me`、`/organizations`、`/api/config`
- [ ] Dockerfile 单镜像（python:3.12-slim + lite + 嵌入的 daemon 二进制）
- [ ] `docker run -v /var/run/docker.sock:/var/run/docker.sock daytona-lite` 一行启动

**Phase 1 交付物**：
- ~80MB 镜像（python slim + 你的代码 + 嵌入的 daemon）
- ~100MB 内存常驻
- 1 个进程
- 上游 SDK 100% 兼容（只少一些企业字段）

---

## 4. Phase 2：写自己的 daemon（可选，~6 周）

只有当**你想让运行时也 100% MIT** 时才进。

### 4.1 必做的子集（按 Daytona daemon 80 个 endpoint 排）

| 模块 | endpoint 数 | 工作量 | 是否做 |
|---|---|---|---|
| 文件系统 | 14 | 1 周 | ✅ 必做 |
| 进程 execute / code-run | 2 | 3 天 | ✅ 必做 |
| Session（带状态 shell） | 9 | 1 周 | ✅ 必做 |
| Git wrapper | 11 | 3 天 | ✅ 必做 |
| LSP 桥 | 7 | 1 周 | △ 选做（很多 Agent 用不到） |
| PTY（含 WS） | 6 | 1 周 | △ 选做 |
| Interpreter（持久 Jupyter） | 4 | 1 周 | △ 选做 |
| Computer-use（鼠标/键盘/截屏/a11y） | 24 | **3-4 周** | ✗ 后期 |
| 录屏 | 6 | 1 周 | ✗ 后期 |

**Phase 2 范围**：files + process + session + git，约 36 个 endpoint。
**Phase 2.5 / 3**：LSP / PTY / interpreter
**Phase 4+**：computer-use（这部分换个语言/直接调 xdotool/PyAutoGUI 也许更快）

### 4.2 兼容性

- 严格按上游 daemon 的 OpenAPI schema 实现 → 上游 toolbox-api-client（Apache 2.0）直接能用
- 所有路径、参数、响应字段对齐 → 用户 SDK 无感

### 4.3 语言选择

- **Go**：与上游一致，性能好，单二进制注入容器最方便
- **Python**：和控制面同语言，但容器内塞 Python 解释器太重（~50MB），而且要跨 Linux 发行版兼容

**强烈建议 Go**。daemon 二进制要求"任何 Linux 容器内能跑"，静态链接的 Go 几乎是唯一答案。

### 4.4 里程碑（草稿）

- M6（1 周）：Go skeleton + files API
- M7（2 周）：process / session
- M8（1 周）：git
- M9（1 周）：替换 Phase 1 注入的二进制，跑通 SDK quickstart
- M10（视情况）：LSP / PTY / interpreter

---

## 5. Phase 3：写自己的 runner（远期，多机才需要）

**90% 用户永远不需要 Phase 3。**

只有当你需要：
- 把控制面和执行节点物理分离（控制面在公有云、执行机在用户内网）
- 多台执行机并行
- GPU 节点池

才考虑。届时可以：
- 选项 A：直接用 Docker 自带的 remote API over TLS（零代码，控制面把 docker socket 改 TCP 就行）
- 选项 B：写一个 thin Go runner，等价于"控制面分发 docker 命令的 Agent"

**Phase 3 不在本计划当前阶段范围内**，只列在这里是为了说明架构能扩展。

---

## 6. 法律 / 许可清单

### 6.1 你的仓库
- 全部 MIT
- LICENSE、NOTICE 完整
- 不 vendor 任何 AGPL 源码（包括 `apps/runner/pkg/*` 和 `apps/daemon/pkg/*` 的 Go 文件）

### 6.2 第三方依赖
- `fastapi`, `sqlalchemy`, `httpx`, `pydantic` —— 全部 MIT/BSD/Apache 2.0
- `docker-py` —— Apache 2.0（直接调 Docker socket）
- `libs/api-client-python`（如需对接上游 API） —— Apache 2.0
- `libs/runner-api-client` —— **不需要**（已经不调 runner）
- `libs/toolbox-api-client-python` —— Apache 2.0（用来调 daemon，可选）

### 6.3 运行时（Phase 1）
- 上游 `daytonaio/daemon:vX` 镜像 / 二进制 —— **AGPL-3.0**
- 进程隔离 + HTTP 通信 → 你的代码不被传染
- 在 README / docs / Docker 镜像 manifest 里清晰声明

### 6.4 运行时（Phase 2 之后）
- 全 MIT，无 AGPL 依赖

---

## 7. 风险与权衡

| 风险 | 说明 | 应对 |
|---|---|---|
| Phase 1 仍依赖 AGPL daemon 容器 | 法律上 OK 但商业用户可能不喜欢 | README 透明声明；Phase 2 落地后即解决 |
| 自建 daemon 工作量大 | 对齐上游 80 个 API 不轻松 | 分子集，先 files/process/git，computer-use 永远后置 |
| 上游 daemon 升级 → schema 变化 | 自建 daemon 要跟随 | 锁定一个长期 LTS-like 版本作为兼容目标；CI 跑兼容矩阵 |
| docker-py 性能 | Python 调 Docker socket 在高并发下不如 Go | v1 单机几十个 sandbox 完全够用；高并发场景应该已经走 Phase 3 |
| 单机部署用 docker socket 安全 | 拥有 socket = root | 文档强调用 docker rootless，或 Phase 3 改 socket-proxy |

---

## 8. 决策点（这一版需要确认）

1. **Phase 1 接受用上游 AGPL daemon 容器吗？** 是 → 进入推荐流程；否 → Phase 1 + Phase 2 合并，~10 周才能 v0.1
2. **Phase 1 的 toolbox 反代是 control plane 同进程做，还是单独 sidecar？** 同进程更简单，推荐
3. **Computer-use 是 Phase 2 范围吗？** 强烈建议**否** —— 永远不做或推到 Phase 4，避免拖累主路径

---

## 9. 与 `03-lite-plan.md` 的对比汇总

| 维度 | `03` 旧版 | 本版 |
|---|---|---|
| 中间 runner 层 | 上游 AGPL 容器 | **删** |
| 镜像数 | 3 | **2** |
| 你写的代码 license | MIT 可行 | **MIT 可行** |
| 运行时 AGPL 容器 | runner + daemon 两个 | **仅 daemon 一个** |
| Phase 1 工期 | ~6.5 周 | **~5 周** |
| 100% MIT 运行时是否可达 | 需要重写 daemon + runner | **只需重写 daemon (Phase 2)** |
| 单机部署复杂度 | docker compose 3 服务 | **docker run 1 服务** |
| 多机扩展能力 | 现成（runner 协议在） | 需 Phase 3 重写 runner（90% 用户用不到） |

---

## 10. 一句话总结

**先用 5 周做出"MIT 控制面 + AGPL daemon 容器"的 v0.1，能跑能用、单机一键起；之后 6 周自写 daemon 走到 v0.5，达成 100% MIT 运行时；多机扩展是远期，绝大多数用户用不到。**

这与 Gitea 的渐进式去 GitLab 化是同构的：先做"能用的 80%"，后做"理想的 100%"。
