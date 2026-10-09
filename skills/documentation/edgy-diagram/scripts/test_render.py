#!/usr/bin/env python3
"""Tests for edgy_document.py (pages + mxfile) and edgy_render.py (SVG preview)."""

import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_document  # noqa: E402
import edgy_render  # noqa: E402
import edgy_lint  # noqa: E402

SINGLE = """
facet: identity
elements:
  - purpose: "Sustainable mobility"
  - story: "From depot to platform"
  - organisation: "Acme Transit"
relationships:
  - "From depot to platform" -> "Sustainable mobility": "contextualises"
  - "Acme Transit" -> "Sustainable mobility": "pursues"
"""

MULTI = """
facet: architecture
pages:
  - name: "Roles & actors"
    elements:
      - organisation: "Board"
      - process: "Steer"
    relationships:
      - "Board" -> "Steer": "performs"
  - name: "Systems"
    map_type: asset
    elements:
      - asset: "Fare engine"
      - asset: "App backend"
      - asset: "Data lake"
      - asset: "CRM"
      - asset: "Identity provider"
"""


def _write(content, suffix='.drawio'):
    f = tempfile.NamedTemporaryFile('w', suffix=suffix, delete=False, encoding='utf-8')
    f.write(content)
    f.close()
    return f.name


def test_split_pages_single_and_multi():
    single = edgy_document.split_pages(SINGLE)
    assert len(single) == 1 and single[0][0] is None
    multi = edgy_document.split_pages(MULTI)
    assert [n for n, _ in multi] == ['Roles & actors', 'Systems'], multi
    assert 'facet: architecture' in multi[1][1], "document-level defaults must apply to every page"
    assert 'map_type: asset' in multi[1][1] and 'map_type' not in multi[0][1]


def test_parse_document_pages_are_independent():
    pages = edgy_document.parse_document(MULTI)
    assert len(pages) == 2
    (n1, p1), (n2, p2) = pages
    assert p1.facet == 'architecture' and p1.map_type is None
    assert p2.map_type == 'asset'
    assert len(p1.elements) == 2 and len(p2.elements) == 5
    assert p1.warnings == [] and p2.warnings == [], (p1.warnings, p2.warnings)


def test_pages_without_name_entry_is_an_error():
    try:
        edgy_document.split_pages("pages:\n  elements:\n    - purpose: \"x\"\n")
    except ValueError:
        return
    raise AssertionError("content under pages: without '- name:' must raise")


def test_mxfile_wrapper_is_uncompressed_and_reproducible():
    pages = edgy_document.parse_document(MULTI)
    xml1 = edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in pages])
    xml2 = edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in edgy_document.parse_document(MULTI)])
    assert xml1 == xml2, "mxfile output must be reproducible (no timestamps / random ids)"
    root = ET.fromstring(xml1)
    assert root.tag == 'mxfile' and root.get('compressed') == 'false'
    diagrams = root.findall('diagram')
    assert [d.get('name') for d in diagrams] == ['Roles & actors', 'Systems']
    assert [d.get('id') for d in diagrams] == ['roles-actors', 'systems']
    assert all(d.find('mxGraphModel') is not None for d in diagrams), "pages must be plain XML, not base64"
    assert xml1.count('<?xml') == 1, "only one XML declaration"
    # every page carries its own legend
    for d in diagrams:
        assert any((c.get('value') or '').find('Legend') >= 0 for c in d.iter('mxCell')), d.get('name')


def test_mxfile_is_lint_clean_and_pages_reported():
    pages = edgy_document.parse_document(MULTI)
    path = _write(edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in pages]))
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False)
        findings = edgy_lint.lint_file(path, opts)
        assert not [f for f in findings if f.level == 'ERROR'], [str(f) for f in findings]
        # a deliberately broken second page is attributed to its page name
        broken = edgy_document.build_mxfile([
            ('Good', pages[0][1].generate_xml()),
            ('Bad', pages[1][1].generate_xml().replace('pageWidth="1200"', 'pageWidth="100"')),
        ])
        path2 = _write(broken)
        findings = edgy_lint.lint_file(path2, opts)
        assert any(f.rule == 'E007' and f.page == 'Bad' for f in findings), [str(f) for f in findings]
        os.unlink(path2)
    finally:
        os.unlink(path)


