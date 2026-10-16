#!/usr/bin/env python3
"""Model format 1.9 migration contract (edgy-assessment 1.10.0).

1. Old input is accepted: every shipped 1.8 model gives byte-identical output
   from edgy_model_to_txt.py (default and triad), edgy_model_diff.py (TXT,
   report, JSON) and edgy_model_to_archimate.py — compared with fixtures
   written from the v2.3.0 scripts (tools/make-compat-fixtures.sh).
2. Old writers stay old: a model that uses a 1.9 structure without declaring
   schema_version 1.9 is rejected by the validator.
3. 1.9 is valid: organisation as an array, people, asset kinds and
   relationships[] between element ids; a dangling id is rejected.
"""

import copy
import filecmp
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tools" / "fixtures" / "compat-1.8"
sys.path.insert(0, str(REPO / "tools"))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("vem", REPO / "tools" / "validate-edgy-model.py")
vem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vem)
SCHEMA = json.loads(vem.DEFAULT_SCHEMA.read_text(encoding="utf-8"))
SAMPLE = REPO / "skills" / "architecture" / "edgy-deep-dive" / "examples" / "sample-model.json"


def test_shipped_18_models_give_byte_identical_output():
    with tempfile.TemporaryDirectory() as tmp:
        script = REPO / "tools" / "make-compat-fixtures.sh"
        # write the same outputs with the current scripts into a scratch copy of the fixture tree
        work = Path(tmp) / "repo"
        (work / "tools").mkdir(parents=True)
        text = script.read_text(encoding="utf-8").replace('OUT="$REPO/tools/fixtures/compat-1.8"', f'OUT="{tmp}/out"')
        (work / "run.sh").write_text(text.replace('REPO="$(cd "$(dirname "$0")/.." && pwd)"', f'REPO="{REPO}"'),
                                     encoding="utf-8")
        r = subprocess.run(["bash", str(work / "run.sh")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr + r.stdout
        cmp = filecmp.dircmp(FIX, Path(tmp) / "out")
        diffs = []

        def walk(c, prefix=""):
            diffs.extend(prefix + f for f in c.diff_files + c.left_only + c.right_only)
            for name, sub in c.subdirs.items():
                walk(sub, prefix + name + "/")
        walk(cmp)
        # filecmp's shallow compare can trust equal stat signatures — compare bytes explicitly
        for f in FIX.rglob("*"):
            if f.is_file():
                other = Path(tmp) / "out" / f.relative_to(FIX)
                if other.is_file() and other.read_bytes() != f.read_bytes():
                    diffs.append(str(f.relative_to(FIX)))
        assert not diffs, f"1.8 output changed: {sorted(set(diffs))}"


def _model():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_19_structures_need_schema_version_19():
    m = _model()
    m.pop("schema_version", None)
    m["elements"]["organisation"] = [m["elements"]["organisation"], {"name": "Partner", "description": "x"}]
    errs = vem.validate_model(m, SCHEMA)
    assert any("1.9 structures" in e and "organisation as an array" in e for e in errs), errs
    m["schema_version"] = "1.9"
    assert not vem.validate_model(m, SCHEMA), vem.validate_model(m, SCHEMA)


def test_19_relationships_people_and_kinds_validate():
    m = _model()
    m["schema_version"] = "1.9"
    m["elements"]["people"] = [{"name": "Ticket inspector", "description": "checks tickets", "id": "PEO-01"}]
    m["elements"]["asset"][0].update({"id": "AST-01", "kind": "application", "hosting": "saas", "time": "invest"})
    cap = m["elements"]["capability"][0]
    cap["id"] = "CAP-01"
    m["relationships"] = [
        {"source_id": "CAP-01", "target_id": "AST-01", "verb": "requires", "attributes": {"primary": True}},
        {"source_id": "PEO-01", "target_id": "AST-01", "verb": "interacts with"},
    ]
    assert not vem.validate_model(m, SCHEMA), vem.validate_model(m, SCHEMA)
    bad = copy.deepcopy(m)
    bad["relationships"].append({"source_id": "CAP-01", "target_id": "AST-99", "verb": "requires"})
    errs = vem.validate_model(bad, SCHEMA)
    assert any("AST-99" in e and "E015" in e for e in errs), errs
    bad = copy.deepcopy(m)
    bad["elements"]["asset"][0]["time"] = "keep"
    assert any("time" in e for e in vem.validate_model(bad, SCHEMA))
    old = copy.deepcopy(m)
    old["schema_version"] = "1.8"
    errs = vem.validate_model(old, SCHEMA)
    assert any("relationships[]" in e and "elements.people" in e and "asset" in e for e in errs), errs


def test_one_of_is_enforced():
    m = _model()
    m["schema_version"] = "1.9"
    m["elements"]["organisation"] = "Acme"            # neither an element nor an array of elements
    errs = vem.validate_model(m, SCHEMA)
    assert any("oneOf" in e for e in errs), errs


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} model compatibility tests passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
