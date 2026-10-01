#!/usr/bin/env python3
"""Tests for tools/validate-edgy-model.py, tools/edgy-eval.py, tools/render-core-links.py
and skills/architecture/edgy-assessment/scripts/edgy_model_to_txt.py."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
SAMPLE = REPO / "skills" / "architecture" / "edgy-deep-dive" / "examples" / "sample-model.json"
M2T = REPO / "skills" / "architecture" / "edgy-assessment" / "scripts" / "edgy_model_to_txt.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validator = load("validate_edgy_model", TOOLS / "validate-edgy-model.py")
renderer = load("render_core_links", TOOLS / "render-core-links.py")


def schema():
    return json.loads(validator.DEFAULT_SCHEMA.read_text(encoding="utf-8"))


def test_sample_model_is_valid():
    model = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert validator.validate_model(model, schema()) == []


def test_validator_survives_wrong_item_types():
    # review: [null] items used to raise AttributeError / TypeError
    for bad in (
        {"core_links": [None], "suggested_deep_dives": [None]},
        {"core_links": "x", "suggested_deep_dives": {"a": 1}, "elements": []},
        {"suggested_deep_dives": [{"pair": None}], "elements": None},
        [],
        None,
    ):
        findings = validator.validate_model(bad, schema())
        assert findings, f"invalid model must produce findings: {bad!r}"


def test_validator_cli_reports_instead_of_crashing():
    d = tempfile.mkdtemp()
    p = Path(d) / "bad.json"
    p.write_text(json.dumps({"company": "x", "assessed_at": "2026-01-01", "language": "fi", "elements": {},
                             "core_links": [None], "coherence": {}, "suggested_deep_dives": [None]}), encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOLS / "validate-edgy-model.py"), str(p)], capture_output=True, text=True)
    assert r.returncode == 1 and "Traceback" not in r.stderr, (r.stdout, r.stderr)


def test_eval_fails_on_lint_errors():
    # review: the eval parsed only the first line of the JSON report and never saw findings
    d = tempfile.mkdtemp()
    txt = Path(d) / "wrong-pair.txt"
    txt.write_text('facet: architecture\nelements:\n  - organisation: "Org"\n  - asset: "System"\n'
                   'relationships:\n  - "Org" -> "System": "has"\n', encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOLS / "edgy-eval.py"), "--json", str(txt)], capture_output=True, text=True)
    rows = json.loads(r.stdout)
    assert r.returncode == 1, r.stdout
    assert rows[0]["lint_errors"] >= 1 and rows[0]["rules"].get("E010"), rows


def test_eval_counts_only_edgy_elements():
    # review: the legend background was counted as an element
    r = subprocess.run([sys.executable, str(TOOLS / "edgy-eval.py"), "--json",
                        str(REPO / "skills/documentation/edgy-diagram/examples/full-edgy-map.txt")],
                       capture_output=True, text=True)
    rows = json.loads(r.stdout)
    assert rows[0]["elements"] == 12, rows


def test_render_core_links_rejects_unpaired_markers():
    # review summary: an unpaired begin/end marker was skipped silently
    ok = "x\n<!-- edgy-links:begin format=influence -->\nold\n<!-- edgy-links:end -->\n"
    assert renderer.check_markers("f", ok) == []
    assert renderer.check_markers("f", "<!-- edgy-links:begin format=influence -->\nno end\n")
    assert renderer.check_markers("f", "<!-- edgy-links:end -->\n<!-- edgy-links:begin format=influence -->\n")


def test_model_to_txt_fails_loudly_without_vocabulary():
    # review: a missing vocabulary module used to produce TXT files without relationships
    d = Path(tempfile.mkdtemp())
    script_dir = d / "a" / "b" / "c" / "scripts"     # DIAGRAM_SCRIPTS resolves to a non-existent path
    script_dir.mkdir(parents=True)
    shutil.copy(M2T, script_dir / "edgy_model_to_txt.py")
    env = dict(os.environ, PYTHONPATH="")
    r = subprocess.run([sys.executable, str(script_dir / "edgy_model_to_txt.py"), str(SAMPLE), "--out", str(d / "out")],
                       capture_output=True, text=True, env=env, cwd=str(d))
    assert r.returncode != 0 and "vocabulary" in (r.stderr + r.stdout), (r.returncode, r.stdout, r.stderr)
    assert not (d / "out").exists() or not list((d / "out").glob("*.txt")), "no TXT may be written without the vocabulary"


def test_model_to_txt_derives_relationships():
    d = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, str(M2T), str(SAMPLE), "--out", d, "--prefix", "s"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    text = (Path(d) / "s-all-facets.txt").read_text(encoding="utf-8")
    rels = [ln for ln in text.splitlines() if " -> " in ln]
    assert len(rels) >= 10, rels


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        print(f"Testing {t.__name__}...")
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} tool tests passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
