# Research Report Structure Template

This template defines the recommended section structure for a research report. Not every section is required for every topic, but this is the default order. Adapt as needed, but do not omit sections without reason.

## Recommended Section Order

1. **Executive Summary** — What the report covers, what the key findings are, and why they matter. Written last, placed first. 1–2 paragraphs.

2. **The Problem** — What problem the technology/architecture/system was trying to solve. Why did the designers make the choices they made? What constraints shaped the design? This section should make the reader understand the design decisions before seeing the technical details.

3. **The Data Model / Core Architecture** — The central technical abstraction explained in depth. What are the key entities? How do they relate? What are the access patterns? Include code examples, data structure sketches, and API signatures from primary sources.

4. **The Programming Language / Implementation Layer** — How the programming model connects to the data model. Why was this language chosen over alternatives? What properties of the language enable the architecture? What are the key language features that matter?

5. **The UX Paradigm** — How the user experiences the system. What mental model does the UX impose? How does the data architecture shape the user experience? What UI patterns emerge from the technical design?

6. **Historical Context and Contemporary Systems** — What else was happening at the time? What alternative approaches existed? How did contemporary systems solve the same problems differently? Include direct quotes from historical sources.

7. **Modern Comparisons** — How does the system compare to modern equivalents? What did it get right that we lost? What ideas are worth reviving? Use comparison tables for systematic analysis.

8. **Architecture Diagrams** — Mermaid diagrams showing data flow, component relationships, and lifecycle transitions. At least 2 diagrams for a substantial report.

9. **Key Technical Details for Reimplementation** — Concrete code examples, API signatures, and data model sketches in a modern language (TypeScript, Go, Python). This is not "code that runs" — it is "code that teaches."

10. **References and Sources** — Tables listing all primary documents (with file paths in sources/) and external references (with URLs). Organized by category (primary documents, web sources, external references).

11. **Open Questions for Future Investigation** — Genuine unknowns that the research could not resolve. Each question should explain why it matters and what would be needed to answer it.

## Section Depth Guidelines

Each section (except Executive Summary and Open Questions) should be at least 2–3 KB of prose for a substantial topic. Sections 3, 4, and 5 are typically the longest (5–10 KB each) because they contain the core technical content.

The total report should target 50–80 KB for a substantial research topic. Reports shorter than 30 KB are almost certainly too terse.

## Prose Patterns by Section Type

### For technical architecture sections (3, 4)
Start with the design problem, then show the solution, then explain why this solution works. Use code examples from primary sources. Include comparison tables when multiple mechanisms exist.

### For UX sections (5)
Describe what the user does, then explain what happens technically, then connect the UX behavior to the underlying architecture. Use direct quotes from UI guidelines or user documentation.

### For historical sections (6)
Present the historical context as a narrative, but ground every claim in a cited source. Use direct quotes from historical figures. Include comparison tables for contemporary systems.

### For modern comparison sections (7)
Use tables for systematic comparison. Follow each table with prose that explains the key differences and their implications. Do not just list differences — explain what they mean for someone building a modern system.
