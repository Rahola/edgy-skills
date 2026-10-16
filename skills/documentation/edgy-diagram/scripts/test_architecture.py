#!/usr/bin/env python3
"""Tests for the architecture views (edgy-diagram 2.8.0, Sprint 23): application map
(domains × layers, group by capability with the Shared strip, external column,
TIME and second badges, owners and data folded, integrations, routing), process
chain (bands, L2 / L3) and swimlane (lanes, staircase, chips), W124–W126, S013,
views derived from the document graph and edgy_model_to_txt --views."""

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SKILL, '..', '..', '..'))
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile  # noqa: E402
import edgy_lint  # noqa: E402
import edgy_semantic_review  # noqa: E402


def _xml(text):
    pages = parse_document(text)
    return pages, build_mxfile([(n, p.generate_xml()) for n, p in pages])


def _lint(xml):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False)
        return [(x.rule, x.level, x.msg) for x in edgy_lint.lint_file(path, opts)]
    finally:
        os.unlink(path)


def _cells(xml):
    """{first label line: (abs x, abs y, w, h)} of the element cells."""
    root = ET.fromstring(xml)
    out = {}
    for d in root.iter('diagram'):
        cells = {c.get('id'): c for c in d.iter('mxCell')}
        for c in cells.values():
            if 'edgyType=' not in (c.get('style') or ''):
                continue
            g = c.find('mxGeometry')
            x, y = float(g.get('x')), float(g.get('y'))
            p = cells.get(c.get('parent'))
            while p is not None and p.get('vertex') == '1':
                pg = p.find('mxGeometry')
                x, y = x + float(pg.get('x')), y + float(pg.get('y'))
                p = cells.get(p.get('parent'))
            name = re.sub(r'<[^>]+>', '\n', (c.get('value') or '').replace('&lt;', '<').replace('&gt;', '>')).strip().split('\n')[0]
            out[name] = (x, y, float(g.get('width')), float(g.get('height')))
    return out


def _example(name):
    return open(os.path.join(SKILL, 'examples', name), encoding='utf-8').read()


def test_domains_by_layers_and_external_column():
    pages, xml = _xml(_example('application-map.txt'))
    p = pages[0][1]
    assert p.stages == ['Customer', 'Fares and ticketing', 'Operations', 'Data', 'External systems'], p.stages
    cells = _cells(xml)
    # same domain → same column (x), same layer → same row band; externals in the last column
    assert cells['Ticket shop'][0] == cells['Fare engine'][0] == cells['Payment gateway'][0]
    assert cells['Ticket shop'][1] < cells['Fare engine'][1] < cells['Payment gateway'][1]
    assert cells['National timetable registry'][0] > cells['Integration platform'][0]
    assert 'Fare rules' not in cells and 'Platform team' not in cells, 'data and owners are folded'
    assert 'owner: Platform team' in xml
    found = _lint(xml)
    assert not found, found
    # every integration was routed around the cards
    assert xml.count('<Array as="points">') >= 5


def test_time_and_second_badge_with_legend():
    pages, xml = _xml(_example('application-map.txt'))
    assert 'Lifecycle (Gartner TIME, extension)' in xml and 'Hosting (extension)' in xml
    badges = re.findall(r'value="(\w[\w-]*)" style="rounded=1;arcSize=40;[^"]*edgyRole=badge;', xml)
    assert {'Invest', 'Tolerate', 'Migrate', 'Eliminate', 'cloud', 'on-prem', 'saas'} <= set(badges), set(badges)
    p = parse_document('map_type: application\nelements:\n  - asset: "A" {id: A-1, kind: application, time: forever}\n')[0][1]
    p.generate_xml()
    assert any("not Gartner TIME" in w for w in p.warnings)
    fi = parse_document('map_type: application\nlanguage: fi\nelements:\n  - asset: "A" {id: A-1, kind: application, time: invest}\n')
    assert 'Investoi' in build_mxfile([(n, q.generate_xml()) for n, q in fi])


