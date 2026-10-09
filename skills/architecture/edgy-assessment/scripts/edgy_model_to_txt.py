#!/usr/bin/env python3
"""
edgy_model_to_txt.py — Derive the four facet TXT inputs for edgy-diagram from
an edgy-model.json, so that diagrams and analysis never disagree.

Usage:
  python3 edgy_model_to_txt.py <company>-edgy-model.json [--out DIR] [--prefix <company>]
                               [--language fi|en|fr|de] [--layout default|triad]

Writes <prefix>-identity.txt, <prefix>-architecture.txt, <prefix>-experience.txt
and <prefix>-all-facets.txt. Elements become `- type: "Name - Description" [tags] {id: …}`;
the model's active core links become relationships. A core link between two
element *types* is drawn once, between the *primary* element of each type —
the element flagged `"primary": true` in the model, otherwise the first of
its type — and the flag is written into the TXT as `{primary: true}`. The
report's tables carry the full detail, the diagram shows the structure.
`--layout triad` adds `map_type: triad` to every file: the planned ring with
"Further <type>" panels (edgy-diagram, EDGY extension) — use it when a facet
has more than ~8 elements. Standard library only.
"""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAGRAM_SCRIPTS = HERE.parent.parent.parent / "documentation" / "edgy-diagram" / "scripts"
sys.path.insert(0, str(DIAGRAM_SCRIPTS))
try:
    from edgy_core_links import CORE_LINKS  # noqa: E402
except ImportError as exc:  # the vocabulary is required to derive core links — never continue without it
    sys.exit(f"edgy_model_to_txt: cannot import the EDGY vocabulary module edgy_core_links from "
             f"{DIAGRAM_SCRIPTS} ({exc}). Run `python3 tools/render-core-links.py` or check the "
             f"edgy-diagram skill installation; refusing to write TXT files without core links.")
if not CORE_LINKS:
    sys.exit("edgy_model_to_txt: the EDGY vocabulary module is empty — regenerate it with "
             "`python3 tools/render-core-links.py`.")

IDENTITY = ["purpose", "story", "content"]
ARCHITECTURE = ["capability", "asset", "process"]
EXPERIENCE = ["task", "channel", "journey"]
FACETS = {
    "identity": (IDENTITY, ["brand", "organisation"]),
    "architecture": (ARCHITECTURE, ["organisation", "product"]),
    "experience": (EXPERIENCE, ["brand", "product"]),
}
VERB_KEY = {"fi": "verb_fi", "en": "verb_en", "fr": "verb_fr", "de": "verb_de"}


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _clean(text):
    return " ".join(str(text or "").replace('"', "'").split())


def primary_index(elements):
    """Index of the element that carries the type's core links: the one flagged
    `"primary": true` (the first such, if several), else 0."""
    for i, e in enumerate(elements):
        if isinstance(e, dict) and e.get("primary") is True:
            return i
    return 0


def element_lines(model, types, with_ids=True):
    """Returns (lines, names) where names[type] lists the element names with the
    primary element FIRST, so relationship_lines can use names[type][0]."""
    lines, names = [], {}
    for t in types:
        elements = _as_list(model["elements"].get(t))
        pi = primary_index(elements)
        for i, e in enumerate(elements):
            name = _clean(e.get("name"))
            desc = _clean(e.get("description"))
            tags = [_clean(x) for x in e.get("tags", []) if _clean(x)]
            for key in ("nature", "level"):
                if e.get(key):
                    tags.append(_clean(e[key]).lower())
            # provenance: confirmed (public source) | analytical (this analysis) | proposed — read by
            # edgy_semantic_review.py and shown on the element's tag line
            if e.get("provenance") in ("confirmed", "analytical", "proposed") and e["provenance"] not in tags:
                tags.append(e["provenance"])
            value = f"{name} - {desc}" if desc else name
            tag_part = f" [{', '.join(tags)}]" if tags else ""
            metrics = {}
            if with_ids:
                metrics["id"] = e.get("id") or f"{t[:3].upper()}-{i + 1:02d}"
            if e.get("primary") is True and i == pi:
                metrics["primary"] = "true"
            metric_part = " {" + ", ".join(f"{k}: {v}" for k, v in metrics.items()) + "}" if metrics else ""
            lines.append(f'  - {t}: "{value}"{tag_part}{metric_part}')
            names.setdefault(t, []).append(name)
        if t in names and pi:
            names[t].insert(0, names[t].pop(pi))
    return lines, names


