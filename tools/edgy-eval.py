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
import edgy_qa  # noqa: E402 — the approval rule of the manifest gate
EXAMPLES = REPO / "skills" / "documentation" / "edgy-diagram" / "examples"
DEFAULT_INPUTS = [
    EXAMPLES / "eval" / "large-capability-map.txt",
    EXAMPLES / "eval" / "large-reference-architecture.txt",
    EXAMPLES / "eval" / "large-architecture-facet.txt",
    EXAMPLES / "eval" / "fixture-f1-ports-waypoints.txt",
    EXAMPLES / "eval" / "fixture-f2-labels.txt",
    EXAMPLES / "eval" / "fixture-f4-long-bold-title.txt",
    EXAMPLES / "eval" / "fixture-f5-purpose-tree.txt",
    EXAMPLES / "eval" / "series-acme-capability.txt",
    EXAMPLES / "eval" / "series-acme-task.txt",
    EXAMPLES / "eval" / "series-acme-purpose.txt",
    EXAMPLES / "multipage-map.txt",
    EXAMPLES / "full-edgy-map.txt",
    EXAMPLES / "purpose-hierarchy-map.txt",
    EXAMPLES / "organisation-roles-map.txt",
    EXAMPLES / "transition-overlay.txt",
]


def run_one(txt: Path, out_dir: Path) -> dict:
    """Generate with --qa and read the qa.json manifest the generator wrote — the
    same numbers the assessment Phase 5 and a reviewer see; nothing is re-parsed here."""
    drawio = out_dir / (txt.stem + ".drawio")
    gen = subprocess.run([sys.executable, str(SCRIPTS / "edgy_generator.py"), str(txt), "--output", str(drawio), "--qa"],
                         capture_output=True, text=True)
    gen_warnings = gen.stderr.count("Warning:")
    row = {"input": txt.name, "gen_exit": gen.returncode, "gen_warnings": gen_warnings,
           "elements": 0, "edges": 0, "pages": 0, "ratio": 0.0,
           "lint_errors": 0, "lint_warnings": 0, "visual": 0, "layout": 0, "rules": {}}
    if gen.returncode != 0:
        row["error"] = gen.stderr.strip()[-300:]
        return row
    qa_path = out_dir / (txt.stem + ".qa.json")
    try:
        manifest = json.loads(qa_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # A missing or unreadable manifest must fail the eval, never count as "no findings"
        row["error"] = f"qa.json missing or not JSON ({exc})"
        row["lint_errors"] = 1
        return row
    pages = manifest["pages"]
    row["pages"] = len(pages)
    row["ratio"] = max((pg["page"]["ratio"] for pg in pages), default=0.0)   # page height / width, worst page
    rules = Counter()
    for pg in pages:
        rules.update(pg["lint"]["rules"])
    t = manifest["totals"]
    row.update({"elements": t["elements"], "edges": t["edges"], "lint_errors": t["lint_errors"],
                "lint_warnings": t["lint_warnings"], "visual": t["visual"], "layout": t["layout_quality"],
                "rules": dict(rules),
                "approved": edgy_qa.is_approval(manifest.get("visual_approval")) and edgy_qa.is_approval(manifest.get("semantic_approval"))})
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
        print("| Input | Pages | Elements | Edges | H/W | Generator warnings | Lint errors | Lint warnings | Visual | Layout | Rules |")
        print("|-------|------:|---------:|------:|----:|-------------------:|------------:|--------------:|-------:|-------:|-------|")
        for r in rows:
            rules = ", ".join(f"{k}×{v}" for k, v in sorted(r["rules"].items())) or "—"
            status = " **GEN FAILED**" if r["gen_exit"] else ""
            print(f"| {r['input']}{status} | {r['pages']} | {r['elements']} | {r['edges']} | {r['ratio']:.2f} | "
                  f"{r['gen_warnings']} | {r['lint_errors']} | {r['lint_warnings']} | {r['visual']} | {r['layout']} | {rules} |")
        print(f"\nedgy-eval: {len(rows)} inputs, {len(failed)} failing" + (f" (files kept in {out_dir})" if args.keep else ""))
        for r in failed:
            if r.get("error"):
                print(f"  {r['input']}: {r['error']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