def test_group_by_capability_primary_shared_and_none():
    text = '''map_type: application
group_by: capability
elements:
  - group: "Fares"
    - capability: "Pricing" {id: CAP-1}
    - capability: "Sales" {id: CAP-2}
  - capability: "Planning" {id: CAP-3}
  - asset: "Fare engine" {id: APP-1, kind: application}
  - asset: "Identity" {id: APP-2, kind: platform}
  - asset: "Planner" {id: APP-3, kind: application}
  - asset: "Orphan" {id: APP-4, kind: application}
  - asset: "Bus" {id: APP-5, kind: integration}
relationships:
  - "CAP-1" -> "APP-1": "requires"
  - "CAP-3" -> "APP-1": "requires" {primary: true}
  - "CAP-2" -> "APP-2": "requires"
  - "CAP-3" -> "APP-2": "requires"
  - "CAP-3" -> "APP-3": "requires"
  - "CAP-1" -> "APP-5": "requires"
  - "CAP-2" -> "APP-5": "requires"
'''
    pages, xml = _xml(text)
    p = pages[0][1]
    areas = {g['name']: sorted(p.elements[m]['name'] for m in g['members']) for g in p.groups.values()}
    assert areas['Planning'] == ['Fare engine', 'Planner'], areas        # primary wins over input order
    assert areas['Shared'] == ['Identity'], areas                         # two areas, no primary
    assert areas['Fares'] == ['Bus'], areas                               # two capabilities of one area
    assert areas['Not required by a capability'] == ['Orphan'], areas
    assert list(areas)[-2:] == ['Shared', 'Not required by a capability']
    assert '+1 area' in xml
    assert 'value="Pricing"' not in xml and 'edgyType=capability' not in xml, 'capabilities are the areas'
    assert not [f for f in _lint(xml) if f[0] in ('W106', 'E008', 'W111')]
    # deterministic: the same page twice gives the same drawing
    p2 = parse_document(text)[0][1]
    assert p2.generate_xml() == p2.generate_xml()


def test_owner_and_integration_checks():
    base = '''map_type: application
{own}
elements:
  - asset: "Shop" {{id: A-1, kind: application}}
  - asset: "Engine" {{id: A-2, kind: application, owner: ORG-1}}
relationships:
  - "A-2" -> "A-1": "transfers"
'''
    p = parse_document(base.format(own=''))[0][1]
    p.generate_xml()
    assert any(n.startswith('W124') and 'Shop' in n for n in p.notes), p.notes
    assert not any(w.startswith('W124') for w in p.warnings)
    assert any(w.startswith('W125') for w in p.warnings)
    q = parse_document(base.format(own='ownership: required'))[0][1]
    q.generate_xml()
    assert any(w.startswith('W124') for w in q.warnings)


def test_edges_none_counts_integrations():
    rels = '\n'.join(f'  - "A-{i}" -> "A-{i + 1}": "transfers" {{data: D-1}}' for i in range(1, 15))
    els = '\n'.join(f'  - asset: "App {i}" {{id: A-{i}, kind: application}}' for i in range(1, 16))
    text = f'map_type: application\nelements:\n{els}\n  - asset: "Data" {{id: D-1, kind: data}}\nrelationships:\n{rels}\n'
    pages, xml = _xml(text)
    assert 'transfers' not in xml and '↔ 2' in xml, 'above 12 integrations the cards count them'
    assert any('edges: direct draws them' in n for n in pages[0][1].notes)
    pages, xml = _xml(text.replace('map_type: application', 'map_type: application\nedges: direct'))
    assert xml.count('>transfers<') + xml.count('value="transfers') >= 14


