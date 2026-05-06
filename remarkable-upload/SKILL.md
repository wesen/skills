---
name: remarkable-upload
description: Upload Markdown and source files to a reMarkable device as PDFs using the remarquee CLI (rmapi-backed). Use when the user asks to upload/send/export docs/examples to reMarkable, bundle multiple files into one PDF with a ToC, choose an /ai/YYYY/MM/DD destination, avoid or force overwrites, or troubleshoot pandoc/xelatex/rmapi auth.
---

# Remarkable Upload

## Preconditions

1. Confirm `remarquee` exists:
   - `remarquee status`
2. Confirm PDF tooling if needed:
   - `pandoc`, `xelatex`
3. Confirm cloud auth if needed:
   - `remarquee cloud account --non-interactive` (or run without `--non-interactive` to complete one-time code)

## Workflow (safe default, recommended)

1. Choose inputs (use absolute paths when possible).
2. Dry-run first:
   - Single/many markdown: `remarquee upload md --dry-run <path...>`
   - Bundled markdown (one PDF + ToC): `remarquee upload bundle --dry-run <path...>`
   - Source code PDFs: `remarquee upload src --dry-run <path...>`
3. Upload (no overwrite):
   - Same commands without `--dry-run`
4. Overwrite only if explicitly requested (WARNING: deletes existing document + annotations):
   - add `--force`

## Bundling multiple files (preferred)

- Bundle multiple markdown inputs into a single PDF with a clickable ToC:
  - `remarquee upload bundle <path...> --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2`
- Bundle multiple source files into a single syntax-highlighted PDF:
  - `remarquee upload src <path...> --bundle --include-ext .go --name "<doc name>" --remote-dir "/ai/YYYY/MM/DD/<folder>" --toc-depth 2`

Tip: if you care about ToC order and titles, copy/rename files into a temp folder with numeric prefixes, then pass that directory to `bundle`.

## Ticket-aware uploads (recommended)

- Put uploads under a stable ticket folder (avoids collisions):
  - Remote: `/ai/YYYY/MM/DD/<TICKET-ID>/`
  - Use `--date YYYY/MM/DD` (or `--remote-dir ...`) explicitly.
- Verify results:
  - `remarquee cloud ls /ai/YYYY/MM/DD/<TICKET-ID> --long --non-interactive`

## Common issues

- **Nested code blocks in markdown**: If you have markdown containing code blocks (e.g., a markdown example inside a markdown doc), use explicit language tags like ` ```markdown ` and ` ```json `. Do NOT use sed to replace all ` ``` ` markers - it will break nested code blocks.
- **Pandoc "Unknown alias" errors**: Usually caused by malformed code block syntax. Test with `pandoc <file>.md -o /tmp/test.pdf --pdf-engine=xelatex` to isolate.

## Reference

- Full guide + troubleshooting: `references/remarkable.md`
