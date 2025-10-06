import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build'
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'vocaframe.com',
      'www.vocaframe.com'
    ],
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
      '/admin/config': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin/simple': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/backgrounds': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 3000,
    host: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'vocaframe.com',
      'www.vocaframe.com'
    ]
  }
})
