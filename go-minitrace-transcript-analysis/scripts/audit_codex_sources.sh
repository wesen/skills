#!/usr/bin/env bash
set -euo pipefail

SOURCE_LIST="${1:?usage: audit_codex_sources.sh <source-list>}"

if [[ ! -f "${SOURCE_LIST}" ]]; then
  printf 'error: source list not found: %s\n' "${SOURCE_LIST}" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || {
  printf 'error: jq is required\n' >&2
  exit 1
}

rows="$(mktemp)"
trap 'rm -f "${rows}"' EXIT

printf 'native_id\tparent_thread_id\teffective_normalized_id\trelation\tcwd\tpath\n'

while IFS= read -r source || [[ -n "${source}" ]]; do
  [[ -z "${source}" || "${source}" == \#* ]] && continue

  if [[ ! -f "${source}" ]]; then
    printf 'error: native source not found: %s\n' "${source}" >&2
    exit 1
  fi

  meta="$(head -n 1 "${source}")"
  if ! printf '%s\n' "${meta}" | jq -e '.type == "session_meta"' >/dev/null; then
    printf 'error: first line is not Codex session_meta: %s\n' "${source}" >&2
    exit 1
  fi

  native_id="$(printf '%s\n' "${meta}" | jq -r '.payload.id // empty')"
  parent_id="$(printf '%s\n' "${meta}" | jq -r '
    .payload.source
    | if type == "object"
      then .subagent.thread_spawn.parent_thread_id // empty
      else empty
      end
  ')"
  cwd="$(printf '%s\n' "${meta}" | jq -r '.payload.cwd // empty')"

  if [[ -n "${parent_id}" ]]; then
    effective_id="${parent_id}"
    relation="subagent"
  else
    effective_id="${native_id}"
    relation="root"
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "${native_id}" "${parent_id}" "${effective_id}" "${relation}" "${cwd}" "${source}" \
    | tee -a "${rows}"
done < "${SOURCE_LIST}"

if [[ ! -s "${rows}" ]]; then
  printf 'warning: no Codex sources found in %s\n' "${SOURCE_LIST}" >&2
  exit 0
fi

collisions="$(cut -f3 "${rows}" | sort | uniq -d)"
if [[ -n "${collisions}" ]]; then
  printf '\ncollision risk: multiple native Codex sources map to the same effective normalized identity:\n' >&2
  while IFS= read -r effective_id; do
    [[ -z "${effective_id}" ]] && continue
    printf '  effective_normalized_id=%s\n' "${effective_id}" >&2
    awk -F '\t' -v id="${effective_id}" '$3 == id { printf "    %s (%s) %s\n", $1, $4, $6 }' "${rows}" >&2
  done <<< "${collisions}"
  printf 'convert colliding sources into separate output directories or select one authoritative source\n' >&2
  exit 2
fi

printf 'audit passed: %s native source(s), no effective-identity collisions\n' "$(wc -l < "${rows}" | tr -d ' ')" >&2
