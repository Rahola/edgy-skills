#!/usr/bin/env python3
"""Tests for edgy_model_diff.py — current + target model → transition map."""

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edgy_model_diff as md  # noqa: E402

EXAMPLES = HERE.parent / "examples" / "model-diff"
REPO = HERE.parent.parent.parent.parent
DIAGRAM = REPO / "skills" / "documentation" / "edgy-diagram"


def _models():
    return (json.loads((EXAMPLES / "current-model.json").read_text(encoding="utf-8")),
            json.loads((EXAMPLES / "target-model.json").read_text(encoding="utf-8")))


def _changes(result):
    return {(t, (tgt or cur)["name"]): change for t, pairs in result["elements"].items() for change, cur, tgt, _ in pairs}


def test_tags_match_the_hand_tagged_transition_example():
    """The pair is built from examples/transition-overlay.txt: every tag a comparison can know matches;
    replace (Legacy fare engine) and decide (Open-loop payment gateway) are judgements → remove / new."""
    cur, tgt = _models()
    ch = _changes(md.compare(cur, tgt, "architecture"))
    assert ch[("capability", "Ticketing")] == "keep"
    assert ch[("capability", "Account-based travel")] == "new"
    assert ch[("asset", "Account-based ticketing platform")] == "new"
    assert ch[("asset", "Card personalisation service")] == "remove"
    assert ch[("process", "Fare change")] == "change"
    assert ch[("organisation", "Platform team")] == "keep"
    assert ch[("product", "Acme app")] == "change"
    assert ch[("asset", "Legacy fare engine")] == "remove", "replace is a judgement the diff never makes"
    assert ch[("asset", "Open-loop payment gateway")] == "new", "decide is a judgement the diff never makes"


def test_renamed_by_id_and_by_similarity():
    cur, tgt = _models()
    tgt = copy.deepcopy(tgt)
    tgt["elements"]["capability"][0]["name"] = "Ticketing and validation"        # same id CAP-05
    tgt["elements"]["organisation"]["name"] = "Platform teams"                    # no id, similar name
    result = md.compare(cur, tgt, "architecture")
    details = {(t, (b or a)["name"]): (c, d) for t, pairs in result["elements"].items() for c, a, b, d in pairs}
    assert details[("capability", "Ticketing and validation")][0] == "change"
    assert 'renamed from "Ticketing"' in details[("capability", "Ticketing and validation")][1]
    assert details[("organisation", "Platform teams")][0] == "change"


def test_core_link_changes():
    cur, tgt = _models()
    links = {(s, t): c for c, (s, t), _v, _d in md.compare(cur, tgt, "all")["links"]}
    assert links[("product", "capability")] == "new" and links[("capability", "asset")] == "keep"
    tgt2 = copy.deepcopy(tgt)
    tgt2["core_links"] = [l for l in tgt2["core_links"] if l["source"] != "task"]
    tgt2["core_links"][0]["verb_en"] = "depends on"
    links = {(s, t): (c, d) for c, (s, t), _v, d in md.compare(cur, tgt2, "all")["links"]}
    assert links[("task", "channel")][0] == "remove"
    assert links[("capability", "asset")] == ("change", 'verb was "requires"')


