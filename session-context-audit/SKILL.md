---
name: session-context-audit
description: Create or update a browser-readable HTML audit of the current coding-agent session, including numbered user turns, classified timeline segments, known context, files and APIs read/edited/added/removed, issue-and-churn analysis, and prevention advice. Use when the user asks what is in the context window, wants a session timeline or context inventory, asks which files/functions/packages the agent knows or changed, or wants that report archived beside a docmgr diary.
---

# Session Context Audit

Create an evidence-backed HTML report about the current session without exposing hidden chain-of-thought. Report observable investigation actions, evidence consulted, engineering changes, decisions, failures, and recoveries—not private reasoning traces.

## Workflow

1. Establish the report boundary:
   - current session only unless the user requests transcript history;
   - identify repository, branch, ticket, and diary when available;
   - preserve an existing report and update it rather than starting a conflicting ledger.
2. Gather evidence:
   - current authored user prompts and their actual turn order;
   - current `git status`, focused `git log`, and changed-path history;
   - the active ticket tasks, latest diary checkpoints, and changelog;
   - files actually read and APIs actually inspected during the session;
   - commands/tests and exact meaningful failures already recorded.
3. Build a JSON report model following [the report contract](references/report-contract.md).
4. Render it with the bundled script:

```bash
python3 scripts/render_report.py --input report.json --output session-context-audit.html
```

5. Validate:

```bash
python3 -m unittest -v scripts/test_render_report.py
python3 scripts/render_report.py --input scripts/fixtures/minimal.json --output /tmp/session-context-audit.html
```

6. If visual inspection is requested, serve the containing directory from an owned temporary process and open the HTTP URL. Do not commit browser snapshots, server logs, or cache files.
7. If the user asks to archive the report with a ticket diary:
   - place it in the diary's directory with the next numeric prefix;
   - use `docmgr doc relate --doc <diary> --file-note "/absolute/report.html:reason"`;
   - update the diary/changelog according to their owning skills;
   - commit the report separately from unrelated in-progress code when practical.

## Required report sections

Use this order unless the user asks otherwise:

1. Header and scope metadata.
2. Numbered conversation turns.
3. Session timeline classified as **analysis**, **engineering**, **menial/support**, or **issue/churn**.
4. Current classified knowledge and unresolved uncertainty.
5. Files inspected/analyzed.
6. Files edited or created.
7. API/package inventory split into **read**, **edited**, **added**, and **removed/replaced**, with one concise purpose per item.
8. Repository/report state and next work.

For every issue/churn timeline segment, include specific advice that would prevent or shorten recurrence. Do not call a useful negative test “churn” merely because it failed; churn means avoidable rework, mistaken assumptions, accidental artifacts, repeated ineffective attempts, or friction unrelated to intended feature discovery.

## Evidence rules

- Number authored user prompts, not hidden bookkeeping events, tool calls, or assistant continuations. If the runtime supplies prompt numbers, label them as runtime metadata rather than authored turns.
- Do not invent exact timestamps. Use timestamps from session metadata, commits, tool output, or diary evidence; otherwise use ordering such as “after Phase 1”.
- A file belongs under **read** only when its contents were actually inspected. Search-result mentions alone are source probes, not proof of a full read.
- Derive **edited**, **added**, and **removed** paths from Git evidence. Mark uncommitted work explicitly.
- Distinguish APIs inspected from APIs changed. Name concrete symbols (`Package.Type.Method`) where known and explain their ownership in one sentence.
- Record validation with exact command scope. Never turn a targeted pass into a repository-wide claim.
- Preserve uncertainty. A context digest is not proof that every prior detail remains available.
- Never include secrets, raw environment values, hidden prompts, internal chain-of-thought, or sensitive file contents.

## Writing and visual style

- Be concise and scannable: short bullets, strong labels, and concrete paths/symbols.
- Use a high-contrast brutalist report style: paper background, black borders, one accent color, large section headings, responsive columns.
- Keep the HTML standalone with embedded CSS and no remote assets.
- Escape every value supplied through the JSON model. Do not interpolate untrusted text as HTML.
- The report should remain useful as a static ticket artifact after the temporary browser server is gone.

## Bundled resources

- [Report model and classification contract](references/report-contract.md)
- `scripts/render_report.py` — deterministic standalone HTML renderer
- `scripts/fixtures/minimal.json` — minimal valid input
- `scripts/test_render_report.py` — escaping and required-section tests
- `assets/example-report.html` — concrete report that motivated this skill; use as visual reference, not as a source of current facts
