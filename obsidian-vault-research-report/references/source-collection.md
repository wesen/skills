# Research Source Collection Guide

This guide describes how to collect sources for a research report using the tools available in the pi environment.

## Source Collection Pipeline

### 1. Kagi Web Search (breadth)

Use `kagi_web_search` for initial discovery. Run 3–5 parallel searches with different query formulations:

```
kagi_web_search(query="topic architecture paradigm", max_results=15)
kagi_web_search(query="topic internals mechanism how works", max_results=15)
kagi_web_search(query="topic historical context comparison alternatives", max_results=15)
```

Each search returns up to 15 results with URLs and descriptions. Skim all results and identify:
- Wikipedia articles (factual overviews)
- Primary source documents (papers, manuals, official docs)
- Community discussions (forums, HN, blog posts with insider perspective)
- Modern implementations or re-creations (GitHub repos)

### 2. Defuddle (download web pages)

For every promising web result, download the full content:

```bash
defuddle parse "<url>" --md -o ttmp/.../sources/<descriptive-name>.md
```

Naming convention: `<source>-<topic>.md` (e.g., `wikipedia-soup-apple.md`, `retrocomputing-newton-object-soup.md`)

Defuddle extracts clean markdown, removing navigation and ads. This is far better than relying on the search snippet.

### 3. PDF Downloads (primary documents)

Download PDFs directly with curl:

```bash
curl -sL "<url>" -o ttmp/.../sources/<author>-<topic>.pdf
```

PDFs are the most important sources — they are the original papers, manuals, and specifications. Prioritize:
- Academic papers (conference proceedings, journal articles)
- Official documentation (programming guides, API references, UI guidelines)
- Historical documents (product specifications, internal memos)

### 4. Kagi Assistant (deep synthesis)

Use `surf kagi assistant` with `--web-search-mode on` for synthesized analysis:

```bash
surf kagi assistant --web-search-mode on --prompt-timeout-sec 180 \
  'Research <topic> in depth. I need to understand: <numbered questions>. Please be thorough and cite specific sources.'
```

The assistant provides a synthesized analysis with 10+ cited sources per call. It is not a replacement for reading primary sources, but it fills gaps and makes connections that simple searches miss.

Run 2–3 assistant calls with different focus areas (e.g., architecture, UX, modern comparisons).

### 5. ChatGPT Assistant (alternative synthesis)

If available (login required), use `surf chatgpt ask` for additional depth. Falls back to Kagi Assistant if unavailable.

### 6. Targeted follow-up searches

After the initial round, run targeted searches for specific gaps:
- Historical quotes and insider accounts
- Specific technical mechanisms not covered in broad searches
- Modern comparisons and implementations
- Original articles or papers referenced in other sources

## Source Organization

Store all sources in the ticket's `sources/` directory:

```
sources/
├── author-topic.pdf          # PDFs with author-topic naming
├── source-topic.md           # defuddle extractions
├── ...                       # typically 15-25 files
```

## Source Citation in the Report

In the report's References section, use a table format:

```markdown
| File | Description |
|------|-------------|
| [author-topic.pdf](sources/author-topic.pdf) | Author, A. (Year). "Title." Venue. |
| [source-topic.md](sources/source-topic.md) | Source name: Topic description |
```

For external references not downloaded, include the URL:

```markdown
| Reference | URL |
|-----------|-----|
| Author, A. (Year). "Title." Venue | https://... |
```

## Minimum Source Count

A substantial research report should have at least 15–20 sources. If you have fewer, the research is not deep enough. Go back and search for more specific aspects of the topic.
