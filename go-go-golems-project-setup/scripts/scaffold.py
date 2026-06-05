#!/usr/bin/env python3

import argparse
import re
import shutil
from pathlib import Path


def _replace_placeholders(content: str, mapping: dict[str, str]) -> str:
    out = content
    for k, v in mapping.items():
        out = out.replace(k, v)
    return out


def _should_treat_as_text(path: Path) -> bool:
    # Template set should be all text, but keep a conservative guard.
    # If a file contains NUL bytes, treat as binary.
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return b"\x00" not in data


def _go_package_name(value: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_]", "_", value.strip())
    candidate = re.sub(r"_+", "_", candidate).strip("_")
    if not candidate:
        return "project"
    if candidate[0].isdigit():
        candidate = f"project_{candidate}"
    return candidate


def _copy_tree(
    src_root: Path,
    dst_root: Path,
    mapping: dict[str, str],
    force: bool,
    ignore_names: set[str] | None = None,
) -> None:
    ignore_names = ignore_names or set()
    for src in src_root.rglob("*"):
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        if src.name in ignore_names:
            continue
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue

        if dst.exists() and not force:
            raise RuntimeError(f"Refusing to overwrite existing file: {dst}")

        dst.parent.mkdir(parents=True, exist_ok=True)

        if _should_treat_as_text(src):
            text = src.read_text(encoding="utf-8")
            text = _replace_placeholders(text, mapping)
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold standard go-go-golems Go project files into the current repository."
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Go module path (e.g. github.com/go-go-golems/mytool)",
    )
    parser.add_argument(
        "--binary",
        required=True,
        help="CLI binary name (e.g. mytool)",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="GoReleaser project_name (usually same as repo/binary)",
    )
    parser.add_argument(
        "--description",
        default="",
        help="One-line description for README/GoReleaser templates",
    )
    parser.add_argument(
        "--repo-owner",
        default="",
        help="GitHub owner for the main repo (defaults to owner parsed from --module)",
    )
    parser.add_argument(
        "--repo-name",
        default="",
        help="GitHub repo name (defaults to repo parsed from --module)",
    )
    parser.add_argument(
        "--tap-owner",
        default="go-go-golems",
        help="Homebrew tap GitHub owner (default: go-go-golems)",
    )
    parser.add_argument(
        "--tap-repo",
        default="homebrew-go-go-go",
        help="Homebrew tap repository name (default: homebrew-go-go-go)",
    )
    parser.add_argument(
        "--brew-tap",
        default="go-go-golems/go-go-go",
        help="Homebrew tap name for README (default: go-go-golems/go-go-go)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )

    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    src_root = skill_root / "assets" / "scaffold"
    if not src_root.exists():
        raise RuntimeError(f"Missing scaffold assets at {src_root}")

    dst_root = Path.cwd()

    # Try to parse owner/repo from module like github.com/<owner>/<repo>
    repo_owner = args.repo_owner
    repo_name = args.repo_name
    if not repo_owner or not repo_name:
        parts = args.module.split("/")
        if len(parts) >= 3 and parts[0] == "github.com":
            repo_owner = repo_owner or parts[1]
            repo_name = repo_name or parts[2]
        elif len(parts) >= 2:
            repo_owner = repo_owner or parts[0]
            repo_name = repo_name or parts[1]

    mapping = {
        "__MODULE__": args.module,
        "__BINARY__": args.binary,
        "__PROJECT_NAME__": args.project_name,
        "__DESCRIPTION__": args.description or "A go-go-golems tool",
        "__REPO_OWNER__": repo_owner or args.tap_owner,
        "__REPO_NAME__": repo_name or args.project_name,
        "__ORG__": repo_owner or args.tap_owner,
        "__TAP_OWNER__": args.tap_owner,
        "__TAP_REPO__": args.tap_repo,
        "__BREW_TAP__": args.brew_tap,
        "__GO_PACKAGE_NAME__": _go_package_name(repo_name or args.project_name or args.binary),
    }

    readme_template = src_root / "README.md.template"
    if not readme_template.exists():
        raise RuntimeError("Missing README.md.template in scaffold assets")

    _copy_tree(src_root, dst_root, mapping, force=args.force, ignore_names={"README.md.template"})

    # Write README.md from template
    readme = _replace_placeholders(readme_template.read_text(encoding="utf-8"), mapping)
    out_path = dst_root / "README.md"
    if out_path.exists() and not args.force:
        raise RuntimeError(f"Refusing to overwrite existing file: {out_path} (use --force)")
    out_path.write_text(readme, encoding="utf-8")

    print("Scaffold applied.")
    print("Next:")
    print("- run: go mod tidy")
    print("- run: make lint && go test ./... -count=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
