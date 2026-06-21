# Husk 快速入门

> 5 分钟跑通一个沙盒。以下内容随 M5 迭代；目前为占位稿。

## 前置要求

- Docker（目前需要 root 权限；rootless 支持在路线图中）
- ~200 MB 磁盘空间，用于 Husk 镜像 + 沙盒快照

## 快速开始（Docker）

```bash
docker run -d --name husk \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v husk-data:/data \
  -e HUSK_ADMIN_USERNAME=admin \
  -e HUSK_ADMIN_PASSWORD=你的密码 \
  husk/husk:latest

# 浏览器打开 Dashboard
open http://localhost:8000

# 或者用 API Key 创建沙盒
curl -X POST http://localhost:8000/api/sandbox \
  -H "Authorization: Bearer hk_xxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"snapshot_id":"py-3.12","cpu":2,"memory_mb":2048}'
```

## 从源码运行

```bash
git clone https://github.com/your-org/husk
cd husk
uv sync
uv run alembic upgrade head
uv run husk serve
```

然后打开 <http://localhost:8000> 进入 Dashboard，或访问 <http://localhost:8000/docs> 查看 OpenAPI 文档。

## 下一步

- [配置说明](./configuration.md)
- [架构详解](../docs/project/ARCHITECTURE.md)
- [SDK 快速入门（Python）](./sdks/python.md)
