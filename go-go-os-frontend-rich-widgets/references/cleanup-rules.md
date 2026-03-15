# Cleanup Rules

These are the current repo-specific cleanup rules for rich widgets.

## 1. Shell chrome removal

Imported sketches often fake:

- menu bars
- title bars
- close boxes
- window borders
- desktop textures
- status bars

Remove those unless they are part of the widget’s actual content model. The desktop shell already owns app chrome.

## 2. CSS conversion

Convert stable styling into:

- `RICH_PARTS` keys in `packages/rich-widgets/src/parts.ts`
- widget CSS in `packages/rich-widgets/src/theme/<widget>.css`

Prefer:

- `var(--hc-color-*)`
- `var(--hc-font-family)`
- `var(--hc-color-border)`
- low-specificity `[data-part="..."]` selectors

Avoid:

- giant inline style objects
- injected `<style>` tags inside components
- remote font imports
- duplicated primitive selectors that should live in `primitives.css`

## 3. State policy

Keep local:

- drag ghosts
- hover coordinates
- animation counters
- timer handles
- modal input drafts that are not yet committed

Use seed props or seeded stories:

- selected row/panel
- search query
- palette-open / modal-open states
- filtered views that matter for Storybook only

Use Redux slices:

- durable document/session state
- states that should be reopened or persisted
- states that should be easy to seed in Storybook
- states launcher/desktop features may observe later

## 4. Redux serialization rules

Do not store in slices:

- `Date`
- `Set`
- DOM nodes
- `MouseEvent`
- `setInterval` / `requestAnimationFrame` handles
- callback updaters like `(prev) => next`

Instead:

- store timestamps as numbers
- store enabled sets as arrays
- compute next snapshots before dispatch
- rebuild convenience shapes with selectors / `useMemo()`

## 5. Exported widget rule

If the widget is exported from `@hypercard/rich-widgets`, prefer:

- connected/store-backed path when the slice is present
- standalone local fallback when no widget slice is registered

This keeps package consumers working while launcher and Storybook use the Redux path.

## 6. Storybook minimum matrix

At minimum, add:

- `Default`
- `Empty`
- `Dense` or stressed data
- `Compact` if relevant
- one or more seeded internal-state stories

If the widget has a slice, use `seededStore.tsx` instead of relying on interaction-only `play` steps to reach meaningful states.
