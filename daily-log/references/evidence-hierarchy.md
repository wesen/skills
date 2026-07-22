# Evidence Hierarchy

The daily report rests on a distinction between strong and weak evidence. The report uses this hierarchy to decide what to claim and what to hedge. No claim in the report rests on weak evidence alone.

## Strong evidence

Strong evidence proves that work landed in the repository or was recorded as complete by the system of record.

- **Git-verified commit hash.** A commit object in the repository, confirmed by `git log --since <day> --until <day>`. This is the strongest single evidence. The commit count is the primary measure of work volume.
- **Docmgr changelog entry with a matching commit hash.** The changelog is the agent's contemporaneous record of a completed step. When the commit hash in the changelog entry matches a hash in the git log, the step is verified.
- **Passing test run corroborated by CI.** A test command that exited zero, recorded in the transcript, and confirmed by a green CI run.

Use strong evidence to anchor claims. Commit counts and verified step numbers go in the report's summary and tables.

## Supporting evidence

Supporting evidence shows that the agent was working on the task but does not by itself prove completion. Use it to explain what the commits accomplished.

- **Tool call that modified a file.** A `MODIFY` or `NEW` operation in the `files` table, with a timestamp in the target window. Shows focus of work.
- **User instruction requesting the implementation.** The first human turn in a session, recorded as the session title. Shows intent.
- **File reads and git status around the relevant operation.** Shows the agent inspected state before acting.

## Weak evidence

Weak evidence should never be used alone to attribute work. It may appear in the report as context but never as proof.

- **Cwd match.** A session may work in a repository without changing it. A long-lived session may work in multiple repositories. Cwd groups sessions; it does not prove implementation.
- **Filename or title match.** A filename may be quoted from another session. A title is auto-extracted from the first turn and may not reflect the session's actual work.
- **Keyword frequency.** Counting how often a word appears in a transcript measures mention, not action.
- **Quoted transcript content.** An agent may quote a commit hash, a file path, or a command from a previous turn. Quotation is not performance.

## The verification procedure

For every claim the report makes about completed work:

1. Find the candidate evidence in the transcript (file-history, ticket-timeline, or tool-call query output).
2. Verify against git: does the commit exist in the repository with a timestamp in the target window?
3. Verify against the docmgr changelog: does the changelog entry's commit hash match the git log?
4. If both confirm, report it as verified. If only the transcript confirms, report it as candidate and note the gap in caveats. If neither confirms, do not report it.

## What never counts as evidence

- A `git commit` command in the transcript. The command may have failed. The commit object in the repository is the only proof.
- A commit hash mentioned in transcript text. It may be quoted from a previous turn or from another session. Verify it exists in the git log.
- A file path in a tool call. The file may have been read, not written. Check the `operation_type`.
- A session title. It is auto-extracted and may be truncated or misleading.
- A cwd match alone. Use it to group, not to attribute.

## Applying the hierarchy in the report

The report's commit-volume table is strong evidence. The file and ticket timelines are supporting evidence that explains the commits. The sessions table is context. The caveats section records where evidence was weak or incomplete.

When the evidence is ambiguous, say so. A report that hedges an uncertain claim is more useful than one that asserts a false one.
