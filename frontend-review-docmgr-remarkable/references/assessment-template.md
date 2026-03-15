# Assessment Template

Use this structure for the primary design-doc.

## Executive Summary

- Current maturity snapshot
- Highest-risk issues
- Highest-leverage cleanup actions

## Current State of Affairs (Long Section)

Cover architecture baseline in depth:

- repo topology and runtime boundaries
- build/storybook setup
- app boot and store composition
- state/event flow summary
- subsystem complexity hotspots

## Subsystem Reviews

Repeat this structure per subsystem:

1. Current design and flow
2. Findings (duplication/deprecation/problematic areas)
3. Why it matters
4. Improvement proposals
5. Migration/implementation plan

## Performance and State Management Notes

- high-frequency event behavior
- selector/render invalidation pressure
- opportunities for external/transient stores

## CSS and Design System Notes

- current token/part architecture
- gaps in reusability
- recommended modular CSS layout

## Roadmap

- Phase 1: low-risk/high-clarity
- Phase 2: medium-risk/high-leverage
- Phase 3+: structural improvements

## Open Questions

List unresolved decisions needed for implementation.

## References

List key file paths used as evidence.
