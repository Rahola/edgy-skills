#!/usr/bin/env python3
"""
edgy-eval.py — Generate and lint the EDGY eval set and print a metrics table.

Usage:
  python3 tools/edgy-eval.py                 # default inputs, markdown table
  python3 tools/edgy-eval.py --json          # machine-readable
  python3 tools/edgy-eval.py a.txt b.txt     # specific inputs

Exit 1 when any input produces generator errors or lint errors.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "documentation" / "edgy-diagram" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import edgy_lint  # noqa: E402 — element classification shared with the linter
EXAMPLES = REPO / "skills" / "documentation" / "edgy-diagram" / "examples"
DEFAULT_INPUTS = [
    EXAMPLES / "eval" / "large-capability-map.txt",
    EXAMPLES / "eval" / "large-reference-architecture.txt",
    EXAMPLES / "multipage-map.txt",
    EXAMPLES / "full-edgy-map.txt",
    EXAMPLES / "purpose-hierarchy-map.txt",
    EXAMPLES / "organisation-roles-map.txt",
    EXAMPLES / "transition-overlay.txt",
]


def run_one(txt: Path, out_dir: Path) -> dict:
    drawio = out_dir / (txt.stem + ".drawio")
    gen = subprocess.run([sys.executable, str(SCRIPTS / "edgy_generator.py"), str(txt), "--output", str(drawio)],
                         capture_output=True, text=True)
    gen_warnings = gen.stderr.count("Warning:")
    row = {"input": txt.name, "gen_exit": gen.returncode, "gen_warnings": gen_warnings,
           "elements": 0, "edges": 0, "pages": 0, "lint_errors": 0, "lint_warnings": 0, "rules": {}}
    if gen.returncode != 0:
        row["error"] = gen.stderr.strip()[-300:]
        return row
    import xml.etree.ElementTree as ET
    root = ET.parse(drawio).getroot()
    models = [root] if root.tag == "mxGraphModel" else [d.find("mxGraphModel") for d in root.findall("diagram")]
    row["pages"] = len(models)
    for m in models:
        cells = {c.get("id"): c for c in m.findall("./root/mxCell")}
        # Same classification as the linter: EDGY + base elements only — no legend
        # background, chips, containers, lanes or text cells.
        cls = edgy_lint.classify_cells(cells)
        row["elements"] += len(cls["elements"])
        row["edges"] += sum(1 for c in cells.values()
                            if c.get("edge") == "1" and c.get("source") in cls["elements"] and c.get("target") in cls["elements"])
    lint = subprocess.run([sys.executable, str(SCRIPTS / "edgy_lint.py"), "--json", str(drawio)], capture_output=True, text=True)
    try:
        findings = json.loads(lint.stdout)          # --json writes only the JSON array to stdout
    except json.JSONDecodeError as exc:
        # An unreadable report must fail the eval, never count as "no findings"
        row["error"] = f"edgy_lint --json output is not JSON ({exc}): {lint.stdout[:200]!r} {lint.stderr[-200:]!r}"
        row["lint_errors"] = 1
        return row
    if lint.returncode not in (0, 1):
        row["error"] = f"edgy_lint exited {lint.returncode}: {lint.stderr[-300:]}"
        row["lint_errors"] = max(row["lint_errors"], 1)
    rules = Counter(f["rule"] for f in findings)
    row["rules"] = dict(rules)
    row["lint_errors"] = sum(1 for f in findings if f["level"] == "ERROR")
    row["lint_warnings"] = sum(1 for f in findings if f["level"] == "WARNING")
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="EDGY eval set: generate, lint, report")
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keep", help="directory to keep generated files in")
    args = ap.parse_args(argv)
    inputs = [Path(p) for p in args.inputs] or DEFAULT_INPUTS
    out_dir = Path(args.keep) if args.keep else Path(tempfile.mkdtemp(prefix="edgy-eval-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [run_one(p, out_dir) for p in inputs]
    failed = [r for r in rows if r["gen_exit"] != 0 or r["lint_errors"] or r.get("error")]
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print("| Input | Pages | Elements | Edges | Generator warnings | Lint errors | Lint warnings | Rules |")
        print("|-------|------:|---------:|------:|-------------------:|------------:|--------------:|-------|")
        for r in rows:
            rules = ", ".join(f"{k}×{v}" for k, v in sorted(r["rules"].items())) or "—"
            status = " **GEN FAILED**" if r["gen_exit"] else ""
            print(f"| {r['input']}{status} | {r['pages']} | {r['elements']} | {r['edges']} | {r['gen_warnings']} | {r['lint_errors']} | {r['lint_warnings']} | {rules} |")
        print(f"\nedgy-eval: {len(rows)} inputs, {len(failed)} failing" + (f" (files kept in {out_dir})" if args.keep else ""))
        for r in failed:
            if r.get("error"):
                print(f"  {r['input']}: {r['error']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
