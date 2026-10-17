#!/usr/bin/env python3
"""
edgy_trace.py — the realisation trace (edgy-diagram 2.9.0, plan v2.5.0 F7).

From a customer journey down to the organisation, and back: one page per
element, each page showing the element (the focus) and its **direct**
neighbours over the EDGY links of the trace, placed by level:

    level 1  journey
    level 2  task, channel
    level 3  product
    level 4  capability
    level 5  process, asset, people
    level 6  organisation

* above  — linked elements of a lower level (what the focus serves), dimmed
* centre — the focus, and linked elements of its own level beside it
* below  — linked elements of a higher level (what realises the focus),
           grouped by level under a header

The band follows the level, never the arrow: every edge keeps its EDGY verb
and direction. Only the link rows of LINK_ROWS are walked (core links, the
v2.4.0 influence verbs and `organisation contains people`); `contains`
between two elements of the same type is shown as *part of* / *parts*
chips, and flows (`transfers` …) never appear. `people → process` is not an
EDGY link (E010) and is never drawn.

Pages: `expand: trace` writes an index page (journeys | organisations), one
page per element with an id at levels 1–6, and a list page for every band
with more than MAX_BAND cards. A card links to the page of its element when
that page is in the document (`data:page/id,…`, wrapped in a draw.io
UserObject); otherwise it has no link and is counted in a note. Page ids are
stable: `trace-<slug of the model id>`, with a short SHA-1 suffix when the
slug loses characters.

W129: an empty *below* band on the way down, for the keys of W129_KEYS, with
the evidence status of `{gaps: key=status}` (as W127): not_investigated /
unknown = warning, out_of_scope / confirmed_absent = note; every one is a
`model_gaps[]` entry. Never on `up` pages, never on organisations.

Standard library only.
"""

import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple

LEVEL = {'journey': 1, 'task': 2, 'channel': 2, 'product': 3, 'capability': 4,
         'process': 5, 'asset': 5, 'people': 5, 'organisation': 6}
TYPE_RANK = {t: i for i, t in enumerate(('journey', 'task', 'channel', 'product', 'capability',
                                         'process', 'asset', 'people', 'organisation'))}
# (source type, canonical verb, target type) — plan v2.5.0 §4 F7 link table
LINK_ROWS = {
    ('task', 'is part of', 'journey'), ('journey', 'traverses', 'channel'), ('task', 'uses', 'channel'),
    ('product', 'serves', 'task'), ('product', 'features in', 'journey'), ('product', 'offers', 'channel'),
    ('product', 'requires', 'capability'), ('process', 'creates', 'product'),
    ('process', 'realises', 'capability'), ('capability', 'requires', 'asset'),
    ('process', 'requires', 'asset'), ('process', 'accesses', 'asset'), ('people', 'interacts with', 'asset'),
    ('organisation', 'performs', 'process'), ('organisation', 'makes', 'product'),
    ('organisation', 'has', 'capability'), ('organisation', 'manages', 'asset'),
    ('organisation', 'contains', 'people'),
}
CANON_VERBS = sorted({v for _s, v, _t in LINK_ROWS} | {'contains'})
# gaps key → element types that fill it; the W129-checked keys per focus type (plan §4a)
KEY_TYPES = {'tasks': ('task',), 'channels': ('channel',), 'products': ('product',),
             'capabilities': ('capability',), 'processes': ('process',), 'resources': ('asset',),
             'organisation': ('organisation',)}
W129_KEYS = {'journey': ('tasks',), 'task': ('products',), 'channel': ('products',), 'product': ('capabilities',),
             'capability': ('processes', 'resources'), 'process': ('organisation',), 'asset': ('organisation',),
             'people': ('organisation',)}
GAP_STATUSES = ('not_investigated', 'out_of_scope', 'unknown', 'confirmed_absent')
LIST_COLUMNS = 5     # cards per row on a list page
EDGE_ROW_MAX = 8     # a row with more cards: its edges are shown by position, the verb in the row header
EDGE_BAND_MAX = 8    # a band with more cards (all its rows): the same for the whole band — ten links converging on
                     # one focus from several rows are a bundle of parallel lines nobody can follow
