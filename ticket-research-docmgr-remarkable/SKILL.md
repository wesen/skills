---
name: ticket-research-docmgr-remarkable
description: Create exhaustive ticket-based research deliverables using docmgr and reMarkable upload. Use when a user asks to create a new ticket, analyze a codebase deeply, keep a chronological investigation diary, write long-form design/reference docs, relate files and changelog/tasks, and publish the final document bundle to reMarkable.
---

# Ticket Research Docmgr Remarkable

## Overview

Use this skill to run an end-to-end research pipeline for new tasks: ticket creation, evidence-first investigation, detailed documentation (with strong writing quality), docmgr bookkeeping, and reMarkable delivery.

Load these references when writing:

- `references/writing-style.md`
- `references/deliverable-checklist.md`

## Workflow

## 1) Initialize ticket workspace

Create or locate the ticket first.

```bash
docmgr status --summary-only
docmgr ticket create-ticket --ticket <TICKET-ID> --title "<title>" --topics <topic1,topic2,...>
docmgr doc add --ticket <TICKET-ID> --doc-type design-doc --title "<Primary analysis title>"
docmgr doc add --ticket <TICKET-ID> --doc-type reference --title "Investigation diary"
```

Then inspect generated files and ensure these are present:

1. `index.md`
2. `tasks.md`
3. `changelog.md`
4. primary design doc
5. diary doc

## 2) Gather evidence before writing conclusions

Use fast repository discovery and anchor every major claim to concrete files.

Preferred command patterns:

```bash
rg --files <dirs>
rg -n "<pattern>" <dirs> -S
wc -l <key files>
nl -ba <file> | sed -n '<range>'
```

Investigation requirements:

1. Map architecture boundaries (think about things like entrypoints, runtime behavior, state, extensability... map to appropriate idomatic concepts).
2. Identify current behavior, gaps, risks, and constraints relevant to the requested feature.
3. Capture line-anchored evidence for key claims.
4. Inspect existing docs/stories/tests for commonly used patterns, style used and concrete examples.

Never write speculative recommendations without file-backed evidence.

## 3) Write the primary analysis document

Write one comprehensive design doc with:

1. Executive summary.
2. Problem statement and scope.
3. Current-state architecture (evidence-based).
4. Gap analysis against requested outcomes.
5. Proposed solution with API references and pseudocode.
6. Decision records for major architecture/API choices.
7. Phased implementation plan (file-level guidance).
8. Testing and validation strategy.
9. Risks, alternatives, and open questions.
10. References list of key files.

Writing requirements:

1. Optimize for onboarding unfamiliar engineers.
2. Be explicit, structured, and concrete.
3. Explain tradeoffs, not just chosen direction.
4. Include compact decision records when a design chooses between viable alternatives.
5. Include pseudocode and minimal API sketches where useful.
6. Keep tone factual and implementation-focused.

Decision records should state context, options considered, decision, rationale, consequences, and status (`proposed`, `accepted`, or `superseded`). Use them for major representation, API, runtime, security, generated-code, integration, or compatibility choices.

See `references/writing-style.md`.

## 4) Maintain a chronological investigation diary (via `diary` skill)

Do not redefine a diary schema in this skill. Use the `diary` skill directly for diary authoring and updates.

Requirements:

1. Follow the standard `diary` skill format (including sections like `What worked`, `What didn't work`, `What was tricky to build`, and `Code review instructions`).
2. Keep entries chronological and continuation-friendly.
3. Include concrete commands/errors exactly as they occurred.
4. Ensure diary updates are reflected in ticket bookkeeping (relations/changelog/tasks).

## 5) Update ticket bookkeeping

Relate key files and keep status artifacts consistent.

```bash
docmgr doc relate --doc <doc-path> --file-note "/abs/path:reason"
docmgr changelog update --ticket <TICKET-ID> --entry "..." --file-note "/abs/path:reason"
```

Update tasks checklist to reflect completion status.

Use absolute paths for all `--file-note` entries.

## 6) Validate doc quality and vocabulary

Run doctor before upload.

```bash
docmgr doctor --ticket <TICKET-ID> --stale-after 30
```

If vocabulary warnings appear, add missing slugs and rerun.

```bash
docmgr vocab add --category topics --slug <slug> --description "..."
```

Proceed only after doctor passes cleanly.

## 7) Upload to reMarkable

Use bundled upload with dry-run first.

```bash
remarquee status
remarquee cloud account --non-interactive
remarquee upload bundle --dry-run <doc1.md> <doc2.md> ... \
  --name "<bundle name>" \
  --remote-dir "/ai/YYYY/MM/DD/<TICKET-ID>" \
  --toc-depth 2
remarquee upload bundle <doc1.md> <doc2.md> ... \
  --name "<bundle name>" \
  --remote-dir "/ai/YYYY/MM/DD/<TICKET-ID>" \
  --toc-depth 2
remarquee cloud ls /ai/YYYY/MM/DD/<TICKET-ID> --long --non-interactive
```

Prefer bundle upload so the receiver gets one PDF with ToC.

## 8) Final handoff

Report:

1. ticket id/path,
2. docs created/updated,
3. validation result (`docmgr doctor`),
4. reMarkable upload path and verification listing,
5. unresolved risks/open questions.

## Guardrails

1. Keep analysis and recommendations evidence-based.
2. Keep docs exhaustive but navigable (sectioned, scannable).
3. Keep wording precise; avoid vague advice.
4. Preserve existing repository changes unrelated to the task.
5. Never skip dry-run for upload unless user explicitly asks.
