---
name: obsidian-vault-writing
description: Append-only Obsidian vault writing workflow for Manuel's vault at /home/manuel/code/wesen/obsidian-vault. Create new project notes, article/playbook-style knowledge notes, or new dated follow-up notes without overwriting historical notes unless the user explicitly asks. Use when the user mentions the Obsidian vault, asks to add a project description, wants a note modeled after an existing Projects/PROJ note such as PROJ - ZK Tool, wants a reusable ARTICLE/playbook/knowledge entry, or asks to include metadata such as the project date, repo directory, status, tags, and current purpose.
---

# Obsidian Vault Writing

## Overview

Use this skill to create durable Obsidian notes in Manuel's vault at `/home/manuel/code/wesen/obsidian-vault`. The most common outputs are:

- **project notes** in the `PROJ - ...` style
- **article / playbook / knowledge notes** in the `ARTICLE - ...` style
- **dated follow-up notes** that preserve earlier historical notes rather than overwriting them

The default target is still the vault's `Projects/YYYY/MM/DD/` structure. The default style references are:

- project-note exemplar: `/home/manuel/code/wesen/obsidian-vault/Projects/2026/03/15/PROJ - ZK Tool.md`
- knowledge/article exemplar: `/home/manuel/code/wesen/obsidian-vault/Projects/2026/04/02/ARTICLE - Playbook - Self-Contained Go Wasm and JavaScript Browser Applications.md`

This skill should operate in append-only mode by default: preserve existing historical notes and create a new dated note instead of overwriting or deleting an older one unless the user explicitly asks for replacement.

The resulting note should usually have:

- YAML frontmatter first,
- a short opening paragraph,
- a summary callout when useful,
- stable explanatory sections,
- concrete repo paths and code locations where relevant,
- prose-first writing with compact bullets where useful.

The important decision is not just *how to write the note*, but *what kind of note it is*. In this vault, reusable technical knowledge is often better stored as an `ARTICLE - ...` note than as a `PROJ - ...` note.
## Workflow

### 1. Use the vault's default location and naming convention

Default assumptions for this user's vault:

- Vault root: `/home/manuel/code/wesen/obsidian-vault`
- Project/knowledge notes section: `/home/manuel/code/wesen/obsidian-vault/Projects`
- Default folder layout: `Projects/YYYY/MM/DD/`
- Default project filename pattern: `PROJ - <Project Name> - <Subtitle>.md`
- Default knowledge/article filename pattern: `ARTICLE - <Topic> - <Subtitle>.md`
- Default project-note exemplar: `/home/manuel/code/wesen/obsidian-vault/Projects/2026/03/15/PROJ - ZK Tool.md`
- Default article/playbook exemplar: `/home/manuel/code/wesen/obsidian-vault/Projects/2026/04/02/ARTICLE - Playbook - Self-Contained Go Wasm and JavaScript Browser Applications.md`

Rules:

- If the user gives an example note, read it first and match its tone, frontmatter shape, section style, and level of detail.
- If the user gives an exact destination path, use it exactly.
- If no destination is given, place the note in today's `Projects/YYYY/MM/DD/` folder unless the user explicitly wants a different location.
- If a related historical note already exists, keep it and create a new dated note rather than overwriting it by default.
- If the repo directory itself encodes a project date, use that date in the note body; folder placement still follows the user's request, or today's date by default.
- Choose the note type deliberately:
  - use `PROJ - ...` when the note is primarily about a specific repo/project and its current shape, direction, implementation, and status
  - use `ARTICLE - ...` when the note is primarily durable reusable knowledge, a playbook, a pattern, a failure-mode writeup, or a technical concept that should outlive a single project
- When in doubt, ask: "Will a future reader come to this note mainly to understand *this project*, or mainly to learn a *reusable pattern*?"
- Prefer a `PROJ - ...` or `ARTICLE - ...` name unless the user clearly wants a different naming scheme.
### 2. Gather concrete facts from the repo or topic source

Collect enough evidence to describe the note accurately.

For project notes, gather:

- repo date from the directory name when present,
- absolute repo directory,
- main subdirectories and prototypes,
- what problem the project is trying to solve,
- what is implemented today,
- what the likely direction is if that is visible from local docs or code.

