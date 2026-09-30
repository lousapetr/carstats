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
        // Firefox on Android uses start_url as its home-screen shortcut's ID,
        // and Android launchers keep a shortcut's icon under that ID, so a
        // reinstall with an unchanged start_url brings the old icon back.
        // Bump icon= whenever the icon changes; id keeps the app's identity
        // stable for browsers that key on it instead.
        id: '/',
        start_url: '/?icon=3',
        // PNGs only. Firefox on Android builds an adaptive launcher icon from
        // any maskable entry, and Nova shows that as a blank gray square; with
        // no maskable entry it pins a plain bitmap, which Nova draws. The
        // maskable-icon-*.png files are still generated, just not listed.
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
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
