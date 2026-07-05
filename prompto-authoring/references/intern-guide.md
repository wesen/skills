# Prompto — An Intern-Ready Analysis, Design & Implementation Guide

> This is the canonical intern guide for the `prompto` pi extension. It
> explains *what prompto is*, *why it is shaped the way it is*, and *how every
> subsystem works*, with prose, bullet lists, pseudocode, diagrams, API
> references, and concrete file paths. By the end you should be able to
> author a plain prompt, a templated prompt, and a JSONL plugin, and review
> changes to the extension itself.
>
> Diagrams in this guide are ASCII art inside fenced code blocks. They render
> identically in the markdown viewer, the terminal, and the reMarkable PDF.
> Every code reference points at a real file under
> `extensions/prompto/` (relative to the repository root at
> `/home/manuel/code/wesen/2026-04-21--pi-extensions`).

## 0. Table of contents

- Part I — Orientation
  - 1. Executive summary
  - 2. Problem statement and design philosophy
  - 3. Mental model: the three kinds and two layers
- Part II — System architecture
  - 4. Extension layout and registration
  - 5. The discovery pipeline (`store.ts`)
  - 6. Template parsing (`frontmatter.ts`, `template.ts`)
  - 7. The rendering dialect (`template.ts`)
  - 8. The JSONL plugin protocol (`plugin-protocol.ts`, `plugin.ts`)
  - 9. LLM-assisted prefill (`prefill.ts`, `prefill-parse.ts`)
  - 10. Value memory (`state.ts`)
  - 11. Configuration (`config.ts`)
  - 12. The runtime orchestrator (`run.ts`)
  - 13. The UI layer (`ui/picker.ts`, `ui/form.ts`)
- Part III — Authoring
  - 14. Authoring a plain prompt
  - 15. Authoring a template
  - 16. Authoring a plugin
- Part IV — Testing & operations
  - 17. Test architecture
  - 18. Operations & diagnostics
- Part V — Reference
  - 19. API reference (types & contracts)
  - 20. File map
  - 21. Glossary
  - 22. Intern onboarding checklist
  - 23. Decision records

---

# Part I — Orientation

## 1. Executive summary

Prompto is a pi extension that turns reusable prompt fragments into a
first-class, form-driven workflow. A user types `/prompto`, picks a prompt
from a filterable list, fills in a generated modal form, and the prompt is
expanded and dropped into the editor (or sent directly to the assistant).
The expanded prompt is plain text; the *templating* lives in how it was
produced.

Prompto supports three kinds of prompts:

- **Plain** — any file in a prompts directory with no `fields:`/`prefill:`
  frontmatter. Selecting it pastes the file contents verbatim. No form.
- **Template** — a Markdown file with YAML frontmatter that declares
  `fields:` (and optionally `prefill:`). The body is a tiny, deliberately
  limited templating dialect (`{{name}}`, `{{#if name}}…{{/if}}`). A form
  is generated from the fields and the body is rendered with the submitted
  values.
- **Plugin** — an executable file (any language) that speaks a short JSONL
  protocol over stdin/stdout. Used when a prompt needs computed content
  (live git state, existing ticket ids, network lookups, multi-step logic).

Templates and plugins are discovered from two layered directories:

- **Project layer** — `<project>/.pi/prompts/**`, travels with the repo,
  shared with teammates via git.
- **Global layer** — `~/.pi/agent/prompts/**`, personal, crosses projects.

Project entries shadow global entries with the same addressable name. After
adding or editing files, `/prompto reload` rescans.

Prompto is registered through the shared pi extension framework
(`extensions/_shared/registry.ts`), so it surfaces through the `/px`
launcher, the command palette, two docs entries, a default action, and the
`/prompto` slash command plus a `Ctrl+Alt+P` paste shortcut.

The extension is small: ~13 TypeScript files, ~65 tests, all passing. It
has no runtime dependencies beyond `yaml` (for frontmatter) and the pi /
pi-tui packages. The design is deliberately conservative — small parsing
surface, strict rendering, soft-failing optional features — so prompts stay
auditable and the extension stays maintainable.

## 2. Problem statement and design philosophy

### 2.1 The problem

Coding agents are most effective when given high-quality, structured
prompts. In practice, users accumulate prompt fragments in notes, shell
history, or clipboard managers and paste them with manual edits each time.
This has four failure modes:

1. **Drift** — the "real" version of a prompt lives in someone's head; the
   copy in the repo goes stale.
2. **Cargo-cult editing** — users copy a long prompt and only change one
   field, but never learn which parts are parameters.
3. **No validation** — required context is missing; the agent flails.
4. **No reuse signal** — there is no way to see "what prompts do I have?"

Prompto addresses these by making prompts *named, declared, form-driven
artifacts* with project/global layering, computed choices, and value
memory.

### 2.2 Design philosophy

Five principles, each visible in the code, shape every decision:

- **P1 — Tiny templating dialect.** `{{name}}` and `{{#if …}}…{{/if}}` are
  the entire surface. No loops, no filters, no nesting. Unknown
  placeholders are a hard error at expand time. Prompts that need real
  logic become plugins. This keeps templates auditable and forces complex
  behavior into testable code.
- **P2 — Strict parse, soft-fail runtime.** Template *structure* errors
  (bad field type, unknown prefill field, duplicate name) throw at scan
  time and are reported as warnings. *Runtime* optional features (prefill,
  value memory) never fail the expansion: they degrade to an unprefilled
  form with a warning. The user always gets a working form.
- **P3 — Plugins are short-lived, stateless subprocesses.** No daemon, no
  handshake, no shared state. The extension spawns the plugin twice: once
  with `--describe` (scan time) and once with a render request on stdin
  (expand time). This is trivially testable and language-agnostic.
- **P4 — User secrets never land in the worktree.** Value memory (last
  submitted values, which may contain sensitive prompt text) is stored
  under `~/.pi/agent/prompto-state/`, keyed by a hash of the project
  directory — never inside the user's repository.
- **P5 — Forward compatibility by skipping.** The JSONL protocol ignores
  unknown frame `type`s and junk stdout lines. New plugin features can be
  added without breaking old plugins, and chatty plugins do not crash the
  extension.

### 2.3 What prompto is *not*

- Not a general templating engine (no Jinja/Mustache loops/filters).
- Not a prompt *runner* — it expands text; the agent runs the prompt.
- Not a chat-template system for model providers; it produces user-facing
  prompt strings.
- Not a dependency-injection framework; plugins are plain executables.

## 3. Mental model: the three kinds and two layers

### 3.1 The three kinds at a glance

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        /prompto  (user invocation)                       │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                          store.list() / store.resolve(name)
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │  kind: "plain"   │    │ kind: "template"  │    │  kind: "plugin"  │
   │  no frontmatter  │    │  YAML frontmatter │    │  executable file │
   │  (or no fields)  │    │  fields: [...]    │    │  JSONL protocol  │
   └────────┬─────────┘    └────────┬──────────┘    └────────┬─────────┘
            │                       │                        │
            │                  collectValues()        collectValues()
            │                  (form + prefill)      (form + prefill)
            │                       │                        │
            ▼                       ▼                        ▼
     read file verbatim      renderTemplate(body,        renderViaPlugin(
     → prompt string           values) → prompt string     values) → prompt
            │                       │                        │
            └───────────────────────┴────────────────────────┘
                                     │
                          output: replace-editor
                                  | paste-editor
                                  | send
                                     ▼
                          editor text / agent message
