# Writing Style for Research Reports

This style guide governs the primary research report written in the ticket workspace (the ttmp design-doc). It is based on the Peter Norvig textbook style and the lessons from the Newton Object Soup research project.

## The Core Principle: Foundational Prose Before Technical Detail

Every section starts with 1–2 paragraphs of foundational prose that develop the idea — explaining **why** a design exists, **what** problem it solves, and **what** insight the reader should carry — before showing code, tables, or diagrams. The reader who understands why can extend the pattern; the reader who only knows how copies it.

## Prose That Develops Ideas

Write in complete paragraphs that advance the argument or explanation. Each paragraph should develop a thought fully. Do not write short, declarative sentences that feel like bullet points in disguise. Do not write wandering preambles that buy time before getting to the point. Start with the point.

## Concrete Over Abstract

Show real code, real output, real API signatures, real historical quotes. Abstract descriptions of patterns are useful, but they land better when grounded in something the reader can see and trace. Quote original sources (with attribution) rather than paraphrasing them vaguely.

## No Analogies

Explain technical systems directly in their own terms. Do not use metaphors such as kitchens, traffic cops, rooms, doors, trains, or factories. If a concept is difficult, clarify it with precise definitions, state diagrams, architecture diagrams, code, and concrete traces instead.

## Breaks in the Rhythm

Use code blocks, tables, diagrams, and bullet points strategically to break up long passages of prose. These are not decorations — they are part of the argument. A table comparing two approaches does work that prose cannot. A Mermaid diagram showing data flow conveys structure that paragraphs obscure.

## The Reader Is Capable

Do not talk down to the reader. Assume they are intelligent and can follow complex ideas if presented clearly. Do not qualify every statement with "of course" or "clearly" or "it goes without saying." Let the ideas speak.

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Fix |
|-------------|--------------|-----|
| Wandering preamble | Signals insecurity, wastes time | Start with the point |
| Hedged non-claims ("could potentially offer certain advantages") | Says nothing | Be direct |
| Vague bullet lists ("Important concepts") | No content | Each bullet is a complete sentence |
| Philosophical throat-clearing | Filler | Show the code, let reader decide |
| Overused qualifiers ("of course", "clearly") | Implies uncertainty | Just say it |
| Analogies instead of precise explanation | Hides technical details | Define the actual entities and transitions |

## Research Report Specific Patterns

### Quote original sources directly

When a source says something important in its own words, quote it verbatim with attribution. This grounds the report in evidence and lets the reader evaluate the source independently.

Example (good):
> "We narrowly rejected SQL in favor of stream storage. Different applications were having to save the same system objects and we were having to duplicate that code."
> — Charles Davies, Symbian/Psion, quoted in Retro Computing Forum

Example (bad):
Davies said they considered SQL but went with stream storage because of code duplication.

### Use comparison tables for systematic analysis

When comparing systems, approaches, or historical platforms, use tables with named columns. Tables do work that prose cannot — they make the comparison scannable and force you to be specific about each dimension.

### Include architecture diagrams

Every non-trivial system deserves at least one Mermaid diagram. Prefer `flowchart TD` for data flow and system architecture, `flowchart LR` for transformation pipelines. Use `style` directives for color highlights on key nodes.

### Provide implementation sketches

Include pseudocode or real code sketches for the key abstractions. The reader should be able to see the data model, the API surface, and the access patterns. This is not "code that runs" — it is "code that teaches."

### Link to sources explicitly

Every source mentioned in the report should appear in the References section with a description, a file path (if downloaded), and a URL (if available). The reader should be able to find the original source from the report alone.

## The Distinction: Report vs. Article

The **ttmp research report** is the primary deliverable. It should be exhaustive, detailed, and written in textbook style. Target 50–80 KB for a substantial research topic. Do not be afraid of length — a report that is too terse is useless.

The **Obsidian vault article** should be a copy of the full report (or a slightly adapted version), not a terse summary. The user has explicitly stated that terse summaries are not useful. The vault article should contain the same depth, the same diagrams, the same code sketches, and the same source links as the ttmp report. The vault is where the user reads; the ttmp is where the research happened.

The vault article lives at `Research/YYYY/MM/DD/` in the Obsidian vault at `/home/manuel/code/wesen/go-go-golems/go-go-parc/`. This is distinct from `Projects/YYYY/MM/DD/` which is for project notes. Research reports go in `Research/`.

If the vault article must be shorter than the report, cut by removing sections entirely (e.g., the diary can stay in ttmp only), not by making every section shallow.
