# Design-guide writing guidance

Write for the stated audience and decision. A design guide should let a capable reader new to this system understand the problem, assess the proposed change, and begin the appropriate work without reconstructing the author's private context. Scale detail to consequence and unfamiliarity, not to a fixed word count. These principles apply to any system or design domain; skip inapplicable questions rather than inventing complexity to fill a template.

## Establish understanding before drafting

Read the requirements and existing design in full. Inspect enough implementation, schemas, tests, examples or other primary evidence to understand the actual system and its boundaries. Trace one representative use from entry to outcome, including relevant failure behavior. Follow dependencies where a claim depends on another subsystem. For a greenfield design, identify assumptions and external contracts instead of inventing existing code.

Make brief research notes: the reader's task, current concepts and relationships, evidence for important claims, uncertainties and decisions needed. Keep observed results, source-based deductions and proposals distinct. A prior document is an input to verify, not proof of its own correctness. Do not imply tests were run when only source was read.

## Teach the reader, not the vocabulary list

The primary quality test is understandability: can a capable newcomer explain what the system does, why this change is needed, and how the important parts work together? Technical accuracy supports that explanation, but exhaustive edge-case analysis and implementation-perfect sketches are not the writing objective. Spend detail where a reader would otherwise have to infer meaning. Treat minor corrections separately from gaps that prevent understanding.

At the first consequential use of a project-specific term, explain its purpose in a sentence and, where useful, show a small ordinary use. Knowing a programming language does not imply knowing this project's feature names. Do not merely expand an acronym or replace one unfamiliar noun with another. Introduce the general concept before listing implementation names. A later glossary is optional navigation, not a substitute for the first explanation.

When several abstract objects interact, give one concrete instance of their relationship: a small input/output, message, record, example call, or state before and after an action. Use just enough fields or steps to explain the relationship. Then explain what the reader should notice. Do not add an example mechanically to every subsection or force one running example onto unrelated behavior.

Maintain an explanatory thread through the middle and ending, not only the introduction. Connect a user-visible situation to the relevant current mechanism, the proposed behavior and the reason for it. Introduce an interface after its purpose is clear. Make section transitions explain why the next subject matters. Reference paths support the explanation but cannot stand in for it. A detailed textbook-style account may be appropriate; neither brevity nor length is a goal by itself.

## First writing pass: produce a complete explanation

Start with what the system does for its users, the concrete problem and the intended change. Teach enough of the existing system to explain the proposal. Historical project/process detail belongs in references unless it affects the design. Introduce local terminology before dependent claims; a later glossary cannot repair an unexplained argument.

Use a coherent order that fits the design: purpose and scope; current operation; evidence and problems; proposed behavior and decisions; interfaces and key flows; implementation/migration; validation; risks and unresolved decisions. This is a navigation aid, not a mandatory set of twelve headings. Put related reasoning together rather than scattering it across checklists.

For significant concepts:

- Define the actual entities and how they relate. Explain scope, identity, lifetime, cardinality or ownership when these determine behavior. Similar names do not establish equivalence; say what changes and what remains the same.
- Follow a small representative situation through actions and consequences. Explain what fails or becomes costly, who changes it, and why the proposed behavior resolves that problem. Label hypothetical failures as such.
- Identify responsibilities at relevant boundaries: caller, component, process, external service or operator. Do not hide actions behind noun phrases such as “handling” or “coordination.”
- Show the technical contract after teaching its meaning. Use a small concrete record/message/state example when fields and relationships carry the argument. Interfaces alone may not show how objects fit together.
- Explain important success and failure transitions. For a handoff, say when responsibility changes and who retains it if the handoff fails. For concurrent behavior, name the arbiter and the competing events. Cancellation, delivery and completion must not be equated unless the design establishes that equivalence. Apply these questions only where relevant.

Use this as an explanatory progression, not repeated subsection scaffolding. One paragraph may suffice. Reuse an example across sections where it helps establish continuity; do not stretch it to unrelated mechanisms. Explain technical systems directly, without analogies.

Keep clear boundaries between current behavior, proposed changes and open decisions. Preserve existing safeguards in the explanation. A rejected operation is different from silently accepted invalid state. Label an unresolved policy, explain its consequences and whether it blocks implementation; do not quietly resolve it by inventing facts or conceal it behind an illustrative method name.

