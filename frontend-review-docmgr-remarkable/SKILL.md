---
name: frontend-review-docmgr-remarkable
description: Perform deep frontend architecture and code-quality assessments that result in long-form ticket documentation and reMarkable delivery. Use when asked to audit frontend subsystems, map current state, identify duplicated/deprecated/problematic code, propose reorganizations or performance improvements, maintain an investigation diary, and publish the final report to a docmgr ticket plus reMarkable.
---

# Frontend Review Docmgr Remarkable

## Overview

Execute a repeatable end-to-end review workflow:

1. Investigate the frontend codebase with concrete evidence.
2. Produce a long-form assessment in a docmgr ticket.
3. Maintain a detailed investigation diary.
4. Relate important code files to docs.
5. Upload the final document bundle to reMarkable.

Use this skill for review/assessment deliverables, not for implementing product features.

## Core Workflow

### 1) Align scope and deliverables

Capture explicit constraints before deep analysis:

- ticket behavior: create new ticket or continue existing
- required depth/length (for example 5+ pages current-state section)
- required sections (subsystem breakdown, proposals, pseudocode, diagrams)
- delivery targets: ticket docs, diary, reMarkable upload

If scope is ambiguous, ask one short clarifying question before investigating.

### 2) Initialize or locate ticket workspace

Prefer docmgr commands:

```bash
docmgr status --summary-only
docmgr ticket create-ticket --ticket <TICKET-ID> --title "<title>" --topics frontend,architecture,storybook,debugging
```

Add/locate docs:

```bash
docmgr doc add --ticket <TICKET-ID> --doc-type design-doc --title "Frontend Current State and Subsystem Cleanup Assessment"
docmgr doc add --ticket <TICKET-ID> --doc-type reference --title "Diary"
```

### 3) Gather evidence first

Use fast discovery and anchor every major claim to files:

- repo topology and scripts
- storybook structure and ownership
- app boot/store architecture
- state management and high-frequency event paths
- subsystem hotspots (windowing/chat/runtime/theme)
- duplication/deprecation/problematic code signals

Preferred command patterns:

```bash
rg --files apps packages
rg -n "pattern" apps packages
wc -l $(rg --files ...)
```

Avoid speculative statements not backed by concrete file evidence.

### 4) Analyze by subsystem

For each subsystem, include:

- current design and flow
- concrete problem list
- why it matters (correctness/perf/maintainability)
- proposal options and tradeoffs
- phased implementation suggestions

Target subsystems usually include:

- workspace/build/storybook
- shell/windowing
- chat/timeline/event pipeline
- runtime/plugin host
- state management/selectors/diagnostics
- CSS/theming/design-system readiness

Load `references/subsystem-checklist.md` when needed.

### 5) Write the assessment document

Write one primary design-doc with:

- executive summary
- long current-state section
- subsystem deep dives with proposals
- pseudocode and diagrams for key redesigns
- cleanup roadmap and docs-to-write plan
- open questions
- explicit file references

Use `references/assessment-template.md` as skeleton when helpful.

### 6) Maintain the diary

Document the investigation process with:

- user prompt context
- commands run
- findings and failed attempts
- tricky points and reviewer watchouts
- validation and delivery steps

Keep the diary chronological and continuation-friendly.

### 7) Update ticket bookkeeping

Keep ticket artifacts consistent:

```bash
docmgr doc relate --doc <doc-path> --file-note "/abs/path:reason"
docmgr changelog update --ticket <TICKET-ID> --entry "..." --file-note "/abs/path:reason"
```

Update tasks/checklists to reflect completion state.

### 8) Upload to reMarkable

Use safe upload workflow:

```bash
remarquee status
remarquee cloud account --non-interactive
remarquee upload bundle --dry-run <doc1.md> <doc2.md> --name "<bundle>" --remote-dir "/ai/YYYY/MM/DD/<TICKET-ID>" --toc-depth 2
remarquee upload bundle <doc1.md> <doc2.md> --name "<bundle>" --remote-dir "/ai/YYYY/MM/DD/<TICKET-ID>" --toc-depth 2
remarquee cloud ls /ai/YYYY/MM/DD/<TICKET-ID> --long --non-interactive
```

Default to bundle upload so the reader gets one PDF with ToC.

### 9) Validate before final handoff

Run doc hygiene check:

```bash
docmgr doctor --ticket <TICKET-ID> --stale-after 30
```

Confirm:

- assessment doc exists and is complete
- diary exists and is complete
- tasks/changelog updated
- upload verified with remote listing

## Quality Bar

Meet all criteria before closing:

- Evidence-based: every major claim anchored to specific files.
- Thorough: covers architecture, behavior, risk, and actionable proposals.
- Practical: gives phased plan and concrete implementation direction.
- Reusable: readable by a developer unfamiliar with the codebase.
- Delivered: stored in ticket and uploaded to reMarkable.

## Failure Handling

If blocked:

- ticket path missing: locate repo root and `ttmp` path first
- remarquee auth failure: run `remarquee cloud account` interactively
- upload collision: choose a unique `--name` or user-approved overwrite strategy
- unknown vocabulary warnings: add needed terms via `docmgr vocab add`

When any step cannot be completed, report what succeeded, exact failure output, and remaining manual action.

## References

- `references/assessment-template.md`
- `references/subsystem-checklist.md`
