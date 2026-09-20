#!/usr/bin/env python3
"""Build a self-contained, browsable HTML summary page for coding-agent transcripts.

Accepts native transcript paths directly, a workspace to discover sessions in,
or an existing glob of converted minitrace archives. Uses go-minitrace for
discovery/conversion and reads the normalized archive JSON for the page data.
"""

from __future__ import annotations

import argparse
import glob as globlib
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone

FRAMEWORKS = ("claude-code", "pi", "codex")

DEFAULT_SOURCE_DIRS = {
    "claude-code": "~/.claude/projects",
    "pi": "~/.pi/agent/sessions",
    "codex": "~/.codex",
}

# Session-opening noise that is not the user's actual request.
NOISE_PREFIXES = (
    "<local-command",
    "<command-name",
    "<command-message",
    "<system-reminder",
    "<user_info>",
    "[REMINDER]",
    "# AGENTS.md instructions",
    "Caveat:",
)

FRAMEWORK_LABELS = {
    "claude-code": "Claude Code",
    "pi": "Pi",
    "codex": "Codex",
}


# ── process helpers ──────────────────────────────────────────────────────
def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def have_go_minitrace() -> bool:
    return shutil.which("go-minitrace") is not None


def detect_framework(path: str) -> str | None:
    p = os.path.abspath(os.path.expanduser(path))
    if "/.pi/" in p or "/pi/agent/sessions/" in p:
        return "pi"
    if "/.codex/" in p:
        return "codex"
    if "/.claude/" in p:
        return "claude-code"
    return None


# ── acquisition ──────────────────────────────────────────────────────────
def discover(workspace: str, since: str | None, frameworks: list[str], source_dirs: dict[str, str]) -> dict[str, list[str]]:
    fragment = workspace.rstrip("/")
    found: dict[str, list[str]] = {}
    for fw in frameworks:
        cmd = ["go-minitrace", "discover", fw, "--source-dir", os.path.expanduser(source_dirs[fw]),
               "--cwd-contains", fragment, "--output", "json"]
        if since:
            cmd += ["--active-since", since]
        try:
            proc = run(cmd)
        except subprocess.CalledProcessError as exc:
            print(f"warn: discover {fw} failed: {exc.stderr.strip()[:200]}", file=sys.stderr)
            continue
        try:
            rows = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            print(f"warn: discover {fw} returned unparseable JSON", file=sys.stderr)
            continue
        found[fw] = [r["source_path"] for r in rows if r.get("source_path")]
    return found


def convert(frameworks: dict[str, list[str]], work_dir: str) -> None:
    for fw, paths in frameworks.items():
        if not paths:
            continue
        list_file = os.path.join(work_dir, f"{fw}-sources.txt")
        with open(list_file, "w") as fh:
            fh.write("\n".join(paths) + "\n")
        out_dir = os.path.join(work_dir, "archives", fw)
        cmd = ["go-minitrace", "convert", fw, "--source-list", list_file, "--output-dir", out_dir]
        if fw == "codex":
            cmd += ["--collision", "replace"]
        try:
            run(cmd)
        except subprocess.CalledProcessError as exc:
            print(f"warn: convert {fw} failed: {exc.stderr.strip()[:300]}", file=sys.stderr)
            continue
        print(f"converted {len(paths)} {fw} source(s)")


# ── extraction ───────────────────────────────────────────────────────────
def clean_text(text) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def is_substantive(text: str) -> bool:
    if not text:
        return False
    s = text.lstrip()
    return not any(s.startswith(p) or p in s[:160] for p in NOISE_PREFIXES)


def first_substantive(turns: list[dict], role: str, min_chars: int) -> str:
    for turn in turns:
        if turn.get("role") != role:
            continue
        text = clean_text(turn.get("content"))
        if role == "user" and not is_substantive(text):
            continue
        if role == "assistant" and len(text) < min_chars:
            continue
        if text:
            return text
    return ""


def last_substantive(turns: list[dict], role: str, min_chars: int) -> str:
    for turn in reversed(turns):
        if turn.get("role") != role:
            continue
        text = clean_text(turn.get("content"))
        if role == "user" and not is_substantive(text):
            continue
        if role == "assistant" and len(text) < min_chars:
            continue
        if text:
            return text
    return ""


SUMMARY_FIELDS = ("this turn", "session so far", "issues", "next steps")
SUMMARY_BLOCK_RE = re.compile(r"<summary>([\s\S]*?)</summary>", re.IGNORECASE)


def parse_summary_block(block: str) -> tuple[dict[str, str], str]:
    """Split a <summary> body into its four known fields, keeping free prose as fallback."""
    sections: dict[str, list[str]] = {key: [] for key in SUMMARY_FIELDS}
    fallback: list[str] = []
    current: str | None = None
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z][A-Za-z ]*?):\s*(.*)$", line)
        key = match.group(1).strip().lower() if match else None
        if key in sections:
            current = key
            rest = match.group(2).strip()
            if rest:
                sections[current].append(rest)
        elif current:
            sections[current].append(line)
        else:
            fallback.append(line)
    return ({key: " ".join(value) for key, value in sections.items()}, " ".join(fallback))


