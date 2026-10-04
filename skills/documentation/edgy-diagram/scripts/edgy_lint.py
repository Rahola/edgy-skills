#!/usr/bin/env python3
"""
edgy_lint.py — Lint draw.io files that carry EDGY 23 notation.

Checks structure, layout and EDGY semantics of a .drawio / .drawio.xml file
and reports findings as `file:line: LEVEL RULE message`, so an agent can fix
the *input* (or the XML, when it was written by hand) before delivery.

Works on a bare <mxGraphModel>, an <mxfile> with one or many <diagram> pages
(plain or deflate-compressed), and on nested cells (container / parent
chains — positions are resolved to absolute page coordinates).

Usage:
  python3 edgy_lint.py FILE [FILE ...]
  python3 edgy_lint.py --warnings-as-errors FILE
  python3 edgy_lint.py --json FILE            # machine-readable findings
  python3 edgy_lint.py --no-legend FILE       # allow a diagram without a legend

Exit codes: 0 clean (warnings allowed), 1 findings at ERROR level, 2 usage /
unreadable input.

Rules
  E001 XML does not parse                    E002 nested <mxCell> (must be flat)
  E003 duplicate cell id                     E004 edge without <mxGeometry>
  E005 edge source/target missing or not a vertex
  E006 vertex has negative absolute coordinates
  E007 vertex outside the page               E008 two elements overlap > 30 %
  E009 EDGY 23 legend missing (title + ≥ 3 colour chips + ≥ 1 line sample)
  E010 core-link verb on a non-core pair
  E011 non-core verb drawn with core-link style
  W101 text does not fit the element (estimate)
  W102 fill colour is not an EDGY 23 palette colour
  W103 intersection element (brand/product/organisation) not a rectangle
  W104 core-link verb drawn without core-link style
  W105 relationship verb not in any vocabulary (core / flow / tree / influence)
  W106 empty container                       W107 double-escaped HTML entity in a label
  W108 unlabelled edge between two elements  W109 label repeats the element type ("Capability X")
  W110 stroke colour outside EDGY white / base-element dark / transition overlay palette

Visual rules — computed on the same resolved geometry the native renderer
draws (edgy_geometry.py): ports, orthogonal joins, waypoints, label boxes.
  W111 edge passes through an element that is neither its source nor target (> 8 px inside)
  W112 edge label overlaps an element (> 20 % of the label box)
  W113 edge label overlaps another edge label (> 20 % of the smaller box; a
       parent → children fan with one verb is one bus and does not count)
  W114 edge label or edge end outside the page
  --visual prints only the visual findings, as JSON with page, cell ids and
  coordinates, for a machine to act on.
"""

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_geometry as geo  # noqa: E402 — the renderer's geometry, so lint checks what is drawn
import edgy_text  # noqa: E402 — glyph-table text measurement, the same the renderer wraps with

try:  # vocabulary from the generated module next to this file
    from edgy_core_links import core_link_pairs, INFLUENCE_RELATIONSHIPS  # noqa: E402
    from edgy_parser import FLOW_RELATIONSHIPS, TREE_RELATIONSHIPS  # noqa: E402
except Exception:  # pragma: no cover — lint must still run standalone
    def core_link_pairs(_verb):
        return set()
    INFLUENCE_RELATIONSHIPS = set()
    FLOW_RELATIONSHIPS = set()
    TREE_RELATIONSHIPS = set()

VISUAL_RULES = ('W111', 'W112', 'W113', 'W114')   # geometry findings with coordinates; W115 (--scale) is a size check
W111_MIN_INSIDE = 8.0      # px of an edge inside a foreign element before it counts
W112_MIN_OVERLAP = 0.20    # share of the label box over an element
W113_MIN_OVERLAP = 0.20    # share of the smaller label box over another label

PALETTE = {
    '#80ffb7': 'identity', '#a6c0ff': 'architecture', '#ff99bd': 'experience',
    '#ffd580': 'brand', '#e599ff': 'product', '#80eaff': 'organisation',
}
NEUTRAL_FILLS = {'#ffffff', '#fff', 'none', '#f5f5f5', '#f4f4f4', '#fafafa', '#f3f4f6', '',
                 '#e3ffee', '#e6edff', '#ffe6ef', '#eef2f7', '#c9d9ff', '#dce6ff'}  # container / lane / legend tints
