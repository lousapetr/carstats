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
      // pwa-*.png / maskable-icon-*.png are generated from favicon.svg and
      // icon-source/favicon-maskable.svg via ImageMagick — regenerate rather
      // than hand-edit if the source design changes.
      workbox: {
        // Google OAuth redirects (/auth/login, /auth/callback) are real
        // server navigations, not SPA routes — without this the service
        // worker's catch-all navigation fallback serves the cached
        // index.html for them instead of letting them reach the backend,
        // silently breaking login.
        navigateFallbackDenylist: [/^\/auth\//],
      },
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
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          // Full-bleed variant with the car glyph confined to the safe zone,
          // for Android/Nova Launcher's adaptive (maskable) home-screen icon.
          { src: 'maskable-icon-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
          { src: 'maskable-icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
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
