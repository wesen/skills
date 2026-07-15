# Repository Work Attribution

Use this reference when the question is: **which coding-agent session implemented, committed, reviewed, or investigated this repository work?**

The result must be based on repository-changing evidence and external verification. Cwd, titles, filenames, and mention counts are candidate signals only.

## 1. Define the target work from the repository

Inspect the repository before searching transcripts:

```bash
git -C "$REPO" status --short
git -C "$REPO" log \
  --since="$SINCE" \
  --date=iso-strict \
  --pretty='%H%x09%aI%x09%an%x09%s' \
  --name-status
```

Build a signature sheet containing:

- full and short commit hashes;
- exact commit subjects;
- author and committer timestamps;
- distinctive changed file paths;
- package and symbol names;
- ticket IDs and branch names;
- currently untracked or modified files;
- unusual test commands or failure strings.

Prefer signatures that are unlikely to occur in review prose. An exact path such as `pkg/raglab/laboratory.go` is more useful than `RAG`. A full commit hash is more useful than a broad commit subject.

## 2. Discover metadata candidates

Run structured discovery for both stores:

```bash
go-minitrace discover pi \
  --source-dir ~/.pi/agent/sessions \
  --since "$SINCE" \
  --cwd-contains "$CWD_FRAGMENT" \
  --output json > pi-candidates.json

go-minitrace discover codex \
  --source-dir ~/.codex \
  --since "$SINCE" \
  --cwd-contains "$CWD_FRAGMENT" \
  --output json > codex-candidates.json
```

Metadata discovery answers “which sessions started here?” It does not answer “which session later modified this repository?” Long-lived sessions and parent/subagent sessions require content fallback.

## 3. Shortlist by exact content when metadata is insufficient

Search raw stores for two or more independent signatures:

```bash
rg -l -F 'pkg/raglab/laboratory.go' \
  ~/.pi/agent/sessions ~/.codex/sessions \
  > path-candidates.txt

rg -l -F '9056ecd' \
  ~/.pi/agent/sessions ~/.codex/sessions \
  > hash-candidates.txt
```

Combine and deduplicate paths:

```bash
cat path-candidates.txt hash-candidates.txt | sort -u > content-candidates.txt
```

Raw content may include quoted transcripts, generated reports, or the current investigation. The source list is not an attribution result.

## 4. Inspect Codex parent/subagent relationships

A Codex native source begins with `session_meta`. Relevant fields are:

```text
payload.id
payload.cwd
payload.timestamp
payload.source.subagent.thread_spawn.parent_thread_id
payload.source.subagent.thread_spawn.agent_path
```

Run:

```bash
scripts/audit_codex_sources.sh codex-sessions.txt
```

The current converter may assign the parent thread ID to a converted child source. Parent and child files can therefore target one normalized archive filename. Native IDs remain distinct; the collision is introduced by parent-identity normalization during conversion.

When collision risk exists, do not label child files “resumes” without evidence. Preserve their native role and agent path. Convert separately or choose the source required by the question.

## 5. Convert and profile narrowly

Convert Pi and Codex source lists independently. If Codex collision risk exists, use one output directory per native source.

Profile every result:

```sql
SELECT
  session_id,
  agent_framework,
  model,
  working_directory,
  started_at,
  ended_at,
  turn_count,
  tool_call_count,
  source_path
FROM sessions
ORDER BY started_at;
```

Record both:

- native source path and native ID;
- normalized session ID and archive path.

Do not discard the distinction.

## 6. Extract candidate implementation operations

See `queries.md` for reusable SQL. The initial extraction should include:

- patch and write arguments containing exact target paths;
- shell/exec calls containing the repository workdir;
- `git add`, `git commit`, `git rev-parse`, and `git status` commands;
- test and formatter commands;
- nearby user instructions;
- tool results and failures.

For Codex wrappers, command text may be in `arguments_json` rather than `command`. Patch targets may also exist only in `arguments_json`.

## 7. Verify commits precisely

A reliable commit attribution has this sequence:

