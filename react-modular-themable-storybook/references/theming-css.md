# Theming CSS

## Layering strategy

1. Base layout CSS (`widget.css`): uses `data-part` selectors and tokens.
2. Theme CSS (`theme-default.css`): sets default token values.
3. Consumer overrides: set `:root` or widget-specific overrides.

Keep all selectors scoped to a root `data-widget` attribute to avoid bleed.

## Selector guidance

- Prefer `:where([data-widget="X"])` for low specificity.
- Target parts with `[data-part="..."]` rather than classes.

Example:

```css
:where([data-widget="chat"]) {
  --color-bg: #0f1115;
  --color-text: #f5f7fb;
}

:where([data-widget="chat"]) [data-part="header"] {
  padding: var(--space-3);
  background: var(--color-surface);
}
```

## Unstyled mode

Expose an `unstyled` prop or flag. If `unstyled` is true:

- Do not import base CSS automatically, or skip applying a class/attribute.
- Still render `data-part` attributes for user CSS.

## Tokens vs. structure

- Tokens control visuals (color, spacing, fonts).
- Structure should remain in base CSS to keep layout stable.
- Keep tokens reusable; avoid overly specific names.

## Accessibility

- Use tokens for focus outlines and high-contrast modes.
- Ensure default theme meets contrast guidelines where possible.
