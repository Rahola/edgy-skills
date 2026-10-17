#!/usr/bin/env python3
"""Tests for the presenter-lite (edgy_present.py, plan F6a) and the native SVG it inlines.

Static checks always run: the HTML is self-contained (no http(s) src / href,
no network API in the script), the CSP pins the inline script and style by
their sha256, the embedded graph and view list parse, every draw.io page is
one view, hostile labels and styles render inert, the size budget holds.

The browser self-test opens presentation.html#selftest in headless Chrome
(`--dump-dom`, standard library only): wall → view → highlight → zoom →
search → current / target filter (and a no-op on a page without
annotations) → paging → back, with no script error. Without Chrome it is a
visible SKIP and exit 2 locally (check.sh's environment-warning code), and a
failure (exit 1) in CI ($CI set) — never a silent pass."""

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile, page_ids_of  # noqa: E402
import edgy_present  # noqa: E402
import edgy_render  # noqa: E402

DEMO = '''pages:
  - name: "Capabilities"
    map_type: capability
    elements:
      - capability: "Ticketing" {id: CAP-05, change: keep}
      - capability: "Account-based travel" {id: CAP-03, change: new}
      - capability: "Paper tickets" {id: CAP-02, change: remove}
      - capability: "Open loop" {id: CAP-04, change: decide}
    relationships:
      - "CAP-05" -> "CAP-03": "contains"
  - name: "Applications"
    map_type: asset
    elements:
      - asset: "Fare engine" {id: AST-02, kind: application}
      - asset: "Fare rules" {id: AST-07, kind: data}
      - capability: "Ticketing" {id: CAP-05}
    relationships:
      - "CAP-05" -> "AST-02": "requires"
      - "AST-02" -> "AST-07": "stores"
  - name: "Journey"
    elements:
      - journey: "Buy a ticket" {id: JRN-01}
      - task: "Pay" {id: TSK-01}
      - product: "Single ticket" {id: PRD-01}
      - capability: "Ticketing" {id: CAP-05}
    relationships:
      - "TSK-01" -> "JRN-01": "is part of"
      - "PRD-01" -> "TSK-01": "serves"
      - "PRD-01" -> "CAP-05": "requires"
  - name: "Trace"
    map_type: trace
    expand: trace
  - name: "Fare engine context"
    notation: c4
    level: context
    system: AST-02
'''


def _build(text=DEMO, title='Acme Transit'):
    tmp = tempfile.mkdtemp()
    pages, graph = parse_document(text, with_graph=True)
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages], page_ids=page_ids_of(pages))
    drawio = os.path.join(tmp, 'demo.drawio')
    open(drawio, 'w', encoding='utf-8').write(xml)
    html, stats = edgy_present.build(drawio, graph.to_json(), title)
    out = os.path.join(tmp, 'demo.html')
    open(out, 'w', encoding='utf-8').write(html)
    return html, stats, out, drawio


def _inline(html, tag):
    return [m for m in re.findall(rf'<{tag}>(.*?)</{tag}>', html, re.S)]


def test_self_contained_and_pinned_by_csp():
    html, stats, _out, _d = _build()
    assert not re.search(r'''(?:src|href)\s*=\s*["']?\s*(?:https?:)?//''', html), 'no remote src / href'
    script = _inline(html, 'script')
    style = _inline(html, 'style')
    assert len(script) == 1 and len(style) == 1, (len(script), len(style))
    js = script[0]
    for api in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'sendBeacon', 'eval(', 'new Function', 'document.write'):
        assert api not in js, api
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1).replace('&#x27;', "'")
    def sha(t):
        return "'sha256-" + base64.b64encode(hashlib.sha256(t.encode()).digest()).decode() + "'"
    assert f"script-src {sha(js)}" in csp and f"style-src {sha(style[0])}" in csp, csp
    assert "connect-src 'none'" in csp and "default-src 'none'" in csp and "form-action 'none'" in csp
    assert 'style="' not in html.split('<template')[0], 'no style attribute in the markup (CSP blocks them)'


