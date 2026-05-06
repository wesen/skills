---
name: textbook-authoring
description: Author high-quality interactive textbooks in Peter Norvig style. Use when writing or rewriting Systemlab chapters, creating educational documentation for evtstream, or any task that requires explaining technical concepts through foundational prose, concrete examples, pseudocode, diagrams, and structured learning materials. Define the skill's tone, structure, and patterns before drafting.
---

# Textbook Authoring

## Purpose

This skill guides the creation of high-quality technical textbooks in Peter Norvig style. It helps authors write educational material that:

- Builds foundational understanding before diving into implementation
- Explains **why** things are, not just **what** they are or **how** to do them
- Uses concrete examples, pseudocode, and diagrams to ground abstract concepts
- Balances prose paragraphs with bullet points for rhythm and emphasis
- Creates interactive learning experiences that connect teaching text to working code

## The Peter Norvig Style

### Core Characteristics

**Foundational first.** Start with the conceptual foundation. Help the reader understand why a design decision was made before showing them how it was implemented. A reader who understands why can extend the pattern; a reader who only knows how copies it.

**Prose paragraphs that develop ideas.** Write in complete paragraphs that develop a thought fully. Each paragraph should advance the argument or explanation. Avoid short, declarative sentences that feel like bullet points in disguise.

**Concrete over abstract.** Whenever possible, show real code, real output, real trace lines. Abstract descriptions of patterns are useful, but they land better when grounded in something the reader can see and run.

**Breaks in the rhythm.** Use code blocks, tables, diagrams, and bullet points strategically to break up long passages of prose. These aren't decorations—they are part of the argument. A table comparing two approaches does work that prose cannot.

**The reader is capable.** Do not talk down to the reader. Assume they are intelligent and can follow complex ideas if presented clearly. Do not qualify every statement with "of course" or "clearly" or "it goes without saying." Let the ideas speak.

### What Good Writing Looks Like

**Example: "1. The Command Path"** (from Systemlab Phase 1)

> When you click **Submit** on the Phase 1 page, a series of things happen in sequence. Understanding that sequence—not just what occurs, but why each step exists and how it connects to the next—is the purpose of this chapter. The goal is not to make you memorize an API, but to help you see the architecture as a coherent system of responsibilities, each playing a specific role.
>
> The entry point is the `Hub`. It sits at the center of the framework, and its job is deceptively simple: receive a command, find the right handler, give the handler what it needs, and let the rest unfold. The `Hub` does not know what commands do. It does not format output. It does not decide what state should look like. It routes. Everything else flows from that decision.

Notice:
- First sentence sets up the sequence and why it matters
- Second sentence states the goal (not memorizing, but understanding)
- Third paragraph introduces the Hub with concrete role description
- Final sentence is short and punchy: "It routes. Everything else flows from that decision."

**Example: Explaining a design decision**

> Why does the handler receive a publisher rather than returning a result? This is the most important design decision in the framework, and it pays to sit with it for a moment. If the handler returned a final value—say, a `UIState` or a `ChatMessage`—then the framework would have to know what to do with that value. It would have to route it somewhere, decide how to transform it, decide whether to store it. That knowledge would live in the handler, or in the framework, or in both in ways that would be hard to untangle. Instead, the handler describes what happened by publishing events. The framework then asks: what should happen next? The answer lives in the projections, not in the handler.

Notice:
- Question is posed directly ("Why does the handler...")
- "It pays to sit with it for a moment" acknowledges the reader needs time to absorb
- Concrete example of what would happen with the alternative approach
- Final sentence delivers the insight with no hedging

**Example: Bullet points that add value**

> The key points to internalize:
>
> - One command produces multiple events. This is intentional. Real work rarely has a single outcome; it has a beginning, intermediate states, and an end.
> - Events are published, not returned. The handler does not wait for projections to run; it simply describes what happened and returns. The framework handles the rest.
> - Events are canonical. They describe backend state, not frontend state. The distinction matters because it means the same event stream can be consumed by multiple projections, each deriving a different view.

Notice:
- Each bullet is a complete thought in a full sentence
- The first bullet explains the pattern and the rationale ("This is intentional. Real work rarely...")
- The second bullet contrasts "published" vs "returned"
- The third bullet defines a term ("canonical") and explains why the distinction matters

