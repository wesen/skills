---
name: go-go-os-frontend-rich-widgets
description: Port, clean up, and integrate rich widgets specifically in the `go-go-os-frontend` repo. Use when importing JSX widget sketches from `imports/`, converting them into `packages/rich-widgets/src/*` widgets, migrating styles into `parts.ts` + `theme/*.css`, adding Storybook stories, wiring launcher modules, or deciding local state vs Redux slices for rich widgets.
---

# Go-Go-OS Frontend Rich Widgets

Use this skill for work inside `go-go-os-frontend` that touches the rich-widget package or its import/cleanup pipeline.

## When to use

Trigger this skill when the task involves any of:

- importing a widget from `go-go-os-frontend/imports/*.jsx`;
- cleaning up an existing widget in `packages/rich-widgets/src/*`;
- migrating inline styles to `data-part` + tokenized CSS;
- adding or fixing rich-widget Storybook stories;
- deciding whether widget state should stay local, use seed props, or move into Redux;
- wiring a widget into `packages/rich-widgets/src/launcher/modules.tsx`.

## Workflow

1. Audit the source widget.
   - Read the full import/component first.
   - Inventory fake shell chrome, local state, parser/helpers, and inline style regions.
   - Build a primitive mapping table before coding.
   - Read `references/repo-map.md` for the repo-specific file layout.

2. Remove shell reimplementation.
   - Delete custom app menu bars, title bars, close boxes, desktop backgrounds, fake status bars, and custom overlays unless they are genuinely widget content.
   - Replace with rich-widget primitives such as `WidgetToolbar`, `WidgetStatusBar`, `ModalOverlay`, `CommandPalette`, `Separator`, `SearchBar`, `LabeledSlider`, and engine `Btn`/`Checkbox`.

3. Create the widget package structure.
   - Add `packages/rich-widgets/src/<widget>/`.
   - Start with `<Widget>.tsx`, `<Widget>.stories.tsx`, `types.ts`, `sampleData.ts`.
   - Add `<widget>State.ts` only when seeded stories or durable state justify it.

4. Convert styling the repo way.
   - Add `RICH_PARTS` keys in `packages/rich-widgets/src/parts.ts`.
   - Add widget CSS in `packages/rich-widgets/src/theme/<widget>.css`.
   - Import that CSS from `packages/rich-widgets/src/theme/index.ts`.
   - Move stable visual styling out of inline JSX and into CSS.
   - Keep only dynamic layout values inline.
   - Read `references/cleanup-rules.md` for current CSS/state rules.

5. Apply the current state policy.
   - Local state for pointer/animation/DOM-only concerns.
   - Seed props or seeded stories for widget-local deterministic states.
   - Redux slice only for durable, story-worthy, persistence-worthy, or launcher-observable state.
   - If a widget is exported from `@hypercard/rich-widgets`, prefer a connected path plus a standalone fallback rather than forcing every consumer to provide Redux.

6. Add Storybook before launcher wiring.
   - Add default, empty, dense, compact, and domain-specific state stories.
   - If a key state cannot be reached cleanly through props, add a seeded story.
   - Use `packages/rich-widgets/src/storybook/seededStore.tsx` when the widget has a slice.

7. Wire launcher/export integration last.
   - Export from `packages/rich-widgets/src/index.ts`.
   - Register the widget in `packages/rich-widgets/src/launcher/modules.tsx`.
   - Use a unique `app_rw_<widget>` state key for module reducers.

8. Validate and document.
   - Run `npm run test -w packages/rich-widgets`.
   - Run `npm run storybook:check`.
   - If a rollout ticket is active, update its tasks/changelog/diary and refresh reMarkable uploads as needed.

## Hard rules

- Do not keep fake desktop/window chrome from imports unless it is essential widget content.
- Do not keep large inline style dictionaries; convert them to parts + CSS.
- Do not put `Date`, `Set`, DOM nodes, timer handles, or function updaters in Redux state.
- Do not copy local `useReducer` actions into Redux if they carry callbacks like `updater: (prev) => next`.
- Do not add a package-wide shared widget reducer key for per-widget state; use unique module keys.
- Do not rely on Storybook `play` interactions to reach important states when seed props or seeded store state would be cleaner.

## Current source-of-truth docs in the repo

- OS-07 porting playbook:
  `go-go-os-frontend/ttmp/2026/03/01/OS-07-ADD-RICH-WIDGETS--import-and-integrate-rich-macos-widgets-into-frontend-collection/playbooks/01-widget-porting-playbook.md`
- OS-16 Redux migration guide:
  `go-go-os-frontend/ttmp/2026/03/05/OS-16-RICH-WIDGET-REDUX-SLICE-STUDY--rich-widget-redux-slice-study-migration-design-and-intern-guide/playbooks/01-rich-widget-redux-slice-implementation-guide-for-interns.md`
- OS-17 rollout diary/tasks:
  `go-go-os-frontend/ttmp/2026/03/05/OS-17-RICH-WIDGET-REDUX-ROLLOUT--rich-widget-redux-rollout-and-storybook-parity/`

## References

- `references/repo-map.md`
- `references/cleanup-rules.md`
