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

Before inventing a query or command from scratch, use `go-minitrace help` to discover what is already embedded. The help tree includes both raw DuckDB query guidance and reusable structured query commands, so future users should prefer the built-ins first and only fall back to custom SQL when necessary.

## Native stores

- Codex sessions usually live under `~/.codex/sessions/YYYY/MM/DD/*.jsonl`.
- Pi sessions usually live under `~/.pi/agent/sessions/--slugged-cwd--/*.jsonl`.

## Important caveats

- `go-minitrace discover codex` does **not** expose the session working directory. For repo-specific filtering, inspect the first JSONL line and read `payload.cwd`.
- `go-minitrace convert codex` accepts only `--source-dir`, not `--source-session`. To convert a narrow Codex subset, stage matching JSONL files into a temporary `.codex/sessions/...` tree first.
- `go-minitrace convert pi --source-session ...` works for one-off files, but repeated calls into the same output directory can leave manifests reflecting only the last invocation. The `.minitrace.json` files are still queryable, so prefer querying the file glob directly or converting a whole directory in one command when manifests matter.

## Workflow

### 0. Use the built-in help tree first

The fastest way to avoid re-deriving existing analysis paths is to inspect the embedded help pages:

- `go-minitrace help query-commands` — choose between raw SQL (`query duckdb`) and reusable structured commands (`query commands`)
- `go-minitrace help query-duckdb` — built-in DuckDB presets, SQL-file mode, and archive loading flags
- `go-minitrace help structured-query-commands` — how repository-backed query commands are discovered, named, and run
- `go-minitrace help duckdb-query-recipes` — ready-made SQL examples for common questions
- `go-minitrace help writing-duckdb-queries` — JSON access, `UNNEST`, casting, and annotation query patterns
- `go-minitrace query commands --help` — list the embedded command groups currently available
- `go-minitrace query commands overview session-list --help` — inspect one embedded command’s flags and usage

The embedded catalog currently includes examples such as:

- `go-minitrace query commands overview session-list`
- `go-minitrace query commands overview framework-summary`
- `go-minitrace query commands timing timing-analysis`
- `go-minitrace query commands overview aliases codex-framework-summary`

Use `go-minitrace query duckdb` for quick ad hoc analysis, and `go-minitrace query commands` when the analysis should become a named, reusable command with typed flags and web-UI support.

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

If you must use `--source-session`, treat the manifests as advisory and query the `.minitrace.json` files directly.

### 4. Query the archive

For one-off work, start with the embedded DuckDB presets or a saved SQL file:

```bash
go-minitrace query duckdb \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --preset framework-summary
```

Then switch to custom SQL for repo-specific questions. Save every SQL file you write inside the working folder (for example under `scripts/`) before running it, so the full analysis path is reproducible:

```bash
go-minitrace query duckdb \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --sql-file ./queries/tool-frequency.sql
```

The default table name is `sessions_base`.

### 4b. Write and run JS command handlers

SQL is sufficient for most analysis tasks, but JavaScript command handlers let you go further: scoring, multi-query joins in JS, async logic, relative helper modules, and richer row shapes. Use JS when the analysis logic is complex enough that SQL becomes unwieldy or when you need to reuse shared helper code.

Start by reading the two embedded help pages:

```bash
go-minitrace help js-api-reference
go-minitrace help structured-query-commands
```

The **JS API Reference** covers every export of `require("minitrace")` — `mt.query()`, `mt.queryOne()`, `mt.tableName`, `mt.sql.string()`, `mt.sql.stringIn()`, `mt.sql.like()`, and `mt.runtime` — as well as the other built-in modules (`timer`, `database`, `fs`, `exec`, `path`, `console`). The **structured query commands** page covers the `__verb__`, `__section__`, and `__package__` scanner markers, the file-to-CLI path convention, and how to load external repositories.

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
  return mt.query(`
    SELECT id, title,
           environment->>'agent_framework' AS framework
    FROM ${mt.tableName}
    WHERE 1=1
    ${filters.framework?.length
      ? `AND environment->>'agent_framework' IN (${mt.sql.stringIn(filters.framework)})`
      : ""}
    ORDER BY timing->>'started_at' DESC
    LIMIT ${filters.limit}
  `);
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

The `js-showcase` directory demonstrates every pattern listed in its own README: multi-verb files, aliases targeting JS commands, relative helper modules, pure synthetic rows, async commands with `require("timer")`, `mt.queryOne()` reshaping, multi-query joins in JS, JS-side scoring, and per-session tool co-occurrence analysis.

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

## Embedded documentation quick reference

These embedded help pages cover the full surface area:

| Help page | What it covers |
|-----------|----------------||
| `go-minitrace help js-api-reference` | `require("minitrace")`, all built-in modules, scanner markers, field types |
| `go-minitrace help structured-query-commands` | Authoring `.sql` and `.js` files, repository layout, aliases |
| `go-minitrace help duckdb-query-recipes` | Ready-to-use SQL for common analysis patterns |
| `go-minitrace help writing-duckdb-queries` | JSON access, `UNNEST`, casting, annotation queries |
| `go-minitrace help minitrace-schema` | Every field in a minitrace session document |
| `go-minitrace help annotation-playbook` | Annotation CLI and web UI workflow |
| `go-minitrace help query-duckdb` | Presets, `--sql-file`, and archive loading flags |

## If a local go-minitrace checkout exists

`go-minitrace help` and `go-minitrace help --ui` already expose a substantial set of embedded commands, queries, and tutorials. Check those first before inventing new SQL or shell workflows; many common analysis tasks already have examples or preset queries you can reuse.

Useful implementation entry points:

- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/main.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/codex.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/cmd/go-minitrace/cmds/convert/pi.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/minitrace/archive.go`
- `/home/manuel/code/wesen/corporate-headquarters/go-minitrace/pkg/query/engine.go`

Use those files when the user wants implementation-level analysis or when you need to explain why a query or manifest behaves a certain way.
