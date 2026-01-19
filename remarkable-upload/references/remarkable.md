Upload markdown, documentation bundles, and source code bundles to a reMarkable device as PDFs.

Preferred tool:

- `remarquee` (rmapi-backed)

Legacy fallback:

- `python3 /home/manuel/.local/bin/remarkable_upload.py`

What it does:
- Converts `.md` → `.pdf` via `pandoc` + `xelatex` (DejaVu fonts)
- (bundle mode) Creates a single PDF with a clickable Table of Contents (ToC)
- (src mode) Renders source files as syntax-highlighted PDFs
- Uploads into `/ai/YYYY/MM/DD/` (optionally into a per-ticket subdirectory)
- Avoids overwriting unless you pass `--force`

## The mental model (for people new to this)

You always do the same 3 steps:

1) **Choose the inputs** you want to upload (markdown and/or source files).
2) **Dry-run** to confirm:
   - destination folder (`/ai/YYYY/MM/DD/` or `--remote-dir` override)
   - (optional) ticket subfolder (choose via `--remote-dir`, e.g. `/ai/YYYY/MM/DD/<TICKET-ID>/`)
   - PDF filename(s)
   - the exact pandoc/rmapi commands that would run
3) **Run the real upload** (and only use `--force` if you explicitly want to overwrite).

## Quick Start (remarquee)

1) Dry-run:

```bash
remarquee upload md --dry-run /abs/path/to/doc.md
```

2) Upload (no overwrite):

```bash
remarquee upload md /abs/path/to/doc.md
```

3) If it reports the PDF already exists, ask before overwriting, then:

```bash
remarquee upload md --force /abs/path/to/doc.md
```

## Bundle multiple markdown files into one PDF (ToC)

If you want a single PDF (e.g. diary + tutorial + READMEs), use `bundle`:

```bash
remarquee upload bundle --dry-run \
  --name "MO-GLAZE-001 Docs" \
  --remote-dir "/ai/2026/01/19/MO-GLAZE-001-UPDATE-DOCS" \
  --toc-depth 2 \
  /abs/path/to/01-diary.md \
  /abs/path/to/02-tutorial.md \
  /abs/path/to/03-readme.md
```

Then run without `--dry-run`.

### Tip: control ToC order + titles

If you care about ordering and ToC labels, copy/rename inputs into a temp dir like:

```
01-diary.md
02-tutorial.md
03-example-a.md
04-example-b.md
```

Then pass the directory to `bundle`.

## Bundle source files into one PDF (syntax highlighted)

```bash
remarquee upload src --dry-run \
  --bundle \
  --include-ext .go \
  --name "MO-GLAZE-001 Examples" \
  --remote-dir "/ai/2026/01/19/MO-GLAZE-001-UPDATE-DOCS" \
  --toc-depth 2 \
  /abs/path/to/examples/
```

Then run without `--dry-run`.

## Ticket-aware uploads (recommended)

Recommended remote layout:

- `/ai/YYYY/MM/DD/<TICKET-ID>/`

Example:

```bash
remarquee upload bundle --dry-run \
  --name "TICKET Docs" \
  --remote-dir "/ai/2026/01/19/MO-GLAZE-001-UPDATE-DOCS" \
  --toc-depth 2 \
  /abs/path/to/ttmp/2026/01/19/MO-GLAZE-001-UPDATE-DOCS--*/diary/01-diary.md \
  /abs/path/to/pkg/doc/tutorials/05-build-first-command.md
```

Then run the same command without `--dry-run`.

## Verify uploads

List the destination folder:

```bash
remarquee cloud ls /ai/YYYY/MM/DD/<TICKET-ID> --long
```

## Choose / override the destination folder (remarquee)

Destination is `/ai/YYYY/MM/DD/` by default.

Override explicitly:

```bash
remarquee upload md --date 2025/12/11 /abs/path/to/doc.md
```

## Troubleshooting (remarquee)

- **Auth / one-time code**:
  - Run without `--non-interactive` once to complete auth, then use `--non-interactive` in scripts/CI.
- **Noisy debug logs**:
  - Use `--log-level warn` (global flag), e.g. `remarquee --log-level warn upload bundle ...`
- **PDF already exists**:
  - Default is skip; only use `--force` if you explicitly want to overwrite (it deletes annotations too).
- **pandoc/xelatex missing**:
  - Install pandoc and a TeX distribution that provides xelatex.

## Legacy fallback: remarkable_upload.py

The legacy script may still be useful if you rely on its frontmatter-stripping behavior.

```bash
python3 /home/manuel/.local/bin/remarkable_upload.py --dry-run /abs/path/to/doc.md
python3 /home/manuel/.local/bin/remarkable_upload.py /abs/path/to/doc.md
python3 /home/manuel/.local/bin/remarkable_upload.py --force /abs/path/to/doc.md
```

## Getting Annotated PDFs from reMarkable

If you need to download annotated PDFs from the device, use the `remarks` tool (installed at `~/code/others/remarks`).

```bash
# 1. Download the .rmdoc archive from reMarkable
rmapi get ai/YYYY/MM/DD/DOCUMENT_NAME

# 2. Extract the archive and process with remarks
testdir=$(mktemp -d)
unzip -q DOCUMENT_NAME.rmdoc -d "$testdir"
outdir=$(mktemp -d)
cd ~/code/others/remarks
poetry run remarks "$testdir" "$outdir"

# 3. Copy the generated PDF (and markdown if needed)
cp "$outdir"/*.pdf ./DOCUMENT_NAME-annotated.pdf
cp "$outdir"/*.md ./DOCUMENT_NAME-annotated.md  # Optional: highlights in markdown

# 4. Cleanup
rm -rf "$testdir" "$outdir"
```
