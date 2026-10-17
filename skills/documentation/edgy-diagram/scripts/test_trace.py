#!/usr/bin/env python3
"""Realisation trace (edgy-diagram 2.9.0, plan v2.5.0 F7) — the exact oracles of test plan §3.0 / §3.1.

F-PATH holds every row of the F7 link table; the tests check the neighbour sets per page and band, the order,
the edges drawn (verb, direction, nothing extra, nothing missing), the link-table coverage, the navigation on the
emitted links (down and up), page sets and link closure for where:, W129 per type / key / status / direction,
stable page ids, the UserObject readers, crowded bands and the trace direction.
"""

import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['EDGY_TEXT_TABLE_ONLY'] = '1'

import edgy_trace  # noqa: E402
from edgy_document import parse_document, load_pages_from_file, unwrap_links as edgy_document_unwrap  # noqa: E402

FIX = os.path.join(HERE, 'fixtures', 'trace')
F_PATH = open(os.path.join(FIX, 'f-path.txt'), encoding='utf-8').read()

# test plan §3.0 — exact neighbours per page: (above, centre, below), in band order
F_PATH_TABLE = {
    'JRN-01': ([], [], ['TSK-01', 'CH-01', 'PRD-01']),
    'TSK-01': (['JRN-01'], ['CH-01'], ['PRD-01']),
    'CH-01': (['JRN-01'], ['TSK-01'], ['PRD-01']),
    'PRD-01': (['JRN-01', 'TSK-01', 'CH-01'], [], ['CAP-01', 'PRO-01', 'ORG-01']),
    'CAP-01': (['PRD-01'], [], ['PRO-01', 'APP-01', 'ORG-01']),
    'PRO-01': (['PRD-01', 'CAP-01'], ['APP-01', 'DAT-01'], ['ORG-01']),
    'APP-01': (['CAP-01'], ['PRO-01', 'PPL-01'], ['ORG-01']),
    'DAT-01': ([], ['PRO-01'], ['ORG-01']),
    'PPL-01': ([], ['APP-01'], ['ORG-01']),
    'ORG-01': (['PRD-01', 'CAP-01', 'PRO-01', 'APP-01', 'DAT-01', 'PPL-01'], [], []),
}
LEVEL_OF = {'JRN-01': 1, 'TSK-01': 2, 'CH-01': 2, 'PRD-01': 3, 'CAP-01': 4, 'PRO-01': 5, 'APP-01': 5, 'DAT-01': 5,
            'PPL-01': 5, 'ORG-01': 6}


def with_trace(text, *view_lines):
    """F-PATH with extra view lines on the Trace page (where:, trace_direction: …)."""
    return text.replace('    expand: trace', '    expand: trace' + ''.join('\n    ' + v for v in view_lines))


def model_extra(text, elements=(), relationships=()):
    for e in elements:
        text = text.replace('    relationships:\n', f'      {e}\n    relationships:\n', 1)
    for r in relationships:
        text = text.replace('  - name: "Trace"', f'      {r}\n  - name: "Trace"', 1)
    return text


def pages_of(text):
    return {p.view.get('focus') or ('index' if p.view.get('trace_index') else '?'): (n, p)
            for n, p in parse_document(text) if p.map_type == 'trace' and not p.view.get('trace_list')}


def bands(parser):
    out = {'above': [], 'centre': [], 'below': []}
    for e in parser.elements.values():
        b = (e.get('attrs') or {}).get('tband')
        if b in out:
            out[b].append(e['ref'])
    return out


def generate(text, extra=()):
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, 'in.txt')
    open(src, 'w', encoding='utf-8').write(text)
    out = os.path.join(tmp, 'out.drawio')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_generator.py'), src, '--output', out, '--qa', *extra],
                       capture_output=True, text=True, timeout=300,
                       env={**os.environ, 'EDGY_TEXT_TABLE_ONLY': '1'})
    assert r.returncode == 0, r.stdout + r.stderr
    qa = json.load(open(os.path.join(tmp, 'out.qa.json'), encoding='utf-8'))
    raw = open(out, encoding='utf-8').read()
    return out, raw, qa, r.stdout + r.stderr


