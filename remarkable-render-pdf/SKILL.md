---
name: remarkable-render-pdf
description: Download a document from a reMarkable device/cloud via remarquee (rmapi-backed) and render it to an annotated PDF via `remarquee rmdoc render-v6`/`render-legacy`, optionally extracting the last N pages into a smaller PDF. Use when asked to export/render/download a reMarkable notebook/journal/document to PDF (full doc or page subset).
---

# reMarkable Render to PDF

## Preconditions

- Confirm `remarquee` works: `remarquee status`
- Confirm cloud auth: `remarquee cloud account --non-interactive` (run without `--non-interactive` once if you need to complete login)
- For page extraction: `qpdf` and `pdfinfo`

## Workflow

### 1) Locate the document on reMarkable cloud

Search by name (often easiest):

```bash
remarquee cloud search "journal #001" --match name --limit 50 --compact --non-interactive
```

If you already know the folder, list it:

```bash
remarquee cloud ls /Journals --long --non-interactive
```

Pick the remote path you want (example):

```text
/Journals/#001 - 2025-12 - 2026-01-19
```

### 2) Download as `.rmdoc`

```bash
outdir="$HOME/remarkable_exports/$(date +%F)"
mkdir -p "$outdir"
remarquee cloud get "/Journals/#001 - 2025-12 - 2026-01-19" --out-dir "$outdir" --non-interactive
```

### 3) Inspect to choose renderer (V6 vs legacy)

```bash
remarquee rmdoc inspect "$outdir/#001 - 2025-12 - 2026-01-19.rmdoc"
```

- If `schema=cPages`, render with `render-v6`
- Otherwise try `render-legacy`

### 4) Render to PDF (annotated)

```bash
remarquee rmdoc render-v6 \
  "$outdir/#001 - 2025-12 - 2026-01-19.rmdoc" \
  --out "$outdir/#001 - 2025-12 - 2026-01-19-annotated.pdf" \
  --force
```

Legacy fallback:

```bash
remarquee rmdoc render-legacy "$outdir/#001 - 2025-12 - 2026-01-19.rmdoc" --out "$outdir/#001 - 2025-12 - 2026-01-19-annotated.pdf" --force
```

### 5) Extract the last N pages (optional)

Example: last 2 pages

```bash
pdf="$outdir/#001 - 2025-12 - 2026-01-19-annotated.pdf"
pages="$(pdfinfo "$pdf" | rg '^Pages:' | awk '{print $2}')"
start=$((pages-2+1))
qpdf --empty --pages "$pdf" "$start-$pages" -- "$outdir/#001 - 2025-12 - 2026-01-19-last-2-pages.pdf"
```

## Scripted workflow

Use `scripts/render_remote_to_pdf.py` when you want a single deterministic command (download → render → optionally extract):

```bash
python3 scripts/render_remote_to_pdf.py \
  --remote-path "/Journals/#001 - 2025-12 - 2026-01-19" \
  --out-dir "$HOME/remarkable_exports/$(date +%F)" \
  --extract-last 2 \
  --force
```

It prints the generated paths on success.

If cloud tokens are missing and you need to authenticate, add `--interactive`.
