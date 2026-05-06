---
name: pr-deep-dive-report
description: Create a deep-dive project report for a GitHub Pull Request by reading implementation diaries, git history, and source code, then writing a narrative report to the Obsidian vault. Use when asked to "write a report for PR #N", "what was done in this PR", "deep dive this PR", or "compare the work since main in PR #N".
---

# PR Deep-Dive Report

## Overview

This skill creates a narrative, implementation-focused project report for a GitHub Pull Request. Unlike a changelog or a diff summary, this report tells the story of *what was built, why, how the architecture evolved, what failed and why, and what the important technical decisions were*. It draws from implementation diaries, git history, source code, and architecture documentation to produce a durable note in the Obsidian vault.

## When to Use

Use this skill when:

- a user asks to "compare the work since main in PR #N"
- a user asks to "write a report for PR #N"
- a user asks to "deep dive this PR"
- a user asks to "document what was done in this PR"
- a user asks to "write a project report in our obsidian vault" and provides a PR URL

## What This Produces

A `PROJ - <Project> - <PR Title>` note in `/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/` with:

- YAML frontmatter (title, aliases, tags, status, type, created, repo)
- A narrative opening that frames the problem and why the work matters
- A `[!summary]` callout with the 2-4 most important themes
- Prose sections explaining *why* decisions were made, not just *what* was built
- Real code snippets that capture essential logic
- Architecture diagrams where they illuminate the design
- Failure modes, recovery stories, and the lessons learned
- Concrete file paths pointing to the real implementation
- Open questions and near-term next steps

The report should feel like reading a good technical blog post about a weekend project — enough to teach, not so much that it becomes a code dump.

## Workflow

### 1. Detect PR State (merged vs open) and Fetch

PRs can be **open** (not yet merged) or **already merged**. Handle both:

**For open PRs:**

```bash
git fetch origin pull/<N>/head:<BRANCH>
git log --oneline origin/main..<BRANCH>   # list PR commits
git diff --stat origin/main..<BRANCH>    # diff summary
```

**For merged PRs** (PR branch may not exist locally):

```bash
git fetch origin
# Find the merge commit on main:
git log --oneline origin/main | grep -i "Merge pull request #<N>"
# e.g. git log --oneline origin/main shows: c2782d7 Merge pull request #6 from wesen/task/minitrace-js
# Then use merge-commit^..pr-head:
MERGE_COMMIT=$(git log --oneline origin/main | grep -i "Merge pull request #<N>" | head -1 | awk '{print $1}')
git log --oneline ${MERGE_COMMIT}^..<MERGE_COMMIT>
# Or if you know the PR head commit:
git log --oneline <merge-commit>..<pr-head-commit>
```

The key insight: for merged PRs, `origin/main` *contains* the merge commit. You need `merge-commit^..<pr-branch-head>` to get the commits that were added by the PR.

### 2. Find All Ticket Workspaces

A large PR can have 5-10 ticket workspaces under `ttmp/`. Don't guess paths — enumerate them:

```bash
# List all ttmp directories in the PR diff:
git diff <RANGE> --name-only -- "ttmp/**" | grep -o 'ttmp/[^/]*/[^/]*' | sort -u

# Or if the PR branch exists:
git ls-tree <BRANCH> ttmp/ | awk '{print $4}'   # list top-level ticket dirs
```

### 3. Find and Read All Diaries

Diaries are not always at `reference/01-diary.md`. Find them by pattern:

```bash
# Find all markdown files with "diary" in the path within the PR diff:
git diff <RANGE> --name-only -- "ttmp/**" | grep -i diary

# Examples of actual diary names encountered:
# ttmp/.../reference/01-diary.md
# ttmp/.../reference/01-investigation-diary.md
# ttmp/.../reference/02-diary.md
# ttmp/.../diary.md
```

Read all of them. Use `git show <BRANCH>:<PATH>` for PR-only files, or read directly from the working tree for merged PRs:

```bash
# For merged PRs, read from current branch (PR commits are now in main):
git show <BRANCH>:<PATH>        # if PR branch exists
git show origin/main:<PATH>       # if merged, read from main
# For files that were added in the PR (not modified):
git ls-tree <BRANCH> --name-only ttmp/ | while read ticket; do
  git ls-tree <BRANCH> --name-only "ttmp/$ticket" | grep -i diary
done
```

Diary files are often very large (500-1000+ lines). Read the full content, not just the first 200 lines. Use offset/limit for pagination if needed.

Diaries contain the actual narrative: what was attempted, what failed, what was learned, what was tricky, what warranted a second pair of eyes, and exact commands used for validation. **These are far more valuable than commit messages.**

### 4. Read the Architecture and Design Docs

Look for design documents, playbooks, and architecture guides:

```bash
# List new/modified doc files:
git diff <RANGE> --name-only -- "**/*.md" | grep -v "ttmp/"
git diff <RANGE> --name-only -- "pkg/doc/**"
git diff <RANGE> --name-only -- "docs/**"
git diff <RANGE> --name-only -- "ttmp/**/design-doc/**"
git diff <RANGE> --name-only -- "ttmp/**/playbook/**"
```

