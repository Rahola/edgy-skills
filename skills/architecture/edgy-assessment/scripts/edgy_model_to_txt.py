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
sys.path.insert(0, str(HERE))
import edgy_paths  # noqa: E402 — finds edgy-diagram in a checkout and after an install
DIAGRAM_SCRIPTS = edgy_paths.add_diagram_scripts_to_path() or edgy_paths.candidates()[-1]
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


# Generated ids when the model has none: the first three letters of the type, except where two
# types would share them — process and product are both "PRO" (the examples use PRO / PRD).
ID_PREFIX = {"product": "PRD"}


def id_prefix(element_type):
    return ID_PREFIX.get(element_type, element_type[:3].upper())


def primary_index(elements):
    """Index of the element that carries the type's core links: the one flagged
    `"primary": true` (the first such, if several), else 0."""
    for i, e in enumerate(elements):
        if isinstance(e, dict) and e.get("primary") is True:
            return i
    return 0


# provenance tags in the four languages the semantic review accepts (edgy_semantic_review.PROVENANCE_TAGS)
PROVENANCE_TAGS = {
    "en": {"confirmed": "confirmed", "analytical": "analytical", "proposed": "proposed"},
    "fi": {"confirmed": "vahvistettu", "analytical": "analyyttinen", "proposed": "ehdotettu"},
    "fr": {"confirmed": "confirmé", "analytical": "analytique", "proposed": "proposé"},
    "de": {"confirmed": "bestätigt", "analytical": "analytisch", "proposed": "vorgeschlagen"},
}


def element_lines(model, types, with_ids=True, lang="en"):
    """Returns (lines, names) where names[type] lists the element names with the
    primary element FIRST, so relationship_lines can use names[type][0].
    Provenance tags are written in `lang` (the report language)."""
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
            if e.get("provenance") in ("confirmed", "analytical", "proposed"):
                tag = PROVENANCE_TAGS.get(lang, PROVENANCE_TAGS["en"])[e["provenance"]]
                if tag not in tags:
                    tags.append(tag)
            value = f"{name} - {desc}" if desc else name
            tag_part = f" [{', '.join(tags)}]" if tags else ""
            metrics = {}
            if with_ids:
                metrics["id"] = e.get("id") or f"{id_prefix(t)}-{i + 1:02d}"
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
    el, names = element_lines(model, main_types, lang=lang)
    il, inames = element_lines(model, inter, lang=lang)
    names.update(inames)
    rel = relationship_lines(model, names, lang)
    body = header + el + ["  # intersection elements"] + il + ["", "relationships:"] + rel
    return "\n".join(body) + "\n"


# ---- architecture views (model format 1.9) ---------------------------------------------------------
# --views writes one multi-page TXT: a `draw: false` model page with every element (by id) and every
# relationships[] entry, then one or more view pages that edgy-diagram 2.8.0 derives from that graph.
MODEL_TYPES = IDENTITY + ARCHITECTURE + EXPERIENCE + ["organisation", "product", "brand", "people"]
ATTRIBUTE_KEYS_19 = ("kind", "hosting", "owner", "criticality", "time", "master", "gaps", "band")
VIEW_WRITERS = {}     # view name → function(model, lang) -> list of page blocks; registered by the view sprints


def register_view(name):
    def deco(fn):
        VIEW_WRITERS[name] = fn
        return fn
    return deco


def model_elements(model):
    """[(type, element dict, id)] for every element of the model, ids generated where missing."""
    out = []
    elems = model.get("elements") or {}
    for t in MODEL_TYPES:
        for i, e in enumerate(_as_list(elems.get(t))):
            if isinstance(e, dict) and e.get("name"):
                out.append((t, e, e.get("id") or f"{id_prefix(t)}-{i + 1:02d}"))
    return out


def _opt(value):
    v = _clean(value)
    return f'"{v}"' if ("," in v or ":" in v) else v


def model_page(model, lang, name="Model"):
    """The `draw: false` model page: in the document graph, not drawn."""
    lines = [f'  - name: "{name}"', "    draw: false", "    elements:"]
    for t, e, eid in model_elements(model):
        desc = _clean(e.get("description"))
        value = f"{_clean(e['name'])} - {desc}" if desc else _clean(e["name"])
        opts = {"id": eid}
        for k in ATTRIBUTE_KEYS_19:
            if k == "gaps" and isinstance(e.get(k), dict) and e[k]:
                # {"processes": "out_of_scope"} → gaps: "processes=out_of_scope" (the capability view's syntax)
                opts[k] = '"' + "; ".join(f"{_clean(b)}={_clean(v)}" for b, v in e[k].items()) + '"'
            elif k in e and e[k] not in (None, "") and k != "gaps":
                opts[k] = str(e[k]).lower() if isinstance(e[k], bool) else e[k]
        tags = [_clean(x) for x in e.get("tags", []) if _clean(x)]
        tag_part = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f'      - {t}: "{value}"{tag_part} {{' + ", ".join(f"{k}: {v if k == 'gaps' else _opt(v)}"
                                                                          for k, v in opts.items()) + "}")
    lines.append("    relationships:")
    for r in model.get("relationships") or []:
        if not isinstance(r, dict):
            continue
        attrs = r.get("attributes") or {}
        parts = []
        for k in ("crud", "technology", "container", "change"):
            if attrs.get(k):
                parts.append(f"{k}: {_opt(attrs[k])}")
        if attrs.get("primary") is True:
            parts.append("primary: true")
        if attrs.get("data"):
            parts.append('data: "' + "; ".join(_clean(x) for x in attrs["data"]) + '"')
        tail = " {" + ", ".join(parts) + "}" if parts else ""
        lines.append(f'      - "{_clean(r["source_id"])}" -> "{_clean(r["target_id"])}": "{_clean(r["verb"])}"{tail}')
    return lines