MAX_BAND = 12          # more cards than this in a band: MAX_BAND - 1 cards and a "+N more" card
SOFT_CAP_PAGES = 100   # above this many trace pages a note suggests a narrower where:

LEVEL_TITLES = {
    'en': {1: 'Journeys', 2: 'Tasks and channels', 3: 'Products and services', 4: 'Capabilities',
           5: 'Processes, assets and actors', 6: 'Organisation', 'beside': 'Same level',
           'index': 'Realisation trace', 'journeys': 'Journeys — start here and go down',
           'organisations': 'Organisations — start here and go up', 'more': '+{n} more', 'list': '{name} — {band} ({n})',
           'above': 'above', 'below': 'below', 'centre': 'same level'},
    'fi': {1: 'Asiakaspolut', 2: 'Tehtävät ja kanavat', 3: 'Tuotteet ja palvelut', 4: 'Kyvykkyydet',
           5: 'Prosessit, resurssit ja toimijat', 6: 'Organisaatio', 'beside': 'Sama taso',
           'index': 'Toteutusketju', 'journeys': 'Asiakaspolut — aloita tästä alaspäin',
           'organisations': 'Organisaatiot — aloita tästä ylöspäin', 'more': '+{n} lisää',
           'list': '{name} — {band} ({n})', 'above': 'yläpuolella', 'below': 'alapuolella', 'centre': 'samalla tasolla'},
    'fr': {1: 'Parcours', 2: 'Tâches et canaux', 3: 'Produits et services', 4: 'Capacités',
           5: 'Processus, ressources et acteurs', 6: 'Organisation', 'beside': 'Même niveau',
           'index': 'Chaîne de réalisation', 'journeys': 'Parcours — commencez ici et descendez',
           'organisations': 'Organisations — commencez ici et remontez', 'more': '+{n} de plus',
           'list': '{name} — {band} ({n})', 'above': 'au-dessus', 'below': 'en dessous', 'centre': 'même niveau'},
    'de': {1: 'Journeys', 2: 'Aufgaben und Kanäle', 3: 'Produkte und Services', 4: 'Fähigkeiten',
           5: 'Prozesse, Ressourcen und Akteure', 6: 'Organisation', 'beside': 'Gleiche Ebene',
           'index': 'Realisierungskette', 'journeys': 'Journeys — hier beginnen und absteigen',
           'organisations': 'Organisationen — hier beginnen und aufsteigen', 'more': '+{n} weitere',
           'list': '{name} — {band} ({n})', 'above': 'darüber', 'below': 'darunter', 'centre': 'gleiche Ebene'},
}

_SLUG = re.compile(r'[^a-z0-9]+')


# ---- vocabulary --------------------------------------------------------------------------------------

_CANON_CACHE: Dict[str, Optional[str]] = {}


def canon(verb: str) -> Optional[str]:
    """The canonical (English) verb of a trace link in any of the four languages, else None."""
    key = (verb or '').lower().strip()
    if key not in _CANON_CACHE:
        import edgy_vocab
        hit = None
        for c in CANON_VERBS:
            if key == c or key in edgy_vocab.spellings(c):
                hit = c
                break
        _CANON_CACHE[key] = hit
    return _CANON_CACHE[key]


# ---- ids ------------------------------------------------------------------------------------------------

def page_id(model_id: str) -> str:
    """trace-<slug>; when the slug loses characters (/ : . _ …), six hex characters of the SHA-1 of the
    UTF-8 id are appended so the id stays unique and deterministic (plan §4a, CX7)."""
    slug = _SLUG.sub('-', model_id.lower()).strip('-') or 'x'
    if slug != model_id.lower():
        slug += '-' + hashlib.sha1(model_id.encode('utf-8')).hexdigest()[:6]
    return 'trace-' + slug


def list_page_id(focus_mid: str, band: str) -> str:
    return f"{page_id(focus_mid)}-more-{band}"


INDEX_PAGE_ID = 'trace-index'


# ---- traversal ------------------------------------------------------------------------------------------

def _sort_key(graph, node: dict):
    return (LEVEL.get(node['type'], 9), TYPE_RANK.get(node['type'], 99), node['id'])


