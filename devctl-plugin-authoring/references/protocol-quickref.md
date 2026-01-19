# Devctl Plugin Protocol Quick Reference

Keep stdout clean: one JSON object per line, no extra output. Log to stderr.

## Handshake (first stdout line)

Example minimal handshake:

{
  "type": "handshake",
  "protocol_version": "v2",
  "plugin_name": "myrepo",
  "capabilities": {
    "ops": ["config.mutate", "validate.run", "launch.plan"]
  }
}

## Request shape (stdin)

{
  "type": "request",
  "request_id": "...",
  "op": "config.mutate",
  "ctx": {
    "repo_root": "/path/to/repo",
    "cwd": "/path/to/cwd",
    "dry_run": false,
    "deadline_ms": 1700000000
  },
  "input": { }
}

## Response shape (stdout)

Success:

{
  "type": "response",
  "request_id": "...",
  "ok": true,
  "output": { }
}

Failure:

{
  "type": "response",
  "request_id": "...",
  "ok": false,
  "error": { "code": "E_UNSUPPORTED", "message": "unsupported op: ..." }
}

## Minimal Python skeleton

- Emit handshake immediately.
- Flush after each write.
- Never print to stdout except protocol frames.

#!/usr/bin/env python3
import json
import sys


def emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def log(msg):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


emit({
    "type": "handshake",
    "protocol_version": "v2",
    "plugin_name": "myrepo",
    "capabilities": {"ops": ["config.mutate", "validate.run", "launch.plan"]},
})

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    rid = req.get("request_id", "")
    op = req.get("op", "")

    if op == "config.mutate":
        emit({
            "type": "response",
            "request_id": rid,
            "ok": True,
            "output": {"config_patch": {"set": {"env.API_PORT": "8080"}, "unset": []}},
        })
    elif op == "validate.run":
        emit({
            "type": "response",
            "request_id": rid,
            "ok": True,
            "output": {"valid": True, "errors": [], "warnings": []},
        })
    elif op == "launch.plan":
        emit({
            "type": "response",
            "request_id": rid,
            "ok": True,
            "output": {
                "services": [
                    {"name": "api", "command": ["bash", "-lc", "python3 -m http.server 8080"]}
                ]
            },
        })
    else:
        emit({
            "type": "response",
            "request_id": rid,
            "ok": False,
            "error": {"code": "E_UNSUPPORTED", "message": f"unsupported op: {op}"},
        })

## Minimal bash + jq skeleton

#!/usr/bin/env bash
set -euo pipefail

emit() { jq -c . <<<"$1"; }
log() { printf '%s\n' "$*" >&2; }

emit '{"type":"handshake","protocol_version":"v2","plugin_name":"bash","capabilities":{"ops":["launch.plan"]}}'

while IFS= read -r line; do
  [ -z "$line" ] && continue
  rid="$(jq -r '.request_id // ""' <<<"$line")"
  op="$(jq -r '.op // ""' <<<"$line")"

  if [ "$op" = "launch.plan" ]; then
    emit "$(jq -nc --arg rid "$rid" '{
      type:"response", request_id:$rid, ok:true,
      output:{services:[{name:"api", command:["bash","-lc","echo api && sleep 3600"]}]}
    }')"
  else
    emit "$(jq -nc --arg rid "$rid" --arg op "$op" '{
      type:"response", request_id:$rid, ok:false,
      error:{code:"E_UNSUPPORTED", message:("unsupported op: "+$op)}
    }')"
  fi
 done
