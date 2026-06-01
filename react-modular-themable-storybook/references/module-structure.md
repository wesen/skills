# Module Structure

## Preferred design-system package layout

For React projects with a reusable component system, use this layered `src/components` layout unless an existing project convention says otherwise:

```
src/
  components/
    foundation/
      Text/
        Text.tsx
        Text.module.css
        Text.stories.tsx
        index.ts
      Heading/
        Heading.tsx
        Heading.module.css
        Heading.stories.tsx
        index.ts
      Caption/
        Caption.tsx
        Caption.module.css
        Caption.stories.tsx
        index.ts
      Divider/
        Divider.tsx
        Divider.module.css
        Divider.stories.tsx
        index.ts
      VisuallyHidden/
        VisuallyHidden.tsx
        VisuallyHidden.module.css
        VisuallyHidden.stories.tsx
        index.ts
      Foundation.stories.tsx
      index.ts
    layout/
      Section/
      Container/
      Grid/
      Stack/
      Split/
      Surface/
      index.ts
    atoms/
      Button/
      Chip/
      Icon/
      index.ts
    molecules/
      SectionHeader/
      ProductCard/
      SearchBox/
      index.ts
    organisms/
      Header/
      Footer/
      ProductGridSection/
      WidgetShell/
      index.ts
    pages/
      HomePage/
      index.ts
    index.ts
```

Layering rule:

```
tokens -> foundation -> layout/atoms -> molecules -> organisms -> pages
```

- `foundation` turns raw/semantic tokens into React APIs for typography, text tone, accessibility utilities, separators, and token documentation.
- `layout` owns structural primitives and repeated composition recipes.
- `atoms` are small product controls or visuals.
- `molecules` are reusable combinations of foundation/layout/atoms.
- `organisms` are full feature blocks, sections, widgets, or application chrome.
- `pages` compose organisms and route/page data.
- Public component folders should keep `XXX.tsx`, `XXX.module.css`, `XXX.stories.tsx`, and `index.ts` together so implementation, styling, documentation, and exports stay synchronized.

Storybook should mirror the same mental model:

```
Design System/Foundation
Design System/Layout
Component Library/Atoms
Component Library/Molecules
Component Library/Organisms
Applications/Pages
```

## Single-widget module layout

For a standalone widget package, use this smaller module shape:

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
