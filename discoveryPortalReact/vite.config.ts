import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// The backend exposes routes under both `/api/*` (auth, notebooks, sources,
// outputs, vector search, qa, mindmap) and `/articles/*` (article search).
// During local dev the Vite server proxies BOTH prefixes to the FastAPI
// backend so the browser only ever talks to the same origin (no CORS).
//
// IMPORTANT: unlike the old Angular proxy, we do NOT rewrite the path — the
// backend routers already include the `/api` prefix, so stripping it would
// 404. Set the backend location with VITE_API_TARGET (defaults to the local
// uvicorn server on :8000).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.VITE_API_TARGET || 'http://localhost:8000';
  const secure = target.startsWith('https');

  return {
    plugins: [react()],
    server: {
      port: 4200,
      proxy: {
        '/api': { target, changeOrigin: true, secure },
        '/articles': { target, changeOrigin: true, secure },
      },
    },
    // Emit a relative-path build so the bundle can be served from any mount
    // point (e.g. mounted as static files on the FastAPI app in the future).
    base: './',
    build: {
      outDir: 'dist',
    },
  };
});
