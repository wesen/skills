---
name: devctl-plugin-authoring
description: Write, update, and troubleshoot devctl plugins that speak the NDJSON stdio protocol v2 (handshake + request/response/event frames). Use when creating a new devctl plugin, converting repo scripts into devctl pipeline ops, adding dynamic commands, wiring .devctl.yaml, or debugging protocol contamination/timeouts and other plugin failures.
---

# Devctl Plugin Authoring

## Overview

Build repo-specific dev environment logic as a devctl plugin while devctl handles orchestration, supervision, and logs.

## Workflow

Before implementing, run `devctl help --all` and use the topic slugs printed by
that installed binary. In the current version, read `devctl help user-guide`,
`devctl help scripting-guide`, and `devctl help plugin-authoring`. Treat the
discovered slugs and schemas as authoritative rather than relying on remembered
or prefixed aliases.

### 1. Collect repo context

- Identify services to run and their commands, env vars, ports, and health checks.
- Identify prerequisites (node, docker, db migrations) and build/prepare steps.
- Decide which ops you will implement.
- Identify whether services should run directly or through a small shell wrapper for setup such as `mkdir -p var/devctl`.
- Identify which settings should be committed defaults and which should be environment overrides (ports, profile names, registry paths, credentials, backend targets).

### 2. Choose ops and config keys

- Start small: `config.mutate`, `validate.run`, and `launch.plan` are usually enough.
- Add `build.run` and `prepare.run` when you need ordered steps with artifacts.
- Add `command.run` only for dynamic helper commands (db reset, seed, etc.).
- Keep config keys stable and descriptive: `env.*`, `services.<name>.port`, `services.<name>.url`, `artifacts.*`.

For repositories with several demos or deployment shapes, prefer one small,
committed environment manifest per profile. The plugin should load and validate
the manifest, then derive config, preparation, launch, and dynamic commands from
the same source. Keep topology and secret *schemas* in the manifest; never put
secret values there.

### 3. Implement the protocol skeleton

- Emit a handshake as the very first stdout line.
- After the handshake, stdout must be *only* NDJSON frames (one JSON object per line).
- Send all logs to stderr; flush after every stdout write.
- Return `E_UNSUPPORTED` for unhandled ops to keep behavior explicit.

See `references/protocol-quickref.md` for minimal Python and bash skeletons.

### 4. Implement ops

- `config.mutate`: return a config patch with dotted keys; avoid side effects. Include useful discovered URLs/profile/config facts so `devctl plan` is informative.
- `build.run` / `prepare.run`: run named steps and return step results; respect `ctx.deadline_ms`.
- `validate.run`: return actionable errors/warnings; do not hide failures. Check executables, repo-relative paths, profile/config files, and whether dependency directories such as `web/node_modules` are missing.
- `launch.plan`: return services for devctl to supervise; do not start processes yourself.
- `command.run`: execute a named command from `capabilities.commands`; return `exit_code`.

Dynamic command names are part of the handshake and therefore must be
deterministic before a request is read. If commands vary by profile, advertise
the stable union and return an actionable error when a command is unavailable
for the active profile. Test the exact CLI flag forwarding supported by the
installed devctl rather than assuming arbitrary arguments are passed through.

For services that need shell setup, prefer a non-interactive shell wrapper such as `bash --noprofile --norc -lc 'mkdir -p var/devctl && exec ...'` so user shell startup files do not pollute logs or emit interactive-shell warnings. Still keep protocol stdout clean in the plugin itself.

For a backend + Vite frontend setup, return two services: the backend with an HTTP health check, and Vite with `VITE_*_BACKEND_TARGET` (or the repo's equivalent) so the dev server proxies API and websocket requests to the backend.

For Docker Compose, return `docker compose up` as a foreground supervised
service. Do not use detached mode: devctl needs the foreground process to
capture logs and determine whether the environment exited. Avoid fixed Docker
subnets and IP addresses unless stable addressing is an actual requirement;
they frequently overlap other development networks. Prefer service DNS names,
and make health checks independent of fixed container IPs.

When `prepare.run` materializes a set of secret files:

- fetch the complete logical set before publishing any file;
- validate encodings and minimum/exact lengths before writing;
- write a new private staging directory with restrictive modes;
- atomically switch a plugin-owned symlink to the completed directory;
- compare the target path lexically when deciding whether it is a managed
  symlink—calling `resolve()` first dereferences the symlink and breaks repeat
  preparation;
- reject unrelated existing directories instead of overwriting them;
- keep secret values out of argv, environment variables, stdout, and logs.

Use Vault KV v2 check-and-set writes when initializing missing records. Treat
runtime, bootstrap, and integration material as distinct records so permissions
and rotation procedures can differ.

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
3) `devctl up --force` when replacing existing local processes/state
4) `devctl status --tail-lines 5`
5) `devctl logs --service <name> --tail 50 --follow` and `devctl logs --service <name> --stderr --tail 50 --follow` for services that log to stderr
6) project-specific smoke test against the devctl-managed ports/DB/log paths
7) `devctl down`

If protocol issues appear, retry with `devctl --log-level debug plugins list`.

### 7. Troubleshoot common failures

- **stdout contamination**: non-JSON output on stdout; move logs to stderr.
- **missing handshake**: first stdout frame not a handshake; emit immediately.
- **timeouts**: enforce per-command timeouts using `ctx.deadline_ms`.
- **health failures**: check ports/URLs and health config in `launch.plan`.
- **Compose exits during startup**: inspect both stdout and stderr with separate
  `devctl logs` calls; BuildKit progress usually appears on stdout, while daemon
  and service failures may appear on stderr or in `devctl status`.
- **repeat prepare rejects its own secret target**: keep the target path lexical
  while checking the managed symlink; resolve only the symlink destination.
- **Docker network pool overlap**: remove unnecessary fixed subnets/IPs and use
  Compose service discovery.

## References

- Use `devctl help user-guide` for the user workflow.
- Use `devctl help scripting-guide` for practical plugin patterns.
- Use `devctl help plugin-authoring` for full protocol schemas.