def extract_summaries(turns: list[dict]) -> list[dict]:
    """Every <summary> block an assistant emitted, in order, parsed into fields."""
    summaries = []
    for turn in turns:
        if turn.get("role") != "assistant":
            continue
        content = turn.get("content") or ""
        for match in SUMMARY_BLOCK_RE.finditer(content):
            fields, fallback = parse_summary_block(match.group(1))
            if not any(fields.values()) and not fallback:
                continue
            summaries.append({
                "turn": turn.get("index"),
                "at": turn.get("timestamp") or "",
                "fields": {key: value for key, value in fields.items() if value},
                "fallback": fallback,
            })
    return summaries


def tool_input_path(tc: dict) -> str | None:
    inp = tc.get("input")
    if not isinstance(inp, dict):
        return None
    path = inp.get("file_path")
    if not path:
        args = inp.get("arguments")
        if isinstance(args, dict):
            path = args.get("file_path")
    return path if isinstance(path, str) and path else None


def shorten(path: str, prefixes: list[str]) -> str:
    for prefix in prefixes:
        if prefix and path.startswith(prefix):
            return path[len(prefix):]
    return path


def files_touched(tool_calls: list[dict], prefixes: list[str]) -> list[list[str]]:
    seen: dict[str, str] = {}
    for tc in tool_calls:
        if tc.get("operation_type") not in ("NEW", "MODIFY"):
            continue
        path = tool_input_path(tc)
        if not path:
            continue
        seen.setdefault(shorten(path, prefixes), tc["operation_type"])
    return sorted([p, op] for p, op in seen.items())


def op_counts(tool_calls: list[dict]) -> dict[str, int]:
    counts = {"create": 0, "modify": 0, "execute": 0, "read": 0}
    mapping = {"NEW": "create", "MODIFY": "modify", "EXECUTE": "execute", "READ": "read"}
    for tc in tool_calls:
        key = mapping.get(tc.get("operation_type"))
        if key:
            counts[key] += 1
    return counts


def extract_sessions(archives: list[str], prefixes: list[str], min_chars: int, no_files: bool) -> list[dict]:
    sessions = []
    for path in archives:
        try:
            with open(path) as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warn: skipped {path}: {exc}", file=sys.stderr)
            continue
        timing = doc.get("timing") or {}
        env = doc.get("environment") or {}
        opctx = doc.get("operational_context") or {}
        metrics = doc.get("metrics") or {}
        tool_calls = doc.get("tool_calls") or []
        turns = doc.get("turns") or []
        counts = op_counts(tool_calls)
        summaries = extract_summaries(turns)
        sessions.append({
            "id": str(doc.get("id") or (doc.get("provenance") or {}).get("original_session_id") or "?"),
            "framework": env.get("agent_framework") or "unknown",
            "title": doc.get("title") or "(untitled)",
            "model": env.get("model") or "unknown model",
            "started": timing.get("started_at") or "",
            "ended": timing.get("ended_at") or "",
            "duration_s": timing.get("active_duration_seconds") or timing.get("duration_seconds") or 0,
            "cwd": opctx.get("working_directory") or "",
            "branch": opctx.get("git_branch") or "",
            "turns": metrics.get("turn_count") or len(turns),
            "tools": metrics.get("tool_call_count") or len(tool_calls),
            "create": counts["create"],
            "modify": counts["modify"],
            "read": counts["read"],
            "execute": counts["execute"],
            "task": first_substantive(turns, "user", min_chars),
            "outcome": last_substantive(turns, "assistant", min_chars),
            "files": [] if no_files else files_touched(tool_calls, prefixes),
            "summaries": summaries,
            "summary_count": len(summaries),
            "source": (doc.get("provenance") or {}).get("source_path") or "",
        })
    sessions.sort(key=lambda s: s["started"] or "")
    return sessions


# ── rendering ────────────────────────────────────────────────────────────
def render_html(sessions: list[dict], title: str, subtitle: str, note: str, lede: str) -> str:
    counts: dict[str, int] = {}
    for s in sessions:
        counts[s["framework"]] = counts.get(s["framework"], 0) + 1
    data = json.dumps(sessions, ensure_ascii=False)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    counts_text = " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    total_files = sum(len(s["files"]) for s in sessions)

    return TEMPLATE.replace("__DATA__", data) \
                   .replace("__NW__", str(len(sessions))) \
                   .replace("__COUNTS__", htmllib.escape(counts_text)) \
                   .replace("__TITLE__", htmllib.escape(title)) \
                   .replace("__SUBTITLE__", htmllib.escape(subtitle)) \
                   .replace("__LEDE__", lede) \
                   .replace("__NOTE__", note) \
                   .replace("__TOTALFILES__", str(total_files))


def build_note(archive_desc: str) -> str:
    return (
        "<strong>Method and caveats.</strong> Discovered and converted with "
        "<code>go-minitrace</code>; page data comes from the normalized archive JSON. "
        f"Archives: <code>{htmllib.escape(archive_desc)}</code>. Sessions are selected by recorded "
        "working directory, so a session started elsewhere but working here is not shown. File targets "
        "are structural NEW/MODIFY tool-call evidence, not independently verified commits; formats that "
        "expose only opaque <code>exec</code> wrappers, or edits hidden inside shell heredocs, produce "
        "none. &ldquo;Final report&rdquo; is the agent's own last message, not verification."
    )


