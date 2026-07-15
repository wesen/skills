---
name: go-minitrace-transcript-analysis
description: Use when analyzing previous Pi or Codex coding-agent transcripts with go-minitrace, especially to find sessions by repo/date, convert targeted subsets into minitrace archives, run normalized-SQLite queries (`query run`), and summarize findings with concrete evidence and caveats.
---

# go-minitrace Transcript Analysis

## Overview

Use this skill when the user wants to inspect prior coding-agent sessions, compare Pi and Codex behavior, or build summaries from transcript archives instead of reading raw JSONL manually.

Keep the workflow evidence-first:

1. Discover candidate native sessions.
2. Narrow by repository and time window before conversion.
3. Convert only the subset you need.
4. Query the resulting `.minitrace.json` files with the normalized SQLite engine (`query run`).
5. Summarize findings with explicit caveats.

Read `references/queries.md` before writing custom SQL — it contains the normalized schema, ready-made SQLite queries, and a migration table for any legacy DuckDB SQL.

Before inventing a query or command from scratch, use `go-minitrace help` to discover what is already embedded. The help tree includes both normalized SQLite query guidance and reusable structured query commands, so future users should prefer the built-ins first and only fall back to custom SQL when necessary.

> **Note:** The legacy DuckDB backend (`go-minitrace query duckdb`) has been removed. All SQL now runs on a normalized SQLite engine via `go-minitrace query run`. Anywhere older docs/scripts say `query duckdb`, use `query run` instead. `go-minitrace help query-duckdb` is now a migration guide, not a command.

## Native stores

- Codex sessions usually live under `~/.codex/sessions/YYYY/MM/DD/*.jsonl`.
- Pi sessions usually live under `~/.pi/agent/sessions/--slugged-cwd--/*.jsonl`.

## Important caveats

- **`discover pi --cwd-contains <repo>` has a blind spot for workspace-launched sessions.** It matches only on the session's recorded `cwd`. If the work was done *from a workspace dir* (e.g. `/home/manuel/workspaces/2026-06-20/ui-notebook-package`) rather than the repo dir itself, `--cwd-contains go-go-goja` returns nothing even though the session is heavily about that repo. The reliable fallback is to `rg -l <topic>` the raw JSONL to shortlist candidates, then convert that shortlist with `convert pi --source-list` (see step 3).
- `go-minitrace discover codex` does **not** expose the session working directory. For repo-specific filtering, inspect the first JSONL line and read `payload.cwd`.
- `go-minitrace convert codex` accepts only `--source-dir`, not `--source-session`. To convert a narrow Codex subset, stage matching JSONL files into a temporary `.codex/sessions/...` tree first.
- `go-minitrace convert pi` supports `--source-dir`, `--source-session` (repeatable), and `--source-list <file>` (newline-separated paths). Prefer `--source-list` for a narrow subset instead of staging a temp dir. Repeated `--source-session` calls into the same output dir can leave manifests reflecting only the last invocation; the `.minitrace.json` files are still queryable, so prefer querying the file glob directly or converting the whole set in one `--source-dir`/`--source-list` command when manifests matter.
- `go-minitrace query run` builds/reuses a normalized SQLite DB from the archive glob automatically — there is no separate import step. Schema introspection via `sqlite_master` is blocked by the sandbox; use `go-minitrace help minitrace-schema` or `db.tables()`/`db.schema()` from JS instead.

## Workflow

### 0. Use the built-in help tree first

The fastest way to avoid re-deriving existing analysis paths is to inspect the embedded help pages:

- `go-minitrace help query-commands` — choose between ad hoc SQL (`query run`) and reusable structured commands (`query commands`)
- `go-minitrace help query-recipes` — ready-made SQLite examples for common questions (replaces the removed `duckdb-query-recipes`)
- `go-minitrace help writing-queries` — SQLite JSON operators, the normalized schema, and query patterns (replaces the removed `writing-duckdb-queries`)
- `go-minitrace help query-duckdb` — **migration guide only**: how to rewrite legacy DuckDB SQL for the normalized SQLite schema
- `go-minitrace help structured-query-commands` — how repository-backed query commands are discovered, named, and run
- `go-minitrace query commands --help` — list the embedded command groups currently available
- `go-minitrace query commands overview session-list --help` — inspect one embedded command’s flags and usage

The embedded catalog currently includes examples such as:

- `go-minitrace query commands overview session-list`
- `go-minitrace query commands overview framework-summary`
- `go-minitrace query commands timing timing-analysis`
- `go-minitrace query commands overview aliases codex-framework-summary`

Use `go-minitrace query run` for quick ad hoc SQL analysis, and `go-minitrace query commands` when the analysis should become a named, reusable command with typed flags and web-UI support.

### 1. Discover recent sessions for one repository

