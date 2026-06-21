// Husk API client — thin wrapper around fetch that adds Authorization
// and parses errors into JS Error.

const TOKEN_KEY = 'husk-api-key'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? ''
}

export function setToken(t: string): void {
  localStorage.setItem(TOKEN_KEY, t)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const j = await res.json()
      detail = j.message ?? j.detail ?? JSON.stringify(j)
    } catch {
      detail = await res.text()
    }
    throw new Error(`${res.status} ${detail}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ── Sandbox ──

export interface Sandbox {
  id: string
  name: string
  snapshot_id: string | null
  state: string
  cpu: number
  memory_mb: number
  disk_gb: number
  labels: Record<string, string>
  runner_id: string
  region: string
  auto_stop_interval: number | null
  last_activity_at: string | null
  created_at: string
  updated_at: string
}

export interface CreateSandboxRequest {
  name?: string
  snapshot_id?: string
  cpu?: number
  memory_mb?: number
  disk_gb?: number
  labels?: Record<string, string>
  auto_stop_interval?: number
}

export const sandboxes = {
  list: () => request<Sandbox[]>('GET', '/api/sandbox'),
  get: (id: string) => request<Sandbox>('GET', `/api/sandbox/${id}`),
  create: (body: CreateSandboxRequest) => request<Sandbox>('POST', '/api/sandbox', body),
  start: (id: string) => request<Sandbox>('POST', `/api/sandbox/${id}/start`),
  stop: (id: string) => request<Sandbox>('POST', `/api/sandbox/${id}/stop`),
  destroy: (id: string) => request<void>('DELETE', `/api/sandbox/${id}`),
}

// ── Snapshots ──

export interface Snapshot {
  id: string
  name: string
  image_ref: string
  state: string
  size_bytes: number | null
  created_at: string
}

export const snapshots = {
  list: () => request<Snapshot[]>('GET', '/api/snapshots'),
  create: (name: string, image_ref: string) =>
    request<Snapshot>('POST', '/api/snapshots', { name, image_ref }),
  destroy: (id: string) => request<void>('DELETE', `/api/snapshots/${id}`),
}

// ── API Keys ──

export interface ApiKey {
  id: string
  name: string
  prefix: string
  created_at: string
  last_used_at: string | null
}

export interface ApiKeyCreated extends ApiKey {
  key: string
}

export const apiKeys = {
  list: () => request<ApiKey[]>('GET', '/api/api-keys'),
  create: (name: string) => request<ApiKeyCreated>('POST', '/api/api-keys', { name }),
  revoke: (name: string) => request<void>('DELETE', `/api/api-keys/${name}`),
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  username: string
}

export const auth = {
  login: (body: LoginRequest) => request<LoginResponse>('POST', '/api/auth/login', body),
  me: () => request<UserResponse>('GET', '/api/auth/me'),
}

// ── Health ──

export interface Health {
  status: string
  version: string
}

export const health = {
  get: () => request<Health>('GET', '/api/health'),
}
