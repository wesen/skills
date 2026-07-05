# Playbook — Author a Prompto Plugin

> Companion to §16 of `references/intern-guide.md`. This is the
> step-by-step checklist version.

## When to use a plugin

- You need **computed choices** (live ticket ids, git branches, files in a
  directory).
- You need to **gather context** at expand time (run a command, read files,
  fetch a URL) and weave it into the prompt.
- You need **branching logic** beyond `{{#if}}` (loops, data transforms,
  multi-step assembly).

If none of these apply, a template is simpler — use that.

## 0. Prerequisites

- Decide the layer:
  - **Global** (`~/.pi/agent/prompts/<group>/<name>`) — always runs.
  - **Project** (`.pi/prompts/<group>/<name>`) — requires
    `allowProjectPlugins: true` in `~/.pi/agent/prompto.json` (default
    `false`). Project plugins are a security boundary; only enable when you
    trust the repo.
- Pick a language with a JSON library (python, bash+jq, node, go, …).
- The file must be **executable** (`chmod +x`). The extension detects
  plugins by the executable bit.

## 1. Pick the addressable name

The plugin's directory under the layer root is the **group**; each
announced template's addressable name becomes `<group>/<name>`.

```
~/.pi/agent/prompts/docmgr/tickets   →  group "docmgr", names "docmgr/close-ticket", "docmgr/ticket-status"
```

One plugin can announce **multiple** templates (e.g. `close-ticket` and
`ticket-status` from one executable).

## 2. Implement the describe phase

`plugin --describe` prints one JSON object per line on stdout, then `end`:

```json
{"type":"template","name":"<name>","title":"...","description":"...",
 "fields":[{"name":"ticket","type":"choice","choices":["A","B"],"required":true}],
 "submit":"editor"}
{"type":"end"}
```

- `name` — required, `/^[a-zA-Z0-9_][a-zA-Z0-9_-]*$/` (dashes OK, unlike
  field names).
- `fields` — **same schema as template frontmatter fields** (see the
  template playbook). `choices` may be **computed** here (the killer
  feature): call `docmgr`, `git`, the filesystem, etc.
- `prefill` — optional, same schema as template prefill (the LLM call runs
  in the extension, not your plugin).
- `submit` — optional `editor` (default) or `auto`.
- Timeout: **5 seconds**. Exit 0.

Rules:

- stderr is never parsed — log freely there.
- Junk lines and unknown `type`s are skipped (forward compat).
- After `{"type":"end"}`, further frames are ignored.
- Invalid announcements become warnings, not crashes — other templates
  still load.

## 3. Implement the render phase

With no `--describe` arg, the plugin reads **one line** from stdin (the
extension closes stdin after writing it):

```json
{"type":"render","template":"<name>","values":{"ticket":"A","summary":"..."},"cwd":"/home/user/project"}
```

Respond with zero or more `log` frames, then exactly one terminal frame:

```json
{"type":"log","message":"querying docmgr…"}
{"type":"prompt","text":"the full expanded prompt"}
```

or

```json
{"type":"error","message":"what went wrong"}
```

- Timeout: **60 seconds**.
- The subprocess `cwd` is the user's `cwd`.
- Env vars `PROMPTO_TEMPLATE` (the announced name) and `PROMPTO_PLUGIN_PATH`
  (the executable path) are set.
- Always handle an unknown `template` value with an `error` frame.

## 4. Build JSON safely

**Never hand-roll JSON for the prompt text.** Use a JSON builder so
newlines, quotes, and backslashes are escaped correctly:

```bash
# bash: use jq -cn
jq -cn --arg focus "$focus" --arg diff "$diff_output" \
  '{type:"prompt", text:("Review this diff (focus: " + $focus + "):\n\n```diff\n" + $diff + "\n```")}'

# python: json.dumps
print(json.dumps({"type": "prompt", "text": f"Review {values['ticket']}"}))
```

Unescaped characters in hand-built JSON break the JSONL line and the
extension rejects with `exited without a prompt frame`.

## 5. Minimal python skeleton

