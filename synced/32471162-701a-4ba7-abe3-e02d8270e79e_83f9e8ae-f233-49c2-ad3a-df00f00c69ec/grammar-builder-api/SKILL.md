---
name: "grammar-builder-api"
description: Design (examples-only or implemented) a JS fluent builder API over a mathematical, composable grammar of core components, with opinionated defaults, lambda escape hatches and IR compilation.
---

# Composable-grammar builder APIs

This is a method for designing a JavaScript library or DSL whose surface is a **fluent, immutable builder**. Underneath sits a **small grammar of mathematical sorts and operators**. The library is **opinionated by default**, **open to lambdas everywhere**, and compiled through **inspectable IR levels**. Pure work is decided at compile time; effects and unknown inputs wait for runtime. The same grammar serves three jobs:

1. **Production**: the real outputs.
2. **Iteration**: design spaces, metrics, search, branches and diffs.
3. **Studying the domain and the design process itself**: experiments and meta-design.

The worked example throughout is *galley*, a typography and layout engine. The method is domain-agnostic: charts, music, CAD, scheduling, generative art, data pipelines, simulations, UI layout.

The brief this skill captures, in the user's own words:

> Create a js api fluent builder api based on mathematical composable grammar of core components that can be customized with lambdas but opinionated by default with dag/ir compiler techniques for things that benefit, runtime stuff for others … so we can iterate on structured problem solving based on incoming random text or data. Both iteration in the design process, and for production ready output, and as a flexible toolbox for experimenting on the design process itself, the metadesignprocess design process. Create examples from simple to complex based on the maths and then real world scenarios and use cases and also just scientific studying.

Follow-ups often add a **workbench**: presets, data loading, exports including the IRs, and an agent whose prompt, prompt fragments and initial data are written *in the language itself*, so each preset carries its own tailored agent.

## 0. Pick the mode first

| The user says | Deliver |
|---|---|
| "only examples", "no implementation", "sketch the API" | **Mode A, examples-only.** A README (conventions, grammar table, IR table, defaults, example map) and 25–35 numbered example files on the ladder in §7. Every file must parse (`node --check`); mark results as illustrative. |
| "build it", "make it work", "a library" | **Mode B, implementation.** Engine modules in §8 order, the `g` namespace, a test harness that renders and *looks at* output. |
| "workbench", "presets", "agent", "load my data", "export" | **Mode C, workbench.** Mode B plus presets, notes, data, exports and a per-preset agent (§9). |

Modes build on each other: the Mode A examples become the Mode B acceptance tests and the Mode C presets.

## 1. Find the fundamentals: domain → mathematics

Do this before writing any API. List the domain's nouns, quantities and decisions, then give each one an algebraic structure. The structure is what makes composition principled: it tells you which operators exist and which laws they must obey, and that in turn tells you what the compiler may cache, reorder or rewrite.

| Structure | Smell in the domain | Galley | Elsewhere |
|---|---|---|---|
| **Vector space with units** | quantities you add and scale; mixed units | lengths: pt mm em ch lh pct fr; `resolve(ctx)` is linear | durations, money, coordinates, pixels vs dp |
| **Monoid** (identity, associativity) | concatenation, overlay, merge | item lists; `beside`/`above`/`over`; style merge (idempotent, right-biased) | clips in a timeline, CSG union, middleware |
| **Endomorphism / update** | "change X by f" | `g.update({ size: x => x * 0.9 })` | transforms, patches, reducers |
| **Functor** | map over a container while keeping its shape | themes as `rules.map(update)`; flows | data frames, signals, trees |
| **Lattice / grid** | snapping, alignment, multiples | baseline lattice; `lcm`/`gcd` of two leadings | beat grids, time slots, pixel grids |
| **Homomorphism** | a scale, a series, a ratio ladder | modular scale `s(i) = base·rⁱ` maps (ℤ,+) → (ℝ⁺,×) | musical intervals, colour ramps, zoom levels |
| **Boolean algebra / regions** | inside/outside, wrap, exclusion | runaround shapes, frames | CSG, permissions, masks |
| **Shortest path / DP on a DAG** | choose breaks or partitions with a global cost | Knuth–Plass line breaking, optimal page breaking | segmentation, scheduling, alignment |
| **Constraints / LP** | relations among unknowns | margins, grids, copyfitting | layout engines, timetables |
| **Fixpoint** | an output feeds back into an input | page refs and TOC iterate until stable | cross-refs, autosizing, convergence |
| **Order / objective** | "better", trade-offs | metrics, weighted / lexicographic / Pareto | any optimisation or ranking |

