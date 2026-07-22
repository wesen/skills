# Interpreting docmetrics output

Grounding: everything here was established empirically on ticket
GOGO-DOCS-OPTIMIZE-2026-07-19 (claw-stuff), which analyzed the go-go-wm build
session (f26d0273, 668 tool calls) plus five comparison sessions with seven
subagent deep-dives (reports in that ticket's `analysis/02`-`08`; synthesis in
`analysis/09`). Baseline numbers below come from those sessions.

## Adapter traps (check before quoting ANY number)

0. **The JS `db.query()` sandbox silently caps rows (~1000 by default).** No
   error, no flag — with multiple archives only the first session fits the
   window, producing false "missing data" bugs. All shipped verbs set
   `mt.limits().Rows(200000)`; do the same in any new verb, and distrust any
   result whose row count is suspiciously round.

1. **Token inflation ~2-2.5x.** The claude-code adapter stores one `turns` row
   per content block; consecutive assistant rows from one API call repeat
   identical usage numbers. Never SUM token columns naively — use the
   `api-calls` verb's deduped totals and report the inflation_factor. The
   dedup itself is heuristic (identical-tuple collapse, ±5%).
2. **`metrics.subagent_count` counts TaskCreate rows**, not real subagents.
   Verify delegation via `tool_calls.spawned_agent_type != ''`.
3. **User turns have NULL `content_type`** in claude-code archives; filtering
   `content_type != 'tool_result'` silently returns zero rows. Always
   `COALESCE(content_type,'')`. Tool results arrive as `role='user'` rows.
4. **Doc reads hide in Bash.** `sed -n 1,120p SKILL.md`, `cat ARTICLE.md` —
   Read-tool-based counting undercounts documentation consumption badly.
   `doc-consumption` scans command text; so must any custom query.
5. **`success=0` is not friction** until verified: expected non-zero exits
   (pkill with no match, grep no-match probes) and partial successes (payload
   delivered, trailing pretty-printer failed) inflate failure counts. The
   `failure-triage` categories are heuristic candidate labels — the S5-style
   adversarial pass showed a naive classifier mislabeled 5 of 6 "go-compile"
   rows. Verify per-failure context before reporting.
6. **Exit 143/144 + pkill in command = probable self-kill**: `pkill -f`
   patterns match the harness zsh's own `-c` command line and kill the tool
   call mid-payload. This is real friction (lost payloads, recovery calls),
   not noise — but it is ONE bug, not N independent failures.
7. **Codex (codex-session-jsonl-v1) is failure-blind and command-buried**:
   `success` always 1, `exit_code` NULL (real exit codes survive as
   `{"exit_code":N}` chunks in result text); shell commands live inside
   `arguments_json.input` as `tools.exec_command({cmd:"..."})` JS; results
   are Go map stringifications; `wait` calls (~8% of totals) inflate counts;
   approval-assessor sidecar rollouts share the work cwd (see SKILL.md §1).
8. **Pi conventions**: lowercase tool names; `success` keyed off exit code
   even when the payload was delivered (conformance runners, `go doc A B C`
   batches → systematic false failures); assistant narration is NOT in
   `turns.content` (empty for tool-call-only turns) — reconstruct intent
   from tool_calls + human turns.
9. **Framework comparisons are confounded** by model differences and task
   type. Control for task before attributing behavior to the harness: on one
   identical task given to all three frameworks, behavior converged; the
   dramatic divergences came from build-marathon sessions.

## Healthy-session thresholds (empirical baselines)

| Signal | Unhealthy (observed baseline) | Healthy target |
|---|---|---|
| Embedded `<app> help` calls when library APIs are touched | 0 across 6/6 sessions | > 0; first lookup goes to docs |
| Source-probe waves into repos that have skills/help topics | 3-6 waves, 20-45 probes/session | Probes only to *verify* docs, not first contact |
| Repeat-probes (same symbol, 2+ waves) | Present after every /compact | 0 — knowledge persisted to disk before compaction |
| Knowledge-acquisition share of tool calls | ~16% (4:1 on house libs) | < 8%, majority third-party |
| Skill loads for library-API work | 0 (only process skills fire) | Loaded at implementation start, incl. after phase pivots ("build it.", "p5") and re-loaded post-compact |
| Skill sideloads via Bash cat/sed | Recurring | 0 — sideloads mean the Skill mechanism was bypassed |
| Greps for renamed/removed symbols | Present (agents carry version-drifted priors) | 0 — docs carry a renamed-APIs table |

## Failure category → guard mapping

Each `failure-triage` category maps to a one-line prevention guard (full
worked list: GOGO-DOCS-OPTIMIZE ticket, `analysis/06` S5 report):