def test_process_chain_bands_levels_and_w126():
    pages, xml = _xml(_example('process-chain-map.txt'))
    cells = _cells(xml)
    assert cells['Plan services'][1] == cells['Sell travel'][1], 'L1 of a band in one row'
    assert cells['Plan the network'][0] == cells['Plan services'][0] and cells['Plan the network'][1] > cells['Plan services'][1]
    assert cells['Steer the network'][1] < cells['Plan services'][1] < cells['Settle revenue'][1], 'management, core, support'
    for band in ('Management processes', 'Core processes', 'Support processes'):
        assert f'value="{band}"' in xml
    assert '>contains<' not in xml and 'value="contains"' not in xml
    assert not _lint(xml)
    bad = '''map_type: process
process_view: chain
elements:
  - process: "A" {id: P-1, band: core}
  - process: "B" {id: P-2}
  - process: "A1" {id: P-3, band: support}
  - process: "A11" {id: P-4}
relationships:
  - "P-1" -> "P-3": "contains"
  - "P-3" -> "P-4": "contains"
'''
    p = parse_document(bad)[0][1]
    xml2 = p.generate_xml()
    w126 = [w for w in p.warnings if w.startswith('W126')]
    assert any("'B'" in w for w in w126) and any("'A1'" in w and 'support' in w for w in w126), w126
    assert 'A11' not in xml2 and any('L3' in n for n in p.notes)
    p3 = parse_document(bad.replace('process_view: chain', 'process_view: chain\ndepth: 3'))[0][1]
    assert 'A11' in p3.generate_xml()


def test_swimlane_lanes_staircase_and_chips():
    pages, xml = _xml(_example('process-swimlane-map.txt'))
    cells = _cells(xml)
    steps = ['Request a refund', 'Check the ticket', 'Approve the refund', 'Pay the refund', 'Confirm to the passenger']
    xs = [cells[s][0] for s in steps]
    assert xs == sorted(xs) and len(set(xs)) == len(xs), 'input order → staircase columns'
    assert cells['Check the ticket'][1] == cells['Approve the refund'][1] < cells['Pay the refund'][1]
    for actor in ('Passengers', 'Customer service', 'Finance'):
        assert actor not in cells and f'value="{actor}"' in xml, 'actors are lanes, not boxes'
    assert '▸ Fare engine · CRM' in xml and 'CRM' not in cells, 'required assets are chips'
    assert 'performs' not in xml and 'requires' not in xml
    assert not _lint(xml)


def test_s013_is_a_question():
    t = '''map_type: application
elements:
  - capability: "Ticketing" {id: CAP-05}
  - asset: "Ticketing" {id: APP-05, kind: application}
  - asset: "Fare engine" {id: APP-07, kind: application}
relationships:
  - "CAP-05" -> "APP-05": "requires"
  - "CAP-05" -> "APP-07": "requires"
'''
    f = [x for x in edgy_semantic_review.review_text(t) if x['rule'] == 'S013']
    assert [x['name'] for x in f] == ['Ticketing'] and f[0]['level'] == 'info' and 'question only' in f[0]['question']


def test_views_from_the_model_end_to_end():
    m2t = os.path.join(REPO, 'skills', 'architecture', 'edgy-assessment', 'scripts', 'edgy_model_to_txt.py')
    model = os.path.join(REPO, 'skills', 'architecture', 'edgy-assessment', 'examples', 'architecture-model.json')
    tmp = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, m2t, model, '--views', 'application,process-chain,process-swimlane',
                        '--out', tmp, '--prefix', 'acme'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    text = open(os.path.join(tmp, 'acme-views.txt'), encoding='utf-8').read()
    assert 'draw: false' in text and text.count('  - name: ') == 4
    pages, graph = parse_document(text, with_graph=True)
    names = [n for n, _ in pages]
    assert names[:2] == ['Application map', 'Process landscape'], names
    swims = [n for n in names[2:] if n.startswith('Process swimlanes · PRO-')]
    assert swims and len(swims) == len(names) - 2, names       # one swimlane page per L1 process (where: top)
    assert all(not p.errors for _, p in pages), [p.errors for _, p in pages]
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
    assert not _lint(xml), _lint(xml)
    occ = {o['page'] for e in graph.to_json()['elements'] if e['id'] == 'APP-07' for o in e['occurrences']}
    assert occ == {'Application map'}, occ          # a derived page is an occurrence (presenter counters)
    for _n, swim in pages[2:]:
        assert not [g for g in swim.groups.values() if g['name'] == 'No performer'], 'leaf steps all have performers'
    sell = dict(pages)['Process swimlanes · PRO-20 Sell travel']
    procs = {e.get('ref') for e in sell.elements.values() if e['type'] == 'process'}
    assert procs <= {'PRO-20', 'PRO-21', 'PRO-22'} and {'PRO-21', 'PRO-22'} <= procs, procs
    bad = subprocess.run([sys.executable, m2t, model, '--views', 'nope', '--out', tmp], capture_output=True, text=True)
    assert bad.returncode == 2 and 'unknown view' in bad.stderr