def test_transition_txt_generates_clean():
    with tempfile.TemporaryDirectory() as d:
        out, rep = Path(d) / "t.txt", Path(d) / "t.md"
        r = subprocess.run([sys.executable, str(HERE / "edgy_model_diff.py"), str(EXAMPLES / "current-model.json"),
                            str(EXAMPLES / "target-model.json"), "--facet", "architecture", "--layout", "triad",
                            "--out", str(out), "--report", str(rep)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        txt = out.read_text(encoding="utf-8")
        assert "map_type: triad" in txt and "{id: AST-03, change: remove}" in txt
        assert '"Acme app" -> "Ticketing": "requires" {change: new}' in txt
        assert "| asset | Legacy fare engine | remove |" in rep.read_text(encoding="utf-8")
        assert txt == (EXAMPLES / "transition.txt").read_text(encoding="utf-8"), "shipped example is current"
        dr = Path(d) / "t.drawio"
        r = subprocess.run([sys.executable, str(DIAGRAM / "scripts" / "edgy_generator.py"), str(out), "--output", str(dr)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        r = subprocess.run([sys.executable, str(DIAGRAM / "scripts" / "edgy_lint.py"), "--warnings-as-errors", str(dr)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout


def test_generated_ids_do_not_collide():
    cur, tgt = _models()
    txt = md.to_txt(md.compare(cur, tgt, "all"), cur, tgt)
    assert "{id: PRD-01" in txt and txt.count("PRO-01") == 1, "process keeps PRO-01, a product without id gets PRD-"



def _el(name, **kw):
    return {"name": name, "description": "", **kw}


def test_flagged_primary_is_written_and_linked_in_triad():
    """Review of PR #6, finding 1: a primary that is not first in its list must keep its links in triad."""
    cur, tgt = _models()
    tgt = copy.deepcopy(tgt)
    tgt["elements"]["capability"] = [_el("First", id="CAP-90"), _el("Main", id="CAP-91", primary=True)]
    tgt["elements"]["asset"] = [_el("Platform", id="AST-90")]
    txt = md.to_txt(md.compare(cur, tgt, "architecture"), cur, tgt, "triad")
    assert '- capability: "Main" {id: CAP-91, change: new, primary: true}' in txt, txt
    flagged = [l.split(":")[0].strip() for l in txt.splitlines() if "primary: true" in l]
    assert len(flagged) == len(set(flagged)), "one primary per type"
    assert '"Main" -> "Platform": "requires"' in txt
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.txt"
        path.write_text(txt, encoding="utf-8")
        r = subprocess.run([sys.executable, str(DIAGRAM / "scripts" / "edgy_generator.py"), str(path),
                            "--output", str(Path(d) / "t.drawio")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert "not drawn" not in r.stderr, r.stderr


def test_different_ids_never_pair_by_name():
    """Finding 2: explicit, different ids are two elements, even with the same or a similar name."""
    cur, tgt = _models()
    cur, tgt = copy.deepcopy(cur), copy.deepcopy(tgt)
    cur["elements"]["capability"] = [_el("Ticket sales", id="OLD")]
    tgt["elements"]["capability"] = [_el("Ticket rules", id="NEW")]
    ch = _changes(md.compare(cur, tgt, "architecture"))
    assert ch[("capability", "Ticket sales")] == "remove" and ch[("capability", "Ticket rules")] == "new", ch
    cur["elements"]["capability"] = [_el("Ticketing", id="OLD")]
    tgt["elements"]["capability"] = [_el("Ticketing", id="NEW")]
    pairs = md.compare(cur, tgt, "architecture")["elements"]["capability"]
    assert sorted(c for c, *_ in pairs) == ["new", "remove"], pairs
    # without ids the similar names still pair (documented behaviour)
    cur["elements"]["capability"] = [_el("Ticket sales")]
    tgt["elements"]["capability"] = [_el("Ticket rules")]
    assert _changes(md.compare(cur, tgt, "architecture"))[("capability", "Ticket rules")] == "change"


def test_removed_link_keeps_its_current_endpoints():
    """Finding 3: a removed core link is drawn between the current state's primaries."""
    cur, tgt = _models()
    cur, tgt = copy.deepcopy(cur), copy.deepcopy(tgt)
    cur["elements"]["capability"] = [_el("Old primary", id="CAP-1", primary=True), _el("Other", id="CAP-2")]
    tgt["elements"]["capability"] = [_el("Old primary", id="CAP-1"), _el("Other", id="CAP-2", primary=True)]
    cur["elements"]["asset"] = [_el("Platform", id="AST-1")]
    tgt["elements"]["asset"] = [_el("Platform", id="AST-1")]
    tgt["core_links"] = [l for l in tgt["core_links"] if (l["source"], l["target"]) != ("capability", "asset")]
    txt = md.to_txt(md.compare(cur, tgt, "architecture"), cur, tgt)
    assert '"Old primary" -> "Platform": "requires" {change: remove}' in txt, txt
    assert '"Other" -> "Platform"' not in txt
    assert '"Fare change" -> "Other": "realises" {change: keep}' in txt, "kept links use the target's primary"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f'Testing {t.__name__}...')
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} model diff tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'\nTest failed: {e}')
        sys.exit(1)
