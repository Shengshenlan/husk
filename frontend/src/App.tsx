import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from './api/client'

export function App() {
  const [token, setToken] = useState(api.getToken())

  if (!token) return <Login onLogin={(t) => { api.setToken(t); setToken(t) }} />

  return <Layout onLogout={() => { api.clearToken(); setToken('') }} />
}

// ── Login ──

function Login({ onLogin }: { onLogin: (t: string) => void }) {
  const [val, setVal] = useState('')
  const [err, setErr] = useState('')
  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ minWidth: 400 }}>
        <h1>Husk</h1>
        <p className="muted">Paste your API key to sign in.</p>
        <input
          type="password"
          placeholder="hk_..."
          value={val}
          onChange={(e) => setVal(e.target.value)}
          style={{ width: '100%', marginBottom: 12 }}
          onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
        />
        {err && <div className="error">{err}</div>}
        <button className="primary" onClick={submit} style={{ width: '100%' }}>
          Sign in
        </button>
        <p className="muted" style={{ marginTop: 16, fontSize: 12 }}>
          New install? Run <code>husk apikey create root</code> on your server.
        </p>
      </div>
    </div>
  )
  function submit() {
    if (!val.startsWith('hk_')) { setErr('API keys start with hk_'); return }
    onLogin(val.trim())
  }
}

// ── Layout ──

function Layout({ onLogout }: { onLogout: () => void }) {
  const [page, setPage] = useState<'sandboxes' | 'snapshots' | 'keys' | 'settings'>('sandboxes')
  return (
    <div className="layout">
      <div className="sidebar">
        <h1>Husk</h1>
        <a className={page === 'sandboxes' ? 'active' : ''} onClick={() => setPage('sandboxes')}>Sandboxes</a>
        <a className={page === 'snapshots' ? 'active' : ''} onClick={() => setPage('snapshots')}>Snapshots</a>
        <a className={page === 'keys' ? 'active' : ''} onClick={() => setPage('keys')}>API Keys</a>
        <a className={page === 'settings' ? 'active' : ''} onClick={() => setPage('settings')}>Settings</a>
        <a onClick={onLogout} style={{ marginTop: 40, color: 'var(--muted)' }}>Sign out</a>
      </div>
      <div className="main">
        {page === 'sandboxes' && <SandboxesPage />}
        {page === 'snapshots' && <SnapshotsPage />}
        {page === 'keys' && <KeysPage />}
        {page === 'settings' && <SettingsPage />}
      </div>
    </div>
  )
}

// ── Sandboxes ──

