---
name: glazed-help-page-authoring
description: Author and maintain Glazed help entries for Cobra-based CLIs. Use when creating or updating help markdown files with Glazed frontmatter, choosing `SectionType` (GeneralTopic, Example, Application, Tutorial), wiring embedded docs into Go (`go:embed`, `LoadSectionsFromFS`, `help_cmd.SetupCobraRootCommand`), checking slug uniqueness/discoverability, or improving help quality based on `glaze help how-to-write-good-documentation-pages` and `glaze help writing-help-entries`.
---

# Glazed Help Page Authoring

## Quick Refresh Commands

Run these first when exact conventions matter:

```bash
glaze help how-to-write-good-documentation-pages
glaze help writing-help-entries
```

Treat those help topics as authoritative for style and field names.

## Workflow

1. Identify scope.
Decide whether you are writing a general concept, example, tutorial, or multi-command application guide.

2. Choose `SectionType`.
- `GeneralTopic`: conceptual/reference documentation.
- `Example`: narrow, concrete command/feature example.
- `Application`: end-to-end use case spanning multiple commands/features.
- `Tutorial`: step-by-step instructional flow.

3. Draft frontmatter with exact field names.
Use this structure and keep values focused:

```yaml
---
Title: "..."
Slug: "unique-slug"
Short: "One-sentence summary."
Topics:
- topic-a
Commands:
- command-a
Flags:
- flag-a
IsTopLevel: false
IsTemplate: false
ShowPerDefault: true
SectionType: GeneralTopic
---
```

4. Write content with strong section openings.
For each major section, start with:
- what this section covers,
- how it works in practice,
- why it matters to the reader.

5. Apply style constraints.
- Use present tense and active voice.
- Avoid terse prose; explain motivation and failure modes.
- Keep examples runnable.
- Explain why in comments, not obvious mechanics.
- Do not add a top-level `#` heading in document content; Glazed renders the title.

6. Finish with operational sections.
Add:
- troubleshooting table (`Problem | Cause | Solution`),
- `See Also` cross-references to related sections.

7. Validate discoverability and consistency.
- Ensure each `Slug` is unique.
- Ensure `Short` does not duplicate entire intro paragraphs.
- Ensure topics/commands/flags tags improve filtering.

## Go Integration Pattern

Use embedded docs and register them with Cobra:

```go
package doc

import (
    "embed"

    "github.com/go-go-golems/glazed/pkg/help"
)

//go:embed *
var docFS embed.FS

func AddDocToHelpSystem(helpSystem *help.HelpSystem) error {
    return helpSystem.LoadSectionsFromFS(docFS, ".")
}
```

```go
helpSystem := help.NewHelpSystem()
if err := doc.AddDocToHelpSystem(helpSystem); err != nil {
    return err
}
help_cmd.SetupCobraRootCommand(helpSystem, rootCmd)
```

## Definition of Done

- Frontmatter fields parse and use exact Glazed keys.
- Section type matches the intent of the page.
- Content explains what/how/why, not just what.
- Troubleshooting and `See Also` sections exist.
- Slug is unique and queryable with `glaze help <slug>`.