```

### 3.2 The two layers

| Layer | Directory | Lifetime | Sharing | Plugin policy |
| --- | --- | --- | --- | --- |
| Project | `<cwd>/.pi/prompts/**` | Travels with repo | Via git | Requires `allowProjectPlugins: true` |
| Global | `~/.pi/agent/prompts/**` | Permanent, machine-wide | Personal | Always allowed |

The store scans **global first, project second**. Same-named templates
from the project layer overwrite the global ones; overwritten names are
recorded in `ScanResult.shadowed` and surfaced as a warning. The group
(the first path segment of the addressable name, e.g. `docmgr` in
`docmgr/create-ticket`) is derived from the directory *under the layer
root*, not from the file's absolute path.

### 3.3 The lifecycle of one expansion

```
1. /prompto [name]            user types the command (or picks via /px)
2. store.ensureLoaded(cwd)    lazy first scan, cached per session
3. store.resolve(name)        or openPicker() if no name given
4. expandTemplate(template):
     plain     → readFileSync(filePath)
     template  → collectValues() then renderTemplate(body, values)
     plugin    → collectValues() then renderViaPlugin(template, values)
5. collectValues():
     seed = defaultValues(fields)        # from `default:` keys
     seed += loadRememberedValues(cwd)   # ~/.pi/agent/prompto-state/<hash>.json
     if prefill.when == "after-required":
         pass1 = openForm(required fields only)   # ask required first
         seed += pass1
     if prefill: seed += runPrefill(...)            # LLM proposes; soft-fail
     values = openForm(all fields, seed)            # user reviews & edits
     saveRememberedValues(cwd, template, values)
6. output:
     "replace-editor" → ctx.ui.setEditorText(prompt)   # default for submit:editor
     "paste-editor"   → ctx.ui.pasteToEditor(prompt)    # Ctrl+Alt+P
     "send"           → pi.sendUserMessage(prompt)      # default for submit:auto
```

This lifecycle is the single most important diagram in the guide. Every
subsystem that follows is a refinement of one of these steps.

---

# Part II — System architecture

## 4. Extension layout and registration

### 4.1 File map of the extension

```
extensions/prompto/
├── index.ts              # entrypoint: registerPiExtension, /prompto command, Ctrl+Alt+P
├── config.ts             # ~/.pi/agent/prompto.json reader + path helpers
├── frontmatter.ts        # fence splitting + YAML parsing (uses `yaml` package)
├── template.ts           # parseTemplate, parseFields, parsePrefill, renderTemplate
├── types.ts              # PromptTemplate, TemplateField, PromptoConfig, etc.
├── store.ts              # PromptStore: layered scan, shadowing, plugin describer wiring
├── plugin.ts             # subprocess execution: describePlugin, renderViaPlugin
├── plugin-protocol.ts    # pure JSONL parsing: parseDescribeOutput, parseRenderLine, buildRenderRequest
├── prefill.ts            # runPrefill: LLM call + BorderedLoader overlay
├── prefill-parse.ts      # buildSystemPrompt, parseJsonObject, coerceValue (pure, bun-testable)
├── run.ts                # runPrompto orchestrator + expandTemplate + collectValues
├── state.ts              # value memory: load/save outside worktree, sha256(cwd) keying
├── docs/
│   ├── authoring.md      # short authoring guide (exposed via /px docs)
│   └── plugin-protocol.md# short protocol reference (exposed via /px docs)
├── examples/
│   ├── git-diff.plugin.sh   # reference single-template plugin (bash)
│   └── tickets.plugin.py    # reference multi-template plugin (python)
├── ui/
│   ├── picker.ts        # PromptoTemplatePicker: fuzzy filterable modal list
│   └── form.ts          # PromptFormComponent: schema-generated modal form
└── tests/
    ├── frontmatter.test.ts
    ├── template.test.ts
    ├── plugin.test.ts
    ├── prefill.test.ts
    └── state.test.ts
```

### 4.2 The registration (`index.ts`)

The entrypoint exports a default function `prompto(pi: ExtensionAPI)`. It
constructs a `PromptStore` (wired with `describePlugin` from `plugin.ts`),
then calls `registerPiExtension(...)` with the full contribution surface:

```ts
registerPiExtension({
  id: "prompto",
  name: "Prompto",
  description: "Prompt template expansion with modal forms (...)",
  commands: ["prompto"],
  tags: ["prompts", "templates", "forms"],
  run: (ctx) => runPrompto(pi, store, "", ctx),
  docs: [
    { id: "authoring",         title: "Authoring prompto templates", load: () => loadDoc("docs/authoring.md") },
    { id: "plugin-protocol",   title: "JSONL plugin protocol",       load: () => loadDoc("docs/plugin-protocol.md") },
  ],
  actions: [ /* expand, paste, reload */ ],
  palette: [ /* prompto-expand, prompto-paste */ ],
});
```

It also registers the `/prompto` slash command (with argument completions
that list template names sorted project-first then alphabetical, plus the
literal `reload`) and the `Ctrl+Alt+P` global shortcut for paste mode.

**Why the doc paths are relative.** `loadDoc(relativePath)` resolves
against `EXTENSION_DIR` (the directory of the compiled `index.ts`). Doc
paths in `registerPiExtension({ docs })` are ids, not filesystem paths —
the `load` function is what actually reads the file. This is the pattern
documented in `AGENTS.md`: doc ids are relative, never absolute.

### 4.3 The contribution surface

| Contribution | Used for | Where it surfaces |
| --- | --- | --- |
| `commands` | Muscle-memory slash command | `/prompto`, `/prompto <name>`, `/prompto reload` |
| `actions` | Launcher entry points | `/px` launcher, action picker |
| `palette` | Keyboard-driven menu | Command palette (`Ctrl+Shift+Alt+N`) |
| `docs` | In-app documentation | Docs viewer (markdown rendered) |
| `run` (top-level) | Default invocation when launcher just "opens" the extension | Launcher default |

The default action (`expand`) opens the picker and replaces editor text.
The `paste` action uses `output: "paste-editor"` to insert at the cursor
without destroying existing draft text — this is what `Ctrl+Alt+P` and the
palette item both call.

## 5. The discovery pipeline (`store.ts`)

The `PromptStore` is the single source of truth for which templates exist.
It is constructed once in `index.ts` and shared across every invocation.

### 5.1 Responsibilities

- Read `~/.pi/agent/prompto.json` for config.
- Walk the two layer directories (non-dotfiles, recursive).
- For each file: detect executable vs plain file, parse or describe.
- Resolve same-name shadowing (project wins; shadowed names recorded).
- Cache the result per session; `rescan` is explicit (`/prompto reload`).

### 5.2 Addressable naming

The addressable name is the file's path relative to its layer directory,
with the extension stripped. The group is the first `/`-separated segment:

```
<layer-dir>/docmgr/create-ticket.md   → name "docmgr/create-ticket", group "docmgr"
<layer-dir>/greet.md                  → name "greet",                 group ""
<layer-dir>/docmgr/sub/close.md       → name "docmgr/sub/close",      group "docmgr"
```

Implementation: `templateName()` in `store.ts`. Note the edge case — if
stripping the extension would leave an empty basename, the extension is
kept (a file literally named `.md` is already skipped as a dotfile, so
this is defensive).

### 5.3 `rescan` pseudocode

```
function rescan(cwd):
    config, warnings ← readConfig()
    issues ← warnings.map(toScanIssue)
    shadowed ← []
    pluginsRun ← []
    byName ← {}                          # name → PromptTemplate

    layers ← [
        { dir: globalPromptsDir,   source: "global"   },   # scanned FIRST
        { dir: projectPromptsDir(cwd), source: "project" }, # scanned SECOND → wins
    ]

    for layer in layers:
        for filePath in walk(layer.dir):       # non-dot files, recursive, sorted
            name  ← templateName(layer.dir, filePath)
            group ← name.split("/")[0] if "/" in name else ""

            if isExecutable(filePath):
                if no describePlugin wired:     issues.push("not supported"); continue
                if layer.source == "project" and not config.allowProjectPlugins:
                    issues.push("project plugin skipped"); continue
                pluginsRun.push(filePath)
                described ← describePlugin({filePath, group, source, submitDefault, cwd})
                for t in described.templates: addTemplate(byName, t, shadowed)
                for m in described.issues:     issues.push({filePath, m})
            else:
                content ← readFileSync(filePath)
                template ← parseTemplate({content, name, group, filePath, source, submitDefault})
                addTemplate(byName, template, shadowed)

    cache(byName, lastScan)
    return {count, issues, shadowed, pluginsRun}

function addTemplate(byName, template, shadowed):
    if byName.has(template.name): shadowed.push(template.name)   # record the loser
    byName.set(template.name, template)                          # last writer wins
```

Two non-obvious invariants:

1. **Global first, project second.** The project layer overwrites global
   entries with the same name. This is why `shadowed` is recorded: the user
   should know their project layer silently replaced a global template.
2. **Plugin executables are detected by the Unix executable bit** (`stat.mode
   & 0o111`). A `.md` file made `+x` would be treated as a plugin; a script
   without the executable bit is treated as a plain/template file and will
   fail to parse as Markdown. This is a deliberate, simple heuristic.

### 5.4 The `PluginDescriber` seam

`PromptStore` does not import `plugin.ts` directly. Instead the constructor
takes an optional `PluginDescriber`:

```ts
export type PluginDescriber = (options: {
  filePath: string; group: string; source: TemplateSource;
  submitDefault: "editor" | "auto"; cwd: string;
}) => Promise<{ templates: PromptTemplate[]; issues: string[] }>;
```

`index.ts` wires `describePlugin` (from `plugin.ts`) into the store. This
seam exists so the store is testable without spawning subprocesses, and so
the protocol layer (`plugin-protocol.ts`) stays pure (no `node:child_process`
imports — it can be loaded by `bun test` directly).

## 6. Template parsing (`frontmatter.ts`, `template.ts`)

### 6.1 `frontmatter.ts` — fence splitting and YAML

`splitFrontmatter(source)` splits a document into a `frontmatter` map and a
`body` string. The contract:

- A document must start with a `---\n` fence to be considered frontmatter
  (a leading BOM is stripped first).
- The closing fence is the next line matching `^---[ \t]*$`.
- An unterminated fence returns `{ frontmatter: undefined, body: source }`
  (treated as plain — never throws).
- The frontmatter text is parsed by `parseFrontmatter`, which uses the
  `yaml` package. The top level **must be a YAML map**; a scalar, list, or
  parse error throws `FrontmatterError`.

Why full YAML? Earlier versions used a hand-rolled parser and could not
handle block literals (`prompt: |`), inline arrays, or anchors. The repo's
`package.json` depends on `yaml`, and `frontmatter.test.ts` exercises
anchors, folded scalars, nested maps, and the `fields:` block-list-of-maps
shape. Tabs are rejected by `yaml` itself (surfaced as a parse error with
"tabs" in the message).

### 6.2 `parseTemplate` — kind detection

`parseTemplate` is the bridge between a file's raw content and a
`PromptTemplate` object. Its logic:

```
function parseTemplate({content, name, group, filePath, source, submitDefault}):
    base ← { name, group, submit: submitDefault, fields: [], body: content,
             filePath, source, kind: "plain" }

    try:
        { frontmatter, body } ← splitFrontmatter(content)
    catch e:
        throw TemplateError(filePath + ": " + e.message)

    if frontmatter is undefined:
        return base                          # PLAIN: no fence at all

    template ← { ...base, body, kind: "template" }
    if frontmatter.title is string:       template.title = it
    if frontmatter.description is string: template.description = it
    if frontmatter.submit defined:
        if not in {editor, auto}: throw TemplateError
        template.submit = frontmatter.submit
    template.fields  ← parseFields(frontmatter.fields, filePath)
    template.prefill ← parsePrefill(frontmatter.prefill, template.fields, filePath)
    return template
