---
name: remarkable-upload
description: Convert Markdown (.md) to PDF via pandoc/xelatex and upload to a reMarkable device using rmapi and the local remarkable_upload.py script. Use when the user asks to upload/send/export Markdown or ticket docs to reMarkable, mirror ticket folder structure on-device, do a safe dry-run before uploading, avoid or force overwrites, or troubleshoot rmapi/pandoc/xelatex/TeX issues.
---

# Remarkable Upload

## Preconditions

1. Confirm the uploader exists:
   - `python3 /home/manuel/.local/bin/remarkable_upload.py --help`
2. Confirm dependencies if needed:
   - `rmapi`, `pandoc`, `xelatex`

## Workflow (safe default)

1. Choose the markdown file(s) (use absolute paths).
2. Dry-run to confirm the remote path + commands:
   - `python3 /home/manuel/.local/bin/remarkable_upload.py --dry-run /abs/path/to/doc.md`
3. Upload (no overwrite):
   - `python3 /home/manuel/.local/bin/remarkable_upload.py /abs/path/to/doc.md`
4. Overwrite only if explicitly requested:
   - add `--force`

## Ticket-aware uploads (recommended)

- Use `--ticket-dir ...` to infer the `ai/YYYY/MM/DD/` destination date from `ttmp/YYYY/MM/DD/TICKET--slug`.
- Prefer `--mirror-ticket-structure` to avoid collisions under `ai/YYYY/MM/DD/`.
- See `references/remarkable.md` for flag details and full examples (`--remote-ticket-root`, `--date`, multi-file uploads).

## Reference

- Full guide + troubleshooting: `references/remarkable.md`