def test_graph_and_views_are_embedded():
    html, stats, _out, _d = _build()
    graph = json.loads(re.search(r'<script type="application/json" id="edgy-graph">(.*?)</script>', html, re.S).group(1))
    views = json.loads(re.search(r'<script type="application/json" id="edgy-views">(.*?)</script>', html, re.S).group(1))
    assert graph['contract'] == 1 and {e['id'] for e in graph['elements']} >= {'CAP-05', 'AST-02', 'AST-07'}
    plain = [v for v in views if not v.get('trace')]
    assert [v['name'] for v in plain] == ['Capabilities', 'Applications', 'Journey', 'Fare engine context']
    assert len(re.findall(r'<template id="view-\d+">', html)) == len(views)
    assert views[0]['changes'] and not views[1]['changes']
    cap = next(e for e in graph['elements'] if e['id'] == 'CAP-05')
    assert {'capabilities', 'applications', 'journey'} <= {o['page_id'] for o in cap['occurrences']}
    # realisation trace (2.9.0): the index, one page per element with its focus; ids are not page names
    trace = {v['page_id']: v for v in views if v.get('trace')}
    assert trace['trace-index']['trace'] == 'index'
    assert {'JRN-01', 'TSK-01', 'PRD-01', 'CAP-05'} <= {v['focus'] for v in trace.values() if v['trace'] == 'page'}
    assert trace['trace-jrn-01'] == {**trace['trace-jrn-01'], 'trace': 'page', 'focus': 'JRN-01'}
    assert 'data-link="trace-tsk-01"' in html and 'data-trace="focus"' in html


def test_graph_from_cells_without_graph_json():
    _html, _stats, _out, drawio = _build()
    html, _ = edgy_present.build(drawio)
    graph = json.loads(re.search(r'id="edgy-graph">(.*?)</script>', html, re.S).group(1))
    assert any(r['source'] == 'CAP-05' and r['target'] == 'AST-02' and r['verb'] == 'requires' for r in graph['relationships'])


def test_svg_groups_follow_the_contract():
    pages = parse_document(DEMO)
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
    tmp = os.path.join(tempfile.mkdtemp(), 'x.drawio')
    open(tmp, 'w', encoding='utf-8').write(xml)
    from edgy_document import load_pages_from_file
    name, model = load_pages_from_file(tmp)[0]
    svg = edgy_render.page_to_svg(edgy_render.Page(model), name)
    els = re.findall(r'<g class="el" ([^>]*)>', svg)
    assert len(els) == 4 and all('data-id=' in a and 'data-occ=' in a and 'data-type="capability"' in a for a in els)
    assert 'data-change="new"' in svg and 'data-change="remove"' in svg
    edges = re.findall(r'<g class="edge" ([^>]*)>', svg)
    assert edges and 'data-src="CAP-05"' in edges[0] and 'data-tgt="CAP-03"' in edges[0] and 'data-kind="tree"' in edges[0]
    assert '<g class="deco" data-role="legend">' in svg
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)          # well-formed


def test_hostile_label_and_style_render_inert():
    text = '''map_type: asset
elements:
  - asset: "<script>alert(1)</script> & <img src=x onerror=alert(4)>" {id: AST-01}
'''
    pages = parse_document(text)
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
    # a hand-edited element style: an attribute break-out in the colour and in the id
    def poison(m):
        st = m.group(0).replace('fillColor=#a6c0ff;', 'fillColor=#fff&quot; onmouseover=&quot;alert(2);')
        return st.replace('edgyId=AST-01;', 'edgyId=AST-01&quot; onclick=&quot;x;')
    xml, n = re.subn(r'style="[^"]*edgyType=asset;[^"]*"', poison, xml)
    assert n == 1 and 'onmouseover' in xml
    tmp = os.path.join(tempfile.mkdtemp(), 'h.drawio')
    open(tmp, 'w', encoding='utf-8').write(xml)
    html, _ = edgy_present.build(tmp, title='<img src=x onerror=alert(3)>')
    body = html.split('<script>')[0]
    for bad in ('<script>alert', 'onmouseover=', 'onclick=', '<img src=x', 'alert(2)', 'fill="#fff&'):
        assert bad not in body, bad
    from edgy_document import load_pages_from_file
    _n, model = load_pages_from_file(tmp)[0]
    svg = edgy_render.page_to_svg(edgy_render.Page(model), 'x')
    assert '<g class="el"' not in svg, 'an unsafe id is not a model id: the cell is drawn, not interactive'
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in svg, 'the label is shown as text'
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)


