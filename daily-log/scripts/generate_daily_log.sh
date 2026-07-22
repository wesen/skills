#!/usr/bin/env bash
#
# generate_daily_log.sh — Stages 1-3 of the daily-log skill.
#
# Discovers all Pi and Codex sessions active on a target day, converts them
# to normalized minitrace archives, and runs the session-list overview query.
#
# This script does NOT write the report or verify against git. Those stages
# require judgment and are done manually. See the daily-log SKILL.md.
#
# Usage:
#   generate_daily_log.sh <TARGET_DAY> [INVEST_DIR]
#
#   TARGET_DAY   The day to report on, in YYYY-MM-DD format.
#   INVEST_DIR   Optional. Where to store archives/queries/results.
#                Defaults to scripts/<TODAY>/daily-report-<TARGET_DAY>
#                relative to the current working directory.
#
# Run from the claw-stuff repo root (or any repo with a scripts/ dir).

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: generate_daily_log.sh <TARGET_DAY> [INVEST_DIR]" >&2
  echo "  TARGET_DAY  e.g. 2026-07-19" >&2
  exit 1
fi

TARGET_DAY="$1"
TODAY="$(date +%Y/%m/%d)"

if [[ $# -ge 2 ]]; then
  INVEST_DIR="$2"
else
  INVEST_DIR="scripts/${TODAY}/daily-report-${TARGET_DAY}"
fi

mkdir -p "$INVEST_DIR"/{archives,queries,results}

echo "=== Daily log investigation ==="
echo "Target day:  $TARGET_DAY"
echo "Invest dir:  $INVEST_DIR"
echo ""

# ---- Stage 1: Discover ----
echo "=== Stage 1: Discover candidate sessions ==="

go-minitrace discover pi \
  --source-dir ~/.pi/agent/sessions \
  --active-since "$TARGET_DAY" \
  --output json > "$INVEST_DIR/results/pi-discovery.json" 2>&1 || {
    echo "ERROR: pi discovery failed" >&2
    exit 1
  }

go-minitrace discover codex \
  --source-dir ~/.codex \
  --active-since "$TARGET_DAY" \
  --output json > "$INVEST_DIR/results/codex-discovery.json" 2>&1 || {
    echo "ERROR: codex discovery failed" >&2
    exit 1
  }

go-minitrace discover claude-code \
  --source-dir ~/.claude/projects \
  --active-since "$TARGET_DAY" \
  --output json > "$INVEST_DIR/results/claude-code-discovery.json" 2>&1 || {
    echo "ERROR: claude-code discovery failed" >&2
    exit 1
  }

PI_COUNT=$(python3 -c "import json; print(len(json.load(open('$INVEST_DIR/results/pi-discovery.json'))))" 2>/dev/null || echo "?")
CODEX_COUNT=$(python3 -c "import json; print(len(json.load(open('$INVEST_DIR/results/codex-discovery.json'))))" 2>/dev/null || echo "?")
CLAUDE_COUNT=$(python3 -c "import json; print(len(json.load(open('$INVEST_DIR/results/claude-code-discovery.json'))))" 2>/dev/null || echo "?")
echo "Pi candidates:          $PI_COUNT"
echo "Codex candidates:       $CODEX_COUNT"
echo "Claude Code candidates: $CLAUDE_COUNT"
echo ""

# ---- Build source lists ----
# Extract source_path values from discovery JSON, one per line.
python3 -c "
import json, sys
paths = []
for f in ['$INVEST_DIR/results/pi-discovery.json', '$INVEST_DIR/results/codex-discovery.json', '$INVEST_DIR/results/claude-code-discovery.json']:
    try:
        for s in json.load(open(f)):
            p = s.get('source_path')
            if p:
                paths.append(p)
    except Exception:
        pass
for p in sorted(set(paths)):
    print(p)
" > "$INVEST_DIR/sources.txt"

SOURCE_COUNT=$(wc -l < "$INVEST_DIR/sources.txt")
echo "Source list: $SOURCE_COUNT sessions -> $INVEST_DIR/sources.txt"
echo ""

# ---- Stage 2: Convert ----
echo "=== Stage 2: Convert to archives ==="

# Convert Pi sessions.
go-minitrace convert pi \
  --source-list "$INVEST_DIR/sources.txt" \
  --output-dir "$INVEST_DIR/archives/pi" 2>&1 | tail -5 || {
    echo "WARNING: pi convert via source-list had issues" >&2
  }

# Convert Codex sessions explicitly (more reliable than a mixed list).
CODEX_SOURCES=$(python3 -c "
import json
try:
    for s in json.load(open('$INVEST_DIR/results/codex-discovery.json')):
        p = s.get('source_path')
        if p:
            print(p)
except Exception:
    pass
")

if [[ -n "$CODEX_SOURCES" ]]; then
  CODEX_ARGS=()
  while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    CODEX_ARGS+=(--source-session "$src")
  done <<< "$CODEX_SOURCES"
  if [[ ${#CODEX_ARGS[@]} -gt 0 ]]; then
    go-minitrace convert codex \
      "${CODEX_ARGS[@]}" \
      --output-dir "$INVEST_DIR/archives/codex" 2>&1 | tail -5 || {
        echo "WARNING: codex convert failed" >&2
      }
  fi
fi

# Convert Claude Code sessions explicitly.
CLAUDE_SOURCES=$(python3 -c "
import json
try:
    for s in json.load(open('$INVEST_DIR/results/claude-code-discovery.json')):
        p = s.get('source_path')
        if p:
            print(p)
except Exception:
    pass
")

if [[ -n "$CLAUDE_SOURCES" ]]; then
  CLAUDE_ARGS=()
  while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    CLAUDE_ARGS+=(--source-session "$src")
  done <<< "$CLAUDE_SOURCES"
  if [[ ${#CLAUDE_ARGS[@]} -gt 0 ]]; then
    go-minitrace convert claude-code \
      "${CLAUDE_ARGS[@]}" \
      --output-dir "$INVEST_DIR/archives/claude-code" 2>&1 | tail -5 || {
        echo "WARNING: claude-code convert failed" >&2
      }
  fi
fi

echo ""
GLOB="$INVEST_DIR/archives/*/active/*/*.minitrace.json"
ARCHIVE_COUNT=$(ls $GLOB 2>/dev/null | wc -l)
echo "Archives created: $ARCHIVE_COUNT"
echo ""

# ---- Stage 3: Query overview ----
echo "=== Stage 3: Session-list overview ==="

go-minitrace query run \
  --archive-glob "$GLOB" \
  --preset session-list 2>&1 || {
    echo "WARNING: session-list query failed" >&2
  }

echo ""
echo "=== Stages 1-3 complete ==="
echo ""
echo "Next steps (manual):"
echo "  1. Identify repositories and tickets from the session-list above."
echo "  2. Run history file-history per repo path fragment:"
echo "     go-minitrace query commands history file-history --archive-glob '$GLOB' --path '<fragment>' --output json"
echo "  3. Run history ticket-timeline per ticket fragment:"
echo "     go-minitrace query commands history ticket-timeline --archive-glob '$GLOB' --ticket '<FRAGMENT>' --output json"
echo "  4. Verify commit counts against git:"
echo "     git -C <repo> log --since='$TARGET_DAY 00:00:00' --until='$TARGET_DAY 23:59:59' --oneline | wc -l"
echo "  5. Read full changelog entries from disk (the verb truncates detail)."
echo "  6. Write the report to the vault using references/report-template.md."
echo ""
echo "Investigation artifacts: $INVEST_DIR"
