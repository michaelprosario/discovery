# Discovery Portal (React)

A React front-end for the Discovery API — a local NotebookLM-style research app.
Built with **Vite + React + TypeScript**, **TanStack Query** for server state, and
**React Router**. Styling is plain CSS (a global theme in `src/styles/theme.css`
plus a few CSS Modules).

This is a rewrite of the Angular `discoveryPortal`, targeting the backend's
**local JWT auth** (not Firebase).

## Prerequisites

- Node.js 20+ (developed on Node 24)
- The Discovery FastAPI backend running locally (default `http://localhost:8000`)

## Quick start

```bash
cd discoveryPortalReact
npm install
cp .env.example .env   # optional — adjust VITE_API_TARGET if needed
npm run dev
```

The dev server runs on http://localhost:4200.

## How the backend connection works (dev)

The Vite dev server **proxies** API calls to the FastAPI backend so the browser
only ever talks to one origin (no CORS). Configured in `vite.config.ts`:

- `/api/*`  → backend (auth, notebooks, sources, outputs, vector search, Q&A)
- `/articles/*` → backend (article search)

> Unlike the old Angular proxy, the path is **not** rewritten. The backend
> routers already include the `/api` prefix, so stripping it would 404.

Point the proxy at a different backend with an env var (in `.env`):

```bash
# Local backend (default)
VITE_API_TARGET=http://localhost:8000

# Or a forwarded GitHub Codespace URL
VITE_API_TARGET=https://your-codespace-8000.app.github.dev
```

## Authentication

Uses the backend's JWT endpoints:

- `POST /api/auth/register` — create account
- `POST /api/auth/token` — login (OAuth2 password grant; `username` = email)
- `POST /api/auth/refresh` — token rotation
- `GET  /api/auth/me` — current user

The access + refresh tokens are stored in `localStorage`. The API client
(`src/api/client.ts`) attaches `Authorization: Bearer <access_token>` and
**transparently refreshes once** on a `401`, retrying the original request. If
the refresh fails, tokens are cleared and the user is sent back to `/login`.

> Self-registration must be enabled on the backend (`ALLOW_REGISTRATION`) for
> the register page to work.

## Features / use cases covered

- User registration & login
- Notebooks: list, create, view, **rename**, **update** (description/tags), delete
- Sources: import **file** (base64), **URL**, **text**; list; view; **extract content**; delete
- **Index content** (vector ingestion) + indexed-chunk count
- **Generate blog posts** from notebook sources; list & view outputs (markdown)
- **Q&A chat** grounded in the notebook, **with source citations**
- **Article search** for discovering web sources

## Production build

```bash
npm run build      # tsc -b && vite build  → outputs to dist/
npm run preview    # preview the production build locally
```

The build uses a **relative base** (`base: './'`) so the bundle can be served
from any mount point.

### Hosting on the FastAPI backend (future)

The `dist/` output is a static SPA. To serve it from FastAPI you can mount it as
static files and add a catch-all that returns `index.html` (so client-side
routes like `/notebooks/:id` resolve). Sketch:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="discoveryPortalReact/dist", html=True), name="spa")
```

When served same-origin from FastAPI, no proxy is needed — the relative
`/api` and `/articles` paths hit the same host.

## Project structure

```
src/
  api/          # fetch client, token store, typed DTOs, per-resource services
  context/      # AuthContext (token bootstrap + login/register/logout)
  hooks/        # TanStack Query hooks + query keys
  components/   # Layout, ProtectedRoute, Spinner, Markdown, ErrorMessage
  lib/          # file → base64 helper
  pages/        # route screens (notebook/ holds detail sub-panels)
  styles/       # global CSS theme
```

## Scripts

| Command            | Description                          |
| ------------------ | ------------------------------------ |
| `npm run dev`      | Start the Vite dev server (port 4200)|
| `npm run build`    | Type-check and build to `dist/`      |
| `npm run preview`  | Preview the production build         |
| `npm run typecheck`| Type-check only                      |
