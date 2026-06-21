# 安全模型

Husk 按**单租户**设计。威胁模型假设：

- 一位受信任的操作员在自己的机器或 VM 上运行 Husk
- 该操作员（或通过 Agent）可创建多个沙盒容器
- 沙盒**内部**被视为不可信（运行任意代码）

## 信任边界

| 层级 | 信任度 |
|---|---|
| Host 内核 | 受信任 |
| Host 文件系统 | 受信任（机器归你所有） |
| Husk 控制面 | 受信任（你的代码） |
| 沙盒容器 | **不可信**（运行 Agent / 用户代码） |
| 沙盒网络出站 | 可选限制（M4） |

## 默认加固（M1）

- 沙盒启动时带 `--cap-drop=ALL --security-opt=no-new-privileges`
- 尽可能使用只读根文件系统
- 资源限制（`--cpus`、`--memory`、`--pids-limit`）
- 沙盒容器标记 `husk=true`，便于 Reaper 识别

## Docker Socket = Root

Husk 需要访问 Docker Socket。**任何拥有该权限的人都在 Host 上拥有 root 权限。** 建议缓解措施：

1. 在专用 VM 上运行 Husk
2. 使用 [Docker rootless 模式](https://docs.docker.com/engine/security/rootless/)
3. 使用 [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) 过滤 API 调用（Phase 3+）

## API Key 管理

- 以 argon2 哈希存储
- 明文仅在创建时展示一次
- 前缀 `hk_`，便于日志扫描
- 可通过 `husk apikey revoke <name>` 吊销

## Daemon 二进制完整性（Phase 1）

- 嵌入的上游 daemon 在镜像构建时进行 SHA-256 校验
- 校验值记录在 `embedded/CHECKSUMS`

## 当前不在范围内

- 多租户隔离
- 沙盒间网络策略（除出站白名单外）
- 虚拟机级隔离（gVisor、Kata）—— 可通过 Docker runtime 配置接入，但不内置
