import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'CarStats',
        short_name: 'CarStats',
        description: 'Evidence tankování, servisu a nákladů na auto',
        lang: 'cs',
        theme_color: '#111827',
        background_color: '#111827',
        display: 'standalone',
        start_url: '/',
        icons: [
          // Transparent-background icon: "any" only. "maskable" needs a
          // full-bleed, opaque design or it renders broken on Android's
          // adaptive home-screen icon system.
          { src: 'favicon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
    },
  },
  build: {
    // Single-user app served as one bundle; not worth code-splitting.
    chunkSizeWarningLimit: 2000,
  },
})