OVERLAY_STROKES = {'#6b778c', '#006644', '#b26b00', '#c25100', '#bf2600'}
ALLOWED_STROKES = {'#fff', '#ffffff', '#262626', '#555555', '#333333', 'none', ''} | OVERLAY_STROKES
TYPE_WORDS = {'purpose', 'content', 'story', 'capability', 'asset', 'process', 'task', 'channel', 'journey',
              'brand', 'product', 'organisation', 'organization', 'people', 'activity', 'outcome', 'object',
              'tarkoitus', 'sisältö', 'tarina', 'kyvykkyys', 'resurssi', 'prosessi', 'tehtävä', 'kanava', 'matka',
              'brändi', 'tuote', 'organisaatio'}
LEGEND_WORDS = ('legend', 'selite', 'legende', 'légende')
# A named entity surviving XML decoding (e.g. &auml; from &amp;auml; in the file)
# means the label was escaped twice. draw.io's own html labels legitimately
# contain &nbsp; / &amp; / &lt; / &gt; / &quot;, so those are ignored.
ENTITY_RE = re.compile(r'&(?!(?:nbsp|amp|lt|gt|quot|apos);)[a-zA-Z]+;')
CHAR_W = 0.55   # average glyph width as a fraction of font size (bold sans)
LINE_H = 1.25   # line height as a fraction of font size


class Finding:
    def __init__(self, level, rule, msg, file, line=None, cell=None, page=None, coords=None):
        self.level, self.rule, self.msg, self.file, self.line, self.cell, self.page = \
            level, rule, msg, file, line, cell, page
        self.coords = coords   # visual rules: {'edge': id, 'other': id, 'box': [x, y, w, h], …}

    def __str__(self):
        loc = f"{self.file}:{self.line}" if self.line else self.file
        page = f" [page {self.page}]" if self.page else ""
        cell = f" (cell {self.cell})" if self.cell else ""
        return f"{loc}: {self.level} {self.rule}{page}{cell} {self.msg}"

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


def style_dict(style):
    d = {}
    for part in (style or '').split(';'):
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
            d[k] = v
        else:
            d[part] = True
    return d


def strip_html(value):
    text = re.sub(r'<br\s*/?>', '\n', value or '', flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text)


def shape_of(st):
    shape = st.get('shape', '')
    if 'arrows2.arrow' in shape:
        return 'pentagon'
    if 'person' in shape:
        return 'person'
    if 'text' in st or 'line' in st:
        return 'decoration'
    if st.get('rounded') == '1' and st.get('arcSize'):
        return 'rounded'
    return 'rect'


def element_type(st):
    """Infer the EDGY element type from fill colour + shape, or None."""
    fam = PALETTE.get(st.get('fillColor', '').lower())
    if fam is None:
        return None
    if fam in ('brand', 'product', 'organisation'):
        return fam
    sh = shape_of(st)
    table = {
        'identity': {'rounded': 'purpose', 'pentagon': 'story', 'rect': 'content'},
        'architecture': {'rounded': 'capability', 'pentagon': 'process', 'rect': 'asset'},
        'experience': {'rounded': 'task', 'pentagon': 'journey', 'rect': 'channel'},
    }
    return table[fam].get(sh)


BASE_FILLS = {'#ffffff', '#fff'}
BASE_STROKES = {'#262626', '#000000', '#333333', '#555555'} | {'#6b778c', '#006644', '#b26b00', '#c25100', '#bf2600'}
BASE_TYPES = {'rounded': 'outcome', 'pentagon': 'activity', 'rect': 'object', 'person': 'people'}


def base_element_type(st):
    """EDGY base element (people / activity / outcome / object): white fill,
    dark (or transition-overlay) stroke, or the person shape. None otherwise."""
    fill = st.get('fillColor', '').lower()
    stroke = st.get('strokeColor', '').lower()
    sh = shape_of(st)
    if fill not in BASE_FILLS or sh == 'decoration':
        return None
    if sh == 'person' or stroke in BASE_STROKES:
        return BASE_TYPES.get(sh)
    return None


