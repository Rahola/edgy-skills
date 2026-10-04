#!/usr/bin/env python3
"""Tests for edgy_lint.py — synthetic draw.io snippets, one rule per case."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_lint  # noqa: E402
from edgy_parser import EDGYParser  # noqa: E402

HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n'
        '<mxGraphModel pageWidth="800" pageHeight="600"><root>'
        '<mxCell id="0"/><mxCell id="1" parent="0"/>')
TAIL = '</root></mxGraphModel>'
LEGEND = ('<mxCell id="91" value="EDGY 23 — Legend" style="text;html=1;" vertex="1" parent="1">'
          '<mxGeometry x="600" y="480" width="150" height="20" as="geometry"/></mxCell>'
          + ''.join(f'<mxCell id="9{n}" value="" style="rounded=1;fillColor={col};strokeColor=#ffffff;" vertex="1" parent="1">'
                    f'<mxGeometry x="600" y="{500 + n * 16}" width="14" height="12" as="geometry"/></mxCell>'
                    for n, col in enumerate(('#80ffb7', '#a6c0ff', '#ff99bd'), 2))
          + '<mxCell id="99" value="" style="edgeStyle=none;endArrow=classic;endFill=1;" edge="1" parent="1">'
            '<mxGeometry relative="1" as="geometry"><mxPoint x="600" y="560" as="sourcePoint"/>'
            '<mxPoint x="630" y="560" as="targetPoint"/></mxGeometry></mxCell>')
PURPOSE = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;arcSize=30;fontSize=12;'
STORY = 'shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;fontSize=12;'
ORG = 'whiteSpace=wrap;html=1;fillColor=#80eaff;strokeColor=#fff;strokeWidth=2;fontSize=12;'
ASSET = 'whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#fff;strokeWidth=2;fontSize=12;'
CORE = 'edgeStyle=orthogonalEdgeStyle;endArrow=classic;endFill=1;'
INFL = 'edgeStyle=orthogonalEdgeStyle;endArrow=open;endFill=0;dashed=1;'


def vertex(i, value, style, x, y, w=120, h=60, parent='1'):
    return (f'<mxCell id="{i}" value="{value}" style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def edge(i, value, style, src, tgt, geometry=True):
    g = '<mxGeometry relative="1" as="geometry"/>' if geometry else ''
    return f'<mxCell id="{i}" value="{value}" style="{style}" edge="1" source="{src}" target="{tgt}" parent="1">{g}</mxCell>'


def run(xml, *args):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend='--no-legend' in args)
        return [(x.rule, x.level) for x in edgy_lint.lint_file(path, opts)]
    finally:
        os.unlink(path)


def rules(findings):
    return {r for r, _ in findings}


def test_clean_diagram():
    xml = HEAD + vertex(2, 'Purpose', PURPOSE, 40, 40) + vertex(3, 'Story', STORY, 300, 40, 140) + \
        edge(10, 'contextualises', CORE, 3, 2) + LEGEND + TAIL
    f = run(xml)
    assert f == [], f"clean diagram must have no findings, got {f}"


def test_nested_cells_and_missing_geometry():
    xml = HEAD + ('<mxCell id="2" value="Purpose" style="%s" vertex="1" parent="1">'
                  '<mxGeometry x="40" y="40" width="120" height="60" as="geometry"/>'
                  '<mxCell id="3" value="Story" style="%s" vertex="1" parent="2">'
                  '<mxGeometry x="10" y="10" width="100" height="40" as="geometry"/></mxCell></mxCell>' % (PURPOSE, STORY)) + \
        edge(10, 'contextualises', CORE, 3, 2, geometry=False) + LEGEND + TAIL
    r = rules(run(xml))
    assert 'E002' in r, r
    assert 'E004' in r, r


def test_dangling_edge_and_duplicate_id():
    xml = HEAD + vertex(2, 'Purpose', PURPOSE, 40, 40) + vertex(2, 'Dup', PURPOSE, 300, 40) + \
        edge(10, 'contextualises', CORE, 99, 2) + LEGEND + TAIL
    r = rules(run(xml))
    assert 'E003' in r and 'E005' in r, r


def test_negative_offpage_overlap():
    xml = HEAD + vertex(2, 'A', PURPOSE, -10, 40) + vertex(3, 'B', ASSET, 750, 40) + \
        vertex(4, 'C', ORG, 300, 300) + vertex(5, 'D', ORG, 340, 320) + LEGEND + TAIL
    r = rules(run(xml))
    assert {'E006', 'E007', 'E008'} <= r, r


def test_relative_geometry_resolves_through_parent():
    # child at (700, 0) inside a container at (200, 100) → absolute x = 900 > page width 800
    xml = HEAD + vertex(2, 'Area', 'container=1;fillColor=#c9d9ff;', 200, 100, 400, 200) + \
        vertex(3, 'Cap', PURPOSE, 700, 0, parent='2') + LEGEND + TAIL
    r = rules(run(xml))
    assert 'E007' in r, r
    assert 'W106' not in r, "container with a child must not be reported empty"


def test_empty_container_warning():
    xml = HEAD + vertex(2, 'Area', 'container=1;fillColor=#c9d9ff;', 200, 100, 400, 200) + \
        vertex(3, 'Cap', PURPOSE, 40, 40) + LEGEND + TAIL
    assert 'W106' in rules(run(xml))


def test_legend_required_unless_disabled():
    xml = HEAD + vertex(2, 'Purpose', PURPOSE, 40, 40) + TAIL
    assert 'E009' in rules(run(xml))
    assert 'E009' not in rules(run(xml, '--no-legend'))


def test_core_verb_on_wrong_pair_and_noncore_with_core_style():
    xml = HEAD + vertex(2, 'Org', ORG, 40, 40) + vertex(3, 'System', ASSET, 400, 40) + \
        vertex(4, 'Purpose', PURPOSE, 40, 300) + \
        edge(10, 'has', CORE, 2, 3) + edge(11, 'enables', CORE, 3, 4) + edge(12, 'pursues', INFL, 2, 4) + \
        edge(13, 'zaps', INFL, 3, 4) + LEGEND + TAIL
    f = run(xml)
    r = rules(f)
    assert 'E010' in r, f      # has: organisation → asset is not a core pair
    assert 'E011' in r, f      # enables drawn solid
    assert 'W104' in r, f      # pursues drawn dashed
    assert 'W105' in r, f      # zaps unknown verb


def test_text_fit_and_double_escape():
    long = 'A very long element name that certainly does not fit into a small box at all ' * 2
    xml = HEAD + vertex(2, long, PURPOSE, 40, 40) + vertex(3, 'her&amp;auml;tt&amp;auml;&amp;auml;', ORG, 400, 40) + LEGEND + TAIL
    r = rules(run(xml))
    assert 'W101' in r and 'W107' in r, r


def test_intersection_shape_and_palette():
    xml = HEAD + vertex(2, 'Brand', 'rounded=1;arcSize=30;fillColor=#ffd580;', 40, 40) + \
        vertex(3, 'Odd', 'fillColor=#ff0000;', 400, 40) + LEGEND + TAIL
    r = rules(run(xml))
    assert 'W103' in r and 'W102' in r, r


def test_mxfile_multipage_and_compressed():
    import base64
    import urllib.parse
    import zlib
    inner = HEAD.split('?>\n')[1] + vertex(2, 'Purpose', PURPOSE, 40, 40) + LEGEND + TAIL
    comp = base64.b64encode(zlib.compress(urllib.parse.quote(inner, safe='').encode())[2:-4]).decode()
    xml = ('<mxfile host="test"><diagram name="One" id="a">' + inner + '</diagram>'
           '<diagram name="Two" id="b">' + comp + '</diagram></mxfile>')
    f = run(xml)
    assert f == [], f"multi-page mxfile should be clean, got {f}"


def test_generator_output_is_lint_clean():
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Sustainable mobility"
  - story: "From bus depot to mobility platform"
  - content: "Plain-language service promise"
  - capability: "Ticketing"
  - asset: "Fare engine"
  - process: "Fare change"
  - task: "Buy a ticket"
  - channel: "Mobile app"
  - journey: "Daily commute"
  - organisation: "Acme Transit"
  - product: "Acme app"
  - brand: "Acme"
relationships:
  - "From bus depot to mobility platform" -> "Sustainable mobility": "contextualises"
  - "Ticketing" -> "Fare engine": "requires"
  - "Fare change" -> "Ticketing": "realises"
  - "Buy a ticket" -> "Daily commute": "is part of"
  - "Acme Transit" -> "Ticketing": "has"
  - "Acme app" -> "Buy a ticket": "serves"
  - "Acme" -> "Sustainable mobility": "represents"
  - "Fare engine" -> "Sustainable mobility": "contributes to"
""")
    assert parser.warnings == [], parser.warnings
    f = run(parser.generate_xml())
    assert not [x for x in f if x[1] == 'ERROR'], f"generator output must be error-free, got {f}"


