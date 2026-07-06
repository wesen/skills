---
name: go-go-golems-binary-project-creation
description: >-
  Create a new go-go-golems Go binary repository from the go-go-golems/go-template
  GitHub template, clone it under ~/code/wesen/go-go-golems, normalize the module and
  binary names, initialize docmgr, keep origin pointed at the upstream go-go-golems repo,
  optionally fork to wesen, and add the repository to a WSM workspace. Use when the user
  asks to create a new go-go-golems Golang/Go binary project, bootstrap a new CLI repo,
  or repeat the researchctl-style project creation flow.
---

# Go Go Golems Binary Project Creation

## Overview

Use this skill for the full repository-creation workflow for a new go-go-golems Go binary project. The standard path is:

1. create `github.com/go-go-golems/<repo>` from the `go-go-golems/go-template` template,
2. clone it under `~/code/wesen/go-go-golems/<repo>`,
3. replace template placeholders so the Go module, binary, logcopter area, Makefile, and command directory all use the real project name,
4. initialize `docmgr` under `ttmp/`,
5. commit the bootstrap changes,
6. fork to `github.com/wesen/<repo>` while keeping `origin` pointed at upstream,
7. optionally add the repo to the current WSM workspace and push the workspace branch.

This skill is for binary projects. If the user asks for a library-only repository or release-hardening of an existing repository, use `go-go-golems-project-setup` instead or combine both skills deliberately.

## Inputs to decide up front

Collect or infer these values before running commands:

- `repo`: repository name, for example `researchctl`.
- `binary`: CLI binary name, usually the same as `repo`.
- `module`: `github.com/go-go-golems/<repo>`.
- `description`: one-line GitHub repository description.
- `upstream`: `go-go-golems/<repo>`.
- `fork`: `wesen/<repo>` unless the user requests another account.
- `clone_root`: usually `/home/manuel/code/wesen/go-go-golems`.
- `workspace`: optional WSM workspace name, for example `benchmark-cpu-inference`.
- `workspace_branch`: optional WSM branch, usually managed by `wsm add`.

If a repository or fork already exists, stop and inspect it before creating or overwriting anything.

## Step 1 — Check tooling and existing repository state

Run these checks first:

```bash
which gh
which wsm
which docmgr
gh auth status

gh repo view go-go-golems/<repo> >/tmp/<repo>-upstream.txt 2>/tmp/<repo>-upstream.err || true
gh repo view wesen/<repo> >/tmp/<repo>-fork.txt 2>/tmp/<repo>-fork.err || true
```

Rules:

- If `go-go-golems/<repo>` already exists, do not create it again. Ask whether to reuse it.
- If `wesen/<repo>` already exists, do not fork blindly. Add it as the `wesen` remote only after verifying it is the intended fork.
- If `~/code/wesen/go-go-golems/<repo>` already exists, inspect its Git status before touching it.

## Step 2 — Create the upstream repository from the template

Create the repository without cloning through `gh`; clone explicitly in the standard code directory.

```bash
gh repo create go-go-golems/<repo> \
  --public \
  --template go-go-golems/go-template \
  --clone=false \
  --description "<one-line description>"
```

Then clone it:

```bash
cd /home/manuel/code/wesen/go-go-golems
gh repo clone go-go-golems/<repo>
cd <repo>
```

Run WSM discovery in the clone so the repository registry knows about the new repo:

```bash
wsm discover .
```

## Step 3 — Normalize the template into the real Go binary project

The template contains placeholder names such as `XXX`, `github.com/go-go-golems/XXX`, and `go-go-golems.XXX`. Replace them before feature work begins.

Expected transformations:

| Template value | Replacement |
|---|---|
| `github.com/go-go-golems/XXX` | `github.com/go-go-golems/<repo>` |
| `go-go-golems.XXX` | `go-go-golems.<repo>` |
| `cmd/XXX` | `cmd/<binary>` |
| `./dist/XXX` | `./dist/<binary>` |
| `XXX_BINARY` | upper-case binary variable, e.g. `RESEARCHCTL_BINARY` |
| README title `GO GO TEMPLATE` | `<repo>` or a better project title |

A safe scripted edit pattern is:

```bash
cd /home/manuel/code/wesen/go-go-golems/<repo>
python3 - <<'PY'
from pathlib import Path
repo = "<repo>"
binary = "<binary>"
upper = binary.upper().replace('-', '_')
replacements = {
    "github.com/go-go-golems/XXX": f"github.com/go-go-golems/{repo}",
    "go-go-golems.XXX": f"go-go-golems.{repo}",
    "package XXX": f"package {repo.replace('-', '_')}",
    "XXX_BINARY": f"{upper}_BINARY",
    "which XXX": f"which {binary}",
    "./dist/XXX": f"./dist/{binary}",
    "./cmd/XXX": f"./cmd/{binary}",
    "$(XXX_BINARY)": f"$({upper}_BINARY)",
    "GO GO TEMPLATE": repo,
    "XXX/YYY/FOOO": f"cmd/{binary}",
    "./XXX": f"./{binary}",
}
for p in [Path('go.mod'), Path('logcopter_generate.go'), Path('Makefile'), Path('pkg/logcopter.go'), Path('AGENT.md'), Path('README.md')]:
    if not p.exists():
        continue
    s = p.read_text()
    for old, new in replacements.items():
        s = s.replace(old, new)
    p.write_text(s)
PY

mkdir -p cmd/<binary>
if [ -f cmd/XXX/main.go ]; then
  git mv cmd/XXX/main.go cmd/<binary>/main.go
  rmdir cmd/XXX
fi

gofmt -w logcopter_generate.go pkg/logcopter.go cmd/<binary>/main.go
go mod tidy
```

