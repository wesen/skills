# Repo Map

Use these paths when working on rich widgets in `go-go-os-frontend`.

## Core package

- `packages/rich-widgets/src/` — widget source folders
- `packages/rich-widgets/src/index.ts` — public exports
- `packages/rich-widgets/src/parts.ts` — `RICH_PARTS` registry
- `packages/rich-widgets/src/theme/` — widget CSS files
- `packages/rich-widgets/src/theme/index.ts` — theme import aggregator
- `packages/rich-widgets/src/storybook/frameDecorators.tsx` — standard story frames
- `packages/rich-widgets/src/storybook/seededStore.tsx` — seeded Redux story helper
- `packages/rich-widgets/src/launcher/modules.tsx` — launcher module registration

## Import source

- `imports/*.jsx` — raw sketches to port into rich widgets

## Launcher/store integration

- `packages/desktop-os/src/contracts/launchableAppModule.ts`
- `packages/desktop-os/src/store/createLauncherStore.ts`

## Current long-form playbooks

- `ttmp/2026/03/01/OS-07-ADD-RICH-WIDGETS--import-and-integrate-rich-macos-widgets-into-frontend-collection/playbooks/01-widget-porting-playbook.md`
- `ttmp/2026/03/05/OS-16-RICH-WIDGET-REDUX-SLICE-STUDY--rich-widget-redux-slice-study-migration-design-and-intern-guide/playbooks/01-rich-widget-redux-slice-implementation-guide-for-interns.md`
- `ttmp/2026/03/05/OS-17-RICH-WIDGET-REDUX-ROLLOUT--rich-widget-redux-rollout-and-storybook-parity/tasks.md`

## Current rollout examples

Use these as the canonical current patterns:

- `packages/rich-widgets/src/log-viewer/LogViewer.tsx`
- `packages/rich-widgets/src/log-viewer/logViewerState.ts`
- `packages/rich-widgets/src/calculator/MacCalc.tsx`
- `packages/rich-widgets/src/calculator/macCalcState.ts`
- `packages/rich-widgets/src/calendar/MacCalendar.tsx`
- `packages/rich-widgets/src/calendar/macCalendarState.ts`
