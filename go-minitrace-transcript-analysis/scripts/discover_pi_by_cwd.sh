#!/usr/bin/env bash
set -euo pipefail

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

find "${SESSION_DIR}" -maxdepth 1 -type f -name '*.jsonl' | sort -r | while read -r file; do
  base="$(basename "${file}")"
  session_id="${base##*_}"
  session_id="${session_id%.jsonl}"
  timestamp="${base%%_*}"
  bytes="$(stat -c '%s' "${file}")"
  printf '%s\t%s\t%s\t%s\n' "${session_id}" "${timestamp}" "${bytes}" "${file}"
done | head -n "${LIMIT}"
