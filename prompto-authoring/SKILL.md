---
name: prompto-authoring
description: "Author, edit, and debug prompto prompts, templates, and plugins for the pi coding agent. Use when the user asks to create/add/write a prompto template or plugin, fill in a prompto form, fix a 'unknown placeholder' / 'prefill skipped' / 'project-layer plugin skipped' error, choose between plain vs template vs plugin, or understand the prompto rendering dialect ({{name}}, {{#if}}) or the JSONL plugin protocol."
---

# Prompto Authoring

## Overview

Prompto is a pi extension that turns reusable prompt fragments into a
form-driven workflow. A user types `/prompto`, picks a prompt from a
filterable list, fills in a generated modal form, and the prompt is
expanded into the editor (or sent to the agent).

There are **three kinds** of prompto prompts, discovered from two
**layers**:

| Kind | What | When to use |
| --- | --- | --- |
| `plain` | A file, no `fields:`/`prefill:` frontmatter | No parameters |
| `template` | Markdown + YAML frontmatter `fields:` + tiny dialect body | Named fields, light conditionals |
| `plugin` | Executable speaking a two-phase JSONL protocol | Computed content, live data, real logic |

| Layer | Path | Plugin policy |
| --- | --- | --- |
| project | `<cwd>/.pi/prompts/**` (travels with repo) | needs `allowProjectPlugins: true` in `~/.pi/agent/prompto.json` |
| global | `~/.pi/agent/prompts/**` (personal) | always allowed |

Project shadows global (same name wins). Addressable name = relative path,
extension stripped. Group = first path segment.

## Choosing a kind

- **No parameters** → `plain` (just drop a file).
- **Named fields + light `{{#if}}` conditionals** → `template`.
- **Need live data** (git state, ticket ids, HTTP) **or logic the dialect
  can't express** (loops, transforms) → `plugin`.

When in doubt, start with a `template`; promote to `plugin` only when you
hit the dialect's limits or need computed `choices`.

## Authoring a plain prompt

1. Create a file under `.pi/prompts/<group>/<name>.md` (project) or
   `~/.pi/agent/prompts/<group>/<name>.md` (global).
2. Write the prompt text as the body. No frontmatter.
3. `/prompto reload` → pick it from `/prompto` — contents pasted verbatim.

## Authoring a template

```yaml
---
title: <short human title>
description: <one-line picker detail>
submit: editor | auto          # editor (default): review before send; auto: send
fields:
  - name: <[a-zA-Z_]\w*>        # NO dashes in field names
    label: <form label>         # optional; defaults to name
    type: string | text | boolean | choice | multichoice | number
    required: true | false
    help: <shown under field when focused>
    placeholder: <dim hint when empty>      # string/number only
    choices: [a, b, c]                       # required for choice/multichoice
    default: <type-matched>                 # multichoice default is a list: [a]
prefill:                       # optional
  fields: [<declared field names>]
  when: before-form | after-required        # default before-form
  prompt: |
    <instructions to the model; may use {{placeholders}} from known values>
---
<body with {{name}} and {{#if}} blocks>
```

### Field types

| type | edit | default seed | renders as |
| --- | --- | --- | --- |
| `string` | inline single-line | `""` | the value |
| `text` | Enter → nested editor | `""` | the value |
| `boolean` | Space toggles | `false` | `true`/`false` |
| `number` | inline | `0` | the value |
| `choice` | ←→ cycle | `choices[0]` | the value |
| `multichoice` | ←→ move, Space toggle | `[]` | `a, b` (comma-joined) |

### Rendering dialect (the whole thing)

```
{{name}}                       # value; multichoice→"a, b"; bool→"true"/"false"
{{#if name}}…{{/if}}           # keep if truthy (non-empty/non-zero/true)
{{#if name == "lit"}}…{{/if}}  # keep if string-form == "lit"
{{#if name != "lit"}}…{{/if}}  # keep if !=
```

- **No nesting, loops, filters, expressions.** Unknown `{{name}}` or
  `{{#if name}}` → **error** at expand time. Dropped `{{#if}}` blocks also
  drop their trailing newline.
- Prefill proposals land **in the form for review** — never straight into
  the prompt. `after-required` asks required fields first so the prefill
  prompt can reference them (`{{goal}}`).
- Prefill soft-fails to `{}` on: no model, no API key, abort, bad output.
  The form always opens.

### Test + iterate

```
/prompto reload          # rescan; check the toast for issues/shadowed
/prompto <name>          # run end-to-end
```

Inspect remembered values: `cat ~/.pi/agent/prompto-state/*.json`. Reset a
template's memory by deleting its `values[<name>]` key.

## Authoring a plugin

A plugin is any **executable** file in a prompts layer. It speaks JSONL in
two independent, short-lived invocations (no daemon, no handshake):

```
Phase 1 — DESCRIBE (scan time, cached per session, 5s timeout)
   plugin --describe   →   one {"type":"template",...} per line, then {"type":"end"}

Phase 2 — RENDER (expand time, once per expansion, 60s timeout)
   stdin  →  {"type":"render","template":"<name>","values":{...},"cwd":"..."}
   stdout ←  {"type":"log","message":"..."}            (zero or more, optional)
          ←  {"type":"prompt","text":"<full prompt>"}   (terminal: success)
          ←  {"type":"error","message":"<reason>"}      (terminal: failure)
```

