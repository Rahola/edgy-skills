#!/usr/bin/env python3
"""
edgy_model_to_txt.py — Derive the four facet TXT inputs for edgy-diagram from
an edgy-model.json, so that diagrams and analysis never disagree.

Usage:
  python3 edgy_model_to_txt.py <company>-edgy-model.json [--out DIR] [--prefix <company>] [--language fi|en|fr|de]

Writes <prefix>-identity.txt, <prefix>-architecture.txt, <prefix>-experience.txt
and <prefix>-all-facets.txt. Elements become `- type: "Name - Description" [tags] {id: …}`;
the model's active core links become relationships. A core link between two
element *types* is drawn once, between the first (primary) element of each
type — the report's tables carry the full detail, the diagram shows the
structure. Standard library only.
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


def element_lines(model, types, with_ids=True):
    lines, names = [], {}
    for t in types:
        for i, e in enumerate(_as_list(model["elements"].get(t))):
            name = _clean(e.get("name"))
            desc = _clean(e.get("description"))
            tags = [_clean(x) for x in e.get("tags", []) if _clean(x)]
            for key in ("nature", "level"):
                if e.get(key):
                    tags.append(_clean(e[key]).lower())
            value = f"{name} - {desc}" if desc else name
            tag_part = f" [{', '.join(tags)}]" if tags else ""
            metrics = {}
            if with_ids:
                metrics["id"] = e.get("id") or f"{t[:3].upper()}-{i + 1:02d}"
            metric_part = " {" + ", ".join(f"{k}: {v}" for k, v in metrics.items()) + "}" if metrics else ""
            lines.append(f'  - {t}: "{value}"{tag_part}{metric_part}')
            names.setdefault(t, []).append(name)
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


def build(model, facet, lang):
    if facet == "all":
        main_types = IDENTITY + ARCHITECTURE + EXPERIENCE
        inter = ["organisation", "product", "brand"]
    else:
        main_types, inter = FACETS[facet]
    header = [f"# Generated from edgy-model.json by edgy_model_to_txt.py — do not edit by hand; edit the model.",
              f"# company: {_clean(model.get('company'))} · assessed_at: {_clean(model.get('assessed_at'))}",
              f"facet: {facet}", "", "elements:"]
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
    args = ap.parse_args(argv)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    lang = args.language or model.get("language", "en")
    prefix = args.prefix or "".join(c if c.isalnum() else "-" for c in model.get("company", "edgy").lower()).strip("-")
    os.makedirs(args.out, exist_ok=True)
    for facet in ("identity", "architecture", "experience", "all"):
        name = f"{prefix}-{'all-facets' if facet == 'all' else facet}.txt"
        path = Path(args.out) / name
        path.write_text(build(model, facet, lang), encoding="utf-8")
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