```

The kind is `plain` when there is no frontmatter. Note: a document *with*
frontmatter but *without* `fields:`/`prefill:` is still `kind: "template"`
— it just has an empty fields list, so `collectValues` returns the seed
immediately and the body is rendered with no values (placeholders in the
body would then error). In practice, authors who want a "no form, just
structured metadata" prompt should use `plain`.

### 6.3 `parseFields` — the field schema

Each field is a YAML map with at least a `name`. Validation rules:

- `name` — required, must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/`. Duplicate
  names throw. (Note: this is **stricter** than plugin template names, which
  allow `-`.)
- `type` — optional, defaults to `"string"`. Must be one of
  `string | text | boolean | choice | multichoice | number`.
- `choices` — required and non-empty string list for `choice`/`multichoice`.
- `default` — optional; validated against the type:
  - `string`/`text`: accepts string, or number (stringified).
  - `boolean`: must be boolean.
  - `number`: must be a number.
  - `choice`: must be a string present in `choices`.
  - `multichoice`: must be a string list, every element in `choices`.
- `label`, `help`, `placeholder` — optional strings.
- `required` — optional boolean.

### 6.4 `parsePrefill` — the prefill spec

`prefill:` is an optional map:

```yaml
prefill:
  fields: [ticketTitle, ticketId]   # required, non-empty list of declared field names
  when: after-required              # optional: before-form (default) | after-required
  prompt: |                         # required, non-empty string; rendered with current values
    Propose a title for: {{goal}}
```

Validation:

- `prompt` must be a non-empty string.
- `fields` must be a non-empty string list, and **every name must be a
  declared field** — referencing an unknown field throws. This catches
  typos that would silently make prefill a no-op.
- `when` must be `before-form` or `after-required` if present.

The `prompt` string is itself a template body, rendered with
`renderTemplate` against the values known so far (see §9).

### 6.5 `defaultValues` — seeding the form

`defaultValues(fields)` builds the initial value map before the form opens:

- If `field.default` is set, use it.
- Otherwise seed with the type's zero value:
  - `string`/`text` → `""`
  - `boolean` → `false`
  - `number` → `0`
  - `choice` → `choices[0]` (or `""` if empty, though empty choices is
    already a parse error)
  - `multichoice` → `[]`

These defaults are the baseline; remembered values and prefill proposals
layer on top (prefill wins over remembered — see §9.4).

## 7. The rendering dialect (`template.ts`)

`renderTemplate(body, values)` is the entire templating engine. It is
~25 lines and intentionally incapable of anything beyond substitution and
conditional blocks.

### 7.1 The dialect

| Construct | Meaning |
| --- | --- |
| `{{name}}` | The field's value. `multichoice` joins as `a, b`. Booleans render `true`/`false`. |
| `{{#if name}}…{{/if}}` | Keep the inner block when `name` is truthy. |
| `{{#if name == "lit"}}…{{/if}}` | Keep when the value's string form equals the literal. |
| `{{#if name != "lit"}}…{{/if}}` | Keep when not equal. |

That is the whole dialect. There are **no** loops, filters, partials,
nesting, or expression evaluation.

### 7.2 Truthiness rules

`truthy(value)` is defined as:

- Array → `length > 0`
- String → `trim() !== ""`
- Number → `!== 0`
- Boolean → the value itself

This makes `{{#if uploadRemarkable}}` work for booleans, and
`{{#if topics}}` work for a multichoice that the user left empty. The
equality operators compare the **formatted string form** of the value
(`formatValue`), so a `multichoice` of `["a", "b"]` compares against the
string `"a, b"`.

### 7.3 Strict mode

Both `{{unknown}}` and `{{#if unknown}}` throw `TemplateError` at expand
time. This is deliberate: a prompt that silently swallowed an unknown
placeholder would produce subtly broken output. The error surfaces in the
UI as a `notify("error")` toast and the expansion aborts.

### 7.4 The regex pipeline

```
function renderTemplate(body, values):
    # Pass 1: replace conditional blocks
    withConditionals ← body.replace(IF_BLOCK_RE, (all, name, op, literal, inner):
        if name not in values: throw TemplateError("unknown field in #if " + name)
        value ← values[name]
        if op:
            unescaped ← literal.replace(/\\(.)/g, "$1")    # allow \" inside literals
            keep ← (op == "==") ? (formatValue(value) == unescaped)
                               : (formatValue(value) != unescaped)
        else:
            keep ← truthy(value)
        return keep ? inner : "")

    # Pass 2: substitute placeholders
    return withConditionals.replace(PLACEHOLDER_RE, (all, name):
        if name not in values: throw TemplateError("unknown placeholder " + name)
        return formatValue(values[name]))
```

Two regexes:

- `IF_BLOCK_RE = /\{\{#if\s+([a-zA-Z_]\w*)\s*(?:(==|!=)\s*"((?:[^"\\]|\\.)*)"\s*)?\}\}\r?\n?([\s\S]*?)\{\{\/if\}\}\r?\n?/g`
  — note the trailing `\r?\n?`: when a conditional block is *dropped*, its
  trailing newline is also dropped so you do not get blank lines where the
  block was.
- `PLACEHOLDER_RE = /\{\{([a-zA-Z_]\w*)\}\}/g`

### 7.5 Why no nesting?

`[\s\S]*?` is non-greedy, so `{{#if a}}...{{#if b}}...{{/if}}...{{/if}}`
would match the inner `{{/if}}` as the terminator of the outer block. A
nested-aware engine would need a real parser. The dialect bans nesting
instead; if you need branching logic, write a plugin.

## 8. The JSONL plugin protocol (`plugin-protocol.ts`, `plugin.ts`)

Plugins are for prompts that need **computed content** — live git state,
existing ticket ids, HTTP lookups, multi-step transformations. A plugin is
any executable file in a prompts layer.

### 8.1 The two-phase, stateless model

The extension spawns the plugin exactly twice per "use", in independent
short-lived processes:

```
Phase 1 — DESCRIBE (scan time, cached per session)
   extension ──►  plugin --describe          (no stdin, 5s timeout)
   extension  ◄──  {"type":"template",...}  (one per line)
               ◄──  {"type":"end"}

Phase 2 — RENDER (expand time, once per expansion)
   extension ──►  {"type":"render","template":...,"values":{...},"cwd":"..."}  (stdin, then closed)
   extension  ◄──  {"type":"log","message":"..."}   (zero or more, optional progress)
               ◄──  {"type":"prompt","text":"..."}   (terminal — success)
            OR ◄──  {"type":"error","message":"..."}  (terminal — failure)
```

There is no daemon, no handshake, no shared state between the two phases.
This makes plugins trivially testable (pipe stdin, read stdout) and
language-agnostic (bash, python, node, go, anything).

### 8.2 The `describe` phase

Invoked with the literal argument `--describe`. The plugin prints one
JSON object per line on stdout; stderr is never parsed (log freely there).
The extension reads until it sees a `{"type":"end"}` frame (or EOF).

```
{"type":"template","name":"close-ticket","title":"Close a docmgr ticket",
 "description":"...","fields":[{"name":"ticket","type":"choice","choices":["A","B"],"required":true}],
 "submit":"editor","prefill":{...}}
{"type":"end"}
```

- `name` — required, matches `/^[a-zA-Z0-9_][a-zA-Z0-9_-]*$/`. The
  addressable name becomes `<group>/<name>` where `group` is the plugin's
  directory under the layer root.
- `fields` — same schema as template frontmatter fields (§6.3). Because
  `describe` runs at scan time, **`choices` can be computed** (e.g. live
  ticket ids) — this is the killer feature of plugins.
- `prefill` — optional, same schema; the LLM call happens in the extension
  (§9), not in the plugin.
- `submit` — optional `editor` (default) or `auto`.
- Timeout: **5 seconds**, then `SIGKILL`. Exit 0 expected. Invalid
  announcements become issues (warnings), other templates still load.

Junk lines (non-JSON, or JSON that is not an object) are skipped. Frames
after `end` are ignored. Unknown `type`s are skipped (forward compat).

### 8.3 The `render` phase

The extension spawns the plugin again (no `--describe`), writes exactly
one request line to stdin, and closes stdin:

```json
{"type":"render","template":"close-ticket","values":{"ticket":"A","summary":"..."},"cwd":"/home/user/project"}
```

- The subprocess `cwd` is set to the user's `cwd`.
- Env vars `PROMPTO_TEMPLATE` (the plugin template name) and
  `PROMPTO_PLUGIN_PATH` (the executable path) are set.
- The plugin responds with zero or more `log` frames (shown as a working
  status message), then exactly one terminal frame:
  - `{"type":"prompt","text":"the full expanded prompt"}` — success.
  - `{"type":"error","message":"what went wrong"}` — failure (rejects).
- Timeout: **60 seconds**, then `SIGKILL`.

### 8.4 `renderViaPlugin` execution model