1. Transcript shows an exec call whose actual command contains `git commit`.
2. The call's workdir is the target repository.
3. The nested command result indicates success when available.
4. A resulting hash is captured through command output or nearby `git rev-parse` / `git log`.
5. `git -C "$REPO" show --no-patch --format=fuller "$HASH"` verifies the object.
6. Commit subject and time agree with transcript evidence.
7. Changed paths agree with the target work.

Keep these counts separate:

| Count | Meaning |
| --- | --- |
| Text matches | Tool rows whose serialized arguments contain `git commit`. |
| Command attempts | Exec/shell calls whose actual command invokes `git commit`. |
| Confirmed successful attempts | Attempts with verified nested zero exit status. |
| Verified commit hashes | Git objects present in the target repository and tied to the run. |

Do not report the first count as the fourth.

Useful verification commands:

```bash
git -C "$REPO" show --no-patch \
  --date=iso-strict \
  --format='%H%n%aI%n%cI%n%s' \
  "$HASH"

git -C "$REPO" show --stat --oneline "$HASH"
```

## 8. Explain untracked and modified files

Git history does not contain uncommitted work. For each relevant untracked/modified file:

1. locate the first transcript patch or write;
2. inspect subsequent edits and tests;
3. compare current content or a stable content signature;
4. identify why the session ended before commit;
5. distinguish the creator from later readers/investigators.

A transcript patch that creates the exact current file is strong evidence even without a commit, provided alternatives are checked.

## 9. Classify candidate roles

### Implementer

Expected evidence:

- patches or writes target the repository;
- tests/formatters execute against changed packages;
- verified commits or exact untracked-file creation;
- user turns request the implementation.

### Reviewer

Expected evidence:

- reads, diffs, review prompts, or quoted implementation history;
- little or no repository-changing activity;
- comments or reports rather than commits.

### Investigator

Expected evidence:

- searches native session stores;
- runs go-minitrace or Git archaeology;
- reads target files after implementation;
- produces attribution or analysis artifacts.

### Reference-only

Expected evidence:

- topic appears in system context, prior summaries, generated reports, or unrelated commands;
- no relevant repository operations.

One session may have different roles in different time ranges. Long-lived sessions should be segmented by relevant turns and workdir.

## 10. Detect quoted-transcript false positives

Review sessions often receive the full history they are assessing. Signals include:

- first user turn says the following history is being reviewed;
- high topic or session-ID counts with very few tool calls;
- tool calls are read-only or absent;
- quoted commands and patches appear in turn content rather than emitted tool calls;
- model/title indicates auto-review.

Keyword frequency is especially unreliable in this case. Compare emitted tool activity, not just serialized session text.

## 11. Rule out the current investigation

The current investigator can become a top content match because its prompt and report contain every target signature. Record its session ID and start time. A session created after the repository work, whose operations inspect rather than modify the repository, must be classified as investigation evidence.

## 12. Confidence rubric

### Very high

- exact repository writes or patches;
- verified hashes and timestamps;
- external Git/path state agrees;
- plausible alternatives explicitly rejected.

### High

- exact writes/tests and workdir correlation;
- commit hash unavailable or work is uncommitted;
- alternatives checked.

### Moderate

- strong prompt, cwd, and command evidence;
- repository-changing result cannot be independently verified.

### Low

- attribution depends mainly on cwd, mention counts, filenames, or quoted content.

## 13. Report template

```markdown
# Session attribution report

## Conclusion
- Framework:
- Native session ID:
- Native source path:
- Normalized session ID/archive:
- Recorded cwd:
- Relevant time/turn range:
- Role:
- Confidence:

## Repository target
- Commits:
- Paths:
- Untracked changes:
- Distinctive signatures:

## Decisive evidence
- User turns:
- Tool calls:
- Verified hashes:
- File creation/modification evidence:

## Alternatives rejected
- Session:
- Observed role:
- Why it is not the implementer:

## Data-quality caveats
- Parent/subagent normalization:
- Adapter fields:
- Manifest/archive counts:
- Missing or unverified evidence:

## Reproducibility artifacts
- Source lists:
- SQL:
- Query results:
- Native sources:
```