def page_cells(path):
    """{page id: {'cards': {model id: cell}, 'edges': [(src id, verb, tgt id)], 'links': {model id: target}}}"""
    ids = re.findall(r'<diagram id="([^"]+)"', open(path, encoding='utf-8').read())
    out = {}
    for pid, (_name, model) in zip(ids, load_pages_from_file(path)):
        cells = {c.get('id'): c for c in model.find('root').findall('mxCell')}
        cards, links = {}, {}
        for cid, c in cells.items():
            m = re.search(r'edgyId=([^;]+);', c.get('style') or '')
            if c.get('vertex') == '1' and m:
                cards[m.group(1)] = cid
                if c.get('link'):
                    links[m.group(1)] = c.get('link').split(',', 1)[1]
        by_cell = {v: k for k, v in cards.items()}
        edges = []
        for c in cells.values():
            if c.get('edge') == '1' and c.get('source') in by_cell and c.get('target') in by_cell:
                verb = re.sub(r'<[^>]+>.*', '', c.get('value') or '').strip()
                edges.append((by_cell[c.get('source')], verb, by_cell[c.get('target')]))
        more = [c for c in cells.values() if 'edgyRole=more' in (c.get('style') or '')]
        out[pid] = {'cards': cards, 'edges': edges, 'links': links, 'more': more}
    return out


# ---- T01 bands, T03 order ------------------------------------------------------------------------------------

def test_t01_t03_neighbour_sets_and_order():
    pages = pages_of(F_PATH)
    assert set(pages) == set(F_PATH_TABLE) | {'index'}, sorted(pages)
    for mid, (above, centre, below) in F_PATH_TABLE.items():
        b = bands(pages[mid][1])
        assert b == {'above': above, 'centre': centre, 'below': below}, (mid, b)
    # same-type contains is a chip, never a band edge (F-CYCLE has the chips)
    assert all(not p.trace_chips[0] and not p.trace_chips[1] for _n, p in pages.values())


# ---- T02 edges and the whitelist --------------------------------------------------------------------------------

def _input_edges(text):
    rels = re.findall(r'^\s*- "([^"]+)" -> "([^"]+)": "([^"]+)"', text, re.M)
    return {(s, v, t) for s, t, v in rels}


def test_t02_edges_whitelist_and_link_table_coverage():
    path, _raw, qa, _out = generate(F_PATH)
    cells = page_cells(path)
    inputs = _input_edges(F_PATH)
    drawn = set()
    for pid, page in cells.items():
        for s, v, t in page['edges']:
            assert (s, v, t) in inputs, (pid, s, v, t)          # verb and direction as in the input
            drawn.add((s, v, t))
        on_page = set(page['cards'])
        if pid == 'trace-index':
            continue
        focus = next(m for m in on_page if edgy_trace.page_id(m) == pid)
        for s, v, t in inputs:
            if focus in (s, t) and s in on_page and t in on_page:
                assert (s, v, t) in page['edges'], (pid, s, v, t)   # nothing missing
    assert drawn == inputs, inputs - drawn
    # link-table coverage: (verb, source level, target level) drawn == the rows of the table
    types = {m: edgy_trace.LEVEL and t for m, t in (('JRN-01', 'journey'), ('TSK-01', 'task'), ('CH-01', 'channel'),
             ('PRD-01', 'product'), ('CAP-01', 'capability'), ('PRO-01', 'process'), ('APP-01', 'asset'),
             ('DAT-01', 'asset'), ('PPL-01', 'people'), ('ORG-01', 'organisation'))}
    assert {(types[s], v, types[t]) for s, v, t in drawn} == edgy_trace.LINK_ROWS
    assert qa['totals']['lint_errors'] == 0 and qa['totals']['lint_warnings'] == 0, qa['totals']
    assert qa['totals']['visual'] == 0 and qa['totals']['layout_quality'] == 0, qa['totals']


def test_link_table_rows():
    """The traversal walks exactly the plan's link table, in every language of the vocabulary."""
    assert len(edgy_trace.LINK_ROWS) == 18
    for verb in ('is part of', 'on osa', 'fait partie de', 'ist Teil von', 'serves', 'palvelee', 'realises',
                 'toteuttaa', 'performs', 'suorittaa', 'interacts with', 'asioi', 'offers', 'tarjoaa'):
        assert edgy_trace.canon(verb), verb
    assert edgy_trace.canon('transfers') is None and edgy_trace.canon('flows') is None


