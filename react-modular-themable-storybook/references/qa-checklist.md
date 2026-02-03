# QA Checklist

## Build/compile

- Typecheck passes.
- Lint passes.
- Storybook build or dev preview succeeds.

## Visual/regression

- Default theme matches previous UI.
- Part selectors render expected styles.
- Unstyled mode is usable with custom CSS.

## API stability

- Parts list is minimal and documented.
- Theme tokens are consistent across variants.
- Component slots/renderers are optional and typed.

## Accessibility

- Labels, roles, and focus states preserved.
- Keyboard navigation works.
- Contrast is acceptable in default theme.
