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
