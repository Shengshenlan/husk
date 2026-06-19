# Husk SDKs

Three official client libraries for talking to a Husk control plane.

| Language | Package | Status |
|---|---|---|
| Python | `husk-client` (PyPI) | Phase 1.7 (auto-generated) |
| TypeScript | `@husk/client` (npm) | Phase 1.7 (auto-generated) |
| Go | `github.com/<org>/husk-go` | Phase 1.7 (auto-generated) |

All three are auto-generated from the control plane's OpenAPI spec.
Run `scripts/gen-sdk-clients.sh` to regenerate after schema changes.

For other languages, use `openapi-generator` against `http://<husk>/openapi.json`.
