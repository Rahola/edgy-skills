#!/usr/bin/env python3
"""
render-core-links.py — Render the EDGY relationship vocabulary from the single
source (skills/_shared/edgy-core-links.yaml) into every place that repeats it.

Targets:
  * SKILL.md tables between marker comments
        <!-- edgy-links:begin format=<name> -->
        ...generated...
        <!-- edgy-links:end -->
    Formats: grouped4 | flat4-fi | flat-fi-en | assessment | influence
  * skills/documentation/edgy-diagram/scripts/edgy_core_links.py (whole file)

Usage:
  python3 tools/render-core-links.py            # rewrite targets in place
  python3 tools/render-core-links.py --check    # exit 1 if any target is stale
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "skills" / "_shared" / "edgy-core-links.yaml"
MODULE = REPO / "skills" / "documentation" / "edgy-diagram" / "scripts" / "edgy_core_links.py"
SKILL_FILES = [
    REPO / "skills" / "documentation" / "edgy-diagram" / "SKILL.md",
    REPO / "skills" / "architecture" / "edgy-framework" / "SKILL.md",
    REPO / "skills" / "architecture" / "edgy-assessment" / "SKILL.md",
    REPO / "skills" / "architecture" / "edgy-deep-dive" / "SKILL.md",
]
MARKER_RE = re.compile(
    r"(<!-- edgy-links:begin format=(?P<fmt>[a-z0-9-]+) -->\n)(?P<body>.*?)(<!-- edgy-links:end -->)",
    re.S,
)


def load():
    with SOURCE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _row(cells):
    return "| " + " | ".join(cells) + " |"


def render_grouped4(data):
    out = []
    by_group = {}
    for link in data["core_links"]:
        by_group.setdefault(link["group"], []).append(link)
    for g in data["groups"]:
        links = by_group.get(g["id"], [])
        if not links:
            continue
        out.append(f"#### {g['title']}")
        out.append("")
        out.append(_row(["Source → Target", "EN", "FI", "FR", "DE"]))
        out.append(_row(["-----------------", "----", "----", "----", "----"]))
        for l in links:
            out.append(_row([f"{l['source']} → {l['target']}", l["en"], l["fi"], l["fr"], l["de"]]))
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def render_flat(data, langs):
    header = ["Source → Target"] + [x.upper() for x in langs]
    out = [_row(header), _row(["-" * 17] + ["----"] * len(langs))]
    for l in data["core_links"]:
        out.append(_row([f"{l['source']} → {l['target']}"] + [l[x] for x in langs]))
    return "\n".join(out) + "\n"


def render_assessment(data):
    out = [_row(["Source", "Target", "verb_en", "verb_fi"]), _row(["--------", "--------", "---------", "---------"])]
    for l in data["core_links"]:
        out.append(_row([l["source"], l["target"], l["en"], l["fi"]]))
    return "\n".join(out) + "\n"


def render_influence(data):
    out = [_row(["EN", "FI", "FR", "DE", "Typical use"]), _row(["----", "----", "----", "----", "-------------"])]
    for v in data["influence_verbs"]:
        out.append(_row([v["en"], v["fi"], v["fr"], v["de"], v.get("usage", "")]))
    return "\n".join(out) + "\n"


RENDERERS = {
    "grouped4": render_grouped4,
    "flat4-fi": lambda d: render_flat(d, ["fi", "en", "fr", "de"]),
    "flat-fi-en": lambda d: render_flat(d, ["fi", "en"]),
    "assessment": render_assessment,
    "influence": render_influence,
}


def render_module(data):
    lines = [
        '"""',
        "edgy_core_links.py — GENERATED FILE, DO NOT EDIT.",
        "",
        "Source: skills/_shared/edgy-core-links.yaml",
        "Regenerate with: python3 tools/render-core-links.py",
        "",
        "Provides the EDGY 23 relationship vocabulary for edgy_parser.py and",
        "edgy_lint.py: the 24 official core links with their allowed",
        "(source, target) pairs in four languages, and the influence-verb",
        "vocabulary used for every other relationship.",
        '"""',
        "",
        "LANGUAGES = ('en', 'fi', 'fr', 'de')",
        "",
        "# (source, target, {'en': verb, 'fi': verb, 'fr': verb, 'de': verb}, group)",
        "CORE_LINKS = [",
    ]
    for l in data["core_links"]:
        verbs = ", ".join(f"'{x}': {l[x]!r}" for x in ("en", "fi", "fr", "de"))
        lines.append(f"    ({l['source']!r}, {l['target']!r}, {{{verbs}}}, {l['group']!r}),")
    lines += ["]", "", "# Accepted alternative spellings: verb → canonical verb", "CORE_LINK_ALIASES = {"]
    for l in data["core_links"]:
        for lang, alts in (l.get("aliases") or {}).items():
            for a in alts:
                lines.append(f"    {a!r}: {l[lang]!r},")
    lines += ["}", "", "# Influence verbs (non-core relationships → dashed line, open arrowhead)", "INFLUENCE_VERBS = ["]
    for v in data["influence_verbs"]:
        verbs = ", ".join(f"'{x}': {v[x]!r}" for x in ("en", "fi", "fr", "de"))
        lines.append(f"    {{{verbs}, 'usage': {v.get('usage', '')!r}}},")
    lines += [
        "]",
        "",
        "",
        "def _build():",
        "    verbs = {}",
        "    pairs = {}",
        "    for source, target, names, _group in CORE_LINKS:",
        "        for verb in names.values():",
        "            key = verb.lower()",
        "            verbs[key] = 'link'",
        "            pairs.setdefault(key, set()).add((source, target))",
        "    for alias, canonical in CORE_LINK_ALIASES.items():",
        "        key = alias.lower()",
        "        verbs[key] = 'link'",
        "        pairs[key] = set(pairs[canonical.lower()])",
        "    influence = set()",
        "    for entry in INFLUENCE_VERBS:",
        "        for lang in LANGUAGES:",
        "            influence.add(entry[lang].lower())",
        "    return verbs, pairs, influence",
        "",
        "",
        "# verb (lower-case) → 'link'   — every accepted core-link verb in any language",
        "# verb (lower-case) → {(source_type, target_type), ...} — allowed pairs",
        "# influence verbs (lower-case)",
        "EDGY_CORE_LINKS, CORE_LINK_PAIRS, INFLUENCE_RELATIONSHIPS = _build()",
        "",
        "",
        "def core_link_pairs(verb):",
        '    """Allowed (source, target) pairs for a verb, or an empty set if it is not a core-link verb."""',
        "    return CORE_LINK_PAIRS.get(verb.lower().strip(), set())",
        "",
        "",
        "def is_core_link(verb):",
        "    return verb.lower().strip() in EDGY_CORE_LINKS",
        "",
        "",
        "def is_influence_verb(verb):",
        "    return verb.lower().strip() in INFLUENCE_RELATIONSHIPS",
        "",
    ]
    return "\n".join(lines)


def render_skill(text, data):
    def repl(m):
        fmt = m.group("fmt")
        if fmt not in RENDERERS:
            raise SystemExit(f"unknown edgy-links format '{fmt}'")
        return m.group(1) + RENDERERS[fmt](data) + m.group(4)
    return MARKER_RE.sub(repl, text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if any target is stale")
    args = ap.parse_args()
    data = load()
    stale = []
    targets = [(MODULE, render_module(data))]
    for path in SKILL_FILES:
        text = path.read_text(encoding="utf-8")
        if "edgy-links:begin" not in text:
            print(f"warning: no edgy-links markers in {path.relative_to(REPO)}", file=sys.stderr)
            continue
        targets.append((path, render_skill(text, data)))
    for path, new in targets:
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != new:
            stale.append(path)
            if not args.check:
                path.write_text(new, encoding="utf-8")
                print(f"updated: {path.relative_to(REPO)}")
    if args.check:
        if stale:
            for p in stale:
                print(f"stale: {p.relative_to(REPO)} — run: python3 tools/render-core-links.py", file=sys.stderr)
            return 1
        print(f"core-links in sync ({len(targets)} targets)")
    elif not stale:
        print(f"all {len(targets)} targets already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
