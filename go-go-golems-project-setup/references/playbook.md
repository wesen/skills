# go-go-golems project setup (reference)

Use this as a checklist when creating a new go-go-golems Go CLI/library repo or retrofitting an existing repo.

## Standard repo shape

- `cmd/<binary>/` for CLIs (Cobra + Glazed common)
- `internal/` for non-exported packages
- `docs/` for developer docs (optional)
- `examples/` for examples (optional)

## Standard plumbing files

- `Makefile` with common targets: `lint`, `test`, `build`, `install`, `goreleaser`
- `.golangci.yml` (baseline lint config)
- `lefthook.yml` for pre-commit hooks
- `.github/workflows/` for unit/smoke/lint/security/release
- `.goreleaser.yaml` for release artifacts + Homebrew tap
- `README.md` with install + quick start

## Fast path (recommended): use the scaffold

The `go-go-golems-project-setup` skill bundles templates and a scaffold script.

From the repo root:

```bash
python3 /home/manuel/.codex/skills/go-go-golems-project-setup/scripts/scaffold.py \
  --module github.com/go-go-golems/<repo> \
  --binary <binary> \
  --project-name <project_name> \
  --description "<one line description>" \
  --force
```

Then:

```bash
go mod tidy
make lint
go test ./... -count=1
```

## CI expectations

After pushing a branch/PR:

- unit tests: `go test ./... -count=1`
- smoke: `go run ./cmd/<binary> --help` (extend with a tiny e2e fixture for real coverage)
- lint: `golangci-lint`
- security: CodeQL, dependency review (PR), `govulncheck`, secret scanning; gosec optional

Use `gh` to inspect:

```bash
gh workflow list
gh run list --limit 20
gh run watch <run-id> --exit-status
gh run view <run-id> --log
```

## GoReleaser / releases

Typical flow:

1) push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

2) watch `release.yaml`:

```bash
gh run list --workflow release.yaml --limit 5
```

### Secrets you may need

Depends on `.goreleaser.yaml` and release workflow, but commonly:

- `GORELEASER_KEY` (if using GoReleaser Pro)
- `HOMEBREW_TAP_TOKEN` (to push formula updates to the tap repo)
- signing keys/passphrases (GPG) if signing checksums
- `FURY_TOKEN` if publishing packages to fury.io (remove the publisher section if you don’t want this)

## Retrofitting notes

- If the module path changes, update `go.mod` and fix imports (`rg` for old module string).
- Keep smoke tests cheap but meaningful (one minimal e2e fixture is worth it).
- Prefer fixing lint findings over disabling linters; if you must disable, document why in `.golangci.yml`.