# ── CLI ──────────────────────────────────────────────────────────────────
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="session_overview.py",
        description="Build a browsable HTML summary page for coding-agent transcripts.",
    )
    src = p.add_argument_group("input (choose one)")
    src.add_argument("--from-glob", action="append", default=[], metavar="GLOB",
                     help="glob of already-converted *.minitrace.json archives (repeatable)")
    src.add_argument("--source-session", action="append", default=[], metavar="PATH",
                     help="native transcript file to convert (repeatable; framework auto-detected)")
    src.add_argument("--source-list", action="append", default=[], metavar="FILE",
                     help="file of native transcript paths, one per line (repeatable)")
    src.add_argument("--workspace", metavar="DIR",
                     help="discover sessions whose recorded cwd contains DIR")

    disc = p.add_argument_group("discovery (with --workspace)")
    disc.add_argument("--active-since", metavar="DATE", default=None,
                      help="only sessions active at/after DATE (YYYY-MM-DD or RFC3339)")
    disc.add_argument("--framework", action="append", choices=FRAMEWORKS, default=[],
                      help="restrict to a framework (repeatable; default all)")
    disc.add_argument("--source-dir", action="append", default=[], metavar="FW=DIR",
                      help="override a framework's native session dir, e.g. pi=~/.pi/agent/sessions")

    out = p.add_argument_group("output")
    out.add_argument("--out", default=None, metavar="FILE",
                     help="HTML output path (default: ~/tmp/session-overview-<slug>.html)")
    out.add_argument("--json", dest="json_out", default=None, metavar="FILE",
                     help="also write the extracted session records as JSON")
    out.add_argument("--title", default=None, help="page title (default: workspace/repo name)")
    out.add_argument("--work-dir", default=None, metavar="DIR",
                     help="scratch dir for discovery/convert output (default: a temp dir)")
    out.add_argument("--strip-prefix", action="append", default=[], metavar="PREFIX",
                     help="prefix removed from displayed file paths (repeatable)")
    out.add_argument("--no-files", action="store_true", help="omit the file-target ledger entirely")
    out.add_argument("--min-assistant-chars", type=int, default=40,
                     help="ignore assistant messages shorter than this (default 40)")
    out.add_argument("--open", dest="open_page", action="store_true", default=True,
                     help="open the page in a browser when done (default)")
    out.add_argument("--no-open", dest="open_page", action="store_false")
    return p.parse_args(argv)


