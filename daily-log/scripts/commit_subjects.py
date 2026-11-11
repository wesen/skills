#!/usr/bin/env python3
"""Gather commit subjects (hash|date|subject) per repo per day.

Produces a JSON file keyed by day, then repo, then a list of
"H|YYYY-MM-DD|subject" strings. This is the narrative evidence used to
write the per-stream "What happened" sections.

Usage:
  commit_subjects.py <git-commits-per-day.json> [--output commit-subjects.json]
"""
import argparse, json, os, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("git_commits_json", help="output of git_commits.py")
    ap.add_argument("--output", default="commit-subjects.json")
    args = ap.parse_args()

    gc = json.load(open(args.git_commits_json))
    days = set()
    for counts in gc.values():
        days.update(counts.keys())
    days = sorted(days)

    out = {}
    for day in days:
        out[day] = {}
        for repo, counts in gc.items():
            if counts.get(day, 0) > 0:
                r = subprocess.run(
                    ["git", "-C", repo, "log",
                     f"--since={day} 00:00:00",
                     f"--until={day} 23:59:59",
                     "--date=short", "--pretty=%h|%ad|%s"],
                    capture_output=True, text=True, timeout=30,
                )
                out[day][repo] = [l for l in r.stdout.strip().split("\n") if l.strip()]

    with open(args.output, "w") as fh:
        json.dump(out, fh, indent=2)

    for day in days:
        total = sum(len(v) for v in out[day].values())
        print(f"{day}: {total} commit subjects across {len(out[day])} repos", file=sys.stderr)
    print(f"\nSaved -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
