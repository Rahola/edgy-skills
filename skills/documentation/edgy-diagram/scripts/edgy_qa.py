#!/usr/bin/env python3
"""
edgy_qa.py — the qa.json manifest the generator writes next to a .drawio.

One file per delivery artefact, machine-readable, so that `edgy-eval.py`, the
edgy-assessment Phase 5 check and a reviewer read the same numbers: per page
the element and edge counts, the structural lint (errors / warnings / rules),
the visual rules W111–W114, the layout-quality rules W117–W120 (and whether
they ran), the language check W116, the text-size check W115 at the preset's
reference width, the preview image size and orientation; and three fields
the tooling never sets — `visual_approval`, `semantic_approval`,
`delivery_notes` — which stay null until a person fills them in. A manifest
with a null approval is *not approved*; zero lint findings never substitute
for it.

Schema: ../assets/qa.schema.json (validated in tools/check.sh).
"""

import argparse
import datetime as _dt
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_lint  # noqa: E402
import edgy_render  # noqa: E402
import edgy_semantic_review  # noqa: E402

MANIFEST_VERSION = 1


def manifest_path(drawio_path: str) -> str:
    stem = drawio_path[:-len('.drawio')] if drawio_path.endswith('.drawio') else drawio_path
    return stem + '.qa.json'


def _page_facts(drawio_path):
    """[(page name, width, height, drawn edges)] from the generated file, in page order.
    Edges are counted as drawn — merged `a / b` labels are one edge, links the
    triad reports instead of drawing are none — the same count edgy-eval.py used."""
    out = []
    for name, model in edgy_lint.load_models(drawio_path):
        root = model.find('root')
        cells = {c.get('id'): c for c in root.findall('mxCell')} if root is not None else {}
        elements = edgy_lint.classify_cells(cells)['elements']
        edges = sum(1 for c in cells.values()
                    if c.get('edge') == '1' and c.get('source') in elements and c.get('target') in elements)
        out.append((name, float(model.get('pageWidth', 0) or 0), float(model.get('pageHeight', 0) or 0), edges))
    return out


def is_approval(value) -> bool:
    """An approval is a person's non-empty name-and-date string; any other value (true, 1, an object) is not."""
    return isinstance(value, str) and bool(value.strip())


