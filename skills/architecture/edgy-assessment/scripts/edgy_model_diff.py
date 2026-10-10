#!/usr/bin/env python3
"""
edgy_model_diff.py — Compare a current-state and a target-state edgy-model.json
and write a transition map input for edgy-diagram (the transition overlay,
an EDGY extension) plus a change table.

Usage:
  python3 edgy_model_diff.py CURRENT.json TARGET.json [--facet all|identity|architecture|experience]
                             [--out transition.txt] [--report changes.md] [--language fi|en|fr|de]
                             [--layout default|triad] [--json]

Matching, per element type, in this order:
  1. same `id` in both models                → keep, or change when name,
                                               description, nature, level or
                                               tags differ (a new name = renamed)
  2. same name (case-insensitive)            → keep / change as above
  3. similar name (difflib ratio ≥ 0.8)      → change (renamed)
  4. only in the target                      → new
  5. only in the current state               → remove
Core links are type-level in the model: a pair present only in the target is
`new`, only in the current state `remove`, a different verb `change`; they
are drawn between the primary elements of the two types, as in
edgy_model_to_txt.py.

`replace` and `decide` are judgements — "this asset replaces that one", "this
is still open" — that no comparison can make. The tool never writes them;
the analyst edits the TXT (or the model) and the report says so. The output
is a TXT input, so the transition map is generated, linted and previewed like
any other map. Standard library only.
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edgy_model_to_txt as m2t  # noqa: E402

ATTRS = ("description", "nature", "level")
# generated ids when the model has none: process and product would both be "PRO"
ID_PREFIX = {"product": "PRD", "process": "PRC", "organisation": "ORG", "capability": "CAP", "content": "CON",
             "channel": "CHA"}
RENAME_RATIO = 0.8


def _elements(model, t):
    return [e for e in m2t._as_list(model.get("elements", {}).get(t)) if isinstance(e, dict) and e.get("name")]


def _norm(text):
    return " ".join(str(text or "").lower().split())


def _differences(cur, tgt):
    out = []
    if _norm(cur.get("name")) != _norm(tgt.get("name")):
        out.append(f'renamed from "{cur.get("name")}"')
    for key in ATTRS:
        if _norm(cur.get(key)) != _norm(tgt.get(key)):
            out.append(f"{key} changed")
    if sorted(_norm(x) for x in cur.get("tags", [])) != sorted(_norm(x) for x in tgt.get("tags", [])):
        out.append("tags changed")
    return out


def diff_type(current, target, t):
    """[(change, current_element|None, target_element|None, detail)] for one element type."""
    cur, tgt = _elements(current, t), _elements(target, t)
    pairs, used_c, used_t = [], set(), set()

    def take(ci, ti):
        used_c.add(ci)
        used_t.add(ti)
        detail = _differences(cur[ci], tgt[ti])
        pairs.append(("change" if detail else "keep", cur[ci], tgt[ti], "; ".join(detail)))

    by_id = {e.get("id"): i for i, e in enumerate(cur) if e.get("id")}
    for ti, e in enumerate(tgt):
        if e.get("id") in by_id and by_id[e["id"]] not in used_c:
            take(by_id[e["id"]], ti)
    for ti, e in enumerate(tgt):
        if ti in used_t:
            continue
        for ci, c in enumerate(cur):
            if ci not in used_c and _norm(c["name"]) == _norm(e["name"]):
                take(ci, ti)
                break
    for ti, e in enumerate(tgt):
        if ti in used_t:
            continue
        best, score = None, RENAME_RATIO
        for ci, c in enumerate(cur):
            if ci in used_c:
                continue
            r = difflib.SequenceMatcher(None, _norm(c["name"]), _norm(e["name"])).ratio()
            if r >= score:
                best, score = ci, r
        if best is not None:
            take(best, ti)
    for ti, e in enumerate(tgt):
        if ti not in used_t:
            pairs.append(("new", None, e, ""))
    for ci, c in enumerate(cur):
        if ci not in used_c:
            pairs.append(("remove", c, None, ""))
    return pairs


def _links(model, lang):
    out = {}
    for link in model.get("core_links", []):
        s, t = link.get("source"), link.get("target")
        if s and t and (s, t) not in out:
            out[(s, t)] = link.get(m2t.VERB_KEY.get(lang, "verb_en")) or link.get("verb_en") or m2t.default_verb(s, t, lang)
    return out


def diff_links(current, target, lang):
    cur, tgt = _links(current, lang), _links(target, lang)
    out = []
    for key, verb in tgt.items():
        if key not in cur:
            out.append(("new", key, verb, ""))
        elif _norm(cur[key]) != _norm(verb):
            out.append(("change", key, verb, f'verb was "{cur[key]}"'))
        else:
            out.append(("keep", key, verb, ""))
    for key, verb in cur.items():
        if key not in tgt:
            out.append(("remove", key, verb, ""))
    return out


def facet_types(facet):
    if facet == "all":
        return m2t.IDENTITY + m2t.ARCHITECTURE + m2t.EXPERIENCE + ["organisation", "product", "brand"]
    main, inter = m2t.FACETS[facet]
    return main + inter


def compare(current, target, facet="all", lang="en"):
    types = facet_types(facet)
    elements = {t: diff_type(current, target, t) for t in types}
    links = [l for l in diff_links(current, target, lang) if l[1][0] in types and l[1][1] in types]
    return {"facet": facet, "language": lang, "elements": elements, "links": links}


def _line(t, change, e, index):
    name = m2t._clean(e.get("name"))
    desc = m2t._clean(e.get("description"))
    value = f"{name} - {desc}" if desc else name
    ident = e.get("id") or f"{ID_PREFIX.get(t, t[:3].upper())}-{index + 1:02d}"
    return f'  - {t}: "{value}" {{id: {ident}, change: {change}}}', name


def to_txt(result, current, target, layout="default"):
    lang = result["language"]
    lines = ["# Generated by edgy_model_diff.py from a current and a target edgy-model.json.",
             "# Transition overlay (EDGY extension): the stroke shows the change, the fill stays the facet colour.",
             "# replace / decide are judgements the tool never makes — set them by hand where they apply.",
             f"facet: {result['facet']}", f"language: {lang if lang in m2t.VERB_KEY else 'en'}"]
    if layout == "triad":
        lines.append("map_type: triad")       # planned ring: no link crosses a box, further elements in panels
    lines += ["", "elements:"]
    primary = {}
    for t, pairs in result["elements"].items():
        n = 0
        flagged = None
        for change, cur, tgt, _detail in pairs:
            e = tgt if tgt is not None else cur
            line, name = _line(t, change, e, n)
            n += 1
            lines.append(line)
            primary.setdefault(t, name)                     # default: the first element of the type
            if flagged is None and tgt is not None and tgt.get("primary") is True:
                flagged = name                              # the target's flagged primary wins
        if flagged:
            primary[t] = flagged
    lines += ["", "relationships:"]
    for change, (s, t), verb, _detail in result["links"]:
        if s in primary and t in primary and verb:
            lines.append(f'  - "{primary[s]}" -> "{primary[t]}": "{verb}" {{change: {change}}}')
    return "\n".join(lines) + "\n"


def to_report(result):
    rows = ["| Type | Element | Change | Detail |", "|------|---------|--------|--------|"]
    for t, pairs in result["elements"].items():
        for change, cur, tgt, detail in pairs:
            e = tgt if tgt is not None else cur
            rows.append(f"| {t} | {m2t._clean(e.get('name'))} | {change} | {detail} |")
    rows += ["", "| Core link | Verb | Change | Detail |", "|-----------|------|--------|--------|"]
    for change, (s, t), verb, detail in result["links"]:
        rows.append(f"| {s} → {t} | {verb or ''} | {change} | {detail} |")
    counts = {}
    for pairs in result["elements"].values():
        for change, *_ in pairs:
            counts[change] = counts.get(change, 0) + 1
    summary = ", ".join(f"{k} {counts.get(k, 0)}" for k in ("keep", "change", "new", "remove"))
    return (f"Elements: {summary}. `replace` and `decide` are judgements the comparison does not make: "
            f"mark them in the transition TXT where a new element replaces a removed one or a choice is open.\n\n"
            + "\n".join(rows) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="current + target edgy-model.json → transition map TXT and change table")
    ap.add_argument("current")
    ap.add_argument("target")
    ap.add_argument("--facet", choices=["all", "identity", "architecture", "experience"], default="all")
    ap.add_argument("--language", choices=list(m2t.VERB_KEY), help="verb language (default: target model language)")
    ap.add_argument("--out", help="transition TXT (default: stdout)")
    ap.add_argument("--report", help="markdown change table")
    ap.add_argument("--layout", choices=["default", "triad"], default="default",
                    help="triad = planned ring with Further panels (as edgy_model_to_txt.py --layout triad)")
    ap.add_argument("--json", action="store_true", help="print the comparison as JSON instead of TXT")
    args = ap.parse_args(argv)
    try:
        current = json.loads(Path(args.current).read_text(encoding="utf-8"))
        target = json.loads(Path(args.target).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"edgy_model_diff: {exc}", file=sys.stderr)
        return 2
    lang = args.language or target.get("language", "en")
    result = compare(current, target, args.facet, lang)
    if args.json:
        print(json.dumps({**result, "elements": {t: [{"change": c, "current": a and a.get("name"), "target": b and b.get("name"),
                                                       "detail": d} for c, a, b, d in pairs]
                                                  for t, pairs in result["elements"].items()},
                          "links": [{"change": c, "source": s, "target": t, "verb": v, "detail": d}
                                    for c, (s, t), v, d in result["links"]]}, ensure_ascii=False, indent=2))
        return 0
    txt = to_txt(result, current, target, args.layout)
    if args.out:
        Path(args.out).write_text(txt, encoding="utf-8")
        print(args.out)
    else:
        sys.stdout.write(txt)
    if args.report:
        Path(args.report).write_text(to_report(result), encoding="utf-8")
        print(args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
