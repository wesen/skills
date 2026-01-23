#!/usr/bin/env python3
import argparse
import os
import posixpath
import re
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str], *, capture: bool = False) -> str:
    if capture:
        proc = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE)
        return proc.stdout
    subprocess.run(cmd, check=True)
    return ""


def list_rmdocs(out_dir: Path) -> set[Path]:
    return {p for p in out_dir.glob("*.rmdoc") if p.is_file()}


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required tool: {name}")


def parse_schema(inspect_output: str) -> str:
    m = re.search(r"\bschema=([^\s]+)\b", inspect_output)
    if not m:
        return ""
    return m.group(1).strip()


def parse_pdf_pages(pdfinfo_output: str) -> int:
    for line in pdfinfo_output.splitlines():
        if line.startswith("Pages:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1])
    raise ValueError("Unable to parse page count from pdfinfo output")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a reMarkable cloud document as .rmdoc, render annotated PDF, and optionally extract the last N pages."
    )
    parser.add_argument("--remote-path", required=True, help="Remote path (e.g. /Journals/#001 - 2025-12 - 2026-01-19)")
    parser.add_argument("--out-dir", required=True, help="Local output directory for .rmdoc and PDFs")
    parser.add_argument("--extract-last", type=int, default=0, help="If set, write an additional PDF containing the last N pages")
    parser.add_argument("--force", action="store_true", help="Overwrite output PDFs if they already exist")
    parser.add_argument("--interactive", action="store_true", help="Allow remarquee to prompt for cloud auth if needed")
    args = parser.parse_args()

    out_dir = Path(os.path.expanduser(args.out_dir)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    require_tool("remarquee")

    before = list_rmdocs(out_dir)
    cloud_get = ["remarquee", "cloud", "get", args.remote_path, "--out-dir", str(out_dir)]
    if not args.interactive:
        cloud_get.append("--non-interactive")
    run(cloud_get)
    after = list_rmdocs(out_dir)

    created = sorted(after - before)
    remote_basename = posixpath.basename(args.remote_path.rstrip("/"))
    expected = out_dir / f"{remote_basename}.rmdoc"

    if expected.exists():
        rmdoc_path = expected
    elif len(created) == 1:
        rmdoc_path = created[0]
    elif len(created) > 1:
        raise SystemExit(f"Multiple .rmdoc files created in {out_dir}; please re-run with an empty out-dir. New files: {created}")
    else:
        candidates = sorted(out_dir.glob("*.rmdoc"))
        if len(candidates) == 1:
            rmdoc_path = candidates[0]
        else:
            raise SystemExit(f"Unable to determine downloaded .rmdoc in {out_dir}. Candidates: {candidates}")

    inspect_out = run(["remarquee", "rmdoc", "inspect", str(rmdoc_path)], capture=True)
    schema = parse_schema(inspect_out)

    pdf_out = out_dir / f"{rmdoc_path.stem}-annotated.pdf"
    render_cmd = ["remarquee", "rmdoc"]
    if schema == "cPages":
        render_cmd += ["render-v6", str(rmdoc_path)]
    else:
        render_cmd += ["render-legacy", str(rmdoc_path)]
    render_cmd += ["--out", str(pdf_out)]
    if args.force:
        render_cmd.append("--force")
    run(render_cmd)

    print(f"pdf={pdf_out}")

    if args.extract_last and args.extract_last > 0:
        require_tool("pdfinfo")
        require_tool("qpdf")
        pages = parse_pdf_pages(run(["pdfinfo", str(pdf_out)], capture=True))
        n = args.extract_last
        if n > pages:
            raise SystemExit(f"--extract-last {n} exceeds total pages ({pages})")
        start = pages - n + 1
        last_pdf = out_dir / f"{rmdoc_path.stem}-last-{n}-pages.pdf"
        qpdf_cmd = [
            "qpdf",
            "--empty",
            "--pages",
            str(pdf_out),
            f"{start}-{pages}",
            "--",
            str(last_pdf),
        ]
        run(qpdf_cmd)
        print(f"last_pdf={last_pdf}")


if __name__ == "__main__":
    main()