function SandboxesPage() {
  const qc = useQueryClient()
  const list = useQuery({
    queryKey: ['sandboxes'],
    queryFn: api.sandboxes.list,
    refetchInterval: 5000,
  })
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)

  const create = useMutation({
    mutationFn: (body: api.CreateSandboxRequest) => api.sandboxes.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  })
  const start = useMutation({
    mutationFn: api.sandboxes.start,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  })
  const stop = useMutation({
    mutationFn: api.sandboxes.stop,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  })
  const destroy = useMutation({
    mutationFn: api.sandboxes.destroy,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  })

  if (selected) {
    const sb = list.data?.find((s) => s.id === selected)
    return <SandboxDetail sb={sb!} onBack={() => setSelected(null)} />
  }

  return (
    <>
      <div className="row" style={{ marginBottom: 20 }}>
        <h2>Sandboxes</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setCreating(true)}>+ New Sandbox</button>
      </div>

      {list.isLoading && <p>Loading…</p>}
      {list.error && <div className="error">{(list.error as Error).message}</div>}
      {list.data?.length === 0 && (
        <div className="empty">No sandboxes yet. Click "New Sandbox" to create one.</div>
      )}
      {list.data && list.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Image</th>
              <th>State</th>
              <th>Resources</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.data.map((sb) => (
              <tr key={sb.id}>
                <td>
                  <a onClick={() => setSelected(sb.id)}>{sb.name}</a>
                  <div className="muted" style={{ fontSize: 11 }}>{sb.id}</div>
                </td>
                <td className="muted">{sb.snapshot_id ?? '—'}</td>
                <td><span className={`badge ${sb.state}`}>{sb.state}</span></td>
                <td className="muted">{sb.cpu}c / {sb.memory_mb}m</td>
                <td>
                  {sb.state === 'started' && (
                    <button onClick={() => stop.mutate(sb.id)}>Stop</button>
                  )}
                  {sb.state === 'stopped' && (
                    <button onClick={() => start.mutate(sb.id)}>Start</button>
                  )}
                  <button className="danger" style={{ marginLeft: 8 }}
                          onClick={() => { if (confirm(`Destroy ${sb.name}?`)) destroy.mutate(sb.id) }}>
                    Destroy
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {creating && <CreateDialog onClose={() => setCreating(false)} onCreate={(b) => { create.mutate(b); setCreating(false) }} />}
    </>
  )
}

function CreateDialog({ onClose, onCreate }: { onClose: () => void; onCreate: (b: api.CreateSandboxRequest) => void }) {
  const [name, setName] = useState('')
  const [image, setImage] = useState('alpine:3.20')
  const [cpu, setCpu] = useState(1)
  const [mem, setMem] = useState(512)
  return (
    <dialog open>
      <h3>Create Sandbox</h3>
      <div style={{ display: 'grid', gap: 10, marginBottom: 16 }}>
        <label>Name <input value={name} onChange={(e) => setName(e.target.value)} placeholder="auto-generated" style={{ width: '100%' }} /></label>
        <label>Image <input value={image} onChange={(e) => setImage(e.target.value)} style={{ width: '100%' }} /></label>
        <label>CPU <input type="number" min={1} max={64} value={cpu} onChange={(e) => setCpu(+e.target.value)} /></label>
        <label>Memory MB <input type="number" min={128} value={mem} onChange={(e) => setMem(+e.target.value)} /></label>
      </div>
      <div className="row">
        <div className="spacer" />
        <button onClick={onClose}>Cancel</button>
        <button className="primary" style={{ marginLeft: 8 }}
                onClick={() => onCreate({ name: name || undefined, snapshot_id: image, cpu, memory_mb: mem })}>
          Create
        </button>
      </div>
    </dialog>
  )
}

function SandboxDetail({ sb, onBack }: { sb: api.Sandbox; onBack: () => void }) {
  return (
    <>
      <a onClick={onBack}>← Back to sandboxes</a>
      <h2 style={{ marginTop: 12 }}>{sb.name}</h2>

      <div className="card">
        <h3>Overview</h3>
        <dl className="kv">
          <dt>ID</dt><dd>{sb.id}</dd>
          <dt>State</dt><dd><span className={`badge ${sb.state}`}>{sb.state}</span></dd>
          <dt>Image</dt><dd>{sb.snapshot_id ?? '—'}</dd>
          <dt>CPU / Memory</dt><dd>{sb.cpu} cores / {sb.memory_mb} MB</dd>
          <dt>Disk</dt><dd>{sb.disk_gb} GB</dd>
          <dt>Auto-stop</dt><dd>{sb.auto_stop_interval ? `${sb.auto_stop_interval}s` : '—'}</dd>
          <dt>Last activity</dt><dd>{sb.last_activity_at ?? '—'}</dd>
          <dt>Created</dt><dd>{sb.created_at}</dd>
        </dl>
      </div>

      <div className="card">
        <h3>Toolbox</h3>
        <p className="muted">
          Toolbox API is reverse-proxied at <code>/api/toolbox/{sb.id}/*</code>.
          Try: <code>GET /api/toolbox/{sb.id}/files?path=/</code>
        </p>
        <p className="muted">
          (xterm.js terminal lands when daemon binary is embedded — set HUSK_DAEMON_BIN.)
        </p>
      </div>
    </>
  )
}

// ── Snapshots ──

function SnapshotsPage() {
  const qc = useQueryClient()
  const list = useQuery({ queryKey: ['snapshots'], queryFn: api.snapshots.list })
  const [pulling, setPulling] = useState(false)
  const [name, setName] = useState('')
  const [ref, setRef] = useState('alpine:3.20')

  const create = useMutation({
    mutationFn: () => api.snapshots.create(name, ref),
    onSuccess: () => { setPulling(false); setName(''); qc.invalidateQueries({ queryKey: ['snapshots'] }) },
  })
  const destroy = useMutation({
    mutationFn: api.snapshots.destroy,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['snapshots'] }),
  })

  return (
    <>
      <div className="row" style={{ marginBottom: 20 }}>
        <h2>Snapshots</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setPulling(true)}>+ Pull image</button>
      </div>

      {list.data?.length === 0 && <div className="empty">No snapshots yet.</div>}
      {list.data && list.data.length > 0 && (
        <table>
          <thead><tr><th>Name</th><th>Image</th><th>State</th><th>Created</th><th></th></tr></thead>
          <tbody>
            {list.data.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td className="muted">{s.image_ref}</td>
                <td><span className={`badge ${s.state}`}>{s.state}</span></td>
                <td className="muted">{s.created_at}</td>
                <td>
                  <button className="danger" onClick={() => { if (confirm(`Delete ${s.name}?`)) destroy.mutate(s.id) }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {pulling && (
        <dialog open>
          <h3>Pull image as snapshot</h3>
          <div style={{ display: 'grid', gap: 10 }}>
            <label>Name <input value={name} onChange={(e) => setName(e.target.value)} /></label>
            <label>Image ref <input value={ref} onChange={(e) => setRef(e.target.value)} /></label>
          </div>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button onClick={() => setPulling(false)}>Cancel</button>
            <button className="primary" style={{ marginLeft: 8 }}
                    disabled={!name || create.isPending}
                    onClick={() => create.mutate()}>
              {create.isPending ? 'Pulling…' : 'Pull'}
            </button>
          </div>
          {create.error && <div className="error" style={{ marginTop: 12 }}>{(create.error as Error).message}</div>}
        </dialog>
      )}
    </>
  )
}

// ── API Keys ──

function KeysPage() {
  const qc = useQueryClient()
  const list = useQuery({ queryKey: ['keys'], queryFn: api.apiKeys.list })
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [shown, setShown] = useState<api.ApiKeyCreated | null>(null)

  const create = useMutation({
    mutationFn: () => api.apiKeys.create(name),
    onSuccess: (k) => { setShown(k); setCreating(false); setName(''); qc.invalidateQueries({ queryKey: ['keys'] }) },
  })
  const revoke = useMutation({
    mutationFn: api.apiKeys.revoke,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['keys'] }),
  })

  return (
    <>
      <div className="row" style={{ marginBottom: 20 }}>
        <h2>API Keys</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setCreating(true)}>+ New key</button>
      </div>

      {list.data?.length === 0 && <div className="empty">No keys.</div>}
      {list.data && list.data.length > 0 && (
        <table>
          <thead><tr><th>Name</th><th>Prefix</th><th>Created</th><th>Last used</th><th></th></tr></thead>
          <tbody>
            {list.data.map((k) => (
              <tr key={k.id}>
                <td>{k.name}</td>
                <td><code>{k.prefix}…</code></td>
                <td className="muted">{k.created_at}</td>
                <td className="muted">{k.last_used_at ?? '—'}</td>
                <td>
                  <button className="danger" onClick={() => { if (confirm(`Revoke ${k.name}?`)) revoke.mutate(k.name) }}>
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {creating && (
        <dialog open>
          <h3>Create API key</h3>
          <label>Name <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: '100%' }} /></label>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button onClick={() => setCreating(false)}>Cancel</button>
            <button className="primary" style={{ marginLeft: 8 }} disabled={!name} onClick={() => create.mutate()}>
              Create
            </button>
          </div>
        </dialog>
      )}

      {shown && (
        <dialog open>
          <h3>API key created — save it now</h3>
          <p>This is the only time you'll see the plaintext key.</p>
          <code style={{ display: 'block', padding: 12, background: 'var(--hover)', wordBreak: 'break-all' }}>
            {shown.key}
          </code>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button className="primary" onClick={() => setShown(null)}>I've saved it</button>
          </div>
        </dialog>
      )}
    </>
  )
}

// ── Settings ──

function SettingsPage() {
  const h = useQuery({ queryKey: ['health'], queryFn: api.health.get })
  return (
    <>
      <h2>Settings</h2>
      <div className="card">
        <h3>Server</h3>
        <dl className="kv">
          <dt>Version</dt><dd>{h.data?.version ?? '—'}</dd>
          <dt>Status</dt><dd>{h.data?.status ?? '—'}</dd>
        </dl>
      </div>
      <div className="card">
        <h3>About</h3>
        <p>
          <a href="https://github.com/your-org/husk" target="_blank">GitHub</a> ·{' '}
          <a href="/docs" target="_blank">OpenAPI</a> ·{' '}
          <a href="/openapi.json" target="_blank">Schema</a>
        </p>
        <p className="muted" style={{ fontSize: 12 }}>
          Husk is MIT-licensed. Phase 1 runtime embeds the upstream Daytona daemon (AGPL).
        </p>
      </div>
    </>
  )
}

// Suppress unused-import warning if we add useEffect-based polling later
void useEffect
