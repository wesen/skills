#!/usr/bin/env bash
set -euo pipefail

TARGET_CWD="${1:?usage: stage_codex_by_cwd.sh <cwd> <dest_root> [source_root] [date_dir]}"
DEST_ROOT="${2:?usage: stage_codex_by_cwd.sh <cwd> <dest_root> [source_root] [date_dir]}"
SOURCE_ROOT="${3:-$HOME/.codex/sessions}"
DATE_DIR="${4:-}"

mkdir -p "${DEST_ROOT}/sessions"

if [[ -n "${DATE_DIR}" ]]; then
  SEARCH_ROOT="${SOURCE_ROOT}/${DATE_DIR}"
else
  SEARCH_ROOT="${SOURCE_ROOT}"
fi

copied=0
find "${SEARCH_ROOT}" -type f -name '*.jsonl' | sort | while read -r file; do
  meta="$(sed -n '1p' "${file}")"
  cwd="$(printf '%s\n' "${meta}" | jq -r 'select(.type=="session_meta") | .payload.cwd // empty')"
  [[ "${cwd}" == "${TARGET_CWD}" ]] || continue

  rel="${file#${SOURCE_ROOT}/}"
  dest_dir="${DEST_ROOT}/sessions/$(dirname "${rel}")"
  mkdir -p "${dest_dir}"
  cp "${file}" "${dest_dir}/"
  echo "copied ${file} -> ${dest_dir}/"
  copied=$((copied + 1))
done

echo "staged ${copied} codex session(s) into ${DEST_ROOT}"
