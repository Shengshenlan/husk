# Husk

> **The husk is the boundary. What runs inside is yours.**

Husk 是一个轻量级 AI 代码沙盒运行时 —— 给 Agent / SDK 提供"创建容器、跑代码、操作文件、做 Git"等高层能力。**MIT 许可、单镜像、单进程、`docker run` 一行启动。**

---

## 安装 & 启动

**仅需 Docker。**

```bash
docker run -d --name husk \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v husk-data:/data \
  -e HUSK_ADMIN_USERNAME=admin \
  -e HUSK_ADMIN_PASSWORD=你的密码 \
  husk/husk:latest
```

启动后打开 <http://localhost:8000>，用上面设置的用户名密码登录 Dashboard，即可在网页上管理沙盒和 API Key。

> 如需从源码运行，见 [docs/getting-started.md](./docs/getting-started.md)。

---

## 写代码调用

### Python SDK（推荐）

```bash
pip install husk-client
```

```python
from husk_client import Husk

husk = Husk(base_url="http://localhost:8000", api_key="hk_...")
sandbox = husk.create(image="python:3.12-slim")

# 执行命令
result = sandbox.process.execute("python -c 'print(1+2)'")
print(result.stdout)   # "3\n"

# 跑代码片段
result = sandbox.process.code_run("print('hello')")
print(result.stdout)   # "hello\n"

# 文件操作
sandbox.fs.upload(path="/workspace/x.txt", content=b"hello")
files = sandbox.fs.list("/workspace")
content = sandbox.fs.download("/workspace/x.txt")

# 用完销毁
sandbox.destroy()
```

API Key 从 Dashboard 的「API Keys」页面创建，或调用 `husk apikey create <name>` CLI 生成。

### LangChain 集成

配合 [Deep Agents](https://github.com/langchain-ai/deepagents) 使用：

```bash
pip install langchain-husk
```

```python
from husk_client import Husk
from langchain_husk import HuskSandbox

# 先创建沙盒
sandbox = Husk(base_url="http://localhost:8000", api_key="hk_...").create(
    image="python:3.12-slim",
)

# 包装为 Deep Agents backend
backend = HuskSandbox(sandbox=sandbox, timeout=300)
result = backend.execute("python -c 'print(1+2)'")
print(result.output, result.exit_code)

# 接入 Deep Agents
# from deepagents import DeepAgent
# agent = DeepAgent(backend=backend, ...)

sandbox.destroy()
```

### 其他语言 SDK

| 语言 | 包名 | 安装 |
|---|---|---|
| Python | `husk-client` | `pip install husk-client` |
| TypeScript | `@husk/client` | `npm install @husk/client` |
| Go | `github.com/husklabs/husk-go` | `go get github.com/husklabs/husk-go` |

所有 SDK 均从控制面的 OpenAPI 自动生成。运行 `./scripts/gen-sdk-clients.sh` 可在 schema 变更后重新生成。

---

## 配置

核心环境变量：

| 变量 | 说明 |
|---|---|
| `HUSK_ADMIN_USERNAME` | Dashboard 登录用户名（默认 `admin`） |
| `HUSK_ADMIN_PASSWORD` | **必须设置**，Dashboard 登录密码 |
| `HUSK_DATA_DIR` | 数据目录（默认 `/data`） |
| `HUSK_DB_URL` | 数据库（默认 SQLite，可换 Postgres） |
| `HUSK_LISTEN_HOST` / `HUSK_LISTEN_PORT` | 监听地址和端口 |

完整配置见 [docs/configuration.md](./docs/configuration.md)。

---

## 许可

仓库代码：MIT（见 [LICENSE](./LICENSE)）

v0.5+ 运行时：100% MIT（含自写 Go daemon）
