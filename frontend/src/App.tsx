import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useI18n } from './lib/i18n'
import * as api from './api/client'
import FileBrowser from './components/files/FileBrowser'

export function App() {
  const [token, setToken] = useState(api.getToken())

  useEffect(() => {
    const handler = () => setToken('')
    window.addEventListener('husk:auth-expired', handler)
    return () => window.removeEventListener('husk:auth-expired', handler)
  }, [])

  if (!token) return <Login onLogin={(t) => { api.setToken(t); setToken(t) }} />

  return <Layout onLogout={() => { api.clearToken(); setToken('') }} />
}

function Login({ onLogin }: { onLogin: (t: string) => void }) {
  const { t } = useI18n()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit() {
    if (!username || !password) {
      setErr(t.login.required)
      return
    }
    setLoading(true)
    setErr('')
    try {
      const res = await api.auth.login({ username, password })
      onLogin(res.access_token)
    } catch (e: any) {
      setErr(e.message || t.login.error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ minWidth: 400 }}>
        <h1>{t.appName}</h1>
        <p className="muted">{t.login.title}</p>
        <div style={{ display: 'grid', gap: 10, marginBottom: 12 }}>
          <label>
            {t.login.username}
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%' }}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
            />
          </label>
          <label>
            {t.login.password}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%' }}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
            />
          </label>
        </div>
        {err && <div className="error">{err}</div>}
        <button className="primary" onClick={submit} style={{ width: '100%' }} disabled={loading}>
          {loading ? '...' : t.login.submit}
        </button>
      </div>
    </div>
  )
}

function Layout({ onLogout }: { onLogout: () => void }) {
  const { t, locale, setLocale } = useI18n()
  const [page, setPage] = useState<'sandboxes' | 'snapshots' | 'keys' | 'settings'>('sandboxes')
  return (
    <div className="layout">
      <div className="sidebar">
        <h1>{t.appName}</h1>
        <a className={page === 'sandboxes' ? 'active' : ''} onClick={() => setPage('sandboxes')}>{t.nav.sandboxes}</a>
        <a className={page === 'snapshots' ? 'active' : ''} onClick={() => setPage('snapshots')}>{t.nav.snapshots}</a>
        <a className={page === 'keys' ? 'active' : ''} onClick={() => setPage('keys')}>{t.nav.keys}</a>
        <a className={page === 'settings' ? 'active' : ''} onClick={() => setPage('settings')}>{t.nav.settings}</a>
        <a onClick={onLogout} style={{ marginTop: 40, color: 'var(--muted)' }}>{t.nav.logout}</a>
        <div style={{ marginTop: 20, padding: '0 20px' }}>
          <select value={locale} onChange={(e) => setLocale(e.target.value as any)} style={{ width: '100%' }}>
            <option value="zh-CN">中文</option>
            <option value="en-US">English</option>
          </select>
        </div>
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

function SandboxesPage() {
  const { t } = useI18n()
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
    if (!sb) return null
    return <SandboxDetail sb={sb} onBack={() => setSelected(null)} />
  }

  return (
    <>
      <div className="row" style={{ marginBottom: 20 }}>
        <h2>{t.sandboxes.title}</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setCreating(true)}>+ {t.sandboxes.new}</button>
      </div>

      {list.isLoading && <p>{t.sandboxes.loading}</p>}
      {list.error && <div className="error">{(list.error as Error).message}</div>}
      {list.data?.length === 0 && (
        <div className="empty">{t.sandboxes.empty}</div>
      )}
      {list.data && list.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>{t.sandboxes.name}</th>
              <th>{t.sandboxes.image}</th>
              <th>{t.sandboxes.state}</th>
              <th>{t.sandboxes.resources}</th>
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
                    <button onClick={() => stop.mutate(sb.id)}>{t.sandboxes.stop}</button>
                  )}
                  {sb.state === 'stopped' && (
                    <button onClick={() => start.mutate(sb.id)}>{t.sandboxes.start}</button>
                  )}
                  <button className="danger" style={{ marginLeft: 8 }}
                          onClick={() => { if (confirm(t.common.confirmDestroy(sb.name))) destroy.mutate(sb.id) }}>
                    {t.sandboxes.destroy}
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
  const { t } = useI18n()
  const [name, setName] = useState('')
  const [image, setImage] = useState('alpine:3.20')
  const [cpu, setCpu] = useState(1)
  const [mem, setMem] = useState(512)
  return (
    <dialog open>
      <h3>{t.sandboxes.createTitle}</h3>
      <div style={{ display: 'grid', gap: 10, marginBottom: 16 }}>
        <label>{t.sandboxes.nameLabel} <input value={name} onChange={(e) => setName(e.target.value)} placeholder="auto-generated" style={{ width: '100%' }} /></label>
        <label>{t.sandboxes.imageLabel} <input value={image} onChange={(e) => setImage(e.target.value)} style={{ width: '100%' }} /></label>
        <label>{t.sandboxes.cpuLabel} <input type="number" min={1} max={64} value={cpu} onChange={(e) => setCpu(+e.target.value)} /></label>
        <label>{t.sandboxes.memoryLabel} <input type="number" min={128} value={mem} onChange={(e) => setMem(+e.target.value)} /></label>
      </div>
      <div className="row">
        <div className="spacer" />
        <button onClick={onClose}>{t.sandboxes.cancel}</button>
        <button className="primary" style={{ marginLeft: 8 }}
                onClick={() => onCreate({ name: name || undefined, snapshot_id: image, cpu, memory_mb: mem })}>
          {t.sandboxes.create}
        </button>
      </div>
    </dialog>
  )
}

