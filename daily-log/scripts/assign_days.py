#!/usr/bin/env python3
"""Assign sessions to specific days based on activity-window overlap.

The discovery step uses `--active-since <EARLIEST_DAY>`, which returns a
cumulative superset of every session active from that day onward. This
script splits that superset into per-day sets by checking whether each
session's [started_at, last_activity_at] window overlaps each target day
(in UTC).

Usage:
  assign_days.py <DISCOVERY_DIR> [--days DAY1,DAY2,...] [--output day-assignment.json]

DISCOVERY_DIR must contain pi-discovery.json, codex-discovery.json, and
claude-code-discovery.json (as produced by generate_daily_log.sh).

If --days is omitted, the script infers the range from the earliest
session started_at to today.
"""
import argparse, json, os, sys
from datetime import datetime, timezone, timedelta


def parse(ts):
    if not ts:
        return None
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("discovery_dir", help="dir with pi/codex/claude-code-discovery.json")
    ap.add_argument("--days", help="comma-separated YYYY-MM-DD days to assign (default: infer)")
    ap.add_argument("--output", default="day-assignment.json")
    args = ap.parse_args()

    sessions = []
    for name in ["pi", "codex", "claude-code"]:
        p = os.path.join(args.discovery_dir, f"{name}-discovery.json")
        try:
            for s in json.load(open(p)):
                s["_framework"] = name
                sessions.append(s)
        except FileNotFoundError:
            print(f"WARNING: {p} not found", file=sys.stderr)

    # Determine the day range
    if args.days:
        days = args.days.split(",")
    else:
        starts = [parse(s.get("started_at")) for s in sessions]
        starts = [x for x in starts if x]
        if not starts:
            print("ERROR: no sessions with started_at", file=sys.stderr)
            sys.exit(1)
        earliest = min(starts).astimezone(timezone.utc).date()
        today = datetime.now(timezone.utc).date()
        days = []
        d = earliest
        while d <= today:
            days.append(d.isoformat())
            d += timedelta(days=1)

    day_sessions = {d: [] for d in days}
    for s in sessions:
        started = parse(s.get("started_at"))
        last = parse(s.get("last_activity_at"))
        if not started:
            continue
        end = last or started
        for d in days:
            day_start = datetime.fromisoformat(d + "T00:00:00+00:00")
            day_end = datetime.fromisoformat(d + "T23:59:59+00:00")
            if started <= day_end and end >= day_start:
                day_sessions[d].append(s)

    out = {}
    for d in days:
        fw = {}
        for s in day_sessions[d]:
            fw[s["_framework"]] = fw.get(s["_framework"], 0) + 1
        print(f"{d}: {len(day_sessions[d])} sessions  {fw}")
        out[d] = []
        for s in day_sessions[d]:
            out[d].append({
                "id": s.get("id"),
                "framework": s["_framework"],
                "model": s.get("model"),
                "title": s.get("title"),
                "cwd": s.get("cwd"),
                "started_at": s.get("started_at"),
                "last_activity_at": s.get("last_activity_at"),
                "source_path": s.get("source_path"),
            })

    with open(args.output, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nSaved {args.output}")


if __name__ == "__main__":
    main()
