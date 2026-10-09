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


def test_chain_per_language_has_no_language_mismatch():
    """fi / fr / de models: verbs and legend come out in the model language — no W116."""
    for lang in ('fi', 'fr', 'de'):
        d = tempfile.mkdtemp()
        model = _model()
        model['language'] = lang
        path = Path(d) / 'model.json'
        path.write_text(json.dumps(model), encoding='utf-8')
        r = subprocess.run([sys.executable, str(HERE / 'edgy_model_to_txt.py'), str(path), '--out', d, '--prefix', 'acme'],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        txt = Path(d) / 'acme-identity.txt'
        assert f'language: {lang}' in txt.read_text(encoding='utf-8')
        out = Path(d) / 'acme-identity.drawio'
        g = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_generator.py'), str(txt), '--output', str(out)], capture_output=True, text=True)
        assert g.returncode == 0, g.stderr
        lint = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_lint.py'), '--json', str(out)], capture_output=True, text=True)
        findings = json.loads(lint.stdout)
        assert not [f for f in findings if f['rule'] == 'W116'], (lang, [f['msg'] for f in findings if f['rule'] == 'W116'])
        assert not [f for f in findings if f['level'] == 'ERROR'], (lang, [f['msg'] for f in findings if f['level'] == 'ERROR'])


def test_provenance_tags_follow_the_report_language():
    model = _model()
    model['elements']['purpose']['provenance'] = 'confirmed'
    for lang, tag in (('en', 'confirmed'), ('fi', 'vahvistettu'), ('fr', 'confirmé'), ('de', 'bestätigt')):
        txt = m2t.build(model, 'identity', lang)
        line = [l for l in txt.splitlines() if l.strip().startswith('- purpose:')][0]
        assert f'[{tag}' in line or f', {tag}]' in line, (lang, line)
        assert not (lang != 'en' and 'confirmed' in line), (lang, line)


def test_layout_block_is_written_to_every_file():
    model = _model()
    model['layout'] = {'legend': 'strip', 'card_width': 200, 'equal_group_width': True, 'title': 'Acme Oy — EDGY\nmap_type: triad'}
    for facet in ('identity', 'architecture', 'experience', 'all'):
        head = m2t.build(model, facet, 'en').split('elements:')[0]
        assert 'legend: strip' in head and 'card_width: 200' in head and 'equal_group_width: true' in head and 'title: Acme Oy — EDGY map_type: triad' in head, head
        assert '\nmap_type: triad' not in head, 'a newline in free text never becomes a directive'


def test_assessment_chain_requires_approvals():
    """Four files from one model: --series clean, a qa.json per file with null approvals →
    the Phase 5 check (edgy_qa.py --require-approvals) fails until a person sets both fields."""
    d = tempfile.mkdtemp()
    model = _model()
    model['layout'] = {'legend': 'strip'}
    path = Path(d) / 'model.json'
    path.write_text(json.dumps(model), encoding='utf-8')
    r = subprocess.run([sys.executable, str(HERE / 'edgy_model_to_txt.py'), str(path), '--out', d, '--prefix', 'acme'],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    outs = []
    for txt in sorted(Path(d).glob('acme-*.txt')):
        out = Path(d) / (txt.stem + '.drawio')
        g = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_generator.py'), str(txt), '--output', str(out), '--qa'], capture_output=True, text=True)
        assert g.returncode == 0, (txt.name, g.stderr)
        assert (Path(d) / (txt.stem + '.qa.json')).exists(), txt.name
        outs.append(str(out))
    lint = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_lint.py'), '--json', '--series'] + outs, capture_output=True, text=True)
    findings = json.loads(lint.stdout)
    assert not [f for f in findings if f['rule'] == 'W121'], [f['msg'] for f in findings if f['rule'] == 'W121']
    qa_files = sorted(str(q) for q in Path(d).glob('acme-*.qa.json'))
    check = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_qa.py'), '--require-approvals'] + qa_files, capture_output=True, text=True)
    assert check.returncode == 1 and 'NOT APPROVED' in check.stdout, check.stdout
    for q in qa_files:
        m = json.loads(Path(q).read_text(encoding='utf-8'))
        assert m['visual_approval'] is None and m['semantic_approval'] is None
        m['visual_approval'] = 'Reviewer, 2026-10-09'
        m['semantic_approval'] = 'Reviewer, 2026-10-09'
        Path(q).write_text(json.dumps(m), encoding='utf-8')
    check = subprocess.run([sys.executable, str(DIAGRAM / 'edgy_qa.py'), '--require-approvals'] + qa_files, capture_output=True, text=True)
    assert check.returncode == 0, check.stdout


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