```python
#!/usr/bin/env python3
import json, subprocess, sys

def existing_ticket_ids(cwd):
    try:
        out = subprocess.run(["docmgr", "ticket", "list"],
            capture_output=True, text=True, timeout=3, cwd=cwd, check=False).stdout
    except Exception:
        return []
    return [l[4:].split(" ")[0] for l in out.splitlines() if l.startswith("### ")][:20]

def describe():
    print(json.dumps({
        "type": "template", "name": "close-ticket", "title": "Close a docmgr ticket",
        "fields": [
            {"name": "ticket", "type": "choice",
             "choices": existing_ticket_ids(".") or ["NO-TICKETS-FOUND"], "required": True},
            {"name": "summary", "type": "text", "required": True},
        ],
    }))
    print(json.dumps({"type": "end"}))

def render():
    req = json.loads(sys.stdin.readline())
    v = req.get("values", {})
    if req.get("template") == "close-ticket":
        print(json.dumps({"type": "log", "message": "building closing prompt"}))
        print(json.dumps({"type": "prompt", "text":
            f"Close docmgr ticket {v.get('ticket')}.\n\nSummary:\n{v.get('summary','')}\n\n"
            "Check tasks, update changelog, run docmgr doctor, then: "
            f"docmgr ticket close --ticket {v.get('ticket')}"}))
    else:
        print(json.dumps({"type": "error", "message": f"unknown template {req.get('template')!r}"}))

if __name__ == "__main__":
    describe() if "--describe" in sys.argv else render()
```

## 6. Install and reload

```bash
# global layer
cp my.plugin ~/.pi/agent/prompts/<group>/<name>
chmod +x ~/.pi/agent/prompts/<group>/<name>

# project layer (needs allowProjectPlugins: true)
cp my.plugin .pi/prompts/<group>/<name>
chmod +x .pi/prompts/<group>/<name>
```

Then in pi:

```
/prompto reload
```

Check the toast: `N templates loaded · M plugins queried`. If you see
`project-layer plugin skipped`, set `allowProjectPlugins: true` in
`~/.pi/agent/prompto.json`.

## 7. Test manually before using

```bash
# Describe phase — pretty-print the announcement
./my.plugin --describe | jq .

# Render phase — pipe a request, see the frames
echo '{"type":"render","template":"close-ticket","values":{"ticket":"FOO-1","summary":"x"},"cwd":"."}' | ./my.plugin
```

Confirm:

- `describe` emits one `template` per announced template, then `end`.
- `render` emits zero or more `log`, then exactly one `prompt` or `error`.
- No non-JSON lines on stdout (send debug to stderr).

## 8. Debugging

| Symptom | Cause | Fix |
| --- | --- | --- |
| Plugin not in picker | Not executable, or skipped | `chmod +x`; check reload toast |
| `project-layer plugin skipped` | `allowProjectPlugins` false | Set it true in `~/.pi/agent/prompto.json` |
| `describe timed out after 5s` | Slow describe | Cache results, fail fast, or move slow I/O to render |
| `plugin timed out after 60s` | Slow render | Emit `log` frames for progress; optimize; or `error` out |
| `exited without a prompt frame` | Crashed or no terminal frame | Check stderr tail in the toast; add a `prompt`/`error` |
| Choices are stale | `describe` cached per session | `/prompto reload` re-runs describe |
| Bad JSON in prompt | Hand-rolled JSON | Use `jq`/`json.dumps` |

## 9. Patterns

### Computed choices (the main reason to use a plugin)

```python
"choices": existing_ticket_ids(req_cwd) or ["NO-TICKETS-FOUND"]
```

Run at `describe` time so the form offers live values. Re-run with
`/prompto reload` when the underlying data changes.

### Multi-template plugin

```python
def describe():
    print(json.dumps({"type":"template","name":"close-ticket",...}))
    print(json.dumps({"type":"template","name":"ticket-status",...}))
    print(json.dumps({"type":"end"}))

def render():
    req = json.loads(sys.stdin.readline())
    if req["template"] == "close-ticket":   ...
    elif req["template"] == "ticket-status": ...
    else: print(json.dumps({"type":"error","message":f"unknown template {req['template']!r}"}))
```

### Progress reporting

Emit `log` frames during long renders — they show as a working status
message:

```python
print(json.dumps({"type":"log","message":"querying docmgr…"}))
# ... do work ...
print(json.dumps({"type":"prompt","text":result}))
```

### Graceful failure

```python
try:
    result = expensive_lookup()
except Exception as e:
    print(json.dumps({"type":"error","message":f"lookup failed: {e}"}))
    sys.exit(0)   # still exit 0; the error frame is the signal
```

Exit 0 even on logical failure — the `error` frame is the terminal signal.
Non-zero exit is treated as a crash and reported without your message.

## 10. Done checklist

- [ ] File is executable (`chmod +x`) and in a prompts layer.
- [ ] `--describe` emits one `template` per template, then `end`, in <5s.
- [ ] Field names use `[a-zA-Z_]\w*` (no dashes); template names may use dashes.
- [ ] `choices` for choice/multichoice fields (computed is fine).
- [ ] Render reads one stdin line, emits `log`* then one `prompt`/`error`, in <60s.
- [ ] JSON built with a real builder (no hand-rolled strings).
- [ ] Unknown `template` value returns an `error` frame.
- [ ] Tested manually with the §7 commands.
- [ ] `/prompto reload` shows the plugin in the toast.
- [ ] End-to-end `/prompto <group>/<name>` works.