Priority docs:
- `pkg/doc/*.md` — durable help pages and playbooks
- `README.md` — updated project overview
- `ttmp/**/design-doc/*.md` — design documents
- `ttmp/**/playbook/*.md` — implementation playbooks
- `ttmp/**/reference/*.md` — investigation and research docs

### 5. Read the Source Code

Read the actual implementation files. For large PRs, prioritize by:

1. **New files** — files that exist only in the PR are the main deliverable
2. **Large diffs** — files with hundreds of lines changed are the core implementation
3. **Core domain logic** — types, schemas, repository patterns, runtime dispatch

```bash
# Get a sorted list of changed Go files by size:
git diff <RANGE> --stat -- "*.go" | sort -k2 -n | tail -20

# Read a new file from the PR branch:
git show <BRANCH>:<PATH>

# Read a modified file's diff:
git diff <RANGE> -- <PATH> | head -200   # first 200 lines of diff
```

For each changed file, ask: does this file implement something, or does it test/connect something that exists elsewhere? Focus on implementations.

### 6. Build a Mental Model

Before writing, build a clear picture of:

- **What problem does this PR solve?** What was the gap or bug?
- **What was the architecture before?** What constraints existed?
- **What changed and why?** What were the key design decisions?
- **What are the key interfaces?** How do the pieces connect?
- **Where does state live?** What data flows through the system?
- **What are the execution paths?** What happens when you run the command or call the API?
- **What failed during implementation?** What was recovered from?

### 7. Identify the Themes

Every substantial PR has 2-4 intertwined identities. Identify them early:

- A new feature or subsystem
- A refactoring or architectural improvement
- A bug fix or recovery
- A tooling or workflow improvement
- A documentation or research deliverable

These themes become the section headings of the report.

### 8. Write the Report

Structure the report around the actual narrative, not around the diff:

1. **Opening** — Frame the problem and why the work matters. What was the starting state? What was missing or broken?

2. **Architecture Decisions** — The non-obvious choices that shaped the implementation. Not just "we chose X" but "we considered A and B, and X was better because..."

3. **Implementation Sections** — Group related changes into coherent sections. Each section should explain the *why*, show *representative code*, and capture *failure modes and recovery*.

4. **Key Technical Details** — Use real code snippets to show the essential logic. Show 5-30 lines that capture the core behavior. Avoid dumping entire files.

5. **What Was Tricky** — Document the hard parts, the failed attempts, and the lessons learned. These are the most valuable parts of any technical documentation.

6. **Open Questions and Next Steps** — What remains to be done? What should a future contributor know?

### 9. Output Location

Write the report to:
`/home/manuel/code/wesen/obsidian-vault/Projects/YYYY/MM/DD/PROJ - <Project> - <PR Title>.md`

Use today's date unless the PR's work has a clear temporal context (e.g., the PR is named after a specific feature date).

## What to Avoid

- **Changelogs** — Don't list files changed or commits made. Focus on the narrative.
- **AI summaries** — Don't write generic "this PR adds feature X" summaries. Show the actual code and reasoning.
- **Incomplete understanding** — Don't write confidently about parts you haven't read. If you can't understand a section, say so and focus on what you do understand.
- **Surface-level reporting** — Don't just describe what each file does. Explain the relationships, the design decisions, and the edge cases.
- **Assuming diary paths** — Diary files are not always at `reference/01-diary.md`. Find them by pattern matching.

## Key Git Patterns

### Reading files from a PR branch

```bash
# Files that only exist in the PR:
git show <BRANCH>:<PATH>

# Files modified by the PR (merged or not):
git show origin/main:<PATH>      # before (for merged PRs)
git show <BRANCH>:<PATH>        # after

# The diff for a specific file:
git diff <RANGE> -- <PATH>
```

### Finding the PR range

```bash
# Open PR:
RANGE="origin/main..<BRANCH>"

# Merged PR — find the merge commit:
MERGE=$(git log --oneline origin/main | grep -i "Merge pull request #<N>" | head -1 | awk '{print $1}')
# The PR head is the second parent of the merge commit:
PR_HEAD=$(git show $MERGE --format=%P | awk '{print $2}')
RANGE="${MERGE}^..${PR_HEAD}"
```

### Enumerating ticket workspaces

```bash
# From the diff (works for both merged and open PRs):
git diff <RANGE> --name-only -- "ttmp/**" | \
  grep -o 'ttmp/[^/]*/' | sort -u

# From the PR branch (if it exists locally):
git ls-tree <BRANCH> ttmp/ | awk '{print $4}' | grep -v '\.$'

# From main (for merged PRs):
git ls-tree origin/main ttmp/ | awk '{print $4}' | grep -v '\.$'
```

## Style Guide

- Write in first person plural ("we") or passive voice, not "the AI"
- Use prose paragraphs for explanations, bullets for lists
- Show real code snippets, not pseudocode (unless the real code is too large)
- Use Mermaid diagrams for architecture and data flow
- Include callouts for key themes and important caveats
- Keep sections focused — if a section is longer than ~400 words, consider splitting it