def test_element_named_legend_does_not_satisfy_legend_rule():
    # review: an element labelled "Legend" (or a cell id starting with "leg") must not bypass E009
    xml = HEAD + vertex('leg5', 'Legend', PURPOSE, 40, 40) + \
        '<mxCell id="3" value="Legend" style="text;html=1;" vertex="1" parent="1"><mxGeometry x="300" y="40" width="80" height="20" as="geometry"/></mxCell>' + TAIL
    r = rules(run(xml))
    assert 'E009' in r, f"a legend title without colour chips and line samples is not a legend: {r}"


def test_legend_element_ids_are_not_skipped():
    # a real element whose id starts with "leg" is still linted (here: off-page)
    xml = HEAD + vertex('legacy', 'Legacy engine', ASSET, 750, 40) + LEGEND + TAIL
    assert 'E007' in rules(run(xml))


def test_base_elements_are_linted():
    # review: people / activity / outcome / object use neutral fills and were invisible to the linter
    person = 'shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#262626;'
    outcome = 'rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#262626;'
    xml_no_legend = HEAD + vertex(2, 'Customer', person, 40, 40, 60, 80) + TAIL
    assert 'E009' in rules(run(xml_no_legend)), "base-only diagram without a legend must fail E009"
    xml = HEAD + vertex(2, 'Customer', person, -20, 40, 60, 80) + vertex(3, 'KPI', outcome, 300, 40) + \
        vertex(4, 'Purpose', PURPOSE, 300, 300) + edge(10, 'pursues', CORE, 2, 4) + edge(11, 'zaps', INFL, 3, 4) + LEGEND + TAIL
    r = rules(run(xml))
    assert 'E006' in r, f"negative coordinates of a base element are reported: {r}"
    assert 'E010' in r, f"core-link verb from a base element is a wrong pair: {r}"
    assert 'W105' in r, f"unknown verb from a base element is reported: {r}"


