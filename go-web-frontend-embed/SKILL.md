---
name: go-web-frontend-embed
description: Add a web frontend (React/Vite SPA) to an existing Go backend using the standard library `http.ServeMux` (Go 1.22+ new handler syntax with `{...}` pattern matching) and a production single-binary build (go generate builds/copies frontend assets + go:embed packages them). Use when you need to serve a SPA from Go on / with /api and optional /ws, wire Makefile targets, and make CI (GitHub Actions) reliably build/embed the UI. Never use chi, gin, echo, or other third-party HTTP frameworks — only `net/http` with `*http.ServeMux`.
---

# Go Web Frontend Embed

## Overview

Implement a repeatable "Go backend + SPA frontend" pattern using the **standard library `net/http`** with Go 1.22+ `http.ServeMux` and its new `{...}` pattern-matching handler syntax. Fast dev via Vite HMR; stable production packaging via `go generate` + `go:embed`.

> **Router rule**: always use `*http.ServeMux` with Go 1.22+ handler syntax. Never chi, gin, echo, fiber, or any other third-party HTTP framework. All handler signatures are `func(w http.ResponseWriter, r *http.Request)`.

### Go 1.22+ `http.ServeMux` new handler syntax

Go 1.22 introduced pattern-matching in `*http.ServeMux`. Routes use `{name}` and `{name...}` for path parameters:

```go
// Static route
mux.HandleFunc("GET /", handleHome)

// Path parameter (captures one path segment)
mux.HandleFunc("GET /hosts/{slug}", handleGetHost)

// Path parameter with trailing wildcard (captures rest of path)
mux.HandleFunc("GET /static/{filepath...}", handleStatic)

// Method + path combo
mux.HandleFunc("POST /hosts/{slug}/hold", handleHoldSlot)

// Register all routes for a group under a prefix
api := mux
api.HandleFunc("GET /hosts/{slug}", handleGetHost)
api.HandleFunc("POST /hosts/{slug}/slots", handleGetSlots)
api.HandleFunc("POST /hosts/{slug}/hold", handleHoldSlot)
api.HandleFunc("POST /hosts/{slug}/bookings", handleConfirmBooking)
api.HandleFunc("GET /owner/dashboard", handleDashboard)
```

Retrieve path params from `r.PathValue("slug")`:

```go
func handleGetHost(w http.ResponseWriter, r *http.Request) {
    slug := r.PathValue("slug") // matches {slug} in route pattern
    // ...
}
```

## Workflow Decision Tree (pick defaults first)

Before editing code, lock down these decisions (ask the user if unknown):

