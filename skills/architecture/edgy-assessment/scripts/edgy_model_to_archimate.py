#!/usr/bin/env python3
"""
edgy_model_to_archimate.py — Export an edgy-model.json as an ArchiMate 3.1
Open Exchange Format file, for architecture teams that keep Archi (or another
ArchiMate tool) as the system of record. One-way: the EDGY model stays the
source; re-export after every change.

Usage:
  python3 edgy_model_to_archimate.py <company>-edgy-model.json [-o model.xml] [--language fi|en|fr|de]
                                     [--no-views]

What is written
  * every element with its name, description (documentation) and a property
    `edgy:type` (the EDGY element type), plus `edgy:id`, `edgy:provenance`,
    `edgy:nature`, `edgy:level` when the model has them;
  * every active core link as a directed Association named with the verb,
    between the primary elements of the two types (as in the diagrams);
  * one view per facet map (identity, architecture, experience, all facets)
    with the positions edgy-diagram computes for the same TXT input, so the
    views look like the delivered maps.

Mapping (EDGY 23 → ArchiMate 3.1). EDGY types without an exact ArchiMate
counterpart keep their meaning in `edgy:type`:

  purpose → Goal               story → Meaning            content → Representation
  capability → Capability      asset → Resource           process → BusinessProcess
  task → BusinessProcess*      channel → BusinessInterface  journey → ValueStream
  organisation → BusinessActor product → Product          brand → Value
  (* a Task is the person's job, not the organisation's process: edgy:type = task)

Relationships are Associations (allowed between any two ArchiMate elements)
named with the core-link verb; no Realization / Serving is inferred, because
EDGY verbs do not map one-to-one onto ArchiMate relationship semantics.
Standard library only.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edgy_model_to_txt as m2t  # noqa: E402

DIAGRAM_SCRIPTS = HERE.parent.parent.parent / "documentation" / "edgy-diagram" / "scripts"
sys.path.insert(0, str(DIAGRAM_SCRIPTS))

NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SCHEMA_LOCATION = f"{NS} http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"

ARCHIMATE_TYPE = {
    "purpose": "Goal", "story": "Meaning", "content": "Representation",
    "capability": "Capability", "asset": "Resource", "process": "BusinessProcess",
    "task": "BusinessProcess", "channel": "BusinessInterface", "journey": "ValueStream",
    "organisation": "BusinessActor", "product": "Product", "brand": "Value",
}
# ArchiMate 3.1 element types (Open Exchange xsi:type values) — the exporter only writes these
ARCHIMATE_ELEMENT_TYPES = {
    "BusinessActor", "BusinessRole", "BusinessCollaboration", "BusinessInterface", "BusinessProcess",
    "BusinessFunction", "BusinessInteraction", "BusinessEvent", "BusinessService", "BusinessObject", "Contract",
    "Representation", "Product", "ApplicationComponent", "ApplicationCollaboration", "ApplicationInterface",
    "ApplicationFunction", "ApplicationInteraction", "ApplicationProcess", "ApplicationEvent", "ApplicationService",
    "DataObject", "Node", "Device", "SystemSoftware", "TechnologyCollaboration", "TechnologyInterface", "Path",
    "CommunicationNetwork", "TechnologyFunction", "TechnologyProcess", "TechnologyInteraction", "TechnologyEvent",
    "TechnologyService", "Artifact", "Equipment", "Facility", "DistributionNetwork", "Material", "Stakeholder",
    "Driver", "Assessment", "Goal", "Outcome", "Principle", "Requirement", "Constraint", "Meaning", "Value",
    "Resource", "Capability", "ValueStream", "CourseOfAction", "WorkPackage", "Deliverable", "ImplementationEvent",
    "Plateau", "Gap", "Grouping", "Location", "AndJunction", "OrJunction",
}
PROPERTIES = ("edgy:type", "edgy:id", "edgy:provenance", "edgy:nature", "edgy:level")
FACET_VIEWS = (("identity", "Identity"), ("architecture", "Architecture"), ("experience", "Experience"),
               ("all", "All facets"))
ALL_TYPES = m2t.IDENTITY + m2t.ARCHITECTURE + m2t.EXPERIENCE + ["organisation", "product", "brand"]


def _q(tag):
    return f"{{{NS}}}{tag}"


def _text(parent, tag, value, lang):
    el = ET.SubElement(parent, _q(tag))
    el.set(XML_LANG, lang)
    el.text = value
    return el


def _ident(prefix, n):
    return f"id-{prefix}-{n}"


def collect(model):
    """[(type, index, element)] in the model's order, every type."""
    out = []
    for t in ALL_TYPES:
        for i, e in enumerate(m2t._as_list(model.get("elements", {}).get(t))):
            if isinstance(e, dict) and e.get("name"):
                out.append((t, i, e))
    return out


def view_positions(model, facet, lang):
    """{(type, name): (x, y, w, h)} from edgy-diagram's own layout of the facet TXT, or {} without the generator."""
    try:
        from edgy_parser import EDGYParser
    except Exception:   # pragma: no cover — the views then fall back to a plain grid
        return {}
    p = EDGYParser()
    p.parse_input(m2t.build(model, facet, lang))
    p.generate_xml()                    # runs the full layout (groups, facet containers, collisions)
    pos = p._calculate_layout()
    out = {}
    for eid, e in p.elements.items():
        w, h = p._get_element_size(e)
        x, y = pos.get(eid, (0, 0))
        out[(e["type"], e["name"].lower())] = (int(x), int(y), int(w), int(h))
    return out


