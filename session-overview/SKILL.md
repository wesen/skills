---
name: session-overview
description: Build a self-contained, browsable HTML summary page for coding-agent transcripts (Claude Code, Codex, Pi). Use when asked for a summary page, overview, dashboard or "what did these sessions do" report over one or many transcripts, a workspace, or a date range; takes transcript paths, a workspace to discover in, or converted go-minitrace archives. Shows each session's task, parsed <summary> checkpoints and file targets.
metadata:
  title: Session Overview Page
  topics:
    - go-minitrace
    - transcripts
    - reporting
    - html
  what_for: Turn agent transcripts into one interactive HTML page showing the task, the agent's final report, and every file target per session.
  when_to_use: When the user wants a summary/overview page over coding-agent sessions or transcript paths.
---

# Session Overview Page

Produce one self-contained HTML file that summarizes a set of coding-agent
transcripts: one card per session with framework, model, timing, turn/tool
counts, the first substantive user prompt, the agent's last message, and the
structural file targets it touched. The page is interactive — live search,
framework filters, sorting, a sidebar index, collapsible file lists, and
click-to-copy paths — and needs no server or network.

## When to use it

- "Build a summary page for these transcripts."
- "What did the sessions in this workspace do?"
- "Make an overview of my agent sessions from last week."

For deep, question-driven analysis of a single transcript (attribution,
symbol relevance, adoption tracing), use `go-minitrace-transcript-analysis`
instead; that skill owns discovery/conversion semantics and the SQL schema.
This skill owns the *presentation* of a session set.

## Script

```
~/.pi/agent/skills/session-overview/scripts/session_overview.py
```

Requirements: `python3` (stdlib only) and `go-minitrace` on `PATH`.
No Python packages are needed.

## Quick start

Four input modes; pick one.

```bash
S=~/.pi/agent/skills/session-overview/scripts/session_overview.py

# 1. A workspace: discover all three frameworks by recorded cwd, then convert.
python3 "$S" --workspace /home/manuel/workspaces/2026-09-01/add-plot-editor \
  --active-since 2026-09-01 --out ~/tmp/overview.html

# 2. Explicit native transcripts (framework auto-detected from the path).
python3 "$S" --source-session ~/.pi/agent/sessions/--slug--/abc.jsonl \
  --source-session ~/.codex/sessions/2026/09/04/rollout-abc.jsonl

# 3. A file listing transcript paths, one per line (# comments allowed).
python3 "$S" --source-list ./sessions.txt --out ~/tmp/overview.html

# 4. Already-converted archives — no go-minitrace conversion needed.
python3 "$S" --from-glob './analysis/*/active/*/*.minitrace.json' --no-open
```

The page opens in a browser by default; `--no-open` suppresses that.
A `--json` sidecar of the extracted records is useful for diffing or reuse.

## Flags

| Flag | Meaning |
|---|---|
| `--from-glob GLOB` | Read converted `*.minitrace.json` archives (repeatable). |
| `--source-session PATH` | Native transcript to convert (repeatable; framework auto-detected). |
| `--source-list FILE` | File of transcript paths, one per line (repeatable). |
| `--workspace DIR` | Discover sessions whose recorded cwd contains DIR. |
| `--active-since DATE` | With `--workspace`: only sessions active at/after DATE. |
| `--framework FW` | Restrict discovery to `pi` / `codex` / `claude-code` (repeatable). |
| `--source-dir FW=DIR` | Override a framework's native store, e.g. `codex=~/.codex`. |
| `--out FILE` | HTML output; default `~/tmp/session-overview-<slug>.html`. |
| `--json FILE` | Also write extracted session records as JSON. |
| `--title TITLE` | Page title. |
| `--strip-prefix PREFIX` | Prefix removed from displayed paths (repeatable; workspace and `~` are stripped automatically). |
| `--no-files` | Omit the file ledger. |
| `--min-assistant-chars N` | Ignore assistant messages shorter than N (default 40). |
| `--work-dir DIR` | Scratch dir for discovery/convert output (default: temp dir). |
| `--no-open` | Do not open a browser. |

## What the page shows

- **Search** filters sessions on title, prompt, outcome, model, branch, summary
  text and file paths, highlights matches, and hides non-matching files inside
  a card.
