#!/usr/bin/env python3
"""
edgy_c4.py — the C4 notation handler of edgy-c4 0.1.0 (edgy-diagram extension contract 1).

A TXT page with `notation: c4` is drawn here, never by the EDGY parser:

  level: context    (L1) derived from the EDGY document graph for one application asset:
                    Persons — people or organisations that *interact with* it, and (inferred, dashed)
                    those that *perform* a process that *requires* it; Software Systems — its `transfers`
                    partners, `[external]` ones grey. A missing Person is a note.
  level: container  (L2) from the page itself: containers with ids and technology, relationships with a
                    description and {technology:}, the system boundary, and the boundary crossings named
                    by `{container: C-…}` on the EDGY `transfers` of the system.

`system: APP-07` (or `focus: APP-07`, which `expand: per-application` writes) names the application. The
handler writes static styled cells only (rectangles and the `person` shape) with `edgyNotation=c4`, so the
preview, the presenter and the linter draw them through the generic renderer. The legend reads
"C4 model (Simon Brown, CC BY 4.0)".

Rules (findings: (severity, rule, message, subject)):
  C001 error    {container:} names an unknown or invalid container, or one of neither endpoint
  C002 warning  a relationship without a description
  C003 warning  an L2 relationship without a technology
  C004 error    system: is not an application asset (or is a platform / integration)
  C005 warning  system: is not drawn on its hand-written L1 page
  C006 error    a container id declared twice

Contract entry points: prepass(pages, graph), generate_page(page_text, graph), page_id(page_text, graph),
lint_page(cells, page_name). Standard library only.
"""

import hashlib
import html
import re
import textwrap
from typing import Dict, List, Optional, Tuple

NOTATION = 'c4'
LEGEND_TITLE = 'C4 model (Simon Brown, CC BY 4.0)'
INFERRED_TEXT = 'inferred: performs a process that requires this system'
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/-]*$')
CONTAINER_ID_MAX = 64
APP_KINDS_NOT_SYSTEMS = ('platform', 'integration')

COLOURS = {
    'person': ('#08427b', '#073b6f', '#ffffff'),
    'inferred': ('#5d82a8', '#08427b', '#ffffff'),    # an inferred Person: lighter, with a dashed dark border
    'system': ('#1168bd', '#0b4884', '#ffffff'),
    'external': ('#999999', '#8a8a8a', '#ffffff'),
    'container': ('#438dd5', '#3c7fc0', '#ffffff'),
}
BOX_W, PERSON_W = 240, 200
GAP_X, ROW_GAP = 60, 140
FONT = 12

try:                                     # the glyph tables of edgy-diagram when it is on the path
    import edgy_text as _text
except ImportError:                      # pragma: no cover - standalone use
    _text = None


# ---- page text ---------------------------------------------------------------------------------------------
def _headers(page_text: str) -> Dict[str, str]:
    out = {}
    for ln in (page_text or '').split('\n'):
        m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*):\s*(\S.*)$', ln)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def _system_of(h: Dict[str, str]) -> str:
    return h.get('focus') or h.get('system') or ''


def _split_options(text: str) -> Dict[str, str]:
    opts, buf, quote = {}, '', None
    parts = []
    for ch in text:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
            buf += ch
        elif ch == ',':
            parts.append(buf)
            buf = ''
        else:
            buf += ch
    parts.append(buf)
    for p in parts:
        if ':' in p:
            k, v = p.split(':', 1)
            opts[k.strip().lower()] = v.strip().strip('"').strip("'")
    return opts


ELEMENT_RE = re.compile(r'^\s*-\s*(container|person|system):\s*"([^"]*)"\s*(\[[^\]]*\])?\s*(\{.*\})?\s*$')
REL_RE = re.compile(r'^\s*-\s*"([^"]+)"\s*->\s*"([^"]+)"\s*:\s*"([^"]*)"\s*(\{.*\})?\s*$')