def export(model, lang=None, views=True):
    lang = lang or model.get("language", "en")
    ET.register_namespace("", NS)
    ET.register_namespace("xsi", XSI)
    root = ET.Element(_q("model"), {"identifier": "id-model", f"{{{XSI}}}schemaLocation": SCHEMA_LOCATION})
    _text(root, "name", m2t._clean(model.get("company")) or "EDGY model", lang)
    _text(root, "documentation", f"Exported from edgy-model.json (assessed {m2t._clean(model.get('assessed_at'))}) "
                                 f"by edgy_model_to_archimate.py — one-way export; edit the EDGY model.", lang)

    elements_el = ET.SubElement(root, _q("elements"))
    ids = {}                 # (type, index) → identifier
    names = {}               # type → [names], primary first (as in the TXT)
    for n, (t, i, e) in enumerate(collect(model), 1):
        ident = _ident("el", n)
        ids[(t, i)] = ident
        el = ET.SubElement(elements_el, _q("element"), {"identifier": ident, f"{{{XSI}}}type": ARCHIMATE_TYPE[t]})
        _text(el, "name", m2t._clean(e["name"]), lang)
        if e.get("description"):
            _text(el, "documentation", m2t._clean(e["description"]), lang)
        props = ET.SubElement(el, _q("properties"))
        values = {"edgy:type": t, "edgy:id": e.get("id"), "edgy:provenance": e.get("provenance"),
                  "edgy:nature": e.get("nature"), "edgy:level": e.get("level")}
        for k, key in enumerate(PROPERTIES, 1):
            if values[key]:
                prop = ET.SubElement(props, _q("property"), {"propertyDefinitionRef": f"pd-{k}"})
                _text(prop, "value", str(values[key]), lang)

    for t in ALL_TYPES:
        elems = m2t._as_list(model.get("elements", {}).get(t))
        if elems:
            names[t] = m2t.primary_index(elems)

    rels_el = ET.SubElement(root, _q("relationships"))
    rels = []                # (identifier, source id, target id, (s_type, t_type))
    seen = set()
    for link in model.get("core_links", []):
        s, t = link.get("source"), link.get("target")
        if s not in names or t not in names or (s, t) in seen:
            continue
        verb = link.get(m2t.VERB_KEY.get(lang, "verb_en")) or link.get("verb_en") or m2t.default_verb(s, t, lang)
        if not verb:
            continue
        seen.add((s, t))
        ident = _ident("rel", len(rels) + 1)
        src, tgt = ids[(s, names[s])], ids[(t, names[t])]
        rel = ET.SubElement(rels_el, _q("relationship"), {"identifier": ident, "source": src, "target": tgt,
                                                           f"{{{XSI}}}type": "Association", "isDirected": "true"})
        _text(rel, "name", verb, lang)
        rels.append((ident, src, tgt, (s, t)))

    pdefs = ET.SubElement(root, _q("propertyDefinitions"))
    for k, key in enumerate(PROPERTIES, 1):
        pd = ET.SubElement(pdefs, _q("propertyDefinition"), {"identifier": f"pd-{k}", "type": "string"})
        _text(pd, "name", key, lang)

    if views:
        views_el = ET.SubElement(root, _q("views"))
        diagrams = ET.SubElement(views_el, _q("diagrams"))
        for v, (facet, title) in enumerate(FACET_VIEWS, 1):
            types = ALL_TYPES if facet == "all" else m2t.FACETS[facet][0] + m2t.FACETS[facet][1]
            positions = view_positions(model, facet, lang)
            view = ET.SubElement(diagrams, _q("view"), {"identifier": _ident("view", v), f"{{{XSI}}}type": "Diagram"})
            _text(view, "name", title, lang)
            node_of = {}
            col = 0
            for n, (t, i, e) in enumerate(collect(model), 1):
                if t not in types:
                    continue
                x, y, w, h = positions.get((t, m2t._clean(e["name"]).lower()), (40 + (col % 5) * 200, 40 + (col // 5) * 100, 160, 60))
                col += 1
                node_id = f"{_ident('view', v)}-n{n}"
                ET.SubElement(view, _q("node"), {"identifier": node_id, "elementRef": ids[(t, i)],
                                                 f"{{{XSI}}}type": "Element", "x": str(x), "y": str(y),
                                                 "w": str(w), "h": str(h)})
                node_of[ids[(t, i)]] = node_id
            for c, (rid, src, tgt, _pair) in enumerate(rels, 1):
                if src in node_of and tgt in node_of:
                    ET.SubElement(view, _q("connection"), {"identifier": f"{_ident('view', v)}-c{c}",
                                                           "relationshipRef": rid, f"{{{XSI}}}type": "Relationship",
                                                           "source": node_of[src], "target": node_of[tgt]})
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="edgy-model.json → ArchiMate 3.1 Open Exchange XML (one-way)")
    ap.add_argument("model")
    ap.add_argument("-o", "--output", help="output file (default: <model stem>.archimate.xml)")
    ap.add_argument("--language", choices=list(m2t.VERB_KEY), help="name / verb language (default: model.language)")
    ap.add_argument("--no-views", action="store_true", help="elements and relationships only, no diagrams")
    args = ap.parse_args(argv)
    try:
        model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"edgy_model_to_archimate: {exc}", file=sys.stderr)
        return 2
    out = Path(args.output) if args.output else Path(args.model).with_suffix(".archimate.xml")
    out.write_text(export(model, args.language, not args.no_views), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
