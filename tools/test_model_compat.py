#!/usr/bin/env python3
"""Model format migration contracts: 1.9 (edgy-assessment 1.10.0) and 1.10 (edgy-assessment 1.11.0).

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


def _regenerate_and_compare(script_name, fixture_dir, label):
    """Run a fixture script with the current scripts into a scratch dir and compare bytes with the fixtures."""
    with tempfile.TemporaryDirectory() as tmp:
        script = REPO / "tools" / script_name
        work = Path(tmp) / "repo"
        (work / "tools").mkdir(parents=True)
        text = script.read_text(encoding="utf-8").replace(f'OUT="$REPO/tools/fixtures/{fixture_dir.name}"', f'OUT="{tmp}/out"')
        (work / "run.sh").write_text(text.replace('REPO="$(cd "$(dirname "$0")/.." && pwd)"', f'REPO="{REPO}"'),
                                     encoding="utf-8")
        r = subprocess.run(["bash", str(work / "run.sh")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr + r.stdout
        cmp = filecmp.dircmp(fixture_dir, Path(tmp) / "out")
        diffs = []

        def walk(c, prefix=""):
            diffs.extend(prefix + f for f in c.diff_files + c.left_only + c.right_only)
            for name, sub in c.subdirs.items():
                walk(sub, prefix + name + "/")
        walk(cmp)
        # filecmp's shallow compare can trust equal stat signatures — compare bytes explicitly
        for f in fixture_dir.rglob("*"):
            if f.is_file():
                other = Path(tmp) / "out" / f.relative_to(fixture_dir)
                if other.is_file() and other.read_bytes() != f.read_bytes():
                    diffs.append(str(f.relative_to(fixture_dir)))
        assert not diffs, f"{label} output changed: {sorted(set(diffs))}"


def test_shipped_18_models_give_byte_identical_output():
    _regenerate_and_compare("make-compat-fixtures.sh", FIX, "1.8")


def test_19_models_give_byte_identical_output():
    """Model format 1.10 (edgy-assessment 1.11.0): 1.9 input gives the v2.4.0 output, byte for byte — the shipped
    model, a single journey with an id and relationships to it, and a 200-character element id."""
    _regenerate_and_compare("make-compat-fixtures-19.sh", REPO / "tools" / "fixtures" / "compat-1.9", "1.9")


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


def _model_19():
    return json.loads((REPO / "skills" / "architecture" / "edgy-assessment" / "examples" / "architecture-model.json")
                      .read_text(encoding="utf-8"))


def test_110_journeys_and_gaps_validate():
    """M01: journeys as an array with ids and gaps on chain types validate as 1.10."""
    m = _model_19()
    m["schema_version"] = "1.10"
    j = m["elements"]["journey"]
    m["elements"]["journey"] = [dict(j, id="JRN-01"), {"name": "Inspect a ticket", "description": "", "id": "JRN-02"}]
    m["elements"]["task"][0]["gaps"] = {"products": "unknown"}
    m["elements"]["product"][0]["gaps"] = {"capabilities": "out_of_scope", "organisation": "not_investigated"}
    assert not vem.validate_model(m, SCHEMA), vem.validate_model(m, SCHEMA)


def test_110_gate():
    """M02: a single journey with an id stays 1.9; a journey array or chain gaps in a 1.9 model are rejected."""
    m = json.loads((REPO / "tools" / "fixtures" / "models-1.9" / "journey-with-id.json").read_text(encoding="utf-8"))
    assert m["schema_version"] == "1.9" and not vem.validate_model(m, SCHEMA), vem.validate_model(m, SCHEMA)
    arr = copy.deepcopy(m)
    arr["elements"]["journey"] = [arr["elements"]["journey"]]
    errs = vem.validate_model(arr, SCHEMA)
    assert any("1.10 structures" in e and "journey as an array" in e for e in errs), errs
    gaps = copy.deepcopy(m)
    gaps["elements"]["task"][0]["gaps"] = {"products": "unknown"}
    errs = vem.validate_model(gaps, SCHEMA)
    assert any("1.10 structures" in e and "gaps on task" in e for e in errs), errs
    org = copy.deepcopy(m)
    org["elements"]["capability"][0]["gaps"] = {"organisation": "unknown"}
    errs = vem.validate_model(org, SCHEMA)
    assert any("capability gaps.organisation" in e for e in errs), errs


def test_110_gap_keys_per_type():
    """M04: every allowed key validates on its type; another type's key is the additionalProperties error at its
    pointer; the capability keeps its W127 keys."""
    allowed = vem.GAP_KEYS
    assert allowed["capability"][:5] == ("actors", "processes", "resources", "data", "products")
    for t, keys in allowed.items():
        for k in keys:
            m = _model_19()
            m["schema_version"] = "1.10"
            items = m["elements"][t] if t != "journey" else None
            target = items[0] if items else m["elements"]["journey"]
            target["gaps"] = {k: "out_of_scope"}
            errs = vem.validate_model(m, SCHEMA)
            assert not errs, (t, k, errs)
    m = _model_19()
    m["schema_version"] = "1.10"
    m["elements"]["capability"][0]["gaps"] = {"tasks": "unknown"}
    errs = vem.validate_model(m, SCHEMA)
    assert any(e.startswith("/elements/capability/0/gaps/tasks: additionalProperties") for e in errs), errs
    m["elements"]["capability"][0]["gaps"] = {}
    m["elements"]["organisation"][0]["gaps"] = {"organisation": "unknown"}
    errs = vem.validate_model(m, SCHEMA)
    assert any("/elements/organisation/0/gaps/organisation: additionalProperties" in e for e in errs), errs
    m["elements"]["organisation"][0].pop("gaps")
    m["elements"]["task"][0]["gaps"] = {"products": "maybe"}
    errs = vem.validate_model(m, SCHEMA)
    assert any("gaps/products" in e and "maybe" in e for e in errs), errs


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
