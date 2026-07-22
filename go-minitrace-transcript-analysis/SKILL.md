---
name: go-minitrace-transcript-analysis
description: Use when analyzing previous Pi or Codex coding-agent transcripts with go-minitrace, especially to find sessions by repository/date, attribute implementation work to a session, convert targeted native JSONL sources, query normalized SQLite tables, compare agent behavior, and report evidence with explicit caveats.
---

# go-minitrace Transcript Analysis

## Purpose

Use this skill to turn native coding-agent session logs into a small, reproducible body of evidence. The standard sequence is:

1. Define the question and evidence standard.
2. Inspect the installed CLI help for the commands you will use.
3. Discover and shortlist native sessions; use `--active-since` rather than `--since` when the question is about recorded activity in a time window.
4. Convert only the required source files.
5. Query normalized SQLite tables with saved SQL.
6. Reopen relevant transcript context and external state.
7. Report observations, inferences, alternatives, and caveats separately.

Raw grep is a candidate-selection tool, not the final analytical method. A cwd match, filename, title, or topic count is never sufficient proof that a session implemented a change.

The legacy DuckDB backend (`go-minitrace query duckdb`) is removed. Use `go-minitrace query run` and the normalized SQLite schema.

## Load references selectively

- Read `references/queries.md` before custom SQL. It documents the normalized schema, adapter caveats, and verified query patterns.
- Read `references/attribution.md` when determining which session implemented repository work, authored commits, or created files.
- Read `references/js-query-authoring.md` only when the analysis should become a reusable JavaScript query command. Most investigations need saved SQL, not a JS command repository.

## Built-in query commands

Typed verbs for the recurring "join transcript evidence to something outside the transcript" question shape. They ship **embedded in the binary itself** (`pkg/minitracecmd/core/`) — no `--query-repository` flag, no separately-distributed skill files. This skill ships no query commands of its own. Run them directly:

```bash
go-minitrace query commands <group> <verb> --archive-glob '<archives>/active/*/*.minitrace.json' --output json ...
```

If `go-minitrace query commands history --help` shows nothing, the installed binary predates this change — rebuild from a checkout containing commit `311102e`+ (`make install` in the go-minitrace repo).

### `history <verb>`

- **`history file-history --path <fragment>`** — when was a file created/edited/read, in which session/turn, at what timestamp; per-file summary plus full timeline. Extracts every *structurally* file-path-shaped candidate from a tool call — the `file_path` column, each `*** Update/Add/Delete File:` header in a Codex patch, JSON `file_path`/`path` keys, shell redirect targets — and keeps those matching the fragment. Two consequences worth knowing: a multi-file Codex patch correctly attributes to every file it touches (`tool_calls.file_path` only records the first), and prose that merely mentions a path is not counted as a touch. Paths are home-normalized before grouping, so `~/x` and `/home/you/x` collapse into one summary row.
- **`history ticket-timeline --ticket <fragment>`** — when was a docmgr ticket created (`docmgr ticket create`), and when were its `tasks.md`/`changelog.md`/diary files touched. Reports evidence (a command ran, a file was touched), not verified success — cross-check against the ticket's own git history for certainty.
- **`history context-window --session <id> --turn <n>`** — for a given turn, reconstructs every file, tool call, and skill signal since the last compaction boundary. Combines a textual continuation-summary marker with a cache-read-collapse heuristic (`--boundary-method auto|summary-only|cache-collapse-only` — note kebab-case on the CLI even though the JS field is `boundaryMethod`); has no reliable signal on Codex archives (no comparable cache accounting — prefer `summary-only` there).

Chain `ticket-timeline` → `context-window` to answer "when was this ticket created, and what was the agent's context at that moment" in two calls: take the `ticket-timeline` creation event's `session_id`/`turn_index` and feed them straight into `context-window`.

### Activity verbs

- **`overview session-activity`** — sessions ordered by last interaction, where that is the latest of any turn *or* any tool call. Filters: `--framework`, `--cwd-contains`, `--since`, `--limit`.
- **`files file-activity`** — touched files by most recent write or tool activity, one row per (session, file) with an operation count. Filters add `--path-contains` and `--write-only` (default true: NEW and MODIFY only). Narrowing with `--since`/`--path-contains` narrows `operations` too — it counts operations in the requested window, not the file's lifetime.

These two previously lived in this skill as one `overview/session-activity.js`; they are now one verb per file, so the paths are flat (`overview session-activity`, `files file-activity`) rather than doubled.

Design rationale and the original validation log (including one false-positive bug found and fixed) live in ticket `GOGO-MINITRACE-HISTORY-VERBS-2026-07-20` (claw-stuff), `design-doc/01` and `reference/01-diary.md`. The embedding work itself (moving from external `--query-repository` into `pkg/minitracecmd/core/`) is documented in ticket `ADD-HISTORY-QUERY-COMMANDS-2026-07-20` (go-minitrace repo, `ttmp/2026/07/20/`).

