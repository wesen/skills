---
name: go-minitrace-transcript-analysis
description: Use when analyzing previous Pi or Codex coding-agent transcripts with go-minitrace, especially to find sessions by repo/date, convert targeted subsets into minitrace archives, run DuckDB queries, and summarize findings with concrete evidence and caveats.
---

# go-minitrace Transcript Analysis

## Overview

Use this skill when the user wants to inspect prior coding-agent sessions, compare Pi and Codex behavior, or build summaries from transcript archives instead of reading raw JSONL manually.

Keep the workflow evidence-first:

1. Discover candidate native sessions.
2. Narrow by repository and time window before conversion.
3. Convert only the subset you need.
4. Query the resulting `.minitrace.json` files with DuckDB.
5. Summarize findings with explicit caveats.

Read `references/queries.md` before writing custom SQL.

## Native stores

- Codex sessions usually live under `~/.codex/sessions/YYYY/MM/DD/*.jsonl`.
- Pi sessions usually live under `~/.pi/agent/sessions/--slugged-cwd--/*.jsonl`.

## Important caveats

- `go-minitrace discover codex` does **not** expose the session working directory. For repo-specific filtering, inspect the first JSONL line and read `payload.cwd`.
- `go-minitrace convert codex` accepts only `--source-dir`, not `--source-session`. To convert a narrow Codex subset, stage matching JSONL files into a temporary `.codex/sessions/...` tree first.
- `go-minitrace convert pi --source-session ...` works for one-off files, but repeated calls into the same output directory can leave manifests reflecting only the last invocation. The `.minitrace.json` files are still queryable, so prefer querying the file glob directly or converting a whole directory in one command when manifests matter.

## Workflow

### 1. Discover recent sessions for one repository

Use the bundled scripts:

- `scripts/discover_codex_by_cwd.sh`
- `scripts/discover_pi_by_cwd.sh`

These emit tab-separated rows with session id, timestamp, size, and source path.

### 2. Stage Codex sessions when you need repo/date filtering

Use `scripts/stage_codex_by_cwd.sh` to build a temporary `.codex`-shaped tree containing only matching JSONL files.

Then convert that staged tree:

```bash
go-minitrace convert codex --source-dir /tmp/staged-codex-home --output-dir ./analysis/codex
```

### 3. Convert Pi sessions

For a repo-specific Pi directory:

```bash
go-minitrace convert pi --source-dir ~/.pi/agent/sessions/--slugged-cwd-- --output-dir ./analysis/pi
```

If you must use `--source-session`, treat the manifests as advisory and query the `.minitrace.json` files directly.

### 4. Query the archive

Start with a preset:

```bash
go-minitrace query duckdb \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --preset framework-summary
```

Then switch to custom SQL for repo-specific questions:

```bash
go-minitrace query duckdb \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --sql-file ./queries/tool-frequency.sql
```

The default table name is `sessions_base`.

## What to extract in summaries

- Session counts by framework and model
- Turn counts and tool-call counts
- Dominant tool families via `UNNEST(tool_calls)`
- Timing and latency patterns via `timing` and `metrics`
- Outlier sessions worth manual reading
- Data-quality caveats, especially manifest drift or missing repo filters

## Scripts

- `scripts/discover_codex_by_cwd.sh`: find Codex sessions for one cwd by reading `session_meta.payload.cwd`
- `scripts/discover_pi_by_cwd.sh`: find Pi sessions for one cwd from the slugged directory
- `scripts/stage_codex_by_cwd.sh`: copy matching Codex JSONL files into a temporary `.codex` tree
- `scripts/query_minitrace.sh`: run ad hoc SQL against a minitrace archive glob
- `scripts/audit_manifests.sh`: compare manifest counts with actual `.minitrace.json` file counts

## If a local go-minitrace checkout exists

Useful implementation entry points:

- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/main.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/codex.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/pi.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/minitrace/archive.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/query/engine.go`

Use those files when the user wants implementation-level analysis or when you need to explain why a query or manifest behaves a certain way.
