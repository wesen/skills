# Module Structure

## Suggested layout

```
src/
  widget/
    index.ts
    Widget.tsx
    types.ts
    parts.ts
    components/
      Header.tsx
      Timeline.tsx
      Composer.tsx
    styles/
      widget.css
      theme-default.css
    utils.ts
```

## Patterns

- `Widget.tsx` is the only public entrypoint; it composes subcomponents.
- `index.ts` re-exports public types and the widget.
- `types.ts` contains the external API for slots/renderers/theme props.
- `parts.ts` is the single source of truth for `data-part` names.
- `styles/` contains:
  - `widget.css` for layout and structure using tokens.
  - `theme-default.css` for default token values.

## Behavioral guidance

- Preserve existing behaviors before refactoring styling.
- Extract UI sections into components only when it clarifies ownership.
- Keep components presentational; pass state from the widget.
- Avoid creating cross-cutting dependencies between parts.
