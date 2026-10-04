#!/usr/bin/env python3
"""Tests for edgy_model_to_txt.py — model → TXT, primary flag, --layout triad,
and the full chain model → TXT → drawio → lint on the fictional sample model."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edgy_model_to_txt as m2t  # noqa: E402

REPO = HERE.parent.parent.parent.parent
SAMPLE = REPO / 'skills' / 'architecture' / 'edgy-deep-dive' / 'examples' / 'sample-model.json'
DIAGRAM = REPO / 'skills' / 'documentation' / 'edgy-diagram' / 'scripts'


def _model():
    return json.loads(SAMPLE.read_text(encoding='utf-8'))


def test_default_layout_has_no_map_type_and_first_element_is_primary():
    model = _model()
    txt = m2t.build(model, 'architecture', 'en')
    assert 'map_type:' not in txt and 'primary: true' not in txt
    first_cap = m2t._clean(model['elements']['capability'][0]['name'])
    assert f'"{first_cap}"' in txt.split('relationships:')[1], 'core links use the first capability'


def test_primary_flag_moves_links_and_is_written():
    model = _model()
    caps = model['elements']['capability']
    assert len(caps) >= 2, 'sample model needs two capabilities for this test'
    caps[1]['primary'] = True
    txt = m2t.build(model, 'architecture', 'fi', layout='triad')
    head = txt.splitlines()[:6]
    assert 'map_type: triad' in head and 'language: fi' in head, head   # panel headings follow the report language
    chosen = m2t._clean(caps[1]['name'])
    first = m2t._clean(caps[0]['name'])
    elements, rels = txt.split('relationships:')
    assert f'"{chosen}' in elements and 'primary: true' in elements
    assert sum(1 for line in elements.splitlines() if 'primary: true' in line) == 1
    assert f'"{chosen}"' in rels and f'"{first}"' not in rels, 'relationships follow the primary element'


def test_chain_model_to_txt_to_drawio_lints_clean_with_triad():
    d = tempfile.mkdtemp()
    model = _model()
    path = Path(d) / 'model.json'
    path.write_text(json.dumps(model), encoding='utf-8')
    r = subprocess.run([sys.executable, str(HERE / 'edgy_model_to_txt.py'), str(path), '--out', d,
                        '--prefix', 'acme', '--layout', 'triad'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    txts = sorted(Path(d).glob('acme-*.txt'))
    assert len(txts) == 4, txts
    for txt in txts:
        out = Path(d) / (txt.stem + '.drawio')
        g = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_generator.py'), str(txt), '--output', str(out)],
                           capture_output=True, text=True)
        assert g.returncode == 0, (txt.name, g.stderr)
        lint = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_lint.py'), '--json', str(out)], capture_output=True, text=True)
        findings = json.loads(lint.stdout)
        errors = [f for f in findings if f['level'] == 'ERROR']
        visual = [f for f in findings if f['rule'] in ('W111', 'W112', 'W113', 'W114')]
        assert not errors, (txt.name, [f['msg'] for f in errors])
        assert not visual, (txt.name, [f['msg'] for f in visual])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        print(f'Testing {t.__name__}...')
        t()
        print(f'{t.__name__} passed')
    print(f'\nAll {len(tests)} model→TXT tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'\nTest failed: {e}')
        sys.exit(1)