def is_legend_chip(c, st):
    """A small, unlabelled palette swatch, or a palette-filled text cell (hand-written legends)."""
    fill = st.get('fillColor', '').lower()
    if fill not in PALETTE:
        return False
    g = c.find('mxGeometry')
    w = float(g.get('width', 0) or 0) if g is not None else 0
    h = float(g.get('height', 0) or 0) if g is not None else 0
    small_unlabelled = w <= 40 and h <= 20 and not strip_html(c.get('value') or '').strip()
    return small_unlabelled or ('text' in st)


def classify_cells(cells):
    """Split a page's cells into EDGY elements, containers, legend parts.

    Returns dict with:
      elements   {id: (cell, style, kind)}  kind = facet/intersection type or base type
      containers set of container ids
      legend     {'title': bool, 'chips': set(colours), 'samples': int}
    Legend detection is structural: a text cell whose label names a legend,
    at least three palette chips, and at least one free-standing line sample
    (an edge without source/target). An element merely *named* "Legend" does
    not count, and cell ids carry no meaning.
    """
    elements, containers = {}, set()
    legend = {'title': False, 'chips': set(), 'samples': 0}
    for i, c in cells.items():
        st = style_dict(c.get('style'))
        if c.get('edge') == '1':
            if not c.get('source') and not c.get('target'):
                legend['samples'] += 1
            continue
        if c.get('vertex') != '1':
            continue
        label = strip_html(c.get('value') or '').strip().lower()
        if st.get('container') == '1' or 'swimlane' in (c.get('style') or ''):
            containers.add(i)
            continue
        if 'text' in st and any(w in label for w in LEGEND_WORDS):
            legend['title'] = True
        if is_legend_chip(c, st):
            legend['chips'].add(st.get('fillColor', '').lower())
            continue
        if shape_of(st) == 'decoration':
            continue
        if st.get('fillColor', '').lower() in PALETTE:
            elements[i] = (c, st, element_type(st))
            continue
        base = base_element_type(st)
        if base:
            elements[i] = (c, st, base)
    return {'elements': elements, 'containers': containers, 'legend': legend}


def legend_complete(legend):
    return legend['title'] and len(legend['chips']) >= 3 and legend['samples'] >= 1


def load_models(path):
    """Yield (page_name, mxGraphModel element) for every diagram in the file."""
    raw = open(path, 'rb').read()
    root = ET.fromstring(raw)
    if root.tag == 'mxGraphModel':
        yield None, root
        return
    if root.tag != 'mxfile':
        raise ValueError(f"unexpected root element <{root.tag}>")
    for diagram in root.findall('diagram'):
        model = diagram.find('mxGraphModel')
        if model is None and diagram.text and diagram.text.strip():
            data = base64.b64decode(diagram.text.strip())
            xml = urllib.parse.unquote(zlib.decompress(data, -15).decode('utf-8'))
            model = ET.fromstring(xml)
        if model is not None:
            yield diagram.get('name'), model


def line_index(path):
    """cell id → first line number where id="…" appears (best effort)."""
    idx = {}
    try:
        for n, line in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
            for m in re.finditer(r'\bid="([^"]+)"', line):
                idx.setdefault(m.group(1), n)
    except OSError:
        pass
    return idx