```
function renderViaPlugin({template, values, cwd, onLog, timeoutMs=60_000}):
    request ← buildRenderRequest(template.pluginTemplateName ?? template.name, values, cwd)
    child ← spawn(template.filePath, [], { cwd, env: {...process.env, PROMPTO_TEMPLATE, PROMPTO_PLUGIN_PATH} })
    buffered ← ""; stderrTail ← ""; settled ← false

    timer ← setTimeout(() ⇒ reject("timed out after " + timeoutMs/1000 + "s"), timeoutMs)

    child.stdout.on("data", chunk):
        buffered += chunk
        while (newline found) and not settled:
            line ← buffered up to newline
            frame ← parseRenderLine(line)
            if frame.type == "log":    onLog(frame.message)
            elif frame.type == "prompt": finish(() ⇒ resolve(frame.text))
            elif frame.type == "error": finish(() ⇒ reject(PluginError(frame.message)))

    child.stderr.on("data", chunk):  stderrTail = (stderrTail + chunk).slice(-2000)   # keep tail for errors

    child.on("close", code):
        frame ← parseRenderLine(buffered)        # flush final unterminated line
        if frame.type == "prompt": return finish(resolve(frame.text))
        if frame.type == "error":  return finish(reject(frame.message))
        finish(reject("exited (code " + code + ") without a prompt frame" + stderrTail excerpt))

    child.stdin.write(request); child.stdin.end()
```

Three subtleties:

1. **Line-buffered, not byte-stream.** The extension accumulates stdout
   until a newline, then parses one complete JSON line at a time. A plugin
   that writes a partial JSON object across multiple flushes is fine; a
   plugin that writes a frame without a trailing newline is still handled
   on `close`.
2. **`finish` is idempotent and kills the child.** Once a terminal frame
   arrives (or the timer fires, or the process exits), the child is
   `SIGKILL`ed. This guarantees no zombie processes even if the plugin
   keeps writing after a `prompt`.
3. **stderr is kept, never parsed.** The last 2000 bytes of stderr are
   retained so that, if the plugin exits without a terminal frame, the
   rejection message includes a stderr tail (truncated to 300 chars) for
   debugging.

### 8.5 Pure parsing (`plugin-protocol.ts`)

`plugin-protocol.ts` contains all the JSONL parsing with **no pi imports
and no `node:child_process`** — it is pure string-in, structured-out. This
is what makes `bun test` able to load it directly and what makes the
protocol unit-testable without spawning anything.

Key functions:

- `parseDescribeOutput({stdout, filePath, group, source, submitDefault})`
  → `{ templates, issues }`. Reuses `parseFields`/`parsePrefill` from
  `template.ts` (the JSON shape is structurally identical to the YAML
  shape), so the validation rules are shared between templates and plugins.
- `parseRenderLine(line)` → `RenderFrame | undefined`. Returns `undefined`
  for junk/unknown lines (skip), or a typed union `log | prompt | error`.
- `buildRenderRequest(name, values, cwd)` → the single JSON line to write
  to stdin.

The `RenderFrame` type is a discriminated union:

```ts
export type RenderFrame =
  | { type: "log";    message: string }
  | { type: "prompt"; text: string; submit?: "editor" | "auto" }
  | { type: "error";  message: string };
```

A `prompt` frame may carry an optional `submit` override (currently parsed
but not propagated to the output decision — see decision record DR-5).

## 9. LLM-assisted prefill (`prefill.ts`, `prefill-parse.ts`)

Prefill is the feature that makes large forms fast: before the form opens,
the model proposes values for a declared subset of fields, and those
proposals land **in the form for review** — never straight into the prompt.

### 9.1 The `when` modes

| `when` | Behavior |
| --- | --- |
| `before-form` (default) | Run prefill before the form opens, using only field defaults + remembered values as context. |
| `after-required` | First open a mini-form for the `required` fields only, then run prefill so the model can reference the user's answers (e.g. derive a title from the goal). Then open the full form. |

`after-required` is the more powerful mode and is what the
`docmgr/create-ticket` and `research/intern-design-guide` templates use:
the user types the goal, and the prefill prompt references `{{goal}}` to
propose a ticket title.

### 9.2 The system prompt contract

`buildSystemPrompt(fields)` constructs a strict instruction:

```
You fill in form fields. Reply with exactly one JSON object and nothing else:
no prose, no markdown fences, no explanations.
Allowed keys (any other key is discarded):
- "ticketTitle" (a string) — Short SCREAMING-KEBAB title
- "ticketId" (a string) — Ticket id
Omit a key rather than guessing when you have no good value for it.
```

The constraint string per type: `choice` → "one of: …", `multichoice` →
"array with values from: …", `boolean` → "true or false", `number` → "a
number", else "a string". The instruction to *omit rather than guess* is
important — it reduces hallucinated values.

### 9.3 Tolerant parsing (`parseJsonObject`)

Models do not always return clean JSON. `parseJsonObject(raw)` tolerates:

- Clean JSON objects.
- Fenced JSON (```` ```json ... ``` ```` stripped).
- JSON embedded in prose (extracts the outermost `{...}` span).
- Nested objects inside prose.

It rejects (returns `undefined`): arrays, scalars, garbage, empty strings.
The two-candidate strategy: try the stripped whole string first, then fall
back to the substring between the first `{` and the last `}`.

### 9.4 Type-safe coercion (`coerceValue`)

Even if the model returns JSON, the values must match the field types.
`coerceValue(value, field)` applies the same rules as `normalizeDefault`:

- `string`/`text`: accept string, stringify number; reject else.
- `boolean`: must be boolean.
- `number`: accept number, or numeric string; reject non-numeric.
- `choice`: must be a string in `choices`.
- `multichoice`: must be an array; filter to elements in `choices`; reject
  if the result is empty.

Rejected values are simply dropped (not stored in `accepted`). The model's
proposals thus never produce an invalid form state.

### 9.5 The soft-fail contract

`runPrefill` returns `{}` (no proposals) on *every* failure path:

- No model selected → warn "prefill skipped: no model selected".
- No API key for the model → warn "prefill skipped: no API key".
- `prefill.prompt` fails to render (e.g. references a missing value) →
  warn and return `{}`.
- User aborts the loader overlay (or the call rejects) → warn and `{}`.
- Model output is not a JSON object → warn and `{}`.

The form always opens. This is principle P2 in action: prefill is an
enhancement, never a dependency.

### 9.6 The prefill→form→prefill precedence

```
seed  ← defaultValues(fields)               # lowest priority
seed  ← loadRememberedValues(cwd)            # overrides defaults
seed  ← runPrefill(...)                      # overrides remembered
values ← openForm(template, seed)            # user edits override everything
saveRememberedValues(cwd, template, values)  # persist the user's final choice
```

Prefill proposals override remembered values because the model may have
new context (e.g. the goal changed). The user's final edit overrides
everything and is what gets remembered for next time.

### 9.7 The UI during prefill

`runPrefill` uses `ctx.ui.custom(...)` to render a `BorderedLoader` overlay
with the text `Prefilling <template.name>…`. The loader is abortable
(`loader.onAbort` → `done(null)`), and its `signal` is passed to
`complete()` so aborting cancels the underlying model call. The overlay
disappears as soon as the call resolves or rejects.

## 10. Value memory (`state.ts`)

### 10.1 Why outside the worktree

Submitted values can contain sensitive prompt text (ticket goals, internal
references, secrets pasted by mistake). If state lived under
`.pi/` inside the repo, it would be a `git add .` accident away from being
committed. So state lives under `~/.pi/agent/prompto-state/`, keyed by a
hash of the project directory.

### 10.2 The state file

```
~/.pi/agent/prompto-state/
└── <sha256(cwd)[0:16]>.json
```

The file contains:

```json
{
  "cwd": "/home/manuel/code/wesen/2026-04-21--pi-extensions",
  "values": {
    "demo/greeting": { "name": "foobar", "language": "English" },
    "obsidian/deep-dive-project-report": { "...": "..." }
  }
}
```

The `cwd` field is stored for debuggability (you can tell which project a
state file belongs to by opening it), but the *filename* is the hash so
that path lookups are O(1) and path components never leak through the
filesystem layer.

### 10.3 Drift handling

- **Load** filters remembered values to fields the template *still
  declares*. If you remove a field from a template, stale remembered
  values for it are dropped on the next load. Type drift beyond this
  shallow filter is left to the form's own validation.
- **Save** also filters to declared fields before writing, so the stored
  state never accumulates stale keys.
- **Corrupt state file** → start over (treated as empty). Value memory is
  best-effort; it must never fail the expansion.

### 10.4 `statePath` determinism

`statePath(cwd)` is `sha256(cwd).slice(0,16)` → deterministic, so the same
project always maps to the same file. `state.test.ts` verifies that
different cwds map to different files and that the cwd string never
appears in the path.

## 11. Configuration (`config.ts`)

`~/.pi/agent/prompto.json` is optional. Three keys:

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `submitDefault` | `"editor" \| "auto"` | `"editor"` | Default submit mode for templates/plugins that do not declare their own. |
| `allowProjectPlugins` | `boolean` | `false` | Whether executables in the *project* layer are run as plugins. Global-layer plugins always run. |
| `prefillMaxTokens` | `number` | `1024` | Max tokens for the prefill model call. |

`readConfig()` returns `{ config, warnings }`. Invalid values are *ignored*
(not crashed on) with a warning pushed to `warnings`, which surface as scan
issues on the next `/prompto reload`. This is the soft-fail philosophy
applied to configuration.

### 11.1 The `allowProjectPlugins` security boundary

A plugin is an arbitrary executable that the extension will spawn with
your `cwd` and environment. Running project-layer plugins means anyone who
can commit an executable to `.pi/prompts/` can run code on your machine
when you open the project. The default `false` forces an opt-in. Global
plugins are assumed to be author-installed and trusted.

## 12. The runtime orchestrator (`run.ts`)

`runPrompto` is the entry point for every surface (command, action,
palette, shortcut). It dispatches by argument and template kind.

