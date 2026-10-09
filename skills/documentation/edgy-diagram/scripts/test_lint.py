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


def test_w116_label_language_mismatch():
    src = ("map_type: purpose\nlanguage: fi\nelements:\n  - purpose: \"Sujuva arki\" [vahvistettu]\n"
           "  - purpose: \"Saumattomat matkaketjut\" [analyyttinen]\nrelationships:\n"
           "  - \"Sujuva arki\" -> \"Saumattomat matkaketjut\": \"contains\"\n")
    ns = edgy_lint.main.__globals__['argparse'].Namespace

    def lint_of(text, **kw):
        p = EDGYParser()
        p.parse_input(text)
        xml = p.generate_xml()
        with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
            f.write(xml)
            path = f.name
        try:
            return edgy_lint.lint_file(path, ns(no_legend=False, **kw))
        finally:
            os.unlink(path)

    # generator translates → no W116; the legend title tells the linter the map is Finnish
    assert not [x for x in lint_of(src) if x.rule == 'W116']
    # translation off → the English verb survives in a Finnish map → W116
    f = lint_of(src.replace('language: fi', 'language: fi\ntranslate_verbs: false'))
    assert [x.rule for x in f if x.rule == 'W116'] == ['W116'], [str(x) for x in f]
    assert 'sisältää' not in ' '.join(x.msg for x in f) or 'language: fi' in ' '.join(x.msg for x in f)
    # no language in the file: nothing to compare against unless --language says so
    plain = src.replace('language: fi\n', '')
    assert not [x for x in lint_of(plain) if x.rule == 'W116']
    assert [x.rule for x in lint_of(plain, language='fi') if x.rule == 'W116'] == ['W116']
    # free text is not a vocabulary verb → never W116
    free = src.replace('"contains"', '"kuuluu kokonaisuuteen"').replace('language: fi', 'language: fi\ntranslate_verbs: false')
    assert not [x for x in lint_of(free) if x.rule == 'W116']


def test_w116_silent_without_explicit_language():
    """The default (English) legend is not a language choice: Finnish verbs in a map without language: pass."""
    p = EDGYParser()
    p.parse_input('map_type: purpose\nelements:\n  - purpose: "Tavoite A"\n  - purpose: "Tavoite B"\nrelationships:\n  - "Tavoite A" -> "Tavoite B": "sisältää"\n')
    xml = p.generate_xml()
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml); path = f.name
    try:
        ns = edgy_lint.main.__globals__['argparse'].Namespace
        assert not [x for x in edgy_lint.lint_file(path, ns(no_legend=False)) if x.rule == 'W116']
        assert 'edgyLang=' not in xml
        assert [x for x in edgy_lint.lint_file(path, ns(no_legend=False, language='en')) if x.rule == 'W116'], '--language still checks'
    finally:
        os.unlink(path)
    p2 = EDGYParser()
    p2.parse_input('map_type: purpose\nlanguage: fi\nelements:\n  - purpose: "A"\n  - purpose: "B"\n')
    assert 'edgyLang=fi;' in p2.generate_xml()


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


# ---- Sprint 15: layout quality W117–W121 ---------------------------------------
CONT = 'rounded=1;whiteSpace=wrap;html=1;container=1;fillColor=#eef2f7;strokeColor=none;'


def _head(w, h):
    return HEAD.replace('pageWidth="800" pageHeight="600"', f'pageWidth="{w}" pageHeight="{h}"')


def _run_opts(xml, **kw):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        ns = edgy_lint.main.__globals__['argparse'].Namespace
        return edgy_lint.lint_file(path, ns(no_legend=True, **kw))
    finally:
        os.unlink(path)


def test_w117_size_spread():
    xml = HEAD + vertex(2, 'A', ASSET, 40, 40, 120) + vertex(3, 'B', ASSET, 300, 40, 200) + vertex(4, 'C', ORG, 40, 200, 300) + TAIL
    f = _run_opts(xml)
    msgs = [x.msg for x in f if x.rule == 'W117']
    assert len(msgs) == 1 and '120 to 200' in msgs[0] and '×1.67' in msgs[0], msgs
    assert not [x for x in _run_opts(xml, no_layout_quality=True) if x.rule in edgy_lint.LAYOUT_RULES]
    xml2 = HEAD + vertex(2, 'A', ASSET, 40, 40, 120) + vertex(3, 'B', ASSET, 300, 40, 140) + TAIL   # ×1.17: within the limit
    assert not [x for x in _run_opts(xml2) if x.rule == 'W117']


