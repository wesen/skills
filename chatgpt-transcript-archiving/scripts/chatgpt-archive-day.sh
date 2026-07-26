#!/usr/bin/env bash
# chatgpt-archive-day.sh — Download and archive ChatGPT conversations for a given day
#
# Usage: chatgpt-archive-day.sh [YYYY-MM-DD] [TAB_ID]
#   YYYY-MM-DD  Date to archive (default: today)
#   TAB_ID      ChatGPT tab id (auto-detected if omitted)
#
# Requires: surf-go installed, ChatGPT logged in, Obsidian vault at
# ~/code/wesen/go-go-golems/go-go-parc
#
# Outputs:
#   - Transcripts in $VAULT/Transcripts/YYYY/MM/DD/CHATGPT TRANSCRIPT - <title>.md
#   - Output files in $VAULT/Transcripts/YYYY/MM/DD/<title>/ (per-conversation subdirectory)
#   - A summary printed to stdout

set -euo pipefail

VAULT="${HOME}/code/wesen/go-go-golems/go-go-parc"
SURF_SOCKET_PATH="${SURF_SOCKET_PATH:-${HOME}/snap/chromium/common/surf-cli/surf.sock}"
export SURF_SOCKET_PATH

DATE="${1:-$(date +%Y-%m-%d)}"
YEAR=$(echo "$DATE" | cut -d- -f1)
MONTH=$(echo "$DATE" | cut -d- -f2)
DAY=$(echo "$DATE" | cut -d- -f3)
TRANSCRIPT_DIR="${VAULT}/Transcripts/${YEAR}/${MONTH}/${DAY}"
TMP_DIR="/tmp/chatgpt-archive-${DATE}"

mkdir -p "$TRANSCRIPT_DIR" "$TMP_DIR"

echo "=== ChatGPT Daily Archive: ${DATE} ==="
echo "Transcripts → ${TRANSCRIPT_DIR}"
echo ""

