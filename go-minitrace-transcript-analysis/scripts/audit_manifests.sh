#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:?usage: audit_manifests.sh <minitrace_root>}"

printf 'framework\tjson_files\troot_manifest_sessions\tperiod_manifest_sessions\n'

find "${ROOT_DIR}" -mindepth 1 -maxdepth 1 -type d | sort | while read -r framework_dir; do
  framework="$(basename "${framework_dir}")"
  json_files="$(find "${framework_dir}/active" -type f -name '*.minitrace.json' | wc -l | tr -d ' ')"
  root_manifest_sessions="$(jq -r '.statistics.total_sessions // 0' "${framework_dir}/manifest.json")"
  period_manifest_sessions="$(find "${framework_dir}/active" -type f -name 'manifest.json' -print0 | xargs -0 jq -r '.sessions | length' | paste -sd+ - | bc)"
  printf '%s\t%s\t%s\t%s\n' "${framework}" "${json_files}" "${root_manifest_sessions}" "${period_manifest_sessions}"
done
