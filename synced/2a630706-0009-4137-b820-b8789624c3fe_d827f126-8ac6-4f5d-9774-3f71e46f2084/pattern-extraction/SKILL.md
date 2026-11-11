---
name: "pattern-extraction"
description: "Find the reusable, interesting parts of an existing codebase and write them up as a portable pattern language (GoF and Alexander style): an extraction map, then markdown chapters, then an optional refactoring plan."
---

# Pattern extraction

Given a project that has been built, find the parts that would make independent, composable components, and write each one up as a design pattern that works in any codebase. Write in the style of *Design Patterns* (Gamma, Helm, Johnson, Vlissides) and Christopher Alexander's *A Pattern Language*. The result is conceptual, not a prescription for this project: pseudocode, forces and consequences, with the project as the running example.

## When to use

- "What in this codebase could be extracted into libraries or packages?"
- "Write up the reusable patterns in this project."
- "Turn what we built into a design pattern chapter (or book)."

Not for a code review, or for documenting the project's own API. Those stay about this project.

## The three parts

The work comes in three parts. Each ends with a stop for the person.

### Part 1. The extraction map (in chat). Mandatory checkpoint.

List the candidate components, each with:

- its seam: the interface between the generic part and the project-specific part;
- the rough share of its code that is generic;
- what blocks extraction (global state, import cycles);
- three other domains where it applies.

Add the prerequisite fixes, what to leave in place, how the pieces would compose, and a suggested order.

**Always stop here and wait for the person to approve, trim or reorder the list.** Do this even if they asked to go straight through, and even if no one is watching. In that case, end the run with the map. Writing is the expensive part; the map is where the person redirects cheaply.

### Part 2. The pattern language (markdown files).

Write one overview and one chapter per approved component, as markdown files. Use `docs/patterns/` unless the person names another place:

```
docs/patterns/
  00-overview.md
  01-<pattern-slug>.md
  02-<pattern-slug>.md
  …
```

Link chapters to each other with relative links (`[Chapter 3](03-temporal-goal-monitor.md)`). The overview links to every chapter.

When this part is done, give one or two lines on what was written and where. Then offer Part 3 in one sentence.

### Part 3 (optional). The refactoring plan.

Write it only if the person wants it, as `docs/patterns/extraction-plan.md`. Unlike the chapters, it is about this project:

1. **Prerequisites.** The fixes that unblock everything: module-level state moved into a context object, import cycles broken, hidden dependencies made explicit. Give file names.
2. **Order.** Which package to extract first and why. Smallest, cleanest seam first; the biggest framework last.
3. **Per package:**
    - which files and functions move;
    - the public interface, as a short signature list;
    - what stays behind and how it now uses the package;
    - the chapter it implements.
4. **Safety net.** The existing tests, fixtures or examples that act as the regression suite. Name the command that runs them before and after each step.
5. **What not to extract,** and why.

## Workflow

### 1. Survey (cheap, mechanical)

Map the code before reading it in depth.

- **Size:** line counts per file, so you know where the weight is.
- **Import graph:** who imports whom. Look for cycles, which block extraction, and for leaf modules with no imports, which are free already.
- **Export surfaces:** what each module offers.
- **Module-level mutable state:** counters, registries, an "active" anything, reset functions. These make two instances in one process collide.
- **README, architecture notes and tests:** the authors' own view of the parts.

Useful commands (adapt to the language):

```sh
wc -l src/**/*.{js,ts,py} | sort -n | tail -30
rg -o "from ['\"][^'\"]+['\"]" -r '$0' src | sort | uniq -c        # JS/TS imports
rg -n "^(import|from) " --type py src                                 # Python imports
rg -n "^(let|var) |^export let |new Map\(\)|_reset|global " src     # module-level state
```

### 2. Recognize candidates

The signals, strongest first:

1. **The same idea written twice** in different subsystems. Two copies of one idea is the strongest evidence that it is a pattern.
2. **A domain-free core with a domain-specific edge.** A goal combinator knows nothing about balls; only its atoms do. Test: can you name the interface between core and edge in about five functions?
3. **Several callers or outputs for one thing.** The same runner for the editor, the checker and an agent. The same drawing code for screen, export and tests.
4. **A small interface over a large implementation.**
5. **A surface that people or agents touch**: error messages, explanations, controls, undo.
6. **A trade-off between forces resolved on purpose.** For example, fluent chaining against safe sharing, resolved by immutable values.

Bugs the project fixed, and design debts it carries, are not candidates. Record them as **lessons**; they become the implementation notes, and they are the most valuable lines in the chapters.

Anti-signals (leave these in place):

- the domain vocabulary itself (catalogs of kinds, game rules, business entities);
- glue and the application shell;
- anything an established library already does better (a hand-written markdown renderer).

### 3. Triage and checkpoint

For each candidate, decide:

- **Seam.** Name the interface in a line.
- **Generic share.** Roughly how many of its lines would come out.
- **Blockers.** What must change first.
- **Portability.** Name three other domains where it applies. With fewer than three, it is a project idiom, not a pattern; drop it or fold it into another.
- **Cost.** How hard it is to extract.

Present the map grouped as "cleanest to extract", "worth it with some surgery" and "ambitious", then stop (Part 1).

### 4. Write the language (Part 2)