def test_people_process_and_flows_never_drawn():
    """F-PATH-NEG: people → process performs (E010 in the input) and a flow add no edge; the neighbour sets stay."""
    text = model_extra(F_PATH, elements=['- asset: "Fare engine" {id: APP-02, kind: application}'],
                       relationships=['- "PPL-01" -> "PRO-01": "performs"',
                                      '- "APP-01" -> "APP-02": "transfers"'])
    pages = pages_of(text)
    for mid, (above, centre, below) in F_PATH_TABLE.items():
        assert bands(pages[mid][1]) == {'above': above, 'centre': centre, 'below': below}, mid
    # an asset reached only by a flow has its own page, with no trace neighbours: the flow is never walked
    assert bands(pages['APP-02'][1]) == {'above': [], 'centre': [], 'below': []}


# ---- T04 navigation on the emitted links -------------------------------------------------------------------------

def test_t04_navigation_down_and_up_on_emitted_links():
    path, raw, _qa, _out = generate(F_PATH)
    cells = page_cells(path)
    page_ids = set(cells)
    for pid, page in cells.items():
        for target in page['links'].values():
            assert target in page_ids, (pid, target)                 # every link resolves
        # converse: every card whose page exists carries its link
        for mid in page['cards']:
            if edgy_trace.page_id(mid) in page_ids and edgy_trace.page_id(mid) != pid:
                assert mid in page['links'], (pid, mid)

    def walk(start, goal, pick):
        cur, steps = start, 0
        while cur != goal and steps < 10:
            page = cells[edgy_trace.page_id(cur)]
            cur = pick([m for m in page['links'] if m != cur])
            steps += 1
        return steps if cur == goal else None
    down = walk('JRN-01', 'ORG-01', lambda ms: max(ms, key=lambda m: (LEVEL_OF[m], m == 'ORG-01' or
                                                                        m in ('TSK-01', 'PRD-01', 'CAP-01', 'PRO-01'))))
    assert down is not None and down <= 6, down
    up = walk('ORG-01', 'JRN-01', lambda ms: min(ms, key=lambda m: LEVEL_OF[m]))
    assert up is not None, up
    # level ladder: a page at every level 1–6
    assert {LEVEL_OF[m] for m in LEVEL_OF if edgy_trace.page_id(m) in page_ids} == {1, 2, 3, 4, 5, 6}


# ---- T05 page set and link closure ----------------------------------------------------------------------------------

def _unlinked_total(path):
    cells = page_cells(path)
    n = 0
    for pid, page in cells.items():
        if pid == 'trace-index':
            continue
        n += sum(1 for m in page['cards'] if edgy_trace.page_id(m) != pid and m not in page['links'])
    return cells, n


def test_t05_page_sets_and_unlinked_cards():
    cases = [
        (['where: CAP-01, APP-01'], {'trace-index', 'trace-cap-01', 'trace-app-01'}, 6),
        # same-level links are walked too (phase 4, S02): the channel, the data and the people join the set
        (['where: from TSK-01'], {'trace-index'} | {edgy_trace.page_id(m) for m in
                                                    ('TSK-01', 'CH-01', 'PRD-01', 'CAP-01', 'PRO-01', 'APP-01',
                                                     'DAT-01', 'PPL-01', 'ORG-01')}, 3),
        (['where: from ORG-01', 'trace_direction: up'], {'trace-index'} | {edgy_trace.page_id(m) for m in LEVEL_OF}, 0),
    ]
    for lines, expected_pages, unlinked in cases:
        path, _raw, qa, _out = generate(with_trace(F_PATH, *lines))
        cells, n = _unlinked_total(path)
        assert set(cells) == expected_pages, (lines, sorted(cells))
        assert n == unlinked, (lines, n)
        notes = ' '.join(qa['generator_notes'])
        assert 'trace page(s)' in notes, notes
        if unlinked:
            assert 'without a page' in notes, notes
    # where: highlight, and an element without an id is skipped with a note (never an error)
    text = F_PATH.replace('{id: CAP-01}', '{id: CAP-01, highlight: yes}')
    text = model_extra(text, elements=['- task: "Pay"'])
    path, _raw, qa, _out = generate(with_trace(text, 'where: highlight'))
    assert set(page_cells(path)) == {'trace-index', 'trace-cap-01'}
    assert any('without an id skipped' in n for n in qa['generator_notes']), qa['generator_notes']