For knowledge/article notes, gather:

- the concrete triggering project or incident, if any,
- the reusable pattern being explained,
- the class of failure modes involved,
- the stable engineering rules or heuristics worth preserving,
- the code paths or artifacts that illustrate the pattern well,
- how the lesson generalizes beyond the immediate repo.

Prefer local sources first:

- `README*` files,
- ticket docs in `ttmp/`,
- top-level source directories,
- tests that reveal semantics,
- any example note the user provided,
- existing vault notes that establish the user's style for this kind of writing.
### 3. Write the right kind of durable note, not a changelog

#### Project-note shape (`PROJ - ...`)

Default note shape, based on `PROJ - ZK Tool`:

1. YAML frontmatter with at least:
   - `title`
   - `aliases`
   - `tags`
   - `status`
   - `type: project`
   - `created`
   - `repo`
2. `# <Project Name>` heading
3. Short opening paragraph describing the project
4. `> [!summary]` callout with a short 1-3 item summary when useful
5. Stable sections such as:
   - `## Why this project exists`
   - `## Current project status`
   - `## Project shape`
   - `## Architecture`
   - `## Implementation details` — prose, pseudocode, and diagrams explaining how the system works technically
   - `## Current user-facing commands` or equivalent, when relevant
   - `## Important project docs`
   - `## Open questions`
   - `## Near-term next steps`
   - `## Project working rule`

Do not force every section if the repo does not justify it, but prefer this shape over inventing a new structure.

#### Knowledge/article-note shape (`ARTICLE - ...`)

Use this when the note should preserve reusable engineering knowledge rather than describe one repo's status.

A good default structure is:

1. YAML frontmatter with at least:
   - `title`
   - `aliases`
   - `tags`
   - `status`
   - `type: article`
   - `created`
   - `repo` when there is a concrete source repo
2. `# <Title>` heading
3. Short opening paragraph explaining what knowledge this note preserves
4. `> [!summary]` callout with the 2-4 most important ideas
5. Stable sections such as:
   - `## Why this note exists`
   - `## When to use this pattern`
   - `## Core mental model`
   - `## Architecture` or `## Pattern shape`
   - `## Common failure modes`
   - `## Anti-patterns`
   - `## Recommended implementation sequence`
   - `## Working rules`
   - `## Pseudocode` or `## Examples`
   - `## Related notes`

The note should read like a durable engineering article or internal playbook. It should teach a future reader how to think about the pattern, not just record that something happened once.

### Implementation details section

Every substantial project note or knowledge/article note should include at least one section with substantive technical content. In project notes this is usually `## Implementation details`. In article notes it may instead be `## Core mental model`, `## Pattern shape`, `## Architecture`, or `## Common failure modes`, but the goal is the same: a written-out explanation aimed at someone who needs to understand, modify, reproduce, or safely reuse the idea.

The implementation details section should contain:

- **Prose explanations** of key algorithms, data flows, and design decisions. Explain *why* the code works the way it does, not just *what* it does. Cover the non-obvious parts — the things that would trip up someone reading the code for the first time.

- **Pseudocode or real code snippets** for the most important logic paths. Show the actual algorithm structure, the SQL query patterns, the key function signatures, or the shell commands that drive the system. Keep snippets short and focused on the essential logic.