def parse_body(page_text: str, unparsed: Optional[List[str]] = None) -> Tuple[List[dict], List[dict]]:
    """(elements, relationships) of a C4 page body; an item line it cannot read goes to `unparsed`."""
    elements, rels = [], []
    unparsed = unparsed if unparsed is not None else []
    section = None
    for ln in textwrap.dedent(page_text or '').split('\n'):
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        if re.match(r'^(elements|relationships):\s*$', s):
            section = s[:-1]
            continue
        if section and not s.startswith('-'):
            section = None                          # a header line after the sections ends them
            continue
        if section == 'elements':
            m = ELEMENT_RE.match(ln)
            if not m:
                unparsed.append(s)
            else:
                name, _, desc = m.group(2).partition(' - ')
                opts = _split_options(m.group(4)[1:-1]) if m.group(4) else {}
                tags = [t.strip().lower() for t in (m.group(3) or '')[1:-1].split(',') if t.strip()]
                elements.append({'type': m.group(1), 'name': name.strip(), 'description': desc.strip(),
                                 'id': opts.get('id', ''), 'technology': opts.get('technology', ''),
                                 'external': 'external' in tags})
        elif section == 'relationships':
            m = REL_RE.match(ln)
            if not m:
                unparsed.append(s)
            else:
                opts = _split_options(m.group(4)[1:-1]) if m.group(4) else {}
                rels.append({'source': m.group(1), 'target': m.group(2), 'description': m.group(3).strip(),
                             'technology': opts.get('technology', '')})
    return elements, rels