def test_algorithm_fixtures():
    """F-CYCLE (bounded, contains cycle reported, chips once), F-SHARED, F-LONE."""
    cyc = '''pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "A" {id: CAP-A}
      - capability: "B" {id: CAP-B}
      - asset: "One" {id: APP-1, kind: application}
      - process: "P1" {id: PRO-1}
      - process: "P2" {id: PRO-2}
    relationships:
      - "CAP-A" -> "APP-1": "requires"
      - "CAP-B" -> "APP-1": "requires"
      - "PRO-1" -> "CAP-A": "realises"
      - "PRO-1" -> "CAP-B": "realises"
      - "PRO-1" -> "APP-1": "requires"
      - "PRO-1" -> "PRO-2": "contains"
      - "PRO-2" -> "PRO-1": "contains"
  - name: "Trace"
    map_type: trace
    expand: trace
'''
    t0 = time.time()
    pages = parse_document(cyc)
    assert time.time() - t0 < 10
    ids = {p.page_id for _n, p in pages}
    assert ids == {'trace-index', 'trace-cap-a', 'trace-cap-b', 'trace-app-1', 'trace-pro-1', 'trace-pro-2'}, ids
    index = next(p for _n, p in pages if p.page_id == 'trace-index')
    assert any('contains cycle' in w and 'PRO-1' in w and 'PRO-2' in w for w in index.warnings), index.warnings
    p1 = next(p for _n, p in pages if p.page_id == 'trace-pro-1')
    assert p1.trace_chips == (['P2'], ['P2']), p1.trace_chips
    shared = model_extra(F_PATH, elements=['- capability: "Payments" {id: CAP-02}'],
                         relationships=['- "CAP-02" -> "APP-01": "requires"'])
    assert bands(pages_of(shared)['APP-01'][1])['above'] == ['CAP-01', 'CAP-02']
    lone = model_extra(F_PATH, elements=['- task: "Refund" {id: TSK-09}'])
    p = pages_of(lone)['TSK-09'][1]
    p.generate_xml()
    assert bands(p) == {'above': [], 'centre': [], 'below': []}
    assert p.model_gaps == [{'rule': 'W129', 'element_id': 'TSK-09', 'band': 'products',
                             'status': 'not_investigated'}], p.model_gaps
    assert any(w.startswith('W129 TSK-09') for w in p.warnings), p.warnings


# ---- T06 W129 parameterised ------------------------------------------------------------------------------------------

LONE = {'journey': 'journey: "J" {id: X-1%s}', 'task': 'task: "T" {id: X-1%s}', 'channel': 'channel: "C" {id: X-1%s}',
        'product': 'product: "P" {id: X-1%s}', 'capability': 'capability: "K" {id: X-1%s}',
        'process': 'process: "R" {id: X-1%s}', 'asset': 'asset: "A" {id: X-1, kind: application%s}',
        'people': 'people: "E" {id: X-1%s}', 'organisation': 'organisation: "O" {id: X-1%s}'}


def _lone_page(etype, gaps=None, direction='both'):
    g = f', gaps: "{gaps}"' if gaps else ''
    text = f'''pages:
  - name: "Model"
    draw: false
    elements:
      - {LONE[etype] % g}
  - name: "Trace"
    map_type: trace
    trace_direction: {direction}
    expand: trace
'''
    p = next(p for _n, p in parse_document(text) if p.view.get('focus') == 'X-1')
    p.generate_xml()
    return p