def neighbours(graph, mid: str) -> List[dict]:
    """[{node, edges, band}] — the direct neighbours of `mid` over LINK_ROWS, one entry per neighbour
    (every edge between the two kept), sorted by level, type, id. band: above / centre / below."""
    focus = graph.get(mid)
    if focus is None or focus['type'] not in LEVEL:
        return []
    found: Dict[str, dict] = {}
    for e in graph.edges:
        if e['source'] != mid and e['target'] != mid:
            continue
        other_id = e['target'] if e['source'] == mid else e['source']
        if other_id == mid:
            continue
        other = graph.get(other_id)
        src, tgt = graph.get(e['source']), graph.get(e['target'])
        if other is None or src is None or tgt is None or other['type'] not in LEVEL:
            continue
        c = canon(e['verb'])
        if c is None or (src['type'], c, tgt['type']) not in LINK_ROWS:
            continue
        lf, lo = LEVEL[focus['type']], LEVEL[other['type']]
        band = 'above' if lo < lf else 'below' if lo > lf else 'centre'
        entry = found.setdefault(other['id'], {'node': other, 'edges': [], 'band': band})
        entry['edges'].append(e)
    return sorted(found.values(), key=lambda x: _sort_key(graph, x['node']))


def chips(graph, mid: str) -> Tuple[List[dict], List[dict]]:
    """(parents, parts): `contains` between elements of the same type as the focus."""
    focus = graph.get(mid)
    if focus is None:
        return [], []
    parents, parts = [], []
    for e in graph.edges:
        if canon(e['verb']) != 'contains':
            continue
        src, tgt = graph.get(e['source']), graph.get(e['target'])
        if not src or not tgt or src['type'] != tgt['type'] or src['type'] != focus['type']:
            continue
        if tgt['id'] == mid and src['id'] != mid and src not in parents:
            parents.append(src)
        if src['id'] == mid and tgt['id'] != mid and tgt not in parts:
            parts.append(tgt)
    key = lambda n: n['id']  # noqa: E731
    return sorted(parents, key=key), sorted(parts, key=key)


def contains_cycles(graph) -> List[List[str]]:
    """Cycles in same-type `contains` (a malformed hierarchy) — reported, never followed."""
    succ: Dict[str, List[str]] = {}
    for e in graph.edges:
        if canon(e['verb']) != 'contains':
            continue
        src, tgt = graph.get(e['source']), graph.get(e['target'])
        if src and tgt and src['type'] == tgt['type'] and src['id'] != tgt['id']:
            succ.setdefault(src['id'], []).append(tgt['id'])
    cycles, state = [], {}

    def visit(n, path):
        state[n] = 1
        for m in sorted(succ.get(n, [])):
            if state.get(m) == 1:
                cyc = path[path.index(m):] + [m] if m in path else [n, m]
                if sorted(cyc[:-1]) not in [sorted(c[:-1]) for c in cycles]:
                    cycles.append(cyc)
            elif not state.get(m):
                visit(m, path + [m])
        state[n] = 2
    for n in sorted(succ):
        if not state.get(n):
            visit(n, [n])
    return cycles


def trace_nodes(graph) -> List[dict]:
    """Every element at levels 1–6, in level / type / id order (slug ids included; the caller filters)."""
    return sorted((graph.nodes[m] for m in graph.order if graph.nodes[m]['type'] in LEVEL),
                  key=lambda n: _sort_key(graph, n))


