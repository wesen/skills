# QA Checklist

## When to run this checklist

Use this checklist at major feature or integration boundaries, not after every small edit or commit. Complete a coherent, visible feature before running its relevant validation gate. Smaller commits are useful checkpoints; they do not warrant full builds, broad test suites or a complete visual/accessibility matrix merely because a commit is being made.

Scope checks to the affected behavior and reuse existing coverage for unchanged components. Run an earlier targeted check only to resolve a concrete uncertainty or material risk, or when explicitly required by the project.

If a gate fails, collect diagnostics, batch related fixes where practical, and rerun the narrow checks needed to confirm those fixes. Do not restart the entire pipeline after each edit. Record passed, failed and deferred checks honestly; an unvalidated checkpoint is not a qualified release.

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
