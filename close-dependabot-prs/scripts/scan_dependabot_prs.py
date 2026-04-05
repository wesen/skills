#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from dataclasses import dataclass
from typing import Iterable


DEPENDABOT_AUTHOR_LOGINS = {"app/dependabot", "dependabot[bot]"}
PASS_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
FAIL_CONCLUSIONS = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE"}
PENDING_STATUSES = {"QUEUED", "IN_PROGRESS", "REQUESTED", "PENDING"}


@dataclass(frozen=True)
class CheckRun:
    name: str
    workflow: str
    status: str
    conclusion: str
    url: str


@dataclass(frozen=True)
class CiSummary:
    overall: str
    total: int
    passing: int
    failing: int
    pending: int
    other: int
    checks: tuple[CheckRun, ...]

    def short_label(self) -> str:
        return f"{self.overall} S:{self.passing} F:{self.failing} P:{self.pending} O:{self.other}"


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    author: str
    merge_state: str
    mergeable: str
    head_ref: str
    title: str
    url: str
    ci: CiSummary
    ready: bool


def run_gh(args: list[str]) -> str:
    completed = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def load_json(args: list[str]) -> object:
    return json.loads(run_gh(args))


def summarize_checks(checks: list[CheckRun]) -> CiSummary:
    passing = failing = pending = other = 0
    for check in checks:
        conclusion = check.conclusion.upper()
        status = check.status.upper()
        if status in PENDING_STATUSES or not conclusion:
            pending += 1
        elif conclusion in PASS_CONCLUSIONS:
            passing += 1
        elif conclusion in FAIL_CONCLUSIONS:
            failing += 1
        else:
            other += 1

    if not checks:
        overall = "unknown"
    elif pending > 0:
        overall = "pending"
    elif failing > 0:
        overall = "failing"
    elif passing == len(checks):
        overall = "passing"
    else:
        overall = "unknown"

    return CiSummary(
        overall=overall,
        total=len(checks),
        passing=passing,
        failing=failing,
        pending=pending,
        other=other,
        checks=tuple(checks),
    )


def search_dependabot_prs(org: str, limit: int, ready_only: bool) -> Iterable[dict]:
    args = [
        "search",
        "prs",
        "--owner",
        org,
        "--state",
        "open",
        "--limit",
        str(limit),
        "--app",
        "dependabot",
        "--archived=false",
        "--json",
        "repository,number,title,url,author",
    ]
    if ready_only:
        args.extend(["--checks", "success"])

    try:
        payload = load_json(args)
    except subprocess.CalledProcessError as exc:
        print(f"error: unable to search Dependabot PRs in {org}: {exc.stderr.strip()}", file=sys.stderr)
        raise

    assert isinstance(payload, list)
    return payload


def fetch_pr_metadata(repo: str, number: int) -> tuple[str, str, str]:
    try:
        payload = load_json(
            [
                "pr",
                "view",
                "-R",
                repo,
                str(number),
                "--json",
                "mergeStateStatus,mergeable,headRefName",
            ]
        )
    except subprocess.CalledProcessError as exc:
        print(f"warning: unable to query PR metadata for {repo}#{number}: {exc.stderr.strip()}", file=sys.stderr)
        return ("UNKNOWN", "UNKNOWN", "")

    assert isinstance(payload, dict)
    merge_state = payload.get("mergeStateStatus")
    mergeable = payload.get("mergeable")
    head_ref = payload.get("headRefName")
    if not isinstance(merge_state, str):
        merge_state = "UNKNOWN"
    if not isinstance(mergeable, str):
        mergeable = "UNKNOWN"
    if not isinstance(head_ref, str):
        head_ref = ""
    return merge_state, mergeable, head_ref


def fetch_ci_summary(repo: str, number: int) -> CiSummary:
    try:
        payload = load_json(
            [
                "pr",
                "view",
                "-R",
                repo,
                str(number),
                "--json",
                "statusCheckRollup",
            ]
        )
    except subprocess.CalledProcessError as exc:
        print(f"warning: unable to query CI for {repo}#{number}: {exc.stderr.strip()}", file=sys.stderr)
        return CiSummary(overall="unknown", total=0, passing=0, failing=0, pending=0, other=0, checks=tuple())

    assert isinstance(payload, dict)
    rollup = payload.get("statusCheckRollup") or []
    checks: list[CheckRun] = []
    for item in rollup:
        name = item.get("name")
        workflow = item.get("workflowName") or ""
        status = item.get("status") or ""
        conclusion = item.get("conclusion") or ""
        url = item.get("detailsUrl") or ""
        if not isinstance(name, str) or not isinstance(workflow, str) or not isinstance(status, str):
            continue
        if not isinstance(conclusion, str) or not isinstance(url, str):
            continue
        checks.append(CheckRun(name=name, workflow=workflow, status=status, conclusion=conclusion, url=url))

    return summarize_checks(checks)


