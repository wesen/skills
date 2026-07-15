# Query Notes

All queries run on the **normalized SQLite engine** via `go-minitrace query run`.
There is no separate import step — `query run` builds/reuses a SQLite DB from the
archive glob and executes the SQL through a sandboxed read-only runner.

```bash
go-minitrace query run \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --sql-file ./queries/tool-frequency.sql
```

Useful flags: `--sql`, `--sql-file`, `--preset`, `--archive-glob` (repeatable),
`--max-rows`, `--max-cell-chars`, `--timeout-ms`.

Built-in presets (see `go-minitrace help query-commands`): `session-list`,
`framework-summary`, `annotations`, `timing-analysis`,
`tool-operation-breakdown`, `tool-failures`, `read-ratio-distribution`,
`file-operations`, `file-timeline`.

## Normalized schema (tables)

The engine materializes real tables from each `.minitrace.json`. The ones you
will query most:

- `sessions` — one row per session, with **real columns** (no JSON-blob access
  needed for common fields).
- `turns` — one row per message, joined to `sessions` by `session_id`, ordered
  by `turn_index`.
- `tool_calls` — one row per tool invocation, joined by `session_id` and
  `emitting_turn_index`.
- Also: `annotations`, `metrics`, `files`, `events`, `attachments`, `handovers`.
- `sessions_base` — compatibility view that keeps the legacy flattened shape
  working for session-level SQL.

Key `sessions` columns: `session_id`, `title`, `agent_framework`,
`provider_hint`, `model`, `working_directory`, `started_at`, `ended_at`,
`duration_seconds`, `turn_count`, `tool_call_count`, `read_count`,
`modify_count`, `create_count`, `execute_count`, `git_branch`, `source_path`,
`raw_json` (full original document, for long-tail fields).

Treat `sessions.source_path` as importer/archive provenance, not necessarily the
original native JSONL path. Preserve discovery output and source-list files when
native provenance matters.

Key `turns` columns: `session_id`, `turn_index`, `timestamp`, `role`,
`content`, `model`, `thinking`, `input_tokens`, `output_tokens`.

Key `tool_calls` columns: `session_id`, `tool_call_id`, `tool_name`,
`operation_type`, `command`, `file_path`, `emitting_turn_index`, `success`,
`error`, `exit_code`, `duration_ms`, `result`, `arguments_json`, `raw_json`.

Long-tail fields that never got a real column are reachable via
`json_extract(raw_json, '$.path.to.field')` on any table.

> Schema introspection via `sqlite_master` is blocked by the sandbox. Use
> `go-minitrace help minitrace-schema`, or `db.tables()` / `db.schema()` from a
> JS command handler, to inspect the schema.

## Session counts

```sql
SELECT COUNT(*) AS sessions, COUNT(DISTINCT session_id) AS distinct_ids
FROM sessions;
```

## Framework and model summary

```sql
SELECT
  agent_framework AS framework,
  provider_hint   AS provider,
  model,
  COUNT(*) AS sessions,
  SUM(turn_count)      AS turns,
  SUM(tool_call_count) AS tool_calls
FROM sessions
GROUP BY framework, provider, model
ORDER BY framework, model;
```

## Session list (with timing)

```sql
SELECT
  session_id,
  substr(title, 1, 50)        AS title,
  agent_framework             AS framework,
  model,
  turn_count,
  tool_call_count,
  working_directory,
  started_at
FROM sessions
ORDER BY started_at DESC;
```

## Tool frequency

```sql
SELECT
  s.agent_framework AS framework,
  tc.tool_name,
  COUNT(*) AS calls
FROM tool_calls tc
JOIN sessions s USING (session_id)
GROUP BY framework, tool_name
ORDER BY framework, calls DESC, tool_name;
```

## Activity profile

```sql
SELECT
  session_id,
  agent_framework AS framework,
  read_count     AS reads,
  modify_count    AS modifies,
  create_count    AS creates,
  execute_count   AS executes
FROM sessions
ORDER BY framework, session_id;
```

## Timing summary

```sql
SELECT
  agent_framework AS framework,
  AVG(duration_seconds) AS avg_duration_s,
  MIN(started_at)       AS earliest,
  MAX(ended_at)         AS latest
FROM sessions
GROUP BY framework
ORDER BY framework;
```

