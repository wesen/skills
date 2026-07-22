---
name: transcript-doc-friction-analysis
description: Analyze coding-agent session transcripts (Claude Code, Codex, Pi) with go-minitrace to find where documentation, skills, or agent instructions caused friction — and turn the evidence into concrete doc/skill fixes. Use when asked to analyze why an agent session struggled, audit skill usage or doc consumption, find what documentation is missing or ignored, measure token cost of knowledge acquisition, mine a build session for AGENT.md guards, or re-measure doc-consumption after documentation changes. Also load BEFORE hand-writing SQL/JS against minitrace archives for any docs/skills-improvement question — this skill ships tested docmetrics query commands (doc-consumption, source-probes, api-calls, failure-triage, episodes) that answer the common questions in one call each. Triggers on - "analyze the transcript", "doc friction", "why did the agent grep the source", "improve our skills/docs based on sessions", "which skills fired", "session post-mortem", "documentation optimization".
---

# Transcript analysis for documentation & skill improvement

## Purpose

Turn coding-agent session transcripts into evidence-backed improvements to
documentation, skills, and agent instructions (AGENT.md/CLAUDE.md). This skill
builds on `go-minitrace-transcript-analysis` (which covers discovery,
conversion, attribution, and evidence standards — load it too for those
stages) and adds:

1. a **tested query-command repository** (`query-commands/docmetrics/`) that
   answers the recurring doc-friction questions in one call each;
2. an **interpretation playbook** (what the numbers mean, healthy thresholds,
   known adapter traps);
3. a **deep-dive method catalog** (the seven subagent analyses proven on
   ticket GOGO-DOCS-OPTIMIZE-2026-07-19) with the fix types each produces.

## Workflow

### 1. Scope the question and convert the sessions

Define what improvement you're hunting (missing API references? skill
descriptions that don't trigger? recurring shell friction? token cost?).
Then discover and convert per the go-minitrace-transcript-analysis skill:

**Codex sidecar trap (check BEFORE converting):** Codex writes separate
approval-assessor rollouts that share the work session's cwd and can be large
(re-quoted parent history). They convert to turns-only sessions with
`tool_call_count=0`. Classify every Codex source first:

```bash
head -c 200000 "$f" | grep -c "whose request action you are assessing"
```

non-zero → sidecar, exclude (or analyze separately as approval telemetry).

```bash
go-minitrace discover claude-code --source-dir ~/.claude/projects \
  --cwd-contains <repo> --output json          # shortlist
go-minitrace convert claude-code --source-list sources.txt --output-dir ./archives
```

Never modify native session files. Save the source list as an artifact.
Preflight `--help` on every go-minitrace subcommand you use — the CLI evolves
faster than skill prose.

### 2. Run the docmetrics profile (the standard first pass)

```bash
QR=~/.claude/skills/transcript-doc-friction-analysis/query-commands
G='./archives/active/*/*.minitrace.json'
for v in doc-consumption source-probes api-calls failure-triage episodes; do
  go-minitrace query commands --query-repository $QR docmetrics $v \
    --archive-glob "$G" --output json > results/$v.json
done
```

All verbs are multi-session: pass several `--archive-glob` flags to compare
sessions in one run, and cross-framework: claude-code, pi, and codex archives
work together (codex shell commands are extracted from JS-embedded
`arguments_json`; pi lowercase tool names are handled).

