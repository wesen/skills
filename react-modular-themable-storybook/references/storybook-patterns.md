# Storybook Patterns

## Required stories

1. Default widget
2. Theme overrides (custom tokens)
3. Unstyled mode
4. Custom slots/renderers

## Story structure

- Export a single meta with controls for `themeVars` and `unstyled`.
- Keep stories small; use realistic content for snapshots.

Example (abbreviated):

```tsx
const meta = {
  title: "Widget/Chat",
  component: ChatWidget,
  args: {
    theme: "default",
    unstyled: false,
  },
} satisfies Meta<typeof ChatWidget>;

export const ThemeOverrides: Story = {
  args: {
    themeVars: {
      "--color-bg": "#0b0d10",
      "--color-accent": "#f28c28",
    },
  },
};
```

## Preview checklist

- Check empty state and loading state.
- Validate long messages and overflow cases.
- Validate responsive layout.
