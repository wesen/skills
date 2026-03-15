---
name: obsidian-project-description
description: Create or update an Obsidian project-description note in Manuel's vault at /home/manuel/code/wesen/obsidian-vault when the user wants a repo, project, or ticket summarized as a durable project note. Use when the user mentions the Obsidian vault, asks to add a project description, wants a note modeled after an existing Projects/PROJ note such as PROJ - ZK Tool, or asks to include metadata such as the project date, repo directory, status, tags, and current purpose.
---

# Obsidian Project Description

## Overview

Use this skill to turn a local project or repository into a readable Obsidian project note in Manuel's vault at `/home/manuel/code/wesen/obsidian-vault`. The default target is the vault's `Projects/YYYY/MM/DD/` structure, and the default style reference is `/home/manuel/code/wesen/obsidian-vault/Projects/2026/03/15/PROJ - ZK Tool.md`.

The note should follow that pattern closely:

- YAML frontmatter first,
- short opening paragraph,
- summary callout,
- stable explanatory sections,
- concrete repo paths and code locations,
- prose-first writing with compact bullets where useful.

## Workflow

### 1. Use the vault's default location and naming convention

Default assumptions for this user's vault:

- Vault root: `/home/manuel/code/wesen/obsidian-vault`
- Project notes section: `/home/manuel/code/wesen/obsidian-vault/Projects`
- Default folder layout: `Projects/YYYY/MM/DD/`
- Default filename pattern: `PROJ - <Project Name> - <Subtitle>.md`
- Default style exemplar: `/home/manuel/code/wesen/obsidian-vault/Projects/2026/03/15/PROJ - ZK Tool.md`

Rules:

- If the user gives an example note, read it first and match its tone, frontmatter shape, section style, and level of detail.
- If the user gives an exact destination path, use it exactly.
- If no destination is given, place the note in today's `Projects/YYYY/MM/DD/` folder unless the user explicitly wants a different location.
- If the repo directory itself encodes a project date, use that date in the note body; folder placement still follows the user's request, or today's date by default.
- Prefer a `PROJ - ...` name unless the user clearly wants a different naming scheme.

### 2. Gather concrete project facts from the repo

Collect enough evidence to describe the project accurately:

- repo date from the directory name when present,
- absolute repo directory,
- main subdirectories and prototypes,
- what problem the project is trying to solve,
- what is implemented today,
- what the likely direction is if that is visible from local docs or code.

Prefer local sources first:

- `README*` files,
- ticket docs in `ttmp/`,
- top-level source directories,
- tests that reveal semantics,
- any example note the user provided.

### 3. Write the note as a project description, not a changelog

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
   - `## Current user-facing commands` or equivalent, when relevant
   - `## Important project docs`
   - `## Open questions`
   - `## Near-term next steps`
   - `## Project working rule`

Do not force every section if the repo does not justify it, but prefer this shape over inventing a new structure.

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
- `type: project`
- `created: <YYYY-MM-DD>`
- `repo: <absolute path>`

If the repo directory encodes a date like `2026-03-14--query-treesitter`, prefer that project date for `created` unless the user explicitly wants today's date.

For tags:

- always include `project`,
- add 2-5 concrete tags derived from the repo topic, language, or tool domain,
- keep them short and descriptive.

### 5. Keep the note continuation-friendly

- Mention the main repo path directly.
- Mention the main directories or files that define the project.
- If there is a major ticket or design doc in the repo, mention it as current research output.
- Avoid stale task-level detail unless the user asked for a worklog.
- Include a short "current status" section that separates what exists from what is still incomplete.
- Include "open questions" and "near-term next steps" when the project is clearly still evolving.

## Writing Rules

Use these rules strictly:

- Match the `PROJ - ZK Tool` note structure by default unless the user asks for a different style.
- Match the user's existing vault style if an example note is given.
- Do not invent architecture details that are not supported by local files.
- Prefer absolute paths when mentioning repo directories outside wikilinks.
- Use Obsidian wikilinks only for notes inside the vault; use plain text paths for local repo directories.
- When creating a new project note in this vault, default to `/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/`.
- When choosing a filename from scratch, default to `PROJ - <Project Name> - <Subtitle>.md`.
- Prefer YAML frontmatter over ad hoc metadata bullets in the body.
- Use callouts sparingly but do include a `> [!summary]` callout when the project has 2-3 clear identities or themes.
- Keep the note human-readable first. It should feel like durable project documentation, not an AI summary dump.

## Common Requests This Skill Should Handle

- "Create a project note for this repo in my Obsidian vault."
- "Model it after this existing `Projects/PROJ - ...` note."
- "Copy the style of `PROJ - ZK Tool`."
- "Include the project date and directory."
- "Put it in `/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/`."
- "Use my `PROJ - ...` naming convention."
- "Move today's project notes into a dated `YYYY/MM/DD` folder."
- "Update the existing project note to reflect the current design direction."