Write the result as a **grammar table**, the spine of the README and the API:

| Sort | Constructors | Operators | Laws / structure |
|---|---|---|---|
| Length | `pt(10)` `em(1)` `ch(66)` `g.len(ctx => …)` | `add sub mul div min max clamp resolve` | vector space; `resolve` linear |
| Style | `g.style({...})` `g.update({...})` `g.rules()` | `with on map` | idempotent monoid; cascade = fold |
| Strategy | `g.lines.knuthPlass()` `.greedy()` `(items, ctx) => …` | params, `ctx.default` | shortest path in a DAG |
| Design | `g.param.range/choice` `g.design(params, p => doc)` | `sample fix where` | product space → documents |

Keep the grammar **small**: 8–16 sorts is typical. Every user-facing feature should be expressible as constructors and operators over these sorts. If a feature isn't, a sort is missing.

## 2. The five conventions (non-negotiable)

| # | Convention | Why |
|---|---|---|
| 1 | **Builders are immutable values.** Every fluent method returns a new builder, and there is no `.build()`. | Branching is `const b = a.lines(...)`. Designs can be hashed, diffed, cached and stored. |
| 2 | **Every slot accepts four things:** nothing (the opinionated default), a value or partial params, a named library strategy, or a lambda `(input, ctx) => output` whose `ctx.default` is the default strategy. | Users *wrap* an opinion instead of replacing it: `(p, ctx) => tweak(ctx.default(p))`. |
| 3 | **Pure unless declared.** Passes, styles, metrics and lambdas are pure; I/O is an explicit effect. | Pure work can be content-addressed, cached, incremental and parallel. Effects mark the compile/runtime boundary. |
| 4 | **Laws are executable.** Monoid, linearity and idempotence are checked by property tests (`g.law.monoid(...)`). | The algebra stays honest, and laws justify optimiser rewrites. |
| 5 | **Every quantity has a unit.** Relative units stay symbolic until a context resolves them. A dimension error is an error. | Late resolution makes one design work across sizes and devices. |

Also:
- **Presets are functions `builder → builder`**: `.use(preset.book, house)`, plus `.with(b => …)` and a raw `.set(key, v)` escape hatch.
- **Every default is visible**: in `summary()`, in a defaults table in the docs, and in the IR provenance ("this 8.5 pt came from rule `.caption`").

## 3. Opinionated defaults

Write the defaults as a table: **decision | default | why | one-line override**. Three calls should give a good result (`g.doc().content(text)` → a well-set page). Each row is then one line away from changing, at four levels of control:

```js
doc.lines({ tolerance: 400 })                                    // tweak the default's params
doc.lines(g.lines.greedy())                                      // swap in a library strategy
doc.lines((para, ctx) => para.isHeading ? g.lines.balanced() : ctx.default)  // wrap the default
doc.set('lines', { name: myBreaker })                            // raw escape hatch
```

Defaults should be the **domain's best practice**, not the simplest thing: galley defaults to Knuth–Plass, Liang hyphenation, a 66-character measure and widow/orphan avoidance. Name where each default comes from.

## 4. Compiler architecture: DAG of passes, IR levels, staging

**IR levels.** Number them, give each one a question it answers, and make each one dumpable as readable text and as JSON:

| Level | Galley name | Question it answers |
|---|---|---|
| L0 | source | What did we receive? |
| L1 | semantic | What is it (headings, tables, refs) with stable ids? |
| L2 | styled | Why is this 8.5 pt? (provenance per property) |
| L3 | items | What are the primitive units (boxes, glue, penalties)? |
| L4 | decisions | What did the algorithm choose, and at what cost? |
| L5 | placed | Where does everything go, and why there? |
| L6 | paint | The display list that every backend reads |

