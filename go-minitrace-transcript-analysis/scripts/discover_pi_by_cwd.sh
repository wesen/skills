#!/usr/bin/env bash
set -euo pipefail

printf 'warning: legacy fallback; prefer go-minitrace discover pi --cwd-contains ... --output json\n' >&2

TARGET_CWD="${1:?usage: discover_pi_by_cwd.sh <cwd> [source_root] [limit]}"
SOURCE_ROOT="${2:-$HOME/.pi/agent/sessions}"
LIMIT="${3:-20}"

slug_path() {
  local path="$1"
  printf '%s' "${path}" | sed 's#^/##; s#/#-#g; s#^#--#; s#$#--#'
}

SESSION_DIR="${SOURCE_ROOT}/$(slug_path "${TARGET_CWD}")"
if [[ ! -d "${SESSION_DIR}" ]]; then
  echo "missing session dir: ${SESSION_DIR}" >&2
  exit 1
fi

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
  base="$(basename "${file}")"
  session_id="${base##*_}"
  session_id="${session_id%.jsonl}"
  timestamp="${base%%_*}"
  bytes="$(stat -c '%s' "${file}")"
  printf '%s\t%s\t%s\t%s\n' "${session_id}" "${timestamp}" "${bytes}" "${file}"
  count=$((count + 1))
  [[ "${count}" -ge "${LIMIT}" ]] && break
done < <(find "${SESSION_DIR}" -maxdepth 1 -type f -name '*.jsonl' | sort -r)
