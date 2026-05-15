---
name: full-blown-tech-research-design
description: Create exhaustive technology research and design packages for broad engineering topics. Use when the user asks to create a docmgr ticket for full-blown technology research/design, investigate unfamiliar libraries/protocols/frameworks, compare architecture options, gather source material, write intern-ready implementation guides, keep a diary, add small experiments, and optionally upload the final report to reMarkable.
---

# Full-Blown Technology Research and Design

## Purpose

Use this skill when the user asks for a deep technology research/design package, such as:

- “Create a docmgr ticket to do full-blown technology research and design for …”
- “Research this stack and write a design/implementation guide for a new intern.”
- “Investigate these libraries/protocols, save sources, run experiments, and produce an architecture plan.”
- “Do what you did for the Automerge/Keyhive Discord bot design.”

This skill is about **technology understanding and system design**, not merely docmgr mechanics. The deliverable should teach an engineer how the technology works, what to build, why the architecture is shaped that way, how to validate it, and what risks remain.

When the user explicitly asks for docmgr/reMarkable delivery, use the local `docmgr`, `diary`, `defuddle`, and `remarkable-upload` skills as supporting workflows, but keep this skill’s research/design standard as the main guide.

## Output Standard

The final ticket should contain:

1. A docmgr ticket workspace with clear title and topics.
2. A primary design document that is long-form, technical, and intern-ready.
3. A chronological investigation diary.
4. A `sources/` area with important web pages saved as Markdown.
5. A `vendor/` area with relevant upstream repositories cloned when useful.
6. A `scripts/` area with small experiments, probes, or reproducible smoke tests.
7. Updated `index.md`, `tasks.md`, and `changelog.md`.
8. `docmgr doctor` passing, or a clearly documented reason if it cannot pass.
9. Optional reMarkable upload when requested.

The design document should read like an engineering textbook plus implementation RFC: prose paragraphs, diagrams, tables, API sketches, pseudocode, file references, and concrete validation commands.

## Workflow

### 1. Understand the research question

Before creating artifacts, restate the intended research/design target in your own words. Identify:

- The system to be designed.
- The technologies that must be understood.
- The likely runtime/language constraints.
- Whether the user expects implementation, research only, or a design plan.
- Whether reMarkable upload is required.

If the prompt is broad but actionable, proceed. Ask questions only when missing information would materially change the research direction.

### 2. Create or locate the docmgr ticket

Use a short ticket ID that matches the topic. Examples:

```bash
docmgr status --summary-only
docmgr ticket create-ticket \
  --ticket TECH-001 \
  --title "Technology Research and Design Title" \
  --topics topic-one,topic-two,architecture,research

docmgr doc add --ticket TECH-001 --doc-type design-doc --title "Technology Research and Design Guide"
docmgr doc add --ticket TECH-001 --doc-type reference --title "Investigation Diary"
```

Inspect the generated files before writing.

### 3. Gather evidence before writing conclusions

Use multiple evidence sources:

- Official documentation.
- API references.
- Upstream README files.
- Source code and tests.
- Example applications.
- Release notes or maturity warnings.
- Issue trackers only when they explain real constraints.

Useful commands:

```bash
surf kagi search --query "<technology> official docs architecture API"
surf kagi search --query "<technology> examples repository source"
surf kagi search --query "<technology A> <technology B> integration"
```

For web pages, save clean Markdown with Defuddle:

```bash
defuddle parse <url> --md -o ttmp/.../sources/web/NN-topic-name.md
```

For repositories, clone under the ticket:

```bash
mkdir -p ttmp/.../vendor
git clone --depth 1 <repo-url> ttmp/.../vendor/<repo-name>
```

Use line-anchored evidence for important claims:

```bash
rg -n "Repo|Client|Server|Adapter|Access|Policy|Encrypt|Sync" ttmp/.../sources ttmp/.../vendor -S
nl -ba path/to/file | sed -n '40,120p'
```

### 4. Keep source captures docmgr-friendly

Raw upstream Markdown often lacks docmgr frontmatter. To avoid `docmgr doctor` failures, choose one of these approaches:

- Prefer saving web captures under `sources/web/NN-name.md` with docmgr frontmatter added.
- Rename third-party repository Markdown to `.upstream.txt` if docmgr scans it and complains.
- Add local ignore files only if they are known to work for the repo’s docmgr configuration.

A minimal frontmatter for source captures:

```yaml
---
Title: Source Title
Ticket: TICKET-ID
Status: active
Topics:
    - research
DocType: reference
Intent: long-term
Owners: []
RelatedFiles: []
ExternalSources:
    - https://example.com/source
Summary: "Raw source capture for the research ticket."
LastUpdated: YYYY-MM-DDTHH:MM:SSZ
WhatFor: "Source evidence captured during research."
WhenToUse: "When checking original source material for the design guide."
---
```