def test_json_output_is_pure_json():
    import json, subprocess
    xml = HEAD + vertex(2, 'A', PURPOSE, -10, 40) + TAIL
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
    try:
        out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edgy_lint.py'), '--json', f.name],
                             capture_output=True, text=True)
        findings = json.loads(out.stdout)
        assert {x['rule'] for x in findings} >= {'E006', 'E009'}, findings
        assert 'edgy-lint:' in out.stderr and out.returncode == 1
    finally:
        os.unlink(f.name)


STRAIGHT = 'edgeStyle=none;endArrow=open;endFill=0;dashed=1;'


def _findings(xml, *args):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend=True)
        return edgy_lint.lint_file(path, opts)
    finally:
        os.unlink(path)


def test_w111_edge_through_box():
    # A ── straight ──▶ C with B in the middle of the line
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(3, 'B', ASSET, 300, 100) + vertex(4, 'C', ASSET, 560, 100) + \
        edge(10, 'depends on', STRAIGHT, 2, 4) + TAIL
    f = _findings(xml)
    w111 = [x for x in f if x.rule == 'W111']
    assert len(w111) == 1 and w111[0].cell == '10' and w111[0].coords['other'] == '3', [str(x) for x in f]
    assert w111[0].coords['inside_px'] >= 120
    # move B out of the way → clean
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(3, 'B', ASSET, 300, 400) + vertex(4, 'C', ASSET, 560, 100) + \
        edge(10, 'depends on', STRAIGHT, 2, 4) + TAIL
    assert 'W111' not in rules(run(xml, '--no-legend'))


