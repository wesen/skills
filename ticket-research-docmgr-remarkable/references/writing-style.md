# Writing Style Guide

Use this style for the primary analysis and diary deliverables.

## Tone

1. Write in clear, direct engineering prose.
2. Prioritize factual statements over hype.
3. Explain reasoning and tradeoffs explicitly.
4. Assume the reader is new to the codebase and needs orientation.

## Structure

Use strong sectioning and stable ordering.

Recommended design-doc order:

1. Executive summary.
2. Problem statement and scope.
3. System orientation: main concept, overall architecture and essential terminology.
4. Current-state analysis (with evidence).
5. Gap analysis.
6. Proposed architecture and APIs.
7. Decision records for major architecture/API choices.
8. Pseudocode and key flows.
9. Implementation phases.
10. Test strategy.
11. Risks/alternatives/open questions.
12. References.

For intern-facing guides, establish orientation in the introduction before source history, subsystem inventories or API catalogs. Define system-specific terms before using them in dependent design claims. Explain the main parts and how they relate in ordinary technical prose; where relevant, identify who owns work, what data is exchanged and what happens over time.

Use a small representative example and a diagram or end-to-end flow when they clarify the architecture. Distinguish existing behavior, the first implementation slice and deferred design. Keep the overview proportional: it is neither an exhaustive glossary nor the full API reference, and requires no fixed page count.

## Evidence Rules

1. Anchor major claims to concrete files.
2. Prefer line-referenced evidence when possible (`nl -ba`).
3. Distinguish observed behavior from inferred behavior.
4. Avoid speculative assertions without evidence.

## Decision Records

For non-trivial architecture/API choices, include compact decision records inline in the design doc instead of burying the choice in prose.

Use this format:

```md
### Decision: <short name>

- **Context:** What constraint or ambiguity forced the decision?
- **Options considered:** Realistic alternatives.
- **Decision:** What was chosen.
- **Rationale:** Why this option fits the evidence and constraints.
- **Consequences:** What this enables, what it makes harder, and what must be validated.
- **Status:** proposed | accepted | superseded
```

Create decision records especially when choosing between viable implementation paths, public API shapes, runtime ownership models, data representation strategies, security boundaries, generated-vs-handwritten code, or compatibility tradeoffs.

## Detail Level

1. Be detailed and exhaustive for architecture docs.
2. Include concrete API sketches where they reduce ambiguity.
3. Include pseudocode for runtime wiring and command flow.
4. Include migration guidance and compatibility notes.

## Clarity Patterns

1. Use numbered lists for steps and plans.
2. Use short code blocks for contracts/commands.
3. Use explicit naming (`Phase 1`, `Phase 2`, etc.).
4. Define unfamiliar terms before the first explanation or design claim that depends on them; do not rely on a later glossary to repair the introduction.

## Diary Style

1. Keep entries chronological.
2. Include commands that were run.
3. Record what worked and what failed.
4. Capture why decisions were made.
5. End with verification and delivery evidence.