def lint_model(path, page, model, lines, opts):
    F = []
    add = lambda level, rule, msg, cell=None: F.append(  # noqa: E731
        Finding(level, rule, msg, path, lines.get(cell) if cell else None, cell, page))

    root = model.find('root')
    if root is None:
        add('ERROR', 'E001', '<mxGraphModel> has no <root>')
        return F
    page_w = float(model.get('pageWidth', 0) or 0)
    page_h = float(model.get('pageHeight', 0) or 0)

    # E002 nested cells
    for parent in model.iter('mxCell'):
        for child in parent.findall('mxCell'):
            add('ERROR', 'E002', 'mxCell nested inside another mxCell — every cell must be a direct child of <root>; express containment with parent="…"', child.get('id'))

    cells = {}
    for c in root.findall('mxCell'):
        cid = c.get('id')
        if cid in cells:
            add('ERROR', 'E003', f'duplicate cell id "{cid}"', cid)
        cells[cid] = c

    verts = {i: c for i, c in cells.items() if c.get('vertex') == '1'}
    edges = {i: c for i, c in cells.items() if c.get('edge') == '1'}

    def geom(c):
        g = c.find('mxGeometry')
        if g is None:
            return None
        return [float(g.get(k, 0) or 0) for k in ('x', 'y', 'width', 'height')]

    def abs_box(c):
        g = geom(c)
        if g is None:
            return None
        x, y, w, h = g
        p = cells.get(c.get('parent'))
        guard = 0
        while p is not None and p.get('vertex') == '1' and guard < 50:
            pg = geom(p)
            if pg:
                x += pg[0]
                y += pg[1]
            p = cells.get(p.get('parent'))
            guard += 1
        return x, y, w, h

    # classify vertices (EDGY elements incl. base elements, containers, legend parts)
    cls = classify_cells(cells)
    containers = cls['containers']
    legend_seen = legend_complete(cls['legend'])
    elements = {i: (c, st, abs_box(c)) for i, (c, st, _kind) in cls['elements'].items()}
    kinds = {i: kind for i, (_c, _st, kind) in cls['elements'].items()}
    for i, c in verts.items():
        st = style_dict(c.get('style'))
        val = c.get('value') or ''
        if ENTITY_RE.search(val):
            add('WARNING', 'W107', f'double-escaped HTML entity in label ({ENTITY_RE.search(val).group(0)}) — write UTF-8 text and escape only & < > " once', i)
        if i in elements or i in containers or 'text' in st or shape_of(st) == 'decoration':
            continue
        fill = st.get('fillColor', '').lower()
        is_lane = st.get('strokeColor') == 'none' and st.get('verticalAlign') == 'top'
        if fill and fill not in NEUTRAL_FILLS and fill not in PALETTE and not is_lane:
            add('WARNING', 'W102', f'fill colour {fill} is not an EDGY 23 palette colour', i)

    # E004/E005/W108 edges
    for i, e in edges.items():
        if e.find('mxGeometry') is None:
            add('ERROR', 'E004', 'edge has no <mxGeometry relative="1" as="geometry"/> child', i)
        src, tgt = e.get('source'), e.get('target')
        g = e.find('mxGeometry')
        for k, v in (('source', src), ('target', tgt)):
            if v is None:
                point = g.find(f"mxPoint[@as='{k}Point']") if g is not None else None
                if point is None:
                    add('ERROR', 'E005', f'edge has neither {k} nor {k}Point', i)
            elif v not in verts:
                add('ERROR', 'E005', f'edge {k}="{v}" is not an existing vertex', i)
        if src in elements and tgt in elements and not strip_html(e.get('value') or '').strip():
            add('WARNING', 'W108', 'edge between two EDGY elements has no verb label', i)

    # E006/E007/W101/W103/W106 vertices
    for i, (c, st, box) in elements.items():
        if box is None:
            continue
        x, y, w, h = box
        if x < 0 or y < 0:
            add('ERROR', 'E006', f'element at negative coordinates ({x:.0f},{y:.0f})', i)
        elif page_w and page_h and (x + w > page_w or y + h > page_h):
            add('ERROR', 'E007', f'element extends outside the page ({x:.0f},{y:.0f},{w:.0f}x{h:.0f} vs page {page_w:.0f}x{page_h:.0f})', i)
        et = kinds.get(i)
        if et in ('brand', 'product', 'organisation') and shape_of(st) != 'rect':
            add('WARNING', 'W103', f'{et} must use the plain rectangle (Object) shape', i)
        stroke = st.get('strokeColor', '').lower()
        if stroke and stroke not in ALLOWED_STROKES:
            add('WARNING', 'W110', f'stroke colour {stroke} is neither EDGY white nor a transition-overlay colour', i)
        first_line = strip_html(c.get('value') or '').strip().split('\n')[0]
        words = first_line.split()
        if len(words) >= 2 and words[0].lower().strip(':') in TYPE_WORDS:
            add('WARNING', 'W109', f'label starts with the element type ("{words[0]}") — the type is shown by shape and colour; use the name only', i)
        # W101 text fit — per line, honouring <font style="font-size:Npx"> and
        # font-weight overrides; measured with the glyph tables the renderer wraps with
        raw = c.get('value') or ''
        fs_default = float(st.get('fontSize', 12) or 12)
        bold_default = st.get('fontStyle') in ('1', '3', '5', '7')
        if raw.strip() and w > 0 and h > 0:
            needed_h = 0.0
            needed_lines = 0
            usable_w = w - 12 - (20 if shape_of(st) == 'pentagon' else 0)   # the arrow tip is not text area
            for seg in re.split(r'<br\s*/?>', raw, flags=re.I):
                m = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', seg, re.I)
                fs = float(m.group(1)) if m else fs_default
                if re.search(r'<b>|<strong>|font-weight:\s*bold', seg, re.I):
                    bold = True
                elif re.search(r'font-weight:\s*normal', seg, re.I):
                    bold = False
                else:
                    bold = bold_default
                para = html.unescape(re.sub(r'<[^>]+>', '', seg)).strip()
                if not para:
                    continue
                n_lines = edgy_text.lines_needed(para, max(usable_w, 20), fs, bold)
                needed_lines += n_lines
                needed_h += n_lines * fs * LINE_H
            if needed_h > h - 4:
                add('WARNING', 'W101', f'text needs ~{needed_lines} lines (~{needed_h:.0f}px) but the element is {w:.0f}x{h:.0f} — widen the element or shorten the label', i)

    for i in containers:
        if not any(c.get('parent') == i for c in cells.values()):
            add('WARNING', 'W106', 'container has no children (parent="…" pointing to it)', i)

    # E008 overlaps (same parent, > 30 % of the smaller area)
    items = [(i, c.get('parent'), box) for i, (c, st, box) in elements.items() if box]
    for a in range(len(items)):
        ia, pa, (ax, ay, aw, ah) = items[a]
        for b in range(a + 1, len(items)):
            ib, pb, (bx, by, bw, bh) = items[b]
            if pa != pb:
                continue
            ox = max(0, min(ax + aw, bx + bw) - max(ax, bx))
            oy = max(0, min(ay + ah, by + bh) - max(ay, by))
            inter = ox * oy
            smaller = max(min(aw * ah, bw * bh), 1)
            if inter / smaller > 0.30:
                add('ERROR', 'E008', f'overlaps element {ib} by {100*inter/smaller:.0f} % of its area', ia)

    # E009 legend
    if elements and not legend_seen and not opts.no_legend:
        add('ERROR', 'E009', 'EDGY 23 legend missing (element colours + relationship line styles)')

    # E010/E011/W104/W105 semantics
    for i, e in edges.items():
        src, tgt = e.get('source'), e.get('target')
        if src not in elements or tgt not in elements:
            continue
        verb = strip_html(e.get('value') or '').strip().lower()
        if not verb:
            continue
        st = style_dict(e.get('style'))
        overlay_dash = st.get('dashed') == '1' and st.get('strokeColor', '').lower() in OVERLAY_STROKES
        core_style = st.get('endArrow') == 'classic' and st.get('endFill') == '1' and (st.get('dashed') != '1' or overlay_dash)
        s_type = kinds.get(src)
        t_type = kinds.get(tgt)
        allowed = core_link_pairs(verb)
        if allowed:
            if s_type and t_type and (s_type, t_type) not in allowed:
                exp = ', '.join(f'{a} → {b}' for a, b in sorted(allowed))
                add('ERROR', 'E010', f'"{verb}" is a core-link verb for {exp}, but this edge is {s_type} → {t_type} — use an influence verb (dashed) or the correct pair', i)
            elif not core_style:
                add('WARNING', 'W104', f'core link "{verb}" is not drawn with core-link style (endArrow=classic;endFill=1)', i)
        else:
            known = verb in FLOW_RELATIONSHIPS or verb in TREE_RELATIONSHIPS or verb in INFLUENCE_RELATIONSHIPS
            if core_style:
                add('ERROR', 'E011', f'"{verb}" is not one of the 24 core links but is drawn with the solid core-link arrow — use dashed influence style (endArrow=open;endFill=0;dashed=1)', i)
            if not known:
                add('WARNING', 'W105', f'verb "{verb}" is not in the core-link, flow, tree or influence vocabulary', i)

    # W111–W114 visual rules — on the renderer's geometry (edgy_geometry)
    F.extend(visual_findings(path, page, lines, cells, elements, containers, page_w, page_h))

    # W115 minimum rendered text size at the report scale (--scale), px → pt × 0.75
    scale = getattr(opts, 'scale', None)
    if scale:
        for i, c in cells.items():
            if i not in elements and not (c.get('edge') == '1' and c.get('source') and c.get('target')):
                continue
            raw = c.get('value') or ''
            if not strip_html(raw).strip():
                continue
            st = style_dict(c.get('style'))
            fs_default = float(st.get('fontSize', 11 if c.get('edge') == '1' else 12) or 12)
            sizes = [float(m) for m in re.findall(r'font-size:\s*(\d+(?:\.\d+)?)px', raw, re.I)] or []
            if not re.search(r'font-size:', raw.split('<br')[0], re.I):
                sizes.append(fs_default)          # the first (title) line uses the cell font size
            smallest = min(sizes) if sizes else fs_default
            pt = smallest * scale * 0.75
            if pt < 6.0:
                what = 'relation label' if c.get('edge') == '1' else ('description' if smallest < fs_default else 'title')
                add('WARNING', 'W115', f'{what} renders at {pt:.1f} pt at scale {scale:g} (minimum 6 pt) — enlarge the box text, split the view or print it larger', i)
    return F


