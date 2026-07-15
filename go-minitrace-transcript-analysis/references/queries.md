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