### 12.1 The top-level flow

```
function runPrompto(pi, store, args, ctx, options={}):
    if not ctx.hasUI: return                         # headless guard

    if args == "reload":
        scan ← store.rescan(ctx.cwd); reportScan(ctx, scan); return

    store.ensureLoaded(ctx.cwd)

    if args:                                         # /prompto <name>
        template ← store.resolve(args)
        if not template: ctx.ui.notify("no template named ...", "error"); return
    else:                                            # /prompto (no arg)
        templates ← store.list()
        if empty: ctx.ui.notify("no templates found", "warning"); return
        template ← openPicker(ctx, templates)
        if not template: return                      # cancelled

    try:
        prompt ← expandTemplate(ctx, template, store.config.prefillMaxTokens)
    catch e:
        ctx.ui.notify("prompto: " + e, "error"); return
    if prompt === undefined: return                  # cancelled (form)

    output ← options.output ?? (template.submit == "auto" ? "send" : "replace-editor")
    if output == "send":           pi.sendUserMessage(prompt, ctx.isIdle() ? undefined : {deliverAs:"followUp"})
    elif output == "paste-editor": ctx.ui.pasteToEditor(prompt); notify("pasted")
    else:                          ctx.ui.setEditorText(prompt); notify("expanded")
```

### 12.2 `expandTemplate` — dispatch by kind

```
function expandTemplate(ctx, template, prefillMaxTokens):
    if template.kind == "plain":
        return readFileSync(template.filePath, "utf-8")   # no form, no render

    values ← collectValues(ctx, template, prefillMaxTokens)
    if values === undefined: return undefined              # user cancelled

    if template.kind == "plugin":
        return renderViaPlugin({template, values, cwd: ctx.cwd,
                                onLog: m ⇒ ctx.ui.setWorkingMessage?.("prompto: " + m)})
    # kind == "template"
    return renderTemplate(template.body, values)
```

### 12.3 `collectValues` — the two-pass prefill flow

```
function collectValues(ctx, template, prefillMaxTokens):
    seed ← defaultValues(template.fields)
    if template.fields.length == 0: return seed          # no form needed

    seed ← { ...seed, ...loadRememberedValues(ctx.cwd, template) }
    warn ← m ⇒ ctx.ui.notify("prompto: " + m, "warning")

    if template.prefill?.when == "after-required":
        requiredFields ← template.fields.filter(f ⇒ f.required)
        if requiredFields.length > 0:
            pass1 ← openForm({...template, fields: requiredFields}, seed)   # mini-form
            if pass1 === undefined: return undefined
            seed ← { ...seed, ...pass1 }
        seed ← { ...seed, ...runPrefill(ctx, template, seed, prefillMaxTokens, warn) }
        values ← openForm(template, seed)                                  # full form
    else:
        if template.prefill:
            seed ← { ...seed, ...runPrefill(ctx, template, seed, prefillMaxTokens, warn) }
        values ← openForm(template, seed)

    if values !== undefined: saveRememberedValues(ctx.cwd, template, values)
    return values
```

The `after-required` branch opens the form **twice** when there are
required fields: once for just the required fields (so the prefill prompt
can reference them), then once for the full template. This is a deliberate
UX trade-off: one extra form in exchange for prefill that can actually use
the user's answers.

### 12.4 The three output modes

| Mode | Trigger | Effect |
| --- | --- | --- |
| `replace-editor` | default for `submit: editor` | `ctx.ui.setEditorText(prompt)` — replaces current editor draft |
| `paste-editor` | `Ctrl+Alt+P`, `paste` action, palette paste | `ctx.ui.pasteToEditor(prompt)` — inserts at cursor, preserves draft |
| `send` | default for `submit: auto` | `pi.sendUserMessage(prompt)` — sends directly to the agent |

`send` with `deliverAs: "followUp"` is used when the agent is mid-task
(`!ctx.isIdle()`); otherwise the message is delivered as a normal user
turn. This lets `submit: auto` templates inject a follow-up without
interrupting.

## 13. The UI layer (`ui/picker.ts`, `ui/form.ts`)

Both UIs are modal overlays built on `ctx.ui.custom(...)`, which gives the
extension a `TUI`, a `Theme`, and a `done` callback. Each implements the
`Component` interface from `@mariozechner/pi-tui`:

```ts
interface Component {
  handleInput(data: string): void;
  render(width: number): string[];
  invalidate(): void;
}
```

### 13.1 The picker (`ui/picker.ts`)

`PromptoTemplatePicker` is a fuzzy-filterable modal list. Responsibilities:

- **Filtering.** The query is split on `[\s/]+`; each token must fuzzy-match
  at least one "chunk" of a template. Chunks include `name`, `group`,
  `title`, `description`, `source`, `kind`, `submit`, and every field's
  `name`/`label`/`help`/`placeholder`. Scores sum; ties break
  alphabetically. This means typing `docmgr ticket` finds
  `docmgr/create-ticket` even if the title is "Create docmgr ticket".
- **Navigation.** Up/Down, PageUp/PageDown (jumps by visible count),
  Home/End, Enter to select, Esc/Ctrl+C to cancel.
- **Quick open.** `Alt+1`–`Alt+9` open the corresponding *visible* row
  directly (indexed from the current scroll window, not the full list).
- **Clear.** Backspace deletes; Ctrl+U clears the whole query.
- **Scroll window.** The visible window centers on the selection when
  possible, clamped to the list bounds. A scroll indicator
  `(index/total)` appears when the list is longer than the window.
- **Footer.** Shows the current template's title/description and a summary
  line `/<name> · <n> fields · submit:<mode>`.

The overlay is centered, 84 columns wide, up to 90% of the viewport height.

### 13.2 The form (`ui/form.ts`)

`PromptFormComponent` is a schema-generated modal form. Key mechanics:

- **Focus model.** `focus` is an index `0..fields.length` — the last index
  is the button row. Tab/Down moves forward, Shift+Tab/Up backward.
- **Per-type input handlers.** Each `FieldType` has its own `handleInput`
  branch:
  - `boolean` — Space/Left/Right toggles.
  - `choice` — Left/Right/Space cycles through `choices`.
  - `multichoice` — Left/Right moves an inner cursor; Space toggles the
    choice under the cursor.
  - `text` — Enter opens `ctx.ui.editor(...)` (a nested full-screen
    editor) and writes the result back. A `editingText` guard prevents
    the outer form from processing input while the editor is open.
  - `string`/`number` — inline editing: printable chars append, Backspace
    deletes, Ctrl+U clears. Numbers are parsed on submit.
- **Validation.** On submit: required fields must be non-empty (strings
  trimmed, arrays non-empty); `number` fields must parse to a finite
  number. Missing required fields show `required: <labels>`; a bad number
  shows `"X" must be a number`.
- **Caching.** `render(width)` caches its output keyed by width; any input
  calls `invalidate()` then `tui.requestRender()`. This keeps redraws cheap
  when the form has many fields.
- **Rendering.** A bordered modal with the template title, an optional
  description, one or two rows per field (a second row shows `help` when the
  field is focused), an error row, a Submit/Cancel button row, and a
  context-sensitive hint line that changes per field type.

The hint line is the form's discoverability feature — it tells you the
keys for the *currently focused* field type, so an intern never needs to
read docs to operate the form.

---

# Part III — Authoring

This part is the practical core. It is written to be extractable into a
standalone skill (the stated goal of this ticket). Each section is
self-contained.

## 14. Authoring a plain prompt

A plain prompt is the lowest-effort reuse: drop a file in a prompts
directory. No frontmatter, no form.

### 14.1 Steps

1. Create a file under `.pi/prompts/` (project) or
   `~/.pi/agent/prompts/` (global). Any extension is fine; `.md` is
   conventional.
2. Write the prompt text as the file body. No frontmatter.
3. Run `/prompto reload`.
4. Pick it from `/prompto` — the contents are pasted verbatim.

### 14.2 Naming

The addressable name is the relative path with the extension stripped:
`.pi/prompts/notes/standup.md` → `/prompto notes/standup`. The group is
the first segment (`notes`), used only for organization in the picker.

### 14.3 When to use plain

- The prompt has no parameters (a fixed rubric, a checklist, a persona).
- You want zero ceremony and zero risk of a parse error.
- The prompt is short and stable.

### 14.4 When *not* to use plain

If you find yourself editing the pasted text to fill in the same slots
each time, promote it to a template (§15). If you find yourself needing
live data (current diff, ticket list), promote it to a plugin (§16).

## 15. Authoring a template

A template adds a YAML frontmatter block that declares fields; the body
uses the tiny rendering dialect.

### 15.1 The frontmatter schema (reference)

```yaml
---
title: <string>                 # shown in the picker and form header
description: <string>           # one-liner shown in the picker details
submit: editor | auto           # editor (default): review before send; auto: send immediately
fields:                         # list of field maps (see 15.2); empty/omitted = plain-like
  - <field>
prefill:                        # optional; see 15.3
  <prefill-spec>
---
<body with {{placeholders}} and {{#if}} blocks>
```

### 15.2 The field schema (reference)

| Key | Type | Required | Applies to | Meaning |
| --- | --- | --- | --- | --- |
| `name` | string (`[a-zA-Z_]\w*`) | yes | all | Placeholder name and form key. |
| `type` | enum | no (default `string`) | all | `string \| text \| boolean \| choice \| multichoice \| number`. |
| `label` | string | no | all | Form row label. Defaults to `name`. |
| `help` | string | no | all | Shown under the field when focused. |
| `placeholder` | string | no | `string`/`number` | Dim hint when empty and unfocused. |
| `required` | boolean | no | all | Must be non-empty to submit. |
| `choices` | string[] | yes | `choice`/`multichoice` | Non-empty list of allowed values. |
| `default` | value | no | all | Initial value; type-checked (see 15.4). |

