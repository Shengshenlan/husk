# 与上游 Daytona 的兼容性

Husk 实现了 Daytona 控制面子集，在协议层与上游 SDK 兼容 —— 已安装 `pip install daytona` 的用户只需修改 `base_url` 即可指向 Husk，大多数操作都能正常工作。

## 已支持的功能

- 沙盒生命周期（创建 / 列表 / 详情 / 启动 / 停止 / 销毁）
- 快照拉取（镜像引用）
- Toolbox 反代（`/api/toolbox/:id/*`）
- 预览 URL（签名）
- API Key 认证（Bearer）
- Stub 端点：`/api/users/me`、`/api/organizations`、`/api/config`

## 已 Stub 的端点

| Daytona 端点 | Husk 行为 |
|---|---|
| `GET /api/users/me` | 返回固定用户 `user_default` |
| `GET /api/organizations` | 返回固定组织 `default` |
| `GET /api/config` | 返回单区域默认值 |
| `Sandbox.organizationId` | 固定为 `org_default` |
| `Sandbox.runnerId` / `region` | 固定为 `default` |

## 未实现的功能

- 多租户：组织、成员、邀请、配额
- 审计日志 API
- Webhook 端点（Svix）
- 声明式镜像构建器
- 沙盒备份/恢复（S3）
- 多 Runner 协调
- Computer-use 端点（最早 Phase 2.x）

完整"不做列表"见 [PLAN.md §7](../docs/project/PLAN.md)。

## 版本策略

Husk 在每个发行版中锁定兼容的上游 Daytona SDK 版本。运行 `tests/compat/` 目录下的测试，对照 `CHANGELOG.md` 中列出的 SDK 版本进行验证。
