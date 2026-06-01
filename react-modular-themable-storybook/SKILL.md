---
name: react-modular-themable-storybook
description: Build or refactor React UI into a modular, reusable, themeable, Storybook-ready package. Use when asked to extract a widget into a component module/library, create theming APIs (CSS variables/parts), add slots or renderers, migrate styles into tokenized CSS, or produce Storybook stories that demonstrate default, themed, and unstyled variants.
---

# React Modular Themable Storybook

## Overview

Create a reusable React UI package with a stable public API, theme tokens, part-based styling hooks, and Storybook coverage. Use this to modularize an existing widget without changing behavior, while enabling custom styling and composition.

## Standard React design-system decomposition

When scaffolding or refactoring a React design-system package, prefer this stable layered layout unless the project already has a stronger convention:

```text
src/components/
  foundation/  # tokens made usable in React: Text, Heading, Caption, Divider, VisuallyHidden
  layout/      # structural primitives: Section, Container, Grid, Stack, Split, Surface
  atoms/       # smallest product controls: Button, Chip, Icon, Badge
  molecules/   # composed reusable UI: Card, SectionHeader, SearchBox
  organisms/   # feature/section blocks: ProductGridSection, Header, Footer, Widget
  pages/       # routed/page-level compositions
```

Ownership rule of thumb:

```text
tokens -> foundation -> layout/atoms -> molecules -> organisms -> pages
```

- `foundation` owns typography roles, text tones, accessibility helpers, separators, and token documentation stories.
- `layout` owns repeated structural recipes and spacing/container/grid behavior.
- `atoms` own small interactive or visual product controls.
- `molecules` compose foundation/layout/atoms into reusable product UI.
- `organisms` compose molecules into feature sections or widgets.
- `pages` wire organisms into full experiences.
- Every reusable component directory should include an `XXX.stories.tsx` file next to `XXX.tsx` and `XXX.module.css` unless the component is private implementation detail only.

Keep Storybook hierarchy aligned with the same decomposition:

```text
Design System/Foundation
Design System/Layout
Component Library/Atoms
Component Library/Molecules
Component Library/Organisms
Applications/Pages
```

Avoid collapsing these layers into a generic `Box`/style-prop system unless the project explicitly requires it.

## Workflow (high-level)

1. Inventory the existing UI.
   - Enumerate visual regions, variants, and states.
   - Identify "public" parts that should be themeable.

2. Define the public API and theming contract.
   - Choose a `data-*` part/role/state schema.
   - Decide how styles are layered (base layout vs. token theme).
   - Define extension points (slots, renderers, component overrides).
   - See `references/parts-and-tokens.md`.

3. Modularize and move code.
   - Extract components into a dedicated module folder.
   - Introduce a single top-level widget entrypoint + index exports.
   - Preserve behavior and accessibility attributes.
   - See `references/module-structure.md`.

4. Convert styles to tokens + parts.
   - Replace class selectors with `data-part` + CSS variables.
   - Keep selectors low-specificity and scoped to a root attribute.
   - Provide `unstyled` mode that omits base CSS.
   - See `references/theming-css.md`.

5. Wire Storybook.
   - Add stories for default, themed, unstyled, and custom renderers.
   - Use controls to expose key theme variables and slots.
   - See `references/storybook-patterns.md`.

6. Validate and document.
   - Run typecheck/lint/build.
   - Update diary/tasks, ensure migration notes are clear.
   - See `references/qa-checklist.md`.

## Decision cues

- Prefer CSS variables for theme tokens and `data-part` selectors for stability.
- Use component slots/renderers for structural customization; keep CSS for visuals.
- Keep API additive and non-breaking; move legacy assets rather than deleting.

## References

- `references/parts-and-tokens.md`
- `references/module-structure.md`
- `references/theming-css.md`
- `references/storybook-patterns.md`
- `references/qa-checklist.md`
