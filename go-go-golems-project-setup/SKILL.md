---
name: go-go-golems-project-setup
description: >-
  Scaffold or retrofit a go-go-golems Go repository with standard project plumbing:
  Makefile targets, pinned golangci-lint, glazed-lint, logcopter generation/checks,
  lefthook hooks, GitHub Actions (unit/smoke/lint/security), and GoReleaser release setup
  (GitHub releases + Vault/OIDC-backed Homebrew publishing).
  Use when creating a new go-go-golems Go CLI/library repo, renaming an existing module/binary
  to go-go-golems conventions, or making a repo “release-ready” with CI and GoReleaser.
---

# Go Go Golems Project Setup

## Workflow

Set up a Go project to match the common go-go-golems shape and release pipeline (CI + lint + logcopter + GoReleaser + Vault/OIDC-backed publishing). Prefer using the included scaffold script and templates so projects are consistent.

### Inputs to decide up front

- `module`: `github.com/go-go-golems/<repo>`
- `binary`: CLI name (usually same as repo)
- `project_name`: GoReleaser `project_name` (usually same as repo)
- `description`: 1-line summary for README/GoReleaser
- release targets: `linux` + `darwin` (default), `CGO_ENABLED=0` if possible
- brew tap repo: `go-go-golems/homebrew-go-go-go` (default in templates)
- release topology: a single builder or GoReleaser Pro split/merge for native platform builds
- credential inventory: distinguish same-repository `GITHUB_TOKEN` operations, Vault static vendor values, and cross-repository GitHub writes
- Terraform-owned credential profile and fixed external destinations
- whether the repo is new or must migrate legacy GitHub Actions secrets

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

### Step 3 — Design the release authorization boundary

Read the full procedure before adding or migrating a production release:

`/home/manuel/code/wesen/go-go-golems/go-go-parc/Research/playbooks/infra/PLAYBOOK - Vault Backed Go Binary Releases.md`

The standard multi-platform production arrangement is:

```text
tag push
  -> platform build job(s): Vault builder role, build-only credential
  -> named dist artifacts
  -> reusable merge/publish job: Vault publisher role
       -> caller GITHUB_TOKEN for caller-repository release operations
       -> short-lived GitHub App token for Homebrew/cross-repository writes
       -> Vault static vendor credentials only when unavoidable
```

Inventory the actual GoReleaser configuration and workflow before deciding
which credentials exist. Use `GITHUB_TOKEN` for GitHub Release operations in
the caller repository when it is sufficient. For a Homebrew tap or another
cross-repository GitHub write, use a private GitHub App installed only on that
target repository; store its App ID and private key in Vault and mint an
installation token in the final publisher job. Do not use a long-lived tap PAT.

For GoReleaser Pro split/merge releases, add two permanent Vault roles in
`/home/manuel/code/wesen/terraform/vault/github-actions/envs/k3s`:

- `release-<repo>-builder`: read only the license/build credential used by
  split jobs. It must not read App, tap, vendor-publisher, or signing paths.
- `release-<repo>-publisher`: read the Terraform-owned allowlisted credential
  profile used by the shared `publish-goreleaser-release.yml` workflow.

Bind both roles to immutable repository ID, repository, `push`, exact version
tag ref, and exact caller workflow ref. Bind the publisher role also to the
reusable workflow's `job_workflow_ref`. Credential profiles and every Vault
path belong in Terraform; a workflow may select an approved profile but never
an arbitrary Vault path or field.

Use job-level permissions. Build jobs usually have `contents: read` and
`id-token: write`, with `packages: write` only when that job pushes GHCR. Only
the final publisher has `contents: write`. Match the workflow tag trigger to
the ref pattern enforced by Vault.

For an existing project, use a temporary manual bootstrap workflow only when
current GitHub Actions secrets must move without disclosure. Require a literal
confirmation, fixed source values and KV paths, short OIDC TTL, write-only
Vault capability, temporary mode-0600 files, and a removal PR prepared before
dispatch. Register a GitHub App and store its new private key from an
authorized operator terminal, not from a GitHub Actions workflow. After a
successful migration and reversible App write proof, remove temporary
workflows and Terraform roles. Delete legacy GitHub secrets only after a
controlled version-tag release succeeds.

Add a cross-repository contract harness. It must inspect the caller workflow,
shared publisher, and Terraform policy together, including the negative
assertion that a builder cannot read publisher-only paths. Require `terraform
fmt`, `validate`, and a reviewed remote-state plan before apply. Do not apply
unrelated state drift. A targeted saved plan is an exceptional recovery tool
only when exact resources and the reason are independently reviewed.

### Step 4 — Verify CI and releases

Use `gh` to confirm the workflows exist and are green after pushing:

```bash
gh workflow list
gh run list --limit 20
```

To cut a release, push a tag and then watch the repository's release workflow:

```bash
git tag v0.1.0
git push origin v0.1.0
gh run list --workflow release.yml --limit 5
```

Also validate the release contract:

```bash
goreleaser check --config .goreleaser.yaml
goreleaser check --soft --config .goreleaser.yaml
# Run the repository's documented cross-repository contract harness.
```

`goreleaser check --soft` confirms syntax only. Resolve strict-check failures
or document a narrowly reviewed temporary exception before a production tag.

### Step 5 — Record and maintain the release contract

Document the release profile, Vault role names, fixed external destinations,
App installation scope, artifact names, validation commands, controlled-release
evidence, credential owners, and rotation date in a docmgr ticket or operations
document. Record paths, metadata versions, plans, and GitHub run URLs; never
record credential values.

When porting an existing repository, remove retired secret references in the
focused migration. Do not add backward-compatibility aliases for old secret
names unless the user explicitly requires them.

## Bundled resources

- `scripts/scaffold.py`: copy templates into the current repo and replace placeholders.
- `references/playbook.md`: scaffold-specific checklist + commands to validate CI/release.
- `/home/manuel/code/wesen/go-go-golems/go-go-parc/Research/playbooks/infra/PLAYBOOK - Vault Backed Go Binary Releases.md`:
  production credential design, bootstrap procedure, validation matrix, and cleanup checklist.
- `assets/scaffold/`: template files to copy into new repos.
