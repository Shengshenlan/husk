# @husk/client

Auto-generated TypeScript client for the [Husk](https://github.com/your-org/husk)
control plane API.

## Install

```bash
npm install @husk/client
# or pnpm add @husk/client
```

## Quickstart

```typescript
import createClient from "openapi-fetch"
import type { paths } from "@husk/client"

const client = createClient<paths>({
  baseUrl: "http://localhost:8000",
  headers: { Authorization: "Bearer hk_xxxxxxxxxxxx" },
})

const { data, error } = await client.POST("/api/sandbox", {
  body: { snapshot_id: "py-3.12", cpu: 2, memory_mb: 2048 },
})
console.log(data?.id, data?.state)
```

## Status

Phase 1.7 (M5.8 – M5.10). Currently scaffold-only.

## License

MIT