## Native stores

- Codex: `~/.codex/sessions/YYYY/MM/DD/*.jsonl`
- Pi: `~/.pi/agent/sessions/--slugged-cwd--/*.jsonl`

Never modify native session files. Convert them into an investigation-specific output directory.

## Required command preflight

Do not trust remembered flags or stale skill prose over the installed CLI. Before discovery and conversion, run command-specific help for the paths you will use:

```bash
go-minitrace discover pi --help
go-minitrace discover codex --help
go-minitrace convert pi --help
go-minitrace convert codex --help
go-minitrace query run --help
go-minitrace help minitrace-schema
```

For broader analysis options:

```bash
go-minitrace help query-commands
go-minitrace help query-recipes
go-minitrace help writing-queries
```

If the help output contradicts this skill, follow the installed CLI and record the skill drift as a finding.

## Current behavior and caveats

### Discovery

Both `discover pi` and `discover codex` expose `cwd` when the native source records it, and both support `--cwd-contains`. Pi, persisted Codex session JSONL, and Claude Code JSONL also support opt-in `--active-since`, which scans candidate transcripts and emits `last_activity_at`.

Cwd is a shortlist signal, not a content index. Relevant work may be hidden when:

- a session starts from a workspace or parent directory;
- a long-lived session later works in another repository;
- a Codex parent spawns subagents in another cwd;
- a review or investigation session uses the target cwd without implementing anything.

`--since` remains a **start-time** filter: it cannot find a session that began earlier and continued working in the target window. Use `--active-since` for that recovery question. It is more expensive because it streams candidate native JSONL sources. Codex `exec-jsonl-v1` has no authoritative native timestamps and is explicitly reported as unsupported for `--active-since`; do not infer activity from its file mtime.

When cwd discovery misses relevant work, use exact content signatures to shortlist raw JSONL files, then convert the shortlist. Prefer exact paths, commit hashes, ticket IDs, symbols, and unusual phrases over broad topic words.

### Conversion

Both Pi and Codex conversion currently support:

- `--source-dir`
- repeatable `--source-session`
- `--source-list <file>`

Prefer one `--source-list` conversion for a narrow set. Save the source list as an investigation artifact.

### Codex parent/subagent identity and collision safety

Native Codex child files retain their own first `session_meta.payload.id` as the archive identity. Parent thread IDs are recorded separately as lineage. Conversion preflights every requested source, fingerprints raw bytes, rejects conflicting native IDs, and stages the complete batch before publication.

The default `--collision error` policy rejects an existing archive backed by different source bytes. Use `--collision replace` only after independently verifying provenance. Capture a conversion receipt and validate the resulting archive:

```bash
go-minitrace convert codex \
  --source-list ./sessions.txt \
  --output-dir ./analysis/codex \
  --run-record ./analysis/codex/conversion-run.json

go-minitrace validate \
  --path ./analysis/codex \
  --archive \
  --output json
```

The legacy `scripts/audit_codex_sources.sh` can inspect raw native metadata when debugging, but it is no longer required for collision safety.

### Normalized adapter limitations

For some Codex transcripts:

- `operation_type` is `OTHER` for exec and patch operations;
- `command`, `file_path`, or `exit_code` may be empty;
- commands, workdirs, and patch targets remain in `arguments_json`;
- a nested subprocess exit code remains in `result`;
- `success = 1` may mean only that the outer tool transport succeeded.

Inspect `arguments_json`, `result`, and the native transcript before concluding that an operation did not occur or succeeded. Verify commits and files against the repository itself.

### Query engine

`go-minitrace query run` builds or reuses a normalized SQLite database from archive globs automatically. There is no separate import step. The main tables are `sessions`, `turns`, `tool_calls`, `annotations`, `metrics`, `files`, `events`, `attachments`, and `handovers`.

Schema introspection through `sqlite_master` is blocked by the query sandbox. Use `go-minitrace help minitrace-schema` or `db.tables()` / `db.schema()` from a JS handler.

## Workflow

## Playbook: Find sessions active during a time window

Use this playbook when the user asks which Pi or Codex sessions were active at a relative time (for example, “which sessions were active 10 minutes ago?”), especially after a crash or restart.

### 1. Establish the exact time window

Capture the current wall-clock time and timezone before searching:

```bash
date --iso-8601=seconds
```

Convert the relative time to UTC/RFC3339. Define a small activity window around the target (for example, target minus one minute through target plus one minute, or wider if event timestamps are sparse). Report both local time and UTC.

### 2. Run CLI preflight and structured discovery

Check installed help first:

