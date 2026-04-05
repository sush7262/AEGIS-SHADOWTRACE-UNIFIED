# ShadowTrace AI — Frontend

Vite + React dashboard with D3 force graph and Recharts analytics.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

By default the dev server proxies `/api/*` to `http://127.0.0.1:8000`. To call a remote API instead, set:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

When `VITE_API_URL` is set, requests go directly to that origin (ensure CORS is enabled on the backend — already allowed for localhost dev ports).

## Build

```bash
npm run build
npm run preview
```
