# Prompto — Quick Reference Card

## Three kinds

| Kind | What | When |
| --- | --- | --- |
| `plain` | A file, no `fields:`/`prefill:` frontmatter | No parameters |
| `template` | Markdown + YAML frontmatter `fields:` + tiny dialect body | Named fields, light conditionals |
| `plugin` | Executable, JSONL protocol | Computed content, live data, real logic |

## Two layers

| Layer | Path | Plugin policy |
| --- | --- | --- |
| project | `<cwd>/.pi/prompts/**` | needs `allowProjectPlugins: true` |
| global | `~/.pi/agent/prompts/**` | always allowed |

Project shadows global (same name). Addressable name = rel path, ext stripped. Group = first segment.

## Commands / shortcuts

| Input | Effect |
| --- | --- |
| `/prompto` | Open picker, expand into editor (replace text) |
| `/prompto <name>` | Expand a specific template |
| `/prompto reload` | Rescan both layers + re-run plugin `describe` |
| `Ctrl+Alt+P` | Picker, paste at cursor (preserve draft) |
| `/px` → Prompto | Launcher entry; default action = expand |

## Template frontmatter

```yaml
---
title: <string>
description: <string>
submit: editor | auto          # editor=review (default), auto=send
fields:
  - name: <[a-zA-Z_]\w*>       # NO dashes
    label: <string>
    type: string | text | boolean | choice | multichoice | number
    required: true | false
    help: <string>
    placeholder: <string>      # string/number
    choices: [a, b, c]         # required for choice/multichoice
    default: <type-matched>    # multichoice default is a list: [a]
prefill:                       # optional
  fields: [<declared names>]
  when: before-form | after-required    # default before-form
  prompt: |
    <instructions; may use {{placeholders}}>
---
<body>
```

## Field types at a glance

| type | inline edit? | default seed | render form |
| --- | --- | --- | --- |
| `string` | yes (single line) | `""` | the value |
| `text` | Enter → nested editor | `""` | the value |
| `boolean` | Space toggles | `false` | `true`/`false` |
| `number` | yes | `0` | the value |
| `choice` | ←→ cycle | `choices[0]` | the value |
| `multichoice` | ←→ move, Space toggle | `[]` | `a, b` |

## Rendering dialect (the whole thing)

```
{{name}}                       # value; multichoice→"a, b"; bool→"true"/"false"
{{#if name}}…{{/if}}           # keep if truthy (non-empty/non-zero/true)
{{#if name == "lit"}}…{{/if}}  # keep if string-form == "lit"
{{#if name != "lit"}}…{{/if}}  # keep if !=
```

- No nesting, loops, filters, expressions.
- Unknown `{{name}}` or `{{#if name}}` → **error** at expand time.
- Dropped `{{#if}}` block drops its trailing newline too.

## Plugin JSONL protocol

**Describe** — `plugin --describe`, stdout, 5s, exit 0:

```
{"type":"template","name":"<[-a-z0-9_]>","title":"...","description":"...",
 "fields":[<same as template>],"submit":"editor"|"auto","prefill":{...}}
{"type":"end"}
```

**Render** — stdin gets one line, 60s, respond with terminal frame:

```
→ {"type":"render","template":"<name>","values":{...},"cwd":"..."}
← {"type":"log","message":"..."}              # zero or more (optional)
← {"type":"prompt","text":"<full prompt>"}   # terminal: success
← {"type":"error","message":"<reason>"}      # terminal: failure
```

- Env: `PROMPTO_TEMPLATE`, `PROMPTO_PLUGIN_PATH`. cwd = user's cwd.
- stderr never parsed. Junk lines / unknown types skipped.
- Build JSON with `jq`/`json.dumps` — never hand-roll.

## Prefill precedence (low → high)

```
defaultValues  →  loadRememberedValues  →  runPrefill  →  openForm (user edits)
```

- `after-required` asks required fields first, so the prefill prompt can
  reference them (`{{goal}}`).
- Soft-fails to `{}` on: no model, no key, abort, bad output. Form always opens.

## Value memory

- Path: `~/.pi/agent/prompto-state/<sha256(cwd)[0:16]>.json`
- Never inside the repo (no accidental commits).
- Filters to declared fields on load+save (drift-safe).
- Reset: delete `values[<template-name>]` key, or the file.

## Config (`~/.pi/agent/prompto.json`, all optional)

```json
{ "submitDefault": "editor", "allowProjectPlugins": false, "prefillMaxTokens": 1024 }
```

## Diagnostics

| Symptom | Fix |
| --- | --- |
| Template missing | `/prompto reload`; read warnings |
| `unknown placeholder` | declare the field or remove `{{name}}` |
| `prefill skipped` | select a model / set its API key |
| project plugin skipped | `allowProjectPlugins: true` |
| plugin timeout | optimize; cache describe; emit `log` for progress |
| `exited without prompt frame` | add a `prompt`/`error` frame; check stderr |

## Key files

```
extensions/prompto/{index,store,template,plugin,plugin-protocol,prefill,prefill-parse,run,state,config,types}.ts
extensions/prompto/ui/{picker,form}.ts
extensions/prompto/docs/{authoring,plugin-protocol}.md
extensions/prompto/examples/{git-diff.plugin.sh,tickets.plugin.py}
extensions/prompto/tests/*.test.ts
```

## Test

```bash
bun test extensions/prompto/        # 65 tests
```
