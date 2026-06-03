# Deliverable Checklist for Research Reports

Use this checklist before final handoff.

## Ticket setup

- `docmgr ticket create-ticket` completed
- design-doc (research report) exists
- diary doc exists
- sources/ directory has 15+ files
- index/tasks/changelog are updated

## Source collection

- 3+ Kagi web searches run with different query formulations
- 2+ Kagi Assistant deep research calls completed
- All promising web pages downloaded via defuddle
- Key PDFs (papers, manuals, specs) downloaded
- Targeted follow-up searches filled specific gaps
- Source files follow naming convention: `<source>-<topic>.md/.pdf`

## Research report quality

- Written in textbook/Norvig style (see references/writing-style.md)
- Each section starts with foundational prose before technical detail
- Original sources quoted directly with attribution
- Comparison tables used for systematic analysis
- At least one Mermaid architecture diagram included
- Implementation sketches (pseudocode or real code) for key abstractions
- References section has source tables with file paths and URLs
- Open questions section lists genuine unknowns
- Target 50–80 KB for a substantial research topic

## Obsidian vault article

- The vault article is at `Research/YYYY/MM/DD/` (not `Projects/`)
- The vault article is committed and pushed to the vault repository
- The vault article contains the FULL research report (or a slightly adapted version), not a terse summary
- The vault article has proper YAML frontmatter (title, aliases, tags, status, type, created, repo)
- If the vault article must be shorter, cut by removing entire sections, not by making every section shallow
- The vault article links to the ttmp sources/ directory for the full source collection

## Diary

- Follows the `diary` skill format
- Each research step recorded with: what was done, why, what worked, what didn't work, what was tricky
- Commands and errors recorded verbatim
- Diary updated after each major step (not just at the end)

## Bookkeeping

- Key files related via `docmgr doc relate` with absolute paths
- Changelog updated with meaningful entries
- Tasks reflect completion state
- Vocabulary warnings resolved via `docmgr vocab add`

## Validation

- `docmgr doctor --ticket <TICKET-ID> --stale-after 30` passes cleanly
- Vocabulary warnings resolved or intentionally accepted

## reMarkable delivery

- `remarquee status` OK
- Dry-run bundle upload completed
- Real bundle upload completed
- Remote listing verified

## Final response

- Include ticket path
- Include doc paths and sizes
- Include source count
- Include validation status
- Include upload destination
- Include open questions or residual risks
