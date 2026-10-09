#!/usr/bin/env python3
"""Sprint 3 tests: groups/lanes/nesting, label standard, relationship options,
transition overlay, facet containers, purpose hierarchy, organisation role model."""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edgy_parser import EDGYParser, CHANGE_PALETTE  # noqa: E402


def cells_by_label(root):
    out = {}
    for c in root.iter('mxCell'):
        if c.get('vertex') == '1' and c.get('value'):
            import re, html
            key = html.unescape(re.sub(r'<[^>]+>', '\n', c.get('value'))).strip().split('\n')[0].strip()
            out.setdefault(key, c)
    return out


def abs_pos(root, cell):
    by_id = {c.get('id'): c for c in root.iter('mxCell')}
    g = cell.find('mxGeometry')
    x, y = float(g.get('x', 0)), float(g.get('y', 0))
    p = by_id.get(cell.get('parent'))
    while p is not None and p.get('vertex') == '1':
        pg = p.find('mxGeometry')
        x += float(pg.get('x', 0)); y += float(pg.get('y', 0))
        p = by_id.get(p.get('parent'))
    return x, y


def gen(text):
    p = EDGYParser()
    p.parse_input(text)
    xml = p.generate_xml()
    return p, ET.fromstring(xml), xml


def test_group_becomes_container_with_relative_children():
    p, root, xml = gen("""
map_type: capability
elements:
  - group: "1 Customer"
    - capability: "1.1 Customer data" {id: CAP-01}
    - capability: "1.2 Identity"
  - group: "2 Fares"
    - capability: "2.1 Fare products"
  - capability: "Loose capability"
""")
    assert p.warnings == [], p.warnings
    assert len(p.groups) == 2 and p.groups['group1']['members'] == ['capability1', 'capability2']
    assert p.elements['capability4']['group'] is None
    cells = cells_by_label(root)
    g1 = cells['1 Customer']
    assert 'container=1' in g1.get('style') and g1.get('parent') == '1'
    child = cells['1.1 Customer data']
    assert child.get('parent') == g1.get('id'), "child must reference the container via parent"
    cg, gg = child.find('mxGeometry'), g1.find('mxGeometry')
    # relative geometry stays inside the container
    assert 0 <= float(cg.get('x')) and float(cg.get('x')) + float(cg.get('width')) <= float(gg.get('width'))
    assert 0 <= float(cg.get('y')) and float(cg.get('y')) + float(cg.get('height')) <= float(gg.get('height'))
    assert cells['Loose capability'].get('parent') == '1'
    assert '[CAP-01]' in child.get('value'), "id renders in the subtext"
    # containers are emitted before their children (draw-order)
    ids = [c.get('id') for c in root.iter('mxCell')]
    assert ids.index(g1.get('id')) < ids.index(child.get('id'))


def test_tree_inside_group_is_laid_out_as_tree():
    p, root, _ = gen("""
map_type: capability
elements:
  - group: "Area"
    - capability: "Root"
    - capability: "Left"
    - capability: "Right"
relationships:
  - "Root" -> "Left": "contains"
  - "Root" -> "Right": "contains"
""")
    cells = cells_by_label(root)
    rx, ry = abs_pos(root, cells['Root'])
    lx, ly = abs_pos(root, cells['Left'])
    qx, qy = abs_pos(root, cells['Right'])
    assert ly > ry and qy > ry, "children below the root"
    assert lx < qx, "siblings side by side"
    assert cells['Left'].get('parent') == cells['Area'].get('id')


def test_lane_members_stay_at_root_on_the_band():
    p, root, _ = gen("""
facet: architecture
elements:
  - lane: "L1 Channels"
    - channel: "App"
    - channel: "Web"
  - lane: "L2 Core"
    - capability: "Ticketing"
""")
    cells = cells_by_label(root)
    lane = cells['L1 Channels']
    assert 'strokeColor=none' in lane.get('style') and 'container=1' not in lane.get('style')
    app = cells['App']
    assert app.get('parent') == '1', "lane members sit at root level"
    lx, ly = abs_pos(root, lane)
    lg = lane.find('mxGeometry')
    ax, ay = abs_pos(root, app)
    assert lx <= ax <= lx + float(lg.get('width')) and ly <= ay <= ly + float(lg.get('height'))
    l1y = abs_pos(root, lane)[1]
    l2y = abs_pos(root, cells['L2 Core'])[1]
    assert l2y > l1y, "lanes stack top-down"


def test_label_standard_name_subtext_id_size():
    p, root, _ = gen("""
facet: architecture
elements:
  - capability: "Ticketing - sell and validate fares" {id: CAP-05}
  - asset: "Fare engine | runs on-prem" {size: M}
  - process: "Fare change" [internal] {cost: high}
""")
    e1 = p.elements['capability1']
    assert e1['name'] == 'Ticketing' and e1['subtext'] == 'sell and validate fares' and e1['ref'] == 'CAP-05'
    assert 'id' not in e1['metrics'], "reserved keys are not rendered as metrics"
    cells = cells_by_label(root)
    v = cells['Ticketing'].get('value')
    assert v.startswith('<b>Ticketing</b><br>') and '[CAP-05]' in v and 'sell and validate fares' in v
    w = float(cells['Ticketing'].find('mxGeometry').get('width'))
    assert w == 120, f"width follows the NAME length, not the description: {w}"
    g = cells['Fare engine'].find('mxGeometry')
    assert float(g.get('width')) >= 200 and float(g.get('height')) >= 90, "size class M"
    assert 'cost: high' in cells['Fare change'].get('value')


