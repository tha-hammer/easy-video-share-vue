import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // Development server configuration - CRITICAL for CORS
  server: {
    host: true,
    port: 5174,
    // Disable restrictive CORS headers that block API requests
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
      'Cross-Origin-Embedder-Policy': 'unsafe-none',
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Change to your backend URL/port
        changeOrigin: true,
        secure: false,
        // Optionally remove /api prefix if backend does not use it
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  // Preview server configuration for Railway
  preview: {
    host: '0.0.0.0',
    port: process.env.PORT ? parseInt(process.env.PORT) : 4173,
  },
  // Optimize dependencies for AWS SDK
  optimizeDeps: {
    include: ['@aws-sdk/client-s3'],
  },

  // Define global variables for AWS SDK compatibility
  define: {
    global: 'globalThis',
  },
})