def test_w118_alignment():
    xml = HEAD + vertex(2, 'Area 1', CONT, 60, 60, 300, 200) + vertex(3, 'Area 2', CONT, 66, 300, 300, 200) + \
        vertex(4, 'a', ASSET, 20, 40, parent='2') + vertex(5, 'b', ASSET, 20, 40, parent='3') + TAIL
    msgs = [x.msg for x in _run_opts(xml) if x.rule == 'W118']
    assert len(msgs) == 1 and 'nearly left-aligned: 6 px' in msgs[0], msgs
    # elements of one type in one row, tops 5 px apart
    xml2 = HEAD + vertex(2, 'A', ASSET, 40, 40) + vertex(3, 'B', ASSET, 300, 45) + TAIL
    assert [x for x in _run_opts(xml2) if x.rule == 'W118']
    # exact alignment and a different type: silent
    xml3 = HEAD + vertex(2, 'A', ASSET, 40, 40) + vertex(3, 'B', ORG, 300, 45) + vertex(4, 'C', ASSET, 500, 40) + TAIL
    assert not [x for x in _run_opts(xml3) if x.rule == 'W118']
    # three containers in a row of one height with uneven gaps
    xml4 = HEAD + ''.join(vertex(i, f'Area {i}', CONT, x, 60, 150, 200) + vertex(i + 10, 'c', ASSET, 20, 40, parent=str(i))
                          for i, x in ((2, 60), (3, 250), (4, 500))) + TAIL
    msgs = [x.msg for x in _run_opts(xml4) if x.rule == 'W118' and 'gaps' in x.msg]
    assert len(msgs) == 1 and 'from 40 to 100 px' in msgs[0], msgs


def test_w119_balance():
    xml = _head(2400, 1600) + vertex(2, 'A', ASSET, 60, 60) + vertex(3, 'B', ASSET, 300, 60) + TAIL
    msgs = [x.msg for x in _run_opts(xml) if x.rule == 'W119']
    assert any('sits against the left edge' in m for m in msgs) and any('sits against the top edge' in m for m in msgs), msgs
    assert any('covers 0%' in m or 'covers 1%' in m for m in msgs), msgs
    # the editor's minimum page is never judged
    xml2 = _head(1200, 900) + vertex(2, 'A', ASSET, 60, 60) + vertex(3, 'B', ASSET, 300, 60) + TAIL
    assert not [x for x in _run_opts(xml2) if x.rule == 'W119']


def test_w120_aspect():
    row = ''.join(vertex(i, f'A{i}', ASSET, 60 + (i - 2) * 200, 60) for i in range(2, 10))   # 1520 × 60
    f = _run_opts(_head(1700, 900) + row + TAIL)
    msgs = [x.msg for x in f if x.rule == 'W120']
    assert len(msgs) == 1 and 'too wide' in msgs[0] and 'ratio 25.33' in msgs[0], msgs
    seq = ''.join(vertex(i, f'P{i}', STORY, 60 + (i - 2) * 200, 60, 140) for i in range(2, 10))
    assert not [x for x in _run_opts(_head(1700, 900) + seq + TAIL) if x.rule == 'W120'], 'a sequence of pentagons is exempt'
    short = ''.join(vertex(i, f'A{i}', ASSET, 60 + (i - 2) * 200, 60) for i in range(2, 6))   # 720 px: fits a slide
    assert not [x for x in _run_opts(HEAD + short + TAIL) if x.rule == 'W120']


