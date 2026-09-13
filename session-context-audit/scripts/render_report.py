#!/usr/bin/env python3
"""Render a standalone session context audit from a strict JSON model."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

CATEGORIES = {"analysis", "engineering", "menial/support", "issue/churn"}


def text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def require_list(model: dict[str, Any], key: str) -> list[Any]:
    value = model.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def validate_items(items: list[Any], scope: str) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("purpose"), str):
            raise ValueError(f"{scope}[{index}] must contain string name and purpose")


def validate(model: dict[str, Any]) -> None:
    for key in ("title", "kicker", "subtitle"):
        if not isinstance(model.get(key), str):
            raise ValueError(f"{key} must be a string")
    for key in ("turns", "timeline", "knowledge", "file_groups", "change_groups", "api_groups", "state"):
        require_list(model, key)
    for index, turn in enumerate(model["turns"]):
        if not isinstance(turn, dict) or not isinstance(turn.get("number"), str) or not isinstance(turn.get("title"), str) or not isinstance(turn.get("bullets"), list):
            raise ValueError(f"turns[{index}] is invalid")
    for index, entry in enumerate(model["timeline"]):
        if not isinstance(entry, dict) or entry.get("category") not in CATEGORIES:
            raise ValueError(f"timeline[{index}] has invalid category")
        if not isinstance(entry.get("period"), str) or not isinstance(entry.get("title"), str) or not isinstance(entry.get("bullets"), list):
            raise ValueError(f"timeline[{index}] is invalid")
        advice = entry.get("advice", [])
        if not isinstance(advice, list):
            raise ValueError(f"timeline[{index}].advice must be a list")
        if entry["category"] == "issue/churn" and not advice:
            raise ValueError(f"timeline[{index}] issue/churn requires prevention advice")
    for group_key in ("file_groups", "change_groups", "api_groups"):
        for index, group in enumerate(model[group_key]):
            if not isinstance(group, dict) or not isinstance(group.get("title"), str) or not isinstance(group.get("items"), list):
                raise ValueError(f"{group_key}[{index}] is invalid")
            validate_items(group["items"], f"{group_key}[{index}].items")


def bullets(values: list[Any]) -> str:
    return "<ul>" + "".join(f"<li>{text(value)}</li>" for value in values) + "</ul>"


def grouped_section(title: str, groups: list[dict[str, Any]]) -> str:
    columns = []
    for group in groups:
        items = "".join(
            f"<li><code>{text(item['name'])}</code> — {text(item['purpose'])}</li>"
            for item in group["items"]
        )
        columns.append(f"<div class='column'><h3>{text(group['title'])}</h3><ul>{items}</ul></div>")
    return f"<section><h2>{text(title)}</h2><div class='grid'>{''.join(columns)}</div></section>"


def render(model: dict[str, Any]) -> str:
    validate(model)
    turns = "".join(
        f"<article class='row'><div class='period'>TURN {text(turn['number'])}</div>"
        f"<div class='body'><strong>{text(turn['title'])}</strong>{bullets(turn['bullets'])}</div></article>"
        for turn in model["turns"]
    )
    timeline_parts = []
    for entry in model["timeline"]:
        advice = entry.get("advice", [])
        advice_html = ""
        if advice:
            advice_html = "<div class='advice'><b>Prevention:</b>" + bullets(advice) + "</div>"
        timeline_parts.append(
            f"<article class='row'><div class='period'>{text(entry['period'])}</div><div class='body'>"
            f"<span class='badge'>{text(entry['category']).upper()}</span> "
            f"<strong>{text(entry['title'])}</strong>{bullets(entry['bullets'])}{advice_html}</div></article>"
        )
    knowledge = "".join(
        f"<p><span class='badge'>{text(item.get('label', 'FACT'))}</span> {text(item.get('text', ''))}</p>"
        for item in model["knowledge"]
    )
    style = """
:root{--paper:#eee9dc;--ink:#151515;--red:#ce382d;--blue:#274c77;--muted:#625f58}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}header{padding:42px max(24px,6vw) 28px;border-bottom:8px solid var(--ink);background:#faf6eb}h1{max-width:1100px;margin:0;font:900 clamp(36px,7vw,84px)/.9 Arial Black,Impact,sans-serif;letter-spacing:-.045em;text-transform:uppercase}.kicker{display:inline-block;background:var(--red);color:#fff;padding:6px 10px;margin-bottom:18px;font-weight:900}.subtitle{margin-top:22px;color:var(--muted)}main{max-width:1400px;margin:auto;padding:32px max(24px,6vw) 80px}section{border:3px solid var(--ink);margin-bottom:24px;background:#faf6eb}h2{margin:0;padding:12px 16px;background:var(--ink);color:#fff;font:900 24px/1 Arial,sans-serif;text-transform:uppercase}h3{margin:0 0 12px;color:var(--red);font:900 20px Arial,sans-serif;text-transform:uppercase}.row{display:grid;grid-template-columns:130px 1fr;border-top:2px solid var(--ink)}.row:first-of-type{border-top:0}.period{padding:16px 12px;background:var(--blue);color:#fff;font-weight:900}.body,.content,.column{padding:16px 20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.column{border-right:2px solid var(--ink)}.column:last-child{border-right:0}.badge{display:inline-block;border:2px solid var(--ink);padding:2px 6px;font-size:12px;font-weight:900}.advice{border-left:6px solid var(--red);padding-left:12px}ul{margin:8px 0;padding-left:22px}li{margin:5px 0}code{overflow-wrap:anywhere}@media(max-width:760px){.row{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.column{border-right:0;border-bottom:2px solid var(--ink)}}
"""
    sections = [
        f"<section><h2>Conversation turns</h2>{turns}</section>",
        f"<section><h2>Session timeline</h2>{''.join(timeline_parts)}</section>",
        f"<section><h2>Current classified knowledge</h2><div class='content'>{knowledge}</div></section>",
        grouped_section("Files inspected or analyzed", model["file_groups"]),
        grouped_section("Files edited or created", model["change_groups"]),
        grouped_section("API and package inventory", model["api_groups"]),
        f"<section><h2>Repository and report state</h2><div class='content'>{bullets(model['state'])}</div></section>",
    ]
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{text(model['title'])} — Context Audit</title><style>{style}</style></head><body>"
        f"<header><div class='kicker'>{text(model['kicker'])}</div><h1>{text(model['title'])}</h1>"
        f"<div class='subtitle'>{text(model['subtitle'])}</div></header><main>{''.join(sections)}</main></body></html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    model = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(model), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
