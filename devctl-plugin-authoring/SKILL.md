---
name: devctl-plugin-authoring
description: Write, update, and troubleshoot devctl plugins that speak the NDJSON stdio protocol v2 (handshake + request/response/event frames). Use when creating a new devctl plugin, converting repo scripts into devctl pipeline ops, adding dynamic commands, wiring .devctl.yaml, or debugging protocol contamination/timeouts and other plugin failures.
---

# Devctl Plugin Authoring

## Overview

Build repo-specific dev environment logic as a devctl plugin while devctl handles orchestration, supervision, and logs.

## Workflow

Before implementing, discover the installed interface with `devctl help --all`.
Read the listed user, scripting, and plugin-authoring topics (normally
`devctl help user-guide`, `devctl help scripting-guide`, and
`devctl help plugin-authoring`). Use `devctl <verb> --help` to check the flags
for each lifecycle command you intend to document or execute. Use the installed
protocol schemas and verify lifecycle semantics when selecting build, prepare,
validation, or restart behavior.

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

#### Dynamic-command registration

A plugin advertises custom commands in its handshake; devctl uses a persistent
command catalog to expose them as CLI subcommands. Plugin configuration and
command registration are separate steps:

1. Add `command.run` and deterministic command specifications to the handshake.
2. Run `devctl plugins refresh` for the intended repository and profile.
3. Invoke the advertised command and test its argument handling.
4. Refresh the catalog after changing command specifications or when devctl
   requests a refresh because its catalog is missing or stale.

`devctl plugins list` inspects plugin configuration; it is not a substitute for
registering custom commands in the catalog.

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

#### Subprocess lifetime and cancellation

Build and preparation commands are temporary children of the plugin, unlike
long-running services returned by `launch.plan`. The plugin must own their
complete lifetime:

- Convert each request's `ctx.deadline_ms` into a monotonic deadline. Give each
  subprocess only the remaining time; do not restart the full budget per step.
- Route subprocess output to stderr and bound both output collection and
  process waiting.
- On timeout or cancellation, terminate and reap all owned descendants. If a
  subprocess uses a separate process group, arrange explicit cleanup of that
  group rather than relying on termination of the plugin's group.
- Make shutdown safe during active work, idle request handling, and normal EOF.
  Cleanup must be idempotent and must not signal unrelated processes.
- In Python, use a deliberate child-cleanup and exit path for SIGTERM. Avoid
  raising exceptions through interpreter teardown. Test termination during a
  running subprocess and immediately after normal completion.

A streaming-output helper is not a complete subprocess supervisor unless it
also implements timeout, cancellation, and descendant cleanup. Test these
properties with a slow fixture child before using expensive build commands.

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
3) `devctl up` for a new environment; use replacement/force options only after inspecting installed help and confirming ownership
4) `devctl status`
5) `devctl logs <name> --tail 50` or `devctl logs <name> --stream stderr --tail 50 --follow`
6) project-specific smoke test against the devctl-managed ports/DB/log paths
7) `devctl down`

#### Isolated lifecycle smoke tests

Use a dedicated test environment with known process ownership and nonconflicting
ports. Register cleanup before starting services so a failed assertion does not
leave test processes behind:

```bash
# Only in a dedicated environment owned exclusively by this test.
set -e
trap 'devctl down' EXIT
devctl up
devctl status
# Run the project's readiness and behavior assertions here.
```

Pass the same repo/config/profile arguments to launch and cleanup. Do not use a
broad `down` trap in a shared environment or against pre-existing live services.
Verify stopped state and retained exit evidence after cleanup.

#### Build and restart contracts

Building changes artifacts on disk; restarting replaces a running service
attempt. Document them separately. In implementations that run the build phase
during restart, an explicit build followed by a restart that skips rebuilding
makes the intended artifact boundary visible:

```bash
devctl build --timeout 5m
devctl restart <name> --skip-build
```

Check prepare and validation behavior too: `--skip-build` only skips the build
phase. If preparation can modify the executable or its dependencies, the sequence
alone does not establish an immutable artifact. Prefer atomically published,
versioned artifacts, record their hashes, and associate the selected artifact
with the new service run. A hash of the current on-disk binary does not identify
an already-running executable.

Keep restart planning idempotent and avoid recursive lifecycle commands inside
plugins. Use devctl's built-in start/restart/down operations for supervision.
For hardware or stateful services, document domain-specific quiescence and
handoff prerequisites; process termination is not proof that external effects
have stopped.

#### Interpreting status

Read these independently:

- **Desired state:** what the operator requested.
- **Process/run state and exit evidence:** whether the service is running and
  how a completed attempt ended.
- **Health result:** what the last readiness probe observed, including its time.

An exited service can retain a successful historical health result. Health
checks should test the intended readiness contract without mutating external
systems; they are not evidence of current liveness after process exit.

If protocol issues appear, retry with `devctl --log-level debug plugins list`.

### 7. Troubleshoot common failures

- **stdout contamination**: non-JSON output on stdout; move logs to stderr.
- **missing handshake**: first stdout frame not a handshake; emit immediately.
- **timeouts or orphaned build children**: verify the subprocess lifetime contract above, including remaining request budget and descendant cleanup.
- **custom command unavailable**: refresh the command catalog for the intended repo/profile and verify the advertised name and arguments.
- **shutdown errors**: exercise cancellation while busy and idle; verify cleanup is idempotent and terminates only owned processes.
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
