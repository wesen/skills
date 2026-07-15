# JavaScript Query Command Authoring

Load this reference only when transcript analysis should become a named, reusable command with typed flags, multiple SQL queries, JS-side scoring, helper modules, or web-UI integration. For one investigation, saved SQL under the working directory is usually simpler and more reproducible.

## Required help

```bash
go-minitrace help js-api-reference
go-minitrace help structured-query-commands
go-minitrace query commands --help
```

The JavaScript API is builder-composed. Build a `DBHandle`, call `db.query(...)`, and close it in `finally`.

## Minimal command

```js
__section__("filters", {
  fields: {
    framework: { type: "stringList", help: "Filter by framework" },
    limit: { type: "int", default: 25, help: "Row limit" },
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
  name: "session-list",
  short: "List minitrace sessions",
  fields: { filters: { bind: "filters" } },
});
```

If this file lives at `my-commands/overview/session-tools.js`, invoke it with:

```bash
go-minitrace query commands \
  --query-repository ./my-commands \
  overview session-tools session-list \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --framework codex \
  --output json
```

## Main factories

The current `require("minitrace")` module exposes builders such as:

- `mt.db()` — database handle configuration;
- `mt.session()` — session-oriented helpers;
- `mt.sources()` — archive source configuration;
- `mt.cache()` — cache policy;
- `mt.limits()` — query limits;
- `mt.importer()` — import/materialization configuration;
- `mt.query()` — named recipes;
- `mt.view()` — generic views.

Confirm the live API through `go-minitrace help js-api-reference`; do not infer method names from older examples.

## When JS is justified

Use JS when:

- several SQL queries must be joined or post-processed;
- the analysis computes a score or classification from multiple metrics;
- output needs nested or synthetic rows;
- commands share helper modules;
- async batching or timing is part of the command;
- the command should be discoverable through the structured CLI and web UI.

Do not use JS merely to wrap one static SQL file unless typed flags or command discovery provide real value.

## Repository discovery

Pass a repository explicitly:

```bash
go-minitrace query commands \
  --query-repository ./query-commands \
  --help
```

Or configure repositories:

```bash
export GO_MINITRACE_QUERY_REPOSITORIES="$PWD/query-commands:$HOME/shared-minitrace-queries"
```

```yaml
# .go-minitrace.yml
queryRepositories:
  - ./query-commands
```

Linux and macOS use `:` as the environment path-list separator; Windows uses `;`.

Local `.go-minitrace.yml` and `.go-minitrace.override.yml` files are discovered from the Git root and current working directory. Relative `queryRepositories` entries resolve relative to the config file. Explicit CLI and environment repositories take precedence over config and embedded repositories.

## Validation

Validate commands through the CLI before trusting their output:

```bash
go-minitrace query commands \
  --query-repository ./query-commands \
  <section> <file> <verb> \
  --archive-glob './analysis/*/active/*/*.minitrace.json' \
  --output json
```

Check:

- malformed JS surfaces as an error;
- SQL runs against the current normalized schema;
- every database handle is closed;
- output JSON has the intended row shape;
- helper functions are not accidentally registered as verbs;
- query limits are explicit for potentially large outputs.

## Showcase repositories

When a local go-minitrace checkout is available, inspect:

```text
testdata/query-repositories/js-showcase/
testdata/query-repositories/mixed-sql-js-showcase/
```

The showcase covers multi-verb files, aliases, relative helpers, synthetic rows, async commands, multi-query joins, JS-side scoring, and tool co-occurrence analysis. Read its README and run the commands against a small local archive before copying a pattern.