def _view_page(name, keys):
    return [f'  - name: "{name}"'] + [f"    {k}: {v}" for k, v in keys]


@register_view("application")
def _application_view(model, lang):
    """Application map grouped by the capability that requires each application (Shared strip for
    applications several areas need without a primary link)."""
    return [_view_page("Application map", [("map_type", "application"), ("group_by", "capability")])]


@register_view("process-chain")
def _process_chain_view(model, lang):
    return [_view_page("Process landscape", [("map_type", "process"), ("process_view", "chain")])]


@register_view("process-swimlane")
def _process_swimlane_view(model, lang):
    """One swimlane page per L1 process (the top of the contains hierarchy): its steps in the lanes of their
    performers — one page for every process at once would be a staircase of unrelated steps."""
    return [_view_page("Process swimlanes", [("expand", "per-process"), ("where", "top"), ("map_type", "process"),
                                             ("process_view", "swimlane"), ("legend", "strip")])]


@register_view("capability")
def _capability_view(model, lang):
    """One capability view per capability: processes, resources, data (CRUD), actors, products."""
    return [_view_page("Capability", [("expand", "per-capability"), ("map_type", "capability-view"),
                                      ("legend", "strip")])]


@register_view("capability-matrix")
def _capability_matrix_view(model, lang):
    return [_view_page("Capability × application", [("map_type", "capability-matrix")])]


@register_view("crud-matrix")
def _crud_matrix_view(model, lang):
    return [_view_page("Process × data (CRUD)", [("map_type", "capability-matrix"), ("matrix", "crud")])]


def build_views(model, views, lang):
    """One multi-page TXT: the model page and the requested view pages."""
    unknown = [v for v in views if v not in VIEW_WRITERS]
    if unknown:
        raise ValueError(f"unknown view(s): {', '.join(unknown)} (known: {', '.join(sorted(VIEW_WRITERS)) or 'none yet'})")
    if not isinstance(model.get("relationships"), list) or not model["relationships"]:
        raise ValueError("the architecture views need model format 1.9 with relationships[] between element ids")
    head = [f"# Generated from edgy-model.json by edgy_model_to_txt.py --views — do not edit by hand; edit the model.",
            f"# company: {_clean(model.get('company'))} · assessed_at: {_clean(model.get('assessed_at'))}",
            f"language: {lang if lang in VERB_KEY else 'en'}"]
    opts = model.get("layout") if isinstance(model.get("layout"), dict) else {}
    for key in LAYOUT_KEYS:
        if key in opts and opts[key] is not None and key not in ("title", "footnote"):
            value = opts[key]
            head.append(f"{key}: {str(value).lower() if isinstance(value, bool) else _clean(value)}")
    body = head + ["", "pages:"] + model_page(model, lang)
    for v in views:
        for block in VIEW_WRITERS[v](model, lang):
            body += [""] + block
    return "\n".join(body) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="edgy-model.json → four facet TXT inputs")
    ap.add_argument("model")
    ap.add_argument("--out", default=".")
    ap.add_argument("--prefix", help="file prefix (default: company slug)")
    ap.add_argument("--language", choices=list(VERB_KEY), help="verb language (default: model.language)")
    ap.add_argument("--layout", choices=["default", "triad"], default="default",
                    help="triad = planned ring with Further panels (map_type: triad in every file)")
    ap.add_argument("--views", help="comma-separated architecture views, or all (model format 1.9): writes "
                                    "<prefix>-views.txt — a draw: false model page and the view pages — instead of "
                                    "the four facet files")
    args = ap.parse_args(argv)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    lang = args.language or model.get("language", "en")
    prefix = args.prefix or "".join(c if c.isalnum() else "-" for c in model.get("company", "edgy").lower()).strip("-")
    os.makedirs(args.out, exist_ok=True)
    if args.views:
        try:
            views = [v.strip() for v in args.views.split(",") if v.strip()]
            if views == ["all"]:
                # all = every view the model can fill: a matrix without its links would be an empty page
                verbs = {r.get("verb") for r in model.get("relationships") or [] if isinstance(r, dict)}
                skip = {"crud-matrix": "accesses", "capability-matrix": "requires"}
                views = [v for v in VIEW_WRITERS if skip.get(v, "") == "" or skip[v] in verbs]
                for v, verb in skip.items():
                    if verb not in verbs:
                        print(f"edgy_model_to_txt: --views all leaves out {v} — the model has no {verb} relationships",
                              file=sys.stderr)
            text = build_views(model, views, lang)
        except ValueError as e:
            print(f"edgy_model_to_txt: {e}", file=sys.stderr)
            return 2
        path = Path(args.out) / f"{prefix}-views.txt"
        path.write_text(text, encoding="utf-8")
        print(path)
        return 0
    for facet in ("identity", "architecture", "experience", "all"):
        name = f"{prefix}-{'all-facets' if facet == 'all' else facet}.txt"
        path = Path(args.out) / name
        path.write_text(build(model, facet, lang, args.layout), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
