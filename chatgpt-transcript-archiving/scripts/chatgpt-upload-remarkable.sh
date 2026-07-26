#!/usr/bin/env bash
# chatgpt-upload-remarkable.sh — Upload ChatGPT transcripts and output files to reMarkable
#
# Usage: chatgpt-upload-remarkable.sh [YYYY-MM-DD]
#   YYYY-MM-DD  Date to upload (default: today)
#
# Requires: remarquee, rmapi, pandoc-math wrapper at ~/.local/bin/pandoc-math
#
# Uploads to:
#   /ai/YYYY/MM/DD/ChatGPT-Transcripts/  — each transcript as a separate PDF
#   /ai/YYYY/MM/DD/ChatGPT-Outputs/      — output .md files (bundled per conversation) + PDFs

set -uo pipefail

VAULT="${HOME}/code/wesen/go-go-golems/go-go-parc"
DATE="${1:-$(date +%Y-%m-%d)}"
YEAR=$(echo "$DATE" | cut -d- -f1)
MONTH=$(echo "$DATE" | cut -d- -f2)
DAY=$(echo "$DATE" | cut -d- -f3)
TRANSCRIPT_DIR="${VAULT}/Transcripts/${YEAR}/${MONTH}/${DAY}"
PANDOC_MATH="${HOME}/.local/bin/pandoc-math"
REMOTE_TRANSCRIPTS="/ai/${YEAR}/${MONTH}/${DAY}/ChatGPT-Transcripts"
REMOTE_OUTPUTS="/ai/${YEAR}/${MONTH}/${DAY}/ChatGPT-Outputs"

echo "=== reMarkable Upload: ${DATE} ==="
echo "Transcripts → ${REMOTE_TRANSCRIPTS}/"
echo "Outputs     → ${REMOTE_OUTPUTS}/"
echo ""

# --- Step 1: Upload transcripts ---
echo "--- Step 1: Uploading transcripts ---"
for f in "${TRANSCRIPT_DIR}"/CHATGPT*.md; do
  [ -f "$f" ] || continue
  name=$(basename "$f" .md | sed 's/^CHATGPT TRANSCRIPT - //')
  echo -n "  → ${name}: "
  remarquee upload md "$f" \
    --name "$name" \
    --remote-dir "$REMOTE_TRANSCRIPTS" \
    --pandoc "$PANDOC_MATH" \
    --non-interactive 2>&1 | grep -E "^OK:|^Error:" | head -1 || true
done
echo ""

# --- Step 2: Upload output .md files (bundled per conversation) ---
echo "--- Step 2: Uploading output .md files ---"
for d in "${TRANSCRIPT_DIR}"/*/; do
  [ -d "$d" ] || continue
  d="${d%/}"
  conv_name=$(basename "$d")
  md_files=$(find "$d" -maxdepth 1 -name "*.md" -type f 2>/dev/null)
  [ -z "$md_files" ] && continue
  echo -n "  → ${conv_name}: "
  remarquee upload bundle \
    "$d"/*.md \
    --name "ChatGPT Output - ${conv_name}" \
    --remote-dir "$REMOTE_OUTPUTS" \
    --pandoc "$PANDOC_MATH" \
    --toc-depth 2 \
    --non-interactive 2>&1 | grep -E "^OK:|^Error:" | head -1 || true
done
echo ""

# --- Step 3: Upload output .pdf files (via rmapi, deduplicated) ---
echo "--- Step 3: Uploading output .pdf files ---"
# Create the remote directory first (rmapi requires it to exist)
rmapi mkdir "$REMOTE_OUTPUTS" 2>/dev/null || true
PDF_COUNT=0
declare -A seen_pdfs
find "${TRANSCRIPT_DIR}" -name "*.pdf" -type f | while read -r f; do
  name=$(basename "$f" .pdf)
  sha=$(sha256sum "$f" | cut -c1-16)
  if [ -n "${seen_pdfs[$sha]:-}" ]; then
    echo "  (skip dup) ${name}"
    continue
  fi
  seen_pdfs[$sha]=1
  echo -n "  → ${name}: "
  # rmapi needs a simple path (no em-dashes); copy to temp if needed
  if echo "$f" | grep -q '[^a-zA-Z0-9 /._-]'; then
    tmp="/tmp/${name}.pdf"
    cp "$f" "$tmp"
    rmapi put "$tmp" "${REMOTE_OUTPUTS}/" 2>&1 | tail -1
    rm -f "$tmp"
  else
    rmapi put "$f" "${REMOTE_OUTPUTS}/" 2>&1 | tail -1
  fi
done
echo ""

echo "=== Upload Complete: ${DATE} ==="
echo "Transcripts: $(ls "${TRANSCRIPT_DIR}"/CHATGPT*.md 2>/dev/null | wc -l) files"
echo "Output dirs: $(find "${TRANSCRIPT_DIR}" -maxdepth 1 -type d ! -path "${TRANSCRIPT_DIR}" | wc -l) conversations"
