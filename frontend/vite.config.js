import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // В режиме разработки проксируем /api на локальный FastAPI
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Собранные файлы FastAPI будет раздавать как статику
    outDir: 'dist',
  },
})
