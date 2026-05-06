---
name: go-web-dagger-pnpm-build
description: Scaffold or align a Dagger-based pnpm web build pipeline for Go repos with embedded SPAs. Use when setting up a new go+web project, adding a build-web command, or aligning existing build infrastructure with the CacheVolume + pnpm store pattern.
---

# Go Web Dagger pnpm Build

Scaffold a reproducible Dagger-based web build pipeline for Go projects that embed SPAs. Follows the CacheVolume + pnpm store + go:embed pattern.

## Architecture

```
web/ (Vite + React/TypeScript, built to web/dist/)
  -> cmd/build-web (Dagger or local pnpm)
  -> internal/web/embed/public/  (//go:embed source)
  -> internal/web/embed.go (//go:build embed)
  -> Go binary serves SPA + API
```

**Key path invariant**: Vite outputs to `web/dist/`. `cmd/build-web` copies that to `internal/web/embed/public/`. The Go `//go:embed` directive embeds `internal/web/embed/` and `PublicFS` is the `embed/public/` subdirectory.

## When to Use

- Setting up a new Go + web project with embedded SPA
- Adding a `cmd/build-web` command to an existing repo
- Aligning an existing build-web implementation with the pattern
- Adding `go:generate` for frontend builds

## Quick Setup

### Step 1: `packageManager` in `web/package.json`

Add this to the top-level JSON object:
```json
"packageManager": "pnpm@10.15.0"
```

### Step 1b: Move `test` config out of `vite.config.ts`

Vite's `defineConfig` rejects the `test` field (it belongs to Vitest). Move it to `vitest.config.ts`:

```typescript
// vite.config.ts — production config only (NO test block here)
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8080" },
  },
});
```

```typescript
// vitest.config.ts — test config (separate from vite.config.ts)
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
```

`pnpm run build` runs `tsc -b && vite build`. If `test` is in `vite.config.ts`, `tsc -b` will fail with resolution errors because `vite` module doesn't have `defineConfig` (only `vitest/config` does).

### Step 2: Copy `cmd/build-web/main.go`

Copy from `assets/templates/cmd-build-web-main.go.tmpl` and adapt:
- `defaultBuilderImage` — `node:22` or a specific image tag
- `defaultPNPMVersion` — must match `packageManager` field in `web/package.json`
- CacheVolume name is `simplecal-ui-pnpm-store` (replace with your repo name)

**Usage**:
```bash
go run ./cmd/build-web           # Dagger (requires Docker/Dagger engine)
BUILD_WEB_LOCAL=1 go run ./cmd/build-web  # Local pnpm (requires node + pnpm)
```

### Step 3: Copy `internal/web/` package

Copy all four files from `assets/templates/internal-web/`:
- `embed.go` — `//go:build embed` + `//go:embed embed/public`
- `embed_none.go` — `//go:build !embed` + `findRoot()` disk fallback
- `static.go` — `NewSPAHandler()` SPA handler
- `generate.go` — `//go:generate go run ../../../cmd/build-web`

### Step 4: Wire into `cmd/<binary>/main.go`

```go
import "simplecal/internal/web"

spaHandler, err := web.NewSPAHandler(&web.SPAOptions{APIPrefix: "/api"})
if err != nil {
    log.Fatal(err)
}
mux.Handle("GET /", spaHandler)
mux.Handle("GET /{filepath...}", spaHandler)
```

### Step 5: Validate

```bash
go generate ./internal/web           # builds UI → internal/web/embed/public/
go build -tags embed ./cmd/simplecal
./simplecal serve --addr :8080
# open http://localhost:8080 → should serve React SPA
# open http://localhost:8080/api/hosts/shawn → should serve JSON
```

## `cmd/build-web` Design Decisions

**Dagger-first with local fallback**: Tries Docker/Dagger first; if Docker is unavailable (or `BUILD_WEB_LOCAL=1` is set), falls back to `pnpm run build` on the local machine. This means it works on developer machines without Docker.

**CacheVolume persists across builds**: The `pnpm` package store is mounted as a Dagger `CacheVolume`. After the first run, subsequent builds are fast because packages are reused.

**`packageManager` from `web/package.json`**: The Dagger container uses the exact pnpm version pinned in `packageManager` via corepack, so `pnpm install` is reproducible across machines.

## `internal/web/` Package Design

**Embed structure**: `//go:embed embed/public` embeds the `internal/web/embed/public/` directory. Inside that dir, Vite's build output is stored directly — `index.html` and `assets/` at the root.

**PublicFS**: Both `embed.go` and `embed_none.go` expose `PublicFS fs.FS`. `embed.go` uses `fs.Sub(embeddedFS, "embed/public")` to strip the `embed/public/` prefix. `embed_none.go` walks up to find `go.mod` (repo root) and uses `os.DirFS("internal/web/embed/public")`.

**`embed/public/` (not `embed/dist/`)**: Using a dedicated `public/` subdirectory means the Go embed path is stable and doesn't depend on Vite's output directory name. If Vite later changes its output layout, only `cmd/build-web`'s copy step needs updating.

## Reference Implementation

- **codebase-browser**: `/home/manuel/code/wesen/2026-04-19--go-codebase-browser/internal/web/` — the canonical working example
- **simplecal**: `/home/manuel/code/wesen/2026-04-21--cal-doodle-minimax/simplecal/` — this project
