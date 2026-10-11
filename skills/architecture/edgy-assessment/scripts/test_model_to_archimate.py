#!/usr/bin/env python3
"""Tests for edgy_model_to_archimate.py — structural checks of the Open Exchange file
(namespace, element types, identifiers, references, child order). The official XSD is
not bundled; the checks follow its structure (archimate3_Model.xsd / _View.xsd)."""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edgy_model_to_archimate as ma  # noqa: E402

REPO = HERE.parent.parent.parent.parent
MODELS = [HERE.parent / "examples" / "model-diff" / "target-model.json",
          REPO / "skills" / "architecture" / "edgy-deep-dive" / "examples" / "sample-model.json"]
NS = "{http://www.opengroup.org/xsd/archimate/3.0/}"
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"
MODEL_ORDER = ["name", "documentation", "properties", "metadata", "elements", "relationships", "organizations",
               "propertyDefinitions", "views"]


def _export(path, **kw):
    model = json.loads(path.read_text(encoding="utf-8"))
    return model, ET.fromstring(ma.export(model, **kw))


def test_structure_and_references():
    for path in MODELS:
        model, root = _export(path)
        assert root.tag == f"{NS}model"
        order = [c.tag.replace(NS, "") for c in root]
        assert order == sorted(order, key=MODEL_ORDER.index), order
        ids = [e.get("identifier") for e in root.iter() if e.get("identifier")]
        assert len(ids) == len(set(ids)), "identifiers are unique"
        elements = {e.get("identifier"): e for e in root.iter(f"{NS}element")}
        assert all(e.get(XSI_TYPE) in ma.ARCHIMATE_ELEMENT_TYPES for e in elements.values())
        assert all(e[0].tag == f"{NS}name" for e in elements.values()), "name first"
        pdefs = {p.get("identifier") for p in root.iter(f"{NS}propertyDefinition")}
        assert all(p.get("propertyDefinitionRef") in pdefs for p in root.iter(f"{NS}property"))
        rels = {r.get("identifier"): r for r in root.iter(f"{NS}relationship")}
        assert rels and all(r.get("source") in elements and r.get("target") in elements for r in rels.values())
        assert all(r.get(XSI_TYPE) == "Association" and r.get("isDirected") == "true" for r in rels.values())
        views = list(root.iter(f"{NS}view"))
        assert [v.find(f"{NS}name").text for v in views] == ["Identity", "Architecture", "Experience", "All facets"]
        for v in views:
            nodes = {n.get("identifier"): n for n in v.iter(f"{NS}node")}
            assert all(n.get("elementRef") in elements and int(n.get("w")) > 0 for n in nodes.values())
            for c in v.iter(f"{NS}connection"):
                assert c.get("relationshipRef") in rels and c.get("source") in nodes and c.get("target") in nodes


def test_every_model_element_round_trips_with_its_type():
    model, root = _export(MODELS[0])
    exported = {}
    for e in root.iter(f"{NS}element"):
        props = {p.get("propertyDefinitionRef"): p.find(f"{NS}value").text for p in e.iter(f"{NS}property")}
        exported[(props["pd-1"], e.find(f"{NS}name").text)] = e.get(XSI_TYPE)
    expected = {(t, el["name"]) for t, _i, el in ma.collect(model)}
    assert set(exported) == expected
    assert exported[("capability", "Ticketing")] == "Capability"
    assert exported[("channel", "Mobile app")] == "BusinessInterface"
    assert exported[("task", "Buy a ticket")] == "BusinessProcess"


def test_views_follow_the_diagram_layout():
    model, root = _export(MODELS[0])
    view = next(v for v in root.iter(f"{NS}view") if v.find(f"{NS}name").text == "Architecture")
    pos = ma.view_positions(model, "architecture", "en")
    elements = {e.get("identifier"): e.find(f"{NS}name").text for e in root.iter(f"{NS}element")}
    node = next(n for n in view.iter(f"{NS}node") if elements[n.get("elementRef")] == "Ticketing")
    assert (int(node.get("x")), int(node.get("y"))) == pos[("capability", "ticketing")][:2]


def test_no_views_option_and_language():
    _model, root = _export(MODELS[0], views=False, lang="fi")
    assert root.find(f"{NS}views") is None
    assert root.find(f"{NS}name").get("{http://www.w3.org/XML/1998/namespace}lang") == "fi"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f'Testing {t.__name__}...')
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} ArchiMate export tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'\nTest failed: {e}')
        sys.exit(1)
