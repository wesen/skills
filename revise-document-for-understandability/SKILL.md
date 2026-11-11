---
name: revise-document-for-understandability
description: Review and revise an existing technical design document so a capable newcomer can understand the system, rationale and proposed work. Use for readability rewrites, intern-facing revisions, explanations that feel cryptic, or a substantive second pass beyond copyediting. Supports review-only requests without modifying the document.
---

# Revise document for understandability

Make an existing document understandable to someone who lacks the author's project context. The primary test is whether that reader can explain what the system does, why the change is needed, how the important parts work together, and where to begin. Technical accuracy supports that explanation; exhaustive auditing and implementation-perfect pseudocode are not the objective.

Read and apply [the writing guidance](references/writing-style.md). It contains the same generic guidance used for authoring design guides, including concrete examples, technical prose without analogies, and whole-document revision. This skill supplies the entry point for an existing document: the supplied document is your initial draft, and its wording is not a requirement to preserve.

## Establish scope

Use the audience, output location and editing mode in the request. Otherwise assume a technically capable developer new to this project, and revise the supplied document in place when its format and workspace allow ordinary reversible editing. Respect repository and document-specific conventions. If asked for a review only, deliver findings and suggested repairs without editing. If asked for a new version, preserve the original and write to the requested destination.

This skill authorizes document work within the user's request. It does not authorize implementation changes, new architecture, publication, uploads, commits or external reviewers by itself. It works in Claude Code and other coding agents; it does not require a particular model or automatically launch another agent.

## 1. Read as the newcomer before filling gaps from code

Read the entire supplied document, including examples, diagrams, implementation steps and appendices that carry the argument. Before inspecting source, make brief notes about what the document itself lets you understand. Do not let your prior project knowledge silently complete its explanations.

Record concrete passages where you:

- Had to infer a term's purpose, an object's identity or a relationship between components.
- Had to jump ahead, reread an earlier section or supply a missing transition.
- Could follow a signature but could not explain what a normal call accomplishes.
- Could not distinguish current behavior, proposed behavior and an unresolved choice.
- Lost the explanatory thread in inventories, repeated summaries or dense requirement paragraphs.

Say what you understood as well as what is missing. Distinguish a reader's inference from an explicit statement in the document. If you already know the system, describe this as a simulated newcomer reading, not independent evidence from a new reader.

## 2. Understand the system before rewriting

Read enough actual code, tests, schemas, examples and other primary evidence to understand the relevant behavior independently. Trace one representative use from entry to observable result; investigate relevant failure behavior and dependencies where the explanation depends on them. For a greenfield proposal, examine requirements and external contracts instead of inventing an implementation.

Keep concise research notes with file/symbol references and the inspected revision where available. For each important reading gap, identify whether source resolved it, the design left a decision open, or evidence remains unavailable. Reading code to learn how to implement a detail is reasonable; needing code just to understand the document's central argument is usually a repair target.

Do not expand this into a general code audit. Verify the claims carrying the explanation and investigate contradictions that change its meaning. If source is unavailable, improve what can be explained from the supplied evidence and mark unresolved claims. Source inspection is not a test run.

## 3. Diagnose before revising

Before editing, write a compact review note connecting each important problem to a concrete repair. Use whatever structure is readable; for example:

| Passage | What the reader must infer | What evidence clarified | Revision |
|---|---|---|---|
| “The coordinator publishes the result” | What is published, who can read it, and when it becomes visible | Implementation separates writing data from making it visible | Introduce the output and show one before/after state before describing the coordinator |

Separate comprehension gaps from factual corrections and unresolved design decisions. Prioritize missing purpose, relationships and sequences over minor naming or precision issues. Include repetition and section ordering when they make understanding harder. Do not turn every uncertainty into a new open-question section.

Keep these notes separate from the reader-facing guide. A brief working note is sufficient; preserve named research/draft/review artifacts when requested, rather than imposing an experiment directory on every editing task.

## 4. Revise the explanation, not just the sentences

Use the writing reference to produce a coherent, complete document. Keep passages that already teach well; reorganize or replace passages that depend on unstated context. A substantial rewrite is appropriate when local edits cannot repair the sequence of ideas.

- Explain what a local term is for at its first consequential use. Expanding an acronym or giving another unfamiliar name is insufficient.
- Connect a user-visible situation to the current mechanism, the problem, the proposed behavior and its reason.
- Show a small concrete call, record, result or state transition where relationships would otherwise remain abstract. Explain what to notice. Go, JavaScript, TypeScript and language-neutral sketches are all appropriate.
- Introduce interfaces after their purpose. State actors and actions instead of hiding behavior behind phrases such as “result packaging” or “lifecycle handling.”
- Explain ownership, identity, timing and failure responsibilities where they determine behavior; skip these questions when irrelevant.
- Maintain the explanation through the middle and ending. Implementation and validation sections should follow from the design instead of restarting it as a list of names.
- Remove redundant rationale, unnecessary chronology and unused abstractions. Length is neither the goal nor the defect: retain the detail needed for understanding.

Preserve the intended design and material requirements. Correct demonstrably false descriptions with evidence, but do not silently substitute architectural preferences or settle open policy decisions. Label sketches, assumptions and omissions. Surface contradictions that require an author decision and explain their consequences. Keep substantive corrections visible in the handoff.

## 5. Reread the complete revised document

This is the decisive second pass, not a proofreading pass or a demand for a third full draft. Read the revised document end to end as the reader's only explanation. Revisit the review notes and ask whether the actual passages now answer the questions.

Mentally execute important examples. Check that prose, diagrams, API sketches, decisions and implementation/test steps describe the same objects and behavior. When an explanation changes, remove or update superseded claims elsewhere. Check that additions have not buried the main argument or replaced one unexplained term with another.

The reader should be able to describe an ordinary use, explain the reason for the change, follow the relevant success and failure sequence, and begin the appropriate next step without reconstructing private context. Fix remaining comprehension problems in the document, rather than merely adding them to a checklist. Leave genuine unresolved decisions explicit. Apply this standard proportionally; it is not an invitation to pursue every edge case indefinitely.

## Deliver

Return the revised document or its path, a short account of the most consequential readability improvements, and any material correction or unresolved decision. For review-only work, return the passage-specific findings and repairs instead. Mention evidence limits plainly. Do not present word counts, headings, syntax checks or your own confidence as proof that a newcomer understood the document.

Keep author self-review and editing history outside the guide. Follow an explicitly requested diary or document-management workflow, but do not create tickets, upload, or run multi-agent experiments just because this skill was invoked.
