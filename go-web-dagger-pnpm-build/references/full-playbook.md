# Full Playbook: Go Web Dagger pnpm Build

Detailed step-by-step guide for setting up a Dagger-based pnpm web build pipeline.

## Prerequisites

- Go 1.21+
- Dagger installed: `go install dagger.io/dagger/cmd/dagger@latest`
- pnpm installed (for local fallback): `npm install -g pnpm`
- Git

## Directory Structure Target

```
<repo>/
├── cmd/
│   └── build-web/
│       └── main.go           # Dagger build program
├── pkg/
│   └── <module>/
│       └── web/
│           ├── generate.go   # //go:generate entry point
│           ├── embed.go      # //go:build embed
│           ├── embed_none.go # //go:build !embed
│           ├── static.go     # SPA handler
│           └── dist/         # Built assets (gitignored)
└── web/                     # Frontend source
    ├── src/
    ├── dist/                 # Vite build output
    └── package.json
```

## Step 1: Prepare the Frontend

### 1.1 Create `web/package.json`

```json
{
  "name": "<project>-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "packageManager": "pnpm@10.15.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### 1.2 Configure Vite

Create `web/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    // Ensure assets are prefixed correctly for embedding
    assetsDir: 'assets',
  },
})
```

## Step 2: Create the Dagger Build Program

### 2.1 Create `cmd/build-web/main.go`

Copy from `assets/templates/cmd-build-web-main.go.tmpl` and replace:
- `{{.Module}}` → your module name (e.g., `smailnaild`)
- `{{.CacheName}}` → unique cache name (e.g., `smailnail`)

### 2.2 Initialize the Go module (if new)

```bash
cd cmd/build-web
go mod init github.com/<org>/<repo>/cmd/build-web
go mod tidy
```

## Step 3: Create the Go Embed Package

### 3.1 Create Directory

```bash
mkdir -p pkg/<module>/web
```

### 3.2 Copy Templates

Copy from `assets/templates/internal-web/`:
- `embed.go.tmpl` → `embed.go` (replace `{{.Module}}`)
- `embed_none.go.tmpl` → `embed_none.go` (replace `{{.Module}}`)
- `static.go.tmpl` → `static.go`
- `generate.go.tmpl` → `generate.go`

### 3.3 Update Paths

In `embed.go` and `embed_none.go`, ensure the path matches your output:
- If using `pkg/<module>/web/dist`: use `fs.Sub(embeddedFS, "dist")`
- If using `pkg/<module>/web/embed/public`: use `fs.Sub(embeddedFS, "embed/public")`

## Step 4: Wire into Your Server

### 4.1 In Your HTTP Server

```go
import "github.com/<org>/<repo>/pkg/<module>/web"

func main() {
    mux := http.NewServeMux()
    
    // Register API handlers FIRST
    mux.HandleFunc("/api/", apiHandler)
    
    // Register SPA handler LAST
    spaHandler, err := web.NewSPAHandler(&web.SPAOptions{
        APIPrefix: "/api",
    })
    if err != nil {
        log.Fatal(err)
    }
    mux.Handle("/", spaHandler)
    
    http.ListenAndServe(":8080", mux)
}
```

## Step 5: Update .gitignore

Add to `.gitignore`:
```
# Built web assets
pkg/<module>/web/dist/
pkg/<module>/web/embed/public/
```

## Step 6: Test the Build

### 6.1 Generate Frontend Assets

```bash
cd <repo>
go generate ./pkg/<module>/web
```

### 6.2 Build the Binary

```bash
# Without embed (uses disk fallback)
go build -o <binary> ./cmd/<binary>

# With embed (assets baked in)
go build -tags embed -o <binary> ./cmd/<binary>
```

### 6.3 Test the Server

```bash
./<binary>
curl http://localhost:8080/  # Should return HTML
curl http://localhost:8080/api/health  # Should return API response
```

## Validation Checklist

- [ ] `go generate ./pkg/<module>/web` succeeds
- [ ] `pkg/<module>/web/dist/` contains built assets
- [ ] `go build` (no tags) works with disk fallback
- [ ] `go build -tags embed` embeds assets into binary
- [ ] Server serves SPA at `/`
- [ ] Server returns 404 for unknown paths (falls back to index.html)
- [ ] Server does not serve `/api/*` from SPA
- [ ] `WEB_BUILDER_IMAGE` env var changes base image
- [ ] Repeated builds are faster (CacheVolume hits)

## Troubleshooting

### "packageManager field not found"

Add to `web/package.json`:
```json
"packageManager": "pnpm@10.15.0"
```

### Dagger connection fails

The program should fall back to local pnpm. Ensure pnpm is installed:
```bash
which pnpm || npm install -g pnpm
```

### Assets not found

1. Check that `go generate` ran successfully
2. Verify the output path matches the embed directive
3. For `go run`, ensure `dist/` exists on disk

### Cache misses

CacheVolume names must be unique per-project. If reusing a name from another project, the cache may have stale data. Use project-specific names like `<project>-ui-pnpm-store`.