def test_w111_allows_containers_and_nested_coordinates():
    # the edge crosses a container (not an element) and a nested element is checked at its absolute position
    cont = 'rounded=1;container=1;fillColor=#e6edff;strokeColor=#ffffff;'
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(5, 'Area', cont, 250, 20, 220, 300) + \
        vertex(3, 'B', ASSET, 50, 80, parent='5') + vertex(4, 'C', ASSET, 560, 100) + \
        edge(10, 'depends on', STRAIGHT, 2, 4) + TAIL
    f = _findings(xml)
    w111 = [x for x in f if x.rule == 'W111']
    assert [x.coords['other'] for x in w111] == ['3'], [str(x) for x in f]   # B (abs 300,100), never the container


def test_w112_label_on_box():
    # a short edge whose label sits on the target box
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(3, 'B', ASSET, 180, 100) + \
        edge(10, 'a rather long relationship label', STRAIGHT, 2, 3) + TAIL
    f = _findings(xml)
    assert any(x.rule == 'W112' for x in f), [str(x) for x in f]
    # far apart → the label floats over empty space
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(3, 'B', ASSET, 600, 100) + \
        edge(10, 'depends on', STRAIGHT, 2, 3) + TAIL
    assert 'W112' not in rules(run(xml, '--no-legend'))


def test_w113_label_on_label_but_not_for_a_tree_bus():
    # a parent → children fan with one verb from one source is a bus: never W113
    xml = HEAD + vertex(2, 'P', ASSET, 300, 40) + vertex(3, 'C1', ASSET, 40, 300) + vertex(4, 'C2', ASSET, 560, 300) + \
        edge(10, 'contains', 'edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=0.5;entryY=0;', 2, 3) + \
        edge(11, 'contains', 'edgeStyle=orthogonalEdgeStyle;exitX=0.5;exitY=1;entryX=0.5;entryY=0;', 2, 4) + TAIL
    f = _findings(xml)
    assert not any(x.rule == 'W113' for x in f), [str(x) for x in f]
    # same geometry, two different verbs from two different sources → W113
    xml = HEAD + vertex(2, 'P', ASSET, 300, 40) + vertex(5, 'Q', ASSET, 300, 40) + vertex(3, 'C1', ASSET, 40, 300) + vertex(4, 'C2', ASSET, 560, 300) + \
        edge(10, 'contains', 'edgeStyle=none;', 2, 3) + edge(11, 'enables', 'edgeStyle=none;', 5, 3) + TAIL
    f = _findings(xml)
    assert any(x.rule == 'W113' for x in f), [str(x) for x in f]


def test_w114_outside_page():
    xml = HEAD + vertex(2, 'A', ASSET, 40, 40) + vertex(3, 'B', ASSET, 650, 40) + \
        edge(10, 'depends on', 'edgeStyle=none;', 2, 3) + TAIL          # B ends at x=770 < 800: label fits
    assert 'W114' not in rules(run(xml, '--no-legend'))
    xml = HEAD + vertex(2, 'A', ASSET, 40, 40) + vertex(3, 'B', ASSET, 700, 40) + \
        edge(10, 'depends on', 'edgeStyle=orthogonalEdgeStyle;', 2, 3) + \
        edge(11, 'x', 'edgeStyle=none;', 3, 2) + TAIL
    # B extends past the page (E007) and a route with waypoints beyond it
    xml2 = HEAD + vertex(2, 'A', ASSET, 40, 40) + vertex(3, 'B', ASSET, 600, 40) + \
        ('<mxCell id="12" value="loops" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="2" target="3" parent="1">'
         '<mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="400" y="650"/></Array></mxGeometry></mxCell>') + TAIL
    f = _findings(xml2)
    assert any(x.rule == 'W114' for x in f), [str(x) for x in f]