## Find user turns matching a topic (e.g. a repo or PR)

```sql
SELECT session_id, turn_index,
       substr(coalesce(content, ''), 1, 160) AS snippet
FROM turns
WHERE role = 'user'
  AND (content LIKE '%go-go-goja%' OR content LIKE '%xgoja%')
ORDER BY session_id, turn_index;
```

## Last activity per session (when sessions actually ended)

```sql
SELECT s.session_id,
       substr(s.title, 1, 40) AS title,
       (SELECT t.timestamp FROM turns t
        WHERE t.session_id = s.session_id
        ORDER BY t.turn_index DESC LIMIT 1) AS last_turn_at,
       s.turn_count
FROM sessions s
ORDER BY last_turn_at DESC;
```

## Build a portable command-text view

Pi commonly populates `tool_calls.command`. Some Codex adapters leave that
column empty and retain the command or wrapper source in `arguments_json`.
Use a CTE that preserves both the normalized columns and the serialized
arguments:

```sql
WITH calls AS (
  SELECT
    session_id,
    emitting_turn_index AS turn_index,
    tool_call_id,
    tool_name,
    operation_type,
    success AS transport_success,
    exit_code AS normalized_exit_code,
    file_path,
    coalesce(
      nullif(command, ''),
      json_extract(arguments_json, '$.command'),
      json_extract(arguments_json, '$.cmd'),
      json_extract(arguments_json, '$.input'),
      arguments_json
    ) AS command_text,
    arguments_json,
    result,
    error
  FROM tool_calls
)
SELECT *
FROM calls
ORDER BY session_id, turn_index;
```

For wrapped Codex exec calls, `transport_success = 1` may mean only that the
outer tool call completed. The nested subprocess exit code may be encoded in
`result` while `normalized_exit_code` remains null.

## Find exact repository activity

Replace the example path with a distinctive absolute repository path. This
query finds candidates; it does not prove that every returned operation
succeeded.

```sql
WITH calls AS (
  SELECT
    session_id,
    emitting_turn_index AS turn_index,
    tool_name,
    operation_type,
    success,
    exit_code,
    coalesce(nullif(command, ''),
             json_extract(arguments_json, '$.input'),
             arguments_json) AS command_text,
    file_path,
    result,
    error
  FROM tool_calls
)
SELECT *
FROM calls
WHERE coalesce(command_text, '')
        LIKE '%/home/manuel/workspaces/example/repository%'
   OR coalesce(file_path, '')
        LIKE '%/home/manuel/workspaces/example/repository%'
ORDER BY session_id, turn_index;
```

## Find commit command candidates without claiming success

Do not use a raw `arguments_json LIKE '%git commit%'` count as the number of
Git commits. Restrict to shell/exec tools and retain result fields for review:

```sql
WITH exec_calls AS (
  SELECT
    session_id,
    emitting_turn_index AS turn_index,
    tool_call_id,
    tool_name,
    success AS transport_success,
    exit_code AS normalized_exit_code,
    coalesce(nullif(command, ''),
             json_extract(arguments_json, '$.command'),
             json_extract(arguments_json, '$.cmd'),
             json_extract(arguments_json, '$.input'),
             arguments_json) AS command_text,
    result,
    error
  FROM tool_calls
  WHERE tool_name IN ('bash', 'exec', 'exec_command', 'shell')
)
SELECT *
FROM exec_calls
WHERE command_text LIKE '%git commit%'
ORDER BY session_id, turn_index;
```

Classify the output into four distinct quantities:

1. serialized rows containing `git commit`;
2. actual command attempts;
3. attempts with confirmed nested exit status zero;
4. resulting hashes verified with `git -C <repo> show`.

Only the fourth quantity is a repository-verified commit count.

## Find exact file creation or patch evidence

For Codex patch wrappers, the path may exist only in `arguments_json`:

```sql
SELECT
  session_id,
  emitting_turn_index AS turn_index,
  tool_name,
  operation_type,
  success,
  file_path,
  substr(arguments_json, 1, 2000) AS arguments,
  substr(result, 1, 1000) AS result
FROM tool_calls
WHERE coalesce(file_path, '') LIKE '%pkg/example/target.go%'
   OR arguments_json LIKE '%pkg/example/target.go%'
ORDER BY session_id, turn_index;
```

