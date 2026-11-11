---
name: brutalist-work-slip
description: "Print brutalist thermal work slips about current work in one call. Two modes: 'status' (task id, commit QR code, what was done, what was tricky, what's next) and 'plan' (up-front checklist of all task phases, optional reference QR). Use when the user asks to print a slip/ticket about what they did, print a progress/status ticket, print a task plan or phase list on the thermal printer, or wants a commit QR printout."
metadata:
  title: Brutalist Work Slip
  topics:
    - almanach
    - printing
    - thermal-printer
    - brutalist
    - work-slips
  what_for: "One-call brutalist thermal printouts of work status (done/tricky/next + commit QR) or up-front phase plans, via a constrained DSL that generates the almanach YAML for you."
  when_to_use: Use when printing progress or plan tickets on the almanach thermal printer.
---

# Brutalist Work Slip

Print a brutalist work slip on the AtomS3R thermal printer in **one call**. The
script builds the almanach layout YAML for you from a small, strict set of
flags (the constrained DSL) and prints it through the remote almanach service.
Never hand-write slip YAML; always use the script.

## Script

```
~/.pi/agent/skills/brutalist-work-slip/scripts/work_slip.py
```

Requires: `python3` with `pyyaml`, and `almanach-render-service` on PATH
(override with `ALMANACH_CMD`). Default behavior: generate YAML to a temp file
and print for real. Flags `--out FILE` (keep YAML), `--no-print` (generate
only), `--dry-run-remote` (validate against the remote renderer without
printing).

## Mode 1: `status` — progress slip for current work

Prints: task id + label header, h1 title, optional summary paragraph, a "what
was done" bullet list, an optional "what was tricky" list (marker `!`), a
facts table (COMMIT + NEXT + extras), and a QR code linking to the commit URL
on GitHub (when `--commit` is given).

**Always use `--summary` to state the INTENT of the step, not just its actions.**
One or two sentences answering "why does this step exist / what is it trying to
achieve", so a future reader can reconstruct the reasoning without reading the
commit. The `--did` bullets say *what* was done; `--summary` says *why it
matters*.

Good: `--summary "Add graceful converter discovery so a missing rsvg-convert
never hard-fails document conversion."`
Weak: `--summary "Added config and converter discovery."`

```bash
python3 ~/.pi/agent/skills/brutalist-work-slip/scripts/work_slip.py status \
  --task GEPPETTO-RERANKER-002 \
  --label "STEP 3" \
  --title "Wired In: Factory, JS, Docs" \
  --summary "Intent: make Cohere rerank usable end-to-end so gp.reranker works with zero JS changes, via profile-driven factory construction." \
  --did "factory cohere case + key resolution" \
  --did "per-type validation diagnostics" \
  --did "goja parity proven from YAML" \
  --tricky "base-url override placement in api maps" \
  --next "P6 final validation sweep" \
  --commit 66b4e650 \
  --repo go-go-golems/geppetto
```

Flag reference (`status`):

| Flag | Required | Repeatable | Meaning |
|---|---|---|---|
| `--task` | yes | no | Task/ticket id shown top-left (keep ≤ 14 chars) |
| `--label` | no | no | Top-right label, e.g. `"STEP 3"` (default `STATUS`) |
| `--title` | yes | no | h1 headline; ≤ ~54 chars (3 short lines at 384px) |
| `--summary` | no | no | One short body paragraph, 1–2 sentences |
| `--did` | yes (≥1) | yes | One "what was done" bullet per flag; ≤ ~40 chars each |
| `--tricky` | no | yes | One "what was tricky" bullet per flag; omit entirely if nothing was tricky |
| `--next` | yes | no | What's next, short (goes into the facts table) |
| `--commit` | no | no | Commit hash; QR encodes `https://github.com/<repo>/commit/<hash>` |
| `--repo` | no | no | `owner/name` for the commit URL; default: auto-detect from `git remote get-url origin` in cwd |
| `--fact` | no | yes | Extra facts-table row as `KEY=VALUE`, e.g. `--fact "TESTS=30 PASS"` |

## Mode 2: `plan` — up-front phase checklist

Prints: task id + label header, h1 title, optional summary, a `PLAN` checklist
(one checkbox per phase), a facts table (PHASES count + NEXT + extras), and a
QR code when `--url` is given (ticket, PR, or docs link).

**Always use `--summary` to state the ticket's GOAL — what the whole effort is
about** — not just a restatement of the phases. This is the slip most likely to
be read cold months later, so it must explain the point of the ticket in plain
language: the problem, what is being built, and why. Start it with `GOAL:` when
useful. Keep it to 2–4 short sentences.

```bash
python3 ~/.pi/agent/skills/brutalist-work-slip/scripts/work_slip.py plan \
  --task GEPPETTO-RERANKER-002 \
  --label PLAN \
  --title "Cohere Rerank Salvage Plan" \
  --summary "GOAL: replace the deprecated legacy rerank path with the ported pkg/rerank implementation so callers stop depending on removed code, while keeping Goja parity." \
  --phase "P1 adapter core" \
  --phase "P2 mock-server tests" \
  --phase "P3 factory wiring" \
  --phase "P4 goja parity" \
  --phase "P5 docs + live test" \
  --phase "P6 final validation" \
  --next "P1 adapter core" \
  --url https://github.com/go-go-golems/geppetto/pull/169
```

Flag reference (`plan`): same common flags as `status`, except:

| Flag | Required | Repeatable | Meaning |
|---|---|---|---|
| `--phase` | yes (≥1) | yes | One phase line per flag, e.g. `"P1 adapter core"`; ≤ ~40 chars each |
| `--url` | no | no | QR target (ticket / PR / docs URL) |
| `--next` | no | no | First phase or immediate next step |

(`status` has no `--phase`/`--url`; `plan` has no `--did`/`--tricky`/`--commit`/`--repo`.)

## Content rules (keep slips readable)

- Title: ≤ ~54 chars, plain words; the h1 fits ~2–3 words per line.
- Bullets/phases: ≤ ~40 chars each, start lowercase or with a phase tag; 3–6 items is the sweet spot (each gets up to 2 lines).
- Summary: **required in practice** — `plan` states the ticket goal/context; `status` states the intent of the step. Never just re-list the bullets. Skip only when there is genuinely nothing to explain.
- Persist forever: assume a slip is read cold. A `plan` slip must be understandable with no other context (what is this ticket, why does it exist); a `status` slip must explain the purpose of its step, not merely its mechanics.
- Facts keys: short uppercase (`COMMIT`, `NEXT`, `TESTS`, `BRANCH`).
- Nothing was tricky? Omit `--tricky` — do not print filler like "nothing".

## Recommended workflow

1. Optional: `--dry-run-remote` to validate without wasting paper.
2. Print for real (default).
3. Keep the YAML with `--out` only when archiving a slip in a repo (e.g. under `ttmp/YYYY-MM-DD/`).

## Troubleshooting

- `error: status mode requires at least one --did item` / `--phase` — the lists are mandatory; add at least one.
- `warning: --commit given but no --repo and no git origin detected` — run inside the repo or pass `--repo owner/name`; the slip still prints, just without a QR.
- `print command failed` — check `almanach-render-service` is installed and the remote service is healthy (`curl https://almanach.crib.scapegoat.dev/health`); see the `almanach-printing` skill for printer issues.