def test_t06_w129_per_type_key_status_direction():
    for etype in LONE:
        checked = edgy_trace.W129_KEYS.get(etype, ())
        p = _lone_page(etype)
        assert [g['band'] for g in p.model_gaps] == list(checked), (etype, p.model_gaps)
        for status, is_note in (('not_investigated', False), ('unknown', False), ('out_of_scope', True),
                                ('confirmed_absent', True)):
            for key in checked:
                p = _lone_page(etype, f'{key}={status}')
                gap = next(g for g in p.model_gaps if g['band'] == key)
                assert gap['status'] == status, (etype, key, gap)
                hit_w = [w for w in p.warnings if w.startswith('W129') and f'no {key} below' in w]
                hit_n = [n for n in p.notes if n.startswith('W129') and f'no {key} below' in n]
                assert (bool(hit_n), bool(hit_w)) == (is_note, not is_note), (etype, key, status, p.warnings, p.notes)
        assert not _lone_page(etype, direction='up').model_gaps, etype
        if checked:
            assert len(_lone_page(etype, direction='down').model_gaps) == len(checked)
    # same-level only: a process with an asset beside it still lacks its organisation
    text = '''pages:
  - name: "Model"
    draw: false
    elements:
      - process: "R" {id: X-1}
      - asset: "A" {id: X-2, kind: application}
    relationships:
      - "X-1" -> "X-2": "requires"
  - name: "Trace"
    map_type: trace
    expand: trace
'''
    p = next(p for _n, p in parse_document(text) if p.view.get('focus') == 'X-1')
    p.generate_xml()
    assert [g['band'] for g in p.model_gaps] == ['organisation'], p.model_gaps


# ---- T07 stable ids --------------------------------------------------------------------------------------------------

def test_t07_stable_ids():
    assert edgy_trace.page_id('CAP-05') == 'trace-cap-05'
    assert edgy_trace.page_id('APP/07') == 'trace-app-07-11f8e4'
    assert edgy_trace.page_id('CAP:05') == 'trace-cap-05-7f4c7a'
    renamed = F_PATH.replace('"Trip sales" {id: CAP-01}', '"Sales in every channel" {id: CAP-01}')
    a = sorted(p.page_id for _n, p in parse_document(F_PATH))
    b = sorted(p.page_id for _n, p in parse_document(renamed))
    assert a == b, (a, b)
    clash = F_PATH.replace('  - name: "Trace"', '''  - name: "Trace CAP 01"
    elements:
      - capability: "Trip sales" {id: CAP-01}
  - name: "Trace"''')
    ids = [p.page_id for _n, p in parse_document(clash)]
    assert 'trace-cap-01' in ids and 'trace-cap-01-2' in ids, ids


# ---- T08 readers see linked cards -----------------------------------------------------------------------------------

def test_t08_userobject_readers():
    path, raw, _qa, _out = generate(F_PATH, extra=('--preview',))
    assert raw.count('<UserObject') > 0
    sys.path.insert(0, HERE)
    import edgy_lint
    import edgy_present
    import edgy_render
    lint_cards = 0
    for _name, model in edgy_lint.load_models(path):
        cells = {c.get('id'): c for c in model.find('root').findall('mxCell')}
        lint_cards += len(edgy_lint.classify_cells(cells)['elements'])
    render_cards = sum(1 for _n, m in load_pages_from_file(path) for c in m.find('root').findall('mxCell')
                       if 'edgyId=' in (c.get('style') or '') and c.get('vertex') == '1')
    present = edgy_present.graph_from_drawio(edgy_present.read_drawio(path))
    occ = sum(len(e['occurrences']) for e in present['elements'])
    assert lint_cards == render_cards == occ, (lint_cards, render_cards, occ)
    pinned = sum(1 + sum(len(x) for x in F_PATH_TABLE[m]) for m in F_PATH_TABLE) + 2   # pages + index (JRN, ORG)
    assert render_cards == pinned, (render_cards, pinned)
    svg = open(path.replace('.drawio', '-trace-cap-01-trip-sales.svg'), encoding='utf-8').read()
    assert svg.count('class="el"') == 1 + sum(len(x) for x in F_PATH_TABLE['CAP-01'])


# ---- T09 crowded bands ----------------------------------------------------------------------------------------------

