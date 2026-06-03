---
name: obsidian-vault-research-report
description: Research a technology topic deeply using web search, Kagi Assistant, defuddle, and PDF collection, then write a comprehensive textbook-style research report in a docmgr ticket workspace and copy the full report to the Obsidian vault. Use when a user asks to research a topic, write a research report, investigate an architecture/paradigm/system, or create a knowledge document that goes beyond a terse summary.
---

# Obsidian Vault Research Report

## Overview

Use this skill to produce comprehensive, textbook-style research reports on technology topics. The workflow produces two deliverables:

1. **A ttmp research report** — the primary, exhaustive design-doc in the docmgr ticket workspace, with all sources collected in the `sources/` directory and a detailed investigation diary.

2. **An Obsidian vault article** — the FULL research report copied (or slightly adapted) into the vault at `Research/YYYY/MM/DD/`, committed and pushed. This is NOT a terse summary — it contains the same depth, diagrams, code sketches, and source links as the ttmp report.

The key lesson from the Newton Object Soup research project: the vault article must be as detailed as the ttmp report. Terse summaries are not useful. The vault is where the user reads; the ttmp is where the research happened. The reader of the vault article should get the full picture without needing to open the ttmp.

Load these references when writing:

- `references/writing-style.md` — Norvig textbook style, anti-patterns, report-vs-article distinction
- `references/source-collection.md` — search pipeline, defuddle, PDF downloads, Kagi Assistant
- `references/report-structure.md` — recommended section order, depth guidelines, prose patterns
- `references/deliverable-checklist.md` — pre-handoff validation checklist

## Workflow

### 1) Initialize ticket workspace

```bash
docmgr status --summary-only
docmgr ticket create-ticket --ticket <TICKET-ID> --title "<title>" --topics <topic1,topic2,...>
docmgr doc add --ticket <TICKET-ID> --doc-type design-doc --title "<Research Report Title>"
docmgr doc add --ticket <TICKET-ID> --doc-type reference --title "Investigation Diary"
```

Verify these exist:
1. `index.md`
2. `tasks.md`
3. `changelog.md`
4. research report doc
5. diary doc
6. `sources/` directory

Add tasks for the workflow:
```bash
docmgr task add --ticket <TICKET-ID> --text "Web search and gather primary sources"
docmgr task add --ticket <TICKET-ID> --text "Deep research via Kagi Assistant"
docmgr task add --ticket <TICKET-ID> --text "Download key webpages to sources/ via defuddle"
docmgr task add --ticket <TICKET-ID> --text "Write the research report"
docmgr task add --ticket <TICKET-ID> --text "Copy full report to Obsidian vault"
docmgr task add --ticket <TICKET-ID> --text "Validate and upload to reMarkable"
```

### 2) Gather sources using the search pipeline

Follow the source collection pipeline in `references/source-collection.md`:

**Round 1: Breadth** — Run 3–5 parallel Kagi web searches with different query formulations. Identify Wikipedia articles, primary source documents, community discussions, and modern implementations.

**Round 2: Download** — Use `defuddle parse` for every promising web result. Use `curl` for PDFs. Target 15–25 source files in the `sources/` directory.

**Round 3: Deep synthesis** — Run 2–3 Kagi Assistant calls with `--web-search-mode on`, each focusing on a different aspect of the topic (architecture, UX, modern comparisons, historical context). These provide synthesized analysis with source citations.

**Round 4: Targeted follow-up** — Run additional searches for specific gaps identified during reading. Look for original quotes, insider accounts, specific technical mechanisms, and modern comparisons.

### 3) Read all sources before writing

Read every downloaded source file before writing a single paragraph of the report. The report must be grounded in the actual source material, not in vague recollections of search snippets.

Prioritize reading:
1. Primary source PDFs (papers, manuals, specifications)
2. Key web articles (the ones that are most detailed or most authoritative)
3. Kagi Assistant outputs (for synthesized connections)
4. Community discussions (for insider perspectives and corrections)

### 4) Write the research report in textbook style

Follow the report structure in `references/report-structure.md` and the writing style in `references/writing-style.md`.

Critical writing rules:

1. **Start each section with foundational prose.** Explain why a design exists, what problem it solves, what insight the reader should carry — before showing code, tables, or diagrams.