def gather_source_sessions(args: argparse.Namespace) -> dict[str, list[str]]:
    by_fw: dict[str, list[str]] = {}
    paths = list(args.source_session)
    for list_file in args.source_list:
        with open(list_file) as fh:
            paths += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    for path in paths:
        fw = detect_framework(path)
        if not fw:
            print(f"warn: cannot detect framework for {path}", file=sys.stderr)
            continue
        by_fw.setdefault(fw, []).append(os.path.expanduser(path))
    return by_fw


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    prefixes = [os.path.abspath(os.path.expanduser(p)) + ("" if p.endswith("/") else "/")
                for p in args.strip_prefix]
    source_dirs = dict(DEFAULT_SOURCE_DIRS)
    for entry in args.source_dir:
        if "=" not in entry:
            print(f"error: --source-dir wants FW=DIR, got {entry!r}", file=sys.stderr)
            return 2
        fw, directory = entry.split("=", 1)
        source_dirs[fw] = directory

    work_dir = args.work_dir or tempfile.mkdtemp(prefix="session-overview-")
    os.makedirs(work_dir, exist_ok=True)

    archives: list[str] = []
    archive_desc_parts: list[str] = []
    for pattern in args.from_glob:
        matched = sorted(globlib.glob(os.path.expanduser(pattern)))
        archives += matched
        archive_desc_parts.append(f"{pattern} ({len(matched)})")

    to_convert: dict[str, list[str]] = {}
    wanted = args.framework or list(FRAMEWORKS)

    if args.workspace:
        if not have_go_minitrace():
            print("error: go-minitrace is required for --workspace", file=sys.stderr)
            return 2
        workspace = os.path.abspath(os.path.expanduser(args.workspace))
        prefixes.insert(0, workspace + "/")
        prefixes.append(os.path.expanduser("~") + "/")
        print(f"discovering sessions under {workspace} ...")
        discovered = discover(workspace, args.active_since, wanted, source_dirs)
        for fw, paths in discovered.items():
            print(f"  {fw}: {len(paths)} session(s)")
        to_convert.update(discovered)
        archive_desc_parts.append(f"discover --cwd-contains {workspace}")

    direct = gather_source_sessions(args)
    for fw, paths in direct.items():
        to_convert.setdefault(fw, []).extend(paths)
    if direct:
        archive_desc_parts.append(f"{sum(len(v) for v in direct.values())} explicit source(s)")

    if to_convert:
        if not have_go_minitrace():
            print("error: go-minitrace is required to convert native transcripts", file=sys.stderr)
            return 2
        convert(to_convert, work_dir)
        archives += sorted(globlib.glob(os.path.join(work_dir, "archives", "*", "active", "*", "*.minitrace.json")))
        archive_desc_parts.append(f"converted into {work_dir}")

    archives = sorted(set(archives))
    if not archives:
        print("error: no archives. Pass --workspace, --source-session/--source-list, or --from-glob.",
              file=sys.stderr)
        return 2

    prefixes += [os.path.expanduser("~") + "/", "/"]
    seen_prefixes = []
    for p in prefixes:
        if p not in seen_prefixes:
            seen_prefixes.append(p)

    sessions = extract_sessions(archives, seen_prefixes, args.min_assistant_chars, args.no_files)
    if not sessions:
        print("error: archives contained no sessions", file=sys.stderr)
        return 1

    if args.workspace:
        slug = os.path.basename(os.path.abspath(os.path.expanduser(args.workspace))) or "sessions"
        subtitle = args.workspace
        default_title = f"Agent sessions in {slug}"
    else:
        slug = "transcripts"
        subtitle = f"{len(archives)} archive(s)"
        default_title = "Agent transcript overview"
    title = args.title or default_title

    lede = (
        f"Sessions selected from <code>{htmllib.escape(', '.join(archive_desc_parts)) or 'archives'}</code>, "
        "ordered by start time. Extracted with <code>go-minitrace</code>; task and outcome are the first "
        "substantive user prompt and the last substantive assistant message. "
        "<strong>/</strong> focuses search, <strong>Esc</strong> clears, click any path to copy it."
    )
    out_path = os.path.expanduser(args.out) if args.out else os.path.expanduser(f"~/tmp/session-overview-{slug}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    page = render_html(sessions, title, subtitle, build_note("; ".join(archive_desc_parts)), lede)
    with open(out_path, "w") as fh:
        fh.write(page)

    if args.json_out:
        json_path = os.path.expanduser(args.json_out)
        os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
        with open(json_path, "w") as fh:
            json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "sessions": sessions}, fh, indent=2)
        print(f"wrote {json_path}")

    total_files = sum(len(s["files"]) for s in sessions)
    total_summaries = sum(s.get("summary_count", 0) for s in sessions)
    print(f"wrote {out_path}")
    print(f"{len(sessions)} session(s), {total_files} file target(s), {total_summaries} summary block(s)")
    if args.open_page:
        webbrowser.open(f"file://{os.path.abspath(out_path)}")
    return 0


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --bg:#14161a; --panel:#191c21; --card:#22262d; --ink:#e8e6e1; --muted:#9aa0a8;
    --hair:#333941; --accent:#e0b44a; --claude:#d9895b; --pi:#7fb069; --codex:#6aa9d8;
    --new:#8fd18a; --mod:#e0b44a;
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.55 ui-monospace,"IBM Plex Mono",SFMono-Regular,Menlo,monospace; }
  a { color:inherit; }
  .layout { display:grid; grid-template-columns:270px minmax(0,1fr); min-height:100vh; }
  aside { position:sticky; top:0; height:100vh; overflow:auto; background:var(--panel);
    border-right:1px solid var(--hair); padding:18px 14px; }
  aside h1 { font-size:15px; margin:0 0 4px; }
  aside .sub { color:var(--muted); font-size:11px; margin-bottom:14px; }
  nav a { display:block; padding:6px 8px; border-left:2px solid transparent; text-decoration:none;
    font-size:12px; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  nav a:hover { background:#22262d; color:var(--ink); }
  nav a.active { border-left-color:var(--accent); color:var(--ink); background:#22262d; }
  nav a .dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:7px;
    vertical-align:middle; background:var(--hair); }
  nav a[data-fw="claude-code"] .dot { background:var(--claude); }
  nav a[data-fw="pi"] .dot { background:var(--pi); }
  nav a[data-fw="codex"] .dot { background:var(--codex); }
  main { padding:28px 28px 120px; max-width:1150px; }
  .top h2 { font-size:24px; margin:0 0 6px; letter-spacing:-.4px; }
  .lede { color:var(--muted); max-width:80ch; margin:0 0 18px; font-size:13px; }
  .controls { position:sticky; top:0; z-index:5; background:linear-gradient(var(--bg) 78%,transparent);
    padding:12px 0 14px; display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    border-bottom:1px solid var(--hair); }
  input[type=search], select { background:#0f1114; color:var(--ink); border:1px solid var(--hair);
    padding:7px 10px; font:inherit; font-size:12px; border-radius:2px; }
  input[type=search] { flex:1 1 260px; min-width:180px; }
  input[type=search]:focus, select:focus { outline:1px solid var(--accent); border-color:var(--accent); }
  .chips { display:flex; gap:6px; flex-wrap:wrap; }
  .chip { background:transparent; border:1px solid var(--hair); color:var(--muted); padding:6px 11px;
    font:inherit; font-size:12px; border-radius:999px; cursor:pointer; }
  .chip:hover { color:var(--ink); }
  .chip[aria-pressed=true] { color:#14161a; background:var(--ink); border-color:var(--ink); }
  .chip[data-fw=claude-code][aria-pressed=true] { background:var(--claude); border-color:var(--claude); }
  .chip[data-fw=pi][aria-pressed=true] { background:var(--pi); border-color:var(--pi); }
  .chip[data-fw=codex][aria-pressed=true] { background:var(--codex); border-color:var(--codex); }
  .btn { background:transparent; border:1px solid var(--hair); color:var(--muted); padding:6px 11px;
    font:inherit; font-size:12px; border-radius:2px; cursor:pointer; }
  .btn:hover { color:var(--ink); border-color:var(--muted); }
  .count { color:var(--muted); font-size:12px; margin-left:auto; white-space:nowrap; }
  .card { background:var(--card); border:1px solid var(--hair); border-left:3px solid var(--hair);
    padding:16px 18px; margin:14px 0; display:flex; flex-direction:column; gap:12px; scroll-margin-top:70px; }
  .card[data-fw=claude-code] { border-left-color:var(--claude); }
  .card[data-fw=pi] { border-left-color:var(--pi); }
  .card[data-fw=codex] { border-left-color:var(--codex); }
  .card.hit { box-shadow:0 0 0 1px var(--accent); }
  .card > header { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }
  .fw { font-size:10px; text-transform:uppercase; letter-spacing:1.6px; }
  .card[data-fw=claude-code] .fw { color:var(--claude); }
  .card[data-fw=pi] .fw { color:var(--pi); }
  .card[data-fw=codex] .fw { color:var(--codex); }
  h3 { font-size:18px; margin:4px 0 0; line-height:1.3; }
  .when { text-align:right; white-space:nowrap; color:var(--muted); font-size:11px;
    display:flex; flex-direction:column; gap:3px; }
  .dur { color:var(--accent); }
  .meta { display:flex; flex-wrap:wrap; gap:5px 14px; font-size:11px; color:var(--muted);
    border-top:1px solid var(--hair); border-bottom:1px solid var(--hair); padding:7px 0; }
  .meta .sid { color:#b9c0c8; cursor:pointer; }
  .meta .sid:hover { color:var(--accent); }
  .meta .c { color:var(--new); } .meta .m { color:var(--mod); }
  h4 { font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:var(--muted);
    margin:0 0 5px; font-weight:600; }
  p { margin:0; }
  .clamp { display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; overflow:hidden; }
  .clamp.open { -webkit-line-clamp:unset; }
  .more { background:none; border:0; color:var(--muted); font:inherit; font-size:11px;
    cursor:pointer; padding:3px 0; text-decoration:underline; }
  .more:hover { color:var(--accent); }
  details { border-top:1px solid var(--hair); padding-top:9px; }
  summary { cursor:pointer; color:var(--muted); font-size:11px; }
  summary:hover { color:var(--ink); }
  ul.files { margin:8px 0 0; padding:0; list-style:none; display:flex; flex-direction:column; gap:2px;
    font-size:11.5px; max-height:340px; overflow:auto; }
  ul.files li { display:flex; gap:8px; align-items:baseline; padding:2px 4px; border-radius:2px; cursor:copy; }
  ul.files li:hover { background:#2c313a; }
  ul.files li.hidden { display:none; }
  .op { flex:0 0 auto; font-size:9px; padding:0 5px; border:1px solid var(--hair); letter-spacing:.5px; }
  .op-new { color:var(--new); } .op-modify { color:var(--mod); }
  mark { background:#5a4a12; color:#ffe9a8; padding:0 1px; }
  .empty { color:var(--muted); font-size:12px; }
  .sumbox { border:1px solid var(--hair); border-left:2px solid var(--accent); background:#1d2127;
    padding:10px 12px; display:flex; flex-direction:column; gap:6px; }
  .sumhead { display:flex; align-items:center; justify-content:space-between; gap:10px; }
  .sumhead h4 { margin:0; }
  .srow { display:grid; grid-template-columns:112px minmax(0,1fr); gap:10px; font-size:12px; }
  .skey { color:var(--accent); font-size:10.5px; text-transform:uppercase; letter-spacing:1px; }
  .sval { color:var(--ink); overflow-wrap:anywhere; }
  .meta .s { color:var(--accent); }
  /* expanded summary browser */
  body.ov-open { overflow:hidden; }
  #overlay { position:fixed; inset:0; z-index:30; background:rgba(8,9,11,.86);
    display:flex; align-items:center; justify-content:center; padding:32px; }
  #overlay[hidden] { display:none; }
  .ov { background:var(--panel); border:1px solid var(--hair); width:min(1100px,100%);
    height:min(86vh,900px); display:flex; flex-direction:column; }
  .ov-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px;
    padding:14px 18px; border-bottom:1px solid var(--hair); }
  .ov-head h3 { margin:0; font-size:16px; }
  .ov-sub { color:var(--muted); font-size:11px; margin-top:3px; }
  .ov-nav { display:flex; gap:6px; flex:0 0 auto; }
  .ov-body { display:grid; grid-template-columns:320px minmax(0,1fr); min-height:0; flex:1; }
  .ov-list { margin:0; padding:6px; list-style:none; overflow:auto; border-right:1px solid var(--hair); }
  .ov-list li { display:grid; grid-template-columns:34px minmax(0,1fr); gap:8px; padding:7px 8px;
    cursor:pointer; border-left:2px solid transparent; }
  .ov-list li:hover { background:#262b33; }
  .ov-list li.sel { background:#2b313a; border-left-color:var(--accent); }
  .ov-num { color:var(--muted); font-size:11px; }
  .ov-snip { font-size:11.5px; color:var(--ink); overflow:hidden; display:-webkit-box;
    -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .ov-list time { grid-column:2; color:#6f757d; font-size:10.5px; }
  .ov-detail { padding:18px 20px; overflow:auto; display:flex; flex-direction:column; gap:12px; }
  .ov-detail .srow { grid-template-columns:130px minmax(0,1fr); font-size:13px; }
  .ov-detail .sumhead h4 { font-size:11px; }
  @media (max-width:820px){ .ov-body{grid-template-columns:1fr;} .ov-list{border-right:0;border-bottom:1px solid var(--hair);max-height:38%;} }
  footer { color:#6f757d; font-size:10.5px; }
  .note { margin-top:36px; border:1px solid var(--hair); padding:15px 17px; color:var(--muted); font-size:12px; }
  code { color:var(--ink); background:#2b3038; padding:1px 5px; }
  .toast { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); background:var(--ink);
    color:#14161a; padding:8px 14px; font-size:12px; border-radius:2px; opacity:0; pointer-events:none;
    transition:opacity .18s; z-index:20; }
  .toast.on { opacity:1; }
  @media (max-width:820px){ .layout{grid-template-columns:1fr;} aside{position:static;height:auto;} }
</style>
</head>
<body>
<div class="layout">
  <aside>
    <h1>__SUBTITLE__</h1>
    <div class="sub">__NW__ sessions · __COUNTS__</div>
    <input type="search" id="side-search" placeholder="filter index…" style="width:100%;margin-bottom:10px">
    <nav id="nav"></nav>
  </aside>
  <main>
    <div class="top">
      <h2>__TITLE__</h2>
      <p class="lede">__LEDE__</p>
    </div>
    <div class="controls">
      <input type="search" id="q" placeholder="search title, prompt, outcome, path…">
      <div class="chips" id="chips"></div>
      <select id="sort">
        <option value="time-asc">oldest first</option>
        <option value="time-desc">newest first</option>
        <option value="files-desc">most files</option>
        <option value="turns-desc">most turns</option>
      </select>
      <button class="btn" id="files-only" aria-pressed="false">has files</button>
      <button class="btn" id="expand-all">expand files</button>
      <button class="btn" id="sum-only" aria-pressed="false">has summary</button>
      <span class="count" id="count"></span>
    </div>
    <div id="cards"></div>
    <div class="note">__NOTE__</div>
  </main>
</div>
<div id="overlay" hidden>
  <div class="ov" role="dialog" aria-modal="true" aria-labelledby="ov-title">
    <div class="ov-head">
      <div><h3 id="ov-title"></h3><div class="ov-sub" id="ov-sub"></div></div>
      <div class="ov-nav">
        <button class="btn" id="ov-prev">‹ prev</button>
        <button class="btn" id="ov-next">next ›</button>
        <button class="btn" id="ov-close">close (esc)</button>
      </div>
    </div>
    <div class="ov-body">
      <ol class="ov-list" id="ov-list"></ol>
      <div class="ov-detail" id="ov-detail"></div>
    </div>
  </div>
</div>
<div class="toast" id="toast">copied</div>
<script>
const SESSIONS = __DATA__;
const FW = ["claude-code","pi","codex"].filter(f => SESSIONS.some(s => s.framework === f));
const state = { q:"", fw:new Set(FW), filesOnly:false, summariesOnly:false, sort:"time-asc", open:new Set(), expandAll:false };
const SUMFIELDS = [["this turn","This turn"],["session so far","Session so far"],["issues","Issues"],["next steps","Next steps"]];

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
const fmtDur = s => { s=Math.round(s||0); const h=Math.floor(s/3600), m=Math.floor(s%3600/60);
  return h ? `${h}h ${String(m).padStart(2,"0")}m` : `${m}m`; };
function highlight(text, q){
  const t = esc(text); if(!q) return t;
  try { return t.replace(new RegExp("("+q.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")","gi"),"<mark>$1</mark>"); }
  catch { return t; }
}
function matches(s, q){
  if(!q) return true;
  const needle=q.toLowerCase();
  const summaryText = (s.summaries||[]).map(x => Object.values(x.fields||{}).join(" ")+" "+(x.fallback||"")).join(" ");
  return (s.title+" "+s.task+" "+s.outcome+" "+s.model+" "+s.branch+" "+summaryText+" "+s.files.map(f=>f[0]).join(" "))
    .toLowerCase().includes(needle);
}
function visible(){
  const list = SESSIONS.filter(s => state.fw.has(s.framework) && matches(s, state.q)
    && (!state.filesOnly || s.files.length) && (!state.summariesOnly || s.summary_count));
  const by = { "time-asc":(a,b)=>a.started.localeCompare(b.started),
               "time-desc":(a,b)=>b.started.localeCompare(a.started),
               "files-desc":(a,b)=>b.files.length-a.files.length,
               "turns-desc":(a,b)=>b.turns-a.turns };
  return list.sort(by[state.sort]);
}
function renderNav(){
  const items = SESSIONS.filter(s => state.fw.has(s.framework) && matches(s, state.q))
    .sort((a,b)=>a.started.localeCompare(b.started));
  $("#nav").innerHTML = items.map(s =>
    `<a href="#${esc(s.id)}" data-fw="${esc(s.framework)}" data-id="${esc(s.id)}">
       <span class="dot"></span>${esc(s.title.slice(0,42))}</a>`).join("");
  $("#nav").querySelectorAll("a").forEach(a => a.addEventListener("click", e => {
    e.preventDefault();
    const el = document.getElementById(a.dataset.id);
    if(el){ el.scrollIntoView({block:"start"}); el.classList.add("hit");
      setTimeout(()=>el.classList.remove("hit"), 1200); }
  }));
}
function renderChips(){
  $("#chips").innerHTML = FW.map(f =>
    `<button class="chip" data-fw="${f}" aria-pressed="${state.fw.has(f)}">${f} ${SESSIONS.filter(s=>s.framework===f).length}</button>`
  ).join("");
  $("#chips").querySelectorAll("button").forEach(b => b.addEventListener("click", () => {
    const f=b.dataset.fw;
    state.fw.has(f) ? state.fw.delete(f) : state.fw.add(f);
    render();
  }));
}
function summaryFields(block, q){
  const rows = SUMFIELDS.filter(([k]) => block.fields && block.fields[k])
    .map(([k,label]) => `<div class="srow"><span class="skey">${label}</span><span class="sval">${highlight(block.fields[k],q)}</span></div>`)
    .join("");
  return rows || `<p>${highlight(block.fallback || "(empty summary)", q)}</p>`;
}
function latestSummary(s, q){
  if(!s.summary_count) return "";
  const last = s.summaries[s.summaries.length-1];
  const more = s.summary_count > 1 ? ` · ${s.summary_count} total` : "";
  const label = s.summary_count > 1 ? `browse all ${s.summary_count}` : "open summary";
  return `<div class="sumbox"><div class="sumhead"><h4>Latest summary${more}</h4>
    <button class="btn sum-open" data-id="${esc(s.id)}">${label} ▸</button></div>
    ${summaryFields(last, q)}</div>`;
}
function renderCards(){
  const list = visible();
  const q = state.q.toLowerCase();
  $("#cards").innerHTML = list.map(s => {
    const openFiles = state.expandAll || state.open.has(s.id);
    const hitFiles = q ? s.files.filter(f => f[0].toLowerCase().includes(q)) : s.files;
    const files = s.files.length ? `
      <details ${openFiles?"open":""} data-id="${esc(s.id)}">
        <summary>${s.files.length} file target(s)${q&&hitFiles.length!==s.files.length?` · ${hitFiles.length} match`:""}</summary>
        <ul class="files">${s.files.map(([p,op]) =>
          `<li data-path="${esc(p)}" class="${q && !p.toLowerCase().includes(q) ? "hidden":""}">
             <span class="op op-${op.toLowerCase()}">${esc(op)}</span><span>${highlight(p,q)}</span></li>`).join("")}</ul>
      </details>`
      : `<p class="empty">No structured file targets in this transcript.</p>`;
    return `
    <article class="card" id="${esc(s.id)}" data-fw="${esc(s.framework)}">
      <header>
        <div><div class="fw">${esc(s.framework)}</div><h3>${highlight(s.title,q)}</h3></div>
        <div class="when"><time>${esc(s.started.slice(0,16).replace("T"," "))} UTC</time>
          <span class="dur">${fmtDur(s.duration_s)}</span></div>
      </header>
      <div class="meta">
        <span class="sid" data-copy="${esc(s.id)}" title="copy session id">${esc(s.id)}</span>
        <span>${esc(s.model)}</span><span>${s.turns} turns</span><span>${s.tools} tool calls</span>
        <span class="c">${s.create} new</span><span class="m">${s.modify} modified</span>
        <span>${s.read} read</span><span>${s.execute} exec</span>
        ${s.summary_count?`<span class="s">${s.summary_count} summar${s.summary_count===1?"y":"ies"}</span>`:""}
      </div>
      <div><h4>Asked to</h4><p class="clamp">${highlight(s.task,q) || "<em>no substantive user turn recorded</em>"}</p>
        ${s.task.length>320?'<button class="more">show more</button>':""}</div>
      ${latestSummary(s,q)}
      ${s.outcome?`<div><h4>Final report (agent's claim)</h4><p class="clamp">${highlight(s.outcome,q)}</p>
        ${s.outcome.length>320?'<button class="more">show more</button>':""}</div>`:""}
      ${files}
      <footer>${esc(s.branch || "no branch recorded")}</footer>
    </article>`;
  }).join("") || '<p class="empty">Nothing matches those filters.</p>';

  $("#cards").querySelectorAll(".more").forEach(b => b.addEventListener("click", () => {
    const p=b.previousElementSibling; p.classList.toggle("open");
    b.textContent = p.classList.contains("open") ? "show less" : "show more";
  }));
  $("#cards").querySelectorAll(".files li").forEach(li => li.addEventListener("click", () => {
    const t = li.dataset.path;
    navigator.clipboard?.writeText(t).then(()=>toast("copied "+t)).catch(()=>toast(t));
  }));
  $("#cards").querySelectorAll(".sid").forEach(el => el.addEventListener("click", () => {
    navigator.clipboard?.writeText(el.dataset.copy).then(()=>toast("copied session id"));
  }));
  $("#cards").querySelectorAll("details").forEach(d => d.addEventListener("toggle", () => {
    d.open ? state.open.add(d.dataset.id) : state.open.delete(d.dataset.id);
  }));
  $("#cards").querySelectorAll(".sum-open").forEach(b => b.addEventListener("click", () => openOverlay(b.dataset.id)));
  const totalFiles = list.reduce((n,s)=>n+s.files.length,0);
  $("#count").textContent = `${list.length} of ${SESSIONS.length} sessions · ${totalFiles} files`;
}
let toastTimer;
function toast(msg){ const t=$("#toast"); t.textContent=msg; t.classList.add("on");
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>t.classList.remove("on"),1400); }

/* ---- expanded summary browser ---- */
let ovSession = null, ovIndex = 0;
function ovSelect(i){
  if(!ovSession) return;
  ovIndex = Math.max(0, Math.min(ovSession.summaries.length-1, i));
  $("#ov-list").querySelectorAll("li").forEach(li =>
    li.classList.toggle("sel", Number(li.dataset.i) === ovIndex));
  const block = ovSession.summaries[ovIndex];
  const when = block.at ? block.at.slice(0,19).replace("T"," ")+" UTC" : "turn "+(block.turn ?? "?");
  $("#ov-detail").innerHTML =
    `<div class="sumhead"><h4>Block ${ovIndex+1} of ${ovSession.summaries.length} · ${esc(when)}</h4></div>`
    + summaryFields(block, "");
  const sel = $("#ov-list").querySelector("li.sel");
  if(sel) sel.scrollIntoView({block:"nearest"});
}
function ovClose(){ $("#overlay").hidden = true; document.body.classList.remove("ov-open");
  ovSession = null; }
function openOverlay(id){
  const s = SESSIONS.find(x => x.id === id);
  if(!s || !s.summary_count) return;
  ovSession = s; ovIndex = s.summaries.length - 1;
  $("#ov-title").textContent = s.title;
  $("#ov-sub").textContent = `${s.summaries.length} summary block(s) · ${s.framework} · ${(s.started||"").slice(0,10)}`;
  $("#ov-list").innerHTML = s.summaries.map((b,i) => {
    const head = b.fields["this turn"] || b.fallback || "(empty summary)";
    const when = b.at ? b.at.slice(0,16).replace("T"," ") : `turn ${b.turn ?? "?"}`;
    return `<li data-i="${i}" class="${i===ovIndex?"sel":""}">
      <span class="ov-num">#${i+1}</span><span class="ov-snip">${esc(head)}</span>
      <time>${esc(when)}</time></li>`;
  }).join("");
  $("#ov-list").querySelectorAll("li").forEach(li =>
    li.addEventListener("click", () => ovSelect(Number(li.dataset.i))));
  ovSelect(ovIndex);
  $("#overlay").hidden = false; document.body.classList.add("ov-open");
  $("#ov-close").focus();
}
$("#ov-close").addEventListener("click", ovClose);
$("#ov-prev").addEventListener("click", () => ovSelect(ovIndex-1));
$("#ov-next").addEventListener("click", () => ovSelect(ovIndex+1));
$("#overlay").addEventListener("click", e => { if(e.target === $("#overlay")) ovClose(); });
function render(){ renderChips(); renderNav(); renderCards(); }

$("#q").addEventListener("input", e => { state.q=e.target.value.trim(); render(); });
$("#side-search").addEventListener("input", e => { $("#q").value=e.target.value; state.q=e.target.value.trim(); render(); });
$("#sort").addEventListener("change", e => { state.sort=e.target.value; render(); });
$("#files-only").addEventListener("click", e => {
  state.filesOnly=!state.filesOnly; e.target.setAttribute("aria-pressed",state.filesOnly); render(); });
$("#sum-only").addEventListener("click", e => {
  state.summariesOnly=!state.summariesOnly; e.target.setAttribute("aria-pressed",state.summariesOnly); render(); });
$("#expand-all").addEventListener("click", e => {
  state.expandAll=!state.expandAll; e.target.textContent=state.expandAll?"collapse files":"expand files"; render(); });
document.addEventListener("keydown", e => {
  if(!$("#overlay").hidden){
    if(e.key === "Escape"){ e.preventDefault(); ovClose(); }
    else if(e.key === "ArrowDown"){ e.preventDefault(); ovSelect(ovIndex+1); }
    else if(e.key === "ArrowUp"){ e.preventDefault(); ovSelect(ovIndex-1); }
    return;
  }
  if(e.key==="/" && !/input|select|textarea/i.test(document.activeElement.tagName)){ e.preventDefault(); $("#q").focus(); }
  else if(e.key==="Escape"){ state.q=""; $("#q").value=""; $("#side-search").value=""; render(); $("#q").blur(); }
});
render();
</script>
</body>
</html>'''


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