def f_wide():
    prods = ''.join(f'      - product: "Fare {c}" {{id: PRD-{c}}}\n' for c in 'ABCDEFGHIJKLMNO')
    reqs = ''.join(f'      - "PRD-{c}" -> "CAP-W": "requires"\n' for c in 'ABCDEFGHIJKLMNO')
    return f'''pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "Wide" {{id: CAP-W}}
      - process: "Do" {{id: PRO-W}}
      - asset: "Tool" {{id: APP-W, kind: application}}
      - organisation: "Team" {{id: ORG-W}}
{prods}    relationships:
      - "PRO-W" -> "CAP-W": "realises"
      - "CAP-W" -> "APP-W": "requires"
      - "ORG-W" -> "CAP-W": "has"
      - "ORG-W" -> "PRO-W": "performs"
      - "ORG-W" -> "APP-W": "manages"
{reqs}  - name: "Trace"
    map_type: trace
    expand: trace
'''


def test_t09_crowded_band_and_list_page():
    path, _raw, qa, _out = generate(f_wide())
    cells = page_cells(path)
    cap = cells['trace-cap-w']
    above = sorted(m for m in cap['cards'] if m.startswith('PRD-'))
    assert above == [f'PRD-{c}' for c in 'ABCDEFGHIJK'], above
    assert len(cap['more']) == 1 and '+4' in (cap['more'][0].get('value') or '')
    assert cap['more'][0].get('link') == 'data:page/id,trace-cap-w-more-above'
    lst = cells['trace-cap-w-more-above']
    assert sorted(m for m in lst['cards'] if m.startswith('PRD-')) == [f'PRD-{c}' for c in 'ABCDEFGHIJKLMNO']
    assert any('4 card(s) hidden on trace-cap-w' in n for n in qa['generator_notes']), qa['generator_notes']
    assert not [g for g in qa['model_gaps'] if g['rule'] == 'W129'], qa['model_gaps']
    t = qa['totals']
    assert (t['lint_errors'], t['lint_warnings'], t['visual'], t['layout_quality']) == (0, 0, 0, 0), t


# ---- T12 direction --------------------------------------------------------------------------------------------------

def test_t12_direction():
    for direction, keep in (('down', ('centre', 'below')), ('up', ('above', 'centre')), ('both', ('above', 'centre', 'below'))):
        pages = pages_of(with_trace(F_PATH, f'trace_direction: {direction}'))
        for mid, (above, centre, below) in F_PATH_TABLE.items():
            want = {'above': above if 'above' in keep else [], 'centre': centre, 'below': below if 'below' in keep else []}
            assert bands(pages[mid][1]) == want, (direction, mid)
        if direction == 'up':
            for _n, p in pages.values():
                p.generate_xml()
                assert not p.model_gaps, p.model_gaps


def test_from_closure_walks_same_level_links():
    """Phase 4 (S02): up from an organisation through asset → process (requires, both level 5) to the journey."""
    text = """pages:
  - name: "Model"
    draw: false
    elements:
      - journey: "Book a trip" {id: JRN-01}
      - task: "Pay" {id: TSK-01}
      - product: "Booking" {id: PRD-01}
      - capability: "Trip sales" {id: CAP-01}
      - process: "Sell trips" {id: PRO-01}
      - asset: "Booking system" {id: APP-01, kind: application}
      - organisation: "IT" {id: ORG-02}
    relationships:
      - "TSK-01" -> "JRN-01": "is part of"
      - "PRD-01" -> "TSK-01": "serves"
      - "PRD-01" -> "CAP-01": "requires"
      - "PRO-01" -> "CAP-01": "realises"
      - "PRO-01" -> "APP-01": "requires"
      - "ORG-02" -> "APP-01": "manages"
  - name: "Trace"
    map_type: trace
    expand: trace
    where: from ORG-02
    trace_direction: up
"""
    ids = {p.page_id for _, p in parse_document(text)}
    assert ids == {'trace-index'} | {edgy_trace.page_id(m) for m in
                                     ('ORG-02', 'APP-01', 'PRO-01', 'CAP-01', 'PRD-01', 'TSK-01', 'JRN-01')}, ids
    down = {p.page_id for _, p in parse_document(text.replace('where: from ORG-02', 'where: from JRN-01')
                                                 .replace('trace_direction: up', 'trace_direction: down'))}
    assert edgy_trace.page_id('APP-01') in down and edgy_trace.page_id('ORG-02') in down, down