```bash
go-minitrace discover pi --help
go-minitrace discover codex --help
go-minitrace convert pi --help
go-minitrace convert codex --help
go-minitrace query run --help
```

Preserve discovery output. Use `--active-since` for a target activity window; it selects older sessions whose latest native activity is at or after the boundary and returns `last_activity_at`:

```bash
go-minitrace discover pi --source-dir ~/.pi/agent/sessions \\
  --active-since YYYY-MM-DD --output json > pi-discovery.json
go-minitrace discover codex --source-dir ~/.codex \\
  --active-since YYYY-MM-DD --output json > codex-discovery.json
```

Use `--since` only when “session started in this period” is the intended criterion. If a Codex exec JSONL source causes `--active-since` to report unsupported activity filtering, preserve that limitation in the report; its native stream has no authoritative event timestamp.

### 3. Shortlist native sources by exact content when needed

`--active-since` is structured candidate selection, not proof of implementation. When cwd/activity discovery misses relevant work or needs topical narrowing, use exact content signatures to shortlist raw JSONL sources. Treat raw matches only as candidate selection: quoted transcript text may contain false positives. Record each candidate’s native path and timestamps, never modify native files, and save separate source lists.

### 4. Convert only the shortlisted sources

Convert the saved lists into a new investigation directory:

```bash
mkdir -p ./analysis/recovery/{archives/pi,archives/codex}
go-minitrace convert pi \\
  --source-list ./analysis/recovery/pi-sources.txt \\
  --output-dir ./analysis/recovery/archives/pi
go-minitrace convert codex \\
  --source-list ./analysis/recovery/codex-sources.txt \\
  --output-dir ./analysis/recovery/archives/codex
```

Use only flags supported by the installed CLI. Do not assume that `--run-record` exists; if preflight rejects it, record the flag drift and continue without it. Preserve conversion output and manifests.

### 5. Query normalized timing and context

Query all converted archives together. First list session timing and last activity, then inspect turns near the target:

```sql
SELECT s.session_id, s.agent_framework AS framework, s.model,
       s.title, s.working_directory, s.started_at, s.ended_at,
       s.turn_count, s.tool_call_count,
       (SELECT MAX(t.timestamp) FROM turns t
        WHERE t.session_id = s.session_id) AS last_turn_at,
       (SELECT MAX(tc.timestamp) FROM tool_calls tc
        WHERE tc.session_id = s.session_id) AS last_tool_at
FROM sessions s
ORDER BY COALESCE(last_tool_at, last_turn_at, s.ended_at) DESC;
```

Then query `turns` for a bounded interval around the target. Use the results to distinguish genuinely active sessions from sessions that merely contain the target timestamp in quoted or imported transcript content. Save SQL and JSON results.

### 6. Report and recommend a resume target

For every candidate, report the framework, session ID, native source path, working directory, started/ended/last-activity timestamps, title/model, and the most recent meaningful context near the target. Classify it as implementer, reviewer, investigator, or reference-only where possible.

If multiple sessions overlap, do not silently choose one. Identify the strongest resume candidate from the latest direct user instruction and meaningful implementation context, list alternatives, and state timezone, target window, discovery limitations, conversion caveats, and saved evidence paths.

### 1. Define the question and acceptance evidence

Write down what would prove the answer before searching. Examples:

- exact session ID and native source path;
- repository commit hash and timestamp correlation;
- patch/write operations against specific files;
- exact user instruction and relevant turn range;
- test commands and results;
- evidence that alternatives were review-only or reference-only.

Create a working directory with saved inputs and queries:

```bash
mkdir -p ./analysis ./queries ./results
```

### 2. Establish external state first

For repository attribution, inspect Git history and current changes before transcript discovery:

```bash
git -C "$REPO" log \
  --since="$SINCE" \
  --date=iso-strict \
  --pretty='%H%x09%aI%x09%s' \
  --name-status

git -C "$REPO" status --short
git -C "$REPO" diff --name-only
```

Extract distinctive signatures: full hashes, commit subjects, changed paths, symbols, ticket IDs, and untracked files. See `references/attribution.md` for the full evidence procedure.

### 3. Run structured discovery

Examples:

```bash
# For work that started during the period:
go-minitrace discover pi \
  --source-dir ~/.pi/agent/sessions \
  --since "$SINCE" \
  --cwd-contains "$CWD_FRAGMENT" \
  --output json > ./pi-candidates.json

# For work that recorded activity during the period, including older sessions:
go-minitrace discover codex \
  --source-dir ~/.codex \
  --active-since "$SINCE" \
  --cwd-contains "$CWD_FRAGMENT" \
  --output json > ./codex-candidates.json
```

Preserve the discovery output. Do not stop after the first plausible match.

### 4. Use exact content fallback when necessary

Use raw grep only to create a source list:

