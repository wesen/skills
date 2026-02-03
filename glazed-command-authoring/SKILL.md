---
name: glazed-command-authoring
description: "Create and wire Glazed commands (schema/fields, layers, middlewares, Cobra integration, output defaults, help/logging) for Go CLIs. Use when designing or implementing Glazed commands or upgrading existing command definitions."
---

# Glazed Command Authoring

Use this skill when creating or refactoring Glazed commands. It captures the current conventions, pitfalls, and wiring patterns we used successfully. Keep it lean, but always follow the workflow so commands are consistent and CLI behavior is predictable.

## Quick Start (Minimal Workflow)

1) **Define a command struct** embedding `*cmds.CommandDescription`.  
2) **Define a settings struct** with `glazed.parameter` tags.  
3) **Create a constructor** that builds the description using `cmds.NewCommandDescription`, `cmds.WithFlags`, and `cmds.WithLayersList`.  
4) **Implement `RunIntoGlazeProcessor`** and decode values into your settings struct.  
5) **Build a Cobra command** using `cli.BuildCobraCommand` (or a custom wrapper) and register it in your root/group command.

## Canonical Code Skeleton

```go
// 1) Command + settings structs

type FooCommand struct {
    *cmds.CommandDescription
}

type FooSettings struct {
    Limit int  `glazed.parameter:"limit"`
    Debug bool `glazed.parameter:"debug"`
}

// 2) Constructor
func NewFooCommand() (*FooCommand, error) {
    glazedLayer, err := schema.NewGlazedSchema()
    if err != nil {
        return nil, err
    }

    commandSettingsLayer, err := cli.NewCommandSettingsLayer()
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
        cmds.WithLayersList(glazedLayer, commandSettingsLayer),
    )

    return &FooCommand{CommandDescription: cmdDesc}, nil
}

// 3) RunIntoGlazeProcessor
func (c *FooCommand) RunIntoGlazeProcessor(
    ctx context.Context,
    vals *values.Values,
    gp middlewares.Processor,
) error {
    settings := FooSettings{}
    if err := values.DecodeSectionInto(vals, schema.DefaultSlug, &settings); err != nil {
        return err
    }

    row := types.NewRow(
        types.MRP("limit", settings.Limit),
        types.MRP("debug", settings.Debug),
    )
    return gp.AddRow(ctx, row)
}
```

## Field/Parameter Conventions

- **Preferred constructor**: use `fields.New(...)` (not the older `parameters.NewParameterDefinition`).
- **Struct tags**: `glazed.parameter:"flag-name"` is the authoritative mapping.
- **Always decode** with `values.DecodeSectionInto(vals, schema.DefaultSlug, &settings)` instead of reading Cobra flags directly.

## Layer Composition

- **Glazed output layer**: `schema.NewGlazedSchema()` (adds `--output`, `--fields`, etc).  
- **Command settings layer**: `cli.NewCommandSettingsLayer()` (adds `--print-parsed-parameters`, `--print-schema`, `--print-yaml`).  
- Add **custom layers** (e.g. Zigbee layer) via `cmds.WithLayersList(...)`.

### Per-command output defaults

If a command should default to a specific output (ex: `yaml` + streaming), supply output defaults when creating the glazed layer:

```go
glazedLayer, err := schema.NewGlazedSchema(
    settings.WithOutputParameterLayerOptions(
        layers.WithDefaults(map[string]interface{}{
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
cobraCmd, err := cli.BuildCobraCommand(cmd,
    cli.WithParserConfig(cli.CobraParserConfig{
        ShortHelpLayers: []string{schema.DefaultSlug},
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

- Add logging layer to root command:

```go
_ = logging.AddLoggingLayerToRootCommand(rootCmd, "appname")
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

## Streaming Commands

- Use a `--watch` or `--stream` flag.
- If events are long-running, add a duration or timeout and exit cleanly.
- Filter to relevant events before emitting rows.

## Common Pitfalls

- **Pointer to interface**: `schema.Section` is an interface; don’t use `*schema.Section`.
- **Output defaults**: use `settings.WithOutputParameterLayerOptions` on `schema.NewGlazedSchema`.
- **Help frontmatter**: quote strings with colons.
- **Duplicate flags**: don’t add the same layer to both parent and child commands.

## Reference: Read these when needed

- Glazed tutorial: `/home/manuel/code/wesen/corporate-headquarters/glazed/pkg/doc/tutorials/05-build-first-command.md`
- Glazed repo code (patterns, middlewares, layers): `/home/manuel/code/wesen/corporate-headquarters/glazed`

