#!/usr/bin/env python3
"""Extension contract 1 (references/extension-contract.md): what extensions may rely on.

Fixture-based, so a core change that breaks the contract fails here — not in
edgy-c4 or a presenter companion: the style-marker grammar on every shipped
example, the document-graph JSON against assets/edgy-graph.schema.json, and
notation handlers failing closed (E012 / E013)."""

import importlib.util
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(SKILL, '..', '..', '..'))
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile, load_graph  # noqa: E402
import edgy_lint  # noqa: E402
import edgy_notation  # noqa: E402

ID = r'[A-Za-z0-9][A-Za-z0-9._:/-]*'
MARKER_RE = {
    'edgyId': re.compile(rf'^{ID}$'),
    'edgyIdSource': re.compile(r'^slug$'),
    'edgyType': re.compile(r'^(purpose|content|story|capability|asset|process|task|channel|journey|brand|product|'
                           r'organisation|people|activity|outcome|object)$'),
    'edgyKind': re.compile(r'^[a-z0-9-]+$'),
    'edgyFacet': re.compile(r'^(identity|architecture|experience|intersection|base)$'),
    'edgyOcc': re.compile(r'^[a-z0-9-]+/\d+$'),
}
_spec = importlib.util.spec_from_file_location('vem', os.path.join(REPO, 'tools', 'validate-edgy-model.py'))
vem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vem)


def _style(s):
    return dict(kv.split('=', 1) for kv in (s or '').split(';') if '=' in kv)


def test_markers_on_every_shipped_example_follow_the_grammar():
    n = 0
    for path in sorted(os.listdir(os.path.join(SKILL, 'examples'))):
        if not (path.startswith('expected-') and path.endswith('.drawio')):
            continue
        root = ET.parse(os.path.join(SKILL, 'examples', path)).getroot()
        for d in root.iter('diagram'):
            for c in d.iter('mxCell'):
                st = _style(c.get('style'))
                if 'edgyType' not in st:
                    continue
                n += 1
                for key in ('edgyId', 'edgyType', 'edgyFacet', 'edgyOcc'):
                    assert key in st, f'{path} cell {c.get("id")}: {key} missing'
                for key, rx in MARKER_RE.items():
                    if key in st:
                        assert rx.match(st[key]), f'{path} cell {c.get("id")}: {key}={st[key]!r}'
                assert st['edgyOcc'] == f'{d.get("id")}/{c.get("id")}', (path, st['edgyOcc'])
    assert n > 300, f'only {n} element cells checked'


def test_graph_json_validates_against_the_schema():
    text = open(os.path.join(SKILL, 'examples', 'multipage-map.txt'), encoding='utf-8').read()
    pages, graph = parse_document(text, with_graph=True)
    build_mxfile([(n, p.generate_xml()) for n, p in pages])
    data = graph.to_json()
    schema = json.load(open(os.path.join(SKILL, 'assets', 'edgy-graph.schema.json'), encoding='utf-8'))
    assert not vem.validate_model(data, schema), vem.validate_model(data, schema)
    assert data['contract'] == edgy_notation.CONTRACT == 1
    assert all(o['cell'] for e in data['elements'] for o in e['occurrences'])
    assert load_graph(text).to_json()['elements'][0]['id'] == data['elements'][0]['id']


FOREIGN_PAGE = '''pages:
  - name: "EDGY"
    elements:
      - capability: "Ticketing" {id: CAP-05}
  - name: "Context"
    notation: zz
    elements:
      - box: "Fare engine"
'''

HANDLER = '''
def generate_page(page_text, graph):
    return ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            '<mxCell id="2" value="Fare engine" style="rounded=0;fillColor=#1168bd;fontColor=#ffffff;edgyNotation=zz;" '
            'vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>'
            '<mxCell id="3" value="Admin" style="fillColor=#08427b;edgyNotation=zz;" vertex="1" parent="1">'
            '<mxGeometry x="300" y="40" width="160" height="80" as="geometry"/></mxCell>'
            '<mxCell id="4" value="uses daily" style="endArrow=classic;edgyNotation=zz;" edge="1" source="3" target="2" parent="1">'
            '<mxGeometry relative="1" as="geometry"/></mxCell></root></mxGraphModel>')

def lint_page(cells, page_name):
    return [('WARNING', 'Z001', 'handler lint ran on ' + str(page_name), '2')]
'''


