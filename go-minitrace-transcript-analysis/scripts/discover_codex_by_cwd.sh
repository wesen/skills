#!/usr/bin/env bash
set -euo pipefail

printf 'warning: legacy fallback; prefer go-minitrace discover codex --cwd-contains ... --output json\n' >&2

TARGET_CWD="${1:?usage: discover_codex_by_cwd.sh <cwd> [source_root] [limit]}"
SOURCE_ROOT="${2:-$HOME/.codex/sessions}"
LIMIT="${3:-20}"

printf 'session_id\ttimestamp\tbytes\tpath\n'

find "${SOURCE_ROOT}" -type f -name '*.jsonl' | sort -r | while read -r file; do
  meta="$(sed -n '1p' "${file}")"
  cwd="$(printf '%s\n' "${meta}" | jq -r 'select(.type=="session_meta") | .payload.cwd // empty')"
  [[ "${cwd}" == "${TARGET_CWD}" ]] || continue
  session_id="$(printf '%s\n' "${meta}" | jq -r '.payload.id // empty')"
  timestamp="$(printf '%s\n' "${meta}" | jq -r '.payload.timestamp // empty')"
  bytes="$(stat -c '%s' "${file}")"
  printf '%s\t%s\t%s\t%s\n' "${session_id}" "${timestamp}" "${bytes}" "${file}"
done | head -n "${LIMIT}"
