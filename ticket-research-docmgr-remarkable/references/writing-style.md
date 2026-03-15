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
6. Pseudocode and key flows.
7. Implementation phases.
8. Test strategy.
9. Risks/alternatives/open questions.
10. References.

## Evidence Rules

1. Anchor major claims to concrete files.
2. Prefer line-referenced evidence when possible (`nl -ba`).
3. Distinguish observed behavior from inferred behavior.
4. Avoid speculative assertions without evidence.

## Detail Level

1. Be detailed and exhaustive for architecture docs.
2. Include concrete API sketches where they reduce ambiguity.
3. Include pseudocode for runtime wiring and command flow.
4. Include migration guidance and compatibility notes.

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

