#!/usr/bin/env python3
"""
edgy_semantic_review.py — questions about the *meaning* of an EDGY map.

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
  S007 a Capability is named after a system, tool or organisational unit
       (CRM, ERP, "… system", "… team", "… department") — capabilities are
       what the organisation can do, independent of who or what does it
  S008 a Capability is phrased as a verb ("Manage fleet", "Hallinnoida …") —
       name it as a result noun ("Fleet management")
  S009 a Capability is a project, programme or migration — a work package,
       not an ability the organisation keeps
  S010 a Task is phrased from the organisation's side (an internal verb on the
       customer: "Process customer refund") — a Task is what a person wants to
       get done, in their words ("Get my money back")
  S011 an Outcome is phrased as an action ("Implement CRM") — an Outcome is a
       result or a changed state
  S012 an Outcome outside a purpose map carries no measure (no metric in
       {…}, no number in the name) while other Outcomes on the page do —
       how will anyone know it happened? (info)
S001–S006 run on purpose maps (S001 / S006 on every Purpose); S007–S012 on
every page that has the element type.

Standard library only.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_vocab as _vocab  # noqa: E402
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
# The measures verb in every language, from the shared vocabulary (skills/_shared/edgy-core-links.yaml via
# edgy_vocab) — no hand-written spellings, so the review and the linter accept exactly the same labels.
MEASURES_VERBS = _vocab.spellings('measures') or {'measures'}
METRIC_RE = re.compile(r'(\d+([.,]\d+)?\s?(%|€|eur|kpl|pcs|h|min(?:utes?|uut(?:ti|tia))?|pv|d|days?|hours?|km|t|co2)(?!\w))'
                       r'|([≥≤<>]\s?\d)|(\d+\s?/\s?\d+)', re.I)
STEM_MIN = 5
RULE_SET = 'S001-S012'   # recorded in qa.json: which questions a run could raise
REVIEWED_TYPES = {'purpose', 'outcome', 'capability', 'task'}   # pages with these types get a semantic_review entry

# S008 / S011: the FIRST word is a verb in base form (infinitive / imperative) — exact
# words, not stems, so "Ticketing", "Upgraded wagons" and "Development planning" pass.
BASE_VERBS = {
    # words that are also common nouns in capability names (track, plan, run, support, launch, upgrade,
    # increase …) are left out on purpose: "Track access" is rail track, not an instruction
    'en': {'develop', 'implement', 'build', 'deploy', 'manage', 'handle', 'create', 'maintain', 'provide',
           'sell', 'buy', 'procure', 'monitor', 'ensure', 'improve', 'deliver', 'operate',
           'administer', 'introduce', 'establish', 'migrate', 'replace', 'modernise',
           'modernize', 'digitalise', 'digitalize', 'renew', 'optimise', 'optimize'},
    'fi': {'kehittää', 'toteuttaa', 'rakentaa', 'hallinnoida', 'hallita', 'ylläpitää', 'hoitaa', 'käsitellä', 'tuottaa',
           'suunnitella', 'myydä', 'ostaa', 'hankkia', 'seurata', 'varmistaa', 'parantaa', 'uudistaa', 'ottaa',
           'kehitetään', 'toteutetaan', 'rakennetaan', 'otetaan', 'uudistetaan', 'lisätä', 'vähentää', 'optimoida',
           'korvata', 'päivittää', 'digitalisoida', 'modernisoida'},
    'fr': {'gérer', 'développer', 'mettre', 'construire', 'déployer', 'créer', 'fournir', 'planifier', 'vendre',
           'acheter', 'assurer', 'améliorer', 'piloter', 'suivre', 'traiter', 'migrer', 'remplacer', 'moderniser',
           'augmenter', 'réduire', 'optimiser', 'lancer', 'établir'},
    'de': {'verwalten', 'entwickeln', 'umsetzen', 'aufbauen', 'bereitstellen', 'betreiben', 'planen', 'verkaufen',
           'einkaufen', 'sicherstellen', 'verbessern', 'steuern', 'bearbeiten', 'einführen', 'migrieren', 'ersetzen',
           'modernisieren', 'erhöhen', 'reduzieren', 'optimieren', 'starten', 'etablieren'},
}
# S007: systems, tools and organisational units (generic words and common product acronyms only)
SYSTEM_WORDS = {'system', 'systems', 'tool', 'tools', 'software', 'application', 'crm', 'erp', 'sap', 'salesforce',
                'servicenow', 'sharepoint', 'excel', 'jira', 'järjestelmä', 'järjestelmät', 'työkalu', 'sovellus',
                'système', 'logiciel', 'outil', 'anwendung', 'werkzeug'}
SYSTEM_SUFFIXES = ('järjestelmä', 'system', 'software', 'sovellus')
UNIT_WORDS = {'team', 'department', 'unit', 'office', 'division', 'tiimi', 'osasto', 'yksikkö', 'toimisto',
              'équipe', 'service', 'département', 'abteilung', 'bereich', 'referat'}
# S009: project-shaped names
PROJECT_STEMS = ('project', 'projekti', 'hanke', 'programme', 'program', 'ohjelma', 'initiative', 'pilot',
                 'migration', 'migraatio', 'implementation', 'käyttöönotto', 'uudistus', 'projet', 'projekt',
                 'programm', 'einführung')
# S010: an internal verb whose object is the customer
INTERNAL_VERBS = {'process', 'handle', 'approve', 'administer', 'invoice', 'onboard', 'register', 'käsitellä',
                  'käsittele', 'hyväksyä', 'hyväksy', 'laskuttaa', 'laskuta', 'rekisteröidä', 'traiter', 'approuver',
                  'facturer', 'bearbeiten', 'genehmigen', 'abrechnen', 'registrieren'}
CUSTOMER_STEMS = ('customer', 'client', 'passenger', 'citizen', 'user', 'asiak', 'matkustaj', 'käyttäj', 'kansalai',
                  'usager', 'voyageur', 'kunde', 'kundin', 'fahrgast', 'fahrgäst', 'bürger', 'nutzer')


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


def _base_verb(name: str) -> str:
    toks = _tokens(name)
    if not toks:
        return ''
    first = toks[0]
    for lang, words in BASE_VERBS.items():
        if first in words:
            return f'{first} ({lang})'
    return ''


def _system_or_unit(name: str) -> str:
    toks = _tokens(name)
    for t in toks:
        if t in SYSTEM_WORDS or any(t.endswith(suf) and t != suf for suf in SYSTEM_SUFFIXES):
            return f'system or tool word "{t}"'
        if t in UNIT_WORDS:
            return f'organisational unit word "{t}"'
    return ''


def _project_word(name: str) -> str:
    for t in _tokens(name):
        if any(t.startswith(st) for st in PROJECT_STEMS):
            return t
    if re.search(r'\b20\d\d\b', name):
        return re.search(r'\b20\d\d\b', name).group(0)
    return ''


def _org_voice(name: str) -> str:
    toks = _tokens(name)
    if toks and toks[0] in INTERNAL_VERBS and any(t.startswith(st) for t in toks[1:] for st in CUSTOMER_STEMS):
        return toks[0]
    return ''


def _has_measure(e: dict) -> bool:
    metrics = {k: v for k, v in (e.get('metrics') or {}).items() if k != 'status'}
    return bool(metrics) or bool(METRIC_RE.search(e['name'] + ' ' + (e.get('subtext') or '')))


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
    # S007–S012: capability, task and outcome wording on every page
    for eid, e in p.elements.items():
        if e['type'] == 'capability':
            hit = _system_or_unit(e['name'])
            if hit:
                add('S007', 'warning', e, f'named after a system, tool or unit ({hit})',
                    'What can the organisation do here, whoever or whatever does it? Name that ability '
                    '("Customer relationship management", not "CRM"); systems are Assets, units are Organisation.')
            hit = _base_verb(e['name'])
            if hit:
                add('S008', 'warning', e, f'phrased as a verb ({hit})',
                    'Can it be a result noun ("Fleet management" for "Manage fleet")? Capabilities are abilities, not instructions.')
            hit = _project_word(e['name'])
            if hit:
                add('S009', 'warning', e, f'reads as a project or a dated change ("{hit}")',
                    'Is this a work package or roadmap item? Model the lasting ability as the Capability and put the '
                    'change on the roadmap (transition overlay, waves).')
        elif e['type'] == 'task':
            hit = _org_voice(e['name'])
            if hit:
                add('S010', 'warning', e, f'organisation-side verb "{hit}" on the customer',
                    'What does the person want to get done, in their own words ("Get my money back" for '
                    '"Process customer refund")? The internal step is a Process or Activity.')
        elif e['type'] == 'outcome':
            hit = _base_verb(e['name'])
            if hit:
                add('S011', 'warning', e, f'phrased as an action ({hit})',
                    'What result or changed state does the action bring? Name that as the Outcome and put the action '
                    'on a Capability, Process or the roadmap.')
            elif not is_purpose_map and not _has_measure(e) and any(
                    _has_measure(o) for o in p.elements.values() if o['type'] == 'outcome'):
                add('S012', 'info', e, 'no measure (no metric, no number)',
                    'How will anyone know this happened? Add a metric ({kpi: …}) or link a measuring Outcome.')
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
    ap = argparse.ArgumentParser(description='Semantic review of an EDGY map input (questions, not verdicts)')
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