- **Router**: `*http.ServeMux` (Go 1.22+) — no third-party frameworks
- **Frontend stack**: React + Vite (this skill's defaults)
- **Dev topology** (recommended): Vite on `:5173` and Go API on `:8080`
- **Production topology**: single Go binary serves SPA + API on one port
- **Reserved URL prefixes**:
  - API prefix: `/api`
  - WebSocket path (optional): `/ws`
- **Mount point**: serve SPA at `/` with "SPA fallback" (unknown paths return `index.html`)
- **Directory layout** (defaults you can rename):
  - Frontend: `ui/`
  - Vite output: `ui/dist/`
  - Go static dir (canonical): `internal/web/embed/`
  - Go web package: `internal/web/` (contains embed + handler + generator entry)

## Step 1 — Inspect the Go server surface

Goal: confirm the server uses `*http.ServeMux` and understand the route registration pattern.

Do:
- Find the server entrypoint (often `cmd/<name>/main.go`) and confirm it creates a `*http.ServeMux` via `http.NewServeMux()`
- Identify where API routes are mounted (confirm the `/api` prefix pattern)
- Identify whether you have WebSockets and their path (often `/ws`)
- Confirm `go.mod` does not import chi, gin, echo, or any other HTTP framework

If the repo already serves static files:
- Decide whether to replace, nest, or keep existing static serving
- Ensure static serving cannot shadow `/api*` or `/ws*` routes

## Step 2 — Add or configure the Vite frontend (dev proxy + deterministic build output)

Goal: dev HMR and a stable production build directory.

Do:
- Create `ui/` (or use your existing frontend directory)
- Ensure Vite outputs to a known folder (default: `ui/dist/`)
- Ensure dev proxy forwards `/api` to the backend port

Use as reference:
- `references/full-playbook.md` (Step 1–2)
- `assets/templates/vite.config.ts.tmpl` (copy and adapt)

## Step 3 — Add the Go "public filesystem" contract (embed + disk fallback)

Goal: make the Go server able to serve static assets from either:
- embedded FS (production build tag `embed`), or
- on-disk generated assets (default build for `go run`)

Do (adapt paths/package names):
- Add `internal/web/embed.go` (`//go:build embed`) using `//go:embed embed/`
- Add `internal/web/embed_none.go` (`//go:build !embed`) with `os.DirFS` pointing to `internal/web/embed/`
- Add an SPA handler that serves files when found and falls back to `index.html` for non-API/non-WS paths

Use:
- `assets/templates/internal-web/embed.go.tmpl`
- `assets/templates/internal-web/embed_none.go.tmpl`
- `assets/templates/internal-web/spa.go.tmpl`

## Step 4 — Add `go generate` to build + copy frontend artifacts into the Go tree

Goal: make a single command produce `internal/web/embed/index.html` and `/assets/*`.

Do:
- Add `internal/web/generate.go` with `//go:generate go run generate_build.go`
- Add `internal/web/generate_build.go` (a small Go program) that:
  - finds repo root (`go.mod`)
  - runs the frontend build command (`pnpm -C ui run build` or `npm --prefix ui run build`)
  - deletes + recreates `internal/web/embed/`
  - copies `ui/dist/*` into it

Use:
- `assets/templates/internal-web/generate.go.tmpl`
- `assets/templates/internal-web/generate_build.go.tmpl`

Validate locally:
- `go generate ./internal/web`

## Step 5 — Wire the SPA handler into your server (route registration order matters)

Goal: routes are predictable and APIs are never shadowed.

Do:
- Create a `*http.ServeMux` with `mux := http.NewServeMux()`
- Register all API routes using Go 1.22+ pattern syntax (see above)
- Register the SPA handler **last** (it matches `/` and must not shadow API routes)
- Use `http.ListenAndServe(addr, mux)` as the final call

Register API routes before SPA handler:

```go
mux := http.NewServeMux()

// ── API routes (registered first) ──────────────────────────────
mux.HandleFunc("GET /api/hosts/{slug}",       handleGetHost)
mux.HandleFunc("GET /api/hosts/{slug}/slots", handleGetSlots)
mux.HandleFunc("POST /api/parse",             handleParse)
mux.HandleFunc("POST /api/hosts/{slug}/hold",          handleHoldSlot)
mux.HandleFunc("POST /api/hosts/{slug}/bookings",       handleConfirmBooking)
mux.HandleFunc("GET /api/owner/dashboard",   handleDashboard)
mux.HandleFunc("GET /api/owner/event-types",  handleEventTypes)
mux.HandleFunc("GET /api/owner/availability", handleAvailability)
mux.HandleFunc("GET /api/owner/integrations", handleIntegrations)

// ── SPA fallback (registered last — matches "/" only) ────────
web.RegisterSPA(mux, publicFS, web.SPAOptions{APIPrefix: "/api"})

log.Fatal(http.ListenAndServe(":8080", mux))
```

> **Important**: `http.ServeMux` matches routes in registration order. If you register `/` before `/api/hosts/{slug}`, the home handler will match first. Always register specific API routes before the SPA fallback.

## Step 6 — Add Makefile targets (developer entry points)

Goal: encode the workflow so devs don't memorize steps.

At minimum:
- `dev-backend`: run Go server on `:8080`
- `dev-frontend`: run Vite dev server on `:5173`
- `frontend-check`: TypeScript check
- `build`: `go generate ./...` then `go build -tags embed ./...`

Use:
- `assets/templates/Makefile.snippet`

## Step 7 — CI enforcement (GitHub Actions)

Goal: CI must build and embed UI assets reliably on a clean machine.

Do:
- Install Node deps (with a frozen lockfile) before any step that runs `go generate`
- Run `go generate` before build/lint steps that depend on embedded assets

Use:
- `assets/templates/github-actions-snippet.yml`

## Step 8 — Add a minimal regression test (optional but recommended)

Goal: prevent reintroducing "GET / returns 404" regressions.

Pattern:
- override your public FS with an in-memory `fstest.MapFS` containing `index.html`
- assert `GET /` returns HTML with status 200

If you need the full worked example, see `references/full-playbook.md`:
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