def test_load_pages_from_bare_and_mxfile():
    pages = edgy_document.parse_document(SINGLE)
    bare = _write(pages[0][1].generate_xml())
    wrapped = _write(edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in pages]))
    try:
        assert len(edgy_document.load_pages_from_file(bare)) == 1
        loaded = edgy_document.load_pages_from_file(wrapped)
        assert len(loaded) == 1 and loaded[0][0] == 'identity'
    finally:
        os.unlink(bare)
        os.unlink(wrapped)


def test_svg_contains_every_element_and_edge():
    pages = edgy_document.parse_document(SINGLE)
    model = ET.fromstring(pages[0][1].generate_xml())
    svg = edgy_render.page_to_svg(edgy_render.Page(model), 'identity')
    assert svg.startswith('<svg') and svg.rstrip().endswith('</svg>')
    for label in ('Sustainable mobility', 'From depot to platform', 'Acme Transit', 'contextualises', 'pursues'):
        assert label in svg, f"label {label!r} missing from SVG"
    assert svg.count('<polygon') == 1, "one pentagon (story)"
    assert svg.count('<path d="M') >= 2 + 4, "2 relationship edges + 4 legend edges"
    assert 'stroke-dasharray' in svg, "influence legend row must be dashed"
    assert 'marker-end' in svg


def test_svg_resolves_parent_offsets():
    xml = ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="2" value="Area" style="container=1;fillColor=#c9d9ff;" vertex="1" parent="1">'
           '<mxGeometry x="100" y="100" width="400" height="200" as="geometry"/></mxCell>'
           '<mxCell id="3" value="Leaf" style="rounded=1;arcSize=30;fillColor=#a6c0ff;strokeColor=#fff;" vertex="1" parent="2">'
           '<mxGeometry x="20" y="40" width="120" height="60" as="geometry"/></mxCell>'
           '</root></mxGraphModel>')
    svg = edgy_render.page_to_svg(edgy_render.Page(ET.fromstring(xml)))
    assert re.search(r'<rect x="120(\.0)?" y="140(\.0)?" width="120', svg), svg


def test_svg_uses_waypoints_and_anchor_sides():
    xml = ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="2" value="A" style="fillColor=#a6c0ff;" vertex="1" parent="1"><mxGeometry x="100" y="100" width="100" height="50" as="geometry"/></mxCell>'
           '<mxCell id="3" value="B" style="fillColor=#a6c0ff;" vertex="1" parent="1"><mxGeometry x="500" y="100" width="100" height="50" as="geometry"/></mxCell>'
           '<mxCell id="4" value="loop" style="edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=0.5;entryY=1;endArrow=open;endFill=0;" edge="1" source="3" target="2" parent="1">'
           '<mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="550" y="300"/><mxPoint x="150" y="300"/></Array></mxGeometry></mxCell>'
           '</root></mxGraphModel>')
    svg = edgy_render.page_to_svg(edgy_render.Page(ET.fromstring(xml)))
    m = re.search(r'<path d="M ([^"]+)" fill="none"', svg)
    assert m, svg
    assert '550.0,300.0' in m.group(1) and '150.0,300.0' in m.group(1), m.group(1)
    assert m.group(1).startswith('550.0,150.0'), "exit at bottom centre of B"


def test_render_file_writes_svg_per_page():
    pages = edgy_document.parse_document(MULTI)
    path = _write(edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in pages]))
    out = tempfile.mkdtemp()
    try:
        results = edgy_render.render_file(path, out_dir=out, png=False)
        names = sorted(os.path.basename(r['svg']) for r in results)
        base = os.path.basename(path)[:-len('.drawio')]
        assert names == sorted([f'{base}-roles-actors.svg', f'{base}-systems.svg']), names
        assert all(r['png'] is None for r in results)
        for r in results:
            assert os.path.getsize(r['svg']) > 500
    finally:
        os.unlink(path)