Inspect nearby turns before deciding whether the path was written, quoted,
reviewed, or merely searched.

## Role-classification profile

This aggregate helps identify sessions that mention a target but perform little
observable work. Adapter limitations mean the result is a shortlist, not a
final role assignment.

```sql
SELECT
  s.session_id,
  s.agent_framework,
  s.model,
  s.working_directory,
  s.turn_count,
  s.tool_call_count,
  SUM(CASE WHEN tc.operation_type = 'READ' THEN 1 ELSE 0 END) AS reads,
  SUM(CASE WHEN tc.operation_type IN ('NEW', 'MODIFY') THEN 1 ELSE 0 END)
    AS normalized_writes,
  SUM(CASE WHEN tc.tool_name IN ('bash', 'exec', 'exec_command', 'shell')
           THEN 1 ELSE 0 END) AS exec_calls
FROM sessions s
LEFT JOIN tool_calls tc USING (session_id)
GROUP BY s.session_id, s.agent_framework, s.model, s.working_directory,
         s.turn_count, s.tool_call_count
ORDER BY normalized_writes DESC, exec_calls DESC, s.tool_call_count DESC;
```

A review session can have high topic counts and almost no emitted tool calls.
A long-lived implementer can have a misleading original cwd. Confirm roles with
exact operations and external repository state.

## Evaluate diary timing

When a worker was required to maintain a diary, identify diary writes in the
worker's converted Pi transcript:

```sql
SELECT
  session_id,
  emitting_turn_index AS turn_index,
  tool_name,
  success,
  file_path,
  substr(coalesce(command, arguments_json, ''), 1, 500) AS invocation
FROM tool_calls
WHERE coalesce(file_path, '') LIKE '%diary.md%'
   OR coalesce(command, arguments_json, '') LIKE '%diary.md%'
ORDER BY session_id, turn_index;
```

Compare write timestamps with the events described in each checkpoint. A diary
written correctly at the end can still have poor contemporaneous fidelity.

## Adapter and identity caveats

- Native Codex child sessions can have unique `payload.id` values while the
  converter normalizes them to a shared parent thread ID. Audit native sources
  before conversion and use separate output directories when necessary.
- `operation_type = OTHER` does not prove that a Codex call was read-only.
- Empty `command`, `file_path`, or `exit_code` columns do not prove the native
  field is absent; inspect `arguments_json`, `result`, and `raw_json`.
- A tool-call `success` value can describe transport success rather than nested
  process success.
- Text in a user turn or tool argument may quote another transcript. Emitted
  repository-changing tool calls carry more attribution weight than mentions.

## Migrating legacy DuckDB SQL

`go-minitrace help query-duckdb` is now a migration guide. The common rewrites:

| Legacy DuckDB pattern | Normalized SQLite equivalent |
|---|---|
| `environment->>'agent_framework'` | `sessions.agent_framework` column |
| `metrics->>'turn_count'` | `sessions.turn_count` (more rollups in `metrics` table) |
| `->` / `->>` on other blob columns | prefer the real `sessions` columns; unchanged SQL keeps working against the `sessions_base` compat view |
| `UNNEST(tool_calls) AS t(tc)` | query the `tool_calls` table, join `USING (session_id)` |
| `UNNEST(turns) WITH ORDINALITY` | query the `turns` table (`turn_index` column) |
| `LEFT(x, n)` | `substr(x, 1, n)` |
| `CAST(x AS DATE)` | `date(x)` |
| `REPLACE(CAST(json_extract(...) AS VARCHAR), '"', '')` | plain `json_extract(...)` — SQLite returns unquoted values |
| `DESCRIBE` / `SHOW TABLES` | `db.schema()` / `db.tables()` from JS (sandbox blocks `sqlite_master`), or `go-minitrace help minitrace-schema` |
| `read_json(...)` | not needed — the database is built from archives automatically |

Session-level SQL using `->`/`->>` on the old blob columns keeps working
unmodified against the `sessions_base` compatibility view (SQLite >= 3.38
supports the JSON arrow operators); per-tool-call and per-turn SQL must move to
the `tool_calls` / `turns` tables.
