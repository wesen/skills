---
name: code-quality-review-cleanup
description: "Deep code quality inspection and cleanup planning for codebases, including architecture mapping, duplication analysis, runtime implications, and refactor recommendations with concrete file/line examples and solution sketches/pseudocode. Use when asked for code inspection reports, cleanup planning, refactor opportunities, or to produce ‘food inspector’ style code audits with actionable examples and sketches."
---

# Code Quality Review + Cleanup Planning

## Goal

Produce a rigorous, actionable code inspection report and (if requested) a diary. Focus on architectural mapping, duplication, complexity hot spots, runtime implications, and cleanup/refactor opportunities. Every issue must include concrete code locations and a solution sketch/pseudocode.

## Trigger Checklist

Use this workflow when the user asks for any of:
- Code inspection / audit / review across a folder or package
- Cleanup/refactor planning
- Duplication/over-complexity analysis
- “Food inspector” style review
- Solution sketches / pseudocode for improvements

## Workflow (concise, high signal)

1) **Inventory the surface area**
   - List files with `rg --files <path>` or equivalent.
   - Identify conceptual blocks: transport/messaging, runtime engines, models, widgets, styles.

2) **Map the runtime flow**
   - Identify message paths or control flow across layers.
   - Note goroutines, background loops, periodic tasks, or unbounded buffers.

3) **Inspect by section**
   - Messaging pipeline
   - Runtime engines
   - Models/views
   - Widgets/utilities
   - Shared formatting/helpers

4) **Document issues with concrete evidence**
   For each issue, include the following **inline** structure:
   - **Problem** (1–2 sentences)
   - **Where to look** (file paths + function names; line ranges if practical)
   - **Example snippet** (3–10 lines)
   - **Why it matters** (runtime/maintenance implications)
   - **Cleanup sketch** (pseudocode or structural layout)

5) **Summarize cleanup opportunities**
   - Group into: low-risk refactors vs larger architectural changes.
   - Highlight highest leverage fixes first.

## Output Format (report)

Use a consistent section template:

```
## <Section>
### <Issue Title>
Problem: ...
Where to look: <files + functions>
Example:
<code block>
Why it matters: ...
Cleanup sketch:
<pseudocode or layout>
```

## Output Format (diary, when requested)

Follow the repo’s diary style (if a diary skill exists in the session). Include exact user prompt, commands run, findings, and upload steps.

## Pseudocode / Sketch Guidelines

- Keep sketches short and implementation-oriented.
- Prefer naming new helper packages or interfaces over large rewrites.
- If recommending a subpackage split, include a directory layout block.
- If recommending registry/dispatch, show map-based handler example.

## Minimal Example (reference)

```
### 2.2 Transform vs Forward
Problem: Duplicate switch-based dispatch.
Where to look: devctl/pkg/tui/transform.go (DomainType switch), devctl/pkg/tui/forward.go (UIType switch)
Example:
case DomainTypeStreamStarted:
    var ev StreamStarted
    if err := json.Unmarshal(env.Payload, &ev); err != nil { ... }
Cleanup sketch:
var handlers = map[string]func(json.RawMessage) error{...}
```

## Quality Bar

- Every issue has **location + example + sketch**.
- No vague claims; anchor to files.
- Call out runtime implications explicitly (memory, goroutines, throughput).
- Include counts/duplication estimates when obvious (e.g., “14 cases”).