**Pass discipline.**
- Each pass is named, timed and traced: `trace: [{ pass, level, ms, note }]`.
- Each decision is recorded with its reason: `decisions.push({ page, kind, reason })`.
- **Provenance**: the cascade records which rule set each property.
- **Content-addressed caching per unit of work** (paragraph, cell, node). The key must include *everything that changes the output*: text, the relevant style including inline children's styles, width, strategy identity (including a lambda's identity), parameters and resolved refs. It must exclude what doesn't affect the result (galley ignores vertical-only properties when caching line breaks). Wrong keys give stale output or a cache that never hits; test both.
- **Fixpoints** for feedback (cross-references): iterate until the values stop changing, cap the iterations (4), and report convergence in the trace.
- **One display list (L6) feeds every backend**: PDF, SVG, PNG, HTML, e-ink. **Measure with the same data you print** (galley measures with the same font metrics and glyph ids it embeds), so what you measure is what you get.
- **Lower to lossy targets honestly.** When exporting to a format that can't express the IR (reflowable HTML/CSS), produce a *lowering report* of what is kept, approximated and dropped. Lower from the IR's actual distribution, not from a representative sample: use the most common style per selector plus variant classes.

**The Program object** returned by `compile()` is the inspection API, and the agent and the UI use it too:
`summary() · metrics() · diagnostics · trace · layout.decisions · why(target) · node(id) · find(kind|pred) · style(id) (with provenance) · linesOf(id) · hit(x, y) · pageOf(id)`

**Staging rule of thumb (compile time vs runtime).**
- Input known and work pure → compile time, cached by hash.
- Input unknown but from a small finite domain → tabulate it at compile time.
- Input unknown and continuous → emit a residual program; linear dependence can give closed-form breakpoints.
- Effects (network, clock, live data, user input) → always runtime.

**Diagnostics are data**, each with a level, kind, location and message, and **metrics are a registry** (`name, level, dir: min|max, unit, about`). Both feed the UI, the agent and the objectives.

## 5. Design spaces, objectives, search: iteration as a value

```js
const d = g.design({
  size:    g.param.range(9, 12, { step: 0.5, default: 10.5 }),   // lengths keep their unit in ranges
  leading: g.param.choice([1.25, 1.35, 1.45], { default: 1.35 }),
  measure: g.param.choice([ch(55), ch(66), ch(75)]),
}, p => base.scale({ base: p.size }).rhythm(p.size * p.leading).measure(p.measure),
{ objective: g.objective.weighted({ spacingSD: ['spacingSD', 4], hyphens: ['hyphens', 0.3], pages: ['pages', 1] }) })

const r = await g.search.lhs(d, { budget: 24 })   // grid | random | lhs | descent
r.best.point; r.table()                            // ranked, with every metric
g.evaluate(objective, g.compile(d.at(point)))      // synchronous scoring inside scripts
```

- **Objectives compose**: `minimize`, `maximize`, `weighted`, `lexicographic`, `require` (feasibility), and custom `g.metric(name, fn, { dir })`. Show where weighted and lexicographic rankings disagree; that disagreement is the trade-off.
- **Param defaults** take a `default` option and snap to the grid. Without one, a design starts at the middle of each range.
- **Search shares the cache**, so candidates differing in one knob reuse every unaffected unit of work. That is what makes search cheap.
- **Meta-design**: the design process is also a value (`g.process.step/diverge/converge/critique/loop`), so processes can be compared, cached and studied, including "designing the objective" and running experiments with pre-registered hypotheses.

## 6. Ingest: structured problem solving on random input

Incoming text or data is classified (`g.ingest.auto(src) → { kind, confidence, ranked, features }`) and routed to a design, where each route is a preset function. Everything parses to L1 with stable ids. A router preset is a strong first example: load any file and watch the design adapt.

## 7. The example ladder (Mode A deliverable; also the docs and presets of Modes B and C)

| Section | Files | Content |
|---|---|---|
| **A. The maths, simple → complex** | 01–12 | units and measure · scales and rhythm · primitive items · composition algebra · the core optimisation · regions and flow · constraints · style monoid · placement and floats · compiler DAG/IR · staging · backends |
| **B. Real-world scenarios** | 20–27 | quick start (zero config → preset → tweak → lambda) · 5–7 genre scenarios (galley: novel, magazine, paper, e-ink, data report, random-text ingest, newspaper) |
| **C. Design process** | 30–34 | design spaces · objectives and metrics · search · property testing and fuzzing · variants, branches, diffs |
| **D. Scientific study** | 40–42 | factorial experiments over the engine · a human-study protocol · corpus measurement |
| **E. Meta-design + capstone** | 50–51, 60 | process as a value · designing the design process · one end-to-end capstone |