After edits, search for leftovers:

```bash
rg -n "XXX|go-template|GO GO TEMPLATE" -S . --glob '!ttmp/**' --glob '!.git/**'
```

Do not ignore matches in build, release, or logging files. README ASCII art can remain only if the user explicitly wants it; otherwise replace it with a short project description.

## Step 4 — Initialize docmgr and commit bootstrap files

Initialize docmgr from the repository root:

```bash
docmgr init --root ttmp --seed-vocabulary
```

Stage both `ttmp/` and `.ttmp.yaml`. A common mistake is staging only `ttmp/` and leaving `.ttmp.yaml` uncommitted.

```bash
git add .ttmp.yaml ttmp AGENT.md Makefile README.md go.mod go.sum logcopter_generate.go pkg cmd
git status --short
GOWORK=off go test ./...
git commit -m "Initialize <repo> project"
```

If you prefer two commits, use:

```bash
git add .ttmp.yaml ttmp
git commit -m "Initialize docmgr workspace"

git add AGENT.md Makefile README.md go.mod go.sum logcopter_generate.go pkg cmd
git commit -m "Set repository root to <repo>"
```

Keep commits focused and inspect `git status --short` before every commit.

## Step 5 — Fork to `wesen` and set remotes

Keep `origin` pointed at upstream. Add the fork as `wesen`.

```bash
cd /home/manuel/code/wesen/go-go-golems/<repo>

gh repo fork go-go-golems/<repo> --remote=false --clone=false

git remote -v
# origin should still be git@github.com:go-go-golems/<repo>.git

git remote add wesen git@github.com:wesen/<repo>.git
# If the remote already exists, verify it instead of adding it again.

git remote -v
```

Expected remote layout:

```text
origin  git@github.com:go-go-golems/<repo>.git (fetch)
origin  git@github.com:go-go-golems/<repo>.git (push)
wesen   git@github.com:wesen/<repo>.git (fetch)
wesen   git@github.com:wesen/<repo>.git (push)
```

Push bootstrap commits to the fork:

```bash
git push wesen main
```

Do not change the Go module path to `github.com/wesen/<repo>`. The module path stays under `github.com/go-go-golems/<repo>`.

## Step 6 — Add to a WSM workspace when requested

From the workspace root, add the repository:

```bash
cd /home/manuel/workspaces/YYYY-MM-DD/<workspace>
wsm add <workspace> <repo>
```

This creates a worktree at:

```text
/home/manuel/workspaces/YYYY-MM-DD/<workspace>/<repo>
```

If `wsm add` fails because the target path already exists, inspect the target before removing anything:

```bash
TARGET=/home/manuel/workspaces/YYYY-MM-DD/<workspace>/<repo>
ls -la "$TARGET"
(cd "$TARGET" && git status --short --branch && git remote -v) || true
```

Only remove the target automatically if it is an empty partial worktree with no project files. Never delete a non-empty directory without explicit user confirmation.

After successful add, verify:

```bash
cd /home/manuel/workspaces/YYYY-MM-DD/<workspace>/<repo>
git status --short --branch
git remote -v
git branch -vv
```

Push the workspace branch to the fork when useful:

```bash
git push -u wesen task/<workspace>
```

## Step 7 — Validate and hand off

Run these checks before reporting completion:

```bash
cd /home/manuel/code/wesen/go-go-golems/<repo>
git status --short --branch
git remote -v
GOWORK=off go test ./...

gh repo view wesen/<repo> --json nameWithOwner,parent,isFork,url
```

If the repository was added to a workspace:

```bash
cd /home/manuel/workspaces/YYYY-MM-DD/<workspace>/<repo>
git status --short --branch
git remote -v
```

Report:

- upstream repo URL,
- fork repo URL,
- local clone path,
- workspace worktree path if created,
- commits created,
- validation command and result,
- any untracked files or known follow-ups.

## Common failure modes

### `.ttmp.yaml` left uncommitted

`docmgr init` creates both `ttmp/` and `.ttmp.yaml`. Always stage both. If you accidentally commit only `ttmp/`, amend the commit:

```bash
git add .ttmp.yaml
git commit --amend --no-edit
```

### `go test` fails because of an outer `go.work`

Inside a WSM workspace, `go test ./...` may use the workspace `go.work` and fail because another module requires a newer Go version. Validate the new repository itself with:

```bash
GOWORK=off go test ./...
```

Then separately fix the workspace with:

```bash
cd /home/manuel/workspaces/YYYY-MM-DD/<workspace>
go work use ./go-go-goja ./goja ./glazed ./<repo>
```

### Existing fork or remote

If `wesen/<repo>` already exists, verify it is a fork of `go-go-golems/<repo>`:

```bash
gh repo view wesen/<repo> --json nameWithOwner,parent,isFork,url
```

Only add it as `wesen` if the parent is correct or the user confirms it is intended.

### Template placeholders remain

Before the first handoff and before the first release, run:

```bash
rg -n "XXX|go-template|GO GO TEMPLATE" -S . --glob '!ttmp/**' --glob '!.git/**'
```

Fix placeholders in module paths, command directories, release config, logcopter prefixes, Makefile install targets, and README text.

## Relationship to other skills

- Use `go-go-golems-project-setup` after this skill if the project needs release-hardening, CI tuning, Homebrew tap configuration, or retrofit work beyond the template defaults.
- Use `glazed-command-authoring` when implementing the first real CLI commands.
- Use `docmgr` and `diary` when creating the first design ticket and recording implementation phases.
