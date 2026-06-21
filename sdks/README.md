# Husk SDKs

Four official client libraries for talking to a Husk control plane.

| 目录 | 包名 | 说明 |
|---|---|---|
| `python/` | `husk-client` (PyPI) | Python 控制面 SDK，OpenAPI 自动生成 |
| `typescript/` | `@husk/client` (npm) | TypeScript SDK |
| `go/` | `github.com/husklabs/husk-go` | Go SDK |
| `langchain/` | `langchain-husk` (PyPI) | LangChain Deep Agents 集成 |

前三种语言 SDK 均从控制面的 OpenAPI 自动生成。运行 `./scripts/gen-sdk-clients.sh` 可在 schema 变更后重新生成。

如需其他语言，用 `openapi-generator` 对 `http://<husk>/openapi.json` 生成即可。
