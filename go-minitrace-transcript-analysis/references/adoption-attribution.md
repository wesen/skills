# Adoption Attribution

Use this reference when the question is: **which sessions adopted a mechanism into their own codebase, as distinct from the sessions that built the mechanism itself?**

This is a structurally different question from implementation attribution (see `attribution.md`). Implementation attribution asks "who wrote this in repo X." Adoption attribution asks "who wired this into a *different* repo Y." The two populations overlap in symbols but not in target files, and they require different search directions.

## Why the implementation workflow does not work for adoption

The implementation workflow (git history → content grep → convert → query writes) starts from the mechanism's own repository. That workflow fails for adoption because the mechanism's symbols appear in review, investigation, and report sessions — not only in adoption sessions. A raw grep for `profilebootstrap` returned 109 files in a real investigation; the implementer sessions were 6 of them. Symbol frequency cannot separate an adopter from a reviewer who quotes the same symbols.

The adoption question inverts the search direction. Instead of starting from transcripts and looking for symbols, start from the filesystem and look for consumer files that import the mechanism, then match those file paths back against transcript writes.

## The inverted search

### 1. Establish the consumer set from the filesystem

Find every file in the codebase tree that imports the mechanism's packages, excluding the mechanism repositories themselves:

```bash
rg -l 'go-go-golems/pinocchio/pkg/cmds/profilebootstrap' \
  ~/code ~/workspaces \
  | rg -v '/(pinocchio|geppetto)/' > consumer-files.txt

rg -l 'go-go-golems/geppetto/pkg/cli/bootstrap' \
  ~/code ~/workspaces \
  | rg -v '/geppetto/' >> consumer-files.txt
```

This produces a closed set of known consumer files. Each is a real file on disk that imports the mechanism. The set is the attribution target — it is finite, verifiable, and independent of transcript content.

### 2. Convert the consumer-workspace sessions

Identify the workspace directories implied by the consumer files and convert their sessions. A consumer file at `~/code/wesen/2026-05-21--readwise-viewer/pkg/profilebootstrap/bootstrap.go` implies sessions under `~/.pi/agent/sessions/*readwise-viewer*`. Build a focused source list and convert:

```bash
go-minitrace convert pi \
  --source-list ./consumer-sessions.txt \
  --output-dir ./archives/pi
```

### 3. Query writes to the known consumer files

Match the consumer file paths from step 1 against transcript write operations. This is the decisive query — it is precise because the target set came from the filesystem, not from symbol matching:

```sql
SELECT c.session_id, s.working_directory AS cwd, c.turn_index,
       c.operation_type, c.file_path
FROM tool_calls c
JOIN sessions s USING (session_id)
WHERE c.operation_type IN ('NEW','MODIFY')
  AND ( lower(c.file_path) LIKE '%consumer-repo/backend/main.go%'
     OR lower(c.file_path) LIKE '%consumer-repo/pkg/profilebootstrap/bootstrap.go%'
     OR lower(c.file_path) LIKE '%other-consumer/internal/llm/bootstrap.go%' )
ORDER BY c.file_path, c.session_id, c.turn_index;
```

Each returned row is a session that wrote a consumer adoption file. Group by `session_id` to get one attribution per adopter session.

### 4. Verify adoption commits against the consumer repositories

Adoption commits are verified the same way as implementation commits — extract candidate hashes from transcript git-command results and check them with `git show` against the consumer repo:

```bash
git -C ~/code/consumer-repo show --no-patch --date=iso-strict \
  --format='%H%n%aI%n%s' "$HASH"
```

Keep the same four counts separate (text matches / command attempts / confirmed attempts / verified hashes). Only the fourth is an attribution.

## The broad-vs-precise pairing

Run both a broad query (match import strings in `arguments_json`, excluding the mechanism repos) and a precise query (match the known consumer file paths). The broad query establishes that adoption activity exists across many sessions; the precise query attributes it. Keeping both makes the narrowing legible to an auditor:

- **Broad query** — over-matches. It returns pinocchio-internal files whose paths did not hit the exclusion patterns, plus sessions that only read the code. Use it to confirm the population exists, not to attribute.
- **Precise query** — built from filesystem ground truth. It returns only sessions that wrote a known consumer file. Use it to attribute.

A single broad query produces a noisy list with false positives. A single precise query without the broad one first hides how much over-matching the broad approach generates.

## Handling unresolved adopters

Some consumer files exist on disk and are git-verified, but no converted session wrote them. This happens when the session that wrote the file was not converted, predates the converted set, or was manual. Do not force a match.

Document the adopter as filesystem-confirmed and session-unresolved. State the limit explicitly: the gap is in the converted corpus, not in the method. To close it, convert sessions active before the file's commit date using `--active-since`:

```bash
go-minitrace discover pi --source-dir ~/.pi/agent/sessions \
  --active-since 2026-04-21 --cwd-contains consumer-workspace
```

## Two adoption shapes

Adoptions fall into two shapes, worth distinguishing in a report:

1. **Thin-wrapper adoption.** The consumer defines its own `AppBootstrapConfig` (app name, env prefix, config-file mapper) and calls the mechanism's resolution functions directly. This is the recommended pattern for a new host.

2. **Richer-abstraction adoption.** The consumer builds a typed facade (a `BootstrapResult` struct with `Parse`/`Resolved`/`Close`/`BuildEngine` accessors) on top of the mechanism's resolution functions. Useful when the host wants a typed surface over resolved settings.

Both are legitimate adoptions. The shape affects how the playbook documents them, not whether they count.

## When to use this vs. `attribution.md`

| Question | Reference |
|---|---|
| Which session implemented this in repo X? | `attribution.md` (git → grep → convert → query writes in X) |
| Which session adopted this into repo Y (Y ≠ the mechanism repo)? | this reference (filesystem → convert Y's sessions → query writes to known consumer files) |
| Which session reviewed or investigated this? | `attribution.md` role classification (reviewer / investigator) |

The rule of thumb: if the target file lives in the mechanism's own repository, use `attribution.md`. If the target file lives in a different repository and merely imports the mechanism, use this reference.

## Reproducibility artifacts

Save, for every adoption investigation:

- the filesystem grep command and its output (`consumer-files.txt`);
- the consumer-workspace source list and the converted archives;
- the broad and precise SQL queries and their JSON results;
- the verified adoption commit hashes per consumer repository.

An auditor should be able to reproduce the consumer set from the filesystem grep without opening a transcript, then confirm each attribution from the precise query plus `git show`.