Notes:

- `string` is a single-line inline edit; `text` opens a nested editor on
  Enter. Use `text` for anything multi-line or longer than a phrase.
- `number` is inline-edited as a string and parsed on submit.
- `multichoice` `default` must be a list, even for one element: `default: [a]`.

### 15.3 The prefill schema (reference)

```yaml
prefill:
  fields: [ticketTitle, ticketId]      # required; must be declared fields
  when: before-form | after-required   # optional; default before-form
  prompt: |                           # required; rendered with current values
    Propose a SCREAMING-KEBAB title for: {{goal}}
```

- `prompt` is itself a template body — it can use `{{name}}` and `{{#if}}`.
  Unknown placeholders still throw (strict mode applies to prefill too).
- `fields` constrains *which* fields the model may propose; proposals for
  other fields are discarded even if the model returns them.
- `after-required` runs a mini-form for required fields first, so the
  prefill prompt can reference the user's answers.

### 15.4 Default value validation

| Field type | Accepted default |
| --- | --- |
| `string`/`text` | string, or number (stringified) |
| `boolean` | boolean |
| `number` | number |
| `choice` | string in `choices` |
| `multichoice` | string list, every element in `choices` |

A `default` that fails validation throws `TemplateError` at scan time.

### 15.5 The rendering dialect (reference)

| Construct | Example | Effect |
| --- | --- | --- |
| Substitution | `{{goal}}` | The value; multichoice → `a, b`; boolean → `true`/`false` |
| Truthy conditional | `{{#if upload}}…{{/if}}` | Kept when truthy (non-empty/non-zero/true) |
| Equality | `{{#if depth == "full"}}…{{/if}}` | Kept when value's string form equals `full` |
| Inequality | `{{#if depth != "full"}}…{{/if}}` | Kept when not equal |

Rules: no nesting, no loops, no filters, no expressions. Unknown
placeholders are a hard error. Escaping inside literals: `\"` → `"`.

### 15.6 Worked example: `docmgr/create-ticket.md`

```yaml
---
title: Create docmgr ticket + analysis plan
description: Scaffold a docmgr ticket and ask for a project analysis plan
submit: editor
fields:
  - name: goal
    label: Ticket goal
    type: text
    required: true
    help: What should this ticket achieve?
  - name: ticketTitle
    label: Ticket title
    type: string
    placeholder: SCREAMING-KEBAB short title
  - name: topics
    label: Topics
    type: multichoice
    choices: [analysis, design, refactor, tui, docs, pi-extensions]
    default: [analysis]
  - name: planDepth
    label: Analysis plan depth
    type: choice
    choices: [full, light]
    default: full
  - name: uploadRemarkable
    label: Upload report to reMarkable when done
    type: boolean
    default: true
prefill:
  fields: [ticketTitle]
  when: after-required
  prompt: |
    Given this ticket goal, propose a short SCREAMING-KEBAB ticket title
    (like FROB-ANALYSIS, at most 3 words). Goal: {{goal}}
---
Create a new docmgr ticket titled "{{ticketTitle}}" with topics {{topics}}.
The goal of the ticket:

{{goal}}

Then write a project analysis plan.
{{#if planDepth == "full"}}
Make the plan exhaustive: architecture map, evidence with file references,
risk register, and a phased implementation outline.
{{/if}}
{{#if planDepth == "light"}}
Keep the plan light: a one-page summary of scope, approach, and risks.
{{/if}}
{{#if uploadRemarkable}}
When the analysis document is complete, upload it to reMarkable.
{{/if}}
```

What happens when the user runs `/prompto docmgr/create-ticket`:

1. The form opens for the **required** field `goal` only (because
   `prefill.when == "after-required"`).
2. The user types the goal and submits the mini-form.
3. The prefill prompt is rendered: `Given this ticket goal, propose a short
   SCREAMING-KEBAB ticket title (...). Goal: <the goal>`.
4. The model proposes `{"ticketTitle": "FROB-ANALYSIS"}`.
5. The full form opens with `ticketTitle` pre-filled, `topics` defaulting
   to `[analysis]`, `planDepth` to `full`, `uploadRemarkable` to `true`.
6. The user reviews/edits and submits.
7. The body is rendered: `{{goal}}` is substituted, the `full` block is
   kept, the `light` block is dropped, the `uploadRemarkable` block is
   kept.
8. The expanded prompt replaces the editor text (because `submit: editor`).

### 15.7 Patterns and anti-patterns

**Do:**

- Name fields clearly; the `label` is what the intern sees.
- Use `help` for anything non-obvious — it appears on focus.
- Prefer `after-required` prefill when the model can derive a value from a
  required field (titles, ids, summaries).
- Use `multichoice` for tags/topics; `choice` for mutually exclusive modes.
- Put a `{{#if}}` guard around instructions that only apply to one mode,
  so the expanded prompt is clean for every combination.

**Don't:**

- Don't reference a field in the body that you didn't declare — it errors.
- Don't nest `{{#if}}` blocks — the dialect does not support it.
- Don't put a field in `prefill.fields` that you didn't declare — it errors.
- Don't use `text` for a single-word value; use `string` (inline edit is
  faster).
- Don't rely on prefill always succeeding — it soft-fails. The form must
  be usable without it.

## 16. Authoring a plugin

A plugin is an executable that speaks the JSONL protocol. Use it when a
prompt needs computed content.

### 16.1 The contract (reference)

**Describe** — `plugin --describe`, stdout, one JSON per line, 5s timeout:

```
{"type":"template","name":"<name>","title":"...","description":"...",
 "fields":[<field>, ...],"submit":"editor"|"auto","prefill":{<prefill-spec>}}
...
{"type":"end"}
```

**Render** — stdin gets one line, stdout responds, 60s timeout:

```
← stdin:  {"type":"render","template":"<name>","values":{...},"cwd":"..."}
→ stdout: {"type":"log","message":"..."}                    (zero or more)
          {"type":"prompt","text":"<full expanded prompt>"}  (terminal)
       or {"type":"error","message":"<what went wrong>"}      (terminal)
```

Rules:

- `name` matches `/^[a-zA-Z0-9_][a-zA-Z0-9_-]*$/` (allows `-`, unlike
  field names).
- `fields` use the **same schema** as template frontmatter (§15.2).
- `choices` can be **computed at scan time** (the whole point of plugins).
- Env vars `PROMPTO_TEMPLATE` and `PROMPTO_PLUGIN_PATH` are set on render.
- stderr is never parsed; log freely there.
- Junk lines and unknown `type`s are skipped (forward compat).
- Exit 0 after `end` (describe) or after the terminal frame (render).

### 16.2 Minimal plugin (python)

```python
#!/usr/bin/env python3
import json, sys
if "--describe" in sys.argv:
    print(json.dumps({"type": "template", "name": "hello",
                      "fields": [{"name": "who", "type": "string", "required": True}]}))
    print(json.dumps({"type": "end"}))
    sys.exit(0)
req = json.loads(sys.stdin.readline())
print(json.dumps({"type": "prompt", "text": f"Say hello to {req['values']['who']}!"}))
```

Install: copy into a prompts layer and `chmod +x`. The extension detects
it as a plugin via the executable bit.

### 16.3 The computed-choices pattern

The killer feature. `examples/tickets.plugin.py` computes the choice list
for the `ticket` field by shelling out to `docmgr ticket list`:

```python
def existing_ticket_ids(cwd):
    try:
        out = subprocess.run(
            ["docmgr", "ticket", "list"],
            capture_output=True, text=True, timeout=3, cwd=cwd, check=False,
        ).stdout
    except Exception:
        return []
    ids = []
    for line in out.splitlines():
        if line.startswith("### "):
            ids.append(line[4:].split(" ")[0])
    return ids[:20]

def describe():
    print(json.dumps({
        "type": "template", "name": "close-ticket",
        "fields": [
            {"name": "ticket", "type": "choice",
             "choices": existing_ticket_ids(".") or ["NO-TICKETS-FOUND"], "required": True},
            ...
        ],
    }))
```

Because `describe` runs at scan time (and is cached per session), the
choices are fresh when the user opens the form. If the underlying data
changes, `/prompto reload` re-runs `describe`.

### 16.4 The multi-template pattern

One plugin can announce multiple templates:

```python
def describe():
    print(json.dumps({"type": "template", "name": "close-ticket", ...}))
    print(json.dumps({"type": "template", "name": "ticket-status", ...}))
    print(json.dumps({"type": "end"}))

def render():
    req = json.loads(sys.stdin.readline())
    if req["template"] == "close-ticket":   ...
    elif req["template"] == "ticket-status": ...
    else: print(json.dumps({"type": "error", "message": f"unknown template {req['template']!r}"}))
```

The `template` field in the render request tells the plugin which of its
announced templates was selected. Always handle the unknown case with an
`error` frame.

### 16.5 The single-template bash pattern

`examples/git-diff.plugin.sh` is a complete single-template plugin in
bash:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--describe" ]]; then
  printf '%s\n' '{"type":"template","name":"git-diff","title":"Review my current git diff","fields":[{"name":"focus","type":"choice","choices":["correctness","style","performance"],"default":"correctness"}]}'
  printf '%s\n' '{"type":"end"}'
  exit 0
fi