- **Chips** toggle frameworks independently; colors match the framework.
- **Sort**: oldest, newest, most files, most turns.
- **`has files`** narrows to sessions with a file ledger; **`has summary`**
  narrows to sessions with parsed summary blocks.
- **`expand files`** opens every ledger; per-card `<details>` state is remembered.
- **Sidebar** is a sticky, search-synced index that jumps to a card.
- Clicking a path or session id copies it.

Per-session record: framework, model, start time, duration, turns, tool calls,
new/modified/read/exec counts, task, latest summary, final agent message, file
targets, branch.

## Summary blocks

Pi sessions emit `<summary>` checkpoints when the `session-summary` extension is
active. The tool parses every block in every assistant turn into the four known
fields — **This turn**, **Session so far**, **Issues**, **Next steps** — and:

- shows the **latest** block as a distinct section on each card, between the
task and the free-form final report, with an `N summaries` badge in the meta row;
- offers a **`browse all N`** control that opens an expanded modal listing every
block, newest selectable, with `prev` / `next` and `ArrowUp` / `ArrowDown`;
- shows, for each block, the **files written since the previous checkpoint** — a
per-block `NEW`/`MODIFY` delta rather than the session-wide ledger;
- includes all summary text in the search index and in the JSON sidecar.

A block attributed to turn N owns every tool-call write after the previous
block's turn and up to and including N. Writes without a turn index are skipped
rather than guessed at, so a delta may be smaller than reality but never
invented. The card notes how many files the newest checkpoint introduced.

A block whose body has no recognised headings is kept as free prose rather than
discarded. Claude Code and Codex transcripts carry no such blocks, so their
counts are legitimately zero.

> Reading archives with `grep '<summary>'` returns nothing: minitrace is Go and
> `encoding/json` writes `<` as `\u003c` (`\u003csummary\u003e`). Decode the JSON,
> or grep for `u003csummary`.

## Correctness contract (state these when reporting)

- **Task** is the first user turn that is not CLI/extension noise; **final
  report** is the agent's own last message. It is a claim, not verification.
- **File targets** are structural `NEW`/`MODIFY` tool-call evidence, not
  verified commits. Verify against git before asserting authorship.
- Selection is by **recorded working directory**. A session started elsewhere,
  or a long-lived one that later entered the repo, will not appear; widen with
  explicit `--source-session` paths or `--from-glob`.
- Codex transcripts commonly normalize to opaque `exec` wrappers and expose no
  per-file ledger; edits inside shell heredocs also produce none. The page
  states "No structured file targets" rather than implying no files changed.
- **Summary fields are parsed leniently.** A field name appearing in ordinary
  prose can start a section; the JSON sidecar keeps the parsed result, so verify
  against the transcript before quoting a field as authoritative.
- **Summary duplication is expected.** When a session's last assistant message
  is summary-only, the same text appears both in the latest-summary section and
  in the final-report section.
- The expanded modal has `role="dialog"` with `aria-modal`, but focus is not
  trapped and is not restored to the opening button on close.
- The page is static and local: no network calls, no backend, no telemetry.

## Validation performed

- Regenerated a 17-session / 670-file page from converted archives and compared
  counts against the original hand-built generator.
- Exercised `--workspace` end to end (`discover` → `convert` → render).
- Exercised `--source-session` with framework auto-detection.
- Confirmed filters in a browser: search reduced 17 → 2 sessions, framework
  toggle 17 → 13, `has files` 17 → 8, `expand files` opened the 8 ledgers.
- Summary pipeline: 117 blocks parsed across 4 of 17 archives; the first card
  rendered `Latest summary · 3 total` with all four fields; `has summary`
  narrowed 17 → 4.
- Expanded view: the PicoCalc session listed 43 blocks, opened on block 43 of 43,
  moved to block 42 with `ArrowUp`, and closed with `Escape` while releasing the
  body scroll lock.
- Per-checkpoint deltas: the identity-cutover session showed 15 files since the
  previous summary on its final block, and per-block counts summed to 119.

## Related

- `go-minitrace-transcript-analysis` — discovery, conversion, SQL schema and
  attribution caveats.
- `daily-log` — narrative daily report from the same underlying sessions.