def page_set(graph, where: Optional[str], direction: str) -> Tuple[List[dict], List[str], List[str]]:
    """(nodes that get a trace page, notes, problems). `where:` ids | highlight | from <id>; `from` is the
    downward closure (to higher and same levels), or the upward one with trace_direction: up."""
    notes, problems = [], []
    nodes = trace_nodes(graph)
    no_id = [n for n in nodes if not n['explicit']]
    nodes = [n for n in nodes if n['explicit']]
    if no_id:
        notes.append(f"trace: {len(no_id)} element(s) without an id skipped "
                     f"({', '.join(n['name'] for n in no_id[:4])}{' …' if len(no_id) > 4 else ''}) — write {{id: …}}")
    if where:
        w = where.strip()
        if w.lower() == 'highlight':
            nodes = [n for n in nodes if n.get('highlight')]
        elif w.lower().startswith('from '):
            start = graph.get(w[5:].strip())
            if start is None or start['type'] not in LEVEL or not start['explicit']:
                problems.append(f"expand: trace — where: {w} names no element of the trace with an id")
                return [], notes, problems
            keep, frontier = {start['id']}, [start['id']]
            while frontier:
                cur = frontier.pop()
                for nb in neighbours(graph, cur):
                    o = nb['node']
                    if not o['explicit'] or o['id'] in keep:
                        continue
                    # the downward closure (plan §4a); trace_direction: up gives the upward one. Same-level
                    # links are walked too: a process reaches its application (requires, both level 5) and an
                    # asset its process, or the chain breaks inside a level
                    if nb['band'] in ('centre', 'above' if direction == 'up' else 'below'):
                        keep.add(o['id'])
                        frontier.append(o['id'])
            nodes = [n for n in nodes if n['id'] in keep]
        else:
            ids = [x.strip() for x in w.split(',') if x.strip()]
            known = {n['id'].lower(): n for n in nodes}
            for i in ids:
                if i.lower() not in known:
                    problems.append(f"expand: trace — where: {i} is not an element of the trace with an id")
            wanted = {i.lower() for i in ids}
            nodes = [n for n in nodes if n['id'].lower() in wanted]
    if not nodes:
        problems.append("expand: trace found no element at levels 1–6 (journey … organisation) with an explicit id")
    return nodes, notes, problems


# ---- derived page content (edgy_views.materialize) ------------------------------------------------------

def _lang(parser) -> str:
    return parser.language if parser.language in LEVEL_TITLES else 'en'


def materialize(parser, graph):
    """(nodes, rels) for edgy_views: a trace page (focus), the index page or a list page."""
    links: Set[str] = getattr(parser, 'trace_pages', None) or set()
    view = parser.view
    if (view.get('trace_index') or '').lower() in ('yes', 'true'):
        picked = []
        for n in trace_nodes(graph):
            if n['type'] in ('journey', 'organisation') and n['id'] in links:
                picked.append(dict(n, _extra={'tband': 'index', 'tlink': page_id(n['id'])}))
        return picked, []
    focus = graph.get(view.get('focus') or '')
    if focus is None or focus['type'] not in LEVEL:
        msg = f"trace: focus {view.get('focus') or '(none)'} is not a journey, task, channel, product, capability, " \
              f"process, asset, people or organisation of the document"
        parser.warnings.append(msg)
        parser.errors.append(msg)
        return [], []
    direction = (view.get('trace_direction') or 'both').lower()
    only = (view.get('trace_list') or '').lower()
    nbs = neighbours(graph, focus['id'])
    if direction == 'down':
        nbs = [x for x in nbs if x['band'] != 'above']
    elif direction == 'up':
        nbs = [x for x in nbs if x['band'] != 'below']
    if only:
        nbs = [x for x in nbs if x['band'] == only]
    focus_extra = {'highlight': 'yes', 'tband': 'focus'}
    if only and focus['id'] in links:
        focus_extra['tlink'] = page_id(focus['id'])     # a list page's focus card leads back to its trace page
    if notation_page(graph, focus):
        focus_extra['tc4'] = notation_page(graph, focus)
    nodes = [dict(focus, _extra=focus_extra)]
    rels, hidden = [], 0
    per_band: Dict[str, int] = {}
    unlinked = 0
    parser.trace_more = {}
    for x in nbs:
        band = x['band']
        per_band[band] = per_band.get(band, 0) + 1
        total = sum(1 for y in nbs if y['band'] == band)
        if not only and total > MAX_BAND and per_band[band] > MAX_BAND - 1:
            hidden += 1
            parser.trace_more[band] = (total - (MAX_BAND - 1), list_page_id(focus['id'], band)
                                       if list_page_id(focus['id'], band) in links else None)
            continue
        o = x['node']
        extra = {'tband': band, 'tlevel': str(LEVEL[o['type']])}
        if band == 'above':
            extra['dim'] = 'yes'
        if o['id'] in links:
            extra['tlink'] = page_id(o['id'])
        else:
            unlinked += 1
        if notation_page(graph, o):
            extra['tc4'] = notation_page(graph, o)
        nodes.append(dict(o, _extra=extra))
        rels.extend(x['edges'])
    parents, parts = chips(graph, focus['id'])
    parser.trace_chips = ([p['name'] for p in parents], [p['name'] for p in parts])
    parser.trace_unlinked = unlinked
    parser.trace_hidden = hidden
    return nodes, rels