| Verb | Answers | Key outputs |
|---|---|---|
| `doc-consumption` | How did the session consume docs? | Per-session: Skill loads (with names), **Bash-sideloaded skill reads**, **Read-tool skill-file reads** (Pi's channel), codex exec md-read commands, embedded `<app> help <topic>` invocations (prose-false-positive-guarded), pkg/doc reads, md reads (ticket vs other) |
| `source-probes` | Where did it grep dependency source instead of reading docs? | Probe waves (turn ranges, target repos, symbols sought), repeat-probes (same symbol grepped in 2+ waves = re-derivation, e.g. post-compact) |
| `api-calls` | What did it really cost? | **Deduplicated** per-API-call token totals (naive turn-row sums are ~2-2.5x inflated), inflation factor, context-size trajectory, detected compaction events |
| `failure-triage` | What actually went wrong? | Root-cause categories in precedence order: self-kill (pkill matching the harness shell's own cmdline), zsh-expansion, read-before-edit, nul-byte, cwd-drift (tracks persistent-shell cd state), missing-file, timeout, go-compile/test, partial-success |
| `episodes` | How did work flow? | Episode slices at real user instructions (filters tool-result carriers, skill injections, compaction summaries), tool mix, failures, wall/idle minutes |

### 3. Interpret

Read `references/interpretation.md` before quoting any number — it documents
the adapter traps (NULL `content_type`, `subagent_count` counting TaskCreate,
token inflation, codex failure-blindness, per-framework metric semantics) and
healthy-session thresholds. Core reading of the profile:

- **skill_sideloads > 0 or source-probe waves on repos with skills/help
  topics** → discoverability failure: content exists, delivery fails.
- **repeat_probes non-empty** → knowledge evaporated (usually /compact);
  check `api-calls` compaction_events for the timing.
- **embedded_help_calls = 0 while source probes > 0** → the embedded help
  system is invisible; add pointers, don't just write more topics.
- **failure clusters** → each category maps to a one-line AGENT.md guard
  (see references/interpretation.md §Guards). But verify before quoting:
  in one measured Pi session, 84/84 flagged failures were conventions
  (conformance runners, TDD loops), not friction.
- **Metric semantics differ per framework.** Codex can ONLY sideload skills
  (its `~/.codex/skills` mirror — sideloads are its normal channel, not a
  bypass); Pi loads skill files via its `read` tool; only Claude has a Skill
  tool. Codex `success` is always 1 (failure-blind); compare failures only
  within a framework.
- **Fix delivery where all frameworks look**: repo-adjacent files (AGENT.md,
  in-repo docs) are the only channel consumed by claude, pi, AND codex.
  A single user sentence pointing at `<app> help` produced complete,
  permanent adoption in a measured session — pointer lines are the cheapest
  effective fix.

### 4. Deep-dive with subagents (for substantial investigations)

The seven proven methods, each producing a specific fix type — fan out as
parallel subagents, each writing a report doc; synthesize afterward:

1. **Episode deep-read** → doc demand-map ranked by cost (feed it `episodes` output).
2. **Symbol-demand extraction** → per-skill missing-API-signature tables (feed it `source-probes` output; agent diffs symbols against skills/help topics and checks for **stale/renamed APIs** — a skill teaching a removed API is the worst bug class).
3. **Skill-trigger audit** (3-lens judge: literal / intent / skeptic; missed = 2 of 3) → description rewrites in *product language* with *file-path task-state triggers* ("before writing any file under pkg/cmds/..."), because prompts like "build it." carry zero matching vocabulary.
4. **Doc-duplication mining** → upstreaming worklist: classify in-session ticket docs into project-specific / generic-duplicated (discoverability proof) / generic-missing (extraction candidates with destination + slug).
5. **Adversarial failure verification** → verified guard list; skeptic per failure with default "not real friction"; expect the classifier to be wrong sometimes (verify before quoting).
6. **Cross-session comparison** → systematicity verdict (run the same docmetrics profile over 3-5 sessions; one-off findings don't justify structural fixes).
7. **Token hotspot analysis** → docs-gap-to-tokens ranking (must use `api-calls` deduped numbers; state the cost model assumptions explicitly).

### 5. Deliver fixes, then re-measure

Deliverables are always *changes*, ranked P0/P1/P2:

- **P0**: fix stale skill instructions; add "read these first" doc pointers to
  skills; skill-description rewrites; AGENT.md guard lines.
- **P1**: compact API-signature references (~4-6k tokens each — resident-size
  matters because ~80% of session cost is cache reads).
- **P2**: upstream generic content from ticket docs into help topics;
  post-compact protocols; process conventions.

Close the loop: after fixes land, re-run `docmetrics doc-consumption` on the
next few sessions. Success = embedded-help/doc reads > 0 when library APIs are
touched, source probes reserved for verification not first contact, zero greps
for renamed symbols, skill loads at implementation start, no repeat-probes
after compaction.

## Non-negotiables

- Raw grep and every docmetrics heuristic is **candidate selection, not
  proof** — verify claims in the transcript and against external state (git)
  before reporting. Keep an explicit corrections ledger when later evidence
  overturns earlier claims.
- Never modify native session stores.
- Save discovery output, source lists, and verb outputs as committed
  artifacts (docmgr ticket workspace when available).
- Keep a contemporaneous diary if the user asks for one — and load the diary
  skill at that moment, not retroactively.

## Extending the query repository

The verbs live in `query-commands/docmetrics/*.js`. Authoring rules learned
the hard way (see also `go-minitrace help js-api-reference`):

- Handler pattern: `mt.db().RuntimeArchives().QueryCommandDefaults().Build()`,
  query, `db.close()` in `finally`; return plain JSON.
- **Every top-level `function name(...)` declaration is registered as a CLI
  verb** — write helpers as `const name = function(...)` or the file becomes a
  polluted command group and the single-verb path collapse breaks.
- Filter nullable text columns with `COALESCE(col,'')` — `NULL != 'x'` is
  falsy in SQLite and silently drops rows.
- `sqlite_master` is sandbox-blocked; use `db.tables()` / `db.schema()`.
- Test every new verb against a real archive before trusting it, single- and
  multi-session.