```bash
rg -l -F 'pkg/example/distinctive_file.go' \
  ~/.pi/agent/sessions ~/.codex/sessions \
  > ./content-candidates.txt
```

Use two or more independent signatures when possible. Inspect candidate metadata and deduplicate paths before conversion. Broad terms such as a language name or repository topic produce review and quotation false positives.

### 5. Convert the narrow source set

Pi:

```bash
go-minitrace convert pi \
  --source-list ./pi-sessions.txt \
  --output-dir ./analysis/pi
```

Codex:

```bash
go-minitrace convert codex \
  --source-list ./codex-sessions.txt \
  --output-dir ./analysis/codex \
  --run-record ./analysis/codex/conversion-run.json

go-minitrace validate --path ./analysis/codex --archive --output json
```

For deliberate source-by-source isolation during debugging:

```bash
n=0
while IFS= read -r source; do
  [[ -z "$source" || "$source" == \#* ]] && continue
  n=$((n + 1))
  go-minitrace convert codex \
    --source-session "$source" \
    --output-dir "./analysis/codex-source-$n"
done < ./codex-sessions.txt
```

Then query repeatable archive globs or a glob that includes each output root.

### 6. Profile the converted archives

Start with built-ins:

```bash
go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --preset session-list

go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --preset tool-failures
```

Save custom SQL before executing it:

```bash
go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --sql-file ./queries/relevant-tool-calls.sql \
  --output json \
  --max-rows 5000 \
  > ./results/relevant-tool-calls.json
```

Query the archive files directly. Treat manifests as advisory until counts and source identities are audited.

### 7. Verify evidence externally

SQL identifies candidate turns and tool calls. It does not prove authorship by itself.

For implementation attribution:

1. inspect exact tool-call arguments and results;
2. reopen nearby transcript turns;
3. verify resulting hashes with repository Git history;
4. verify file content and working-tree state;
5. classify alternatives by observable activity;
6. state unresolved ambiguity.

Never report a text match for `git commit` as a successful commit object. Separate mention rows, command attempts, nested exit status, and repository-verified hashes.

### 8. Report with explicit roles and caveats

A strong report includes:

- question and time window;
- candidate-selection method;
- framework, session ID, native source path, cwd, and relevant time range;
- decisive user turns and tool calls;
- repository hashes, paths, commands, and external verification;
- implementer/reviewer/investigator/reference-only classification where relevant;
- alternatives rejected and why;
- adapter, manifest, collision, or missing-data caveats;
- saved query and result paths;
- confidence tied to evidence strength.

## Evidence hierarchy for attribution

Strong evidence:

- patch/write operation targeting the exact repository file;
- repository-verified commit hash correlated with transcript command and time;
- test execution against the changed package;
- creation of a current untracked file with matching transcript content.

Supporting evidence:

- command executed with the repository as workdir;
- user instruction requesting the exact implementation;
- file reads and Git status around the relevant operation.

Weak evidence:

- cwd alone;
- filename or title alone;
- keyword frequency;
- quoted transcript content;
- review text that describes another session's work.

Do not attribute implementation from weak evidence alone.

## Diary requirements when requested

A diary is an intervention, not neutral telemetry. If the user requests one:

- append each checkpoint before starting the next phase;
- record wall-clock timestamp, goal, evidence, exact command/query, decision, failure, changed assumption, confidence, and next action;
- do not reconstruct all checkpoints at the end;
- preserve diary writes so an evaluator can compare checkpoint time with transcript events.

## Scripts

- `scripts/audit_codex_sources.sh`: legacy diagnostic for inspecting raw Codex IDs and parent-thread IDs; normal conversion no longer depends on it.
- Archive/manifest/receipt integrity is checked by `go-minitrace validate --archive`; do not use `scripts/audit_manifests.sh` in new workflows.
- `scripts/query_minitrace.sh`: run saved SQL against archive globs.
- `scripts/discover_pi_by_cwd.sh`: legacy/local fallback; prefer `go-minitrace discover pi`.
- `scripts/discover_codex_by_cwd.sh`: legacy/local fallback; prefer `go-minitrace discover codex`.
- `scripts/stage_codex_by_cwd.sh`: legacy fallback only; current Codex conversion supports `--source-list` and `--source-session`.

## Completion checklist

Before finalizing an analysis:

- [ ] Installed command help was checked.
- [ ] Native sources were not modified.
- [ ] Candidate source lists and custom SQL were saved.
- [ ] Conversion counts and Codex parent/subagent collisions were audited.
- [ ] Claims were verified against transcript context and external state.
- [ ] Command mentions were not mislabeled as successful operations.
- [ ] Implementer, reviewer, investigator, and reference-only sessions were distinguished where relevant.
- [ ] Caveats and rejected alternatives were reported.
- [ ] Diary checkpoints were contemporaneous if the diary arm was requested.