def visual_findings(path, page, lines, cells, elements, containers, page_w, page_h):
    """Edge routes and label boxes against element boxes, other labels and the
    page. `elements` is {id: (cell, style, abs_box)} of EDGY elements."""
    F = []

    def add(rule, msg, cell, coords):
        F.append(Finding('WARNING', rule, msg, path, lines.get(cell) if cell else None, cell, page, coords))

    cache = {}
    boxes = {i: box for i, (_c, _st, box) in elements.items() if box}
    labels = []   # (edge id, source id, verb, label box)
    for i, e in cells.items():
        if e.get('edge') != '1':
            continue
        src, tgt = e.get('source'), e.get('target')
        if not src or not tgt:
            continue   # legend samples and free lines are not routes between elements
        st = style_dict(e.get('style'))
        points, sp, tp, offset, rel_x, rel_y = geo.edge_points(e)
        sb = geo.abs_box(cells, src, cache)
        tb = geo.abs_box(cells, tgt, cache)
        route = geo.edge_path(sb, tb, st, points, sp, tp)
        if not route or len(route) < 2:
            continue
        # W111: through a foreign element (containers never count)
        for j, box in boxes.items():
            if j in (src, tgt) or j in containers:
                continue
            inside = geo.path_through_box(route, box)
            if inside > W111_MIN_INSIDE:
                add('W111', f'edge "{strip_html(e.get("value") or "").strip() or "(unlabelled)"}" passes through element {j} ({inside:.0f} px inside) — move the element, add via: waypoints or change the exit/entry side',
                    i, {'edge': i, 'other': j, 'inside_px': round(inside, 1), 'route': [[round(x), round(y)] for x, y in route]})
        # W114a: route end outside the page
        if page_w and page_h:
            for px, py in (route[0], route[-1]):
                if px < 0 or py < 0 or px > page_w or py > page_h:
                    add('W114', f'edge end at ({px:.0f},{py:.0f}) is outside the page {page_w:.0f}x{page_h:.0f}', i,
                        {'edge': i, 'point': [round(px), round(py)]})
                    break
        verb = strip_html(e.get('value') or '').strip()
        if not verb:
            continue
        fs = float(st.get('fontSize', 11) or 11)
        lbox = geo.edge_label_box(route, verb.split('\n')[0], fs, rel_x, rel_y, offset)
        if lbox is None:
            continue
        labels.append((i, src, verb.lower(), lbox))
        area = max(lbox[2] * lbox[3], 1.0)
        # W112: label over an element (its own ends included — a label on the source box is unreadable too)
        for j, box in boxes.items():
            if j in containers:
                continue
            share = geo.rect_intersection(lbox, box) / area
            if share > W112_MIN_OVERLAP:
                add('W112', f'label "{verb}" lies {100 * share:.0f} % over element {j} — use label: source/target, an offset, or a longer edge',
                    i, {'edge': i, 'other': j, 'share': round(share, 2), 'label_box': [round(v) for v in lbox]})
        # W114b: label outside the page
        if geo.outside_page(lbox, page_w, page_h):
            add('W114', f'label "{verb}" extends outside the page', i, {'edge': i, 'label_box': [round(v) for v in lbox]})
    # W113: label over another label; a fan of edges from one source with one verb is a bus
    for a in range(len(labels)):
        ia, sa, va, ba = labels[a]
        for b in range(a + 1, len(labels)):
            ib, sb_, vb, bb = labels[b]
            if sa == sb_ and va == vb:
                continue
            inter = geo.rect_intersection(ba, bb)
            smaller = max(min(ba[2] * ba[3], bb[2] * bb[3]), 1.0)
            if inter / smaller > W113_MIN_OVERLAP:
                add('W113', f'label "{va}" overlaps label "{vb}" of edge {ib} by {100 * inter / smaller:.0f} %', ia,
                    {'edge': ia, 'other': ib, 'share': round(inter / smaller, 2)})
    return F


