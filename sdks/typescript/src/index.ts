/**
 * @husk/client — TypeScript client for the Husk control plane API.
 *
 * Auto-generated path/schema types live in `_generated/schemas.ts`.
 * Use them with `openapi-fetch`:
 *
 *   import createClient from "openapi-fetch"
 *   import type { paths } from "@husk/client"
 *
 *   const client = createClient<paths>({
 *     baseUrl: "http://localhost:8000",
 *     headers: { Authorization: "Bearer hk_..." },
 *   })
 *
 *   const { data } = await client.GET("/api/sandbox")
 */

export type { paths, components, operations } from './_generated/schemas'
export const VERSION = '0.0.1'
