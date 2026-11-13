import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { loopbackProxy } from './config/loopback';
export default defineConfig({
  plugins: [react(), tailwindcss(), { name: 'private-path-denial', configureServer(server) { server.middlewares.use((req, res, next) => { const path = decodeURI((req.url || '/').split('?')[0]); if (/^\/(?:\.env(?:[./]|$)|\.git(?:\/|$))/.test(path)) { res.statusCode = 404; res.end('Not found'); return; } next(); }); } }],
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true, allowedHosts: ['localhost'],
    fs: { strict: true, allow: [process.cwd()] },
    proxy: { '/v1': { target: loopbackProxy(process.env.SENTINEL_PROXY_TARGET), changeOrigin: false } },
    headers: { 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff' }
  },
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], include: ['src/**/*.test.ts?(x)'], restoreMocks: true }
});
