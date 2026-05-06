# Mento Dagger Pipeline Pattern

Summary of the Mento Dagger pipeline documentation and its key patterns.

## Source

`/home/manuel/code/mento/go-go-mento/docs/infra/dagger-build-pipeline.md`

## Architecture Overview

The Mento pipeline is the most sophisticated of the three implementations, with:

1. **PNPM Builder Base (PBB)**: Pre-activated pnpm on `node:22`, published by digest
2. **Dagger Builder Image (DBI)**: Contains precompiled `build-web` generator
3. **Composite Actions**: `prepare-dagger-builder` and `run-web-with-dagger`
4. **Digest-first pattern**: Immutable references for reproducibility
5. **Host-mounted pnpm store**: Cache persists across runs

## Key Patterns

### Digest-First References

```yaml
# prepare-dagger-builder outputs immutable digests:
pnpm_ref: "ghcr.io/<org>/pnpm-builder@sha256:..."
dagger_ref: "ghcr.io/<org>/dagger-builder@sha256:..."
```

Benefits:
- No tag races
- Guaranteed reproducibility
- Cache invalidation is explicit

### Two-Stage Builder

```
Stage 1: prepare-dagger-builder
├── Builds pnpm-builder base image
├── Builds DBI with precompiled generator
└── Outputs digest references

Stage 2: run-web-with-dagger
├── Resolves digest references
├── Runs DBI with mounts
└── Exports dist/ to repo
```

### Host-Mounted pnpm Store

```yaml
# run-web-with-dagger
- name: Run web build with Dagger
  uses: ./.github/actions/run-web-with-dagger
  with:
    pnpm_ref: ${{ steps.prepare.outputs.pnpm_ref }}
    dagger_ref: ${{ steps.prepare.outputs.dagger_ref }}
  environment:
    PNPM_CACHE_DIR: .cache/pnpm-store
```

In the DBI entrypoint:
```bash
-v "$(pwd)/.cache/pnpm-store:/pnpm-cache"
```

Inside the container, the cache is mounted at `/pnpm/store`.

### Composite Actions Pattern

**prepare-dagger-builder/action.yml:**
```yaml
outputs:
  pnpm_ref:
    description: "Digest reference for pnpm builder"
    value: ${{ steps.push-pbb.outputs.ref }}
  dagger_ref:
    description: "Digest reference for DBI"
    value: ${{ steps.push-dbi.outputs.ref }}
```

**run-web-with-dagger/action.yml:**
```yaml
inputs:
  pnpm_ref:
    description: "Digest reference for pnpm builder"
    required: true
  dagger_ref:
    description: "Digest reference for DBI"
    required: true
```

## Applicability to Simpler Projects

The Mento pattern is comprehensive but may be overkill for single-repo projects. Consider:

| Project Type | Recommended Pattern |
|--------------|---------------------|
| Single repo, occasional builds | Glazed (direct Dagger, no composite actions) |
| Single repo, frequent builds | Smailnail (CacheVolume, no composite actions) |
| Multi-repo, needs reproducibility | Mento (digest-first, composite actions) |

## Key Takeaways for Skill Users

1. **Always use CacheVolume** for pnpm store (speeds up repeated builds)
2. **Use digest references** when publishing builder images
3. **Use composite actions** for reusable CI workflows
4. **Mount host cache** for CI to share cache across runs
5. **Exclude unnecessary files** from mounted directories

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `WEB_BUILDER_IMAGE` | Base image for Node/pnpm | `node:22` |
| `WEB_PNPM_VERSION` | pnpm version | From `package.json` |
| `PNPM_CACHE_DIR` | Host path for pnpm store cache | None |
| `WORK_DIR` | DBI workspace mount | `/work` |
| `OUT_DIR` | DBI output directory | `<repo>/go/cmd/frontend/dist` |
| `GHCR_USERNAME` | Registry auth (GHCR) | None |
| `GHCR_TOKEN` | Registry auth token | None |