def test_visual_findings_carry_coordinates_and_visual_flag_filters():
    import json
    import subprocess
    xml = HEAD + vertex(2, 'A', ASSET, 40, 100) + vertex(3, 'B', ASSET, 300, 100) + vertex(4, 'C', ASSET, 560, 100) + \
        edge(10, 'depends on', STRAIGHT, 2, 4) + TAIL
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        r = subprocess.run([sys.executable, edgy_lint.__file__, '--visual', '--no-legend', path], capture_output=True, text=True)
        data = json.loads(r.stdout)
    finally:
        os.unlink(path)
    assert data and all(d['rule'] in edgy_lint.VISUAL_RULES for d in data), data
    assert data[0]['coords']['edge'] == '10' and 'route' in data[0]['coords']
    assert 'edgy-lint:' in r.stderr                       # summary goes to stderr, stdout is pure JSON


def test_legend_strip_satisfies_e009_and_w115_scale():
    p = EDGYParser()
    p.parse_input("""
map_type: asset
legend: strip
elements:
  - asset: "Fare engine" {id: AST-01}
  - asset: "Data lake" {id: AST-02}
relationships:
  - "Fare engine" -> "Data lake": "depends on"
""")
    xml = p.generate_xml()
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        ns = edgy_lint.main.__globals__['argparse'].Namespace
        f_default = edgy_lint.lint_file(path, ns(no_legend=False))
        assert 'E009' not in {x.rule for x in f_default}, [str(x) for x in f_default]
        assert not [x for x in f_default if x.level == 'ERROR'], [str(x) for x in f_default]
        f_scaled = edgy_lint.lint_file(path, ns(no_legend=False, scale=0.3))
        w115 = [x for x in f_scaled if x.rule == 'W115']
        assert len(w115) == 3, [str(x) for x in w115]          # 2 elements + 1 relation label at 0.3
        msgs = ' '.join(x.msg for x in w115)
        assert 'description' in msgs and 'relation label' in msgs, msgs   # the 9 px id line is the smallest text
        assert not [x for x in edgy_lint.lint_file(path, ns(no_legend=False, scale=1.0)) if x.rule == 'W115']
    finally:
        os.unlink(path)


def test_fixtures_reproduce_visual_findings():
    """The eval fixtures lint 0/0 structurally and > 0 on the visual rules."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    gen = os.path.join(here, 'edgy_generator.py')
    eval_dir = os.path.join(here, '..', 'examples', 'eval')
    d = tempfile.mkdtemp()
    ns = edgy_lint.main.__globals__['argparse'].Namespace
    # the 19-element single facet in the default layout still reproduces the field defect
    out = os.path.join(d, 'large.drawio')
    r = subprocess.run([sys.executable, gen, os.path.join(eval_dir, 'large-architecture-facet.txt'), '--output', out], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    f = edgy_lint.lint_file(out, ns(no_legend=False))
    assert not [x for x in f if x.level == 'ERROR'], [str(x) for x in f]
    assert any(x.rule == 'W111' for x in f), sorted({x.rule for x in f})
    # F1 (routing) and F5 (purpose tree) are fixed: clean under --warnings-as-errors, visual rules included
    for name in ('fixture-f1-ports-waypoints', 'fixture-f5-purpose-tree'):
        out = os.path.join(d, name + '.drawio')
        r = subprocess.run([sys.executable, gen, os.path.join(eval_dir, name + '.txt'), '--output', out], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        f = edgy_lint.lint_file(out, ns(no_legend=False))
        assert not f, (name, [str(x) for x in f])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f"Testing {t.__name__}...")
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} lint tests passed")


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