def build_manifest(drawio_path, pages, input_path=None, preset=None, previews=None, generator_warnings=None,
                   layout_quality=True, output_path=None):
    """`pages` is [(name, EDGYParser)], `previews` the result list of edgy_render.render_file (or None);
    `output_path` is the delivery file the user asked for when it is not the .drawio itself (CLI image export)."""
    previews = previews or []
    base_dir = os.path.dirname(os.path.abspath(drawio_path))

    def rel(path):
        # paths relative to the manifest's directory: the delivery folder can move, and no local directory name leaks
        return os.path.relpath(path, base_dir) if path else None

    names = [name for name, _ in pages]
    facts = _page_facts(drawio_path)
    ref_width = edgy_render.NATIVE_PRESETS[preset]['ref_width'] if preset in edgy_render.NATIVE_PRESETS else None
    # pages are matched by ordinal (file order = parser order = preview order), never by name:
    # two pages may share a name. Each page is linted on its own model with its own W115 scale.
    models = list(edgy_lint.load_models(drawio_path))
    lines = edgy_lint.line_index(drawio_path)
    per_page = []
    semantic_total = 0
    for idx, (name, p) in enumerate(pages):
        prev = previews[idx] if idx < len(previews) else None
        scale = round(ref_width / prev['width'], 4) if (ref_width and prev and prev.get('width')) else None
        opts = argparse.Namespace(no_legend=False, language=None, scale=scale, no_layout_quality=not layout_quality)
        if idx < len(models):
            findings = edgy_lint.lint_model(drawio_path, name if len(pages) > 1 else None, models[idx][1], lines, opts)
        else:
            findings = []
        rules = Counter(f.rule for f in findings)
        counts = Counter(e['type'] for e in p.elements.values() if e['id'] not in getattr(p, '_hidden', set()))
        drawn_edges = facts[idx][3] if idx < len(facts) else 0
        semantic = edgy_semantic_review.review_parser(p, name if len(pages) > 1 else None) if p.map_type == 'purpose' else []
        semantic_total += len(semantic)
        page_w, page_h = (facts[idx][1], facts[idx][2]) if idx < len(facts) else (0, 0)
        per_page.append({
            'name': name, 'map_type': p.map_type, 'facet': p.facet, 'language': p.language,
            'elements': dict(sorted(counts.items())), 'edges': drawn_edges,
            'page': {'width': page_w, 'height': page_h, 'ratio': round(page_h / page_w, 2) if page_w else 0},
            'lint': {'errors': sum(1 for f in findings if f.level == 'ERROR'),
                     'warnings': sum(1 for f in findings if f.level == 'WARNING'),
                     'rules': dict(sorted(rules.items()))},
            'visual': sum(v for k, v in rules.items() if k in edgy_lint.VISUAL_RULES),
            'layout_quality': {'ran': bool(layout_quality), 'findings': sum(v for k, v in rules.items() if k in edgy_lint.LAYOUT_RULES)},
            'language_check': {'findings': rules.get('W116', 0)},
            'text_size': {'preset': preset, 'reference_width': ref_width, 'scale': scale,
                          'findings': rules.get('W115', 0) if scale else None},
            'image': ({'svg': rel(prev['svg']), 'png': rel(prev.get('png')), 'width': prev.get('width'), 'height': prev.get('height'),
                       'orientation': prev.get('orientation')} if prev else None),
            'semantic_review': ({'findings': len(semantic), 'questions': sum(1 for f in semantic if f['level'] == 'warning')}
                                if p.map_type == 'purpose' else None),
        })
    return {
        'manifest_version': MANIFEST_VERSION,
        'generated_at': _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'input': os.path.basename(input_path) if input_path else None,
        'output': os.path.basename(output_path or drawio_path),
        'preset': preset,
        'generator_warnings': list(generator_warnings or []),
        'pages': per_page,
        'totals': {'elements': sum(sum(pg['elements'].values()) for pg in per_page),
                   'edges': sum(pg['edges'] for pg in per_page),
                   'lint_errors': sum(pg['lint']['errors'] for pg in per_page),
                   'lint_warnings': sum(pg['lint']['warnings'] for pg in per_page),
                   'visual': sum(pg['visual'] for pg in per_page),
                   'layout_quality': sum(pg['layout_quality']['findings'] for pg in per_page)},
        'semantic_review': {'findings': semantic_total, 'approved_by': None} if any(pg['semantic_review'] for pg in per_page) else None,
        # Set by a person, never by the tooling: a null value means *not approved*.
        'visual_approval': None,
        'semantic_approval': None,
        'delivery_notes': None,
    }


def write_manifest(drawio_path, manifest):
    path = manifest_path(drawio_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write('\n')
    return path


def approval_status(manifest):
    """Lines a reviewer reads: lint and approvals reported separately, never merged."""
    t = manifest['totals']
    def show(value):
        if is_approval(value):
            return value.strip()
        return 'NOT APPROVED (null)' if value is None else f'NOT APPROVED (not a reviewer name and date: {value!r})'
    lines = [f"lint: {t['lint_errors']} error(s), {t['lint_warnings']} warning(s); visual W111–W114: {t['visual']}; "
             f"layout W117–W120: {t['layout_quality']}",
             f"visual approval: {show(manifest.get('visual_approval'))}",
             f"semantic approval: {show(manifest.get('semantic_approval'))}"]
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description='Read qa.json manifests and report their approval status')
    ap.add_argument('files', nargs='+', help='qa.json files')
    ap.add_argument('--require-approvals', action='store_true',
                    help='exit 1 unless visual_approval and semantic_approval are both a non-empty reviewer name-and-date string')
    args = ap.parse_args(argv)
    rc = 0
    for f in args.files:
        m = json.load(open(f, encoding='utf-8'))
        print(f"{f}:")
        for line in approval_status(m):
            print(f"  {line}")
        if args.require_approvals and not (is_approval(m.get('visual_approval')) and is_approval(m.get('semantic_approval'))):
            rc = 1
    return rc


if __name__ == '__main__':
    sys.exit(main())