Each file opens with a header comment: title, the model in 3–6 lines, and what to notice. The code reads as real usage. Results go in `// →` comments marked as the illustrative *shape* of a result. Laws are shown as assertions. Reuse one small set of sample texts and datasets throughout.

The README carries the five-conventions table, the grammar table, the IR-levels table, the staging rule, the defaults table and the example map. Check that every file parses.

## 8. Implementation order (Mode B)

The engine is DOM-free; the browser layer is separate.
1. `units`: the value type with symbolic units (template T1).
2. `measure`: ratios, scales, lattices, canonical geometry (galley: paper sizes, margin canons).
3. Domain data loaded at build time, such as galley's font metrics, kerning and ligatures. Build it once, compactly (dedupe rows and columns of class tables), and use the same bytes to render and to embed.
4. `ingest`: parsers to L1 with ids; a classifier.
5. `style`: rules, selectors, specificity, cascade with provenance (T4).
6. The core algorithms as pure functions over primitive items (galley: line breaking, page breaking).
7. Layout/placement → `paint` (L6 display list) → backends.
8. `compile`: passes, trace, cache, fixpoint, the Program (T5).
9. `metrics`, `design`/`search` (T6), `exports` (including IR dumps and an IR bundle zip).
10. `api`: the `g` namespace (T2, T3), presets and `agent()`.

**Test harness (essential):** compile every preset or example, render to SVG, rasterise with a headless browser, and **look at the pages**. Print one line of metrics per preset and keep a before/after diff of page counts when you change the engine. For each subsystem, keep a tiny probe script you can bundle and run.

## 9. Workbench and per-preset agents (Mode C)

- **A preset is a folder:** `script` (a function body returning a builder or a design), `notes.md` (lede, "**Try it.**" call-outs with deep links into the UI, the maths, "Where next"), `meta.json` (id, title, group, about, tries, data, main), and data files. A build step generates the index and skips incomplete folders, so parallel authors never break each other.
- **Script scope:** `g`, `data` (`data.main`, `csv/table/json/image/fonts`), the units, `rules`, `agent`, `design`, `param`. Scope names can't be redeclared, so document which ones are taken.
- **The agent spec is part of the language:**
  ```js
  agent({ role: 'a book designer who …', prompt: 'Prefer …; never …',
          fragments: { 'protect openings': '…', 'explain the maths': '…' }, defaultFragments: ['protect openings'],
          tries: ['…', '…'], data: { constraints: … }, tier: 'default', effort: 'medium' })
  ```
  The workbench merges it into the agent's briefing. Fragments become toggle chips, `tries` become suggestions, and `tier`/`effort` set the starting model and thinking level.
- **One-tool agent:** a single `eval` tool runs code against a scoped API: `editor.get/set/edit/check` (check compiles a variant without touching the editor), `compile`, `metrics`, `why`, `ir.text(level, { node })`, `data.*`, `presets.list/get/load/save`, `view.*`, `explore.run`, `exports.*`, `chat.table/code/note`.
  - Modes: Auto, Ask (approve each step) and Read-only (writes throw).
  - Snapshot before every step so the user can revert it.
  - Results go back as YAML capped at a few thousand characters.
  - The reference shown to users and the one given to the agent come from **one source**.
- **Data:** load or drop text, Markdown, CSV, JSON, images and fonts; "use as content" switches `data.main`. Fonts parse in the page and join the library under their family name.
- **Exports** are built from L6, plus the IR bundle (manifest, trace, diagnostics, every level as text and JSON), single levels, the preset file and the source.
- **Many presets in parallel**: write a brief (file layout, conventions, notes house style, data rules, validation commands, engine-change etiquette, report format) and give each author a disjoint ID range. Make the tooling safe for concurrent use: write `meta.json` last, generate the index atomically, use per-process output files, and keep engine edits surgical with a full-suite re-run afterwards.