### 5. Run small experiments

When the technology can be validated cheaply, add experiments under `scripts/`.

Experiments should be tiny, reproducible, and focused on one assumption:

- “Can two CRDT replicas merge this shape?”
- “Can the client authenticate and call this API?”
- “Can the library run in Node/browser?”
- “What does the generated schema look like?”
- “Does the sync server persist after restart?”

Each experiment should include:

- A short comment explaining the assumption.
- A `package.json`, `go.mod`, `Cargo.toml`, or similar when dependencies are needed.
- A command that can be copied into the diary and design doc.
- Expected output.

Record failed attempts exactly in the diary. Failed experiments are often the most useful evidence.

### 6. Write the primary design guide

Use this structure unless the user asks for another shape:

1. **Executive summary** — what to build, main recommendation, and maturity/risk posture.
2. **Problem statement and scope** — what is in/out of scope.
3. **Technology primer** — teach the important concepts before architecture.
4. **Current-state evidence** — what docs/source/tests prove, with file/line references.
5. **System overview** — components, responsibilities, and diagrams.
6. **Data/model design** — schemas, state boundaries, lifecycle, persistence.
7. **API design** — HTTP/RPC/CLI/library interfaces, request/response examples, types.
8. **Core flows** — step-by-step runtime flows with sequence diagrams or pseudocode.
9. **Implementation plan** — phased, file-level guidance for a new intern.
10. **Testing and validation strategy** — unit/integration/manual/smoke/security/perf tests.
11. **Risks, alternatives, and open questions** — be explicit and non-handwavy.
12. **Intern onboarding checklist** — what to read first, what to run first, where to edit first.
13. **References** — local source docs, cloned repo files, experiments, external URLs.

Writing rules:

- Explain why each component exists before saying how to implement it.
- Prefer concrete APIs, types, and pseudocode over vague recommendations.
- Use diagrams for boundaries and flows.
- Use tables for tradeoffs and component responsibilities.
- Cite local files and line ranges for major claims.
- Distinguish “observed in source/docs” from “recommended design inference.”
- Call out maturity/security warnings prominently.
- Make the document navigable for a new intern who has never seen the technology.

### 7. Maintain the investigation diary

Use the `diary` skill format. The diary must be chronological and include:

- Original user prompt.
- Commands run.
- Sources gathered.
- Repositories cloned.
- Experiments created and results.
- Exact errors and fixes.
- Decisions made and why.
- What warrants a second pair of eyes.
- Future follow-ups.

Update the diary as work proceeds, not only at the end.

### 8. Update ticket bookkeeping

Update ticket files so the ticket is useful without reading terminal history:

- `index.md`: overview, links, current status, structure.
- `tasks.md`: completed research tasks and follow-up implementation tasks.
- `changelog.md`: concise dated summary of what changed.

Relate important files:

```bash
docmgr doc relate --doc ttmp/.../design-doc/01-...md \
  --file-note "/abs/path/to/source.md:Source evidence for ..." \
  --file-note "/abs/path/to/vendor/file.ts:API reference for ..." \
  --file-note "/abs/path/to/scripts/probe.mjs:Runnable experiment validating ..."
```

Add missing vocabulary topics when `docmgr doctor` reports unknown topics:

```bash
docmgr vocab add --category topics --slug <topic> --description "Topic used by <ticket> research and design."
```

Validate:

```bash
docmgr doctor --ticket <TICKET-ID> --stale-after 30
```

Fix errors before delivery when practical.

### 9. Upload to reMarkable when requested

Use the efficient one-command upload workflow from the `remarkable-upload` skill. Do not run unnecessary status/list checks.

```bash
remarquee upload bundle \
  ttmp/.../index.md \
  ttmp/.../design-doc/01-...md \
  ttmp/.../reference/01-investigation-diary.md \
  ttmp/.../tasks.md \
  ttmp/.../changelog.md \
  --name "TICKET-ID Research Design" \
  --remote-dir "/ai/YYYY/MM/DD/TICKET-ID" \
  --toc-depth 2 \
  --non-interactive 2>&1
```

If the command prints `OK: uploaded ... -> <path>`, treat it as successful.

## Quality Bar

A successful result should answer these questions for a new intern:

- What is the system, in one paragraph?
- What must I understand about each technology before touching code?
- Which upstream files and docs prove the claims in the design?
- What should I implement first, second, and third?
- What are the exact data types and API boundaries?
- What commands validate the assumptions?
- What are the biggest risks and open questions?
- Where are all source documents and experiments stored?

## Final Handoff Format

In the final response, report:

- Ticket ID and path.
- Design doc path.
- Diary path.
- Sources/vendor/experiments created.
- Validation result.
- reMarkable upload destination if performed.
- Remaining risks/open questions.

Keep the response concise; the detailed content belongs in the ticket.