def test_w121_series():
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    gen = os.path.join(here, 'edgy_generator.py')
    eval_dir = os.path.join(here, '..', 'examples', 'eval')
    d = tempfile.mkdtemp()
    outs = []
    for name in ('series-acme-capability', 'series-acme-task', 'series-acme-purpose'):
        out = os.path.join(d, name + '.drawio')
        r = subprocess.run([sys.executable, gen, os.path.join(eval_dir, name + '.txt'), '--output', out], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(out)
    assert not edgy_lint.series_findings(outs), [str(x) for x in edgy_lint.series_findings(outs)]
    ns = edgy_lint.main.__globals__['argparse'].Namespace
    for out in outs:
        f = edgy_lint.lint_file(out, ns(no_legend=False))
        assert not f, (out, [str(x) for x in f])
    src = open(os.path.join(eval_dir, 'series-acme-capability.txt'), encoding='utf-8').read().replace('legend: strip', 'legend: strip\ncard_width: 300')
    wide_txt = os.path.join(d, 'wide.txt'); open(wide_txt, 'w', encoding='utf-8').write(src)
    wide = os.path.join(d, 'wide.drawio')
    subprocess.run([sys.executable, gen, wide_txt, '--output', wide], capture_output=True, text=True)
    msgs = [x.msg for x in edgy_lint.series_findings([outs[2], wide])]
    assert len(msgs) == 1 and 'organisation cards are 300 px wide' in msgs[0], msgs
    boxed = os.path.join(d, 'boxed.drawio')
    open(os.path.join(d, 'boxed.txt'), 'w', encoding='utf-8').write(open(os.path.join(eval_dir, 'series-acme-task.txt'), encoding='utf-8').read().replace('legend: strip', 'legend: box'))
    subprocess.run([sys.executable, gen, os.path.join(d, 'boxed.txt'), '--output', boxed], capture_output=True, text=True)
    msgs = [x.msg for x in edgy_lint.series_findings([outs[1], boxed])]
    assert len(msgs) == 1 and 'legend is a box here but a strip' in msgs[0], msgs
    # a type absent from the first file is still compared between the later files
    narrow_txt = os.path.join(d, 'narrow.txt')
    open(narrow_txt, 'w', encoding='utf-8').write(open(os.path.join(eval_dir, 'series-acme-task.txt'), encoding='utf-8').read().replace('legend: strip', 'legend: strip\ncard_width: 120'))
    narrow = os.path.join(d, 'narrow.drawio')
    subprocess.run([sys.executable, gen, narrow_txt, '--output', narrow], capture_output=True, text=True)
    msgs = [x.msg for x in edgy_lint.series_findings([outs[0], outs[1], narrow])]   # capability map first: no task cards in it
    assert any('task cards are' in m and 'series-acme-task.drawio' in m for m in msgs), msgs
    # every page of a file is compared: a second page with a box legend differs from the strip reference
    two_pages = os.path.join(d, 'two.txt')
    open(two_pages, 'w', encoding='utf-8').write('language: en\npages:\n  - name: "One"\n    map_type: task\n    legend: strip\n    elements:\n      - task: "A"\n      - task: "B"\n'
                                                 '  - name: "Two"\n    map_type: task\n    legend: box\n    elements:\n      - task: "C"\n      - task: "D"\n')
    two = os.path.join(d, 'two.drawio')
    subprocess.run([sys.executable, gen, two_pages, '--output', two], capture_output=True, text=True)
    msgs = [(x.page, x.msg) for x in edgy_lint.series_findings([outs[1], two])]
    assert any(pg == 'Two' and 'legend is a box here' in m for pg, m in msgs), msgs
    # card widths are compared between the pages of one file too
    wide_pages = os.path.join(d, 'wide_pages.txt')
    open(wide_pages, 'w', encoding='utf-8').write('language: en\nlegend: strip\npages:\n  - name: "One"\n    map_type: task\n    elements:\n      - task: "A"\n      - task: "B"\n'
                                                  '  - name: "Two"\n    map_type: task\n    card_width: 300\n    elements:\n      - task: "C"\n      - task: "D"\n')
    wp = os.path.join(d, 'wide_pages.drawio')
    subprocess.run([sys.executable, gen, wide_pages, '--output', wp], capture_output=True, text=True)
    msgs = [(x.page, x.msg) for x in edgy_lint.series_findings([wp])]
    assert any(pg == 'Two' and 'task cards are 300 px wide' in m for pg, m in msgs), msgs
    assert not any(pg == 'One' and 'legend' in m for pg, m in msgs), msgs
    # the full set of widths is compared, not a median: 180/200/200 against 200 is a finding
    mixed = HEAD + vertex(2, 'A', ASSET, 60, 60, 200) + vertex(3, 'B', ASSET, 300, 60, 200) + vertex(4, 'C', ASSET, 540, 60, 180) + TAIL
    plain = HEAD + vertex(2, 'A', ASSET, 60, 60, 200) + vertex(3, 'B', ASSET, 300, 60, 200) + TAIL
    pm = os.path.join(d, 'plain.drawio'); open(pm, 'w', encoding='utf-8').write(plain)
    mm = os.path.join(d, 'mixed.drawio'); open(mm, 'w', encoding='utf-8').write(mixed)
    msgs = [x.msg for x in edgy_lint.series_findings([pm, mm]) if 'asset cards' in x.msg]
    assert len(msgs) == 1 and '180, 200 px wide here vs 200 px' in msgs[0], msgs
    # W120: a wide page without classified elements (containers only) is not a pentagon sequence — it is judged
    empty = _head(1700, 900) + vertex(2, 'Area', CONT, 60, 60, 1500, 60) + TAIL
    assert [x for x in _run_opts(empty) if x.rule == 'W120'], 'an empty element set is not the pentagon exemption'
    # the edge-font baseline comes from the first page that has an edge: an edge-less first file does not silence it
    def mk(name, fs):
        xml = HEAD + vertex(2, 'A', ASSET, 60, 60) + vertex(3, 'B', ASSET, 300, 60) + \
            (edge(10, 'depends on', INFL + f'fontSize={fs};', 2, 3) if fs else '') + TAIL
        path = os.path.join(d, name); open(path, 'w', encoding='utf-8').write(xml); return path
    files = [mk('noedge.drawio', None), mk('f11.drawio', 11), mk('f13.drawio', 13)]
    msgs = [x.msg for x in edgy_lint.series_findings(files) if 'edge label font' in x.msg]
    assert len(msgs) == 1 and '13 px here vs 11 px' in msgs[0] and 'f11.drawio' in msgs[0], msgs
    # CLI: --series adds W121 to the run
    r = subprocess.run([sys.executable, os.path.join(here, 'edgy_lint.py'), '--series', '--json', outs[2], wide], capture_output=True, text=True)
    import json
    assert [x for x in json.loads(r.stdout) if x['rule'] == 'W121']


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
