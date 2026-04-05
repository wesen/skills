# Query Notes

These queries assume the default DuckDB table name `sessions_base`.

## Stable JSON locations

- `environment->>'agent_framework'`
- `environment->>'provider_hint'`
- `environment->>'model'`
- `metrics->>'turn_count'`
- `metrics->>'tool_call_count'`
- `metrics->>'read_count'`
- `metrics->>'modify_count'`
- `metrics->>'create_count'`
- `metrics->>'execute_count'`
- `metrics->>'idle_ratio'`
- `metrics->>'time_to_first_action'`
- `timing->>'started_at'`
- `timing->>'ended_at'`

## Session counts

```sql
SELECT COUNT(*) AS sessions, COUNT(DISTINCT id) AS distinct_ids
FROM sessions_base;
```

## Framework and model summary

```sql
SELECT
  environment->>'agent_framework' AS framework,
  environment->>'provider_hint' AS provider,
  environment->>'model' AS model,
  COUNT(*) AS sessions,
  SUM(CAST(metrics->>'turn_count' AS INT)) AS turns,
  SUM(CAST(metrics->>'tool_call_count' AS INT)) AS tool_calls
FROM sessions_base
GROUP BY framework, provider, model
ORDER BY framework, model;
```

## Tool frequency

```sql
SELECT
  environment->>'agent_framework' AS framework,
  REPLACE(CAST(json_extract(tc, '$.tool_name') AS VARCHAR), '"', '') AS tool_name,
  COUNT(*) AS calls
FROM sessions_base, UNNEST(tool_calls) AS t(tc)
GROUP BY framework, tool_name
ORDER BY framework, calls DESC, tool_name;
```

## Activity profile

```sql
SELECT
  id,
  environment->>'agent_framework' AS framework,
  CAST(metrics->>'read_count' AS INT) AS reads,
  CAST(metrics->>'modify_count' AS INT) AS modifies,
  CAST(metrics->>'create_count' AS INT) AS creates,
  CAST(metrics->>'execute_count' AS INT) AS executes,
  CAST(metrics->>'delegate_count' AS INT) AS delegates
FROM sessions_base
ORDER BY framework, id;
```

## Timing summary

```sql
SELECT
  environment->>'agent_framework' AS framework,
  AVG(CAST(metrics->>'idle_ratio' AS DOUBLE)) AS avg_idle_ratio,
  AVG(CAST(metrics->>'time_to_first_action' AS DOUBLE)) AS avg_time_to_first_action,
  MIN(timing->>'started_at') AS earliest,
  MAX(timing->>'ended_at') AS latest
FROM sessions_base
GROUP BY framework
ORDER BY framework;
```

## Notes

- `go-minitrace query duckdb --preset framework-summary` is the fastest first pass.
- When manifests are wrong but `.minitrace.json` files exist, query the file glob directly. DuckDB reads the session JSON files without consulting the manifests.