### What NOT to Write

**AI Slop Pattern 1: Wandering preamble**

> "In the ever-evolving landscape of modern software architecture, understanding the nuanced dynamics of event-driven systems has become increasingly paramount for engineering teams seeking to build resilient, scalable, and maintainable applications. In this comprehensive chapter, we will delve deep into the fundamental concepts that underpin..."

**Why it's bad:** The writer is buying time before getting to the point. The reader learns nothing in these sentences. Worse, it signals that the writer does not trust the material to be interesting on its own.

**Fix:** Start with the point. "Event-driven systems route work through handlers and publishers rather than returning values directly. This design choice shapes everything that follows."

---

**AI Slop Pattern 2: Hedged non-claims**

> "It is worth noting that somewhat interestingly, one might observe that this approach could potentially offer certain advantages in terms of flexibility and extensibility, which may be particularly relevant in scenarios involving complex event processing requirements."

**Why it's bad:** The writer is afraid to make a statement. "One might observe" and "could potentially" and "may be particularly relevant" add no information while consuming words.

**Fix:** Be direct. "This approach offers flexibility and extensibility. The benefits matter most in complex event processing scenarios."

---

**AI Slop Pattern 3: Vague bullet lists**

> - Important concepts
> - Key takeaways
> - Things to remember
> - Useful patterns
> - Understanding fundamentals

**Why it's bad:** The bullets say nothing. The reader cannot act on "important concepts" without knowing what they are. These bullets exist to signal structure, not deliver content.

**Fix:** Every bullet should be a complete sentence that could stand alone. "Sessions are created lazily. If the `SessionId` has never been seen before, a fresh session is instantiated."

---

**AI Slop Pattern 4: Philosophical throat-clearing**

> "This is one of those patterns that, while appearing simple on the surface, contains within its design a profound elegance that reveals itself only to those who take the time to truly understand the underlying mechanics and their implications for system design."

**Why it's bad:** The writer is filling space. The sentence conveys no information. If the pattern is elegant, show it with code and diagrams, then let the reader decide.

**Fix:** "Sessions are created lazily. This is a deliberate choice: it means there is no separate 'create session' step that callers must remember to perform."

---

**AI Slop Pattern 5: Overused qualifiers**

> "Of course, it goes without saying that clearly, the ordinal is fundamentally important to understanding..."

**Why it's bad:** "Of course," "clearly," and "it goes without saying" are filler that imply the writer is uncertain. If something is obvious, just say it without the qualifier.

**Fix:** "Ordinals define event order. If you know ordinals 1 through 5 have been published, you know the order in which things happened."

---

## Structure of a Good Chapter

### 1. Opening paragraph

State the purpose of the chapter and what the reader should understand by the end. Not a summary of contents—a statement of intent.

**Good:** "This chapter explains how the Hub routes commands to handlers and why handlers publish events rather than returning values. Understanding this pattern is essential for every phase that follows."

**Bad:** "In this chapter, we will explore the command path, including handlers, the hub, event publishing, and related concepts."

### 2. Conceptual foundation

Build the mental model before showing code. Explain why the design exists before showing how it works.

**Good:** "If handlers returned values directly, the framework would have to decide what to do with those values. That knowledge would have to live somewhere—and it would quickly become tangled."

**Bad:** "Handlers publish events through the event publisher. Let's look at the handler code."

### 3. Code and pseudocode

Ground the explanation in concrete implementation. Show the actual structure, not a generic sketch.

**Good:** Show a real handler with real event types and a real publisher call.

**Bad:** "The handler does some stuff and then publishes events."

### 4. Tables and diagrams

Use these for comparisons, sequences, and architectures. They do work that prose cannot.

**Good:** A table showing UIProjection vs TimelineProjection responsibilities side by side.

**Bad:** Two paragraphs trying to describe the same comparison.

### 5. Trace examples

Show real trace output and walk through it step by step. This connects the teaching text to the working system.

**Good:** Show the actual JSON trace from a Phase 1 submission, with annotations explaining each step.

**Bad:** "The trace shows what happened internally."

### 6. Key points (bullet list)

Surface the most important takeaways in a bullet list. These are the things the reader should remember.

Each bullet should be a complete sentence. The bullets should summarize, not introduce new information.

### 7. Closing

