#!/usr/bin/env python3
"""
edgy_semantic_review.py — questions about the *meaning* of a purpose map.

`edgy_lint.py` checks notation, structure and geometry; it has no opinion on
whether a Purpose is a purpose. This tool reads the generator's TXT input
and raises the questions a reviewer must answer before a purpose map is
delivered. It flags; it never decides — the exit code is 0 unless --strict,
and a clean run is not an approval. The sign-off is a person's
("Semantic review: approved by <role>, <date>", see edgy-framework
*Purpose map semantic review*).

Usage:
  python3 edgy_semantic_review.py INPUT.txt [--json] [--strict]

Rules (S = semantic; each finding carries the reason and the question to answer)
  S001 a Purpose is phrased as an action (task verb: develop / implement /
       build / deploy … in fi, en, fr, de) — purposes say why, not what to do
  S002 an Outcome in a purpose map measures no Purpose (no `measures`-type
       relationship to a Purpose)
  S003 an Outcome in a purpose map has no metric status ({status: confirmed|proposed})
  S004 a Purpose in a purpose map has no provenance tag
       ([confirmed] [analytical] [proposed])
  S005 `contains` between two Purposes whose names share no word stem, and
       the child is already flagged by S001 or S006 — is it a part-of
       relationship or an influence? (info; a plain sub-purpose with
       different words is normal and is not reported)
  S006 a Purpose name carries a metric value (number + unit / %) — metrics
       belong to Outcomes

Standard library only.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edgy_parser import EDGYParser, TREE_RELATIONSHIPS  # noqa: E402
from edgy_document import parse_document  # noqa: E402

# Word *stems* of task verbs — a token that starts with one of these is a hint
# (so "kehitetään", "developing", "déploiement", "eingeführt" all match).
TASK_VERB_STEMS = {
    'fi': ('kehit', 'toteut', 'rakenn', 'käyttöönot', 'uudist', 'hank', 'perust', 'käynnist', 'laadi', 'laadit',
           'pilot', 'digitalis', 'modernis', 'migro', 'korva', 'päivit', 'ota käyttöön', 'otetaan käyttöön'),
    'en': ('develop', 'implement', 'build', 'deploy', 'introduc', 'launch', 'establish', 'creat', 'roll out',
           'rollout', 'roll-out', 'migrat', 'modernis', 'moderniz', 'replac', 'upgrad', 'pilot', 'procur', 'set up',
           'digitalis', 'digitaliz', 'renew'),
    'fr': ('développ', 'mettre en œuvre', 'mise en œuvre', 'construi', 'déploi', 'déploy', 'introdui', 'lanc', 'établi',
           'cré', 'migr', 'modernis', 'remplac', 'pilot', 'numéris'),
    'de': ('entwickel', 'umsetz', 'aufbau', 'einführ', 'bereitstell', 'start', 'etablier', 'schaff', 'migrier',
           'modernisier', 'ersetz', 'pilotier', 'digitalisier', 'erneuer'),
}
PROVENANCE_TAGS = {
    'confirmed', 'analytical', 'proposed',
    'vahvistettu', 'analyyttinen', 'ehdotettu',
    'confirmé', 'analytique', 'proposé',
    'bestätigt', 'analytisch', 'vorgeschlagen',
}
MEASURES_VERBS = {'measures', 'mittaa', 'mesure', 'misst', 'measure'}
METRIC_RE = re.compile(r'(\d+([.,]\d+)?\s?(%|€|eur|kpl|pcs|h|min(?:utes?|uut(?:ti|tia))?|pv|d|days?|hours?|km|t|co2)(?!\w))'
                       r'|([≥≤<>]\s?\d)|(\d+\s?/\s?\d+)', re.I)
STEM_MIN = 5


def _tokens(text: str) -> List[str]:
    return [t for t in re.split(r"[^\w'’-]+", text.lower()) if t]


def _task_verb(name: str, lang_hint: str) -> str:
    """The matching stem (and language) or ''."""
    low = name.lower()
    langs = [lang_hint] + [l for l in TASK_VERB_STEMS if l != lang_hint] if lang_hint in TASK_VERB_STEMS else list(TASK_VERB_STEMS)
    toks = _tokens(name)
    for lang in langs:
        for stem in TASK_VERB_STEMS[lang]:
            if ' ' in stem:
                if stem in low:
                    return f'{stem} ({lang})'
            elif any(t.startswith(stem) for t in toks):
                return f'{stem}… ({lang})'
    return ''


def _has_provenance_tag(e: dict) -> bool:
    """Purpose (and any element): a provenance tag [confirmed] / [analytical] / [proposed]."""
    return bool({t.lower() for t in e.get('tags', [])} & PROVENANCE_TAGS)


def _has_metric_status(e: dict) -> bool:
    """Outcome: {status: confirmed|proposed} — a provenance tag alone does not say whether the target value is confirmed."""
    status = (e.get('metrics') or {}).get('status', '').strip().lower()
    return status in ('confirmed', 'proposed')


def _stems(name: str) -> set:
    return {t[:STEM_MIN] for t in _tokens(name) if len(t) >= STEM_MIN}


def review_parser(p: EDGYParser, page: str = None) -> List[Dict]:
    F: List[Dict] = []
    lang = getattr(p, 'language', 'en') or 'en'
    is_purpose_map = p.map_type == 'purpose'

    def add(rule, level, e, reason, question):
        F.append({'rule': rule, 'level': level, 'page': page, 'type': e['type'], 'element': e.get('ref') or e['id'],
                  'name': e['name'], 'reason': reason, 'question': question})

    purposes = {eid: e for eid, e in p.elements.items() if e['type'] == 'purpose'}
    outcomes = {eid: e for eid, e in p.elements.items() if e['type'] == 'outcome'}
    for eid, e in purposes.items():
        hit = _task_verb(e['name'], lang)
        if hit:
            add('S001', 'warning', e, f'name reads as an action ({hit})',
                'What is the lasting value or reason behind this action? Name that as the Purpose and move the action to a Capability, Process or a roadmap item.')
        m = METRIC_RE.search(e['name'])
        if m:
            add('S006', 'warning', e, f'metric value in the name ("{m.group(0).strip()}")',
                'Is this an Outcome that measures a Purpose? Put the target value on an Outcome with its status (confirmed / proposed).')
        if is_purpose_map and not _has_provenance_tag(e):
            add('S004', 'warning', e, 'no provenance tag',
                'Is this purpose confirmed from a public source, an analytical interpretation, or a proposal? Tag it [confirmed] / [analytical] / [proposed].')
    if is_purpose_map:
        for oid, o in outcomes.items():
            measured = any(r['source'] == oid and r['target'] in purposes and r['label'].lower().strip() in MEASURES_VERBS
                           for r in p.relationships)
            linked = any((r['source'] == oid and r['target'] in purposes) or (r['target'] == oid and r['source'] in purposes)
                         for r in p.relationships)
            if not measured:
                add('S002', 'warning', o, 'no `measures` relationship to a Purpose' + (' (linked otherwise)' if linked else ''),
                    'Which Purpose does this result verify? Add `"<outcome>" -> "<purpose>": "measures"` or drop the Outcome from this map.')
            if not _has_metric_status(o):
                add('S003', 'warning', o, 'no metric status',
                    'Is the metric and its target value confirmed by the organisation or proposed by the analysis? Add {status: confirmed} or {status: proposed}.')
        # S005 only where the child already looks like an action or a metric (S001 / S006) —
        # a plain sub-purpose with different words is normal and would drown the real hint
        suspect = {f['element'] for f in F if f['rule'] in ('S001', 'S006')}
        for r in p.relationships:
            if r['label'].lower().strip() in TREE_RELATIONSHIPS and r['source'] in purposes and r['target'] in purposes:
                parent, child = purposes[r['source']], purposes[r['target']]
                child_key = child.get('ref') or child['id']
                if child_key in suspect and not (_stems(parent['name']) & _stems(child['name'])):
                    add('S005', 'info', child, f'`{r["label"]}` from "{parent["name"]}" — the names share no word stem',
                        'Is this a part-of relationship (the child is a component of the parent purpose) or an influence? If influence, use an influence verb.')
    return F


def review_text(text: str) -> List[Dict]:
    findings: List[Dict] = []
    pages = parse_document(text)
    for name, p in pages:
        findings.extend(review_parser(p, name if len(pages) > 1 else None))
    return findings


def format_findings(findings: List[Dict], path: str) -> str:
    lines = []
    for f in findings:
        page = f" [page {f['page']}]" if f.get('page') else ''
        lines.append(f"{path}: {f['level'].upper()} {f['rule']}{page} {f['type']} \"{f['name']}\" ({f['element']}): {f['reason']}\n    → {f['question']}")
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Semantic review of an EDGY purpose map input (questions, not verdicts)')
    ap.add_argument('inputs', nargs='+', help='generator TXT input(s)')
    ap.add_argument('--json', action='store_true', help='machine-readable findings')
    ap.add_argument('--strict', action='store_true', help='exit 1 when any warning-level finding exists')
    args = ap.parse_args(argv)
    all_findings = []
    for path in args.inputs:
        try:
            text = open(path, encoding='utf-8').read()
        except OSError as e:
            print(f'edgy-semantic-review: cannot read {path}: {e}', file=sys.stderr)
            return 2
        try:
            findings = review_text(text)
        except ValueError as e:
            print(f'edgy-semantic-review: {path}: {e}', file=sys.stderr)
            return 2
        for f in findings:
            f['file'] = path
        all_findings.extend(findings)
        if not args.json and findings:
            print(format_findings(findings, path))
    warnings = [f for f in all_findings if f['level'] == 'warning']
    if args.json:
        print(json.dumps(all_findings, ensure_ascii=False, indent=2))
    summary = (f"edgy-semantic-review: {len(args.inputs)} file(s), {len(warnings)} question(s), "
               f"{len(all_findings) - len(warnings)} hint(s) — a clean run is not an approval; a reviewer signs off")
    print(summary, file=sys.stderr if args.json else sys.stdout)
    return 1 if (args.strict and warnings) else 0


if __name__ == '__main__':
    sys.exit(main())
