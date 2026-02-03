# Parts and Tokens

## Goals

- Expose stable styling hooks without leaking internal class names.
- Keep the public contract small and consistent across variants.

## Part/role/state contract

Use `data-*` attributes on the widget root and key elements.

- `data-widget`: root marker (example: `data-widget="chat"`).
- `data-part`: stable styling hooks for key areas.
- `data-role`: semantic roles (author, status, etc.).
- `data-state`: state/variant markers (empty, loading, error, compact, etc.).

Keep the parts list short and user-facing. Example (generic):

- root
- header
- timeline
- message
- message-bubble
- composer
- input
- send-button
- statusbar

Avoid putting transient layout wrappers in `data-part` unless they matter for theming.

## Token categories

Use CSS variables for a theme surface area. Keep tokens grouped by intent:

- Color: `--color-bg`, `--color-surface`, `--color-text`, `--color-muted`, `--color-accent`
- Typography: `--font-family`, `--font-size`, `--line-height`, `--font-weight`
- Spacing: `--space-1`..`--space-6`
- Radius: `--radius-1`..`--radius-3`
- Shadow: `--shadow-1`..`--shadow-3`
- Layout: `--content-max-width`, `--border-width`

## Mapping rules

- Map classes -> `data-part` selectors.
- Map hard-coded values -> CSS variables.
- Preserve semantics: set `data-role` on elements users will target.

## Pitfalls

- Over-rotating on parts: too many parts makes themes brittle.
- High-specificity selectors: keep overrides easy.
- Duplicating tokens with slightly different names.
