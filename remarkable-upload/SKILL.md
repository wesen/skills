---
name: remarkable-upload
description: Upload Markdown and source files to a reMarkable device as PDFs using the remarquee CLI (rmapi-backed). Use when the user asks to upload/send/export docs/examples to reMarkable, bundle multiple files into one PDF with a ToC, choose an /ai/YYYY/MM/DD destination, avoid or force overwrites, or troubleshoot pandoc/xelatex/rmapi auth.
---

# Remarkable Upload

## Delivery policy owner

This specialist skill owns upload mechanics, authentication and success evidence. Research orchestrators delegate here rather than duplicating commands. Explicit user or higher-priority requirements override these defaults.

- A normal successful upload needs no routine status/account preflight or post-upload listing. Retain its `OK: uploaded` result and destination; this proves cloud delivery, not physical device synchronization.
- Run dry-run or independent listing when explicitly required, when an ambiguous result needs investigation, or when inspecting existing state is necessary to prevent overwrite. Dry-run describes the command; it does not render a PDF.
- Never use `--force` without authorization to replace the existing document and lose its annotations. Inspect or choose a new name when overwrite risk is unresolved.
- Let built-in 401/403 reauthentication finish. If it fails, one explicit `--reauth` attempt is reasonable; persistent auth failure is a blocker, not an invitation to loop.
- Use the reference below normally; inspect installed help when flags or behavior demonstrably differ. Do not repeatedly reload unchanged help out of habit.

## Optional subagent finalization

Once the main agent has finished the substantive Markdown, prefer handing routine finalization to a smaller-model subagent when delegation is available and permitted. Use Luna (`gpt-5.6-luna`) when offered, or a comparable available model; otherwise finalize locally without blocking delivery. Keep research, substantive writing, and ambiguous decisions with the main agent. This handoff keeps routine tool output out of the main conversation context.

Give the subagent a bounded task with minimal context rather than the full research conversation:

- Exact input paths and bundle order, document name, remote destination, and requested rendering/verification settings.
- This skill's path and applicable repository instructions; the subagent must read them itself.
- Permitted edit paths, ticket/diary paths if applicable, and existing upload/commit authority. Delegation does not authorize overwrites, dependency installation, commits, or other mutations beyond the user's request.
- Known constraints or unresolved delivery issues. Freeze the handed-off documents while the subagent owns finalization; do not edit or upload the same artifacts concurrently.

The subagent handles scoped formatting, local link checks, PDF generation and required visual inspection, upload, and authorized delivery bookkeeping. Mechanical formatting/rendering repairs are in scope; substantive content changes, uncertain corrections, new authority, and unresolved failures come back to the main agent. Use the diary/docmgr skills when ticket bookkeeping is requested, and commit only when explicitly authorized and assigned.

Apply the delivery policy above unchanged: no routine extra cloud preflight/listing, no unauthorized `--force`, and bounded authentication recovery. Validate the final rendered artifact after any repair that changes its appearance; a dry run is not rendering. Preserve meaningful failure diagnostics in the assigned diary or evidence location rather than flooding the main context with logs.

Return one compact receipt:

```text
Inputs and final artifact:
Changes made:
Validation performed and limitations:
Upload result and destination (retain OK: uploaded):
Diary/evidence paths and commit, if assigned:
Blockers or decisions needed:
```

The main agent reviews the receipt, resolves any escalations, and reports the outcome to the user without repeating successful tool work. Cloud delivery is not physical device synchronization.

## Typical workflow

**Normal upload:**
```bash
remarquee upload bundle <path...> --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2 --non-interactive 2>&1
```

A clear successful result is sufficient by default. Perform any explicitly required independent verification before declaring delivery complete.

**If upload fails with auth error despite auto-retry** (the `NOTE: auth expired` message appears but the retry also fails):
```bash
remarquee upload bundle <path...> --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2 --reauth --non-interactive 2>&1
```

This is rare — the auto-retry handles normal token expiry. Only use `--reauth` manually if the auto-retry also fails.

**If you need to check what's already on the device (e.g. to decide --force):**
```bash
remarquee cloud ls /ai/YYYY/MM/DD/<folder> --long --non-interactive 2>&1
```

Use this for needed state inspection or explicitly required verification, not as an automatic extra step.

## Command reference

### Upload commands

| Command | When to use | Key flags |
|---|---|---|
| `remarquee upload bundle` | Multiple .md files → one PDF with ToC | `--name`, `--remote-dir`, `--toc-depth`, `--force`, `--date`, `--non-interactive`, `--reauth`, `--dry-run` |
| `remarquee upload md` | Single or multiple .md files → separate PDFs | `--name`, `--remote-dir`, `--force`, `--date`, `--non-interactive`, `--reauth`, `--dry-run`, `--flatten` |
| `remarquee upload src` | Source code files → syntax-highlighted PDFs | `--name`, `--remote-dir`, `--force`, `--date`, `--non-interactive`, `--reauth`, `--dry-run`, `--bundle`, `--include-ext` |

### Common flags

- `--name "<title>"` — Document name (use simple names: no special chars, no colons, no parens). The PDF filename is auto-sanitized.
- `--remote-dir "/ai/YYYY/MM/DD/<folder>"` — Full remote path override
- `--date YYYY/MM/DD` — Sets date portion of remote path (default: today)
- `--force` — Overwrite existing document (WARNING: deletes existing + annotations)
- `--non-interactive` — Required for agent sessions (don't prompt for codes)
- `--reauth` — Force re-authentication when tokens are stale
- `--dry-run` — Preview what would happen without running pandoc or uploading
- `--toc-depth N` — ToC depth for bundle (default: 1)

### Cloud commands

| Command | When to use | Key flags |
|---|---|---|
| `remarquee cloud ls <path>` | List files on device | `--long`, `--non-interactive` |
| `remarquee cloud account` | Check auth status | `--non-interactive`, `--reauth` |
| `remarquee cloud get <path>` | Download a document | `--out-dir`, `--non-interactive` |
| `remarquee cloud search <query>` | Search by name | `--match name`, `--limit`, `--compact`, `--non-interactive` |
| `remarquee cloud rm <path>` | Delete a document | `--non-interactive` |

## Destination conventions

- Default remote directory: `/ai/YYYY/MM/DD/`
- Ticket-aware: `/ai/YYYY/MM/DD/<TICKET-ID>/`
- Always use `--non-interactive` in agent sessions

## Name sanitization

The CLI automatically sanitizes document names for upload:
- Spaces → underscores in PDF filenames
- Special characters that break rmapi are stripped

So you can use `--name "GOJA-053 FS Module Guide"` and the CLI will handle it.

## Common issues

- **Pandoc "Unknown alias" errors**: Usually caused by malformed code block syntax. Test with `pandoc <file>.md -o /tmp/test.pdf --pdf-engine=xelatex` to isolate.
- **Nested code blocks in markdown**: Use explicit language tags like ` ```markdown ` and ` ```json `. Do NOT use sed to replace all ` ``` ` markers.
- **401 Unauthorized during upload**: Wait for built-in retry first; if it fails, apply the bounded reauth policy above.
- **400 Bad Request during upload**: Usually a filename issue — use `--name` with a simple name (alphanumeric + spaces + dashes only).
