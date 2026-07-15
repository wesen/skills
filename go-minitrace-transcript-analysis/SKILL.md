---
name: go-minitrace-transcript-analysis
description: Use when analyzing previous Pi or Codex coding-agent transcripts with go-minitrace, especially to find sessions by repository/date, attribute implementation work to a session, convert targeted native JSONL sources, query normalized SQLite tables, compare agent behavior, and report evidence with explicit caveats.
---

# go-minitrace Transcript Analysis

## Purpose

Use this skill to turn native coding-agent session logs into a small, reproducible body of evidence. The standard sequence is:

1. Define the question and evidence standard.
2. Inspect the installed CLI help for the commands you will use.
3. Discover and shortlist native sessions.
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

Both `discover pi` and `discover codex` expose `cwd` when the native source records it, and both support `--cwd-contains`.

Cwd is a shortlist signal, not a content index. Relevant work may be hidden when:

- a session starts from a workspace or parent directory;
- a long-lived session later works in another repository;
- a Codex parent spawns subagents in another cwd;
- a review or investigation session uses the target cwd without implementing anything.

When cwd discovery misses relevant work, use exact content signatures to shortlist raw JSONL files, then convert the shortlist. Prefer exact paths, commit hashes, ticket IDs, symbols, and unusual phrases over broad topic words.

### Conversion

Both Pi and Codex conversion currently support:

- `--source-dir`
- repeatable `--source-session`
- `--source-list <file>`

Prefer one `--source-list` conversion for a narrow set. Save the source list as an investigation artifact.

### Codex parent/subagent identity collision

Native Codex subagent files have their own `payload.id`, but may also record:

```text
payload.source.subagent.thread_spawn.parent_thread_id
```

The current Codex converter can normalize a child source to the parent thread identity. Converting a parent and several children into one output directory can therefore produce the same `.minitrace.json` path and overwrite or collapse outputs even though the native IDs are distinct.

Before converting a Codex shortlist, run:

```bash
scripts/audit_codex_sources.sh ./sessions.txt
```

If several sources map to one effective normalized identity, either:

1. select the authoritative source required by the question; or
2. convert each source into a separate output directory and query all directories explicitly.

After conversion, compare source count, archive count, manifests, `session_id`, and source provenance. A broader archive glob cannot recover a source that was already overwritten.

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
go-minitrace discover pi \
  --source-dir ~/.pi/agent/sessions \
  --since "$SINCE" \
  --cwd-contains "$CWD_FRAGMENT" \
  --output json > ./pi-candidates.json

go-minitrace discover codex \
  --source-dir ~/.codex \
  --since "$SINCE" \
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
scripts/audit_codex_sources.sh ./codex-sessions.txt

go-minitrace convert codex \
  --source-list ./codex-sessions.txt \
  --output-dir ./analysis/codex
```

If the Codex audit reports an effective-identity collision, convert separately:

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

- `scripts/audit_codex_sources.sh`: inspect native Codex IDs, parent-thread IDs, and effective normalized-identity collision risk before conversion.
- `scripts/audit_manifests.sh`: compare generated archive counts with manifest counts.
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
