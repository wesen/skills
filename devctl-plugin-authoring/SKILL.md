---
name: devctl-plugin-authoring
description: Write, update, and troubleshoot devctl plugins that speak the NDJSON stdio protocol v2 (handshake + request/response/event frames). Use when creating a new devctl plugin, converting repo scripts into devctl pipeline ops, adding dynamic commands, wiring .devctl.yaml, or debugging protocol contamination/timeouts and other plugin failures.
---

# Devctl Plugin Authoring

## Overview

Build repo-specific dev environment logic as a devctl plugin while devctl handles orchestration, supervision, and logs.

## Workflow

### 1. Collect repo context

- Identify services to run and their commands, env vars, ports, and health checks.
- Identify prerequisites (node, docker, db migrations) and build/prepare steps.
- Decide which devctl ops you will implement.

### 2. Choose ops and config keys

- Start small: `config.mutate`, `validate.run`, and `launch.plan` are usually enough.
- Add `build.run` and `prepare.run` when you need ordered steps with artifacts.
- Add `command.run` only for dynamic helper commands (db reset, seed, etc.).
- Keep config keys stable and descriptive: `env.*`, `services.<name>.port`, `services.<name>.url`, `artifacts.*`.

### 3. Implement the protocol skeleton

- Emit a handshake as the very first stdout line.
- After the handshake, stdout must be *only* NDJSON frames (one JSON object per line).
- Send all logs to stderr; flush after every stdout write.
- Return `E_UNSUPPORTED` for unhandled ops to keep behavior explicit.

See `references/protocol-quickref.md` for minimal Python and bash skeletons.

### 4. Implement ops

- `config.mutate`: return a config patch with dotted keys; avoid side effects.
- `build.run` / `prepare.run`: run named steps and return step results; respect `ctx.deadline_ms`.
- `validate.run`: return actionable errors/warnings; do not hide failures.
- `launch.plan`: return services for devctl to supervise; do not start processes yourself.
- `command.run`: execute a named command from `capabilities.commands`; return `exit_code`.

Always honor:

- `ctx.repo_root` for relative paths.
- `ctx.dry_run` by avoiding side effects.
- `ctx.deadline_ms` by enforcing timeouts in subprocesses.

### 5. Wire the repo config

Add `.devctl.yaml` at repo root, e.g.:

- `id`: stable plugin identifier.
- `path` + `args`: how to run the plugin.
- `env`: optional plugin env vars.
- `priority`: merge precedence.

### 6. Test the loop

Use the tight feedback loop:

1) `devctl plugins list`
2) `devctl plan`
3) `devctl up`
4) `devctl status`
5) `devctl logs --service <name> --follow`
6) `devctl down`

If protocol issues appear, retry with `devctl --log-level debug plugins list`.

### 7. Troubleshoot common failures

- **stdout contamination**: non-JSON output on stdout; move logs to stderr.
- **missing handshake**: first stdout frame not a handshake; emit immediately.
- **timeouts**: enforce per-command timeouts using `ctx.deadline_ms`.
- **health failures**: check ports/URLs and health config in `launch.plan`.

## References

- Use `devctl help devctl-user-guide` for the user workflow.
- Use `devctl help devctl-scripting-guide` for practical plugin patterns.
- Use `devctl help devctl-plugin-authoring` for full protocol schemas.