For a quick first pass, use `rg -l` against the transcript trees to shortlist likely matches before doing anything heavier. These JSONL files are verbose and large, so a filename/content grep is the fastest way to identify candidate sessions. Use the grep only to narrow the candidate set; once you have the right transcripts, switch to tailored `go-minitrace` discovery/query commands instead of continuing to grep indiscriminately.

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

For a narrow subset (e.g. sessions shortlisted by an `rg` grep, or one per workspace dir), prefer `--source-list` over staging a temp dir:

```bash
# stage just the matching JSONL paths into a text file, then:
go-minitrace convert pi --source-list /tmp/sessions.txt --output-dir ./analysis/pi
```

`--source-session` (repeatable) also works for one-off files. If you must use `--source-session` repeatedly into the same output dir, treat the manifests as advisory and query the `.minitrace.json` file glob directly.

### 4. Query the archive

`go-minitrace query run` builds (or reuses from cache) a normalized SQLite database for the given archives and runs either a named preset or ad hoc SQL through a sandboxed read-only query runner. There is no separate import step.

Start with a built-in preset for one-off work:

```bash
go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --preset session-list
```

Available presets include `session-list`, `framework-summary`, `annotations`, `timing-analysis`, `tool-operation-breakdown`, `tool-failures`, `read-ratio-distribution`, `file-operations`, and `file-timeline` (see `go-minitrace help query-commands`).

Then switch to custom SQL for repo-specific questions. Save every SQL file you write inside the working folder (for example under `scripts/`) before running it, so the full analysis path is reproducible:

```bash
go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --sql-file ./queries/tool-frequency.sql \
  --max-rows 5000
```

Useful flags: `--sql`, `--sql-file`, `--preset`, `--archive-glob` (repeatable), `--max-rows`, `--max-cell-chars`, `--timeout-ms`.

The normalized schema has real tables: `sessions`, `turns`, `tool_calls`, `annotations`, `metrics`, `files`, `events`, `attachments`, `handovers`, plus a `sessions_base` compatibility view for legacy SQL. Prefer the real columns over JSON-blob access — e.g. `sessions.turn_count` instead of `metrics->>'turn_count'`, and join `tool_calls` instead of `UNNEST(tool_calls)`. See `references/queries.md` for ready-made queries and `go-minitrace help minitrace-schema` for every field. Schema introspection via `sqlite_master` is blocked by the sandbox; use `db.tables()`/`db.schema()` from JS or the schema help page.

### 4b. Write and run JS command handlers

SQL is sufficient for most analysis tasks, but JavaScript command handlers let you go further: scoring, multi-query joins in JS, async logic, relative helper modules, and richer row shapes. Use JS when the analysis logic is complex enough that SQL becomes unwieldy or when you need to reuse shared helper code.

Start by reading the two embedded help pages:

```bash
go-minitrace help js-api-reference
go-minitrace help structured-query-commands
```

The **JS API Reference** covers every export of `require("minitrace")`. The current API is **builder-composed**: you build a Go-backed `DBHandle` from sources/cache/limits, then call `db.query(...)`. The key factories are `mt.db()`, `mt.session()`, `mt.sources()`, `mt.cache()`, `mt.limits()`, `mt.importer()`, `mt.query()` (named recipes), and `mt.view()` (generic views). The **structured query commands** page covers the `__verb__`, `__section__`, and `__package__` scanner markers, the file-to-CLI path convention, and how to load external repositories.

A minimal JS command that wraps a single SQL query looks like this:

```js
__section__("filters", {
  fields: {
    framework: { type: "stringList", help: "Filter by framework" },
    limit:     { type: "int",        default: 25, help: "Row limit" },
  },
});

function sessionList(filters) {
  const mt = require("minitrace");
  const db = mt.db()
    .RuntimeArchives()
    .QueryCommandDefaults()
    .Build();
  try {
    return db.query(`
      SELECT session_id, title, agent_framework AS framework
      FROM sessions
      WHERE 1=1
      ${filters.framework?.length
        ? `AND agent_framework IN (${mt.sql.stringIn(filters.framework)})`
        : ""}
      ORDER BY started_at DESC
      LIMIT ${filters.limit ?? 25}
    `);
  } finally {
    db.close();
  }
}

__verb__("sessionList", {
  name:  "session-list",
  short: "List minitrace sessions",
  fields: { filters: { bind: "filters" } },
});
```

If that lives in `my-commands/overview/session-tools.js`, the CLI path becomes:

```bash
go-minitrace query commands overview session-tools session-list \
  --query-repository ./my-commands \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --framework codex
```

For repeated project work, avoid passing `--query-repository` manually by configuring discovery once. Current `go-minitrace` supports all of these repository sources, with CLI/env taking precedence over config and the embedded catalog last:

```bash
# Linux/macOS use ':' as the path-list separator; Windows uses ';'.
export GO_MINITRACE_QUERY_REPOSITORIES="$PWD/query-commands:$HOME/shared-minitrace-queries"
```