def notation_page(graph, node) -> Optional[str]:
    """Q3: the page id of the C4 system context of an application, when the document has one (a notation
    prepass index with pages[('context', id)]). The trace card keeps its own link; this is a second action."""
    if node.get('type') != 'asset' or (node.get('kind') or '') != 'application':
        return None
    for index in (getattr(graph, 'notation_index', None) or {}).values():
        pages = index.get('pages') if isinstance(index, dict) else None
        if isinstance(pages, dict) and pages.get(('context', node['id'])):
            return pages[('context', node['id'])]
    return None


# ---- layout (called from EDGYParser through edgy_architecture.prepare / the layout dispatch) ----------------

def prepare(p) -> None:
    """Bands of a trace page, W129 and the notes; sets p._arch_layout = ('trace', …)."""
    import edgy_architecture as arch
    lang = _lang(p)
    if (p.view.get('trace_index') or '').lower() in ('yes', 'true'):
        cols = {'journey': [], 'organisation': []}
        for eid, e in p.elements.items():
            if e['type'] in cols:
                cols[e['type']].append(eid)
        p._arch_layout = ('trace-index', cols)
        return
    focus_ref = (p.view.get('focus') or '').strip().lower()
    focus = next((eid for eid, e in p.elements.items() if (e.get('ref') or '').lower() == focus_ref), None)
    if focus is None:
        return
    bands: Dict[str, Dict[int, List[str]]] = {'above': {}, 'centre': {}, 'below': {}}
    for eid, e in p.elements.items():
        if eid == focus:
            continue
        a = e.get('attrs') or {}
        band = a.get('tband')
        if band in bands:
            bands[band].setdefault(int(a.get('tlevel') or LEVEL.get(e['type'], 9)), []).append(eid)
    direction = (p.view.get('trace_direction') or 'both').lower()
    fe = p.elements[focus]
    p.model_gaps = []
    if direction in ('both', 'down') and not (p.view.get('trace_list') or ''):
        gaps = arch.parse_gaps((fe.get('attrs') or {}).get('gaps'))
        below_types = {p.elements[i]['type'] for ids in bands['below'].values() for i in ids}
        for key in W129_KEYS.get(fe['type'], ()):
            if any(t in below_types for t in KEY_TYPES[key]):
                continue
            status = gaps.get(key, 'not_investigated')
            if status not in GAP_STATUSES:
                arch._once(p, f"gaps: {key}={status} is not a status ({', '.join(GAP_STATUSES)}) — not_investigated")
                status = 'not_investigated'
            p.model_gaps.append({'rule': 'W129', 'element_id': fe.get('ref'), 'band': key, 'status': status})
            open_q = status in ('not_investigated', 'unknown')
            msg = (f"W129 {fe.get('ref')} {fe['name']}: no {key} below — {status.replace('_', ' ')}"
                   f"{' (a model gap, not a layout error; set {gaps: ' + key + '=…} once it is known)' if open_q else ''}")
            arch._once(p, msg, note=not open_q)
    # crowded rows and list pages: the edges are shown by position (the verb goes into the row header) — a fan of
    # ten arrows into one card reads as noise, not as ten links
    p.trace_row_verbs = {}
    listing = bool(p.view.get('trace_list'))
    for band, by_level in bands.items():
        band_total = sum(len(ids) for ids in by_level.values()) + (1 if band in (p.trace_more or {}) else 0)
        for lvl, ids in by_level.items():
            if not listing and len(ids) <= EDGE_ROW_MAX and (band == 'centre' or band_total <= EDGE_BAND_MAX):
                continue
            members = set(ids)
            verbs = []
            for r in p.relationships:
                if {r['source'], r['target']} & members and focus in (r['source'], r['target']):
                    r['suppressed'] = True
                    if r['label'] not in verbs:
                        verbs.append(r['label'])
            p.trace_row_verbs[(band, lvl)] = verbs
            if verbs:
                arch._once(p, f"trace: {len(ids)} {LEVEL_TITLES[lang][lvl].lower()} "
                              f"{'listed' if listing else 'in one row' if len(ids) > EDGE_ROW_MAX else 'in a crowded band'}"
                              f" — their links ({', '.join(verbs)}) are shown by "
                              f"position and named in the row header, not drawn", note=True)
    unlinked = getattr(p, 'trace_unlinked', 0)
    if unlinked:
        arch._once(p, f"trace: {unlinked} card(s) without a page on this page (outside where:) — drawn without a link",
                   note=True)
    hidden = getattr(p, 'trace_hidden', 0)
    if hidden:
        arch._once(p, f"trace: {hidden} card(s) hidden on {p.page_id or 'this page'} — the '+N more' card lists them",
                   note=True)
    p._arch_layout = ('trace', focus, bands)


