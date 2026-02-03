---
name: plz-confirm-operator-workflows
description: Use plz-confirm to gate long-running or human-in-the-loop steps in scripts and coding workflows (confirm, select, form, table, upload, image), including JSON parsing patterns and failure-proof runbook sequencing.
---

# plz-confirm Operator Workflows

Use this skill when you need to pause for the user, request a decision, collect structured input, or avoid missing a timing window during scripts or multi-step coding workflows.

## Core patterns (pick one)

### 1) Gated action (confirm → run)
Use when you must wait for the user before running a time-sensitive command (pairing windows, device actions, destructive steps).

```bash
APPROVED=$(plz-confirm confirm \
  --title "Start pairing window?" \
  --message "This will open a 120s permit-join window. Put the device in pairing mode now." \
  --approve-text "Run" \
  --reject-text "Cancel" \
  --output json | python3 -c 'import json,sys
try:
    data=json.load(sys.stdin)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        print(str(data[0].get("approved")).lower())
    elif isinstance(data, dict):
        print(str(data.get("approved")).lower())
    else:
        print("false")
except Exception:
    print("false")
')

if [ "$APPROVED" != "true" ]; then
  echo "User cancelled."
  exit 1
fi

# Run the time-sensitive command
./run-permit-join.sh
```

Notes:
- `plz-confirm --output json` typically returns an array of rows; parse both list and dict.
- Do **not** use `python3 - <<'PY'` with a pipe; the here-doc consumes stdin.

### 2) Wait/notify (confirm → wait window)
Use when you need to hold and then start a countdown only after the user is ready.

```bash
plz-confirm confirm \
  --title "Ready to begin?" \
  --message "Click Run when the device LED is flashing." \
  --approve-text "Run" \
  --reject-text "Cancel" \
  --output json > /tmp/confirm.json

python3 -c 'import json;print(json.load(open("/tmp/confirm.json"))[0]["approved"])'
```

### 3) Choice-based branching (select/table)
Use when the user must choose a target device or action.

```bash
CHOICE=$(plz-confirm select \
  --title "Pick device" \
  --message "Select the device to control" \
  --options "plug-office" "plug-lab" \
  --output json | python3 -c 'import json,sys
print(json.load(sys.stdin)[0].get("choice",""))')
```

### 4) Structured input (form)
Use when you need multiple parameters (timeouts, topics, credentials).

```bash
FORM=$(plz-confirm form \
  --title "Permit-join settings" \
  --field "seconds:120" \
  --field "topic:bridge/#" \
  --output json)

# plz-confirm form returns array of rows; data_json often contains a JSON string
python3 -c 'import json,sys
rows=json.load(sys.stdin)
print(rows[0].get("data_json","{}"))' <<< "$FORM" > /tmp/form.json
```

### 5) File-based operator input (upload)
Use when the user must provide a file artifact (config, firmware, logs).

```bash
UPLOAD=$(plz-confirm upload \
  --title "Upload config" \
  --message "Upload the YAML config to use" \
  --output json)
```

### 6) Visual verification (image)
Use when the user must visually confirm a result.

```bash
plz-confirm image \
  --title "Confirm UI" \
  --message "Does the UI look correct?" \
  --path /tmp/screenshot.png
```

## JSON output shapes (important)
- `confirm`, `select`, `table` often return **arrays of row objects**.
- `form` often returns array rows with `data_json` (a JSON string) that must be parsed again.
- Always guard for empty arrays, and fall back to `false`/"" on parse errors.

## Reliability checklist
- Prefer key=value args for scripts to avoid positional ambiguity.
- Align timeouts with the user’s action window (e.g., 120s join window → 120s watch duration).
- Log what you’re about to do **before** the prompt so the user has context.
- If the user cancels, exit cleanly and explain next steps.

## When to call `plz-confirm help how-to-use`
Use when you need to instruct the user on operating plz-confirm or if a workflow might be blocked by lack of familiarity. Capture its output into a file when asked to include it in tickets/runbooks.

## Minimal helper (bash)
```bash
plz_confirm_approved() {
  plz-confirm confirm --title "$1" --message "$2" --approve-text Run --reject-text Cancel --output json |
    python3 -c 'import json,sys
try:
    data=json.load(sys.stdin)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        print(str(data[0].get("approved")).lower())
    elif isinstance(data, dict):
        print(str(data.get("approved")).lower())
    else:
        print("false")
except Exception:
    print("false")'
}
```

## Pitfalls to avoid
- Don’t pipe JSON into `python3 -` while also using a here-doc; stdin will be consumed.
- Don’t assume a single object; array output is common.
- Avoid running time-sensitive actions before the prompt; always gate first.

## References
- If you need more examples, search in the repo for `plz-confirm` usage patterns.