```yaml
# ~/.config/go-minitrace/config.yaml, ~/.go-minitrace/config.yaml,
# /etc/go-minitrace/config.yaml, <git-root>/.go-minitrace.yml,
# <git-root>/.go-minitrace.override.yml, <cwd>/.go-minitrace.yml,
# or <cwd>/.go-minitrace.override.yml
queryRepositories:
  - ./query-commands
```

Local `.go-minitrace.yml` / `.go-minitrace.override.yml` files are discovered from the git root and the current working directory. Relative `queryRepositories` entries in config files resolve relative to the config file directory, so `./query-commands` in a git-root `.go-minitrace.yml` points at that repository's query command folder regardless of the subdirectory where the command is run. If a higher-layer config file contains `queryRepositories`, it replaces lower-layer config-derived repositories; explicit `--query-repository` and `GO_MINITRACE_QUERY_REPOSITORIES` are still prepended.

**When to reach for JS instead of SQL:**

- The analysis needs multiple SQL queries whose results are joined or post-processed in JS
- You need JS-side scoring or classification logic (e.g. computing a `focus_score` from ratios)
- You need async behavior (e.g. delaying, batching, or rate-limiting)
- Several commands share helper utilities
- The output shape is richer than a flat SQL result set (cards, summaries)

**The showcase repositories are the best starting point.** Copy one and adapt it:

```bash
go-minitrace query commands --query-repository ./testdata/query-repositories/js-showcase --help
```

The `js-showcase` directory demonstrates every pattern listed in its own README: multi-verb files, aliases targeting JS commands, relative helper modules, pure synthetic rows, async commands with `require("timer")`, multi-query joins in JS, JS-side scoring, and per-session tool co-occurrence analysis.

Run them against real local sessions to see non-synthetic output:

```bash
# convert Pi sessions locally (nothing leaves the machine)
go-minitrace convert pi --source-dir ~/.pi/agent/sessions --output-dir /tmp/pi-mini

# smoke the JS showcases against the local archive
go-minitrace query commands \
  --query-repository ./testdata/query-repositories/js-showcase \
  analysis workspace-lab workspace-scoreboard \
  --archive-glob '/tmp/pi-mini/active/*/*.minitrace.json' \
  --output json
```

Validate the commands before trusting their output — malformed JS or SQL errors surface as runtime exceptions. Run through the CLI first, then test with `--output json` to confirm the row shape matches your expectation.

For a worked example of JS + SQL side-by-side in the same repository, see `testdata/query-repositories/mixed-sql-js-showcase/`.

## What to extract in summaries

- Session counts by framework and model
- Turn counts and tool-call counts
- Dominant tool families via the `tool_calls` table (join on `session_id`)
- Timing and latency patterns via the `sessions` columns and the `metrics` table
- Outlier sessions worth manual reading
- Data-quality caveats, especially manifest drift or missing repo filters

## Scripts

- `scripts/discover_codex_by_cwd.sh`: find Codex sessions for one cwd by reading `session_meta.payload.cwd`
- `scripts/discover_pi_by_cwd.sh`: find Pi sessions for one cwd from the slugged directory
- `scripts/stage_codex_by_cwd.sh`: copy matching Codex JSONL files into a temporary `.codex` tree
- `scripts/query_minitrace.sh`: run ad hoc SQL against a minitrace archive glob (uses `go-minitrace query run`)
- `scripts/audit_manifests.sh`: compare manifest counts with actual `.minitrace.json` file counts

## Embedded documentation quick reference

These embedded help pages cover the full surface area:

| Help page | What it covers |
|-----------|----------------||
| `go-minitrace help js-api-reference` | `require("minitrace")` builder factories, all built-in modules, scanner markers, field types |
| `go-minitrace help structured-query-commands` | Authoring `.sql` and `.js` files, repository layout, aliases |
| `go-minitrace help query-recipes` | Ready-to-use SQLite SQL for common analysis patterns |
| `go-minitrace help writing-queries` | SQLite JSON operators and normalized-schema query patterns |
| `go-minitrace help minitrace-schema` | Every field in a minitrace session document |
| `go-minitrace help annotation-playbook` | Annotation CLI and web UI workflow |
| `go-minitrace help query-duckdb` | **Migration guide only** — rewriting legacy DuckDB SQL for the normalized SQLite schema |

## If a local go-minitrace checkout exists

`go-minitrace help` and `go-minitrace help --ui` already expose a substantial set of embedded commands, queries, and tutorials. Check those first before inventing new SQL or shell workflows; many common analysis tasks already have examples or preset queries you can reuse.

Useful implementation entry points:

- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/main.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/codex.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/pi.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/minitrace/archive.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/query/engine.go`

Use those files when the user wants implementation-level analysis or when you need to explain why a query or manifest behaves a certain way.