| Category | Guard (target: AGENT.md unless noted) |
|---|---|
| self-kill | Never `pkill -f`/`pgrep -f` a pattern that appears literally in the same command; use pidfiles or `pkill -x`; never combine build+restart in one shell (Makefile `restart-stack` target) |
| zsh-expansion | Quote `echo "==="` or use `---` separators; zsh expands unquoted `=words` |
| read-before-edit | Files created by scaffolding tools (docmgr doc add) must be Read before the first Write; Bash `cat` does not register |
| cwd-drift | The persistent shell keeps your last `cd`; use subshells `(cd x && ...)` and absolute-path prefixes |
| missing-file (hallucinated path) | Never type long slugs (ttmp ticket dirs) from memory; resolve with ls/glob first |
| nul-byte | Write control bytes as escapes (`"\x00"`), never literal; optional lefthook NUL-check pre-commit |
| timeout (blocking wait) | Bound waits on interactive processes: `timeout 10 tail --pid=$P -f /dev/null \|\| kill $P` |
| go-compile via shell surgery | Never sed Go imports; use Edit or goimports (`cmd \| head \|\| fallback` never runs the fallback — pipeline status is head's) |
| partial-success | Don't `2>/dev/null` the extraction step you depend on; recheck before treating as failure |

## Cost attribution (token analysis)

- ~80% of session cost is cache reads → **resident context size dominates**.
  Grep residue (~10-15k tokens/wave) is re-read by every later call until a
  compact; curated references (~4-6k tokens each) are 10x smaller resident.
- Attribute a knowledge-acquisition stretch's cost as the whole API calls in
  the stretch (probe + the thinking that consumes it), plus carry
  (cache_creation added x remaining calls in the context window).
- State the price-ratio model explicitly (e.g. cache_read 0.1x, creation
  1.25x, output 5x input) — shares are robust to it, absolute figures are not.
- /compact has positive ROI (context collapse saves tens of millions of
  cache-read tokens) but silently evicts loaded skills and fresh grep
  knowledge. The fix is procedural: persist findings to a ticket doc before
  compacting; re-load skills after. `api-calls`' compaction_events gives the
  timing; `source-probes`' repeat_probes measures the re-derivation.

## Fix-type catalog (what analyses produce)

1. **Stale-instruction fixes** — a skill teaching a removed API (e.g.
   `engine.New()` after its removal) actively causes grep waves. Highest
   priority always; check skills against the library's README/source first.
2. **Signature references** — the difference between "skill was read" and
   "greps happened anyway" is exact signatures. Skills give shape; agents
   need verifiable signatures (a renamed-APIs table kills guess-greps).
3. **Pointer layers** — skills enumerate the relevant `<app> help` slugs and
   pkg/doc files ("read these first"); AGENT.md points at vault/KB notes.
   Content that exists but isn't pointed at has an observed consumption rate
   of zero.
4. **Description rewrites** — product language + task-state file-path
   triggers; loaded skills die at /compact, so also add re-load rules.
5. **Guards** — the failure-category table above.
6. **Upstreaming** — generic material written into ticket docs moves to help
   topics; ticket docs then link instead of re-derive.
7. **Third-party-library cookbooks** — when the dominant probe target is a
   dependency you don't control (e.g. ory/fosite: upstream documents only its
   Quickstart), the fix destination is an in-repo `docs/internals/` cookbook
   in the consuming project, usually extractable from its own ttmp design
   docs rather than authored fresh.
8. **Doc bugs (docs teaching nonexistent APIs)** — grep doc examples against
   the real symbol table; a documented-but-nonexistent constant
   (`fields.TypeDuration`) and an undocumented package removal
   (`keycloakauth`) each caused measured probe waves. Both directions of
   staleness are P0.

## Wave-2b lessons (RAG-ALMANACH ticket, 2026-07-19)

- **Skill content works when consumed — measured twice.** A Pi session re-read
  the glazed-help-page-authoring skill file after each compaction and produced
  checklist-conformant published docs; a Claude session executed the same
  skill's full workflow in 8 minutes after loading. The delivery problem is
  triggering/pointers, never content quality (so far).
- **Every observed technical-skill fire was user-vocabulary triggered** (user
  uttered a description substring: "glazed help entries", "protobuf ... go
  and typescript"). Zero spontaneous task-state fires anywhere. Description
  rewrites should target the phrases users actually say.
- **Handoff docs and ticket diaries neutralize compaction.** Sessions that kept
  contemporaneous ticket diaries or consumed a dense handoff doc showed ZERO
  repeat-probes across 4-80 compactions. Prioritize the post-compact re-read
  protocol only for diary-less sessions; for docmgr-disciplined work the
  existing artifacts already serve as the recovery layer.
- **Skill mirrors can be hardlinks** (~/.claude, ~/.codex, ~/.pi/agent sharing
  one inode). Check with `stat -c '%i'` before editing; write-via-rename
  breaks the link; sandboxes may mount one mirror read-only.
- **Agents author embedded help but rarely read it as consumers** — measure
  authoring (writing-help-entries invocations, doc-file writes) separately
  from consumption when interpreting embedded_help_calls.