def _slug(mid: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', (mid or '').lower()).strip('-') or 'x'
    if slug != (mid or '').lower():
        slug += '-' + hashlib.sha1((mid or '').encode('utf-8')).hexdigest()[:6]
    return slug


def page_id(page_text: str, graph=None) -> str:
    """c4-context-app-07 / c4-container-app-07: fixed, so trace badges and back links resolve by id."""
    h = _headers(page_text)
    level = (h.get('level') or 'context').lower()
    return f"c4-{level if level in ('context', 'container') else 'page'}-{_slug(_system_of(h))}"


def container_ids(raw: str) -> List[str]:
    return [c.strip() for c in re.split(r'\s*;\s*', raw or '') if c.strip()]


# ---- prepass: pages and containers of the whole document ---------------------------------------------------
def prepass(pages: List[Tuple[str, str]], graph):
    """notation_index['c4'] = {'pages': {(level, system): page id}, 'containers': {id: {system, page, name,
    technology, description}}}; C006 for a second declaration, C001 for an EDGY {container:} that does not
    resolve (an unknown or invalid id, or a container of neither endpoint)."""
    index = {'pages': {}, 'containers': {}}
    findings = []
    for name, text in pages:
        h = _headers(text)
        level = (h.get('level') or 'context').lower()
        system = _system_of(h)
        if system:
            if (level, system) in index['pages']:
                findings.append(('error', 'C006', f"a second {level} page for {system} — one page per level and "
                                 f"system (its page id would repeat)", system, name))
            index['pages'][(level, system)] = page_id(text)
        if level != 'container':
            continue
        elements, _ = parse_body(text)
        for e in elements:
            if e['type'] != 'container':
                continue
            cid = e['id']
            if not _valid_container_id(cid):
                findings.append(('error', 'C001', f"container id '{cid}' is not a valid id (letters, digits, "
                                 f". _ : / -, at most {CONTAINER_ID_MAX} characters)", cid or e['name'], name))
                continue
            if cid in index['containers']:
                first = index['containers'][cid]['page']
                findings.append(('error', 'C006', f"container {cid} is declared twice (first on page '{first}')",
                                 cid, name))
                continue
            index['containers'][cid] = {'system': system, 'page': name, 'name': e['name'],
                                        'technology': e['technology'], 'description': e['description']}
    for edge in getattr(graph, 'edges', []) or []:
        raw = (edge.get('options') or {}).get('container')
        if not raw or edge.get('verb') != 'transfers':
            continue
        for cid in container_ids(raw):
            c = index['containers'].get(cid)
            if c is None:
                findings.append(('error', 'C001', f"{{container: {cid}}} on {edge['source']} → {edge['target']} "
                                 f"names no container of a C4 container page", cid, edge.get('page')))
            elif c['system'] not in (edge['source'], edge['target']):
                findings.append(('error', 'C001', f"{{container: {cid}}} on {edge['source']} → {edge['target']}: "
                                 f"{cid} belongs to {c['system']}, which is neither endpoint", cid, edge.get('page')))
    return index, findings


def _data_names(graph, edge) -> str:
    """The data a transfer carries, by name (DAT-01 → Fare rules)."""
    names = []
    for d in (edge.get('options') or {}).get('data') or []:
        n = graph.get(d) if graph is not None else None
        names.append(n['name'] if n else d)
    return '; '.join(names)


def _valid_container_id(cid: str) -> bool:
    return bool(cid) and len(cid) <= CONTAINER_ID_MAX and bool(ID_RE.match(cid)) and cid != '__proto__'


def crossings(graph, system: str, containers: Dict[str, dict]) -> List[dict]:
    """The boundary crossings of `system`: each EDGY transfers with a {container:} of the system attaches to the
    endpoint that owns the container — the target end, or the source end when the transfer leaves it."""
    out = []
    for edge in getattr(graph, 'edges', []) or []:
        raw = (edge.get('options') or {}).get('container')
        if not raw or edge.get('verb') != 'transfers' or system not in (edge['source'], edge['target']):
            continue
        for cid in container_ids(raw):
            c = containers.get(cid)
            if not c or c['system'] != system:
                continue
            data = _data_names(graph, edge)
            if edge['target'] == system:
                out.append({'source': edge['source'], 'target': cid, 'description': data or 'transfers',
                            'technology': edge['options'].get('technology') or '', 'external': edge['source']})
            else:
                out.append({'source': cid, 'target': edge['target'], 'description': data or 'transfers',
                            'technology': edge['options'].get('technology') or '', 'external': edge['target']})
    return out


# ---- drawing -----------------------------------------------------------------------------------------------
def _measure(text: str, size: float = FONT, bold: bool = False) -> float:
    if _text is not None:
        return _text.measure(text, size, bold=bold)
    return len(text) * size * (0.62 if bold else 0.55)


def _wrap(text: str, width: float, size: float, bold: bool = False) -> List[str]:
    lines, cur = [], ''
    for word in (text or '').split():
        cand = (cur + ' ' + word).strip()
        if cur and _measure(cand, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def legend_width(entries: List[Tuple[str, str, bool]]) -> float:
    """The legend's natural width: the page is centred on max(content, legend), never on the content alone."""
    w = 12 + _measure(LEGEND_TITLE, 11, True) + 16 + 8
    for label, _kind, _dashed in entries:
        w += 22 + _measure(label, 10) + 12 + 14
    return w + 8


class Drawing:
    def __init__(self):
        self.cells: List[str] = []
        self.next_id = 2
        self.max_x = 0
        self.max_y = 0

    def _id(self) -> str:
        self.next_id += 1
        return str(self.next_id)

    def box(self, kind: str, name: str, stereotype: str, description: str, x: float, y: float,
            w: float = BOX_W, dashed: bool = False, link: Optional[str] = None, role: str = '') -> Tuple[str, float]:
        fill, stroke, font = COLOURS[kind if kind in COLOURS else 'system']
        inner = w - 24
        name_lines = _wrap(name, inner, 14, True)
        st_lines = _wrap(stereotype, inner, 10)
        desc_lines = _wrap(description, inner, 11)
        parts = ['<b>' + '<br>'.join(html.escape(t) for t in name_lines) + '</b>']
        parts += [f'<font style="font-size:10px">{html.escape(t)}</font>' for t in st_lines]
        parts += [f'<font style="font-size:11px">{html.escape(t)}</font>' for t in desc_lines]
        head = 46 if kind == 'person' else 0
        h = head + 22 + 18 * len(name_lines) + 14 * len(st_lines) + 15 * len(desc_lines)
        h = max(h, 110 if kind == 'person' else 80)
        if kind == 'person':
            shape = (f"shape=mxgraph.basic.person;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                     f"fontColor={font};verticalAlign=bottom;spacingBottom=8;fontSize=14;")
        else:
            shape = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                     f"fontColor={font};verticalAlign=middle;fontSize=14;")
        if dashed:
            fill, stroke, font = COLOURS['inferred']
            shape = shape.replace(f"fillColor={COLOURS['person'][0]};strokeColor={COLOURS['person'][1]};",
                                  f"fillColor={fill};strokeColor={stroke};") + 'dashed=1;strokeWidth=3;'
        cid = self._id()
        self._vertex(cid, '<br>'.join(parts), shape + f"edgyNotation={NOTATION};{role}", x, y, w, h, link)
        return cid, h

    def _vertex(self, cid, value, style, x, y, w, h, link=None, parent='1'):
        geometry = (f'<mxGeometry x="{int(x)}" y="{int(y)}" width="{int(w)}" height="{int(h)}" as="geometry"/>')
        if link:            # a draw.io page link: the wrapper carries the id, the label and the link
            cell = (f'<UserObject id="{cid}" label="{html.escape(value, quote=True)}" link="data:page/id,{link}">'
                    f'<mxCell style="{style}" vertex="1" parent="{parent}">{geometry}</mxCell></UserObject>')
        else:
            cell = (f'<mxCell id="{cid}" value="{html.escape(value, quote=True)}" style="{style}" vertex="1" '
                    f'parent="{parent}">{geometry}</mxCell>')
        self.cells.append(cell)
        self.max_x = max(self.max_x, x + w)
        self.max_y = max(self.max_y, y + h)

    def text(self, value: str, x, y, w, h, size=12, bold=False, link=None, role='edgyRole=header;'):
        style = (f"text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontSize={size};"
                 f"fontStyle={1 if bold else 0};fontColor=#333333;edgyNotation={NOTATION};{role}")
        self._vertex(self._id(), html.escape(value), style, x, y, w, h, link)

    def frame(self, label: str, x, y, w, h):
        style = (f"rounded=1;arcSize=2;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#444444;dashed=1;"
                 f"verticalAlign=bottom;align=left;spacingLeft=10;spacingBottom=6;fontSize=12;fontStyle=1;"
                 f"fontColor=#444444;edgyNotation={NOTATION};edgyRole=container;")
        self._vertex(self._id(), html.escape(label), style, x, y, w, h)

    def edge(self, src: str, tgt: str, label: str, dashed: bool = False):
        style = (f"edgeStyle=none;html=1;endArrow=classic;endFill=1;strokeColor=#707070;fontSize=11;"
                 f"fontColor=#333333;labelBackgroundColor=#ffffff;{'dashed=1;' if dashed else ''}"
                 f"edgyNotation={NOTATION};")
        # html=1: the label is HTML, so its text is escaped once as HTML and once for the attribute
        self.cells.append(f'<mxCell id="{self._id()}" value="{html.escape(html.escape(label), quote=True)}" style="{style}" '
                          f'edge="1" source="{src}" target="{tgt}" parent="1">'
                          f'<mxGeometry relative="1" as="geometry"/></mxCell>')

    def legend(self, entries: List[Tuple[str, str, bool]], y: float):
        """Legend at the bottom: the attribution title and one swatch per kind drawn on the page."""
        x = 40
        w = max(self.max_x - 40, legend_width(entries))
        rows = 1
        style = (f"rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#e5e5e5;"
                 f"edgyNotation={NOTATION};edgyRole=legend;")
        self._vertex(self._id(), '', style, x, y, w, 40 * rows)
        tw = _measure(LEGEND_TITLE, 11, True) + 16
        self._vertex(self._id(), html.escape(LEGEND_TITLE),
                     f"text;html=1;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;fontColor=#333333;"
                     f"edgyNotation={NOTATION};edgyRole=legend;", x + 12, y + 8, tw, 24)
        cx = x + 12 + tw + 8
        for label, kind, dashed in entries:
            fill, stroke, _ = COLOURS['inferred' if dashed else kind]
            self._vertex(self._id(), '', f"rounded=1;fillColor={fill};strokeColor={stroke};"
                         f"{'dashed=1;strokeWidth=2;' if dashed else ''}edgyNotation={NOTATION};edgyRole=legend;",
                         cx, y + 13, 18, 14)
            lw = _measure(label, 10) + 12
            self._vertex(self._id(), html.escape(label), f"text;html=1;align=left;verticalAlign=middle;fontSize=10;"
                         f"fontColor=#333333;edgyNotation={NOTATION};edgyRole=legend;", cx + 22, y + 8, lw, 24)
            cx += 22 + lw + 14
        self.max_x = max(self.max_x, cx + 20)

    def xml(self) -> str:  # noqa: D401
        pw, ph = int(self.max_x + 60), int(self.max_y + 60)
        return ('<?xml version="1.0" encoding="utf-8"?>\n'
                f'<mxGraphModel dx="{pw}" dy="{ph}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
                f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{pw}" pageHeight="{ph}" math="0" shadow="0">'
                '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(self.cells) + '</root></mxGraphModel>')


def _row(d: Drawing, items: List[dict], y: float, centre_x: float, draw) -> Dict[str, Tuple[str, float]]:
    widths = [it.get('w', BOX_W) for it in items]
    total = sum(widths) + GAP_X * max(0, len(items) - 1)
    x = max(40.0, centre_x - total / 2)
    out = {}
    for it, w in zip(items, widths):
        out[it['key']] = draw(it, x, y)
        x += w + GAP_X
    return out


def _system_problem(graph, system: str) -> Optional[str]:
    node = graph.get(system) if graph is not None and system else None
    if node is None:
        return f"system: {system or '(none)'} is not an element of the model"
    if node['type'] != 'asset' or (node.get('kind') or '') in APP_KINDS_NOT_SYSTEMS or \
            (node.get('kind') or '') not in ('application', ''):
        what = node.get('kind') or node['type']
        return f"system: {system} is {what}, not an application asset — C4 draws applications only"
    return None


def _label(node: dict) -> Tuple[str, str]:
    return node['name'], node.get('subtext') or ''


def generate_page(page_text: str, graph):
    h = _headers(page_text)
    level = (h.get('level') or 'context').lower()
    system = _system_of(h)
    problem = _system_problem(graph, system)
    if problem:
        d = Drawing()
        d.text(problem, 40, 40, 640, 40)
        d.legend([], 120)
        return d.xml(), [('error', 'C004', problem, system or None)]
    unread: List[str] = []
    parse_body(page_text, unread)
    if unread:
        # a line nobody can read is never dropped in silence (a missing brace used to lose a container)
        msg = f"{len(unread)} line(s) of the C4 page are not understood: " + '; '.join(u[:80] for u in unread[:3])
        d = Drawing()
        d.text(msg, 40, 40, 640, 40)
        d.legend([], 120)
        return d.xml(), [('error', 'C007', msg, unread[0][:80])]
    if level not in ('context', 'container'):
        msg = f"level: {level} is not drawn by edgy-c4 0.1.0 (context, container)"
        d = Drawing()
        d.text(msg, 40, 40, 640, 40)
        d.legend([], 120)
        return d.xml(), [('error', 'C004', msg, system or None)]
    if level == 'container':
        return _container_page(page_text, graph, system)
    return _context_page(page_text, graph, system)


def _index(graph) -> dict:
    return (getattr(graph, 'notation_index', None) or {}).get(NOTATION) or {'pages': {}, 'containers': {}}


def _context_page(page_text: str, graph, system: str):
    findings = []
    node = graph.get(system)
    index = _index(graph)
    observed, inferred = [], {}
    for e in graph.edges:
        if e['target'] == system and e['verb'] == 'interacts with':
            src = graph.get(e['source'])
            if src and src['type'] in ('people', 'organisation') and src['id'] not in observed:
                observed.append(src['id'])
    for e in graph.edges:
        if e['target'] == system and e['verb'] == 'requires':
            proc = graph.get(e['source'])
            if not proc or proc['type'] != 'process':
                continue
            for p in graph.edges:
                if p['target'] == proc['id'] and p['verb'] == 'performs':
                    who = graph.get(p['source'])
                    if who and who['type'] in ('people', 'organisation') and who['id'] not in observed:
                        inferred.setdefault(who['id'], []).append(proc['name'])
    partners, links = [], {}
    for e in graph.edges:
        if e['verb'] != 'transfers' or system not in (e['source'], e['target']) or e['source'] == e['target']:
            continue
        other = e['target'] if e['source'] == system else e['source']
        if graph.get(other) is None:
            continue
        if other not in partners:
            partners.append(other)
        data = _data_names(graph, e) or 'transfers'
        tech = e['options'].get('technology')
        links.setdefault((e['source'], e['target']), []).append(data + (f' [{tech}]' if tech else ''))
    hand, _rels = parse_body(page_text)
    if hand:
        ids = {x['id'] for x in hand}
        if system not in ids:
            findings.append(('warning', 'C005', f"system: {system} is not drawn among the page's own elements — "
                             f"drawn anyway in the centre", system))
        for x in hand:                      # model elements written on the page join the derived ones
            if not x['id'] or x['id'] == system or graph.get(x['id']) is None:
                continue
            if x['type'] == 'person' and x['id'] not in observed:
                observed.append(x['id'])
            elif x['type'] == 'system' and x['id'] not in partners:
                partners.append(x['id'])
    d = Drawing()
    title = f"System context — {node['name']} [{system}]"
    persons = [{'key': m, 'w': PERSON_W} for m in observed + [m for m in inferred if m not in observed]]
    def is_ext(mid):
        return 'external' in [t.lower() for t in (graph.get(mid) or {}).get('tags') or []]
    entries = [('Person', 'person', False)] if observed else []
    if any(m not in observed for m in inferred):
        entries.append((INFERRED_TEXT, 'person', True))
    entries.append(('Software System', 'system', False))
    if is_ext(system) or any(is_ext(p) for p in partners):
        entries.append(('External system', 'external', False))
    note = 'No Person in the model: nobody interacts with this system or performs a process that requires it.'
    note_w = _measure(note, 11) + 24
    rows_w = [len(persons) * (PERSON_W + GAP_X) - GAP_X, len(partners) * (BOX_W + GAP_X) - GAP_X, BOX_W,
              legend_width(entries), 0 if persons else note_w]
    centre = 40 + max(rows_w) / 2           # the legend counts: a narrow diagram is centred on the page
    d.text(title, 40, 20, max(_measure(title, 14, True) + 20, 300), 28, size=14, bold=True)
    y = 80
    cells = {}

    def person(it, x, yy):
        n = graph.get(it['key'])
        dashed = it['key'] in inferred and it['key'] not in observed
        desc = ('performs ' + ', '.join(inferred[it['key']])) if dashed else \
            (n.get('subtext') or 'interacts with it')
        return d.box('person', n['name'], '[Person]', desc, x, yy, PERSON_W, dashed=dashed)
    if persons:
        placed = _row(d, persons, y, centre, person)
        cells.update({k: v[0] for k, v in placed.items()})
        y += max(v[1] for v in placed.values()) + ROW_GAP
    else:
        findings.append(('note', 'C4-L1', f"no Person for {system}: no people interact with it and no process that "
                         f"requires it is performed — add an 'interacts with' or 'performs' link", system))
        d.text(note, centre - note_w / 2, y, note_w, 40, size=11)   # said on the page, not only on the console
        y += 40 + 40
    l2 = index['pages'].get(('container', system))
    name, desc = _label(node)
    sid, sh = d.box('external' if is_ext(system) else 'system', name,
                    '[Software System, external]' if is_ext(system) else '[Software System]', desc,
                    centre - BOX_W / 2, y, link=l2)
    cells[system] = sid
    y += sh + ROW_GAP
    if partners:
        def partner(it, x, yy):
            n = graph.get(it['key'])
            ext = 'external' in [t.lower() for t in n.get('tags') or []]
            return d.box('external' if ext else 'system', n['name'],
                         '[Software System, external]' if ext else '[Software System]', n.get('subtext') or '', x, yy)
        placed = _row(d, [{'key': m} for m in partners], y, centre, partner)
        cells.update({k: v[0] for k, v in placed.items()})
    # short labels ("uses", the C4 habit): several Persons converge on the system and their labels must not
    # meet; the card says how (interacts with it / performs which process)
    for m in observed:
        d.edge(cells[m], sid, 'uses')
    for m in inferred:
        if m not in observed:
            d.edge(cells[m], sid, 'uses (inferred)', dashed=True)
    for (s, t), labels in links.items():
        if s in cells and t in cells:
            d.edge(cells[s], cells[t], '; '.join(labels))
    d.legend(entries, d.max_y + 50)
    return d.xml(), findings


def _container_page(page_text: str, graph, system: str):
    findings = []
    node = graph.get(system)
    index = _index(graph)
    elements, rels = parse_body(page_text)
    containers = [e for e in elements if e['type'] == 'container' and _valid_container_id(e['id'])]
    persons = [e for e in elements if e['type'] == 'person']
    own = {c['id'] for c in containers}
    seen = set()
    for c in list(containers):                     # C006 inside one page (across pages: the prepass)
        if c['id'] in seen:
            containers.remove(c)
        seen.add(c['id'])
    cross = crossings(graph, system, index['containers'])
    for r in rels:
        if not r['description']:
            findings.append(('warning', 'C002', f"relationship {r['source']} → {r['target']} has no description",
                             f"{r['source']} -> {r['target']}"))
        if not r['technology']:
            findings.append(('warning', 'C003', f"relationship {r['source']} → {r['target']} has no {{technology:}}",
                             f"{r['source']} -> {r['target']}"))
    for r in cross:
        if not r['technology']:
            findings.append(('warning', 'C003', f"boundary crossing {r['source']} → {r['target']} has no "
                             f"{{technology:}} on its EDGY transfers", f"{r['source']} -> {r['target']}"))
    externals = []
    person_ids = {p['id'] for p in persons}
    for r in rels + cross:
        for end in (r['source'], r['target']):
            if end not in own and end not in externals and end not in person_ids and graph.get(end):
                externals.append(end)
    for r in rels:                                  # an endpoint nobody declared is never dropped in silence
        for end in (r['source'], r['target']):
            if end not in own and end not in person_ids and graph.get(end) is None:
                findings.append(('error', 'C001', f"relationship {r['source']} → {r['target']}: {end} is not a "
                                 f"container or person of this page, nor an element of the model", end))
    d = Drawing()
    title = f"Containers — {node['name']} [{system}]"
    d.text(title, 40, 20, max(_measure(title, 14, True) + 20, 300), 28, size=14, bold=True)
    l1 = index['pages'].get(('context', system))
    if l1:
        d.text('↑ System context', 40, 50, 160, 22, size=11, link=l1, role='edgyRole=link;')
    rows_of = _container_rows(containers, rels, {r['source'] if r['target'] == r['external'] else r['target']
                                                 for r in cross})
    # a relationship between neighbours of one row runs in the gap: the gap fits its label
    def row_gap(row):
        ids = {c['id'] for c in row}
        labels = [(r['description'] or '') + (f" [{r['technology']}]" if r['technology'] else '')
                  for r in rels if r['source'] in ids and r['target'] in ids]
        return max([GAP_X] + [_measure(t, 11) + 40 for t in labels])
    gaps = [row_gap(r) for r in rows_of]
    inner_w = max([len(r) * BOX_W + (len(r) - 1) * g for r, g in zip(rows_of, gaps)] + [BOX_W])
    entries = [('Person', 'person', False)] if persons else []
    entries += [('Container', 'container', False), ('Software System', 'system', False)]
    total_w = max(inner_w + 80, len(externals) * (BOX_W + GAP_X), len(persons) * (PERSON_W + GAP_X),
                  legend_width(entries))
    centre = 40 + total_w / 2
    y = 100
    cells = {}
    if persons:
        placed = _row(d, [{'key': p['id'] or p['name'], 'w': PERSON_W, 'e': p} for p in persons], y, centre,
                      lambda it, x, yy: d.box('person', it['e']['name'], '[Person]', it['e']['description'], x, yy,
                                              PERSON_W))
        cells.update({k: v[0] for k, v in placed.items()})
        y += max(v[1] for v in placed.values()) + ROW_GAP
    frame_y = y
    mark = len(d.cells)                             # the boundary goes here, drawn behind its containers
    y += 40
    x0 = centre - inner_w / 2
    xs = {}
    for k, (row, gap) in enumerate(zip(rows_of, gaps)):
        row_h = 0
        rx = centre - (len(row) * BOX_W + (len(row) - 1) * gap) / 2
        for n, c in enumerate(row):
            x = rx + n * (BOX_W + gap)
            stereo = f"[Container: {c['technology']}]" if c['technology'] else '[Container]'
            cid, hh = d.box('container', c['name'], stereo, c['description'], x, y)
            cells[c['id']] = cid
            xs[c['id']] = x
            row_h = max(row_h, hh)
        y += row_h + (90 if k < len(rows_of) - 1 else 50)
    frame = f"{node['name']} [Software System]"
    d.frame(frame, x0 - 40, frame_y, inner_w + 80, y - frame_y)
    d.cells.insert(mark, d.cells.pop())
    y += ROW_GAP - 40
    if externals:
        def ext(it, x, yy):
            n = graph.get(it['key'])
            outside = 'external' in [t.lower() for t in n.get('tags') or []]
            return d.box('external' if outside else 'system', n['name'], '[Software System]', n.get('subtext') or '',
                         x, yy, link=index['pages'].get(('context', it['key'])))
        # each external under the container it connects to, in that order (straight, uncrossed lines)
        def anchor(m):
            ends = [r['target'] if r['source'] == m else r['source'] for r in rels + cross if m in (r['source'], r['target'])]
            return min([xs[e] for e in ends if e in xs] or [0])
        externals.sort(key=anchor)
        placed = _row(d, [{'key': m} for m in externals], y, centre, ext)
        cells.update({k: v[0] for k, v in placed.items()})
    for r in rels + cross:
        if r['source'] in cells and r['target'] in cells:
            label = (r['description'] or '') + (f" [{r['technology']}]" if r['technology'] else '')
            d.edge(cells[r['source']], cells[r['target']], label.strip())
    d.legend(entries, d.max_y + 50)
    return d.xml(), findings


def _container_rows(containers: List[dict], rels: List[dict], crossing: set) -> List[List[dict]]:
    """Rows of containers: a relationship points down (longest path from the sources); the containers that
    cross the boundary sit in the last row, next to the externals below; inside a row, containers joined by a
    relationship stand side by side."""
    ids = [c['id'] for c in containers]
    by = {c['id']: c for c in containers}
    internal = [(r['source'], r['target']) for r in rels if r['source'] in by and r['target'] in by
                and r['source'] != r['target']]
    rank = {i: 0 for i in ids}
    for _ in range(len(ids)):                      # longest path; a cycle stops after len(ids) rounds
        changed = False
        for s, t in internal:
            if rank[t] < rank[s] + 1:
                rank[t] = rank[s] + 1
                changed = True
        if not changed:
            break
    last = max(rank.values(), default=0)
    for i in ids:
        if i in crossing:
            rank[i] = last
    rows = []
    for r in sorted(set(rank.values())):
        row = [i for i in ids if rank[i] == r]
        rows.append(_chain_order(row, internal))
    return [[by[i] for i in row] for row in rows]


def _chain_order(row: List[str], edges: List[Tuple[str, str]]) -> List[str]:
    """Order a row so that containers joined inside it are neighbours (a path walk from an end)."""
    inside = [(s, t) for s, t in edges if s in row and t in row]
    if not inside:
        return row
    nb = {i: [] for i in row}
    for s, t in inside:
        nb[s].append(t)
        nb[t].append(s)
    out, seen = [], set()
    starts = [i for i in row if len(nb[i]) == 1] + [i for i in row if len(nb[i]) != 1]
    for start in starts:
        cur = start
        while cur is not None and cur not in seen:
            seen.add(cur)
            out.append(cur)
            cur = next((n for n in nb[cur] if n not in seen), None)
    return out


def lint_page(cells: dict, page_name: str) -> list:
    """Geometry and text checks on a drawn C4 page: every box and relationship has a label."""
    out = []
    for cid, c in (cells or {}).items():
        st = c.get('style') or ''
        if 'edgyNotation=c4' not in st or 'edgyRole=' in st:
            continue
        if c.get('vertex') == '1' and not (c.get('value') or '').strip():
            out.append(('WARNING', 'C002', f'C4 box without a label on {page_name}', cid))
    return out