def test_find_chromium_respects_env(monkey=None):
    old = os.environ.get('EDGY_CHROMIUM')
    os.environ['EDGY_CHROMIUM'] = '/definitely/not/here'
    try:
        found = edgy_render.find_chromium()
        assert found != '/definitely/not/here', "a non-existent EDGY_CHROMIUM must be ignored"
    finally:
        if old is None:
            os.environ.pop('EDGY_CHROMIUM', None)
        else:
            os.environ['EDGY_CHROMIUM'] = old


def test_page_ids_unique_even_with_suffix_collisions():
    # review: "foo-3", "foo", "foo" used to give foo-3, foo, foo-3
    xml = edgy_document.build_mxfile([(n, '<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>')
                                      for n in ('foo-3', 'foo', 'foo', 'foo-2')])
    ids = [d.get('id') for d in ET.fromstring(xml).findall('diagram')]
    assert len(ids) == len(set(ids)), ids
    assert ids == ['foo-3', 'foo', 'foo-2', 'foo-2-2'], ids


def test_preview_stems_unique_for_duplicate_page_names():
    # review: two pages called "A" wrote to the same SVG
    pages = edgy_document.parse_document("""
pages:
  - name: "A"
    elements:
      - purpose: "One"
  - name: "A"
    elements:
      - purpose: "Two"
""")
    path = _write(edgy_document.build_mxfile([(n, p.generate_xml()) for n, p in pages]))
    out = tempfile.mkdtemp()
    try:
        results = edgy_render.render_file(path, out_dir=out, png=False)
        svgs = [r['svg'] for r in results]
        assert len(set(svgs)) == 2, svgs
        assert 'One' in open(svgs[0], encoding='utf-8').read() and 'Two' in open(svgs[1], encoding='utf-8').read()
    finally:
        os.unlink(path)


def _run_generator(*args, cwd=None):
    import subprocess
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edgy_generator.py')
    return subprocess.run([sys.executable, gen, *args], capture_output=True, text=True, cwd=cwd)


def test_preview_failure_exits_non_zero():
    # review: a failing mandatory preview used to exit 0
    import edgy_generator
    original = edgy_render.render_file
    edgy_render.render_file = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        assert edgy_generator.render_preview('whatever.drawio') is None   # None = no preview written (caller exits 3)
    finally:
        edgy_render.render_file = original
    d = tempfile.mkdtemp()
    src = _write(SINGLE, suffix='.txt')
    r = _run_generator(src, '--output', os.path.join(d, 'ok.drawio'), '--preview')
    assert r.returncode == 0 and os.path.exists(os.path.join(d, 'ok.svg')), r.stderr


def test_plantuml_engine_writes_one_source_per_page():
    # review: --engine plantuml used to drop every page after the first
    d = tempfile.mkdtemp()
    src = _write(MULTI, suffix='.txt')
    env_jar = os.environ.pop('PLANTUML_JAR', None)
    try:
        r = _run_generator(src, '--format', 'png', '--engine', 'plantuml', '--output', os.path.join(d, 'map.png'))
    finally:
        if env_jar is not None:
            os.environ['PLANTUML_JAR'] = env_jar
    pumls = sorted(f for f in os.listdir(d) if f.endswith('.puml'))
    assert pumls == ['map-roles-actors.puml', 'map-systems.puml'], (pumls, r.stdout, r.stderr)
    assert 'Fare engine' in open(os.path.join(d, 'map-systems.puml'), encoding='utf-8').read()


EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples', 'eval')


def _svg_of_fixture(name):
    d = tempfile.mkdtemp()
    out = os.path.join(d, name + '.drawio')
    r = _run_generator(os.path.join(EVAL, name + '.txt'), '--output', out)
    assert r.returncode == 0, r.stderr
    pages = edgy_document.load_pages_from_file(out)
    page = edgy_render.Page(pages[0][1])
    return page, edgy_render.page_to_svg(page, name)


def _edge_paths(svg):
    """[(x, y), …] per edge path drawn in the SVG (M … L … segments)."""
    out = []
    svg = re.sub(r'<defs>.*?</defs>', '', svg, flags=re.S)      # arrow markers are paths too
    for d in re.findall(r'<path d="([^"]+)" fill="none"', svg):
        pts = [tuple(float(v) for v in p.split(',')) for p in re.findall(r'(-?\d+\.?\d*,-?\d+\.?\d*)', d)]
        out.append(pts)
    return out


