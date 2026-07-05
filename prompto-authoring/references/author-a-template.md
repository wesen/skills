# Playbook — Author a Prompto Template

> Companion to §15 of `references/intern-guide.md`. This is the
> step-by-step checklist version: keep it open while you type.

## When to use a template (vs plain vs plugin)

- **Plain** if there are no parameters.
- **Template** if the prompt has named fields and light conditional logic.
- **Plugin** if you need computed content (live git state, ticket lists,
  HTTP) or branching logic the dialect cannot express.

## 0. Prerequisites

- The prompto extension is loaded (it is, in this repo).
- You know which layer: **project** (`.pi/prompts/`, travels with repo) or
  **global** (`~/.pi/agent/prompts/`, personal). Default to project.

## 1. Pick the addressable name

The name is the path relative to the layer dir, extension stripped. The
first segment is the group.

```
.pi/prompts/docmgr/create-ticket.md   →  /prompto docmgr/create-ticket  (group: docmgr)
.pi/prompts/greet.md                  →  /prompto greet                 (group: "")
```

Choose a group that organizes related prompts (`docmgr/`, `research/`,
`workflow/`). Avoid top-level names unless the prompt is generic.

## 2. Write the frontmatter

```yaml
---
title: <short human title>            # shown in picker + form header
description: <one-line picker detail>
submit: editor | auto                 # editor (default): review before send
                                      # auto: send straight to the agent
fields:
  - name: <field-name>                # [a-zA-Z_][a-zA-Z0-9_]*  (NO dashes)
    label: <form label>               # optional; defaults to name
    type: string | text | boolean | choice | multichoice | number
    required: true | false            # optional
    help: <shown under field when focused>      # optional
    placeholder: <dim hint when empty>          # optional, string/number
    choices: [a, b, c]                # REQUIRED for choice/multichoice
    default: <value>                  # optional, type-checked
---
```

Field-type quick guide:

| Type | Use | Default seed |
| --- | --- | --- |
| `string` | single-line value | `""` |
| `text` | multi-line / long; Enter opens a nested editor | `""` |
| `boolean` | on/off | `false` |
| `number` | numeric | `0` |
| `choice` | one of `choices` | `choices[0]` |
| `multichoice` | any subset of `choices` | `[]` |

## 3. (Optional) Add prefill

Prefill lets the model propose values for a subset of fields before the
form opens.

```yaml
prefill:
  fields: [<declared field names the model may fill>]
  when: before-form | after-required   # default: before-form
  prompt: |
    <instructions to the model; may use {{placeholders}} from known values>
```

- Use `after-required` when the prefill prompt should reference a required
  field (e.g. derive a title from the goal). The required fields are asked
  first in a mini-form.
- `prompt` is rendered with the strict dialect — unknown `{{name}}` throws.
- Keep `fields` tight: only the fields the model has good signal for.

## 4. Write the body

Use `{{name}}` substitution and `{{#if}}` conditionals.

```
Goal: {{goal}}

{{#if depth == "full"}}
Be exhaustive: architecture, evidence, risks, phased plan.
{{/if}}
{{#if depth == "light"}}
Keep it light: one page of scope, approach, risks.
{{/if}}
{{#if uploadRemarkable}}
Upload the result to reMarkable when done.
{{/if}}
```

Dialect rules (the whole dialect):

- `{{name}}` → value. `multichoice` joins as `a, b`. Booleans → `true`/`false`.
- `{{#if name}}…{{/if}}` → kept when truthy (non-empty/non-zero/true).
- `{{#if name == "lit"}}…{{/if}}` / `!=` → string comparison.
- **No nesting, loops, filters, expressions.** Unknown placeholders error.
- A dropped `{{#if}}` block also drops its trailing newline (no blank lines).

## 5. Reload and test

```
/prompto reload
```

Check the toast for issues:

- `N templates loaded` — good.
- `shadowed: <name>` — you overrode a global; intended?
- Per-line warnings — fix the cited file (parse error with path + message).

Then run it:

```
/prompto <name>
```

Walk through: defaults → (prefill mini-form if `after-required`) → prefill
loader → full form → submit → expanded prompt in editor (or sent, if
`submit: auto`).

## 6. Iterate

- Add `help:` to any field an intern might not understand.
- Add `placeholder:` to show the expected format.
- If a conditional should always/never apply, reconsider the field.
- Check `~/.pi/agent/prompto-state/*.json` to see what was remembered;
  delete a `values[<name>]` key to reset a template's memory.

## 7. Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Dash in field `name` | parse error at scan | use `_` not `-` |
| `{{foo}}` in body but no field `foo` | `unknown placeholder` at expand | declare the field or remove the placeholder |
| `prefill.fields: [foo]` but `foo` undeclared | parse error at scan | declare `foo` or drop from prefill |
| `default: b` for a `choice` where `b` not in `choices` | parse error | add `b` to `choices` or change default |
| Nested `{{#if}}` | inner `{{/if}}` closes the outer | split into sibling blocks or use a plugin |
| `multichoice` default as scalar | parse error | use a list: `default: [a]` |
| `text` for one word | clunky nested editor for tiny input | use `string` |

## 8. Done checklist

- [ ] File under `.pi/prompts/<group>/<name>.md` (or global).
- [ ] Frontmatter parses (no `/prompto reload` warnings).
- [ ] Every `{{placeholder}}` in the body has a declared field.
- [ ] Required fields are marked `required: true`.
- [ ] `help:` on non-obvious fields.
- [ ] `submit` set intentionally (`editor` to review, `auto` to send).
- [ ] Prefill (if any) references only known fields and proposes only
      declared `prefill.fields`.
- [ ] Tested by running `/prompto <name>` end-to-end.
- [ ] (If shared) committed to the repo's `.pi/prompts/`.
