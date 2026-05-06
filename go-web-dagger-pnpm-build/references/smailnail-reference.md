# Smailnail Reference Implementation

Annotated walkthrough of the Smailnail Dagger pnpm build implementation.

## Source Location

`/home/manuel/code/wesen/corporate-headquarters/smailnail/`

## Key Files

### cmd/build-web/main.go

```go
const defaultPNPMVersion = "10.15.0"

func main() {
    ctx := context.Background()
    if err := buildAndExportFrontend(ctx); err != nil {
        // ...
    }
}
```

**Key features:**
1. Uses `dagger.WithLogOutput(os.Stdout)` for visibility
2. Creates `CacheVolume("smailnail-ui-pnpm-store")` for pnpm store
3. Uses `node:22-bookworm` as base image
4. Exports to `pkg/smailnaild/web/embed/public`

### The buildAndExportFrontend Function

```go
func buildAndExportFrontend(ctx context.Context) error {
    repoRoot, err := findRepoRoot()
    // ...
    
    uiDir := filepath.Join(repoRoot, "ui")
    embedDir := filepath.Join(repoRoot, "pkg", "smailnaild", "web", "embed", "public")
    
    // Clean output
    if err := os.RemoveAll(embedDir); err != nil && !os.IsNotExist(err) {
        return errors.Wrap(err, "remove old embed assets")
    }
    
    client, err := dagger.Connect(ctx, dagger.WithLogOutput(os.Stdout))
    // ...
    
    pnpmVersion := strings.TrimSpace(os.Getenv("WEB_PNPM_VERSION"))
    if pnpmVersion == "" {
        pnpmVersion = defaultPNPMVersion
    }
    
    // Source directory with exclusions
    source := client.Host().Directory(uiDir, dagger.HostDirectoryOpts{
        Exclude: []string{"dist", "node_modules", "storybook-static", "tsconfig.tsbuildinfo"},
    })
    
    // CacheVolume for pnpm store
    pnpmStore := client.CacheVolume("smailnail-ui-pnpm-store")
    
    ctr := client.Container().
        From("node:22-bookworm").
        WithEnvVariable("PNPM_HOME", "/pnpm").
        WithEnvVariable("PATH", pathValue).
        WithMountedCache("/pnpm/store", pnpmStore).
        WithDirectory("/src/ui", source).
        WithWorkdir("/src/ui").
        WithExec([]string{"sh", "-lc", "corepack enable && corepack prepare pnpm@" + pnpmVersion + " --activate"}).
        WithExec([]string{"pnpm", "install", "--frozen-lockfile"}).
        WithExec([]string{"pnpm", "run", "build"})
    
    // Export to embed directory
    if _, err := container.Directory("/src/ui/dist/public").Export(ctx, embedDir); err != nil {
        return errors.Wrap(err, "export built frontend into embed/public")
    }
    
    return nil
}
```

## pkg/smailnaild/web/ Embedding

### embed.go (build tag)

```go
//go:build embed

package web

import (
    "embed"
    "io.fs"
)

//go:embed embed/public
var embeddedFS embed.FS

var PublicFS, _ = fs.Sub(embeddedFS, "embed/public")
```

### spa.go (SPA handler)

```go
func RegisterSPA(mux *http.ServeMux, publicFS fs.FS, opts SPAOptions) {
    if publicFS == nil {
        return
    }
    if _, err := publicFS.Open("index.html"); err != nil {
        return
    }
    
    apiPrefix := opts.APIPrefix
    if apiPrefix == "" {
        apiPrefix = "/api"
    }
    
    fileServer := http.FileServer(http.FS(publicFS))
    mux.Handle("/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Never serve API routes from the SPA handler
        if strings.HasPrefix(r.URL.Path, apiPrefix) {
            http.NotFound(w, r)
            return
        }
        
        // Try to serve file, fallback to index.html
        // ...
    }))
}
```

## Package Structure

```
pkg/smailnaild/web/
├── embed.go          # //go:build embed
├── embed_none.go     # //go:build !embed
├── spa.go            # RegisterSPA function
├── generate.go       # //go:generate go run ../../../cmd/build-web
└── embed/
    └── public/       # Built assets (gitignored)
        ├── index.html
        └── assets/
```

## Design Decisions

1. **Separate embed/public directory**: Allows gitignoring the entire `embed/` directory while keeping the structure clear.

2. **RegisterSPA on mux**: Instead of returning a handler, registers directly on an `http.ServeMux`. This is useful when Smailnail has an existing mux with other routes.

3. **Explicit exclusions**: The Dagger program excludes `dist`, `node_modules`, `storybook-static`, and `tsconfig.tsbuildinfo` from the mounted directory.

4. **frozen-lockfile**: Uses `--frozen-lockfile` for CI reliability; local development may use `--prefer-offline` to leverage CacheVolume.

5. **node:22-bookworm**: Uses a specific OS version instead of generic `node:22` for reproducibility.