def test_legend_strip_is_a_band_and_page_is_tight():
    p, root, xml = gen("""
map_type: journey
legend: strip
elements:
  - journey: "Plan"
  - journey: "Buy ticket"
  - journey: "Travel"
relationships:
  - "Plan" -> "Buy ticket": "flows"
  - "Buy ticket" -> "Travel": "flows"
""")
    model = root if root.tag == 'mxGraphModel' else root.find('.//mxGraphModel')
    ph = float(model.get('pageHeight'))
    assert ph < 450, f"strip legend: page height follows the content, got {ph}"
    cells = cells_by_label(root)
    title = cells['EDGY 23 — Legend']
    g = title.find('mxGeometry')
    assert float(g.get('y')) > 250 and float(g.get('y')) + 24 <= ph, "legend title sits in the bottom band"
    assert 'Identity (Purpose' not in xml and 'Identity' in xml, "strip uses short chip names"
    # unknown value → warning, box kept
    q = EDGYParser()
    q.parse_input("legend: ribbon\nelements:\n  - asset: \"A\"\n")
    assert q.legend == 'box' and any('legend' in w for w in q.warnings)


def test_element_width_follows_measured_title():
    # 'Illinois' is narrow, 'WWW MMM' is wide — same character count, different measured widths
    p, root, _ = gen("map_type: asset\nequal_cards: false\nelements:\n  - asset: \"IIIIIIIIIIIIIIII\"\n  - asset: \"WWWWWWWWWWWWWWWW\"\n")
    cells = cells_by_label(root)
    narrow = float(cells['IIIIIIIIIIIIIIII'].find('mxGeometry').get('width'))
    wide = float(cells['WWWWWWWWWWWWWWWW'].find('mxGeometry').get('width'))
    assert narrow < wide, (narrow, wide)
    assert wide <= 280 and narrow >= 120


EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples')


def _triad_all():
    with open(os.path.join(EXAMPLES, 'triad-all-facets.txt'), encoding='utf-8') as f:
        return gen(f.read())


def test_triad_all_facets_positions():
    """The 12 primaries sit on the slot table (centres, ±2 px); page height ≤ 1.2 × width."""
    p, root, xml = _triad_all()
    cells = cells_by_label(root)
    expected = {  # name → slot centre (cx, cy)
        'Effortless everyday travel in the region': (650, 80), 'From a single bus line to a regional mobility platform': (400, 220),
        'We keep the region moving': (910, 220), 'Acme Transit': (380, 400), 'Acme Transit brand': (920, 400),
        'Account-based travel': (230, 560), 'Account-based ticketing platform': (180, 720), 'Sell and validate tickets': (380, 840),
        'Buy a monthly subscription': (1070, 560), 'Mobile app': (1170, 720), 'Commute across two operators': (920, 840),
        'Regional travel subscription': (650, 900),
    }
    for name, (cx, cy) in expected.items():
        c = cells[name]
        x, y = abs_pos(root, c)
        g = c.find('mxGeometry')
        got = (x + float(g.get('width')) / 2, y + float(g.get('height')) / 2)
        assert abs(got[0] - cx) <= 2 and abs(got[1] - cy) <= 2, (name, got, (cx, cy))
    model = root if root.tag == 'mxGraphModel' else root.find('.//mxGraphModel')
    pw, ph = float(model.get('pageWidth')), float(model.get('pageHeight'))
    assert ph <= 1.2 * pw, (pw, ph)
    # the primary flag moved PRD-01 to the ring although it is not the first product
    assert p.elements[[e for e, v in p.elements.items() if v.get('ref') == 'PRD-01'][0]].get('primary')