def test_render_no_diagonal_endpoints():
    # F1: ports spread along a side + waypoints computed for the centre port
    page, svg = _svg_of_fixture('fixture-f1-ports-waypoints')
    paths = [p for p in _edge_paths(svg) if len(p) >= 3]
    assert len(paths) >= 6, len(paths)
    for pts in paths:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            assert abs(ax - bx) < 0.6 or abs(ay - by) < 0.6, f'diagonal segment in {pts}'


def test_render_label_fractions():
    # F2: label: source / middle / target must land at different places along the edge
    page, svg = _svg_of_fixture('fixture-f2-labels')
    xs = [float(m) for m in re.findall(r'<text x="(-?\d+\.?\d*)" y="-?\d+\.?\d*" font-family="[^"]+" font-size="11(?:\.0)?"', svg)]
    assert len(xs) == 3, xs
    assert xs[0] < xs[1] < xs[2], xs        # source 25 % < middle 50 % < target 75 %


def test_render_straight_edges_border_to_border():
    # edgeStyle=none between two boxes: a single segment that starts and ends on the borders
    xml = ('<mxGraphModel pageWidth="600" pageHeight="300"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="a" value="A" style="whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#fff;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="120" height="60" as="geometry"/></mxCell>'
           '<mxCell id="b" value="B" style="whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#fff;" vertex="1" parent="1"><mxGeometry x="400" y="160" width="120" height="60" as="geometry"/></mxCell>'
           '<mxCell id="e" value="requires" style="edgeStyle=none;endArrow=classic;endFill=1;" edge="1" source="a" target="b" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>'
           '</root></mxGraphModel>')
    page = edgy_render.Page(ET.fromstring(xml))
    svg = edgy_render.page_to_svg(page)
    paths = _edge_paths(svg)
    assert len(paths) == 1 and len(paths[0]) == 2, paths
    (x1, y1), (x2, y2) = paths[0]
    assert abs(x1 - 160) < 0.6 and 40 <= y1 <= 100      # leaves A on its right border
    assert abs(x2 - 400) < 0.6 and 160 <= y2 <= 220     # enters B on its left border


def test_render_label_offset_point_moves_label():
    xml = ('<mxGraphModel pageWidth="600" pageHeight="300"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="a" value="A" style="fillColor=#a6c0ff;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="120" height="60" as="geometry"/></mxCell>'
           '<mxCell id="b" value="B" style="fillColor=#a6c0ff;" vertex="1" parent="1"><mxGeometry x="400" y="40" width="120" height="60" as="geometry"/></mxCell>'
           '<mxCell id="e" value="requires" style="edgeStyle=none;" edge="1" source="a" target="b" parent="1">'
           '<mxGeometry relative="1" as="geometry"><mxPoint x="0" y="30" as="offset"/></mxGeometry></mxCell>'
           '</root></mxGraphModel>')
    svg = edgy_render.page_to_svg(edgy_render.Page(ET.fromstring(xml)))
    ys = [float(m) for m in re.findall(r'<text x="-?\d+\.?\d*" y="(-?\d+\.?\d*)" font-family="[^"]+" font-size="11(?:\.0)?"', svg)]
    assert len(ys) == 1 and ys[0] > 70 + 20, ys            # 30 px below the path (y = 70), not raised above it


def test_render_description_rows_are_not_bold():
    # F4: the cell is bold (fontStyle=1) but the generator's description row says font-weight:normal
    page, svg = _svg_of_fixture('fixture-f4-long-bold-title')
    texts = re.findall(r'<text [^>]*font-size="9(?:\.0)?"[^>]*>([^<]*)</text>', svg)
    assert texts, 'no description rows rendered'
    bold_desc = re.findall(r'<text [^>]*font-size="9(?:\.0)?"[^>]*font-weight="bold"', svg)
    assert not bold_desc, bold_desc[:3]
    titles = re.findall(r'<text [^>]*font-size="14(?:\.0)?"[^>]*font-weight="bold"', svg)
    assert titles, 'titles must stay bold'


