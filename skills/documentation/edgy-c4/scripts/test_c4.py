#!/usr/bin/env python3
"""edgy-c4 0.1.0 (test plan v2.5.0 K04–K09; plan §4 F4, §4a CX5).

Runs inside edgy-diagram (its scripts on the path, this skill on EDGY_NOTATION_PATH):
- K04 L1 for every application of the eval model, strict lint clean; Persons observed and inferred
  (dashed), external partners grey, a missing Person a note;
- K05 the example L2 page: containers with technology, the boundary, the back link to L1;
- K06 C001–C006: one fixture per rule, each raising its own finding and nothing else;
- K07 the prepass: page order, the endpoint a container attaches to, a two-sided crossing;
- K08 static shapes, byte-identical runs; K09 the legend on every page and the register entry.
"""

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SKILL, '..', '..', '..'))
CORE = os.path.join(REPO, 'skills', 'documentation', 'edgy-diagram')
os.environ['EDGY_NOTATION_PATH'] = SKILL
os.environ['EDGY_TEXT_TABLE_ONLY'] = '1'
sys.path.insert(0, os.path.join(CORE, 'scripts'))
from edgy_document import parse_document, build_mxfile, page_ids_of  # noqa: E402

EXAMPLE = os.path.join(SKILL, 'examples', 'c4-fare-engine.txt')