def test_triad_further_panels_and_dropped_links():
    p, root, xml = _triad_all()
    cells = cells_by_label(root)
    by_id = {c.get('id'): c for c in root.iter('mxCell')}
    panels = [c for c in root.iter('mxCell') if c.get('vertex') == '1' and (c.get('value') or '').startswith('Further ')]
    assert len(panels) == 12, [c.get('value') for c in panels]           # every type has at least one non-primary
    panel_ids = {c.get('id') for c in panels}
    chip = cells['Single ticket']
    assert chip.get('parent') in panel_ids, "non-primary product sits in a Further panel"
    for c in root.iter('mxCell'):
        if c.get('edge') == '1' and c.get('source'):
            assert by_id[c.get('source')].get('parent') not in panel_ids and by_id[c.get('target')].get('parent') not in panel_ids, \
                "no edge may touch a panel chip"
    assert any('2 relationship(s) not drawn' in w for w in p.warnings), p.warnings
    # all 24 core links are drawn exactly once
    verbs = [c.get('value') for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source')]
    assert len(verbs) == 24, (len(verbs), verbs)


def test_triad_edges_straight_with_two_detours():
    p, root, xml = _triad_all()
    edges = [c for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source')]
    with_points = [c for c in edges if c.find('mxGeometry/Array[@as="points"]') is not None]
    assert len(with_points) == 2, len(with_points)
    anchored_straight = 0
    for c in edges:
        st = c.get('style')
        if c in with_points:
            assert 'edgeStyle=orthogonalEdgeStyle' in st and 'exitX=' in st, st
        else:
            assert 'edgeStyle=none' in st, st
            anchored_straight += 'exitX=' in st
    assert anchored_straight == 2, anchored_straight      # organisation → purpose and brand → purpose use corner ports
    assert sum(1 for c in edges if c.find('mxGeometry/mxPoint[@as="offset"]') is not None) >= 20, "default label shifts"
    # triad defaults to the strip legend; an explicit legend: box wins
    assert 'Identity (Purpose' not in xml and 'EDGY 23 — Legend' in xml
    q = EDGYParser()
    q.parse_input("facet: architecture\nmap_type: triad\nlegend: box\nelements:\n  - capability: \"A\"\n  - product: \"P\"\n")
    assert 'Identity (Purpose' in q.generate_xml()


def test_triad_single_facet_primary_flag_and_layout_from_ignored():
    p, root, xml = gen("""
facet: architecture
map_type: triad
layout_from: nowhere.archimate#View
elements:
  - capability: "First"
  - capability: "Chosen" {primary: true}
  - asset: "Store"
  - process: "Run"
  - product: "Thing"
  - organisation: "Org"
relationships:
  - "Chosen" -> "Store": "requires"
  - "Org" -> "Thing": "makes"
""")
    cells = cells_by_label(root)
    panels = {c.get('id') for c in root.iter('mxCell') if (c.get('value') or '').startswith('Further ')}
    assert cells['First'].get('parent') in panels and cells['Chosen'].get('parent') not in panels
    assert any('layout_from' in w for w in p.warnings)
    x, y = abs_pos(root, cells['Chosen'])
    g = cells['Chosen'].find('mxGeometry')
    assert abs(x + float(g.get('width')) / 2 - 230) <= 2 and abs(y + float(g.get('height')) / 2 - 225) <= 2


def test_triad_panel_titles_follow_language():
    base = "facet: architecture\nmap_type: triad\n{lang}elements:\n  - capability: \"A\"\n  - capability: \"B\"\n  - product: \"P\"\n"
    for lang, title in (('', 'Further capabilities'), ('language: fi\n', 'Muut kyvykkyydet'),
                        ('language: fr\n', 'Autres capacités'), ('language: de\n', 'Weitere Fähigkeiten')):
        p, root, xml = gen(base.format(lang=lang))
        titles = [c.get('value') for c in root.iter('mxCell') if (c.get('value') or '').split(' ')[0] in ('Further', 'Muut', 'Autres', 'Weitere')]
        assert titles == [title], (lang, titles)
    q = EDGYParser()
    q.parse_input("language: sv\nelements:\n  - asset: \"A\"\n")
    assert q.language == 'en' and any('language' in w for w in q.warnings)


FI_PURPOSE = """
map_type: purpose
language: fi
elements:
  - purpose: "Sujuva arki" [vahvistettu]
  - purpose: "Saumattomat matkaketjut" [analyyttinen]
  - outcome: "Ovelta ovelle −15 %" {status: proposed}
  - organisation: "Joukkoliikennelautakunta"
relationships:
  - "Sujuva arki" -> "Saumattomat matkaketjut": "contains"
  - "Ovelta ovelle −15 %" -> "Saumattomat matkaketjut": "measures"
  - "Joukkoliikennelautakunta" -> "Sujuva arki": "pursues"
"""


def _edge_labels(root):
    return [c.get('value') for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source')]


def test_verbs_render_in_map_language():
    p, root, xml = gen(FI_PURPOSE)
    labels = _edge_labels(root)
    assert sorted(labels) == ['mittaa', 'sisältää', 'tavoittelee'], labels     # contains / measures / pursues → fi
    assert p.relationships[0]['label'] == 'contains', 'the model keeps the canonical verb'
    # already Finnish and free text stay as written; translate_verbs: false keeps English
    p2, root2, _ = gen(FI_PURPOSE.replace('"contains"', '"sisältää"').replace('"pursues"', '"ajaa eteenpäin"'))
    assert sorted(_edge_labels(root2)) == ['ajaa eteenpäin', 'mittaa', 'sisältää']
    p3, root3, _ = gen(FI_PURPOSE.replace('language: fi', 'language: fi\ntranslate_verbs: false'))
    assert 'contains' in _edge_labels(root3)
    # merged duplicate labels translate per part
    p4, root4, _ = gen("facet: architecture\nlanguage: de\nelements:\n  - capability: \"A\"\n  - asset: \"B\"\n"
                       "relationships:\n  - \"A\" -> \"B\": \"requires\"\n  - \"A\" -> \"B\": \"depends on\"\n")
    assert _edge_labels(root4) == ['erfordert / hängt ab von'], _edge_labels(root4)
    # no language: → verbs untouched (byte-identity of the existing examples)
    p5, root5, _ = gen(FI_PURPOSE.replace('language: fi\n', ''))
    assert 'contains' in _edge_labels(root5)


def test_flow_verbs_sends_receives_translate():
    from edgy_vocab import translate, languages_of
    assert translate('sends', 'fi') == 'lähettää' and translate('receives', 'de') == 'empfängt' and translate('envoie', 'en') == 'sends'
    assert languages_of('vastaanottaa') == {'fi'}
    p, root, _ = gen('map_type: asset\nlanguage: fi\nelements:\n  - asset: "A"\n  - asset: "B"\nrelationships:\n  - "A" -> "B": "sends"\n')
    assert 'lähettää' in _edge_labels(root) and p.relationships[0]['kind'] == 'flow'


def test_ambiguous_spelling_translates_by_pair():
    from edgy_vocab import translate
    assert translate('erscheint in', 'en', ('product', 'journey')) == 'features in'
    assert translate('erscheint in', 'en', ('brand', 'journey')) == 'appears in'
    assert translate('erscheint in', 'en') == 'appears in', 'without a pair the first row wins'
    p, root, xml = gen('map_type: journey\nlanguage: en\nelements:\n  - product: "App"\n  - journey: "Commute"\nrelationships:\n  - "App" -> "Commute": "erscheint in"\n')
    assert _edge_labels(root) == ['features in'], _edge_labels(root)
    assert not any('Ydinlinkki' in w for w in p.warnings), p.warnings


def test_core_link_alias_is_in_the_vocabulary_index():
    from edgy_vocab import translate, languages_of
    assert languages_of('osa') == {'fi'} and translate('osa', 'en') == 'is part of' and translate('osa', 'fi') == 'on osa'


def test_german_produces_data_is_a_flow_verb():
    p, root, xml = gen('map_type: asset\nlanguage: de\nelements:\n  - asset: "A"\n  - asset: "B"\nrelationships:\n  - "A" -> "B": "erzeugt Daten"\n')
    assert p.relationships[0]['kind'] == 'flow' and not any('tuntematon' in w.lower() for w in p.warnings), p.warnings
    import edgy_lint, tempfile
    d = tempfile.mkdtemp(); path = os.path.join(d, 'de.drawio'); open(path, 'w', encoding='utf-8').write(xml)
    f = edgy_lint.lint_file(path, edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False))
    assert not [x for x in f if x.rule in ('W105', 'W116')], [str(x) for x in f]


def test_legend_follows_language():
    import html as _html
    from edgy_parser import LEGEND_TEXT
    for lang in ('fi', 'fr', 'de'):
        p, root, xml = gen(FI_PURPOSE.replace('language: fi', f'language: {lang}'))
        xml = _html.unescape(_html.unescape(xml))      # value="…&amp;#x27;…": html label escaped once, XML once
        L = LEGEND_TEXT[lang]
        assert L['title'] in xml and L['lines'][2] in xml and L['chips'][0] in xml, (lang, L['title'])
        assert 'Tree (hierarkia)' not in xml, lang
        with_overlay = FI_PURPOSE.replace('language: fi', f'language: {lang}\nlegend: strip') \
                                 .replace('  - organisation:', '  - capability: "K" {change: new}\n  - organisation:')
        p2, root2, xml2 = gen(with_overlay)
        xml2 = _html.unescape(_html.unescape(xml2))
        for s in (L['title'], L['lines_short'][0], L['overlay_short'], L['change']['new']):
            assert s in xml2, (lang, s)
    # default: exactly the old English strings
    p, root, xml = gen(FI_PURPOSE.replace('language: fi\n', ''))
    assert 'EDGY 23 — Legend' in xml and 'Tree (hierarkia)' in xml


def test_purpose_tree_parent_centred_and_no_branch_through_children():
    import tempfile
    import edgy_lint
    with open(os.path.join(EXAMPLES, 'eval', 'fixture-f5-purpose-tree.txt'), encoding='utf-8') as f:
        p, root, xml = gen(f.read())
    cells = cells_by_label(root)
    parent = cells['Make everyday travel in the region effortless']
    kids = [cells[n] for n in ('Seamless travel chains', 'Affordable and fair fares for every traveller group',
                               'Zero-emission fleet', 'Trusted real-time information')]
    px, py = abs_pos(root, parent)
    pg = parent.find('mxGeometry')
    pcx = px + float(pg.get('width')) / 2
    xs = [abs_pos(root, k)[0] for k in kids]
    ws = [float(k.find('mxGeometry').get('width')) for k in kids]
    assert min(xs) < pcx < max(x + w for x, w in zip(xs, ws)), "parent over its children row"
    assert abs(pcx - (min(xs) + max(x + w for x, w in zip(xs, ws))) / 2) < 60, "parent roughly centred"
    ys = {round(abs_pos(root, k)[1]) for k in kids}
    assert len(ys) == 1, f"children on one row: {ys}"
    out = cells['Fare satisfaction ≥ 4.0 / 5']
    assert abs_pos(root, out)[1] > abs_pos(root, kids[1])[1], "Outcome below its purpose"
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        findings = edgy_lint.lint_file(path, edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False))
    finally:
        os.unlink(path)
    assert not any(x.rule == 'W111' for x in findings), [str(x) for x in findings if x.rule == 'W111']


def test_transition_overlay_strokes_and_legend():
    p, root, xml = gen("""
facet: architecture
elements:
  - asset: "Legacy" {change: replace}
  - asset: "New platform" {change: uusi}
  - asset: "Gateway" {change: decide}
  - asset: "Plain"
relationships:
  - "New platform" -> "Legacy": "depends on" {change: replace}
""")
    assert p.uses_change_overlay and p.warnings == [], p.warnings
    cells = cells_by_label(root)
    assert f"strokeColor={CHANGE_PALETTE['replace'][0]}" in cells['Legacy'].get('style')
    assert 'strokeWidth=4' in cells['Legacy'].get('style')
    assert 'fillColor=#a6c0ff' in cells['Legacy'].get('style'), "fill stays the facet colour"
    assert f"strokeColor={CHANGE_PALETTE['new'][0]}" in cells['New platform'].get('style'), "fi synonym accepted"
    assert 'dashed=1' in cells['Gateway'].get('style'), "decide is dashed"
    assert 'strokeColor=#FFFFFF' in cells['Plain'].get('style')
    edge = next(c for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('value') == 'depends on')
    assert f"strokeColor={CHANGE_PALETTE['replace'][0]}" in edge.get('style')
    assert 'Transition (extension' in xml and 'keep / säilyy' in xml, "overlay legend rows present"
    # no overlay → no overlay legend
    _, _, xml2 = gen("facet: architecture\nelements:\n  - asset: \"A\"\n")
    assert 'Transition (extension' not in xml2


def test_unknown_change_value_warns_and_is_ignored():
    p, root, _ = gen("""
facet: architecture
elements:
  - asset: "A" {change: maybe}
""")
    assert any('change' in w for w in p.warnings), p.warnings
    assert not p.uses_change_overlay


def test_relationship_options_sides_via_label_and_merge():
    p, root, _ = gen("""
facet: architecture
elements:
  - capability: "Cap"
  - asset: "Sys"
relationships:
  - "Cap" -> "Sys": "requires" {from: top, to: bottom, via: [(300, 40), (500, 40)], label: source}
  - "Cap" -> "Sys": "depends on"
  - "Sys" -> "Cap": "enables" {label: elsewhere}
""")
    assert any("label-arvo" in w for w in p.warnings), p.warnings
    edges = [c for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source') and not c.get('id', '').startswith('leg')]
    merged = next(c for c in edges if ' / ' in (c.get('value') or ''))
    assert merged.get('value') == 'requires / depends on', merged.get('value')
    st = merged.get('style')
    assert 'exitY=0.0' in st and 'entryY=1.0' in st, f"from top / to bottom override anchors: {st}"
    assert 'endArrow=classic' in st, "merged edge keeps core-link style when one verb is a core link"
    geo = merged.find('mxGeometry')
    assert geo.get('x') == '-0.5', "label near the source"
    pts = geo.find("Array[@as='points']")
    assert pts is not None and len(pts.findall('mxPoint')) == 2
    assert sum(1 for c in edges if (c.get('value') or '').startswith('requires')) == 1, "duplicates merged into one edge"


def test_facet_all_containers_and_intersection_between_columns():
    p, root, _ = gen("""
facet: all
elements:
  - purpose: "Purpose"
  - content: "Content"
  - story: "Story"
  - capability: "Capability"
  - asset: "Asset"
  - process: "Process"
  - task: "Task"
  - channel: "Channel"
  - journey: "Journey"
  - organisation: "Org"
  - product: "Prod"
  - brand: "Brand"
""")
    cells = cells_by_label(root)
    for title in ('Identity', 'Architecture', 'Experience'):
        assert title in cells and 'container=1' in cells[title].get('style'), f"facet container {title}"
    assert cells['Purpose'].get('parent') == cells['Identity'].get('id')
    assert cells['Asset'].get('parent') == cells['Architecture'].get('id')
    ix = abs_pos(root, cells['Identity'])[0]; iw = float(cells['Identity'].find('mxGeometry').get('width'))
    ax = abs_pos(root, cells['Architecture'])[0]; aw = float(cells['Architecture'].find('mxGeometry').get('width'))
    ex = abs_pos(root, cells['Experience'])[0]
    ox = abs_pos(root, cells['Org'])[0]; px = abs_pos(root, cells['Prod'])[0]
    assert ix + iw <= ox < ax, "Organisation between Identity and Architecture"
    assert ax + aw <= px < ex, "Product between Architecture and Experience"
    by = abs_pos(root, cells['Brand'])[1]
    ih = float(cells['Identity'].find('mxGeometry').get('height'))
    assert by >= abs_pos(root, cells['Identity'])[1] + ih, "Brand below the facets as the Identity↔Experience bridge"


def test_single_facet_intersection_row_wraps():
    p, root, _ = gen("""
facet: architecture
elements:
  - capability: "Cap"
  - product: "P1"
  - product: "P2"
  - product: "P3"
  - product: "P4"
  - product: "P5"
  - product: "P6"
""")
    cells = cells_by_label(root)
    ys = {abs_pos(root, cells[f'P{i}'])[1] for i in range(1, 7)}
    assert len(ys) == 2, f"six products wrap into two rows, got rows at {sorted(ys)}"
    positions = p._calculate_layout()
    sizes = {e: p._get_element_size(p.elements[e]) for e in positions}
    ids = list(positions)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            (ax, ay), (bx, by) = positions[ids[i]], positions[ids[j]]
            (aw, ah), (bw, bh) = sizes[ids[i]], sizes[ids[j]]
            assert ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay, f"overlap {ids[i]} / {ids[j]}"


def test_purpose_hierarchy_layout():
    p, root, _ = gen("""
map_type: purpose
elements:
  - purpose: "Mission"
  - purpose: "Focus A"
  - purpose: "Focus B"
  - outcome: "KPI A1"
  - content: "Promise"
  - story: "Origin"
  - organisation: "Board"
  - brand: "Acme"
relationships:
  - "Mission" -> "Focus A": "contains"
  - "Mission" -> "Focus B": "contains"
  - "KPI A1" -> "Focus A": "measures"
""")
    assert p.warnings == [], p.warnings
    cells = cells_by_label(root)
    pos = {k: abs_pos(root, cells[k]) for k in ('Mission', 'Focus A', 'Focus B', 'KPI A1', 'Promise', 'Origin', 'Board', 'Acme')}
    assert pos['Focus A'][1] > pos['Mission'][1] and pos['Focus B'][1] > pos['Mission'][1], "sub-purposes below the top purpose"
    assert pos['KPI A1'][1] > pos['Focus A'][1] and abs(pos['KPI A1'][0] - pos['Focus A'][0]) < 60, "KPI under its focus area"
    assert pos['Board'][1] == pos['Mission'][1] and pos['Acme'][1] == pos['Mission'][1], "Organisation and Brand in the top row"
    assert pos['Promise'][0] < pos['Mission'][0] < pos['Origin'][0], "Content left, Story right"


def test_organisation_role_model_layout():
    p, root, _ = gen("""
map_type: organisation
elements:
  - process: "Steer"
  - process: "Produce"
  - organisation: "Board"
  - organisation: "Team"
  - organisation: "Partner"
relationships:
  - "Board" -> "Steer": "performs"
  - "Team" -> "Produce": "performs"
""")
    cells = cells_by_label(root)
    pos = {k: abs_pos(root, cells[k]) for k in ('Steer', 'Produce', 'Board', 'Team', 'Partner')}
    assert pos['Steer'][1] == pos['Produce'][1], "roles in one top row"
    assert pos['Board'][1] > pos['Steer'][1] and abs(pos['Board'][0] - pos['Steer'][0]) < 10, "actor under its role"
    assert abs(pos['Team'][0] - pos['Produce'][0]) < 10
    assert pos['Partner'][0] > pos['Produce'][0], "actor without a role goes to the right"


def test_name_matching_uses_name_before_separator():
    p, root, _ = gen("""
map_type: organisation
elements:
  - process: "Procure | tendering"
  - organisation: "Procurement office"
relationships:
  - "Procurement office" -> "Procure": "performs"
""")
    rel = p.relationships[0]
    assert p.elements[rel['target']]['type'] == 'process', "'Procure' must match the process, not the organisation by substring"


def test_reference_layout_actors_left_externals_right():
    p, root, _ = gen("""
map_type: reference
elements:
  - organisation: "Passengers"
  - lane: "L1 Channels"
    - channel: "App"
  - lane: "L2 Core"
    - capability: "Ticketing"
  - asset: "Registry" [external]
relationships:
  - "Ticketing" -> "Registry": "depends on"
""")
    assert p.warnings == [], p.warnings
    cells = cells_by_label(root)
    lane_x = abs_pos(root, cells['L1 Channels'])[0]
    lane_w = float(cells['L1 Channels'].find('mxGeometry').get('width'))
    assert abs_pos(root, cells['Passengers'])[0] < lane_x, "actor left of the lanes"
    assert abs_pos(root, cells['Registry'])[0] >= lane_x + lane_w, "external right of the lanes"
    assert abs_pos(root, cells['L2 Core'])[1] > abs_pos(root, cells['L1 Channels'])[1]


def test_summary_layout_rows_and_warning():
    p, root, _ = gen("""
map_type: summary
elements:
  - organisation: "Who A"
  - organisation: "Who B"
  - process: "Does"
  - outcome: "Result"
  - content: "Used for"
""")
    assert p.warnings == [], p.warnings
    cells = cells_by_label(root)
    ya, yb = abs_pos(root, cells['Who A'])[1], abs_pos(root, cells['Who B'])[1]
    assert ya == yb < abs_pos(root, cells['Does'])[1] < abs_pos(root, cells['Result'])[1] < abs_pos(root, cells['Used for'])[1]
    many = EDGYParser()
    many.parse_input("map_type: summary\nelements:\n" + "".join(f'  - organisation: "O{i}"\n' for i in range(5)))
    many.generate_xml()
    assert any('Summary' in w for w in many.warnings), many.warnings


def test_layout_from_archimate_positions_matched_elements():
    here = os.path.dirname(os.path.abspath(__file__))
    model = os.path.join(here, '..', 'examples', 'current-state.archimate')
    p, root, _ = gen(f"""
facet: architecture
layout_from: {model}#Application landscape scale=2 dx=10 dy=0
elements:
  - asset: "Mobile app"
  - asset: "Legacy fare engine"
  - asset: "Brand new platform"
""")
    cells = cells_by_label(root)
    # Mobile app at view (60,60) → ((60+10)*2, 60*2) = (140, 120); container offset applies, so compare relative order/scale
    ma = abs_pos(root, cells['Mobile app']); lf = abs_pos(root, cells['Legacy fare engine'])
    assert abs((lf[1] - ma[1]) - (220 - 60) * 2) < 1, f"vertical distance scaled by 2: {ma} {lf}"
    assert abs(lf[0] - ma[0]) < 1, "same column kept"
    bn = abs_pos(root, cells['Brand new platform'])
    assert bn[1] > lf[1], "unmatched element placed below the anchored ones"
    assert any('ei ole tavoitetilassa' in w and 'web shop' in w for w in p.warnings), p.warnings
    missing = EDGYParser(); missing.parse_input("facet: architecture\nlayout_from: /no/such.archimate#X\nelements:\n  - asset: \"A\"\n")
    missing.generate_xml()
    assert any('ei luettavissa' in w for w in missing.warnings), missing.warnings


# ---- Sprint 15: layout options and equal cards ------------------------------
def _widths(root, names):
    cells = cells_by_label(root)
    return {n: (float(cells[n].find('mxGeometry').get('width')), float(cells[n].find('mxGeometry').get('height'))) for n in names}


def test_equal_cards_default():
    """Same type → same width and height on the page (max of both, width ≤ 280); equal_cards: false restores measured widths."""
    src = 'map_type: asset\nelements:\n  - asset: "Short"\n  - asset: "A considerably longer asset name here"\n  - asset: "Mid - with a description line"\n  - people: "Driver"\n'
    p, root, _ = gen(src)
    ws = _widths(root, ['Short', 'A considerably longer asset name here', 'Mid'])
    assert len({w for w, _ in ws.values()}) == 1 and len({h for _, h in ws.values()}) == 1, ws
    assert max(w for w, _ in ws.values()) <= 280
    assert _widths(root, ['Driver'])['Driver'][0] < 120, 'a lone person keeps its own size'
    p2, root2, _ = gen(src.replace('map_type: asset', 'map_type: asset\nequal_cards: false'))
    ws2 = _widths(root2, ['Short', 'A considerably longer asset name here'])
    assert ws2['Short'][0] < ws2['A considerably longer asset name here'][0], ws2


def test_card_width_option():
    src = 'map_type: asset\ncard_width: 200\nelements:\n  - asset: "Short"\n  - asset: "A considerably longer asset name that wraps"\n  - asset: "Big" {size: L}\n  - people: "Driver"\n'
    p, root, _ = gen(src)
    ws = _widths(root, ['Short', 'A considerably longer asset name that wraps', 'Big', 'Driver'])
    assert ws['Big'][0] == 270, 'size class L stays wider than card_width'   # equalised with the others → all 270
    assert ws['Short'][0] == ws['A considerably longer asset name that wraps'][0] == 270
    assert ws['Driver'][0] < 120, 'person shape ignores card_width'
    p2, root2, _ = gen(src.replace('  - asset: "Big" {size: L}\n', ''))
    ws2 = _widths(root2, ['Short', 'A considerably longer asset name that wraps'])
    assert {w for w, _ in ws2.values()} == {200.0}, ws2
    bad = EDGYParser(); bad.parse_input('map_type: asset\ncard_width: 7\nelements:\n  - asset: "A"\n')
    assert any('card_width' in w for w in bad.warnings), bad.warnings


BALANCED = """map_type: capability
group_columns: 2
cards_per_row: 2
equal_group_width: true
align_groups: grid
elements:
  - group: "Area one"
    - capability: "A1"
    - capability: "A2 with a longer name"
    - capability: "A3"
  - group: "Area two"
    - capability: "B1"
  - group: "Area three with a long title"
    - capability: "C1"
    - capability: "C2"
    - capability: "C3"
    - capability: "C4"
  - group: "Area four"
    - capability: "D1"
    - capability: "D2"
"""


def test_balanced_grid():
    """2 × 2 containers on exact rows and columns: equal widths, two distinct x and two distinct y, row heights equal."""
    import edgy_lint
    p, root, xml = gen(BALANCED)
    cells = cells_by_label(root)
    boxes = {}
    for n in ('Area one', 'Area two', 'Area three with a long title', 'Area four'):
        g = cells[n].find('mxGeometry')
        boxes[n] = tuple(float(g.get(k)) for k in ('x', 'y', 'width', 'height'))
    assert len({b[2] for b in boxes.values()}) == 1, boxes
    xs = sorted({b[0] for b in boxes.values()}); ys = sorted({b[1] for b in boxes.values()})
    assert len(xs) == 2 and len(ys) == 2, (xs, ys)
    assert xs[1] - xs[0] == boxes['Area one'][2] + 40, 'second column exactly one gap after the first'
    assert boxes['Area one'][3] == boxes['Area two'][3] and boxes['Area three with a long title'][3] == boxes['Area four'][3]
    # cards_per_row: 2 → C1..C4 on two rows inside their container
    cx = {n: abs_pos(root, cells[n])[0] for n in ('C1', 'C2', 'C3', 'C4')}
    assert cx['C1'] == cx['C3'] and cx['C2'] == cx['C4'] and cx['C1'] < cx['C2'], cx
    import tempfile
    d = tempfile.mkdtemp(); path = os.path.join(d, 'g.drawio')
    open(path, 'w', encoding='utf-8').write(xml)
    ns = edgy_lint.main.__globals__['argparse'].Namespace
    f = edgy_lint.lint_file(path, ns(no_legend=False))
    assert not [x for x in f if x.rule in ('W117', 'W118', 'W119', 'W120')], [str(x) for x in f]


def test_equal_group_width():
    p, root, _ = gen(BALANCED.replace('equal_group_width: true\n', '').replace('align_groups: grid\n', ''))
    cells = cells_by_label(root)
    ws = {n: float(cells[n].find('mxGeometry').get('width')) for n in ('Area one', 'Area two')}
    assert ws['Area one'] != ws['Area two'], ws
    p, root, _ = gen(BALANCED.replace('align_groups: grid\n', ''))
    cells = cells_by_label(root)
    ws = {n: float(cells[n].find('mxGeometry').get('width')) for n in ('Area one', 'Area two', 'Area four')}
    assert len(set(ws.values())) == 1, ws


def test_uniform_content_margin():
    """Every layout puts the content's top-left corner at (60, 60) — the series check (W121) relies on it."""
    for src in ('map_type: asset\nelements:\n  - asset: "A"\n  - asset: "B"\n',
                'map_type: process\nelements:\n  - process: "A"\n  - process: "B"\n',
                BALANCED):
        p, root, _ = gen(src)
        xs, ys = [], []
        for c in root.iter('mxCell'):
            st = c.get('style') or ''
            if c.get('vertex') == '1' and c.get('parent') == '1' and ('fillColor=#a6c0ff' in st or 'container=1' in st):
                x, y = abs_pos(root, c); xs.append(x); ys.append(y)
        assert min(xs) == 60 and min(ys) == 60, (min(xs), min(ys), src[:20])


# ---- Sprint 16: task stakeholder map ---------------------------------------------
def _edges(root):
    return [c for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source') and c.get('target')]


def test_task_inventory_has_no_edges():
    """Explicit lanes + stages: a matrix with header cells, lane members at root, 0 edges, strict lint clean."""
    import edgy_lint, tempfile
    with open(os.path.join(EXAMPLES, 'task-stakeholder-map.txt'), encoding='utf-8') as f:
        text = f.read()
    import edgy_document
    pages = edgy_document.parse_document(text)
    inv = dict(pages)['Inventory']
    xml = inv.generate_xml(); root = ET.fromstring(xml)
    assert not _edges(root), 'inventory variant draws no relationship'
    headers = [c for c in root.iter('mxCell') if 'edgyRole=header' in (c.get('style') or '')]
    assert [c.get('value') for c in headers] == ['Plan', 'Buy', 'Ride']
    cells = cells_by_label(root)
    hx = {c.get('value'): float(c.find('mxGeometry').get('x')) for c in headers}
    assert abs(abs_pos(root, cells['Buy a ticket'])[0] - hx['Buy']) < 1 and abs(abs_pos(root, cells['Check tickets'])[0] - hx['Ride']) < 1
    assert abs_pos(root, cells['Validate the ticket'])[0] == abs_pos(root, cells['Follow the vehicle'])[0], 'two tasks of one stage stack'
    assert 'stage: Ride' not in xml, 'the stage is shown by the column, not in the subtext'
    assert float(headers[0].find('mxGeometry').get('y')) >= 20, 'headers stay on the page'
    d = tempfile.mkdtemp(); path = os.path.join(d, 'i.drawio'); open(path, 'w', encoding='utf-8').write(xml)
    f = edgy_lint.lint_file(path, edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False))
    assert not f, [str(x) for x in f]


def test_task_lanes_derived_from_stakeholder_relationships():
    p, root, xml = gen("""
map_type: task
elements:
  - people: "Passenger"
  - organisation: "Customer service"
  - task: "Plan a trip"
  - task: "Buy a ticket"
  - task: "Answer a refund claim"
  - task: "Loose task"
relationships:
  - "Passenger" -> "Plan a trip": "performs"
  - "Passenger" -> "Buy a ticket": "performs"
  - "Customer service" -> "Answer a refund claim": "performs"
""")
    lanes = [c for c in root.iter('mxCell') if c.get('vertex') == '1' and 'verticalAlign=top' in c.get('style', '') and 'strokeColor=none' in c.get('style', '')]
    assert sorted(c.get('value') for c in lanes) == ['Customer service', 'Passenger'], [c.get('value') for c in lanes]
    cells = cells_by_label(root)
    assert 'Passenger' in cells and cells['Passenger'] in lanes, 'the stakeholder is the lane, not a box'
    assert not _edges(root), 'stakeholder relationships become lane membership'
    assert any('stakeholder(s) drawn as lanes' in w for w in p.warnings), p.warnings
    assert abs_pos(root, cells['Loose task'])[1] > abs_pos(root, cells['Answer a refund claim'])[1], 'unassigned task below the lanes'
    # a task related to two stakeholders: one lane holds it, the other lane names it — no box, no edge
    p2, root2, _ = gen("""
map_type: task
elements:
  - people: "Passenger"
  - people: "Driver"
  - task: "Validate the ticket"
relationships:
  - "Passenger" -> "Validate the ticket": "performs"
  - "Driver" -> "Validate the ticket": "performs"
""")
    lanes2 = sorted(c.get('value') for c in root2.iter('mxCell') if c.get('vertex') == '1' and 'verticalAlign=top' in c.get('style', '') and 'strokeColor=none' in c.get('style', ''))
    assert lanes2 == ['Driver (also: Validate the ticket)', 'Passenger'], lanes2
    assert not _edges(root2) and {p2.elements[h]['name'] for h in p2._hidden} == {'Passenger', 'Driver'}
    assert any('shares 1 task(s)' in w for w in p2.warnings), p2.warnings
    # a stakeholder with a relationship to something that is not a task keeps its box and its edges
    p3, root3, _ = gen("""
map_type: task
elements:
  - organisation: "Acme Transit"
  - people: "Passenger"
  - purpose: "Effortless travel"
  - task: "Plan a trip"
  - task: "Buy a ticket"
relationships:
  - "Acme Transit" -> "Plan a trip": "performs"
  - "Acme Transit" -> "Effortless travel": "pursues"
  - "Passenger" -> "Buy a ticket": "performs"
""")
    lanes3 = [c.get('value') for c in root3.iter('mxCell') if c.get('vertex') == '1' and 'verticalAlign=top' in c.get('style', '') and 'strokeColor=none' in c.get('style', '')]
    assert lanes3 == ['Passenger'], lanes3
    labels3 = sorted(c.get('value') for c in _edges(root3))
    assert labels3 == ['performs', 'pursues'], labels3
    assert any("keeps its box" in w for w in p3.warnings), p3.warnings


def test_task_path_variant():
    """task → journey / channel without lanes: journeys above, tasks in input order, channels below; vertical ports."""
    import edgy_lint, tempfile, edgy_document
    with open(os.path.join(EXAMPLES, 'task-stakeholder-map.txt'), encoding='utf-8') as f:
        pages = edgy_document.parse_document(f.read())
    path_page = dict(pages)['Path']
    xml = path_page.generate_xml(); root = ET.fromstring(xml)
    cells = cells_by_label(root)
    jy = abs_pos(root, cells['Daily commute'])[1]
    ty = {n: abs_pos(root, cells[n])[1] for n in ('Plan a trip', 'Buy a ticket', 'Validate the ticket', 'Follow the vehicle')}
    cy = abs_pos(root, cells['Mobile app'])[1]
    assert jy < min(ty.values()) and len(set(ty.values())) == 1 and max(ty.values()) < cy
    xs = [abs_pos(root, cells[n])[0] for n in ('Plan a trip', 'Buy a ticket', 'Validate the ticket', 'Follow the vehicle')]
    assert xs == sorted(xs), 'input order left to right'
    assert len(_edges(root)) == 8
    d = tempfile.mkdtemp(); path = os.path.join(d, 'p.drawio'); open(path, 'w', encoding='utf-8').write(xml)
    f = edgy_lint.lint_file(path, edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False))
    assert not f, [str(x) for x in f]


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f"Testing {t.__name__}...")
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} structure tests passed")


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