Prefer linked prose, concrete verbs and precise actors. Use tables for comparisons, numbered steps for sequences and diagrams for relationships or timing. Go, JavaScript, TypeScript or language-neutral pseudocode are appropriate; choose the form that communicates the contract. Label sketches and omissions. A comment saying “atomic,” “secure” or “asynchronous” does not establish the property. Runnable examples must use the actual API and state prerequisites.

Include compact decision records for consequential choices: context, realistic alternatives, decision, rationale, consequences and status. Avoid duplicating the same rationale in a record, the surrounding prose and repeated summaries. Place concise review rules after their explanation. Keep terminology stable throughout the document.

Connect the implementation plan to real entry points, affected consumers, removal/migration work and meaningful validation. Preserve required edge cases without enumerating every imaginable failure. Do not add compatibility layers or frameworks merely to make a generic pattern appear comprehensive. State performance/security/operational claims at the strength supported by evidence. Include one useful starting command or concrete navigation path when the reader needs to work in a repository; do not bury them in an inventory of commands.

## Second writing pass: diagnose first, then revise

Finish and save the first draft before reviewing it. Reread the entire draft as if this were the reader's only explanation. Do not merely polish sentences. In a separate review note, record concrete passages, missing information, likely misunderstanding and the intended correction BEFORE applying revisions.

Ask throughout, including the middle and ending:

1. Can the reader explain the purpose and an ordinary use of the system? Which prerequisites are reasonable general knowledge, and which are unexplained local facts?
2. Does each important entity have enough scope and relationships to make the claims meaningful? Is information required here available earlier, or must the reader guess or jump ahead?
3. Can the reader follow a representative success and relevant failure sequence without adding unstated actions? Who acts, what state changes, and what remains unresolved?
4. Do examples, prose, diagrams and signatures agree? Does each mechanism cover all the objects and cases the text promises? Are implicit preconditions visible?
5. Are current/proposed/tested states distinguishable? Check material factual claims against primary evidence. Do not confuse fidelity to an old document with accuracy.
6. Could the intended reader begin the next step? Separate blocking design decisions from ordinary details an implementer can reasonably choose or discover.
7. Can repetition, chronology, generic disclaimers or unused abstractions be removed without losing a necessary explanation?

In the review notes, distinguish comprehension gaps from technical corrections. Start with places where the reader would ask “what is this for?”, “which thing does this refer to?”, “how did we get here?” or “what happens next?”. Locate the actual passage and repair the explanation there; do not respond to every uncertainty by adding an open-question table.

Mentally execute the important examples against the stated rules. Check that their inputs, outputs, identities, timing and success/error responsibilities make sense. This is a lightweight coherence check, not a demand to implement every sketch or enumerate every exceptional case. Verify the source claims carrying the main argument; qualify uncertainty where the evidence does not establish it.

Revise to address the specific notes. Correct errors, add missing relationships, move definitions to the point of need and remove repetition. More length is not the objective. Preserve the first draft and review notes when requested for an experiment; otherwise choose a lightweight working format. Keep author self-assessment and experiment history out of the reader's design guide unless requested.

After revision, reread the affected explanations in the context of the WHOLE document. Compare opening promises, examples, diagrams, API sketches, decisions and implementation/test steps: they must tell one consistent story. If a proposal deliberately changes an established requirement, identify that change and its reason; do not present it later as an already accepted rule. Remove superseded statements rather than leaving both versions for the reader to reconcile. Check that additions have not buried the main explanation. This final consistency read is part of the second pass, not a required third draft.

A separate reviewer with only the draft is a stronger approximation of fresh eyes, when available and authorized. Have that reviewer record comprehension questions before source inspection; use targeted source reading afterward to distinguish prose gaps from technical mistakes. An author's own second pass is useful but is not independent review or a demonstrated human comprehension test.

## Evidence and handoff

Reference concrete files/symbols or primary artifacts beside claims they support. Specify the inspected revision when state could drift. Do not claim branch/PR status from stale notes. Source references substantiate explanation; they cannot replace it. Report unresolved choices and evidence limits plainly. Syntax checks, headings, word counts and self-ratings do not establish comprehension or correctness.

Diary material follows the diary skill: chronological evidence, commands, failures, decisions and verification. A design guide instead describes the coherent system and proposed work for someone outside the conversation.
