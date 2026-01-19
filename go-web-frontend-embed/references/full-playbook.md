# Full Playbook: Add a Vite (React) SPA to a Go Backend

## Table of contents

1. Goals and constraints
2. Choose the contract (ports, prefixes, mount point)
3. Frontend: Vite output + dev proxy
4. Backend: serve static assets + SPA fallback
5. Build bridge: `go generate` builds and copies assets
6. Developer entry points: Makefile targets
7. CI: enforce build+embed in pipelines
8. Validation checklist (dev + prod-like)
9. Troubleshooting

## 1) Goals and constraints

You want two things at the same time:

- **Fast dev loop**: React/Vite HMR, separate processes, no CORS pain.
- **Simple production**: one Go binary serves both the API and the SPA.

The core design is a “three-phase lifecycle”:

1) **Dev-time**: Vite serves `/` and `/assets/*`; Vite proxies `/api` (and `/ws`) to Go.
2) **Build-time**: Vite builds static assets; Go copies them into a canonical directory.
3) **Run-time**: Go serves those assets (from disk in dev via `go run`, or embedded in prod via `go:embed`).

## 2) Choose the contract (ports, prefixes, mount point)

Pick defaults early (change later only with intent):

- Dev UI: `http://localhost:3000`
- Dev API: `http://localhost:3001`
- API prefix: `/api`
- WebSocket path: `/ws` (optional)
- SPA mount: `/` (recommended)

Invariants:
- Static handler must not shadow `/api` or `/ws`.
- Unknown routes should return `index.html` (SPA routing).
- Asset URLs in built `index.html` must match how Go serves them (usually `/assets/*`).

## 3) Frontend: Vite output + dev proxy

Goal: predictable build output + proxy config.

Key settings in Vite:
- `build.outDir = <ui>/dist/public`
- `server.proxy["/api"].target = http://localhost:3001`
- `server.proxy["/ws"].target = ws://localhost:3001` with `ws: true` (if needed)

Use the template:
- `assets/templates/vite.config.ts.tmpl`

Notes:
- If you serve the SPA under a subpath (e.g. `/app/`), you must coordinate Vite `base` + router basename + Go mount point. Don’t start there.

## 4) Backend: serve static assets + SPA fallback

Goal: serve “files if they exist, otherwise index.html”.

Minimal runtime logic:

- If the public FS is missing or `index.html` can’t be opened, do not register the SPA handler.
- Otherwise register a catch-all handler at `/` that:
  - rejects `/api*` and `/ws*`
  - serves real files (like `/assets/*`)
  - falls back to `index.html`

You need two build variants of the public filesystem:

- **Prod**: embed assets with `go:embed` behind build tag `embed`.
- **Dev**: in default builds, try to serve the on-disk generated directory so `go run` works after `go generate`.

Use templates:
- `assets/templates/internal-web/embed.go.tmpl`
- `assets/templates/internal-web/embed_none.go.tmpl`
- `assets/templates/internal-web/spa.go.tmpl`

## 5) Build bridge: `go generate` builds and copies assets

Goal: make the “frontend → Go tree” step explicit and reproducible.

The generator should:
- find repo root by walking upward to `go.mod`
- run the frontend build command in the frontend directory
- delete + recreate the canonical static directory under the Go tree
- copy the built artifacts into it

Use templates:
- `assets/templates/internal-web/generate.go.tmpl`
- `assets/templates/internal-web/generate_build.go.tmpl`

Important: `go generate` is not a dependency manager. CI should install node deps before running it.

## 6) Developer entry points: Makefile targets

Goal: encode the workflow as a few memorable commands.

Recommended targets:
- `dev-backend`: run Go server on `:3001`
- `dev-frontend`: run Vite on `:3000`
- `frontend-check`: run TS typecheck
- `build`: `go generate ./...` then `go build -tags embed ...`

Use:
- `assets/templates/Makefile.snippet`

## 7) CI: enforce build+embed in pipelines

Goal: CI must work on a clean machine.

Rules:
- Install Node deps first.
- Run `go generate` before build/lint steps that rely on embedded assets.
- Cache pnpm/node modules when possible.

Use:
- `assets/templates/github-actions-snippet.yml`

## 8) Validation checklist (dev + prod-like)

Dev mode:
- Run backend on `:3001` and Vite on `:3000`.
- Open `http://localhost:3000`.
- Confirm `/api/*` works from the browser (proxy).
- Confirm `/ws` connects if used.

Prod-like mode:
- Run `go generate ./internal/web` (or your package path).
- Build with `go build -tags embed ...`.
- Run the server and open the Go port directly.
- Confirm:
  - `/` returns HTML
  - `/assets/*` returns JS/CSS
  - unknown SPA routes return `index.html`
  - `/api/*` still works

## 9) Troubleshooting

- **`GET /` is 404 in prod-like mode**
  - `index.html` missing in the FS → run `go generate` and confirm copy destination matches the embed directory.
  - static handler not mounted → ensure it’s registered and not returning early.
- **Assets 404 but index loads**
  - built `index.html` references `/assets/...` but Go isn’t serving `/assets/*` from the same FS.
  - check mount point (`/`) and whether file-exists branch is correct.
- **Dev API calls fail**
  - proxy target/port mismatch; ensure Vite proxies to the backend port.
- **WebSocket fails in dev**
  - ensure proxy uses `ws: true` and `ws://` target.