def lint_file(path, opts):
    lines = line_index(path)
    try:
        models = list(load_models(path))
    except ET.ParseError as e:
        return [Finding('ERROR', 'E001', f'XML does not parse: {e}', path)]
    except (ValueError, zlib.error, UnicodeDecodeError) as e:
        return [Finding('ERROR', 'E001', f'cannot read draw.io content: {e}', path)]
    if not models:
        return [Finding('ERROR', 'E001', 'no <mxGraphModel> found', path)]
    findings = []
    for page, model in models:
        findings.extend(lint_model(path, page if len(models) > 1 else None, model, lines, opts))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description='Lint EDGY draw.io diagrams', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split('Rules')[1] if 'Rules' in __doc__ else None)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--warnings-as-errors', action='store_true')
    ap.add_argument('--no-legend', action='store_true', help='do not require a legend')
    ap.add_argument('--json', action='store_true', help='print findings as JSON')
    ap.add_argument('--visual', action='store_true',
                    help='print only the visual findings (W111–W114) as JSON with coordinates')
    ap.add_argument('--scale', type=float, default=None,
                    help='report scale (rendered px per diagram px, e.g. 0.4 when a 1600 px page is printed '
                         '640 px wide); W115 when a title, description or relation label falls below 6 pt')
    ap.add_argument('-q', '--quiet', action='store_true', help='print only the summary line')
    opts = ap.parse_args(argv)

    all_findings = []
    for f in opts.files:
        if not os.path.isfile(f):
            print(f"{f}: ERROR E001 file not found", file=sys.stderr)
            return 2
        all_findings.extend(lint_file(f, opts))

    errors = [x for x in all_findings if x.level == 'ERROR']
    warnings = [x for x in all_findings if x.level == 'WARNING']
    if opts.visual:
        opts.json = True
        print(json.dumps([x.as_dict() for x in all_findings if x.rule in VISUAL_RULES], ensure_ascii=False, indent=2))
    elif opts.json:
        print(json.dumps([x.as_dict() for x in all_findings], ensure_ascii=False, indent=2))
    elif not opts.quiet:
        for x in all_findings:
            print(x)
    summary = f"edgy-lint: {len(opts.files)} file(s), {len(errors)} error(s), {len(warnings)} warning(s)"
    print(summary, file=sys.stderr if opts.json else sys.stdout)   # --json: stdout is pure JSON
    if errors or (opts.warnings_as_errors and warnings):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