def generate(text, *extra):
    tmp = tempfile.mkdtemp()
    src, out = os.path.join(tmp, 'in.txt'), os.path.join(tmp, 'out.drawio')
    open(src, 'w', encoding='utf-8').write(text)
    r = subprocess.run([sys.executable, os.path.join(CORE, 'scripts', 'edgy_generator.py'), src, '--output', out, *extra],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, out


def strict_lint(path):
    r = subprocess.run([sys.executable, os.path.join(CORE, 'scripts', 'edgy_lint.py'), '--warnings-as-errors', path],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def findings(text):
    """{(rule, severity, page)} of every C-rule message, and every other message (must be none)."""
    pages = parse_document(text)
    out, other = set(), []
    for name, p in pages:
        for sev, msgs in (('error', p.errors), ('warning', p.warnings), ('note', p.notes)):
            for m in msgs:
                rule = m.split(' ', 1)[0]
                if re.match(r'^C00\d$', rule):
                    out.add((rule, sev, p.page_id, m))
                elif sev != 'note':
                    other.append(m)
    return out, other


def eval_model():
    s = open(os.path.join(CORE, 'examples', 'eval', 'architecture-views.txt'), encoding='utf-8').read()
    return s[:s.index('  - name: "Application map"')].rstrip() + '\n'


def test_k04_l1_for_every_application():
    model = eval_model()
    apps = re.findall(r'asset: "[^"]*" \{id: (APP-\d+), kind: application', model)
    text = model + '\n  - name: "Context"\n    notation: c4\n    level: context\n    expand: per-application\n'
    pages = parse_document(text)
    assert sorted(p.page_id for _, p in pages) == sorted(f'c4-context-{a.lower()}' for a in apps), \
        [p.page_id for _, p in pages]
    notes = [n for _, p in pages for n in p.notes if 'no Person' in n]
    assert notes and all(not p.errors and not p.warnings for _, p in pages)
    rc, out, path = generate(text, '--qa')
    assert rc == 0, out
    rc, out = strict_lint(path)
    assert rc == 0, out
    xml = open(path, encoding='utf-8').read()
    assert 'uses (inferred)' in xml and 'dashed=1;strokeWidth=3;' in xml        # an inferred Person, dashed
    # an observed Person and a grey external partner (the example model)
    ex = open(EXAMPLE, encoding='utf-8').read() + ('\n  - name: "Shop"\n    notation: c4\n    level: context\n'
                                                     '    system: APP-05\n')
    pages = parse_document(ex)
    shop = next(p for _, p in pages if p.page_id == 'c4-context-app-05').generate_xml()
    assert '#999999' in shop and 'Payment gateway' in shop and 'external' in shop


def test_k05_l2_from_the_example():
    rc, out, path = generate(open(EXAMPLE, encoding='utf-8').read(), '--qa')
    assert rc == 0, out
    rc, out = strict_lint(path)
    assert rc == 0, out
    xml = open(path, encoding='utf-8').read()
    l2 = xml[xml.index('id="c4-container-app-07"'):]
    l2 = l2[:l2.index('</diagram>')]
    assert '[Container: Kotlin]' in l2 and '[Container: PostgreSQL]' in l2
    assert 'reads and writes fare rules [JDBC]' in l2 and 'Fare rules [REST]' in l2   # inside and crossing
    assert 'Fare engine [Software System]' in l2 and 'edgyRole=container' in l2         # the boundary
    assert 'link="data:page/id,c4-context-app-07"' in l2                                # back to L1
    l1 = xml[xml.index('id="c4-context-app-07"'):]
    assert 'link="data:page/id,c4-container-app-07"' in l1[:l1.index('</diagram>')]    # down to L2


BASE = '''pages:
  - name: "Model"
    draw: false
    elements:
      - asset: "Ticket shop" {id: APP-05, kind: application}
      - asset: "Fare engine" {id: APP-07, kind: application}
      - asset: "Payment gateway" {id: APP-09, kind: application}
      - asset: "Integration platform" {id: APP-16, kind: integration}
      - people: "Fare analyst" {id: PEO-02}
    relationships:
      - "PEO-02" -> "APP-07": "interacts with"
      - "PEO-02" -> "APP-05": "interacts with"
      - "APP-05" -> "APP-07": "transfers" {technology: REST%s}
'''
L2 = '''  - name: "%s"
    notation: c4
    level: container
    system: %s
    elements:
%s    relationships:
%s'''


def l2(name, system, containers, rels=''):
    return L2 % (name, system, ''.join(f'      - container: "{n}" {{id: {i}, technology: Go}}\n' for i, n in containers),
                 rels or '')


def test_k06_one_fixture_per_rule():
    ok_rel = '      - "C-API" -> "C-DB": "reads" {technology: JDBC}\n'
    two = [('C-API', 'API'), ('C-DB', 'DB')]
    cases = {
        'C001': (BASE % ', container: C-NOPE') + l2('Fare engine L2', 'APP-07', two, ok_rel),
        'C002': (BASE % '') + l2('Fare engine L2', 'APP-07', two, '      - "C-API" -> "C-DB": "" {technology: JDBC}\n'),
        'C003': (BASE % '') + l2('Fare engine L2', 'APP-07', two, '      - "C-API" -> "C-DB": "reads"\n'),
        'C004': (BASE % '') + '  - name: "Bus"\n    notation: c4\n    level: context\n    system: APP-16\n',
        'C005': (BASE % '') + ('  - name: "Hand L1"\n    notation: c4\n    level: context\n    system: APP-07\n'
                               '    elements:\n      - person: "Fare analyst" {id: PEO-02}\n'),
        'C006': (BASE % '') + l2('Fare engine L2', 'APP-07', two, ok_rel) + l2('Shop L2', 'APP-05', [('C-API', 'Dup')]),
    }
    expected = {'C001': ('error', None), 'C002': ('warning', 'c4-container-app-07'),
                'C003': ('warning', 'c4-container-app-07'), 'C004': ('error', 'c4-context-app-16'),
                'C005': ('warning', 'c4-context-app-07'), 'C006': ('error', 'c4-container-app-05')}
    for rule, text in cases.items():
        found, other = findings(text)
        assert [(r, s) for r, s, _p, _m in found] == [(rule, expected[rule][0])], (rule, found)
        if expected[rule][1]:
            assert next(iter(found))[2] == expected[rule][1], (rule, found)
        assert not other, (rule, other)
    found, _ = findings(cases['C001'])
    assert 'C-NOPE' in next(iter(found))[3]
    rc, out, path = generate(cases['C001'])
    assert rc == 2 and not os.path.exists(path), out
    rc, out, path = generate(cases['C003'])
    assert rc == 0 and os.path.exists(path), out
    # an invalid or too long container id is C001 as well
    long_id = 'C-' + 'X' * 70
    found, _ = findings((BASE % '') + l2('L2', 'APP-07', [(long_id, 'Long')]))
    assert [r for r, *_ in found] == ['C001'], found


def test_k07_prepass_and_endpoints():
    text = open(EXAMPLE, encoding='utf-8').read()
    head, *blocks = text.split('  - name: ')
    reordered = head + ''.join('  - name: ' + b.rstrip('\n') + '\n\n' for b in reversed(blocks))

    def by_id(t):
        pages = parse_document(t)
        return {p.page_id: p.generate_xml() for _, p in pages}
    assert by_id(text) == by_id(reordered)
    import edgy_c4
    from edgy_document import load_graph
    cont = {'C-FARE-API': {'system': 'APP-07'}, 'C-WEB': {'system': 'APP-05'}}
    for transfer, expect in (('"APP-05" -> "APP-07"', ('APP-05', 'C-FARE-API')),
                             ('"APP-07" -> "APP-05"', ('C-FARE-API', 'APP-05'))):
        g = load_graph('elements:\n  - asset: "Shop" {id: APP-05, kind: application}\n'
                       '  - asset: "Fare" {id: APP-07, kind: application}\nrelationships:\n'
                       f'  - {transfer}: "transfers" {{technology: REST, container: C-FARE-API}}\n')
        got = [(c['source'], c['target']) for c in edgy_c4.crossings(g, 'APP-07', cont)]
        assert got == [expect], (transfer, got)
    for raw in ('C-WEB; C-FARE-API', 'C-FARE-API; C-WEB'):
        g = load_graph('elements:\n  - asset: "Shop" {id: APP-05, kind: application}\n'
                       '  - asset: "Fare" {id: APP-07, kind: application}\nrelationships:\n'
                       f'  - "APP-05" -> "APP-07": "transfers" {{technology: REST, container: "{raw}"}}\n')
        assert [(c['source'], c['target']) for c in edgy_c4.crossings(g, 'APP-07', cont)] == [('APP-05', 'C-FARE-API')]
        assert [(c['source'], c['target']) for c in edgy_c4.crossings(g, 'APP-05', cont)] == [('C-WEB', 'APP-07')]
    # a container of neither endpoint
    found, _ = findings((BASE % ', container: C-X') + l2('Gateway L2', 'APP-09', [('C-X', 'X')]))
    assert [r for r, *_ in found] == ['C001'] and 'neither endpoint' in next(iter(found))[3], found


def test_k08_static_shapes_and_byte_identical_runs():
    src = open(os.path.join(HERE, 'edgy_c4.py'), encoding='utf-8').read()
    assert 'mxgraph.c4' not in src
    text = open(EXAMPLE, encoding='utf-8').read()
    first = generate(text)
    second = generate(text)
    assert first[0] == second[0] == 0
    assert open(first[2], encoding='utf-8').read() == open(second[2], encoding='utf-8').read()
    rc, out, path = generate(text, '--preview')
    svg = os.path.join(os.path.dirname(path), 'out-fare-engine-containers.svg')
    assert rc == 0 and os.path.exists(svg), out
    assert 'Fare API' in open(svg, encoding='utf-8').read()


def test_k09_legend_and_register():
    rc, out, path = generate(open(EXAMPLE, encoding='utf-8').read())
    xml = open(path, encoding='utf-8').read()
    pages = re.findall(r'<diagram id="(c4-[^"]+)"', xml)
    assert len(pages) == 2
    for chunk in xml.split('<diagram ')[1:]:
        assert 'C4 model (Simon Brown, CC BY 4.0)' in chunk
    reg = open(os.path.join(CORE, 'references', 'external-standards.md'), encoding='utf-8').read()
    c4 = reg[reg.index('### C4 model'):]
    c4 = c4[:c4.index('\n### ')] if '\n### ' in c4 else c4
    assert 'in use' in c4.split('\n')[0] and 'PlantUML' not in c4.replace('C4-PlantUML output is planned for 0.2.0', '')


def test_k10_q3_badge_on_the_trace_card():
    """Q3: with a C4 context page, the APP-01 card on its trace page keeps its trace link and gets a separate
    "C4" badge linking to c4-context-app-01; without it, no badge. No link points to a missing page."""
    fpath = open(os.path.join(CORE, 'scripts', 'fixtures', 'trace', 'f-path.txt'), encoding='utf-8').read()
    c4 = '  - name: "Booking system context"\n    notation: c4\n    level: context\n    system: APP-01\n'
    for with_c4 in (True, False):
        text = fpath.rstrip('\n') + '\n' + (c4 if with_c4 else '')
        pages = parse_document(text)
        xml = build_mxfile([(n, p.generate_xml()) for n, p in pages], page_ids=page_ids_of(pages))
        ids = set(re.findall(r'<diagram id="([^"]+)"', xml))
        assert set(re.findall(r'link="data:page/id,([^"]+)"', xml)) <= ids          # every link resolves
        page = xml[xml.index('id="trace-cap-01"'):]
        page = page[:page.index('</diagram>')]
        assert 'link="data:page/id,trace-app-01"' in page                              # the card's trace link
        has_badge = 'link="data:page/id,c4-context-app-01"' in page
        assert has_badge == with_c4, (with_c4, has_badge)
        if with_c4:
            badge = re.search(r'<UserObject id="(\d+)" label="C4" link="data:page/id,c4-context-app-01">\s*'
                              r'<mxCell style="[^"]*edgyRole=link;[^"]*" vertex="1" parent="(\d+)"', page)
            assert badge, page[:2000]


def test_phase4_findings():
    """Phase 4 (Claude C4 tester): hostile labels stay text, and three wrong inputs are no longer silent."""
    hostile = (BASE % '') + l2('L2', 'APP-07', [('C-API', 'API'), ('C-DB', 'DB')],
                              '      - "C-API" -> "C-DB": "</template><script>alert(1)</script>" {technology: JDBC}\n')
    pages = parse_document(hostile)
    xml = next(p for _, p in pages if p.page_id == 'c4-container-app-07').generate_xml()
    import xml.etree.ElementTree as ET
    values = [c.get('value') or '' for c in ET.fromstring(xml).iter('mxCell') if c.get('edge') == '1']
    assert any('&lt;script&gt;' in v for v in values), values               # html=1 shows it as text
    two = (BASE % '') + ('  - name: "A"\n    notation: c4\n    level: context\n    system: APP-07\n'
                         '  - name: "B"\n    notation: c4\n    level: context\n    system: APP-07\n')
    found, _ = findings(two)
    assert [(r, sev) for r, sev, *_ in found] == [('C006', 'error')], found
    comp = (BASE % '') + '  - name: "L3"\n    notation: c4\n    level: component\n    system: APP-07\n'
    found, _ = findings(comp)
    assert [(r, sev) for r, sev, *_ in found] == [('C004', 'error')], found
    ghost = (BASE % '') + l2('L2', 'APP-07', [('C-API', 'API')],
                             '      - "C-API" -> "C-GHOST": "reads" {technology: JDBC}\n')
    found, _ = findings(ghost)
    assert [(r, sev) for r, sev, *_ in found] == [('C001', 'error')] and 'C-GHOST' in next(iter(found))[3], found


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} edgy-c4 tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