def default_verb(source, target, lang):
    for s, t, verbs, _ in CORE_LINKS:
        if s == source and t == target:
            return verbs.get(lang) or verbs.get("en")
    return None


def relationship_lines(model, names, lang):
    out = []
    seen = set()
    for link in model.get("core_links", []):
        s, t = link.get("source"), link.get("target")
        if s not in names or t not in names or (s, t) in seen:
            continue
        verb = link.get(VERB_KEY.get(lang, "verb_en")) or link.get("verb_en") or default_verb(s, t, lang)
        if not verb:
            continue
        seen.add((s, t))
        out.append(f'  - "{names[s][0]}" -> "{names[t][0]}": "{verb}"')
    return out


LAYOUT_KEYS = ("legend", "card_width", "equal_cards", "group_columns", "cards_per_row", "equal_group_width",
               "align_groups", "title", "footnote")   # model.layout → TXT header, in this order


def build(model, facet, lang, layout="default"):
    if facet == "all":
        main_types = IDENTITY + ARCHITECTURE + EXPERIENCE
        inter = ["organisation", "product", "brand"]
    else:
        main_types, inter = FACETS[facet]
    header = [f"# Generated from edgy-model.json by edgy_model_to_txt.py — do not edit by hand; edit the model.",
              f"# company: {_clean(model.get('company'))} · assessed_at: {_clean(model.get('assessed_at'))}",
              f"facet: {facet}",
              f"language: {lang if lang in VERB_KEY else 'en'}"]   # generated headings (e.g. triad panels) in the report language
    if layout == "triad":
        header.append("map_type: triad")
    # layout block of the model → edgy-diagram document keys, identical in every file (series consistency)
    opts = model.get("layout") if isinstance(model.get("layout"), dict) else {}
    for key in LAYOUT_KEYS:
        if key in opts and opts[key] is not None:
            value = opts[key]
            value = str(value).lower() if isinstance(value, bool) else _clean(value)   # free text on one line: a newline would start a new directive
            header.append(f"{key}: {value}")
    header += ["", "elements:"]
    el, names = element_lines(model, main_types)
    il, inames = element_lines(model, inter)
    names.update(inames)
    rel = relationship_lines(model, names, lang)
    body = header + el + ["  # intersection elements"] + il + ["", "relationships:"] + rel
    return "\n".join(body) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="edgy-model.json → four facet TXT inputs")
    ap.add_argument("model")
    ap.add_argument("--out", default=".")
    ap.add_argument("--prefix", help="file prefix (default: company slug)")
    ap.add_argument("--language", choices=list(VERB_KEY), help="verb language (default: model.language)")
    ap.add_argument("--layout", choices=["default", "triad"], default="default",
                    help="triad = planned ring with Further panels (map_type: triad in every file)")
    args = ap.parse_args(argv)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    lang = args.language or model.get("language", "en")
    prefix = args.prefix or "".join(c if c.isalnum() else "-" for c in model.get("company", "edgy").lower()).strip("-")
    os.makedirs(args.out, exist_ok=True)
    for facet in ("identity", "architecture", "experience", "all"):
        name = f"{prefix}-{'all-facets' if facet == 'all' else facet}.txt"
        path = Path(args.out) / name
        path.write_text(build(model, facet, lang, args.layout), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