def layout(p, items: List[str]) -> Dict[str, Tuple[int, int]]:
    import edgy_text
    if p._arch_layout[0] == 'trace-index':
        return _layout_index(p, items)
    _, focus, bands = p._arch_layout
    lang = _lang(p)
    titles = LEVEL_TITLES[lang]
    sizes = {i: p._size_of(i) for i in items}
    present = set(items)
    GAP, ROW_GAP = 24, 100
    MORE_W = 130
    rows: List[Tuple[str, Optional[int], List[str]]] = []
    centre: List[str] = []
    if (p.view.get('trace_list') or ''):
        # list page: the focus, then the whole band as a grid of LIST_COLUMNS (one long row breaks W120)
        # one row group per level, each with its own header (a list of capabilities and processes under one
        # "Products" header misleads); the focus stays on its side, as on the trace page
        band = p.view['trace_list'].lower()
        groups = []
        for lvl in sorted(bands.get(band, {})):
            ids = [i for i in bands[band][lvl] if i in present]
            groups += [(band, lvl, ids[k:k + LIST_COLUMNS]) for k in range(0, len(ids), LIST_COLUMNS)]
        rows = groups + [('centre', None, [focus])] if band == 'above' else [('centre', None, [focus])] + groups
        bands = {b: (bands.get(b, {}) if b == band else {}) for b in ('above', 'centre', 'below')}
    else:
        for lvl in sorted(bands['above']):
            rows += _split_by_type(p, 'above', lvl, [i for i in bands['above'][lvl] if i in present])
        centre = [i for lvl in sorted(bands['centre']) for i in bands['centre'][lvl] if i in present]
        rows.append(('centre', None, [focus] + centre))
        for lvl in sorted(bands['below']):
            rows += _split_by_type(p, 'below', lvl, [i for i in bands['below'][lvl] if i in present])
    more = getattr(p, 'trace_more', {}) or {}
    row_verbs = getattr(p, 'trace_row_verbs', {}) or {}

    def row_title(band, lvl):
        verbs = row_verbs.get((band, lvl))
        count = f" ({len(bands[band][lvl])})" if p.view.get('trace_list') and lvl in bands.get(band, {}) else ''
        return titles[lvl] + (f" — {' / '.join(verbs)}" if verbs else '') + count
    header_w = {}
    for band, lvl, ids in rows:
        if lvl is not None and ids:
            header_w[(band, lvl)] = int(edgy_text.measure(row_title(band, lvl), 12, bold=True)) + 16

    def row_width(band, lvl, ids):
        w = sum(sizes[i][0] for i in ids) + GAP * max(0, len(ids) - 1)
        if band in more and lvl is not None and ids and ids[-1] == _last_card(rows, band):
            w += GAP + MORE_W
        return w

    hw_max = max(header_w.values() or [0])
    widths = [row_width(b, l, ids) for b, l, ids in rows if ids]
    fw = sizes[focus][0]
    centre_half_right = sum(sizes[i][0] + GAP for i in centre)
    half = max([w / 2 for w in widths] + [fw / 2 + centre_half_right])
    x_left = 60 + (hw_max + 20 if hw_max else 0)
    p._left_reserve = hw_max + 20 if hw_max else 0     # the canvas normalisation keeps the level headers on the page
    cx = x_left + half
    positions: Dict[str, Tuple[int, int]] = {}
    p._chain_headers = []
    p.trace_more_pos = {}
    level_headers = []
    y = 60
    headed = set()
    last_row = {}
    for k, (band, lvl, ids) in enumerate(rows):
        if ids and band in more and lvl is not None:
            last_row[band] = k
    for k, (band, lvl, ids) in enumerate(rows):
        if not ids:
            continue
        if band == 'centre':
            fx = cx - fw / 2
            positions[focus] = (fx, y)
            x = fx + fw + GAP
            for i in centre:
                positions[i] = (x, y)
                x += sizes[i][0] + GAP
            if centre:
                p._chain_headers.append((titles['beside'], centre[0], 0, max(sizes[centre[0]][0], 120), -30))
        else:
            w = row_width(band, lvl, ids)
            x = cx - w / 2
            for i in ids:
                positions[i] = (x, y)
                x += sizes[i][0] + GAP
            if last_row.get(band) == k:
                p.trace_more_pos[band] = (x, y, MORE_W, max(sizes[i][1] for i in ids))
            if lvl is not None and (band, lvl) not in headed:
                headed.add((band, lvl))
                level_headers.append((row_title(band, lvl), ids[0], header_w[(band, lvl)]))
        y += max(sizes[i][1] for i in ids) + ROW_GAP
    # the leftmost card starts at x_left, so the canvas normalisation moves nothing and the headers stay put
    dx = x_left - min(x for x, _ in positions.values())
    positions = {i: (x + dx, yy) for i, (x, yy) in positions.items()}
    p.trace_more_pos = {b: (x + dx, yy, w, h) for b, (x, yy, w, h) in p.trace_more_pos.items()}
    for text, first, hw in level_headers:
        # the level header stands left of its row, right-aligned to the card column (edges come from above / below)
        p._chain_headers.append((text, first, (x_left - hw - 20) - positions[first][0], hw,
                                 int(sizes[first][1] / 2) - 4))
    rest = [i for i in items if i not in positions]
    x = 60
    for i in rest:
        positions[i] = (x, y)
        x += sizes[i][0] + 40
    p._layout_handles_tree = True
    return positions


