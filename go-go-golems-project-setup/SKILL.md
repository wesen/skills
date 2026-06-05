---
name: go-go-golems-project-setup
description: >-
  Scaffold or retrofit a go-go-golems Go repository with standard project plumbing:
  Makefile targets, pinned golangci-lint, glazed-lint, logcopter generation/checks,
  lefthook hooks, GitHub Actions (unit/smoke/lint/security), and GoReleaser release setup
  (GitHub releases + Homebrew tap).
  Use when creating a new go-go-golems Go CLI/library repo, renaming an existing module/binary
  to go-go-golems conventions, or making a repo “release-ready” with CI and GoReleaser.
---

# Go Go Golems Project Setup

## Workflow

Set up a Go project to match the common go-go-golems shape and release pipeline (CI + lint + logcopter + GoReleaser + Homebrew tap). Prefer using the included scaffold script and templates so projects are consistent.

### Inputs to decide up front

- `module`: `github.com/go-go-golems/<repo>`
- `binary`: CLI name (usually same as repo)
- `project_name`: GoReleaser `project_name` (usually same as repo)
- `description`: 1-line summary for README/GoReleaser
- release targets: `linux` + `darwin` (default), `CGO_ENABLED=0` if possible
- brew tap repo: `go-go-golems/homebrew-go-go-go` (default in templates)

### Step 1 — Scaffold the plumbing

Use the scaffold script to copy standard files into the current repo and apply placeholder replacements.

1) Run:

```bash
python3 /home/manuel/.pi/agent/skills/go-go-golems-project-setup/scripts/scaffold.py \
  --module github.com/go-go-golems/<repo> \
  --binary <binary> \
  --project-name <project_name> \
  --description "<one line description>" \
  --force
```

2) Then run:

```bash
go get -tool github.com/go-go-golems/logcopter/cmd/logcopter-gen@latest
go mod tidy
make logcopter-generate
make logcopter-check
make lint
make test
```

Notes:

- The scaffold copies `.github/workflows/*` when present, `.goreleaser.yaml`, `.golangci.yml`, `.golangci-lint-version`, `lefthook.yml`, `Makefile`, `logcopter_generate.go`, and a README template.
- The Makefile defaults to pinned `golangci-lint` from `.golangci-lint-version`, builds `glazed-lint` from `github.com/go-go-golems/glazed/cmd/tools/glazed-lint`, and adds `logcopter-generate` / `logcopter-check` targets.
- If the repo cannot load `./...` with `GOWORK=off`, narrow `GO_PACKAGES` temporarily and document the blocker in the Makefile until dependencies are fixed.
- Adjust smoke tests in `.github/workflows/push.yml` to exercise real subcommands / a tiny e2e fixture for your project.

### Step 2 — Wire the actual CLI/library

- CLI: create `cmd/<binary>/main.go` (Cobra) and add minimal subcommands so smoke tests are meaningful.
- Library-only repo: remove CLI-specific smoke steps and adjust `builds[].main`/`binary` in GoReleaser (or drop builds).

### Step 3 — Verify CI and releases

Use `gh` to confirm the workflows exist and are green after pushing:

```bash
gh workflow list
gh run list --limit 20
```

To cut a release, push a tag and then watch `release.yaml`:

```bash
git tag v0.1.0
git push origin v0.1.0
gh run list --workflow release.yaml --limit 5
```

### Step 4 — Configure secrets (if using GoReleaser workflow)

This scaffold expects secrets similar to other go-go-golems repos. Adjust to your org’s reality.

See `references/playbook.md` for a fuller checklist and explanations.

## Bundled resources

- `scripts/scaffold.py`: copy templates into the current repo and replace placeholders.
- `references/playbook.md`: checklist + commands to validate CI/release.
- `assets/scaffold/`: template files to copy into new repos.