def test_capability_view_bands_gaps_and_matrices():
    pages, xml = _xml(_example('capability-view-map.txt'))
    assert [n for n, _ in pages] == ['Capability · CAP-05 Sales in every channel',
                                     'Capability · CAP-06 Validation and inspection', 'Capability × application', 'CRUD']
    assert not _lint(xml), _lint(xml)
    cap = pages[0][1]
    assert cap.model_gaps == [{'rule': 'W127', 'element_id': 'CAP-05', 'band': 'products', 'status': 'out_of_scope'}]
    assert not cap.warnings and any('W127' in n for n in cap.notes)   # a known gap is a note, not a warning
    first = build_mxfile([(pages[0][0], pages[0][1].generate_xml())])
    c = _cells(first)
    centre = c['Sales in every channel']
    assert c['Fares team'][1] < centre[1], 'actors above the capability'
    assert c['Sell in every channel'][0] < centre[0], 'processes left of the capability'
    assert c['Fare engine'][0] > centre[0], 'resources right of the capability'
    assert c['Sales ledger'][1] > centre[1], 'data below the capability'
    assert 'Inspect tickets' not in c, 'only the focus capability\'s neighbourhood is drawn'
    cells = re.findall(r'value="([^"]{1,4})"[^>]*edgyRole=matrix', xml)
    assert cells == ['●', '◉', '●', '●', 'R', 'CU', 'C', 'R'], cells


def test_capability_view_unknown_gap_warns_and_qa_records_it():
    text = _example('capability-view-map.txt').replace('gaps: "products=out_of_scope"}', '}', 1)
    pages, _xml_ = _xml(text)
    cap = pages[0][1]
    assert cap.model_gaps[0]['status'] == 'not_investigated'
    assert any(w.startswith('W127') for w in cap.warnings), cap.warnings
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, 'cv.txt')
    open(src, 'w', encoding='utf-8').write(text)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_generator.py'), src, '--output',
                        os.path.join(tmp, 'cv.drawio'), '--qa'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    qa = json.load(open(os.path.join(tmp, 'cv.qa.json'), encoding='utf-8'))
    assert ('CAP-05', 'products', 'not_investigated') in {(g['element_id'], g['band'], g['status']) for g in qa['model_gaps']}
    assert any('matrix:' in n for n in qa['generator_notes'])
    val = os.path.join(REPO, 'tools', 'validate-edgy-model.py')
    schema = os.path.join(SKILL, 'assets', 'qa.schema.json')
    v = subprocess.run([sys.executable, val, os.path.join(tmp, 'cv.qa.json'), '--schema', schema],
                       capture_output=True, text=True)
    assert v.returncode == 0, v.stdout + v.stderr


def test_capability_views_from_the_model():
    m2t = os.path.join(REPO, 'skills', 'architecture', 'edgy-assessment', 'scripts', 'edgy_model_to_txt.py')
    model = os.path.join(REPO, 'skills', 'architecture', 'edgy-assessment', 'examples', 'architecture-model.json')
    tmp = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, m2t, model, '--views', 'capability,capability-matrix,crud-matrix',
                        '--out', tmp, '--prefix', 'acme'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    pages = parse_document(open(os.path.join(tmp, 'acme-views.txt'), encoding='utf-8').read())
    names = [n for n, _ in pages]
    assert sum(n.startswith('Capability · ') for n in names) >= 2 and names[-2:] == ['Capability × application', 'Process × data (CRUD)'], names
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
    assert not [f for f in _lint(xml) if f[1] == 'error'], _lint(xml)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} architecture view tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
