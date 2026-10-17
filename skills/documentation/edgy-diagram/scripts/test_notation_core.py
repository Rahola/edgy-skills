#!/usr/bin/env python3
"""F4-core (edgy-diagram 2.9.0; test plan v2.5.0 K01–K03, plan §4 F4-core 1–6).

- K01: a notation: page keeps only its header keys in the EDGY parser — no container node, no C4 edge,
  no vocabulary warning and no E014 in the document graph;
- K02: expand: on a notation page reaches the handler (one page per target, the handler's page ids);
  without a handler it is E013 on one page, exit 2 and no file — never an empty page per target;
- K03: the findings channel — five stub handlers in fixtures/notation, each in a fresh subprocess:
  a string (v2.4.0 form), a warning, an error, a raise in generate_page, a raise in the prepass;
- the prepass index (graph.notation_index) sees every page of the notation, in any page order;
- {container:} passes through the TXT writer and the graph, and is never drawn or exported to ArchiMate.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
STUBS = os.path.join(HERE, 'fixtures', 'notation')
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile, page_ids_of  # noqa: E402

K01 = '''pages:
  - name: "Applications"
    elements:
      - asset: "Fare engine" {id: APP-07, kind: application}
      - asset: "Ticket shop" {id: APP-05, kind: application}
    relationships:
      - "APP-07" -> "APP-05": "transfers" {data: Fare rules, container: C-FARE-API}
  - name: "Fare engine containers"
    notation: zz
    level: container
    system: APP-07
    elements:
      - container: "Fare API" {id: C-FARE-API, technology: Kotlin}
      - asset: "Fare engine again" {id: APP-07}
    relationships:
      - "C-FARE-API" -> "APP-05": "serves fares to"
'''

K02 = '''pages:
  - name: "Model"
    draw: false
    elements:
      - asset: "Booking system" {id: APP-01, kind: application}
      - asset: "Customer portal" {id: APP-02, kind: application}
      - asset: "Fare rules" {id: DAT-01, kind: data}
  - name: "Context"
    notation: zz
    level: context
    expand: per-application
'''


def env_with(*stubs):
    env = {k: v for k, v in os.environ.items() if k != 'EDGY_NOTATION_PATH'}
    env['EDGY_NOTATION_PATH'] = os.pathsep.join(os.path.join(STUBS, s) for s in stubs) if stubs else os.devnull
    return env


def in_env(stub, fn):
    old = os.environ.get('EDGY_NOTATION_PATH')
    os.environ['EDGY_NOTATION_PATH'] = os.path.join(STUBS, stub) if stub else os.devnull
    try:
        return fn()
    finally:
        if old is None:
            os.environ.pop('EDGY_NOTATION_PATH', None)
        else:
            os.environ['EDGY_NOTATION_PATH'] = old


def generate(text, env, *extra):
    tmp = tempfile.mkdtemp()
    src, out = os.path.join(tmp, 'in.txt'), os.path.join(tmp, 'out.drawio')
    open(src, 'w', encoding='utf-8').write(text)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'edgy_generator.py'), src, '--output', out, *extra],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr, out


def test_k01_notation_page_stays_out_of_the_graph():
    def run():
        pages, graph = parse_document(K01, with_graph=True)
        msgs = [m for _, p in pages for m in p.warnings + p.errors]
        assert not msgs, msgs                                  # no vocabulary warning, no E014 on APP-07
        data = graph.to_json()
        assert {e['id'] for e in data['elements']} == {'APP-07', 'APP-05'}, data['elements']
        assert all(r['verb'] == 'transfers' for r in data['relationships']), data['relationships']
        assert 'C-FARE-API' not in json.dumps([e for e in data['elements']])
        xml = build_mxfile([(n, p.generate_xml()) for n, p in pages], page_ids=page_ids_of(pages))
        assert 'edgyNotation=zz' in xml
        return pages
    in_env('h-str', run)


def test_k02_expand_reaches_the_handler():
    pages = in_env('h-str', lambda: parse_document(K02))
    assert [p.page_id for _, p in pages] == ['zz-context-app-01', 'zz-context-app-02'], [p.page_id for _, p in pages]
    assert all(not p.errors for _, p in pages)
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages], page_ids=page_ids_of(pages))
    assert 'system APP-01' in xml and 'system APP-02' in xml and 'DAT-01' not in xml
    # without a handler: E013 naming the notation, exit 2, no file, no empty pages
    rc, out, path = generate(K02, env_with())
    assert rc == 2 and "E013 unsupported notation 'zz'" in out and not os.path.exists(path), out
    pages = in_env(None, lambda: parse_document(K02))
    assert len(pages) == 1 and any(e.startswith('E013') for e in pages[0][1].errors)


ONE_PAGE = '''pages:
  - name: "Applications"
    elements:
      - asset: "Fare engine" {id: APP-07, kind: application}
  - name: "Context"
    notation: zz
    level: context
    system: APP-07
'''


def test_k03_findings_channel():
    tmp = tempfile.mkdtemp()
    rc, out, path = generate(ONE_PAGE, env_with('h-str'))
    assert rc == 0 and os.path.exists(path) and 'X00' not in out, out
    qa = os.path.join(tmp, 'w.drawio')
    rc, out, path = generate(ONE_PAGE, env_with('h-warn'), '--qa')
    assert rc == 0 and os.path.exists(path) and 'Warning: [Context] X001 msg' in out, out
    manifest = json.load(open(path.replace('.drawio', '.qa.json'), encoding='utf-8'))
    assert any('X001' in w for w in json.dumps(manifest['generator_warnings']).split('","')), manifest['generator_warnings']
    rc, out, path = generate(ONE_PAGE, env_with('h-err'))
    assert rc == 2 and 'Error: [Context] X002 msg' in out and not os.path.exists(path), out
    rc, out, path = generate(ONE_PAGE, env_with('h-raise'))
    assert rc == 2 and not os.path.exists(path), out
    assert "notation handler 'zz' failed on page 'Context'" in out and 'stub handler broke' in out, out
    assert 'Traceback' not in out and sum(ln.startswith('Error:') for ln in out.splitlines()) == 1, out
    rc, out, path = generate(ONE_PAGE, env_with('h-prepass'))
    assert rc == 2 and not os.path.exists(path), out
    assert "notation handler 'zz' failed in the prepass" in out and 'Traceback' not in out, out
    del qa


TWO_SYSTEMS = '''pages:
  - name: "B"
    notation: zz
    level: container
    system: APP-09
  - name: "Applications"
    elements:
      - asset: "Fare engine" {id: APP-07, kind: application}
  - name: "A"
    notation: zz
    level: container
    system: APP-07
'''


def test_prepass_index_sees_every_page_in_any_order():
    def run(text):
        pages = parse_document(text)
        return {p.page_id: p.generate_xml() for _, p in pages}
    first = in_env('h-index', lambda: run(TWO_SYSTEMS))
    head, *blocks = TWO_SYSTEMS.split('  - name: ')
    reordered = head + ''.join('  - name: ' + b for b in reversed(blocks))
    second = in_env('h-index', lambda: run(reordered))
    assert first == second, (sorted(first), sorted(second))
    assert 'index APP-07,APP-09' in first['zz-container-app-07']


def test_container_key_passes_through_and_is_never_drawn():
    """F4-core 6: the TXT writer and the graph carry {container:}; the drawing and ArchiMate leave it out."""
    model = {"schema_version": "1.10", "company": "Acme Transit (fictional)", "language": "en",
             "assessed_at": "2026-10-17",
             "elements": {"asset": [{"id": "APP-05", "name": "Ticket shop", "kind": "application"},
                                    {"id": "APP-07", "name": "Fare engine", "kind": "application"}]},
             "relationships": [{"source_id": "APP-07", "target_id": "APP-05", "verb": "transfers",
                                "attributes": {"technology": "REST", "container": "C-FARE-API"}}]}
    tmp = tempfile.mkdtemp()
    mpath = os.path.join(tmp, 'm.json')
    json.dump(model, open(mpath, 'w', encoding='utf-8'))
    a = os.path.join(REPO, 'skills', 'architecture', 'edgy-assessment', 'scripts')
    r = subprocess.run([sys.executable, os.path.join(a, 'edgy_model_to_txt.py'), mpath, '--views', 'application',
                        '--out', tmp, '--prefix', 'm'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    txt = open(os.path.join(tmp, 'm-views.txt'), encoding='utf-8').read()
    assert 'container: C-FARE-API' in txt, txt                                      # 1. TXT writer
    pages, graph = parse_document(txt, with_graph=True)
    edge = next(e for e in graph.edges if e['verb'] == 'transfers')
    assert edge['options'].get('container') == 'C-FARE-API', edge                     # 2. graph
    xml = build_mxfile([(n, p.generate_xml()) for n, p in pages], page_ids=page_ids_of(pages))
    assert 'C-FARE-API' not in xml and 'REST' in xml                                  # 3. drawing
    r = subprocess.run([sys.executable, os.path.join(a, 'edgy_model_to_archimate.py'), mpath, '-o',
                        os.path.join(tmp, 'm.archimate')], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run([sys.executable, os.path.join(a, 'edgy_model_to_archimate.py'), mpath,
                            os.path.join(tmp, 'm.archimate')], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    arch = open(os.path.join(tmp, 'm.archimate'), encoding='utf-8').read()
    assert 'C-FARE-API' not in arch and 'Fare engine' in arch                          # 4. ArchiMate


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} notation core tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        import traceback
        traceback.print_exc()
        print(f'\nTest failed: {e}')
        sys.exit(1)