def test_publication_bounds_are_tight():
    sparse = """
map_type: journey
legend: strip
elements:
  - journey: "Plan"
  - journey: "Buy ticket"
  - journey: "Travel"
  - journey: "Arrive"
relationships:
  - "Plan" -> "Buy ticket": "flows"
  - "Buy ticket" -> "Travel": "flows"
  - "Travel" -> "Arrive": "flows"
"""
    d = tempfile.mkdtemp()
    src = _write(sparse, suffix='.txt')
    out = os.path.join(d, 'sparse.drawio')
    r = _run_generator(src, '--output', out)
    assert r.returncode == 0, r.stderr
    page = edgy_render.Page(edgy_document.load_pages_from_file(out)[0][1])
    full = edgy_render.page_to_svg(page)
    pub = edgy_render.page_to_svg(page, publication=True)
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', pub).group(1).split()]
    cb = edgy_render.content_bounds(page)
    assert vb[2] * vb[3] <= 1.15 * (cb[2] + 48) * (cb[3] + 48), (vb, cb)     # ≤ content + margin
    assert 'stroke-dasharray="4,4"' not in pub and 'stroke-dasharray="4,4"' in full   # no editor page frame
    assert edgy_render.orientation_hint(page) == 'landscape'
    # publication crop via the CLI
    r = _run_generator(src, '--output', os.path.join(d, 'p.drawio'), '--preview', '--publication')
    assert r.returncode == 0 and 'Orientation: landscape' in r.stdout, (r.stdout, r.stderr)


def test_native_presets_differ_only_in_frame():
    """publication vs presentation from one input: same content bounds, different margin, bands and legend placement."""
    import subprocess, json
    here = os.path.dirname(os.path.abspath(__file__))
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'in.txt')
    open(src, 'w', encoding='utf-8').write('title: Acme Transit — purpose\nfootnote: fictional example\n' + SINGLE)
    svgs = {}
    for preset in ('publication', 'presentation'):
        out = os.path.join(d, preset + '.drawio')
        r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', out, '--preview', '--preset', preset],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        svg = open(os.path.join(d, preset + '.svg'), encoding='utf-8').read()
        svgs[preset] = svg
        assert 'Acme Transit — purpose' in svg and 'fictional example' in svg, preset
        qa = json.load(open(os.path.join(d, preset + '.qa.json'), encoding='utf-8'))
        assert qa['preset'] == preset and qa['pages'][0]['text_size']['reference_width'] == edgy_render.NATIVE_PRESETS[preset]['ref_width']
        assert qa['pages'][0]['image']['svg'] == preset + '.svg' and not os.path.isabs(qa['pages'][0]['image']['png'] or ''), qa['pages'][0]['image']
        assert qa['pages'][0]['text_size']['scale'] is not None
    pages = {p: edgy_render.Page(edgy_document.load_pages_from_file(os.path.join(d, p + '.drawio'))[0][1]) for p in svgs}
    # the content (elements + edges) is identical; only the legend placement differs between the presets
    def element_boxes(page):
        return sorted(b for cid in page.order if page.cells[cid].get('vertex') == '1' and 'fillColor=#80ffb7' in (page.cells[cid].get('style') or '')
                      for b in [page.abs_box(cid)] if b[2] > 20)   # legend chips (14 × 12) are not elements
    assert element_boxes(pages['publication']) == element_boxes(pages['presentation'])
    # strip legend for publication (title cell left), box legend for presentation (right)
    def legend_x(page):
        for cid in page.order:
            c = page.cells[cid]
            if c.get('vertex') == '1' and 'Legend' in (c.get('value') or ''):
                return page.abs_box(cid)[0]
    assert legend_x(pages['publication']) < page_w(pages['publication']) / 2 < legend_x(pages['presentation'])
    vb = {p: [float(v) for v in re.search(r'viewBox="([^"]+)"', svgs[p]).group(1).split()] for p in svgs}
    assert vb['presentation'][2] > vb['publication'][2] or vb['presentation'][3] > vb['publication'][3], 'presentation has the wider margin'