## 10. Templates

**T1. A value type with symbolic units (vector space, linear resolution)**
```js
const ABS = { pt: 1, mm: 72 / 25.4, in: 72, px: 0.75 };
export class Length {
  constructor(terms = {}, lambda = null) { this.terms = terms; this.lambda = lambda; }
  static of(v) { return v instanceof Length ? v : typeof v === 'number' ? new Length({ pt: v }) : typeof v === 'function' ? new Length({}, v) : parse(v); }
  add(b) { b = Length.of(b); if (this.lambda || b.lambda) return new Length({}, c => this.resolve(c) + b.resolve(c));
    const t = { ...this.terms }; for (const [u, v] of Object.entries(b.terms)) t[u] = (t[u] || 0) + v; return new Length(t); }
  mul(k) { if (k instanceof Length) throw new TypeError('DimensionError: Length × Length'); /* scale every term */ }
  resolve(ctx = {}) { /* Σ coef × (pt | ctx.fontSize for em | ctx.leading for lh | ctx.measure/100 for pct) */ }
  toString() { /* '2lh - 4pt' */ } toJSON() { return this.toString(); }
}
export const pt = v => new Length({ pt: v }), em = v => new Length({ em: v }); // …
```

**T2. An immutable builder; presets are functions**
```js
class Doc {
  constructor(spec = {}) { this.spec = Object.freeze({ ...spec }); }
  _with(p) { return new Doc({ ...this.spec, ...p }); }
  lines(x) { return this._with({ lines: slot(x, this.spec.lines) }); }
  styles(r) { return this._with({ rules: (this.spec.rules || rules()).with(r) }); }
  use(...ps) { return ps.flat().reduce((b, p) => (p ? p(b) || b : b), this); }
  with(fn) { return fn(this) || this; }
  set(k, v) { return this._with({ [k]: v }); }
  agent(o) { return this._with({ agent: mergeAgent(this.spec.agent, o) }); }
}
const preset = (name, fn) => Object.assign(b => fn(b), { presetName: name, toString: () => `preset(${name})` });
```

**T3. The four-way slot**
```js
const strat = (name, params) => ({ isStrategy: true, name, params });
function slot(x, prev) {
  if (x == null) return null;                                     // the default
  if (x.isStrategy) return x;                                     // a library strategy
  if (typeof x === 'string') return strat(x);                     // by name
  if (typeof x === 'function') return strat(x);                   // a lambda; it gets ctx.default when called
  return strat(prev?.name || 'default', { ...(prev?.params || {}), ...x });  // partial params tweak the current one
}
// when calling: const run = s => typeof s.name === 'function' ? (i, c) => s.name(i, { ...c, default: DEFAULT }) : LIB[s.name];
```

**T4. A cascade with specificity and provenance**
```js
// rules: [{ sel, decl, spec: [ids, classes, kinds], order, src }]; values may be functions of the inherited value
function cascade(node, parentStyle, rules) {
  const hits = rules.filter(r => r.sel(node)).sort((a, b) => cmp(a.spec, b.spec) || a.order - b.order);
  const st = { ...inherited(parentStyle) }, src = {};
  for (const r of hits) for (const [k, v] of Object.entries(r.decl)) { st[k] = typeof v === 'function' ? v(st[k]) : v; src[k] = r.src; }
  node.style = st; node.styleSrc = src;                            // provenance for why() and the L2 dump
  for (const c of node.children || []) cascade(c, st, rules);
}
```

**T5. A compile pipeline with trace, cache, fixpoint and Program**
```js
export function compile(spec, env) {
  const trace = []; const T = (pass, level, fn, note) => { const t = performance.now(); const r = fn(); trace.push({ pass, level, ms: +(performance.now() - t).toFixed(2), note: note?.(r) }); return r; };
  const l1 = T('parse', 'L1', () => ingest(spec.content));
  T('cascade', 'L2', () => cascade(l1, docStyle(spec), rulesOf(spec)));
  let refs = new Map(), layout, it = 0;
  do { it++; const prev = refs;
    const items = T('items+decisions', 'L3–L4', () => breakAll(l1, { cache, key: n => hash([text(n), styleKey(n), width, strategyId, refsKey(n, prev)]) }));
    layout = T('place', 'L5', () => place(items, spec)); refs = collectRefs(layout);
    if (!hasRefs(l1) || same(prev, refs)) break; } while (it < 4);
  const paint = T('paint', 'L6', () => paintAll(layout, spec));
  return makeProgram({ spec, l1, layout, paint, trace, diagnostics: diagnose(layout), iterations: it });
}
```

