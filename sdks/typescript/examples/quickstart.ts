/**
 * Quickstart: create a sandbox, list, destroy.
 *
 * Run with:  npx tsx quickstart.ts
 */
import createClient from 'openapi-fetch'
import type { paths } from '../src'

const client = createClient<paths>({
  baseUrl: 'http://localhost:8000',
  headers: { Authorization: 'Bearer hk_xxxxxxxxxxxx' },
})

const { data: sb, error } = await client.POST('/api/sandbox', {
  body: { snapshot_id: 'alpine:3.20', cpu: 1, memory_mb: 512 },
})
if (error) throw new Error(JSON.stringify(error))
console.log(`Created sandbox ${sb!.id} state=${sb!.state}`)

const { data: list } = await client.GET('/api/sandbox')
console.log(`Total sandboxes: ${list?.length}`)

await client.DELETE('/api/sandbox/{sandbox_id}', {
  params: { path: { sandbox_id: sb!.id } },
})
console.log(`Destroyed ${sb!.id}`)