def _lint_xml(xml):
    with tempfile.NamedTemporaryFile('w', suffix='.drawio', delete=False, encoding='utf-8') as f:
        f.write(xml)
        path = f.name
    try:
        opts = edgy_lint.main.__globals__['argparse'].Namespace(no_legend=False)
        return [(x.rule, x.level, x.msg) for x in edgy_lint.lint_file(path, opts)]
    finally:
        os.unlink(path)


def _with_handler(contract=1):
    tmp = tempfile.mkdtemp()
    skill = os.path.join(tmp, 'edgy-zz')
    os.makedirs(os.path.join(skill, 'scripts'))
    open(os.path.join(skill, 'notation.json'), 'w').write(json.dumps({'notation': 'zz', 'contract': contract,
                                                                       'module': 'scripts/zz.py'}))
    open(os.path.join(skill, 'scripts', 'zz.py'), 'w').write(HANDLER)
    return tmp


def test_unknown_notation_fails_closed():
    old = os.environ.pop('EDGY_NOTATION_PATH', None)
    try:
        pages = parse_document(FOREIGN_PAGE)
        errs = [e for _, p in pages for e in p.errors]
        assert any(e.startswith('E013') and "'zz'" in e for e in errs), errs
        xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
        assert 'box' not in xml and 'Fare engine' not in xml, 'a foreign page is never drawn as EDGY'
        # a hand-made foreign cell without a handler is E013 in the linter too
        foreign = ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                   '<mxCell id="2" value="X" style="fillColor=#1168bd;edgyNotation=zz;" vertex="1" parent="1">'
                   '<mxGeometry x="10" y="10" width="100" height="60" as="geometry"/></mxCell></root></mxGraphModel>')
        rules = [r for r, _, _ in _lint_xml(foreign)]
        assert 'E013' in rules and 'W102' not in rules, rules
    finally:
        if old is not None:
            os.environ['EDGY_NOTATION_PATH'] = old


def test_registered_handler_draws_and_lints_its_page():
    os.environ['EDGY_NOTATION_PATH'] = _with_handler()
    try:
        pages = parse_document(FOREIGN_PAGE)
        assert not [e for _, p in pages for e in p.errors]
        xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
        found = _lint_xml(xml)
        rules = [r for r, _, _ in found]
        assert 'Z001' in rules, found                       # the handler's own lint ran
        assert not {'E013', 'E012', 'W102', 'W105', 'E011'} & set(rules), found
        # EDGY and foreign cells on one page → E012
        one = ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
               '<mxCell id="2" value="Ticketing" style="rounded=1;arcSize=10;fillColor=#a6c0ff;strokeColor=#FFFFFF;" '
               'vertex="1" parent="1"><mxGeometry x="10" y="10" width="120" height="60" as="geometry"/></mxCell>'
               '<mxCell id="3" value="X" style="fillColor=#1168bd;edgyNotation=zz;" vertex="1" parent="1">'
               '<mxGeometry x="300" y="10" width="100" height="60" as="geometry"/></mxCell></root></mxGraphModel>')
        assert 'E012' in [r for r, _, _ in _lint_xml(one)]
    finally:
        os.environ.pop('EDGY_NOTATION_PATH', None)


def test_handler_for_another_contract_is_not_registered():
    os.environ['EDGY_NOTATION_PATH'] = _with_handler(contract=2)
    try:
        assert 'zz' not in edgy_notation.handlers()
        pages = parse_document(FOREIGN_PAGE)
        assert any(e.startswith('E013') for _, p in pages for e in p.errors)
    finally:
        os.environ.pop('EDGY_NOTATION_PATH', None)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} contract tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