def test_size_budget():
    html, stats, _out, _d = _build()
    assert stats['bytes'] < edgy_present.budget_bytes(stats['pages']) / 5, stats
    assert edgy_present.budget_bytes(60) == 2 * edgy_present.budget_bytes(30)


def test_present_cli_and_generator_option():
    _html, _stats, _out, drawio = _build()
    out = drawio.replace('.drawio', '-p.html')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_present.py'), drawio, '-o', out], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.isfile(out), r.stderr
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_present.py'), drawio, '-o', out, '--max-mb', '0.001'],
                       capture_output=True, text=True)
    assert r.returncode == 3 and 'budget' in r.stderr
    src = os.path.join(os.path.dirname(drawio), 'in.txt')
    open(src, 'w', encoding='utf-8').write(DEMO)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_generator.py'), src, '--output',
                        os.path.join(os.path.dirname(drawio), 'g.drawio'), '--present', out], capture_output=True, text=True)
    assert r.returncode == 0 and 'Presentation:' in r.stdout, r.stderr + r.stdout


def browser_selftest():
    """'pass' | 'fail: …' | 'skip: …'"""
    chrome = edgy_render.find_chromium()
    if not chrome:
        return 'skip: no Chromium / Chrome found (set EDGY_CHROMIUM=<binary>)'
    _html, _stats, out, _d = _build()
    # a narrow window (one column, the cards taller than the wall) is where flattened cards showed up
    cmd = [chrome, '--headless', '--no-sandbox', '--disable-gpu', '--window-size=500,700', '--virtual-time-budget=15000', '--dump-dom',
           'file://' + out + '#selftest']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f'fail: {e}'
    m = re.search(r'<div id="edgy-selftest" data-result="(\w+)" data-errors="(\d+)" data-steps="([^"]*)"', r.stdout)
    if not m:
        return f'fail: no self-test sentinel in the DOM (exit {r.returncode})'
    if m.group(1) != 'pass' or m.group(2) != '0':
        return f'fail: result={m.group(1)} errors={m.group(2)} steps={m.group(3)}'
    for step in ('wall', 'wall-cards', 'view', 'highlight', 'zoom', 'search-jump', 'state-noop', 'state-current', 'state-target', 'paging',
                 'trace-card', 'drill', 'card-first-click', 'card-second-click', 'breadcrumb', 'breadcrumb-jump',
                 'history-back', 'forward', 'deeplink-restore', 'route-malformed', 'card-vs-badge', 'return-to-trace',
                 'back', 'no-errors'):
        if f'{step}:ok' not in m.group(3):
            return f'fail: step {step} missing ({m.group(3)})'
    return 'pass'


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    result = browser_selftest()
    print(f'browser self-test: {result}')
    if result.startswith('skip'):
        if os.environ.get('CI'):
            print('Test failed: the browser self-test must run in CI (GitHub runners ship Google Chrome)')
            sys.exit(1)
        print(f'\nAll {len(tests)} presenter tests passed — browser self-test SKIPPED (exit 2: environment)')
        sys.exit(2)
    if result != 'pass':
        print(f'\nTest failed: {result}')
        sys.exit(1)
    print(f'\nAll {len(tests)} presenter tests and the browser self-test passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
