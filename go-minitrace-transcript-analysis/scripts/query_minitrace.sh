#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: query_minitrace.sh <archive_glob> <sql>" >&2
  exit 1
fi

ARCHIVE_GLOB="$1"
SQL="$2"

go-minitrace query run --archive-glob "${ARCHIVE_GLOB}" --sql "${SQL}"
