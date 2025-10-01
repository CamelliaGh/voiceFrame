import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/stats': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/fonts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/backgrounds': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/suggested-texts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/simple': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