**T6. Designs and search**
```js
const design = (params, fn, { objective } = {}) => ({ isDesign: true, params, fn, objective,
  defaults: () => Object.fromEntries(Object.entries(params).map(([k, p]) => [k, p.default ?? p.values[(p.values.length - 1) >> 1]])),
  at(pt) { return fn({ ...this.defaults(), ...pt }); } });
async function search(d, { sampler, objective = d.objective, budget }) {
  const ranked = sampler(d).slice(0, budget).map(point => { const prog = compile(d.at(point)); return { point, ...evaluate(objective, prog) }; })
    .sort((a, b) => (a.feasible === b.feasible ? a.score - b.score : a.feasible ? -1 : 1));
  return { ranked, best: ranked[0] };
}
```

## 11. Pitfalls this method has hit (check each)

- **Duck-typing collisions.** A value type with `.resolve()` was mistaken for a "canon" object that also has `.resolve(page)`. Check `instanceof` and primitives *before* checking for methods.
- **Cache keys.** A per-unit strategy lambda that isn't in the key returns the same cached result for two different settings. Inline children's styles must be in the key too, and cosmetic or vertical-only properties should stay out of it. Note that stats from the last fixpoint iteration under-report breaks.
- **Ids.** Content assembled from several sources produces duplicate ids (`p1` twice), so renumber in document order.
- **Frozen specs and cloning.** Deep-copying with JSON loses functions such as lambdas and chart renderers. Write a clone that keeps functions by reference.
- **Two numberings.** A page's position in sequence is not its printed number (the folio). Name both (`page:3` vs `folio:3`, `pageMap` vs `pageOf`) and use positions in the UI.
- **Namespace spreads shadow names.** `g.em` (an emphasis constructor) overwrote the unit `em`. Document which bare names scripts must use.
- **Parameter defaults.** Give them as an option (`{ default }`) rather than by mutating the param object.
- **Strict grids.** Snapping must never set text tighter than solid (a 14 pt line on a 13.5 pt grid takes two grid lines). Keep-together and keep-with-next are different relations: a "keep together" built from keep-with-next chains the following block in too.
- **Measure what you print.** Use one font database (metrics, kerning, ligatures, glyph ids) for measuring and for embedding. For characters a face lacks, fall back by splitting runs, not by drawing a missing-glyph box.
- **Unsupported inputs fail loudly and helpfully.** Say what to load instead (galley: "WOFF2 needs Brotli … load the TTF, OTF or WOFF").
- **Text extracted from layout fragments** needs gap-aware joining, or you get "emphasis ." with a space before the full stop.
- **Device or target settings belong to the data that implies them.** A device page carries its pixel density, so exports default to the panel's exact pixels.
- **Defaults compound.** A narrow glue stretch plus narrow columns forces last-resort line breaks; surface that in diagnostics rather than hiding it.

## 12. Deliverable checklist

- [ ] The grammar table (sorts, constructors, operators, laws) exists, and every feature maps onto it.
- [ ] The five conventions are stated and honoured: immutable builders, four-way slots, purity, executable laws, units.
- [ ] A defaults table (decision | default | why | override), visible at run time.
- [ ] IR levels are named, each dumpable as text and JSON, with trace, decisions, provenance and `why()`.
- [ ] The cache keys, fixpoint and staging rule are written down.
- [ ] Metrics registry, diagnostics, design spaces, objectives and search, with an example where weighted and lexicographic rankings disagree.
- [ ] The example ladder A→E, from maths to scenarios to process to science to meta, all parsing (Mode A) or all compiling and rendered and looked at (Modes B and C).
- [ ] Mode C: presets with notes, data and a tailored `agent({...})`; one-tool agent with modes, revert and capped results; data loading; exports including IR bundles; one reference source for users and agent.
