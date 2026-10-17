#!/usr/bin/env python3
"""
edgy_present.py — one self-contained presentation.html of every page of a .drawio file.

Presenter-lite (edgy-diagram 2.8.0, plan F6a). The page has no server, no CDN
and no network at all: the inline script and style are pinned by a Content
Security Policy with their sha256 hashes and `connect-src 'none'`, so the
page cannot send the model anywhere. It works offline and as an e-mail
attachment.

It never computes layout: it inlines the native SVG of edgy_render.py (the
same picture the preview shows) and decorates it through the extension
contract 1 attributes (data-id, data-src / data-tgt, data-change). Five
effects, no more — a sixth belongs to the deferred presenter effects (F6b):

  1. card wall → zoom: every view as a card; a click zooms the card into the
     view, the SVG viewBox tweens with a spring to an element (crisp vector)
  2. cross-view highlight: hover / focus highlights an element and its
     neighbours, dims the rest, and counts the element on the other views
  3. search: ⌘K / Ctrl+K over every element and id, jumps with the zoom
  4. current ↔ target: T filters the page's change annotations — current
     hides `new`, target hides `remove`; a page without annotations is left as
     it is. The {change:} overlay is a stroke colour on one diagram, so this is
     a filter over annotations, never a second (target) model
  5. paging: ← / → through the views, F full screen, deep links
     #/view/<page>/<id>?state=target, a print stylesheet (one view per page); drill-through on a
     realisation trace (2.9.0) belongs here: the trace pages are one Trace card on the wall, the "→"
     badge or a second click on a card opens its trace page, #/trace/<id>/<id>/… routes with the
     browser history and a breadcrumb of the path taken

The diagrams stay on a light paper card in both chrome themes; with
prefers-reduced-motion every animation is a cut.

Usage:
  python3 edgy_present.py FILE.drawio [--graph graph.json] [-o presentation.html] [--title T] [--lang en]
  python3 edgy_generator.py input.txt --output map.drawio --present presentation.html   # same, one step

Without --graph the document graph is read from the draw.io cells (edgyId
markers and edges). Exit 0 on success, 2 on unreadable input, 3 when the
page exceeds the size budget (--max-mb, default 1.5 MB for 30 pages, scaled).
Standard library only.
"""

import argparse
import base64
import hashlib
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edgy_render  # noqa: E402
from edgy_document import unique_slugs  # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), 'assets', 'presenter')
BUDGET_MB_PER_30 = 1.5
FACET_ORDER = ('identity', 'architecture', 'experience', 'intersection', 'base')


def read_drawio(path: str) -> List[Tuple[str, str, ET.Element]]:
    """[(page name, page id, mxGraphModel)] — page ids as the <diagram id> (the page half of edgyOcc)."""
    root = ET.parse(path).getroot()
    if root.tag == 'mxGraphModel':
        return [('Diagram', 'page', root)]
    pages = []
    from edgy_document import load_pages_from_file
    loaded = load_pages_from_file(path)
    ids = [d.get('id') for d in root.findall('diagram')]
    names = [n or f'Page {i + 1}' for i, (n, _m) in enumerate(loaded)]
    fallback = unique_slugs(names)
    for i, (name, model) in enumerate(loaded):
        pid = ids[i] if i < len(ids) and ids[i] and re.match(r'^[a-z0-9-]+$', ids[i]) else fallback[i]
        pages.append((names[i], pid, model))
    return pages


def _style(s: Optional[str]) -> Dict[str, str]:
    return edgy_render.style_dict(s)


def _first_line(value: str) -> str:
    lines = edgy_render.label_lines(value or '')
    return lines[0][0] if lines else ''


def graph_from_drawio(pages) -> dict:
    """The document graph from the cells alone (when no --graph JSON is given)."""
    elements: Dict[str, dict] = {}
    order: List[str] = []
    rels = []
    seen = set()
    for name, pid, model in pages:
        root = model.find('root')
        cells = {c.get('id'): c for c in (root.findall('mxCell') if root is not None else [])}
        mids = {}
        for cid, c in cells.items():
            st = _style(c.get('style'))
            mid = st.get('edgyId')
            if not mid or st.get('edgyRole') or not edgy_render.ID_RE.match(mid):
                continue
            mids[cid] = mid
            if mid not in elements:
                lines = edgy_render.label_lines(c.get('value') or '')
                elements[mid] = {
                    'id': mid, 'id_source': 'slug' if st.get('edgyIdSource') == 'slug' else 'explicit',
                    'type': st.get('edgyType') or 'object', 'name': lines[0][0] if lines else mid,
                    'description': ' '.join(t for t, _w, _s in lines[1:2]) or None,
                    'kind': st.get('edgyKind'), 'attributes': {}, 'change': st.get('edgyChange'), 'tags': [],
                    'occurrences': []}
                order.append(mid)
            elements[mid]['occurrences'].append({'page': name, 'page_id': pid, 'cell': cid})
        for cid, c in cells.items():
            if c.get('edge') != '1':
                continue
            s, t = mids.get(c.get('source')), mids.get(c.get('target'))
            if not s or not t:
                continue
            verb = _first_line(c.get('value') or '').lower()
            key = (s, t, verb)
            if key in seen:
                continue
            seen.add(key)
            rels.append({'source': s, 'target': t, 'verb': verb,
                         'kind': edgy_render.edge_kind(_style(c.get('style'))), 'attributes': {}, 'page': name})
    return {'contract': 1, 'elements': [elements[m] for m in order], 'relationships': rels}