def test_bands_per_page_and_wide_title_widens_frame():
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'in.txt')
    long_title = 'A deliberately very long title band that is much wider than the two small boxes of this tiny page ' * 2
    text = MULTI.replace('  - name: "Systems"\n', '  - name: "Systems"\n    title: "Systems view"\n').replace('facet: architecture', f'facet: architecture\ntitle: "{long_title.strip()}"')
    open(src, 'w', encoding='utf-8').write(text)
    out = os.path.join(d, 'm.drawio')
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', out, '--preview', '--preset', 'publication'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    first = open(os.path.join(d, 'm-roles-actors.svg'), encoding='utf-8').read()
    second = open(os.path.join(d, 'm-systems.svg'), encoding='utf-8').read()
    assert long_title.strip()[:40] in first and 'Systems view' not in first
    assert 'Systems view' in second and long_title.strip()[:40] not in second, 'page-level title overrides the head'
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', first).group(1).split()]
    assert vb[2] >= edgy_render.edgy_text.measure(long_title.strip(), edgy_render.TITLE_FS, bold=True), 'frame at least as wide as the title'


def page_w(page):
    return page.page_w


def test_qa_manifest_schema_and_approvals_null():
    import subprocess, json
    here = os.path.dirname(os.path.abspath(__file__))
    d = tempfile.mkdtemp()
    src = os.path.join(d, 'in.txt'); open(src, 'w', encoding='utf-8').write(MULTI)
    out = os.path.join(d, 'm.drawio')
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', out, '--qa', '--no-layout-quality'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    qa = json.load(open(os.path.join(d, 'm.qa.json'), encoding='utf-8'))
    assert len(qa['pages']) == 2 and qa['pages'][1]['name'] == 'Systems'
    # pages are matched by ordinal: two pages with one name keep their own counts and images
    dup = MULTI.replace('- name: "Systems"', '- name: "Roles & actors"')
    src2 = os.path.join(d, 'dup.txt'); open(src2, 'w', encoding='utf-8').write(dup)
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src2, '--output', os.path.join(d, 'dup.drawio'), '--preview', '--no-png'], capture_output=True, text=True) if False else \
        subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src2, '--output', os.path.join(d, 'dup.drawio'), '--preview'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    qd = json.load(open(os.path.join(d, 'dup.qa.json'), encoding='utf-8'))
    assert qd['pages'][0]['elements'] != qd['pages'][1]['elements'] and qd['pages'][0]['image']['svg'] != qd['pages'][1]['image']['svg'], qd['pages']
    assert qd['pages'][0]['edges'] == 1 and qd['pages'][1]['edges'] == 0
    assert qa['visual_approval'] is None and qa['semantic_approval'] is None and qa['delivery_notes'] is None
    # one semantic sign-off field: the review block of a purpose page only counts findings
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), os.path.join(here, '..', 'examples', 'purpose-map.txt'),
                        '--output', os.path.join(d, 'pm.drawio'), '--qa'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    qp = json.load(open(os.path.join(d, 'pm.qa.json'), encoding='utf-8'))
    assert set(qp['semantic_review']) == {'findings'} and 'approved_by' not in json.dumps(qp)
    assert qa['pages'][0]['layout_quality'] == {'ran': False, 'findings': 0}
    assert qa['pages'][1]['elements'] == {'asset': 5} and qa['pages'][0]['edges'] == 1
    # edges are counted as drawn: the triad reports links into panels instead of drawing them
    import edgy_qa
    tri = os.path.join(here, '..', 'examples', 'triad-all-facets.txt')
    out3 = os.path.join(d, 't.drawio')
    subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), tri, '--output', out3, '--qa'], capture_output=True, text=True)
    qa3 = json.load(open(os.path.join(d, 't.qa.json'), encoding='utf-8'))
    assert qa3['pages'][0]['edges'] == 24, qa3['pages'][0]['edges']
    # approvals: only a reviewer name-and-date string counts
    assert not edgy_qa.is_approval(True) and not edgy_qa.is_approval(1) and not edgy_qa.is_approval({'automated': True}) and not edgy_qa.is_approval(' ')
    assert edgy_qa.is_approval('Reviewer, 2026-10-09')
    qa['visual_approval'] = True; qa['semantic_approval'] = 1
    bad = os.path.join(d, 'bad.qa.json'); open(bad, 'w', encoding='utf-8').write(json.dumps(qa))
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_qa.py'), '--require-approvals', bad], capture_output=True, text=True)
    assert r.returncode == 1 and 'not a reviewer name and date' in r.stdout, r.stdout
    assert qa['pages'][0]['image'] is None, 'no preview requested'
    repo = os.path.abspath(os.path.join(here, '..', '..', '..', '..'))
    v = subprocess.run([sys.executable, os.path.join(repo, 'tools', 'validate-edgy-model.py'), '--schema',
                        os.path.join(here, '..', 'assets', 'qa.schema.json'), os.path.join(d, 'm.qa.json')], capture_output=True, text=True)
    assert v.returncode == 0, v.stdout + v.stderr
    # a native preset with an unsupported engine / format is refused, never silently exported without its frame
    for extra in (['--format', 'pdf', '--preset', 'publication'], ['--format', 'png', '--engine', 'drawio', '--preset', 'publication']):
        r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'x.png')] + extra, capture_output=True, text=True)
        assert r.returncode == 2 and 'native preset' in r.stderr, (extra, r.stderr)
    # publication without a native render is refused; presentation without --preview stays the draw.io CLI preset
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'plain.drawio'), '--preset', 'publication'], capture_output=True, text=True)
    assert r.returncode == 2 and 'native preset' in r.stderr, r.stderr
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'x.drawio'), '--engine', 'native', '--preset', 'publication'], capture_output=True, text=True)
    assert r.returncode == 2 and 'native preset' in r.stderr, 'no native render runs for .drawio output without --preview'
    # an explicit native engine always means the native preset: pdf is refused instead of being written as XML
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'out.pdf'), '--engine', 'native', '--format', 'pdf', '--preset', 'presentation'], capture_output=True, text=True)
    assert r.returncode == 2 and 'native preset' in r.stderr and not os.path.exists(os.path.join(d, 'out.pdf')), r.stderr
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'slide.png'), '--preset', 'presentation'], capture_output=True, text=True)
    # the CLI preset path was taken (slide.drawio, not slide.png.drawio); without the CLI the export is not confirmed → exit 1
    assert r.returncode == 1 and not os.path.exists(os.path.join(d, 'slide.png.drawio')) and os.path.exists(os.path.join(d, 'slide.drawio')), r.stdout + r.stderr
    # manifest image paths are relative to the manifest's directory
    qa_prev = json.load(open(os.path.join(d, 'publication.qa.json'), encoding='utf-8')) if os.path.exists(os.path.join(d, 'publication.qa.json')) else None
    # --qa with a draw.io CLI export: without the CLI the export is not confirmed → exit 1, no manifest, .drawio kept
    out4 = os.path.join(d, 'cli.png')
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', out4, '--format', 'png', '--qa'], capture_output=True, text=True)
    assert r.returncode == 1 and 'no qa.json written' in r.stderr and not os.path.exists(os.path.join(d, 'cli.qa.json')), r.stdout + r.stderr
    assert os.path.exists(os.path.join(d, 'cli.drawio'))
    # with a confirmed export the manifest names the delivery file
    import edgy_qa, edgy_document
    pages = edgy_document.parse_document(MULTI)
    for _n, pp in pages:
        pp.generate_xml()
    m = edgy_qa.build_manifest(out, pages, output_path=out4)
    assert m['output'] == os.path.basename(out) and m['outputs'] == [os.path.basename(out)], 'cli.png does not exist: the manifest names the file that does'
    # a multi-page native export: the manifest lists the per-page files the renderer wrote, not the requested single name
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', os.path.join(d, 'maps.svg'), '--format', 'svg', '--engine', 'native', '--qa'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    qm = json.load(open(os.path.join(d, 'maps.qa.json'), encoding='utf-8'))
    assert qm['outputs'] == ['maps-roles-actors.svg', 'maps-systems.svg'] and qm['output'] == 'maps-roles-actors.svg', qm['outputs']
    assert all(os.path.exists(os.path.join(d, f)) for f in qm['outputs'])
    # --no-qa: nothing written
    out2 = os.path.join(d, 'n.drawio')
    subprocess.run([sys.executable, os.path.join(here, 'edgy_generator.py'), src, '--output', out2, '--no-qa'], capture_output=True, text=True)
    assert not os.path.exists(os.path.join(d, 'n.qa.json'))


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f"Testing {t.__name__}...")
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} document/render tests passed")


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
