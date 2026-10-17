#!/usr/bin/env python3
"""Tests for the document graph and identity rules (edgy-diagram 2.8.0, Sprint 21a):
quote-aware options, attributes that are not printed, relationship attributes,
model ids in the output (edgyId / edgyOcc …), E014 / E015, cross-page
relationships, `draw: false` model pages, `expand:` pages, two-line edge
labels and the influence verbs of the architecture views."""

import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile  # noqa: E402
from edgy_parser import EDGYParser, split_options  # noqa: E402
import edgy_lint  # noqa: E402
import edgy_geometry as geo  # noqa: E402


def _cells(xml):
    return list(ET.fromstring(xml).iter('mxCell'))


def _drawio(pages):
    return build_mxfile([(n, p.generate_xml()) for n, p in pages])


def _lint(xml):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False)
        return [(x.rule, x.level, x.msg) for x in edgy_lint.lint_file(path, opts)]
    finally:
        os.unlink(path)


def test_split_options_respects_quotes_brackets_and_apostrophes():
    assert split_options('a: 1, b: "x, y", via: [(1,2),(3,4)]') == ['a: 1', ' b: "x, y"', ' via: [(1,2),(3,4)]']
    assert split_options("owner: Fare team's, c: 2") == ["owner: Fare team's", ' c: 2']


def test_attributes_are_kept_and_not_printed():
    p = EDGYParser()
    p.parse_input('''map_type: asset
elements:
  - asset: "Fare engine" {id: AST-02, kind: application, hosting: saas, technology: "Kotlin, Spring Boot", cost: high}
''')
    e = next(iter(p.elements.values()))
    assert e['kind'] == 'application' and e['ref'] == 'AST-02'
    assert e['attrs']['technology'] == 'Kotlin, Spring Boot' and e['attrs']['hosting'] == 'saas'
    assert e['metrics'] == {'cost': 'high'}, e['metrics']          # free metrics are still printed
    value = p._build_display_value(e)
    assert 'kind' not in value and 'saas' not in value and 'Kotlin' not in value and 'cost: high' in value


def test_relationship_attributes_and_id_endpoints():
    p = EDGYParser()
    p.parse_input('''map_type: asset
elements:
  - asset: "Fare engine" {id: AST-02, kind: application}
  - asset: "Fare rules" {id: AST-07, kind: data}
  - process: "Sell tickets" {id: PRO-01}
relationships:
  - "AST-02" -> "AST-07": "stores" {primary: true}
  - "PRO-01" -> "AST-07": "accesses" {crud: ru}
  - "AST-02" -> "AST-07": "transfers" {data: "AST-07", technology: "REST, JSON", container: "Fare API"}
''')
    by = {r['label']: r for r in p.relationships}
    assert set(by) == {'stores', 'accesses', 'transfers'}, by
    assert by['stores']['options']['primary'] is True
    assert by['accesses']['options']['crud'] == 'RU'
    t = by['transfers']['options']
    assert t['data'] == ['AST-07'] and t['technology'] == 'REST, JSON' and t['container'] == 'Fare API'
    assert not [w for w in p.warnings if 'Tuntematon relaatio-optio' in w], p.warnings


def test_every_element_cell_carries_identity_markers():
    pages = parse_document('''map_type: capability
elements:
  - capability: "Ticketing" {id: CAP-05}
  - capability: "Planning"
''')
    xml = _drawio(pages)
    cells = [c for c in _cells(xml) if 'edgyType=' in (c.get('style') or '')]
    assert len(cells) == 2
    st = {re.search(r'edgyId=([^;]+)', c.get('style')).group(1): c.get('style') for c in cells}
    assert 'edgyType=capability;' in st['CAP-05'] and 'edgyFacet=architecture;' in st['CAP-05']
    assert 'edgyIdSource' not in st['CAP-05']
    slug = 'capability:planning'
    assert slug in st and 'edgyIdSource=slug;' in st[slug]
    page_id = re.search(r'<diagram id="([^"]+)"', xml).group(1)
    for c in cells:
        assert f"edgyOcc={page_id}/{c.get('id')};" in c.get('style'), c.get('style')


def test_same_id_on_two_pages_is_one_element_with_two_occurrences():
    pages, g = parse_document('''pages:
  - name: "Map"
    map_type: capability
    elements:
      - capability: "Ticketing" {id: CAP-05}
  - name: "Detail"
    map_type: capability
    elements:
      - capability: "Ticketing" {id: CAP-05}
      - capability: "Fares" {id: CAP-06}
    relationships:
      - "CAP-05" -> "CAP-06": "contains"
''', with_graph=True)
    assert all(not p.errors for _, p in pages)
    node = g.get('CAP-05')
    assert len(node['occurrences']) == 2 and node['explicit']
    _drawio(pages)                 # cell ids exist once the pages are generated
    j = g.to_json()
    occ = next(e for e in j['elements'] if e['id'] == 'CAP-05')['occurrences']
    assert [o['page'] for o in occ] == ['Map', 'Detail'] and all(o['cell'] for o in occ), occ
    assert any(e['source'] == 'CAP-05' and e['verb'] == 'contains' for e in j['relationships'])


def test_conflicting_definition_is_e014():
    pages = parse_document('''pages:
  - name: "A"
    elements:
      - capability: "Ticketing" {id: CAP-05}
  - name: "B"
    elements:
      - asset: "Ticketing system" {id: CAP-05}
''')
    errs = [e for _, p in pages for e in p.errors]
    assert any(e.startswith('E014') for e in errs), errs


def test_duplicate_id_on_one_page_is_e014():
    p = EDGYParser()
    p.parse_input('''elements:
  - capability: "Ticketing" {id: CAP-05}
  - capability: "Fares" {id: CAP-05}
''')
    assert any(e.startswith('E014') for e in p.errors), p.errors