Connect back to the chapter's purpose. "Now that you understand X, you can see why Y matters. The next phase builds on this."

## Interactive Elements

### Controls Placement

When a chapter describes an interactive exercise:

1. **Inline controls in "Try" sections.** If the chapter explains what a control does, put the control near that explanation. The reader should not have to scroll from explanation to action.

2. **Side-by-side layout.** Chapter text on the left, evidence/output on the right. When the reader submits input, results appear immediately adjacent to the controls.

3. **Evidence that teaches.** Raw JSON is not evidence—it's data. Evidence is a rendered view that shows the reader what the trace means. Use icons, step numbers, and readable labels.

### ToggledViewer Pattern

For any evidence panel showing structured data:

- **JSON mode**: Full structural data for debugging. Show the raw JSON with proper formatting.
- **Rendered mode**: Human-readable view that shows meaning, not just structure.

Rendered mode guidelines:
- Event names as readable labels (`LabStarted` → `● Started`)
- Status icons (● in-progress, ✓ complete, ✗ error)
- Key properties on separate lines
- Ordinals dimmed or shown separately (technical detail, not primary meaning)
- Visual hierarchy: event name prominent, details indented

Example JSON → Rendered:

```json
{"step": 1, "kind": "command", "message": "LabStart received"}
```

Rendered:
```
① Command received: LabStart
```

### Widget Inventory for Systemlab

| Widget | Purpose | States |
|--------|---------|--------|
| `ChapterViewer` | Renders chapter markdown with styled prose | loading, ready |
| `ScenarioControls` | Grouped inputs + actions for a scenario | idle, running, complete |
| `ToggledViewer` | JSON ↔ Rendered toggle for evidence | json-mode, rendered-mode |
| `TraceTimeline` | Sequential trace with step numbers | empty, running, complete |
| `CheckList` | Invariant badges | all-pass, partial, all-fail |
| `WebSocketClient` | Simulated client with state indicators | disconnected, connected, subscribed, hydrated |

## Writing Prompts for Quality

Before writing any section, answer these:

1. **What should the reader understand after reading this?** (State it in one sentence.)

2. **Why does this design exist?** (Not how—why. What problem does it solve?)

3. **What would break if this were removed?** (Helps explain importance.)

4. **What code or trace can I show that makes this concrete?** (Abstract descriptions without examples are hollow.)

5. **What is the most common misunderstanding here?** (Address it directly.)

## Example Chapter Structure (Phase 1)

```
1. The Command Path
   1.1 Submit hits the Hub
   1.2 What handlers publish and why
   1.3 Ordinals: why order matters
   1.4 Two projections, one source, different jobs
   1.5 Reading the trace
```

Each subsection:
- Opens with a paragraph that develops the concept
- Includes code or pseudocode
- Uses tables/diagrams where they add clarity
- Closes with key points in bullet form

## Anti-Patterns Summary

| Anti-Pattern | Why It's Bad | Fix |
|-------------|--------------|-----|
| Wandering preamble | Signals insecurity, wastes time | Start with the point |
| Hedged non-claims | Says nothing | Be direct |
| Vague bullet lists | No content | Each bullet is a complete sentence |
| Philosophical throat-clearing | Filler | Show the code, let reader decide |
| Overused qualifiers | Implies uncertainty | Just say it |
| "This is one of those..." | Buys time, adds nothing | Be specific |
| Bullets that are fragments | Incomplete thoughts | Write complete sentences |
| Walls of text | Exhausts reader | Break with code, tables, diagrams |
| "As you can see" | Condescending | Just show it |
| "It's important to note" | Redundant structure | Just note it |

## Quick Reference: Phases and Their Teaching Goals

| Phase | Core Teaching Goal |
|-------|-------------------|
| Phase 0 | What evtstream is, why it exists, what Systemlab is for |
| Phase 1 | Command → Event → Projection flow, canonical events |
| Phase 2 | Watermill bus, consumer-side ordinal assignment, ordering |
| Phase 3 | Websocket transport, snapshot-before-live, reconnect |
| Phase 4 | Chat built ON evtstream (not in it), stop behavior |
| Phase 5 | SQL hydration, restart correctness, cursor preservation |

For each phase: focus on ONE core insight. Build to it. Prove it with working code. Connect it to what came before and what comes after.