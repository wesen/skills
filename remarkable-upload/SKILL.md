---
name: remarkable-upload
description: Upload Markdown and source files to a reMarkable device as PDFs using the remarquee CLI (rmapi-backed). Use when the user asks to upload/send/export docs/examples to reMarkable, bundle multiple files into one PDF with a ToC, choose an /ai/YYYY/MM/DD destination, avoid or force overwrites, or troubleshoot pandoc/xelatex/rmapi auth.
---

# Remarkable Upload

## IMPORTANT: Minimize tool calls

Remarquee operations are expensive in agent sessions. Follow these rules strictly:

1. **Never run `remarquee status` before uploading.** The upload command itself will fail clearly if something is wrong. Just run the upload directly.
2. **Never run `remarquee cloud ls` to verify after a successful upload.** If the upload prints `OK: uploaded <name> -> <path>`, it succeeded. Only check `cloud ls` if the upload fails AND you need to understand why.
3. **Never run `remarquee cloud account` to check auth before uploading.** Upload commands now auto-retry with reauth on 401/403 — you do NOT need to handle auth expiry manually. If you see `NOTE: auth expired, re-authenticating and retrying...` in stderr, just let it proceed.
4. **Do NOT call `remarquee upload --help` or `remarquee cloud --help`.** The command reference below has all the flags you need.

## Typical workflow (2 calls max, not 5)

**Normal upload:**
```bash
remarquee upload bundle <path...> --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2 --non-interactive 2>&1
```

That's it. One call. If it succeeds (output contains "OK: uploaded"), you're done. No verification step needed.

**If upload fails with auth error despite auto-retry** (the `NOTE: auth expired` message appears but the retry also fails):
```bash
remarquee upload bundle <path...> --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2 --reauth --non-interactive 2>&1
```

This is rare — the auto-retry handles normal token expiry. Only use `--reauth` manually if the auto-retry also fails.

**If you need to check what's already on the device (e.g. to decide --force):**
```bash
remarquee cloud ls /ai/YYYY/MM/DD/<folder> --long --non-interactive 2>&1
```

Only do this when you genuinely need to know existing state, never as a routine post-upload check.

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
- **401 Unauthorized during upload**: Re-run the same command with `--reauth --non-interactive` added.
- **400 Bad Request during upload**: Usually a filename issue — use `--name` with a simple name (alphanumeric + spaces + dashes only).
