---
name: diary
description: Write and maintain chronological implementation diaries with evidence, failures, decisions, commits and review instructions. Use when asked to keep a diary, dev log, ticket work history or debugging record; detailed diary requests use the full investigation format.
---

# Diary

## Select the entry mode

- **Investigation:** substantive implementation, debugging, design decisions, or an explicit detailed diary request. Use the full [investigation format](references/investigation-entry.md).
- **Milestone:** routine successful validation, publication or bookkeeping without substantive debugging. Use the compact [milestone format](references/milestone-entry.md).
- When uncertain, preserve the meaningful failure/decision context rather than compressing it away. Higher-priority instructions and an explicit user format override these defaults.

Each numbered step begins with 1–2 short prose paragraphs explaining intent and outcome. Record failures promptly, including the exact command and relevant diagnostic. Keep historical entries intact; change future entry conventions prospectively.

## Prompt and evidence discipline

Record the actual authored user request verbatim the first time it appears; later steps link to that entry. Do not fabricate a verbatim quote from a summary. Distinguish user-authored instructions from automatically injected runtime metadata; avoid repeating counters or budget notices. If only a summary survives, label it as a summary and link the original source when available.

Use [evidence levels](references/evidence-levels.md): routine success needs command/result/revision, experiments need configuration and measurements, and failures need exact relevant diagnostics. Preserve raw bytes when identity matters, not just to archive decorative successful CLI output.

## Working loop

Implement toward a major feature or integration milestone, then validate its affected behavior at that boundary. Commit boundaries and validation boundaries are not the same: smaller focused commits are useful checkpoints and do not warrant extensive checks, full builds or broad test suites merely because a commit is being made. Prioritize visible feature progress over repeated validation and bookkeeping loops.

At a major boundary, run the relevant validation gate. If it fails, collect the diagnostics, fix the issues together where practical, and rerun the narrow checks needed to verify those fixes rather than restarting the entire validation pipeline after each edit. Run an earlier targeted check only when it resolves a concrete uncertainty or material risk; honor explicit project-required checks. Record which checks passed, failed or were deferred, and never describe an unvalidated checkpoint as qualified.

Update the detailed diary, tasks and changelog at meaningful milestones, preserving failure evidence as it occurs without requiring a full bookkeeping cycle for every small edit. Code and documentation may share a focused commit when that is clearer; two separate commits per small edit are not mandatory. Record the code hash in the subsequent checkpoint when available.

Use `docmgr` for ticket creation, task updates and relations. If a verified local binary provides `milestone record`, it can consolidate task/history updates; it does not author the diary or judge evidence. Follow the docmgr skill's actual API and capability check, not a proposed command from a design sketch.

Keep RelatedFiles focused on primary implementation and evidence files, with absolute `--file-note "path:reason"` arguments. A commit or bounded receipt supplies the full changed-path inventory; do not duplicate every path in metadata. Never hide review-critical files merely to hit an arbitrary count.

## Resume and review

Resume from the latest relevant checkpoint, current request and current files, then expand the necessary earlier investigation. Do not reread an entire long diary automatically. Unchanged instruction hashes are change signals, not proof the model still remembers the text; reload absent instructions and obey higher-priority full-read rules.

The [workflow reference](references/diary.md) points to the canonical formats and evidence rules. No runtime phase loader or automatic policy enforcement is implied by this prose.
