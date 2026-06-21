import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useI18n } from '../../lib/i18n'
import * as api from '../../api/client'

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

export default function FileBrowser({ sandboxId, sandboxState }: { sandboxId: string; sandboxState: string }) {
  const { t } = useI18n()
  const [currentPath, setCurrentPath] = useState('/workspace')

  const list = useQuery({
    queryKey: ['toolbox', sandboxId, currentPath],
    queryFn: () => api.toolbox.listDir(sandboxId, currentPath),
    enabled: sandboxState === 'started',
  })

  async function handleDownload(entry: api.FileEntry) {
    try {
      const res = await api.toolbox.download(sandboxId, entry.path)
      const disposition = res.headers.get('Content-Disposition') ?? ''
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      const filename = match ? match[1].replace(/['"]/g, '') : entry.name
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert(t.sandboxes.files.downloadError)
    }
  }

  if (sandboxState !== 'started') {
    return <p className="muted">{t.sandboxes.files.notRunning}</p>
  }

  const segments = currentPath.split('/').filter(Boolean)

  return (
    <>
      <nav className="breadcrumb">
        <a onClick={() => setCurrentPath('/')}>{t.sandboxes.files.root}</a>
        {segments.map((seg, i) => {
          const path = '/' + segments.slice(0, i + 1).join('/')
          return (
            <span key={path}>
              <span className="sep">/</span>
              <a onClick={() => setCurrentPath(path)}>{seg}</a>
            </span>
          )
        })}
      </nav>

      {list.isLoading && <p>{t.sandboxes.files.loading}</p>}
      {list.error && <div className="error">{t.sandboxes.files.error}</div>}
      {list.data && list.data.entries.length === 0 && (
        <div className="empty">{t.sandboxes.files.empty}</div>
      )}
      {list.data && list.data.entries.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>{t.sandboxes.files.name}</th>
              <th>{t.sandboxes.files.size}</th>
              <th>{t.sandboxes.files.modified}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.data.entries.map((entry) => (
              <tr key={entry.path}>
                <td>
                  <span className="file-name">
                    <span className="file-icon">{entry.is_dir ? '\uD83D\uDCC1' : '\uD83D\uDCC4'}</span>
                    {entry.is_dir ? (
                      <a onClick={() => setCurrentPath(entry.path)}>{entry.name}</a>
                    ) : (
                      entry.name
                    )}
                  </span>
                </td>
                <td className="muted">{entry.is_dir ? '—' : formatSize(entry.size)}</td>
                <td className="muted">{new Date(entry.mod_time).toLocaleString()}</td>
                <td>
                  {!entry.is_dir && (
                    <button onClick={() => handleDownload(entry)}>{t.sandboxes.files.download}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}