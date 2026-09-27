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