def test_phase4_codex_ids_and_model_page_messages():
    """Codex F1: INDEX never takes the index's page id, and ids that differ only in case are an error, not two
    pages with one id. Codex F3: E010 on a draw: false model page is reported (F-PATH-NEG)."""
    base = """pages:
  - name: "Model"
    draw: false
    elements:
      - journey: "Book a trip" {id: JRN-01}
      - capability: "Reserved" {id: INDEX}
%s  - name: "Trace"
    map_type: trace
    expand: trace
"""
    pages = parse_document(base % '')
    ids = [p.page_id for _, p in pages]
    assert len(ids) == len(set(ids)) and ids.count('trace-index') == 1, ids
    assert edgy_trace.page_id('INDEX').startswith('trace-index-'), edgy_trace.page_id('INDEX')
    pages = parse_document(base % '      - capability: "A" {id: CAP-X}\n      - capability: "B" {id: cap-x}\n')
    errs = [e for _, p in pages for e in p.errors]
    assert any('would share the page id trace-cap-x' in e for e in errs), errs
    neg = F_PATH.replace('      - "PRD-01" -> "JRN-01": "features in"',
                         '      - "PRD-01" -> "JRN-01": "features in"\n      - "PPL-01" -> "PRO-01": "performs"')
    assert neg != F_PATH
    pages = parse_document(with_trace(neg))
    warns = [w for _, p in pages for w in p.warnings]
    assert any(w.startswith('[Model] E010') and 'people → process' in w for w in warns), warns


def test_views_trace_is_opt_in():
    """--views trace writes the Trace page; --views all leaves it out (a large model gives many pages)."""
    script = os.path.join(HERE, '..', '..', '..', 'architecture', 'edgy-assessment', 'scripts', 'edgy_model_to_txt.py')
    model = os.path.join(HERE, '..', '..', '..', 'architecture', 'edgy-assessment', 'examples', 'architecture-model.json')
    with tempfile.TemporaryDirectory() as tmp:
        for views, want in (('trace', True), ('all', False)):
            r = subprocess.run([sys.executable, script, model, '--views', views, '--out', tmp, '--prefix', views],
                               capture_output=True, text=True)
            assert r.returncode == 0, r.stderr
            text = open(os.path.join(tmp, f'{views}-views.txt'), encoding='utf-8').read()
            assert ('expand: trace' in text) == want, (views, text[-300:])


def test_mixed_crowded_row_splits_by_type():
    """A level row of more than ROW_SPLIT cards of several types gets one row per type (W120, eval JRN-01)."""
    lines = ['language: en', 'pages:', '  - name: "Model"', '    draw: false', '    elements:',
             '      - journey: "J" {id: JRN-01}']
    rels = []
    for k in range(1, 5):
        lines.append(f'      - task: "Task {k}" {{id: TSK-0{k}}}')
        rels.append(f'      - "TSK-0{k}" -> "JRN-01": "is part of"')
    for k in range(1, 3):
        lines.append(f'      - channel: "Channel {k}" {{id: CHA-0{k}}}')
        rels.append(f'      - "JRN-01" -> "CHA-0{k}": "traverses"')
    text = '\n'.join(lines + ['    relationships:'] + rels +
                     ['  - name: "Trace"', '    map_type: trace', '    expand: trace', '    where: JRN-01'])
    pages = parse_document(text)
    page = next(p for n, p in pages if p.page_id == 'trace-jrn-01')
    import xml.etree.ElementTree as ET
    root = edgy_document_unwrap(ET.fromstring(page.generate_xml()))
    ys = {}
    for c in root.iter('mxCell'):
        st = dict(kv.split('=', 1) for kv in (c.get('style') or '').split(';') if '=' in kv)
        if st.get('edgyType') in ('task', 'channel') and c.find('mxGeometry') is not None:
            ys.setdefault(st['edgyType'], set()).add(c.find('mxGeometry').get('y'))
    assert len(ys['task']) == 1 and len(ys['channel']) == 1 and ys['task'] != ys['channel'], ys


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} trace tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
