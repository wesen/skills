#!/usr/bin/env python3
"""Count git commits per day per repository (HEAD only, local timezone).

This is the git-verification stage. It walks candidate roots for .git repos
and counts commits in each day's window using `git log --since/--until`
(HEAD only — never --all, which double-counts across branches).

CRITICAL: build the --since/--until strings with f-strings (or .format).
A plain string like '--until={d} 23:59:59' passes a literal '{d}' to git,
which git SILENTLY IGNORES (no stderr warning), returning every commit
since --since. This produces a 10-100x overcount with no error signal.

CRITICAL: do not use --all. `git log --all --since/--until` counts a
commit once per branch that contains it, double- or triple-counting
merge-heavy repos. Use plain `git log` (HEAD only).

Usage:
  git_commits.py <DAYS_CSV> [--roots ROOT1,ROOT2,...] [--output OUT.json]

DAYS_CSV   e.g. 2026-07-21,2026-07-22,2026-07-23
--roots    comma-separated search roots (default: ~/code/wesen,~/workspaces)
--output   default: git-commits-per-day.json
"""
import argparse, json, os, subprocess, sys


def find_repos(roots):
    repos = []
    for root in roots:
        if not os.path.exists(os.path.expanduser(root)):
            continue
        for dirpath, dirnames, _ in os.walk(os.path.expanduser(root)):
            if ".git" in dirnames:
                repos.append(dirpath)
                dirnames[:] = []  # don't descend into the repo
            rel = os.path.relpath(dirpath, os.path.expanduser(root))
            if rel.count(os.sep) >= 4:
                dirnames[:] = []
    return sorted(set(repos))


def count_commits(repo, day):
    """Count HEAD commits in [day 00:00:00, day 23:59:59] (local tz)."""
    # NOTE: both --since and --until MUST be f-strings. A literal '{d}'
    # in --until is silently ignored by git, returning all commits since
    # --since (a massive overcount with no error).
    out = subprocess.run(
        ["git", "-C", repo, "log",
         f"--since={day} 00:00:00",   # f-string: interpolates
         f"--until={day} 23:59:59",   # f-string: interpolates
         "--date=short", "--pretty=%H"],
        capture_output=True, text=True, timeout=30,
    )
    return len([l for l in out.stdout.strip().split("\n") if l.strip()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("days", help="comma-separated YYYY-MM-DD days")
    ap.add_argument("--roots", default="~/code/wesen,~/workspaces",
                    help="comma-separated search roots")
    ap.add_argument("--output", default="git-commits-per-day.json")
    args = ap.parse_args()

    days = args.days.split(",")
    roots = args.roots.split(",")
    repos = find_repos(roots)
    print(f"Found {len(repos)} git repos", file=sys.stderr)

    results = {}
    for repo in repos:
        counts = {}
        for d in days:
            counts[d] = count_commits(repo, d)
        total = sum(v for v in counts.values() if v > 0)
        if total > 0:
            results[repo] = counts

    with open(args.output, "w") as fh:
        json.dump(results, fh, indent=2)

    print("\n=== Per-day commit totals (HEAD only) ===", file=sys.stderr)
    for d in days:
        day_total = sum(r.get(d, 0) for r in results.values() if r.get(d, 0) > 0)
        repos_active = [r for r, v in results.items() if v.get(d, 0) > 0]
        print(f"{d}: {day_total} commits across {len(repos_active)} repos", file=sys.stderr)
    print(f"\nSaved {len(results)} repos with commits -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
