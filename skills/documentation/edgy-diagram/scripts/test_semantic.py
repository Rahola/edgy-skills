#!/usr/bin/env python3
"""Tests for edgy_semantic_review.py — questions about purpose-map meaning."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_semantic_review as sem  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, '..', 'examples')
FIXTURE = os.path.join(EXAMPLES, 'eval', 'fixture-s1-purpose-semantics.txt')


def _rules(findings):
    out = {}
    for f in findings:
        out.setdefault(f['rule'], []).append(f)
    return out


def test_fixture_raises_each_question():
    findings = sem.review_text(open(FIXTURE, encoding='utf-8').read())
    r = _rules(findings)
    assert sorted(f['element'] for f in r['S001']) == ['PUR-02', 'PUR-03'], r.get('S001')
    assert [f['element'] for f in r['S002']] == ['OUT-02'], r.get('S002')
    assert [f['element'] for f in r['S003']] == ['OUT-02'], r.get('S003')
    assert [f['element'] for f in r['S004']] == ['PUR-02'], r.get('S004')
    assert [f['element'] for f in r['S006']] == ['PUR-04'], r.get('S006')
    assert all(f['level'] == 'info' for f in r.get('S005', [])), 'S005 is a hint, never a warning'
    assert all(f['question'] and f['reason'] for f in findings)


def test_task_verbs_in_four_languages():
    cases = {
        'fi': ('Toteutetaan uusi lippujärjestelmä', 'Sujuva arki'),
        'en': ('Develop a regional travel app', 'Effortless everyday travel'),
        'fr': ('Déployer un nouveau système billettique', 'Une mobilité fluide au quotidien'),
        'de': ('Einführung eines neuen Ticketsystems', 'Mühelose Alltagsmobilität'),
    }
    for lang, (action, purpose) in cases.items():
        assert sem._task_verb(action, lang), (lang, action)
        assert not sem._task_verb(purpose, lang), (lang, purpose)


def test_shipped_purpose_examples_are_silent():
    for name in ('purpose-hierarchy-map.txt', 'purpose-map.txt', os.path.join('eval', 'fixture-f5-purpose-tree.txt')):
        findings = sem.review_text(open(os.path.join(EXAMPLES, name), encoding='utf-8').read())
        warnings = [f for f in findings if f['level'] == 'warning']
        assert not warnings, (name, [(f['rule'], f['name'], f['reason']) for f in warnings])


def test_rules_scoped_to_purpose_maps():
    # S001 / S006 apply to any Purpose; S002–S005 only when map_type is purpose
    txt = 'facet: identity\nelements:\n  - purpose: "Implement the new platform"\n  - outcome: "Time −15 %"\n'
    r = _rules(sem.review_text(txt))
    assert 'S001' in r and 'S002' not in r and 'S003' not in r and 'S004' not in r


def test_cli_json_and_strict_exit_codes():
    script = os.path.join(HERE, 'edgy_semantic_review.py')
    r = subprocess.run([sys.executable, script, '--json', FIXTURE], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr                      # findings never fail a build by default
    data = json.loads(r.stdout)
    assert data and all('question' in f for f in data)
    assert 'not an approval' in r.stderr
    r = subprocess.run([sys.executable, script, '--strict', FIXTURE], capture_output=True, text=True)
    assert r.returncode == 1
    r = subprocess.run([sys.executable, script, '--strict', os.path.join(EXAMPLES, 'purpose-hierarchy-map.txt')], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_generator_flag_prints_review():
    gen = os.path.join(HERE, 'edgy_generator.py')
    import tempfile
    d = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, gen, FIXTURE, '--output', os.path.join(d, 's1.drawio'), '--semantic-review'],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert 'S001' in r.stderr and 'not an approval' in r.stderr, r.stderr


def test_s003_needs_status_and_s004_needs_tag():
    import edgy_semantic_review as sr
    from edgy_parser import EDGYParser
    p = EDGYParser()
    p.parse_input('map_type: purpose\nelements:\n  - purpose: "Effortless travel" {status: confirmed}\n'
                  '  - outcome: "Door-to-door time −15 %" [confirmed]\nrelationships:\n  - "Door-to-door time −15 %" -> "Effortless travel": "measures"\n')
    rules = [f['rule'] for f in sr.review_parser(p, None)]
    assert 'S004' in rules, 'a status on a Purpose is not a provenance tag'
    assert 'S003' in rules, 'a tag on an Outcome is not a metric status'


def test_s006_matches_values_ending_in_a_symbol():
    import edgy_semantic_review as sr
    for name in ('Cut churn 15%', 'Save 50 €', 'Reach 95 % on time', 'Cost 3 €/trip'):
        assert sr.METRIC_RE.search(name), name
    assert not sr.METRIC_RE.search('Platform 9 hub'), 'a bare number is no metric'


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f'Testing {t.__name__}...')
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} semantic-review tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'\nTest failed: {e}')
        sys.exit(1)