2. **Quote original sources directly.** When a source says something important in its own words, quote it verbatim with attribution. Ground the report in evidence.

3. **Use comparison tables.** When comparing systems, approaches, or historical platforms, use tables with named columns. Tables do work that prose cannot.

4. **Include architecture diagrams.** Every non-trivial system deserves at least one Mermaid diagram. Use `flowchart TD` for data flow, `flowchart LR` for pipelines.

5. **Provide implementation sketches.** Include pseudocode or real code sketches for the key abstractions in a modern language (TypeScript, Go, Python).

6. **Link to sources explicitly.** Every source mentioned should appear in the References section with a description, file path (if downloaded), and URL (if available).

7. **Target 50–80 KB.** A substantial research report should be 50–80 KB. Reports shorter than 30 KB are almost certainly too terse. Do not be afraid of length.

8. **No analogies.** Explain technical systems directly in their own terms. No kitchens, no traffic cops, no factories.

9. **No hedged non-claims.** Be direct. "This approach offers flexibility and extensibility" not "This approach could potentially offer certain advantages in terms of flexibility."

### 5) Maintain a chronological investigation diary

Use the `diary` skill format. Record each research step with:
- What was done (commands, searches, downloads)
- Why (motivation for this step)
- What worked (useful findings)
- What didn't work (failed searches, unavailable sources, tool errors)
- What was tricky (challenges and how they were approached)
- What warrants a second pair of eyes (claims that need validation)
- What should be done in the future (open follow-ups)

Update the diary after each major step, not just at the end.

### 6) Copy the full report to the Obsidian vault

**This is the critical step that distinguishes this skill from generic research workflows.**

The vault article must contain the FULL research report, not a terse summary. The user has explicitly stated that terse summaries are not useful.

```bash
mkdir -p /home/manuel/code/wesen/go-go-golems/go-go-parc/Research/YYYY/MM/DD
cp ttmp/.../design-doc/01-<report>.md \
   "/home/manuel/code/wesen/go-go-golems/go-go-parc/Research/YYYY/MM/DD/<Article Title>.md"
```

Then add YAML frontmatter to the vault copy:

```yaml
---
title: "<Report Title>"
aliases:
  - <short name>
tags:
  - article
  - <topic tags>
status: active
type: article
created: YYYY-MM-DD
repo: /abs/path/to/project/dir
---
```

If the vault article must be shorter than the full report, cut by **removing entire sections** (e.g., the diary stays in ttmp only), not by making every section shallow. A shallow section is worse than a missing section.

### 7) Commit and push the vault

```bash
cd /home/manuel/code/wesen/go-go-golems/go-go-parc
git add "Research/YYYY/MM/DD/<Article Title>.md"
git commit -m "Research report: <descriptive message>"
git push
```

### 8) Update ticket bookkeeping

```bash
docmgr doc relate --doc <doc-path> --file-note "/abs/path:reason"
docmgr changelog update --ticket <TICKET-ID> --entry "..." --file-note "/abs/path:reason"
docmgr task check --ticket <TICKET-ID> --id <task-ids>
```

### 9) Validate and upload to reMarkable

```bash
docmgr doctor --ticket <TICKET-ID> --stale-after 30
# Fix vocabulary warnings if needed:
docmgr vocab add --category topics --slug <slug> --description "..."

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

### 10) Final handoff

Report:
1. ticket id/path
2. research report path and size
3. source file count
4. Obsidian vault article path (committed and pushed)
5. reMarkable upload path and verification
6. validation result
7. open questions

## Guardrails

1. **The vault article is the full report, not a summary.** This is the most important guardrail. Terse summaries are explicitly rejected by the user.

2. **Write in textbook style.** Foundational prose before technical detail. Concrete over abstract. No analogies. No hedged non-claims.

3. **Quote original sources directly.** Do not paraphrase important statements vaguely. Quote them verbatim with attribution.

4. **Collect sources before writing.** Do not write the report from memory of search snippets. Read the downloaded sources first.

5. **Keep the diary current.** Update after each major step, not just at the end.

6. **Use comparison tables, not prose comparisons.** Tables are scannable and force specificity.

7. **Include implementation sketches.** The report should teach, not just describe. Code sketches and pseudocode make the abstractions concrete.

8. **Target 50–80 KB for substantial topics.** Do not be afraid of length. A report that is too terse is useless.