# --- Step 1: Find or open a ChatGPT tab ---
find_tab() {
  local tab_id
  # Look for a tab whose URL is exactly https://chatgpt.com/
  tab_id=$(surf-go tab list 2>/dev/null | awk '
    /^      id:/ { id = $2 }
    /url: https:\/\/chatgpt.com\/$/ { print id }
  ' | head -1)
  if [ -z "$tab_id" ]; then
    echo "No ChatGPT tab found, opening one..."
    tab_id=$(surf-go tab new --args-json '{"url":"https://chatgpt.com/"}' 2>/dev/null \
      | awk '/tabId:/ { print $2 }')
    echo "Opened tab ${tab_id}, waiting for page load..."
    sleep 5
  fi
  echo "$tab_id"
}

TAB_ID="${2:-$(find_tab)}"
if [ -z "$TAB_ID" ]; then
  echo "ERROR: Could not find or open a ChatGPT tab. Is surf-go running?" >&2
  exit 1
fi
echo "Using ChatGPT tab: ${TAB_ID}"
echo ""

# --- Step 2: List conversations for the target date ---
echo "--- Step 1: Listing conversations for ${DATE} ---"
CONV_LIST="${TMP_DIR}/conversations.txt"

# The js tool returns the result as a JSON-encoded string wrapped in single quotes:
#   content: '"id1|title1\nid2|title2"'
# We strip the wrapper and unescape \n.
surf-go js --tab-id "$TAB_ID" --timeout-ms 30000 "
const s = await fetch('/api/auth/session', {credentials: 'include'});
const token = (await s.json()).accessToken;
if (!token) { throw new Error('ChatGPT login required'); }
const r = await fetch('/backend-api/conversations?offset=0&limit=100&order=updated', {
  credentials: 'include', headers: { Authorization: 'Bearer ' + token },
});
const j = await r.json();
const items = j.items || [];
const target = items.filter(it => (it.update_time || '').slice(0,10) === '${DATE}')
  .map(it => it.id + '|' + (it.title || 'Untitled'));
return target.join('\n');
" 2>/dev/null \
  | sed "s/^content: '//; s/'$//" \
  | sed 's/^"//; s/"$//' \
  | sed 's/\\n/\n/g' \
  | grep -E '^[0-9a-f]{8}-' > "${CONV_LIST}"

CONV_COUNT=$(wc -l < "${CONV_LIST}")
echo "Found ${CONV_COUNT} conversations for ${DATE}"
echo ""

if [ "$CONV_COUNT" -eq 0 ]; then
  echo "No conversations found for ${DATE}. Done."
  exit 0
fi

# --- Step 3: Download transcripts ---
echo "--- Step 2: Downloading transcripts ---"
NEW_TRANSCRIPTS=0
SKIPPED_TRANSCRIPTS=0
while IFS='|' read -r CONV_ID CONV_TITLE; do
  [ -z "$CONV_ID" ] && continue
  # Sanitize title for filename (keep it readable, no underscores)
  SAFE_TITLE=$(echo "$CONV_TITLE" | tr '/' '_' | tr -cd 'A-Za-z0-9 _.-' | sed 's/  */ /g' | sed 's/^ *//; s/ *$//' | cut -c1-70)
  DEST="${TRANSCRIPT_DIR}/CHATGPT TRANSCRIPT - ${SAFE_TITLE}.md"

  # Skip if already downloaded — check if any transcript file contains this conversation URL
  CONV_URL="https://chatgpt.com/c/${CONV_ID}"
  EXISTING=$(grep -rl "$CONV_URL" "${TRANSCRIPT_DIR}"/CHATGPT*.md 2>/dev/null | head -1 || true)
  if [ -n "$EXISTING" ]; then
    echo "  ✓ (skip) ${SAFE_TITLE}"
    SKIPPED_TRANSCRIPTS=$((SKIPPED_TRANSCRIPTS + 1))
    continue
  fi

  echo -n "  → ${SAFE_TITLE}: "
  if surf-go chatgpt transcript --from-api --conversation-id "$CONV_ID" --tab-id "$TAB_ID" --timeout-ms 60000 2>/dev/null > "$DEST"; then
    LINES=$(wc -l < "$DEST")
    echo "${LINES} lines"
    NEW_TRANSCRIPTS=$((NEW_TRANSCRIPTS + 1))
  else
    echo "FAILED"
    rm -f "$DEST"
  fi
  sleep 1
done < "${CONV_LIST}"
echo "  (${NEW_TRANSCRIPTS} new, ${SKIPPED_TRANSCRIPTS} skipped)"
echo ""

# --- Step 4: Download output files alongside transcripts ---
echo "--- Step 3: Downloading output files ---"
TOTAL_DOWNLOADED=0
while IFS='|' read -r CONV_ID CONV_TITLE; do
  [ -z "$CONV_ID" ] && continue
  # Sanitize title for the per-conversation subdirectory
  SAFE_TITLE=$(echo "$CONV_TITLE" | tr '/' '_' | tr -cd 'A-Za-z0-9 _.-' | sed 's/  */ /g' | sed 's/^ *//; s/ *$//' | cut -c1-70)
  CONV_FILES_DIR="${TRANSCRIPT_DIR}/${SAFE_TITLE}"
  echo -n "  → ${SAFE_TITLE}: "
  # Download files directly into a per-conversation subdirectory next to the transcript
  DL_COUNT=$(surf-go chatgpt download --conversation-id "$CONV_ID" --tab-id "$TAB_ID" --output-dir "$CONV_FILES_DIR" --timeout-ms 120000 --skip-existing 2>/dev/null | grep -c "downloaded" || true)
  echo "${DL_COUNT} files"
  TOTAL_DOWNLOADED=$((TOTAL_DOWNLOADED + DL_COUNT))
  # surf-go creates a <conversation-id>/ subdir inside --output-dir; flatten it
  NESTED_DIR="${CONV_FILES_DIR}/${CONV_ID}"
  if [ -d "$NESTED_DIR" ]; then
    mv "$NESTED_DIR"/* "$CONV_FILES_DIR"/ 2>/dev/null || true
    rmdir "$NESTED_DIR" 2>/dev/null || true
  fi
  # Remove the manifest.json (not useful in the vault) and empty dirs
  rm -f "${CONV_FILES_DIR}/manifest.json"
  if [ -d "$CONV_FILES_DIR" ] && [ -z "$(ls -A "$CONV_FILES_DIR" 2>/dev/null)" ]; then
    rmdir "$CONV_FILES_DIR"
  fi
  sleep 1
done < "${CONV_LIST}"
echo ""

# --- Step 5: Summary ---
TOTAL_TRANSCRIPTS=$(ls "${TRANSCRIPT_DIR}"/CHATGPT*.md 2>/dev/null | wc -l)
echo "=== Archive Complete: ${DATE} ==="
echo "Transcripts: ${TOTAL_TRANSCRIPTS} total (${NEW_TRANSCRIPTS} new, ${SKIPPED_TRANSCRIPTS} skipped)"
echo "Files downloaded: ${TOTAL_DOWNLOADED}"
echo "Transcript dir: ${TRANSCRIPT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review transcripts in Obsidian"
echo "  2. Classify each transcript by topic (see skill: chatgpt-transcript-archiving)"
echo "  3. Link to relevant MOCs in Research/KB/Projects/"
echo "  4. Upload to reMarkable: chatgpt-upload-remarkable.sh ${DATE}"
echo "  5. Commit and push the vault"