def list_dependabot_prs(org: str, pr_limit: int, ready_only: bool) -> list[PullRequest]:
    payload = search_dependabot_prs(org, pr_limit, ready_only)
    prs: list[PullRequest] = []

    for pr in payload:
        repository = pr.get("repository") or {}
        author = pr.get("author") or {}
        repo = repository.get("nameWithOwner")
        login = author.get("login")
        number = pr.get("number")
        title = pr.get("title")
        url = pr.get("url")

        if not isinstance(repo, str) or not isinstance(login, str):
            continue
        if login not in DEPENDABOT_AUTHOR_LOGINS:
            continue
        if not isinstance(number, int):
            continue
        if not isinstance(title, str) or not isinstance(url, str):
            continue

        merge_state, mergeable, head_ref = fetch_pr_metadata(repo, number)
        ci = fetch_ci_summary(repo, number)
        ready = mergeable == "MERGEABLE" and merge_state == "CLEAN" and ci.overall == "passing"
        prs.append(
            PullRequest(
                repo=repo,
                number=number,
                author=login,
                merge_state=merge_state,
                mergeable=mergeable,
                head_ref=head_ref,
                title=title,
                url=url,
                ci=ci,
                ready=ready,
            )
        )

    return prs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List open Dependabot pull requests across all repos in a GitHub organization."
    )
    parser.add_argument("org", nargs="?", default="go-go-golems", help="GitHub organization to scan")
    parser.add_argument("--pr-limit", type=int, default=1000, help="Maximum open PRs to request from GitHub")
    parser.add_argument(
        "--format",
        choices=("both", "table", "json"),
        default="both",
        help="Output format",
    )
    parser.add_argument(
        "--ready-only",
        action="store_true",
        help="Only include PRs that look ready to merge",
    )
    return parser.parse_args()


def render_table(records: list[PullRequest]) -> None:
    headers = ["repo", "pr", "author", "mergeable", "ci", "ready", "title"]

    widths = [
        min(max(len(headers[0]), *(len(record.repo) for record in records)), 30) if records else len(headers[0]),
        max(len(headers[1]), *(len(f"#{record.number}") for record in records)) if records else len(headers[1]),
        max(len(headers[2]), *(len(record.author) for record in records)) if records else len(headers[2]),
        max(len(headers[3]), *(len(record.mergeable) for record in records)) if records else len(headers[3]),
        max(len(headers[4]), *(len(record.ci.short_label()) for record in records)) if records else len(headers[4]),
        max(len(headers[5]), *(len(str(record.ready).lower()) for record in records)) if records else len(headers[5]),
        min(max(len(headers[6]), *(len(record.title) for record in records)), 96) if records else len(headers[6]),
    ]

    def clip(value: str, width: int) -> str:
        if len(value) <= width:
            return value
        if width <= 1:
            return value[:width]
        return value[: width - 1] + "…"

    def format_row(values: list[str]) -> str:
        return "  ".join(clip(value, width).ljust(width) for value, width in zip(values, widths))

    print(format_row(headers))
    print("  ".join("-" * width for width in widths))
    for record in records:
        print(
            format_row(
                [
                    record.repo,
                    f"#{record.number}",
                    record.author,
                    record.mergeable,
                    record.ci.short_label(),
                    str(record.ready).lower(),
                    record.title,
                ]
            )
        )


def render_json(records: list[PullRequest]) -> None:
    print(json.dumps([asdict(record) for record in records], indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()

    records = list_dependabot_prs(args.org, args.pr_limit, args.ready_only)
    records.sort(key=lambda record: (record.repo, record.number))

    if args.ready_only:
        records = [record for record in records if record.ready]

    if args.format in {"both", "table"}:
        render_table(records)
        if args.format == "both":
            print()

    if args.format in {"both", "json"}:
        render_json(records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
