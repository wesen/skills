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
3. Current-state analysis (with evidence).
4. Gap analysis.
5. Proposed architecture and APIs.
6. Decision records for major architecture/API choices.
7. Pseudocode and key flows.
8. Implementation phases.
9. Test strategy.
10. Risks/alternatives/open questions.
11. References.

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

## Decision Records

For non-trivial architecture, API, runtime, representation, security, generated-code, integration, or compatibility choices, include compact decision records in the primary design document instead of burying decisions in prose.

Use this format:

```md
### Decision: <short name>

- **Context:** What constraint, ambiguity, or disagreement forced the choice?
- **Options considered:** What realistic alternatives were considered?
- **Decision:** What was chosen?
- **Rationale:** Why does this fit the evidence and constraints?
- **Consequences:** What does this enable, what does it make harder, and what must be validated?
- **Status:** proposed | accepted | superseded
```

Use decision records especially when a future reader might otherwise re-litigate the choice, such as choosing a runtime harness, public API shape, object representation, naming convention, persistence model, or safety boundary.

## Clarity Patterns

1. Use numbered lists for steps and plans.
2. Use short code blocks for contracts/commands.
3. Use explicit naming (`Phase 1`, `Phase 2`, etc.).
4. Define terms before using them repeatedly.

## Diary Style

1. Keep entries chronological.
2. Include commands that were run.
3. Record what worked and what failed.
4. Capture why decisions were made.
5. End with verification and delivery evidence.

