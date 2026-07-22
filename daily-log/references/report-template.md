# Daily Report Template

This is the format for a daily work report produced by the `daily-log` skill. Copy this structure and fill in the verified evidence. The report goes in the Obsidian vault at:

```
/home/manuel/code/wesen/go-go-golems/go-go-parc/Logs/<TODAY_YYYY>/<TODAY_MM>/<TODAY_DD>/Daily Report - <TARGET_DAY>.md
```

Where `<TODAY_...>` is the generation date and `<TARGET_DAY>` is the day being reported on.

## Frontmatter

```yaml
---
date: <TODAY_YYYY-MM-DD>
report_for: <TARGET_DAY>
type: daily-report
generated_by: go-minitrace transcript analysis
tags: [daily-report, log]
---
```

## Required sections

### 1. Title and provenance note

```markdown
# Daily Report — <TARGET_DAY>

> Generated <TODAY> from go-minitrace transcript analysis of all Pi and Codex sessions active on <TARGET_DAY>. Evidence: converted minitrace archives, docmgr ticket changelogs, and repository git history.
```

The provenance note tells the reader exactly what evidence backs the report. Keep it.

### 2. Summary

One paragraph stating: number of sessions, number of frameworks, total turns/tools, total commits, and the work streams. Lead with the verified commit total.

```markdown
## Summary

A <heavy|moderate|light> implementation day across **<N> major projects**, driven by **<N> coding-agent sessions** (<N> Pi, <N> Codex) totaling ~<N> turns and ~<N> tool calls. **<N> commits** landed across <N> repositories. The day's work fell into <N> streams: (1) ..., (2) ..., (3) ...
```

### 3. Sessions table

Every session active on the target day. Columns: session ID (short), framework, model, title, turns, tools, time window (UTC).

```markdown
## Sessions Active on <TARGET_DAY>

| Session | Framework | Model | Title | Turns | Tools | Window (UTC) |
|---|---|---|---|---|---|---|
| `019f7666` | Pi | gpt-5.6-sol | ... | 1,608 | 1,554 | 07-18 18:04 → 07-20 19:38 |
```

### 4. Commit volume table

Git-verified commit counts per repository. This is the strongest evidence in the report.

```markdown
## Commit Volume (git-verified)

| Repository | Commits on <TARGET_DAY> |
|---|---|
| `go-go-golems/upwork` | 43 |
| **Total** | **257** |
```

### 5. One section per work stream

For each major work stream, a section with:

- The ticket ID and session that drove it
- The repository and commit count
- A `### What happened` subsection with the verified work, grouped logically
- Commit hashes where they add precision

Use the docmgr changelog entries (verified against git) as the backbone. Group related commits. Do not list every commit verbatim unless the day was small.

```markdown
## 1. <Work stream title>

**Ticket:** `<TICKET-ID>` (<repo>)
**Session:** <Framework> `<session-id>` (<model>)
**Repo:** `<repo path>` — <N> commits

### What happened

<One or two paragraphs summarizing the work stream.>

**<Subgroup label>:**
- <Bullet per logical group of commits, with commit hash if useful>
- <Bullet>
```

### 6. Analysis notes and caveats

This section is not optional. Record every limitation that affected the investigation so a reader can calibrate their confidence.

```markdown
## Analysis Notes & Caveats

- **Method:** Sessions discovered via `go-minitrace discover --active-since <TARGET_DAY>`, converted to minitrace archives, then queried with `history file-history`, `history ticket-timeline`, and `session-list` presets. Commit counts verified directly against repository git history.
- **Spanning sessions:** <List any sessions that started before or ended after the target day. Note that their file-history timestamps may fall on adjacent days.>
- **Codex adapter caveat:** <If a Codex session was involved, note that operation_type is OTHER for exec/patch and file paths may be in arguments_json. State that commits were verified via git.>
- **Attribution:** All commit counts are git-verified against the live repositories, not transcript text matches.
- **Investigation artifacts:** <Path to the investigation directory with archives, source lists, and SQL.>
```

## Writing rules

- Lead with verified numbers. Commit counts are the anchor.
- Use the docmgr changelog as the backbone for narrative, but verify every step number against git.
- Group commits logically. Do not dump the full git log.
- Include commit hashes when they add precision (e.g., "Step 8 (commit 0d5e4fb)").
- Classify sessions by role where possible: implementer, reviewer, investigator, reference-only.
- Keep the caveats section honest. If a session spanned the day, say so.
- The report is the only file written to the vault. Stage only that file when committing.