function SandboxDetail({ sb, onBack }: { sb: api.Sandbox; onBack: () => void }) {
  const { t } = useI18n()
  return (
    <>
      <a onClick={onBack}>← {t.sandboxes.back}</a>
      <h2 style={{ marginTop: 12 }}>{sb.name}</h2>

      <div className="card">
        <h3>{t.sandboxes.overview}</h3>
        <dl className="kv">
          <dt>{t.sandboxes.id}</dt><dd>{sb.id}</dd>
          <dt>{t.sandboxes.state}</dt><dd><span className={`badge ${sb.state}`}>{sb.state}</span></dd>
          <dt>{t.sandboxes.image}</dt><dd>{sb.snapshot_id ?? '—'}</dd>
          <dt>CPU / {t.sandboxes.memoryLabel}</dt><dd>{sb.cpu} cores / {sb.memory_mb} MB</dd>
          <dt>{t.sandboxes.disk}</dt><dd>{sb.disk_gb} GB</dd>
          <dt>{t.sandboxes.autoStop}</dt><dd>{sb.auto_stop_interval ? `${sb.auto_stop_interval}s` : '—'}</dd>
          <dt>{t.sandboxes.lastActivity}</dt><dd>{sb.last_activity_at ?? '—'}</dd>
          <dt>{t.sandboxes.created}</dt><dd>{sb.created_at}</dd>
        </dl>
      </div>

      <div className="card">
        <h3>{t.sandboxes.toolbox}</h3>
        <p className="muted">
          {t.sandboxes.toolboxHint} <code>/api/toolbox/{sb.id}/*</code>.
        </p>
      </div>

      <div className="card">
        <h3>{t.sandboxes.files.title}</h3>
        <FileBrowser sandboxId={sb.id} sandboxState={sb.state} />
      </div>
    </>
  )
}

function SnapshotsPage() {
  const { t } = useI18n()
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
        <h2>{t.snapshots.title}</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setPulling(true)}>+ {t.snapshots.pull}</button>
      </div>

      {list.data?.length === 0 && <div className="empty">{t.snapshots.empty}</div>}
      {list.data && list.data.length > 0 && (
        <table>
          <thead><tr><th>{t.snapshots.name}</th><th>{t.snapshots.imageRef}</th><th>{t.sandboxes.state}</th><th>{t.snapshots.created}</th><th></th></tr></thead>
          <tbody>
            {list.data.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td className="muted">{s.image_ref}</td>
                <td><span className={`badge ${s.state}`}>{s.state}</span></td>
                <td className="muted">{s.created_at}</td>
                <td>
                  <button className="danger" onClick={() => { if (confirm(t.common.confirmDelete(s.name))) destroy.mutate(s.id) }}>
                    {t.snapshots.delete}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {pulling && (
        <dialog open>
          <h3>{t.snapshots.pullTitle}</h3>
          <div style={{ display: 'grid', gap: 10 }}>
            <label>{t.snapshots.imageName} <input value={name} onChange={(e) => setName(e.target.value)} /></label>
            <label>{t.snapshots.imageRefLabel} <input value={ref} onChange={(e) => setRef(e.target.value)} /></label>
          </div>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button onClick={() => setPulling(false)}>{t.sandboxes.cancel}</button>
            <button className="primary" style={{ marginLeft: 8 }}
                    disabled={!name || create.isPending}
                    onClick={() => create.mutate()}>
              {create.isPending ? t.snapshots.pulling : t.snapshots.pull}
            </button>
          </div>
          {create.error && <div className="error" style={{ marginTop: 12 }}>{(create.error as Error).message}</div>}
        </dialog>
      )}
    </>
  )
}

function KeysPage() {
  const { t } = useI18n()
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
        <h2>{t.apiKeys.title}</h2>
        <div className="spacer" />
        <button className="primary" onClick={() => setCreating(true)}>+ {t.apiKeys.new}</button>
      </div>

      {list.data?.length === 0 && <div className="empty">{t.apiKeys.empty}</div>}
      {list.data && list.data.length > 0 && (
        <table>
          <thead><tr><th>{t.apiKeys.name}</th><th>{t.apiKeys.prefix}</th><th>{t.apiKeys.created}</th><th>{t.apiKeys.lastUsed}</th><th></th></tr></thead>
          <tbody>
            {list.data.map((k) => (
              <tr key={k.id}>
                <td>{k.name}</td>
                <td><code>{k.prefix}…</code></td>
                <td className="muted">{k.created_at}</td>
                <td className="muted">{k.last_used_at ?? '—'}</td>
                <td>
                  <button className="danger" onClick={() => { if (confirm(t.common.confirmRevoke(k.name))) revoke.mutate(k.name) }}>
                    {t.apiKeys.revoke}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {creating && (
        <dialog open>
          <h3>{t.apiKeys.createTitle}</h3>
          <label>{t.apiKeys.name} <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: '100%' }} /></label>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button onClick={() => setCreating(false)}>{t.sandboxes.cancel}</button>
            <button className="primary" style={{ marginLeft: 8 }} disabled={!name} onClick={() => create.mutate()}>
              {t.sandboxes.create}
            </button>
          </div>
        </dialog>
      )}

      {shown && (
        <dialog open>
          <h3>{t.apiKeys.saveNow}</h3>
          <p>{t.apiKeys.saveHint}</p>
          <code style={{ display: 'block', padding: 12, background: 'var(--hover)', wordBreak: 'break-all' }}>
            {shown.key}
          </code>
          <div className="row" style={{ marginTop: 16 }}>
            <div className="spacer" />
            <button className="primary" onClick={() => setShown(null)}>{t.apiKeys.saved}</button>
          </div>
        </dialog>
      )}
    </>
  )
}

function SettingsPage() {
  const { t } = useI18n()
  const h = useQuery({ queryKey: ['health'], queryFn: api.health.get })
  return (
    <>
      <h2>{t.settings.title}</h2>
      <div className="card">
        <h3>{t.settings.server}</h3>
        <dl className="kv">
          <dt>{t.settings.version}</dt><dd>{h.data?.version ?? '—'}</dd>
          <dt>{t.settings.status}</dt><dd>{h.data?.status ?? '—'}</dd>
        </dl>
      </div>
      <div className="card">
        <h3>{t.settings.about}</h3>
        <p>
          <a href="https://github.com/your-org/husk" target="_blank">{t.settings.github}</a> ·{' '}
          <a href="/docs" target="_blank">{t.settings.openapi}</a> ·{' '}
          <a href="/openapi.json" target="_blank">{t.settings.schema}</a>
        </p>
        <p className="muted" style={{ fontSize: 12 }}>
          {t.settings.license}
        </p>
      </div>
    </>
  )
}

void useEffect
