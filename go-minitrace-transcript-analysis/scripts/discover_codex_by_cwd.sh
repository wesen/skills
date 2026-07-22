#!/usr/bin/env bash
set -euo pipefail

printf 'warning: legacy fallback; prefer go-minitrace discover codex --cwd-contains ... --output json\n' >&2

TARGET_CWD="${1:?usage: discover_codex_by_cwd.sh <cwd> [source_root] [limit]}"
SOURCE_ROOT="${2:-$HOME/.codex/sessions}"
LIMIT="${3:-20}"

printf 'session_id\ttimestamp\tbytes\tpath\n'

# The limit is enforced by a counter inside the loop rather than by piping the
# loop into `head -n`. Under `set -o pipefail`, `head` exits as soon as it has
# printed LIMIT lines, the still-writing loop takes SIGPIPE, and the pipeline
# reports exit 141 — a failure status for a completely normal truncation. Input
# arrives by process substitution for the same reason: keeping the loop out of a
# pipeline means pipefail never inspects find/sort's status when the loop breaks
# early. It also keeps `count` in the current shell instead of a subshell.
count=0
while read -r file; do
  meta="$(sed -n '1p' "${file}")"
  cwd="$(printf '%s\n' "${meta}" | jq -r 'select(.type=="session_meta") | .payload.cwd // empty')"
  [[ "${cwd}" == "${TARGET_CWD}" ]] || continue
  session_id="$(printf '%s\n' "${meta}" | jq -r '.payload.id // empty')"
  timestamp="$(printf '%s\n' "${meta}" | jq -r '.payload.timestamp // empty')"
  bytes="$(stat -c '%s' "${file}")"
  printf '%s\t%s\t%s\t%s\n' "${session_id}" "${timestamp}" "${bytes}" "${file}"
  count=$((count + 1))
  [[ "${count}" -ge "${LIMIT}" ]] && break
done < <(find "${SOURCE_ROOT}" -type f -name '*.jsonl' | sort -r)
