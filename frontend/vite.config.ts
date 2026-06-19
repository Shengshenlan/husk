import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', ws: true, changeOrigin: true },
      '/preview': { target: 'http://localhost:8000', ws: true, changeOrigin: true },
    },
  },
  build: {
    // Build directly into the backend's static dir so a backend-only image still serves the UI.
    outDir: '../husk/static/dashboard',
    emptyOutDir: true,
    sourcemap: true,
  },
})
