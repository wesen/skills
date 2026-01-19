---
name: go-web-frontend-embed
description: Add a web frontend (React/Vite SPA) to an existing Go backend with a two-process dev loop (Vite dev server + proxy to Go) and a production single-binary build (go generate builds/copies frontend assets + go:embed packages them). Use when you need to serve a SPA from Go on / with /api and optional /ws, wire Makefile targets, and make CI (GitHub Actions) reliably build/embed the UI.
---

# Go Web Frontend Embed

## Overview

Implement a repeatable “Go backend + SPA frontend” pattern: fast dev via Vite HMR and stable production packaging via `go generate` + `go:embed`.

This skill is procedural: follow the workflow and adapt the templates to the target repo’s router and directory layout.

## Workflow Decision Tree (pick defaults first)

Before editing code, lock down these decisions (ask the user if unknown):

- **Frontend stack**: React + Vite (this skill’s defaults). If you’re not using Vite, stop and adapt.
- **Dev topology** (recommended): Vite on `:3000` and Go API on `:3001`.
- **Production topology**: single Go binary serves SPA + API on one port.
- **Reserved URL prefixes**:
  - API prefix: `/api`
  - WebSocket path (optional): `/ws`
- **Mount point**: serve SPA at `/` with “SPA fallback” (unknown paths return `index.html`).
- **Directory layout** (defaults you can rename):
  - Frontend: `ui/`
  - Vite output: `ui/dist/public/`
  - Go static dir (canonical): `internal/web/embed/public/`
  - Go web package: `internal/web/` (contains embed + handler + generator entry)

If the target repo already has a frontend, keep its tooling; only apply the Go-side “embed + serve” contract.

## Step 1 — Inspect the Go server surface

Goal: figure out how to register routes and where the server binary entrypoint lives.

Do:
- Find the server entrypoint (often `cmd/<name>/main.go`) and the router setup.
- Identify where API routes are mounted (confirm the `/api` prefix).
- Identify whether you have WebSockets and their path (often `/ws`).
- Confirm whether the server uses `http.ServeMux`, chi, gin, echo, etc.

If the repo already serves static files:
- Decide whether to replace, nest, or keep existing static serving.
- Ensure static serving cannot shadow `/api` (and `/ws`) routes.

## Step 2 — Add or configure the Vite frontend (dev proxy + deterministic build output)

Goal: dev HMR and a stable production build directory.

Do:
- Create `ui/` (or use your existing frontend directory).
- Ensure Vite outputs to a known folder (default: `ui/dist/public/`).
- Ensure dev proxy forwards `/api` (and `/ws`) to the backend port.

Use as reference:
- `references/full-playbook.md` (Step 1–2)
- `assets/templates/vite.config.ts.tmpl` (copy and adapt)

## Step 3 — Add the Go “public filesystem” contract (embed + disk fallback)

Goal: make the Go server able to serve static assets from either:
- embedded FS (production build tag `embed`), or
- on-disk generated assets (default build for `go run`).

Do (adapt paths/package names):
- Add `internal/web/embed.go` (`//go:build embed`) using `//go:embed embed/public`.
- Add `internal/web/embed_none.go` (`//go:build !embed`) with best-effort `os.DirFS` pointing to `internal/web/embed/public`.
- Add an SPA handler with:
  - “serve file if exists”
  - otherwise serve `index.html` fallback
  - never serve on `/api*` or `/ws*`

Use:
- `assets/templates/internal-web/embed.go.tmpl`
- `assets/templates/internal-web/embed_none.go.tmpl`
- `assets/templates/internal-web/spa.go.tmpl`

## Step 4 — Add `go generate` to build + copy frontend artifacts into the Go tree

Goal: make a single command produce `internal/web/embed/public/index.html` and `/assets/*`.

Do:
- Add `internal/web/generate.go` with `//go:generate go run generate_build.go`.
- Add `internal/web/generate_build.go` (a small Go program) that:
  - finds repo root (`go.mod`)
  - runs the frontend build command (`pnpm -C ui run build`)
  - deletes + recreates `internal/web/embed/public`
  - copies `ui/dist/public/*` into it

Use:
- `assets/templates/internal-web/generate.go.tmpl`
- `assets/templates/internal-web/generate_build.go.tmpl`

Validate locally:
- `go generate ./internal/web`

## Step 5 — Wire the SPA handler into your server (order matters)

Goal: routes are predictable and APIs are never shadowed.

Do:
- Register API and WS handlers first.
- Register SPA/static handler last.

If using `http.ServeMux`, the template handler can attach at `/`.
If using another router, adapt the same logic (path guards + fallback) to that router’s middleware/handlers.

## Step 6 — Add Makefile targets (developer entry points)

Goal: encode the workflow so devs don’t memorize steps.

At minimum:
- `dev-backend`: run Go server on `:3001`
- `dev-frontend`: run Vite on `:3000`
- `frontend-check`: TypeScript check
- `build`: `go generate ./...` then `go build -tags embed ...`

Use:
- `assets/templates/Makefile.snippet`

## Step 7 — CI enforcement (GitHub Actions)

Goal: CI must build and embed UI assets reliably on a clean machine.

Do:
- Install Node deps (with a frozen lockfile) before any step that runs `go generate`.
- Run `go generate` before build/lint steps that depend on embedded assets.

Use:
- `assets/templates/github-actions-snippet.yml`

## Step 8 — Add a minimal regression test (optional but recommended)

Goal: prevent reintroducing “GET / returns 404” regressions.

Pattern:
- override your public FS with an in-memory `fstest.MapFS` containing `index.html`
- assert `GET /` returns HTML with status 200

If you need the full worked example, see `references/full-playbook.md` and the `plz-confirm` reference implementation:
- `internal/server/server_static_test.go`

## Resources (optional)

### scripts/
N/A for this skill (templates + references are sufficient). If you add a scaffolder script later, put it here.

### references/
Read these when you need deeper detail or exact wording:
- `references/full-playbook.md`: full, step-by-step explanation and validation checklist.

### assets/
Copy-and-adapt templates (do not load unless patching):
- `assets/templates/vite.config.ts.tmpl`
- `assets/templates/internal-web/*.tmpl`
- `assets/templates/Makefile.snippet`
- `assets/templates/github-actions-snippet.yml`

---

Keep this skill lean: prefer templates and a single reference file rather than duplicating long prose in SKILL.md.
