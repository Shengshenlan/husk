// M5.1 placeholder. Real router setup with TanStack Router lands when the
// dashboard milestone starts. For now, render a minimal landing page so
// `pnpm dev` produces something visible.

export function App() {
  return (
    <main style={{ padding: 40, fontFamily: 'inherit' }}>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Husk Dashboard</h1>
      <p style={{ color: '#666' }}>
        Dashboard scaffold — real UI lands in Phase 1.5 (M5.1–M5.7).
      </p>
      <p style={{ color: '#666', marginTop: 8 }}>
        Backend health:{' '}
        <a href="/api/health" target="_blank">
          /api/health
        </a>{' '}
        · Docs:{' '}
        <a href="/docs" target="_blank">
          /docs
        </a>
      </p>
    </main>
  )
}
