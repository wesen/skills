---
name: glazed-command-authoring
description: "Create and wire Glazed commands (schema/fields/sections, sources/middlewares, Cobra integration, output defaults, help/logging) for Go CLIs. Use when designing or implementing Glazed commands or upgrading existing command definitions."
---

# Glazed Command Authoring

Use this skill when creating or refactoring Glazed commands. It captures the current conventions, pitfalls, and wiring patterns we used successfully. Keep it lean, but always follow the workflow so commands are consistent and CLI behavior is predictable.

## Quick Start (Minimal Workflow)

1) **Define a command struct** embedding `*cmds.CommandDescription`.  
2) **Define a settings struct** with `glazed` tags.  
3) **Create a constructor** that builds the description using `cmds.NewCommandDescription`, `cmds.WithFlags`, and `cmds.WithSections`.  
4) **Implement `RunIntoGlazeProcessor`** and decode values into your settings struct.  
5) **Build a Cobra command** using `cli.BuildCobraCommandFromCommand` (or a custom wrapper) and register it in your root/group command.

## Canonical Code Skeleton

```go
// 1) Command + settings structs

type FooCommand struct {
    *cmds.CommandDescription
}

type FooSettings struct {
    Limit int  `glazed:"limit"`
    Debug bool `glazed:"debug"`
}

// 2) Constructor
func NewFooCommand() (*FooCommand, error) {
    glazedSection, err := settings.NewGlazedSchema()
    if err != nil {
        return nil, err
    }

    commandSettingsSection, err := cli.NewCommandSettingsSection()
    if err != nil {
        return nil, err
    }

    cmdDesc := cmds.NewCommandDescription(
        "foo",
        cmds.WithShort("Short description"),
        cmds.WithLong(`
Long description.

Examples:
  foo --limit 5
  foo --output json
`),
        cmds.WithFlags(
            fields.New(
                "limit",
                fields.TypeInteger,
                fields.WithDefault(10),
                fields.WithHelp("Maximum number of results"),
            ),
            fields.New(
                "debug",
                fields.TypeBool,
                fields.WithDefault(false),
                fields.WithHelp("Enable debug output"),
            ),
        ),
        cmds.WithSections(glazedSection, commandSettingsSection),
    )

    return &FooCommand{CommandDescription: cmdDesc}, nil
}

// 3) RunIntoGlazeProcessor
func (c *FooCommand) RunIntoGlazeProcessor(
    ctx context.Context,
    vals *values.Values,
    gp middlewares.Processor,
) error {
    settings := &FooSettings{}
    if err := vals.DecodeSectionInto(schema.DefaultSlug, settings); err != nil {
        return err
    }

    row := types.NewRow(
        types.MRP("limit", settings.Limit),
        types.MRP("debug", settings.Debug),
    )
    return gp.AddRow(ctx, row)
}
```

## Field/Section Conventions

- **Preferred constructor**: use `fields.New(...)` (not the older `parameters.NewParameterDefinition`).
- **Struct tags**: `glazed:"flag-name"` is the authoritative mapping.
- **Always decode** with `vals.DecodeSectionInto(schema.DefaultSlug, settings)` instead of reading Cobra flags directly.

## Section Composition

- **Glazed output section**: `settings.NewGlazedSchema()` (adds `--output`, `--fields`, etc).  
- **Command settings section**: `cli.NewCommandSettingsSection()` (adds `--print-parsed-fields`, `--print-schema`, `--print-yaml`).  
- Add **custom sections** (e.g. Zigbee section) via `cmds.WithSections(...)`.

### Per-command output defaults

If a command should default to a specific output (ex: `yaml` + streaming), supply output defaults when creating the glazed section:

```go
glazedSection, err := settings.NewGlazedSchema(
    settings.WithOutputSectionOptions(
        schema.WithDefaults(map[string]interface{}{
            "output": "yaml",
            "stream": true,
        }),
    ),
)
```

Use this for commands that primarily stream events or logs.

## Cobra Integration

- Build the Cobra command with:

```go
cobraCmd, err := cli.BuildCobraCommandFromCommand(cmd,
    cli.WithParserConfig(cli.CobraParserConfig{
        ShortHelpSections: []string{schema.DefaultSlug},
        MiddlewaresFunc: cli.CobraCommandDefaultMiddlewares,
    }),
)
```

- For multiple command groups, create a group `root.go` per directory and call `Register(root, defaults)`.

### Custom middlewares

If you need config/env/profile precedence (like Geppetto), implement a custom `MiddlewaresFunc` and pass it via `cli.WithParserConfig`. Keep precedence explicit and documented.

## Help + Documentation

- Use `cmds.WithLong` with examples for every command.
- Wire the help system at the root using `help.NewHelpSystem()` and `help_cmd.SetupCobraRootCommand()`.
- **Frontmatter YAML** in help docs must be valid. Quote strings that contain colons.

## Logging (recommended)

- Add logging section to root command:

```go
_ = logging.AddLoggingSectionToRootCommand(rootCmd, "appname")
```

- Initialize logging in `PersistentPreRunE`:

```go
PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
    return logging.InitLoggerFromCobra(cmd)
},
```

## Grouping Commands

Two valid patterns:

1) **Explicit Cobra parents** (recommended for larger apps)
2) **Metadata parents** using `cmds.WithParents("group")` (fine for simple sets)

If you use explicit groups, keep this convention:
- one directory per group
- one file per verb
- one `root.go` per group to register subcommands

### Directory Layout (Cobra Groups Mirror Folders)

When using explicit Cobra parent commands (groups), make the **folder structure mirror the CLI tree**:

```text
cmd/<app>/
  main.go                        # root cobra command wiring (imports groups)
  cmds/
    <group>/
      root.go                    # defines the group cobra.Command + registers subcommands
      <verb>.go                  # defines the Glazed command for that verb
    <other-group>/
      root.go
      <verb>.go
```

Practical rule: if you type `myapp <group> <verb> ...`, then `<group>` should be a folder and `<verb>` should be a file inside it.

`root.go` in each group should usually expose `NewCommand() (*cobra.Command, error)` (or `Register(root *cobra.Command) error`) and do the `cli.BuildCobraCommandFromCommand(...)` wiring for its children.

## Streaming Commands

- Use a `--watch` or `--stream` flag.
- If events are long-running, add a duration or timeout and exit cleanly.
- Filter to relevant events before emitting rows.

## Common Pitfalls

- **Pointer to interface**: `schema.Section` is an interface; don’t use `*schema.Section`.
- **Output defaults**: use `settings.WithOutputSectionOptions` on `settings.NewGlazedSchema`.
- **Help frontmatter**: quote strings with colons.
- **Duplicate flags**: don’t add the same section to both parent and child commands.

## Reference: Read these when needed

- Glazed tutorial: `/home/manuel/code/wesen/corporate-headquarters/glazed/pkg/doc/tutorials/05-build-first-command.md`
- Glazed repo code (patterns, sources, sections): `/home/manuel/code/wesen/corporate-headquarters/glazed`
