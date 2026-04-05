---
name: close-dependabot-prs
description: Scan open Dependabot PRs, summarize CI and mergeability, and merge or close ready PRs using gh. Includes a bundled scanner script at scripts/scan_dependabot_prs.py.
---

# Close Dependabot PRs

Use this skill when the user wants to inspect, merge, or close Dependabot PRs across a GitHub org.

## Workflow

1. Scan the org with the bundled script:
   - `python3 scripts/scan_dependabot_prs.py <org> --format both`
   - Add `--ready-only` to list only PRs that look mergeable, clean, and CI-passing.
2. Treat a PR as ready only when:
   - `mergeable == MERGEABLE`
   - `mergeStateStatus == CLEAN`
   - CI summary is `passing`
3. Prefer merging ready PRs with `gh pr merge --squash --admin`.
4. After each merge batch, rescan before touching the next PRs.
5. Stop on conflicts or failing CI. Do not guess past the scan output.

## Script Output

The scanner prints:

- a human table with `repo`, `pr`, `author`, `mergeable`, `ci`, `ready`, and `title`
- JSON with the same fields plus the nested CI check list

## Notes

- The script lives at `scripts/scan_dependabot_prs.py`.
- Some workflow-file PRs may need local git merge and push if GitHub blocks the API merge path.
- Use `gh` for PR inspection and merge operations; only close a PR manually when the user explicitly asks for closure without merge.