### Describe frame

```json
{"type":"template","name":"<[-a-zA-Z0-9_]>","title":"...","description":"...",
 "fields":[<same schema as template fields>],"submit":"editor"|"auto","prefill":{...}}
{"type":"end"}
```

- `name` allows dashes (unlike field names).
- `fields` use the **same schema** as template frontmatter.
- **`choices` can be computed at scan time** — the killer feature (live
  ticket ids, git branches, files in a dir). Re-run `/prompto reload` to
  refresh.
- stderr is never parsed — log freely there. Junk lines / unknown frame
  types are skipped (forward compat).
- Env vars `PROMPTO_TEMPLATE` and `PROMPTO_PLUGIN_PATH` are set on render.

### Minimal python plugin

```python
#!/usr/bin/env python3
import json, sys
if "--describe" in sys.argv:
    print(json.dumps({"type":"template","name":"hello",
        "fields":[{"name":"who","type":"string","required":True}]}))
    print(json.dumps({"type":"end"})); sys.exit(0)
req = json.loads(sys.stdin.readline())
print(json.dumps({"type":"prompt","text":f"Say hello to {req['values']['who']}!"}))
```

Install: copy into a prompts layer + `chmod +x`. The extension detects
plugins by the executable bit.

### Build JSON safely

**Never hand-roll JSON for the prompt text.** Use a builder so newlines,
quotes, and backslashes escape correctly:

```bash
# bash: jq -cn
jq -cn --arg focus "$focus" --arg diff "$diff" \
  '{type:"prompt", text:("Review this diff (focus: " + $focus + "):\n```diff\n" + $diff + "\n```")}'

# python: json.dumps
print(json.dumps({"type":"prompt","text":f"Review {values['ticket']}"}))
```

Unescaped characters in hand-built JSON break the JSONL line and the
extension rejects with `exited without a prompt frame`.

### Test a plugin manually before using

```bash
./my.plugin --describe | jq .                                    # describe phase
echo '{"type":"render","template":"hello","values":{"who":"world"},"cwd":"."}' | ./my.plugin   # render phase
```

Confirm: describe emits one `template` per template then `end`; render
emits `log`* then exactly one `prompt`/`error`; no non-JSON on stdout.

## Diagnostics

| Symptom | Fix |
| --- | --- |
| Template missing from picker | `/prompto reload`; read warnings in the toast |
| `unknown placeholder {{name}}` | declare the field, or fix/remove the placeholder |
| `prefill skipped: no model` | select a model |
| `prefill skipped: no API key` | configure the current model's API key |
| `prefill skipped: model did not return a JSON object` | tighten the prefill prompt; check `prefill.fields` |
| project plugin skipped | set `allowProjectPlugins: true` in `~/.pi/agent/prompto.json` |
| `describe timed out after 5s` | cache/fail-fast slow I/O; move slow work to render |
| `plugin timed out after 60s` | emit `log` frames for progress; optimize; or `error` out |
| `exited without a prompt frame` | add a `prompt`/`error` terminal frame; check stderr tail |
| Stale computed `choices` | `/prompto reload` re-runs `describe` |
| Shadowed name warning | a project template overwrote a global one — intended? |

## Config (`~/.pi/agent/prompto.json`, all optional)

```json
{ "submitDefault": "editor", "allowProjectPlugins": false, "prefillMaxTokens": 1024 }
```

## Commands & shortcuts

| Input | Effect |
| --- | --- |
| `/prompto` | Picker → expand into editor (replace text) |
| `/prompto <name>` | Expand a specific template directly |
| `/prompto reload` | Rescan both layers + re-run plugin `describe` |
| `Ctrl+Alt+P` | Picker → paste at cursor (preserve draft) |

## Reference

Load these for the full picture (each is self-contained):

- **`references/intern-guide.md`** — the canonical intern guide: mental
  model, every subsystem (store, parsing, rendering, plugin protocol,
  prefill, value memory, config, runtime, UI), authoring deep-dives, test
  architecture, full API reference, file map, glossary, onboarding
  checklist, and 7 decision records. **Read this before refactoring the
  extension itself.**
- **`references/author-a-template.md`** — step-by-step template authoring
  checklist (keep open while typing).
- **`references/author-a-plugin.md`** — step-by-step plugin authoring
  checklist with python/bash skeletons.
- **`references/quick-reference.md`** — one-page cheat sheet (dialect,
  field schema, prefill schema, protocol frames, commands, paths).

## Where to find real examples

- Templates: `.pi/prompts/{demo,docmgr,obsidian,research,workflow}/*.md`
  in the `2026-04-21--pi-extensions` repo (5 real templates, incl. an
  `after-required` prefill example).
- Plugins: `extensions/prompto/examples/git-diff.plugin.sh` (bash,
  single-template) and `extensions/prompto/examples/tickets.plugin.py`
  (python, multi-template, computed choices).