def test_dangling_relationship_is_e015_and_cross_page_ids_resolve():
    pages, g = parse_document('''pages:
  - name: "Capabilities"
    elements:
      - capability: "Ticketing" {id: CAP-05}
  - name: "Assets"
    elements:
      - asset: "Fare engine" {id: AST-02, kind: application}
    relationships:
      - "CAP-05" -> "AST-02": "requires"
      - "AST-02" -> "AST-99": "depends on"
''', with_graph=True)
    errs = [e for _, p in pages for e in p.errors]
    assert len([e for e in errs if e.startswith('E015')]) == 1 and 'AST-99' in errs[0], errs
    assert any(e['source'] == 'CAP-05' and e['target'] == 'AST-02' and e['verb'] == 'requires' for e in g.edges)


def test_model_page_is_in_the_graph_not_in_the_output():
    pages, g = parse_document('''pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "Ticketing" {id: CAP-05}
      - asset: "Fare engine" {id: AST-02, kind: application}
    relationships:
      - "CAP-05" -> "AST-02": "requires"
  - name: "Map"
    map_type: capability
    elements:
      - capability: "Ticketing" {id: CAP-05}
''', with_graph=True)
    assert [n for n, _ in pages] == ['Map']
    assert g.get('AST-02') and g.out_edges('CAP-05', ['requires'])
    j = g.to_json()
    assert next(e for e in j['elements'] if e['id'] == 'AST-02')['occurrences'] == []   # a model page draws nothing


def test_expand_per_capability_needs_explicit_ids():
    pages = parse_document('''pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "Ticketing" {id: CAP-05, highlight: yes}
      - capability: "Planning" {id: CAP-08}
      - capability: "Unnamed one"
  - name: "Capability"
    expand: per-capability
    map_type: capability
    elements:
      - organisation: "Platform team"
''')
    names = [n for n, _ in pages]
    assert names == ['Capability · CAP-05 Ticketing', 'Capability · CAP-08 Planning'], names
    assert pages[0][1].view['focus'] == 'CAP-05'
    errs = [e for _, p in pages for e in p.errors]
    assert any('explicit ids' in e and 'capability:unnamed-one' in e for e in errs), errs
    only = parse_document('''pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "Ticketing" {id: CAP-05, highlight: yes}
      - capability: "Planning" {id: CAP-08}
  - name: "Capability"
    expand: per-capability
    where: highlight
    map_type: capability
''')
    assert [n for n, _ in only] == ['Capability · CAP-05 Ticketing']


def test_merged_transfers_list_every_data_name_on_a_second_line():
    pages = parse_document('''map_type: asset
elements:
  - asset: "Fare engine" {id: AST-02, kind: application}
  - asset: "Ticket shop" {id: AST-03, kind: application}
  - asset: "Fare rules" {id: AST-07, kind: data}
  - asset: "Price list" {id: AST-08, kind: data}
relationships:
  - "AST-02" -> "AST-03": "transfers" {data: AST-07, technology: REST}
  - "AST-02" -> "AST-03": "transfers" {data: AST-08}
''')
    xml = _drawio(pages)
    edge = next(c for c in _cells(xml) if c.get('edge') == '1' and 'transfers' in (c.get('value') or ''))
    v = edge.get('value')
    assert v.startswith('transfers<br>') and 'Fare rules, Price list · REST' in v, v
    found = _lint(xml)
    assert not [f for f in found if f[0] in ('W105', 'E010', 'E011')], found
    box = geo.edge_label_box([(0, 0), (200, 0)], 'transfers\nFare rules, Price list · REST', 11)
    assert box[3] > 11 * geo.LABEL_H, 'a second label line makes the label box taller'


def test_influence_verbs_of_the_views_and_uses_stays_core():
    base = '''map_type: asset
elements:
  - people: "Ticket inspector"
  - asset: "Inspection app" {id: AST-05, kind: application}
  - asset: "Fare rules" {id: AST-07, kind: data}
  - process: "Inspect tickets" {id: PRO-03}
relationships:
'''
    good = base + '''  - "Ticket inspector" -> "AST-05": "interacts with"
  - "AST-05" -> "AST-07": "stores"
  - "PRO-03" -> "AST-07": "accesses" {crud: R}
'''
    found = _lint(_drawio(parse_document(good)))
    assert not [f for f in found if f[0] in ('W105', 'E010', 'E011')], found
    bad = base + '  - "Ticket inspector" -> "AST-05": "uses"\n'
    pages = parse_document(bad)
    assert any('uses' in w for _, p in pages for w in p.warnings), 'uses on people → asset is not a core pair'
    fi = parse_document(base.replace('map_type: asset', 'map_type: asset\nlanguage: fi') +
                        '  - "AST-05" -> "AST-07": "stores"\n')
    edge = next(c for c in _cells(_drawio(fi)) if c.get('edge') == '1' and c.get('source'))
    assert edge.get('value') == 'tallentaa', edge.get('value')


def test_no_influence_verb_is_spelled_like_a_core_link():
    import importlib.util
    repo = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
    spec = importlib.util.spec_from_file_location('rcl', os.path.join(repo, 'tools', 'render-core-links.py'))
    rcl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcl)
    data = rcl.load()
    assert rcl.spelling_collisions(data) == []
    data['influence_verbs'].append({'en': 'operates', 'fi': 'käyttää', 'fr': 'opère', 'de': 'betreibt'})
    hits = rcl.spelling_collisions(data)
    assert hits and 'käyttää' in hits[0] and 'uses' in hits[0], hits


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} graph tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