ROW_SPLIT = 5    # a level row of more cards than this, holding several types, gets one row per type


def _split_by_type(p, band, lvl, ids):
    """A crowded mixed row (tasks and channels, processes / assets / people) becomes one row per type:
    one long row of six cards and nothing else is too wide for a slide (W120)."""
    if len(ids) <= ROW_SPLIT:
        return [(band, lvl, ids)]
    groups: Dict[str, List[str]] = {}
    for i in ids:
        groups.setdefault(p.elements[i]['type'], []).append(i)
    return [(band, lvl, g) for g in groups.values()]


def _last_card(rows, band):
    ids = [i for b, l, r in rows if b == band and l is not None for i in r]
    return ids[-1] if ids else None


def _layout_index(p, items: List[str]) -> Dict[str, Tuple[int, int]]:
    import edgy_text
    _, cols = p._arch_layout
    lang = _lang(p)
    titles = LEVEL_TITLES[lang]
    sizes = {i: p._size_of(i) for i in items}
    present = set(items)
    positions: Dict[str, Tuple[int, int]] = {}
    p._chain_headers = []
    x = 60
    col_w = max([sizes[i][0] for i in items] + [200])
    for key, title in (('journey', titles['journeys']), ('organisation', titles['organisations'])):
        ids = [i for i in cols[key] if i in present]
        y = 60 + 40
        for i in ids:
            positions[i] = (x, y)
            y += sizes[i][1] + 20
        if ids:
            tw = max(int(edgy_text.measure(title, 12, bold=True)) + 16, col_w)
            p._chain_headers.append((title, ids[0], 0, tw, -40))
            x += max(col_w, tw) + 80
    p._layout_handles_tree = True
    return positions