request="$(head -n 1)"
focus="$(printf '%s' "$request" | sed -n 's/.*"focus":"\([^"]*\)".*/\1/p')"
diff_output="$(git diff --stat && git diff)"
jq -cn --arg focus "${focus:-correctness}" --arg diff "$diff_output" \
  '{type:"prompt", text:("Review the following git diff with a focus on " + $focus + ":\n\n```diff\n" + $diff + "\n```")}'
```

Note the use of `jq -cn` to build the prompt frame safely (escaping is
handled by jq, not by string concatenation). For any non-trivial prompt
text, use a JSON builder (`jq`, `python -c 'json.dumps'`, etc.) rather than
hand-rolling JSON — unescaped newlines/quotes in the diff would break the
JSONL line.

### 16.6 Security and the project layer

- Project-layer plugins require `allowProjectPlugins: true` in
  `~/.pi/agent/prompto.json`. Default is `false`.
- Global-layer plugins always run (you installed them yourself).
- A plugin runs with your `cwd`, your environment, and a 60-second
  window. Audit a plugin before installing it, the same way you would audit
  any shell script.

### 16.7 Error handling and timeouts

- Describe timeout: 5s. If your `describe` does slow I/O (network), cache
  it or fail fast — do not block the scan.
- Render timeout: 60s. Emit `log` frames for long work so the user sees a
  status message.
- On failure, emit `{"type":"error","message":"..."}` and exit. The
  extension surfaces the message as an error toast.
- If the plugin exits without a terminal frame, the extension rejects
  with `exited (code N) without a prompt frame` plus a stderr tail.

### 16.8 Testing a plugin manually

```bash
# Describe phase
./my.plugin --describe | jq .

# Render phase (simulate the request)
echo '{"type":"render","template":"my-template","values":{"who":"world"},"cwd":"."}' | ./my.plugin
```

The extension's own test fixtures (`tests/plugin.test.ts`) do exactly
this, writing real scripts to a tmpdir and asserting on the parsed frames.

---

# Part IV — Testing & operations

## 17. Test architecture

The test suite is 65 tests across 5 files, all `bun:test`. Two design
choices make it fast and reliable:

### 17.1 Pure-function isolation

The parsing layers (`frontmatter.ts`, `template.ts`, `plugin-protocol.ts`,
`prefill-parse.ts`, `state.ts`) have **no pi imports and no subprocess
imports**. They are pure string-in/structured-out functions. This means:

- `bun test` loads them directly (no pi runtime needed).
- Tests are synchronous and sub-millisecond.
- Edge cases (tab rejection, junk lines, nested braces) are cheap to
  enumerate.

`prefill-parse.ts` exists *as a separate file* from `prefill.ts` purely so
the pure helpers (`buildSystemPrompt`, `parseJsonObject`, `coerceValue`)
can be tested without loading `@mariozechner/pi-ai`. This is a pattern to
copy: separate pure logic from pi-bound logic.

### 17.2 Subprocess fixtures for the plugin layer

`tests/plugin.test.ts` writes real executable scripts to a tmpdir
(`mkdtempSync`), `chmod 0o755`s them, and asserts on the parsed output.
This tests the real `spawn`/stdin/stdout pipeline, including:

- Happy path (log then prompt).
- Error frames reject with the message.
- Junk stdout followed by prompt still succeeds.
- Exit without a terminal frame rejects with stderr tail.
- Timeouts kill the process (`timeoutMs: 300` against `sleep 30`).

The fixture pattern:

```ts
function fixture(name: string, script: string): string {
  const path = join(FIXTURE_DIR, name);
  writeFileSync(path, script, "utf-8");
  chmodSync(path, 0o755);
  return path;
}
```

### 17.3 What to test when adding a feature

- **New field type** → add to `FIELD_TYPES` in `template.ts`; add a
  `normalizeDefault` case; add a `coerceValue` case (prefill); add a
  `defaultValues` case; add a form input handler + renderer in `form.ts`;
  add tests in `template.test.ts` and `prefill.test.ts`.
- **New rendering construct** → add the regex to `renderTemplate`; add
  tests in `template.test.ts` for keep/drop/error.
- **New protocol frame** → add a `parseRenderLine`/`parseDescribeOutput`
  branch; add tests in `plugin.test.ts` for parse + skip-unknown.

## 18. Operations & diagnostics

### 18.1 `/prompto reload`

Rescans both layers, re-runs plugin `describe` phases, and reports:

```
prompto: 5 templates loaded · 2 plugins queried · shadowed: docmgr/create-ticket
```

Shadowed names are a warning (something was overwritten). Scan issues are
reported one per line:

```
prompto: /path/to/bad.md: field "x" has unknown type "banana"
prompto: /path/to/plugin: project-layer plugin skipped (set allowProjectPlugins in ~/.pi/agent/prompto.json)
```

### 18.2 Common issues and fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Template not in picker | Not reloaded, or parse error | `/prompto reload`; check warnings |
| `unknown placeholder` | Body references an undeclared field | Add the field or fix the name |
| `prefill skipped: no model` | No model selected | Select a model |
| `prefill skipped: no API key` | Model has no key configured | Configure the model's API key |
| Project plugin skipped | `allowProjectPlugins` false | Set `allowProjectPlugins: true` in `~/.pi/agent/prompto.json` |
| Plugin timed out | `describe` > 5s or `render` > 60s | Optimize, cache, or emit `error` |
| `exited without a prompt frame` | Plugin crashed or did not emit a terminal frame | Check stderr tail; add a `prompt`/`error` frame |
| Form opens unprefilled | Prefill soft-failed | Check the warning toast |

### 18.3 Inspecting state

Value memory: `cat ~/.pi/agent/prompto-state/*.json`. Each file's `cwd`
field identifies the project. To reset a template's remembered values,
delete the `values[<template-name>]` key (or the whole file).

Config: `cat ~/.pi/agent/prompto.json` (may not exist; defaults apply).

---

# Part V — Reference

## 19. API reference

### 19.1 `PromptTemplate` (`types.ts`)

```ts
interface PromptTemplate {
  name: string;                    // addressable id, e.g. "docmgr/create-ticket"
  group: string;                  // first path segment, e.g. "docmgr" ("" if none)
  title?: string;
  description?: string;
  submit: "editor" | "auto";
  fields: TemplateField[];
  prefill?: PrefillSpec;
  body: string;                    // markdown body (empty for plugins)
  filePath: string;                // absolute path of the source file/executable
  source: "project" | "global";
  kind: "template" | "plain" | "plugin";
  pluginTemplateName?: string;     // for plugins: the name announced by the plugin
}
```

### 19.2 `TemplateField` (`types.ts`)

```ts
type FieldType = "string" | "text" | "boolean" | "choice" | "multichoice" | "number";
type FieldValue = string | number | boolean | string[];

interface TemplateField {
  name: string;
  label?: string;
  type: FieldType;
  help?: string;
  placeholder?: string;
  default?: FieldValue;
  required?: boolean;
  choices?: string[];             // required for choice/multichoice
}
```

### 19.3 `PrefillSpec` (`types.ts`)

```ts
interface PrefillSpec {
  fields: string[];                       // which declared fields the model may fill
  prompt: string;                         // rendered with current values, sent to the model
  when: "before-form" | "after-required"; // default before-form
}
```

### 19.4 `PromptoConfig` (`types.ts`, `config.ts`)

```ts
interface PromptoConfig {
  submitDefault: "editor" | "auto";  // default: "editor"
  allowProjectPlugins: boolean;        // default: false
  prefillMaxTokens: number;            // default: 1024
}
```

Path helpers: `getConfigPath()` → `~/.pi/agent/prompto.json`;
`getGlobalPromptsDir()` → `~/.pi/agent/prompts`;
`getProjectPromptsDir(cwd)` → `<cwd>/.pi/prompts`.

### 19.5 `RenderFrame` (`plugin-protocol.ts`)

```ts
type RenderFrame =
  | { type: "log";    message: string }
  | { type: "prompt"; text: string; submit?: "editor" | "auto" }
  | { type: "error";  message: string };
```

### 19.6 `PromptStore` (`store.ts`)

```ts
class PromptStore {
  constructor(describePlugin?: PluginDescriber);
  ensureLoaded(cwd: string): Promise<ScanResult>;   // lazy first scan
  rescan(cwd: string): Promise<ScanResult>;          // force rescan
  list(): PromptTemplate[];                           // sorted by name
  resolve(name: string): PromptTemplate | undefined;
  get config(): PromptoConfig;
}

interface ScanResult {
  count: number;
  issues: ScanIssue[];     // { filePath, message }
  shadowed: string[];      // names overwritten by a higher-priority layer
  pluginsRun: string[];    // plugin executables that were --describe'd
}
```

### 19.7 `PluginDescriber` (`store.ts`)

```ts
type PluginDescriber = (options: {
  filePath: string; group: string; source: TemplateSource;
  submitDefault: "editor" | "auto"; cwd: string;
}) => Promise<{ templates: PromptTemplate[]; issues: string[] }>;
```

### 19.8 Key functions

| Function | File | Signature |
| --- | --- | --- |
| `splitFrontmatter` | `frontmatter.ts` | `(source: string) => { frontmatter: FmMap \| undefined; body: string }` |
| `parseTemplate` | `template.ts` | `(opts) => PromptTemplate` (throws `TemplateError`) |
| `parseFields` | `template.ts` | `(value, filePath) => TemplateField[]` |
| `parsePrefill` | `template.ts` | `(value, fields, filePath) => PrefillSpec \| undefined` |
| `defaultValues` | `template.ts` | `(fields) => Record<string, FieldValue>` |
| `renderTemplate` | `template.ts` | `(body, values) => string` (throws on unknown) |
| `formatValue` | `template.ts` | `(value) => string` |
| `parseDescribeOutput` | `plugin-protocol.ts` | `(opts) => { templates, issues }` |
| `parseRenderLine` | `plugin-protocol.ts` | `(line) => RenderFrame \| undefined` |
| `buildRenderRequest` | `plugin-protocol.ts` | `(name, values, cwd) => string` |
| `describePlugin` | `plugin.ts` | `(opts) => Promise<DescribeResult>` |
| `renderViaPlugin` | `plugin.ts` | `(opts) => Promise<string>` |
| `buildSystemPrompt` | `prefill-parse.ts` | `(fields) => string` |
| `parseJsonObject` | `prefill-parse.ts` | `(raw) => Record<string, unknown> \| undefined` |
| `coerceValue` | `prefill-parse.ts` | `(value, field) => FieldValue \| undefined` |
| `runPrefill` | `prefill.ts` | `(ctx, template, known, maxTokens, warn) => Promise<Record<string, FieldValue>>` |
| `loadRememberedValues` | `state.ts` | `(cwd, template, stateDir?) => Record<string, FieldValue>` |
| `saveRememberedValues` | `state.ts` | `(cwd, template, values, stateDir?) => void` |
| `statePath` | `state.ts` | `(cwd, stateDir?) => string` |
| `readConfig` | `config.ts` | `() => { config, warnings }` |
| `runPrompto` | `run.ts` | `(pi, store, args, ctx, options?) => Promise<void>` |

## 20. File map (responsibilities)

| File | Lines | Responsibility |
| --- | --- | --- |
| `index.ts` | ~85 | Registration, `/prompto` command, `Ctrl+Alt+P`, doc loaders |
| `config.ts` | ~75 | `~/.pi/agent/prompto.json` reader, path helpers, defaults |
| `frontmatter.ts` | ~50 | Fence split + YAML parse (`yaml` package) |
| `types.ts` | ~45 | All shared types |
| `template.ts` | ~180 | `parseTemplate`, `parseFields`, `parsePrefill`, `defaultValues`, `renderTemplate` |
| `store.ts` | ~130 | `PromptStore`: layered scan, shadowing, plugin describer wiring |
| `plugin.ts` | ~130 | `describePlugin` + `renderViaPlugin` subprocess execution |
| `plugin-protocol.ts` | ~115 | Pure JSONL parsing + request building |
| `prefill.ts` | ~85 | `runPrefill`: model call + `BorderedLoader` overlay |
| `prefill-parse.ts` | ~85 | Pure: `buildSystemPrompt`, `parseJsonObject`, `coerceValue` |
| `run.ts` | ~115 | `runPrompto` orchestrator, `expandTemplate`, `collectValues` |
| `state.ts` | ~90 | Value memory outside worktree, `sha256(cwd)` keying |
| `ui/picker.ts` | ~240 | `PromptoTemplatePicker` fuzzy modal list |
| `ui/form.ts` | ~270 | `PromptFormComponent` schema-generated modal form |
| `docs/authoring.md` | — | Short authoring guide (in-app doc) |
| `docs/plugin-protocol.md` | — | Short protocol reference (in-app doc) |
| `examples/git-diff.plugin.sh` | ~20 | Reference single-template bash plugin |
| `examples/tickets.plugin.py` | ~70 | Reference multi-template python plugin (computed choices) |

## 21. Glossary

- **Addressable name** — the path-relative, extension-stripped identifier
  used to invoke a template: `/prompto <name>`.
- **Group** — the first segment of the addressable name; used only for
  picker organization.
- **Layer** — one of the two scan roots: project (`.pi/prompts`) or global
  (`~/.pi/agent/prompts`).
- **Shadowing** — when a project-layer template overwrites a global-layer
  template of the same name.
- **Plain / Template / Plugin** — the three `kind`s of prompt.
- **Prefill** — the LLM-assisted pre-fill of declared form fields before
  the form opens.
- **Value memory** — per-project, per-template remembered last-submitted
  values, stored outside the worktree.
- **Terminal frame** — a `prompt` or `error` JSONL frame that ends the
  render phase.
- **Soft-fail** — an optional feature that degrades to a no-op with a
  warning rather than aborting the expansion.
- **JSONL** — JSON Lines; one JSON object per line.
- **Component** — the pi-tui interface (`handleInput`/`render`/`invalidate`)
  implemented by both the picker and the form.

## 22. Intern onboarding checklist

- [ ] Read this guide end-to-end (Part I + Part III §14–16).
- [ ] Run `/prompto reload` in this repo; confirm you see the 5 templates.
- [ ] Run `/prompto demo/greeting`; fill the form; confirm the expanded
      prompt appears in the editor.
- [ ] Run `/prompto docmgr/create-ticket`; observe the two-pass prefill
      flow (required `goal` first, then the full form with `ticketTitle`
      proposed).
- [ ] Read `~/.pi/agent/prompto-state/*.json`; confirm your last-submitted
      values are there.
- [ ] Read `extensions/prompto/index.ts` and `store.ts`; trace one
      `/prompto <name>` invocation through `runPrompto`.
- [ ] Read `template.ts`; trace `parseTemplate` → `parseFields` →
      `renderTemplate`.
- [ ] Read `plugin.ts` + `plugin-protocol.ts`; run
      `./extensions/prompto/examples/git-diff.plugin.sh --describe` and
      pipe a render request to it manually (§16.8).
- [ ] Author a new plain prompt under `.pi/prompts/`; reload; use it.
- [ ] Author a new template with `fields:` and `prefill:`; reload; use it.
- [ ] Author a new plugin (python or bash) with a computed `choices` list;
      reload; use it.
- [ ] Run `bun test extensions/prompto/`; confirm 65 pass.
- [ ] Read the decision records (§23) for the non-obvious choices.

## 23. Decision records

### DR-1 — Tiny templating dialect (no loops/filters/nesting)

**Context.** Templates need *some* logic (conditional sections by mode).
Full templating engines (Jinja, Handlebars) are powerful but unsafe to
expand with untrusted content and hard to audit.

**Decision.** `{{name}}` and `{{#if …}}…{{/if}}` only. No loops, filters,
nesting, or expressions. Unknown placeholders error.

**Consequence.** Templates stay auditable. Complex prompts become plugins
(testable code). Authors occasionally hit the dialect's limits and must
escalate to a plugin — this is acceptable and expected.

### DR-2 — Soft-fail for prefill and value memory

**Context.** Prefill depends on a configured model + API key; value memory
depends on disk. Neither is guaranteed.

**Decision.** Both degrade to no-ops with a warning. The form always opens.

**Consequence.** The expansion never fails due to an optional feature.
Users learn to read the warning toasts, but the core workflow is
uninterrupted.

### DR-3 — Value memory outside the worktree

**Context.** Submitted values may contain sensitive prompt text.

**Decision.** State lives under `~/.pi/agent/prompto-state/`, keyed by
`sha256(cwd)`. Never under `.pi/` inside the repo.

**Consequence.** No `git add .` accident can commit a user's prompt
history. The `cwd` field is stored inside the file for debuggability, but
the filename is the hash.

### DR-4 — Plugins are stateless, two-phase subprocesses

**Context.** A plugin needs to both announce its templates (with computed
choices) and render prompts.

**Decision.** Two independent invocations: `--describe` (scan) and a render
request on stdin (expand). No daemon, no handshake, no shared state.

**Consequence.** Plugins are trivially testable (pipe stdin, read stdout)
and language-agnostic. The cost is re-running `describe` on reload and
re-spawning on each render — both cheap enough at the scale of interactive
prompt expansion.

### DR-5 — The `prompt` frame's optional `submit` is parsed but not propagated

**Context.** The protocol allows `{"type":"prompt","text":"...","submit":"auto"}`.

**Decision.** `parseRenderLine` captures `submit`, but `renderViaPlugin`
does not currently surface it to the output-mode decision in `run.ts`
(which uses the template's `submit` from `describe`).

**Consequence.** A plugin cannot dynamically override the submit mode per
render today. This is a known gap; wiring it through would require
`renderViaPlugin` to return `{ text, submit? }` and `run.ts` to consult it.

**Follow-up.** If a use case emerges for per-render submit overrides,
thread the `submit` through `renderViaPlugin` → `expandTemplate` →
`runPrompto`. Until then, plugins set `submit` at describe time.

### DR-6 — Strict field-name regex, looser plugin template-name regex

**Context.** Field names appear as `{{placeholders}}` and form keys;
plugin template names appear only in the addressable name.

**Decision.** Field names: `/^[a-zA-Z_][a-zA-Z0-9_]*$/` (no `-`).
Plugin template names: `/^[a-zA-Z0-9_][a-zA-Z0-9_-]*$/` (allows `-`).

**Consequence.** Plugin authors can use kebab-case template names
(`close-ticket`), which read better in the addressable name, while field
names stay compatible with the placeholder regex and JS identifier rules.

### DR-7 — Global scanned before project (project wins)

**Context.** Both layers can define a template with the same name.

**Decision.** Global layer is scanned first; project layer overwrites.
Shadowed names are recorded and warned.

**Consequence.** Project-local overrides "just work" by dropping a file
in `.pi/prompts/`. Users are warned when an override happens, so silent
replacement is visible.

---

*End of guide. The companion playbooks in `playbooks/` walk through authoring
a template and a plugin step by step; the API reference in `reference/02-api-reference.md`
is a quick-lookup table for the types and functions above.*
