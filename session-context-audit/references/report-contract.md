# Session context audit report contract

## Model

The renderer accepts one JSON object:

```json
{
  "title": "DEVCTL Robust Lifecycle",
  "kicker": "CONTEXT AUDIT / 2026-09-13",
  "subtitle": "Repository and branch",
  "turns": [
    {"number": "1", "title": "Initial request", "bullets": ["Requested implementation."]}
  ],
  "timeline": [
    {
      "period": "10:00–10:20",
      "category": "engineering",
      "title": "Implemented feature",
      "bullets": ["Changed the runtime."],
      "advice": []
    }
  ],
  "knowledge": [
    {"label": "INVARIANT", "text": "One process Wait owner."}
  ],
  "file_groups": [
    {"title": "Runtime", "items": [{"name": "pkg/runtime/client.go", "purpose": "Plugin request lifecycle."}]}
  ],
  "change_groups": [
    {"title": "Added", "items": [{"name": "pkg/runtime/process_lifetime.go", "purpose": "Own process cleanup."}]}
  ],
  "api_groups": [
    {"title": "Read", "items": [{"name": "runtime.Factory.Start", "purpose": "Starts and handshakes plugins."}]}
  ],
  "state": ["Working tree clean.", "Next: integration qualification."]
}
```

All top-level list fields may be empty but must be present. The renderer rejects unknown timeline categories and malformed item shapes.

## Timeline classifications

- **analysis**: reading contracts, tracing control flow, comparing APIs, designing or deciding.
- **engineering**: implementing, refactoring, testing intended behavior, or fixing a discovered product defect.
- **menial/support**: formatting, ticket bookkeeping, printing slips, staging, routine publication, and cleanup.
- **issue/churn**: avoidable rework, wrong assumptions, accidental artifacts, tool friction, repeated ineffective attempts, or unrelated breakage.

Every `issue/churn` item requires at least one `advice` entry. Advice should change a future workflow, test order, guard, instruction, or tool—not merely say “be more careful.”

## Turn numbering

A turn is an authored user request followed by the assistant's handling of it. Do not create turns for:

- injected session metadata;
- hidden goal/bookkeeping notices;
- tool calls;
- background continuation ticks;
- assistant-only checkpoints.

When a user prompt contains several requests, keep one turn and describe the subrequests in bullets.

## API inventory

Use fully qualified names when practical:

- Go: `operator.Controller.Restart`, `runstate.Store.LoadRun`.
- Python: `devctl_runner.Runner.run`.
- CLI/framework: `cli.BuildCobraCommandFromCommand`.

Each item answers two questions in one short sentence: what the symbol owns and why it mattered in this session.

Use **removed/replaced** for deleted APIs, deleted behavior, or an in-progress migration away from an API. Label in-progress removals honestly.

## HTML and archival requirements

- One standalone UTF-8 HTML file with embedded CSS.
- No JavaScript or remote fonts/assets are required.
- Escape all model values.
- Responsive at narrow widths.
- The ticket copy is authoritative; `/tmp` browser copies are disposable.
- Remove `.playwright-mcp/`, screenshots, `__pycache__/`, and temporary server logs unless explicitly requested as evidence.