def _trace_info(svg: str, pid: str) -> dict:
    """Realisation trace pages (2.9.0), from the edgyTrace markers the generator writes (data-trace in the SVG):
    {'trace': 'index'} for the trace index, {'trace': 'page', 'focus': id} for an element's trace page and
    {'trace': 'list', 'focus': id, 'band': above|below} for its list page; {} for every other page."""
    if re.search(r'<g class="el" [^>]*data-trace="index"', svg):
        return {'trace': 'index'}
    m = re.search(r'<g class="el" data-id="([^"]+)"[^>]*data-trace="(focus|list)"', svg)
    if not m:
        return {}
    focus = html.unescape(m.group(1))
    if m.group(2) == 'list':
        band = re.search(r'-more-(above|below)$', pid)
        return {'trace': 'list', 'focus': focus, 'band': band.group(1) if band else 'below'}
    return {'trace': 'page', 'focus': focus}


def _json_for_script(data) -> str:
    """JSON safe inside <script type="application/json">: no '<', '>' or '&' can close or confuse it."""
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def _sha256(text: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode('utf-8')).digest()).decode('ascii') + "'"


def csp_for(js: str, css: str) -> str:
    return ("default-src 'none'; "
            f"script-src {_sha256(js)}; "
            f"style-src {_sha256(css)}; "
            "img-src data: blob:; font-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'; "
            "frame-src 'none'; object-src 'none'")


def build(drawio: str, graph: Optional[dict] = None, title: Optional[str] = None, lang: str = 'en') -> Tuple[str, dict]:
    """(html, stats) for every page of `drawio`."""
    pages = read_drawio(drawio)
    if not pages:
        raise ValueError('no diagram pages found')
    graph = graph or graph_from_drawio(pages)
    views, templates = [], []
    for i, (name, pid, model) in enumerate(pages):
        svg = edgy_render.page_to_svg(edgy_render.Page(model), name, publication=True)
        svg = svg.replace('<svg xmlns="http://www.w3.org/2000/svg"', f'<svg xmlns="http://www.w3.org/2000/svg" data-page="{pid}"', 1)
        facets = sorted({m for m in re.findall(r'data-facet="([a-z]+)"', svg)}, key=lambda f: FACET_ORDER.index(f)
                        if f in FACET_ORDER else 9)
        view = {'index': i, 'page_id': pid, 'name': name,
                'elements': len(re.findall(r'<g class="el" ', svg)),
                'edges': len(re.findall(r'<g class="edge" ', svg)), 'facets': facets,
                'changes': 'data-change=' in svg}
        view.update(_trace_info(svg, pid))
        views.append(view)
        templates.append(f'<template id="view-{i}">{svg}</template>')
    css = open(os.path.join(ASSETS, 'presenter.css'), encoding='utf-8').read()
    js = open(os.path.join(ASSETS, 'presenter.js'), encoding='utf-8').read()
    page = open(os.path.join(ASSETS, 'presenter.html'), encoding='utf-8').read()
    title = title or os.path.splitext(os.path.basename(drawio))[0].replace('.drawio', '')
    values = {
        '{{lang}}': html.escape(lang if re.match(r'^[a-z]{2}$', lang or '') else 'en'),
        '{{csp}}': html.escape(csp_for(js, css), quote=True),
        '{{title}}': html.escape(title),
        '{{css}}': css,
        '{{templates}}': '\n'.join(templates),
        '{{graph}}': _json_for_script(graph),
        '{{views}}': _json_for_script(views),
        '{{js}}': js,
    }
    # one pass over the template: text inside a value (a label that reads "{{js}}") is never substituted again
    page = re.sub(r'\{\{[a-z]+\}\}', lambda m: values.get(m.group(0), m.group(0)), page)
    stats = {'pages': len(pages), 'bytes': len(page.encode('utf-8')), 'elements': len(graph.get('elements', [])),
             'relationships': len(graph.get('relationships', []))}
    return page, stats


def budget_bytes(pages: int, mb_per_30: float = BUDGET_MB_PER_30) -> int:
    return int(max(pages, 30) / 30 * mb_per_30 * 1024 * 1024)


def write(drawio: str, out: str, graph: Optional[dict] = None, title: Optional[str] = None, lang: str = 'en',
          mb_per_30: float = BUDGET_MB_PER_30) -> dict:
    page, stats = build(drawio, graph, title, lang)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    stats['budget'] = budget_bytes(stats['pages'], mb_per_30)
    stats['path'] = out
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Self-contained presentation.html of a .drawio file (presenter-lite)')
    ap.add_argument('drawio')
    ap.add_argument('-o', '--output', help='output HTML (default: <file>-presentation.html next to the input)')
    ap.add_argument('--graph', help='document graph JSON (edgy_generator.py --graph); default: read from the cells')
    ap.add_argument('--title', help='page title (default: the file name)')
    ap.add_argument('--lang', default='en', help='html lang attribute (default en)')
    ap.add_argument('--max-mb', type=float, default=BUDGET_MB_PER_30, help='size budget per 30 pages (default 1.5)')
    args = ap.parse_args(argv)
    out = args.output or re.sub(r'\.drawio(\.xml)?$', '', args.drawio) + '-presentation.html'
    try:
        graph = json.load(open(args.graph, encoding='utf-8')) if args.graph else None
        stats = write(args.drawio, out, graph, args.title, args.lang, args.max_mb)
    except (OSError, ValueError, ET.ParseError) as e:
        print(f'edgy-present: cannot build a presentation from {args.drawio}: {e}', file=sys.stderr)
        return 2
    print(f"Presentation: {stats['path']} — {stats['pages']} view(s), {stats['elements']} elements, "
          f"{stats['bytes'] / 1024:.0f} KB")
    if stats['bytes'] > stats['budget']:
        print(f"Error: {stats['bytes'] / 1048576:.2f} MB is over the budget of {stats['budget'] / 1048576:.2f} MB "
              f"for {stats['pages']} page(s) — split the delivery or raise --max-mb", file=sys.stderr)
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