1. **Overview first.** It fixes the pattern names, numbers and groups, so chapters can cross-reference them.
2. **Then one chapter per file,** in the order of the map, using the chapter template below.
3. **Drawings:** where the shape is the point (a state machine, a command's path, a pipeline, the pattern map), use a ```mermaid block, with a sentence under it on how to read it. Keep each diagram under about 12 nodes.

### 5. Verify

Run the review checklist at the end of this skill before handing over.

## Chapter template

Use these sections, in this order, as `##` headings. Target 1,500 to 2,500 words per chapter.

| Section | What goes there |
| --- | --- |
| **Title** | `# Chapter N · <Pattern Name>`, then an italic subtitle of one line saying what it does. |
| **Intent** | Two or three sentences: what the pattern does and for whom. |
| **Also known as** | Other names readers may know it by. |
| **Motivation** | A concrete scenario from the running example, showing how the naive approach fails (two to four specific failures). Then at least two other domains with the same problem. |
| **Problem** | One bold sentence. |
| **Forces** | Four to seven bullets, each a tension between two goods: "**Fluency against reuse.** Chaining reads well, but chaining onto a shared object changes it for every holder." |
| **Solution** | One bold paragraph starting "Therefore:". It is the part a reader remembers, so make it complete on its own. |
| **Applicability** | Use it when …; do not use it when … (always include the second). |
| **Structure** | A table of participants and their responsibilities. |
| **Collaborations** | Numbered steps of how the participants work together, with a mermaid diagram only when the shape is the point. |
| **Sketch** | Language-neutral pseudocode of the shape, with sections commented, ending with the pattern in use. |
| **Implementation notes** | Eight to eleven numbered notes. Each is a decision or a trap, with a bold lead. The project's real lessons go here, named plainly: "This is the bug the originating project shipped." |
| **Variations** | Three or four named alternatives, each with its trade-off. |
| **Consequences** | Bullets marked + and −, three or four of each. |
| **Known uses** | Real systems, libraries, papers or tools only. Prefer well-known ones. |
| **Related chapters** | Links to the chapters this one connects to, plus classic GoF patterns where they apply (Builder, Command, Memento, Composite, Decorator, Interpreter). |

## Overview template

`00-overview.md` holds:

1. **The kit and the quality.** What kind of system these patterns serve, and the quality they aim for, in one paragraph with a few bullet questions it answers.
2. **The running example.** The originating project in one paragraph. Say that nothing depends on it.
3. **How each pattern is written.** The template and the star rating: two stars means close to invariant; one star means a good form among several.
4. **Pseudocode conventions.** The table below.
5. **The pattern map.** A mermaid diagram of the patterns in groups, with arrows reading "is completed by", plus a sentence on how to read it.
6. **The chapters.** One line and one link per chapter.
7. **Using the language.** The order in which to introduce the patterns, each when its need first shows.
8. **All of them in one sketch.** Pseudocode using every pattern together, with comments naming each pattern.
9. **The same language in other systems.** A table with four rows (other kinds of system) and columns for the key patterns.
10. **What to leave out,** and **Further reading** (real references only).

## Writing rules

- **Conceptual over prescriptive.** Pseudocode shows the shape. No library names, framework calls or host-language tricks in a sketch.
- **Portable.** Project identifiers appear only in the running example and in notes about the originating project. Each chapter must make sense with another domain swapped in.
- **Honest.** Name the project's own mistakes and debts in the implementation notes. A pattern book that only shows the good parts teaches less.
- **Named by what it does.** "Journaled World", "Temporal Goal Monitor", "Narrow Pen", not "LiveManager" or "Utils".
- **Specific.** Real numbers from the project ("a pipeline in milliseconds", "sixty rehearsals per turn"), real failures, real names in known uses.
- **Plain prose.** Short sentences, one idea each. Bold leads on list items. No hype words.
- **Consistent.** The same pseudocode conventions, participant names and chapter numbers everywhere. Keep example ids consistent with the code beside them.

## Pseudocode conventions

Put this table in the overview and follow it everywhere:

| Notation | Means |
| --- | --- |
| `value T:` | an immutable record type; its methods return new values |
| `copy(x, f: v)` | x with field f replaced by v |
| `a ⊕ b` | map a with b's entries laid over it |
| `xs ++ ys` | list concatenation |
| `f(a) → B` | a signature: f returns a B |
| `x → expr` | an anonymous function |
| `match x:` | case analysis over the forms x can take |
| `refuse(kind, …)` | return a structured refusal: kind, message, hints, fix, where |
| `-- text` | a comment |

## Review checklist

Before handing over Part 2 (and Part 3 if written):

- [ ] **Known uses are real.** Every system, paper and date is one you know well or have looked up. Remove anything you cannot stand behind.
- [ ] **Claims about the project are true.** Every "the originating project did X" is checked against the source. In Part 3, every file and function named exists.
- [ ] **Each chapter is portable.** Reread it with another domain from its own Motivation as the running example; it still makes sense.
- [ ] **Links and cross-references hold.** Every relative link resolves. Chapter numbers, pattern names and participant names match across files.
- [ ] **Sketches are consistent.** The same conventions; ids, line numbers and values in examples agree with the code around them.
- [ ] **Every chapter has "do not use it when"** and at least one − consequence.
- [ ] **Mermaid blocks parse.** Render each one (for example with `mmdc`, the Mermaid CLI, if available) and fix syntax errors.
- [ ] **Fresh eyes.** Have one chapter reviewed by a separate agent that has not seen the drafting. Ask whether it is longer than a reader needs, whether the solution paragraph stands alone, and whether a newcomer could apply the pattern in another codebase.