- **Mermaid diagrams** showing data flow, system architecture, or component relationships. Use ` ```mermaid ` code blocks — Obsidian renders these natively. Prefer `flowchart TD` or `graph LR` for data flow, `graph TD` with subgraphs for architecture layouts, and `flowchart LR` for transformation pipelines. Use `style` directives for color highlights on key nodes (e.g. databases, outputs, error paths). Examples:
  - pipeline diagrams showing stage-to-stage data flow
  - architecture diagrams with subgraphs for component boundaries
  - data structure diagrams showing schema relationships
  - UI layout diagrams showing spatial arrangement of interface elements

- **Tricky details and failure modes** that are not obvious from the code. Cover encoding issues, edge cases, workarounds for tool limitations, and "why not the obvious approach" explanations. These are often the most valuable parts of the documentation because they capture knowledge that would otherwise be lost.

The implementation section should read like a technical article or a detailed design document — someone should be able to understand how to rebuild the system from this section alone, without reading the code. Aim for the level of detail found in a good blog post about a weekend project: enough to teach, not so much that it becomes a code dump.

Good models from the vault:
- `PROJ - Scopedjs` uses detailed concept explanations with pseudocode for the eval pipeline
- `PROJ - Smailnail` uses phased implementation narratives with schema tables and architecture diagrams
- `PROJ - reMarkable Cleanup` uses data-flow diagrams, algorithm pseudocode, and failure-mode analysis

Prefer prose paragraphs over shallow bullet spam. Use bullets when listing concrete project parts, commands, open questions, or next steps.

The note should answer questions like:

- What is this project about?
- What problem is it trying to solve?
- What are the main moving parts?
- What is the simplest mental model for it?
- What is the likely future direction?

### 4. Include explicit metadata in frontmatter, not as loose body lines

The ZK Tool pattern is frontmatter-heavy. Default to that.

When creating or updating a note, prefer these fields:

- `title: <display title>`
- `aliases:`
- `tags:`
- `status: active` unless there is evidence otherwise
- `type: project` for project notes, `type: article` for durable knowledge/playbook notes
- `created: <YYYY-MM-DD>`
- `repo: <absolute path>` when there is a concrete source repo

If the repo directory encodes a date like `2026-03-14--query-treesitter`, prefer that project date for `created` unless the user explicitly wants today's date.

For tags:

- for project notes, always include `project`
- for knowledge/article notes, prefer `article`, `playbook`, or another accurate durable-knowledge tag when appropriate
- add 2-5 concrete tags derived from the repo topic, language, tool domain, or concept
- keep them short and descriptive.
### 5. Keep the note continuation-friendly

- Mention the main repo path directly when there is one.
- Mention the main directories or files that define the project or illustrate the pattern.
- If there is a major ticket or design doc in the repo, mention it as current research output or as the source incident.
- Avoid stale task-level detail unless the user asked for a worklog.
- Include a short `current status` section for project notes when the implementation is evolving.
- Include `open questions` and `near-term next steps` when the system or pattern is still evolving.
- For knowledge/article notes, make sure the note generalizes beyond the triggering incident rather than reading like a postmortem dump.
## Writing Rules

Use these rules strictly:

- Match the `PROJ - ZK Tool` structure for project notes unless the user asks for a different style.
- Match the existing `ARTICLE - ...` / playbook style for reusable knowledge notes when that is the better fit.
- Match the user's existing vault style if an example note is given.
- Do not invent architecture details that are not supported by local files.
- Prefer absolute paths when mentioning repo directories outside wikilinks.
- Use Obsidian wikilinks only for notes inside the vault; use plain text paths for local repo directories.
- When creating a new note in this vault, default to `/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/` unless the user asks otherwise.
- When choosing a filename from scratch, default to `PROJ - <Project Name> - <Subtitle>.md` for project notes and `ARTICLE - <Topic> - <Subtitle>.md` for reusable knowledge notes.
- Prefer YAML frontmatter over ad hoc metadata bullets in the body.
- Use callouts sparingly but do include a `> [!summary]` callout when the note has 2-4 clear identities or themes.
- Keep the note human-readable first. It should feel like durable project documentation or durable engineering knowledge, not an AI summary dump.
- Treat vault-note work as append-only by default: do not delete or overwrite an existing note unless the user explicitly asks for that.
## Common Requests This Skill Should Handle

- "Create a project note for this repo in my Obsidian vault."
- "Model it after this existing `Projects/PROJ - ...` note."
- "Copy the style of `PROJ - ZK Tool`."
- "Write a reusable knowledge base entry about this engineering pattern."
- "Create an article/playbook note in my Obsidian vault about this bug class."
- "Store this as durable engineering knowledge, not just a project report."
- "Include the project date and directory."
- "Put it in `/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/`."
- "Use my `PROJ - ...` or `ARTICLE - ...` naming convention."
- "Move today's project notes into a dated `YYYY/MM/DD` folder."
- "Update the existing project note to reflect the current design direction."
- "Figure out where in the vault this kind of knowledge should live."
