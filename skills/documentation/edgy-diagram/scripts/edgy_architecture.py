#!/usr/bin/env python3
"""
edgy_architecture.py — the architecture views of edgy-diagram 2.8.0 (plan F1, F2).

Applications and data are EDGY **Assets** (`{kind: application}`, `{kind: data}`),
so every view below stays EDGY notation; these functions only prepare a page
for the existing layouts (groups, matrix rows × columns, lanes) and add the
two layouts that did not exist (the value chain, the swimlane staircase).

Application map — `map_type: application`
  * domains: `group:` as today; with `rows: Channel, Core, Shared` and
    `{row: …}` the domains become the columns of a domains × layers matrix
  * `group_by: capability`: an application sits in the area of the capability
    that `requires` it — the link marked `{primary: true}`, else the single
    requiring capability; several without a primary → the **Shared** strip
    (input order never decides an architectural home); none → **Not
    required by a capability**. The capabilities are not drawn: their
    `requires` links are shown by the membership (reported)
  * `[external]` applications go to an **External systems** column
  * lifecycle badge `{time: tolerate | invest | migrate | eliminate}`
    (Gartner TIME), second badge `{criticality: …}` or `{hosting: …}`
  * integrations: `transfers` between assets; `edges: direct | none`
    (default direct up to 12 integrations, none above — the card counts its
    integrations and the presenter still shows them on hover)
  * W124 application without an owner (`manages` from an organisation or
    `{owner: …}`) — a note by default, a warning with `ownership: required`;
    W125 an integration without a data asset (`{data: …}`)

Process maps — `map_type: process` (the default stays the sequence row)
  * `process_view: chain`: L1 = processes without a `contains` parent, a row
    of pentagons; their L2 children stacked under each (L3 with `depth: 3`);
    `{band: management | core | support}` on the L1 processes gives three
    rows (the process landscape). `contains` is shown by the position
  * `process_view: swimlane`: one lane per actor that `performs` the process
    (Organisation or People), the steps in input order as a staircase, the
    assets a step `requires` as a chip line under it (`chips: assets`,
    default on)
  * W126 on a banded chain: an L1 without `{band:}`, or an L2 with another
    band than its parent

Standard library only.
"""

from typing import Dict, List, Optional, Tuple

APPLICATION_KINDS = ('application', 'platform', 'integration')
TIME_PALETTE = {'tolerate': '#ccbb44', 'invest': '#228833', 'migrate': '#4477aa', 'eliminate': '#ee6677'}
TIME_LABELS = {
    'en': {'tolerate': 'Tolerate', 'invest': 'Invest', 'migrate': 'Migrate', 'eliminate': 'Eliminate'},
    'fi': {'tolerate': 'Siedä', 'invest': 'Investoi', 'migrate': 'Siirrä', 'eliminate': 'Poista'},
    'fr': {'tolerate': 'Tolérer', 'invest': 'Investir', 'migrate': 'Migrer', 'eliminate': 'Éliminer'},
    'de': {'tolerate': 'Tolerieren', 'invest': 'Investieren', 'migrate': 'Migrieren', 'eliminate': 'Eliminieren'},
}
TIME_SYNONYMS = {'tolerate': 'tolerate', 'siedä': 'tolerate', 'tolérer': 'tolerate', 'tolerieren': 'tolerate',
                 'invest': 'invest', 'investoi': 'invest', 'investir': 'invest', 'investieren': 'invest',
                 'migrate': 'migrate', 'siirrä': 'migrate', 'migrer': 'migrate', 'migrieren': 'migrate',
                 'eliminate': 'eliminate', 'poista': 'eliminate', 'éliminer': 'eliminate', 'eliminieren': 'eliminate'}
BAND_ORDER = ('management', 'core', 'support')
BAND_LABELS = {
    'en': {'management': 'Management processes', 'core': 'Core processes', 'support': 'Support processes'},
    'fi': {'management': 'Johtamisprosessit', 'core': 'Ydinprosessit', 'support': 'Tukiprosessit'},
    'fr': {'management': 'Processus de pilotage', 'core': 'Processus cœur', 'support': 'Processus support'},
    'de': {'management': 'Führungsprozesse', 'core': 'Kernprozesse', 'support': 'Unterstützungsprozesse'},
}
AREA_LABELS = {
    'en': {'shared': 'Shared', 'none': 'Not required by a capability', 'external': 'External systems'},
    'fi': {'shared': 'Jaetut', 'none': 'Ei kyvykkyyden vaatima', 'external': 'Ulkoiset järjestelmät'},
    'fr': {'shared': 'Partagées', 'none': 'Requise par aucune capacité', 'external': 'Systèmes externes'},
    'de': {'shared': 'Gemeinsam', 'none': 'Von keiner Fähigkeit benötigt', 'external': 'Externe Systeme'},
}
EDGES_DIRECT_MAX = 12
SYNTH = 'arch'          # synthetic groups / lanes made here — removed and rebuilt on every layout


def _lang(p) -> str:
    return p.language if p.language in TIME_LABELS else 'en'


def _verb_is(label: str, *canonical: str) -> bool:
    """`label` is one of the canonical English verbs in any of the four languages."""
    import edgy_vocab
    low = (label or '').lower().strip()
    for c in canonical:
        if low == c or low in edgy_vocab.spellings(c):
            return True
    return False


def is_application(e: dict) -> bool:
    return e.get('type') == 'asset' and (e.get('kind') in APPLICATION_KINDS)


def reset(p) -> None:
    """Undo what an earlier layout of this page prepared (layout runs can repeat)."""
    restore_removed_groups(p)
    for gid in [g for g, grp in p.groups.items() if grp.get('synthetic') == SYNTH]:
        for m in p.groups[gid]['members']:
            p.elements[m]['group'] = p.elements[m].get('_arch_group')
        del p.groups[gid]
    for e in p.elements.values():
        if '_arch_group' in e:
            e['group'] = e.pop('_arch_group')
        if '_arch_stage' in e:
            e['stage'] = e.pop('_arch_stage')
        e.pop('chips', None)
        e.pop('count_note', None)
    if getattr(p, '_arch_stages', None) is not None:
        p.stages = p._arch_stages
        p._arch_stages = None
    for r in p.relationships:
        r.pop('suppressed', None)
    p._suppressed_note = None
    p._arch_layout = None


def prepare(p) -> None:
    """Called at the start of every layout (EDGYParser._calculate_layout)."""
    reset(p)
    apply_time_badges(p)
    if p.map_type == 'application':
        prepare_application(p)
    elif p.map_type == 'process':
        view = (p.view.get('process_view') or '').lower()
        if view == 'chain':
            prepare_chain(p)
        elif view == 'swimlane':
            prepare_swimlane(p)
        elif view:
            _once(p, f"process_view: {view} is not known (chain, swimlane) — the default sequence row is drawn")


def _once(p, msg: str, note: bool = False) -> None:
    target = p.notes if note else p.warnings
    if msg not in target:
        target.append(msg)


# ---- badges -------------------------------------------------------------------------------------------

def apply_time_badges(p) -> None:
    """{time: invest} → a lifecycle badge (Gartner TIME), localised; unknown values are reported."""
    for e in p.elements.values():
        raw = (e.get('attrs') or {}).get('time')
        if not raw:
            e.pop('time', None)
            continue
        key = TIME_SYNONYMS.get(str(raw).strip().lower())
        if key is None:
            _once(p, f"time '{raw}' on '{e['name']}' is not Gartner TIME (tolerate, invest, migrate, eliminate) — no badge")
            e.pop('time', None)
            continue
        e['time'] = key


def time_label(p, key: str) -> str:
    return TIME_LABELS[_lang(p)][key]


# ---- application map ------------------------------------------------------------------------------------

def _owner_ok(p, eid: str) -> bool:
    e = p.elements[eid]
    if (e.get('attrs') or {}).get('owner'):
        return True
    for r in p.relationships:
        if r['target'] == eid and _verb_is(r['label'], 'manages') and p.elements[r['source']]['type'] == 'organisation':
            return True
    graph = getattr(p, 'graph', None)
    if graph is not None:
        mid = p.model_id(e)[0]
        for g in graph.in_edges(mid):
            src = graph.get(g['source'])
            if src and src['type'] == 'organisation' and _verb_is(g['verb'], 'manages'):
                return True
    return False


def prepare_application(p) -> None:
    lang = _lang(p)
    apps = [eid for eid, e in p.elements.items() if is_application(e)]
    if not apps:
        _once(p, "application map: no asset has {kind: application | platform | integration} — nothing to group")
        return
    # owners (W124): a note by default; a warning when the document says ownership: required
    required = (p.view.get('ownership') or '').lower() == 'required'
    missing = [p.elements[a]['name'] for a in apps if not _owner_ok(p, a)]
    if missing:
        msg = (f"W124 {len(missing)} application(s) without an owner (manages from an organisation, or {{owner: …}}): "
               f"{', '.join(missing[:6])}{' …' if len(missing) > 6 else ''}")
        _once(p, msg, note=not required)
    integrations = [r for r in p.relationships
                    if _verb_is(r['label'], 'transfers') and r['source'] in p.elements and r['target'] in p.elements
                    and p.elements[r['source']]['type'] == 'asset' and p.elements[r['target']]['type'] == 'asset']
    no_data = [r for r in integrations if not (r.get('options') or {}).get('data')]
    if no_data:
        names = ', '.join(f"{p.elements[r['source']]['name']} → {p.elements[r['target']]['name']}" for r in no_data[:4])
        _once(p, f"W125 {len(no_data)} integration(s) without a data asset ({{data: …}}): {names}"
                 f"{' …' if len(no_data) > 4 else ''}")
    mode = (p.view.get('edges') or '').lower() or ('direct' if len(integrations) <= EDGES_DIRECT_MAX else 'none')
    if mode not in ('direct', 'none'):
        _once(p, f"edges: {mode} is not known (direct, none) — direct")
        mode = 'direct'
    if mode == 'none' and integrations:
        counts: Dict[str, int] = {}
        for r in integrations:
            r['suppressed'] = True
            for x in (r['source'], r['target']):
                counts[x] = counts.get(x, 0) + 1
        for x, n in counts.items():
            p.elements[x]['count_note'] = f"↔ {n}"
        if not p.view.get('edges'):
            _once(p, f"application map: {len(integrations)} integrations — not drawn (edges: none above "
                     f"{EDGES_DIRECT_MAX}); each card counts its integrations, the presenter shows them on hover; "
                     f"edges: direct draws them", note=True)
    group_by = (p.view.get('group_by') or '').lower()
    if p.rows and any(g['kind'] == 'group' and not g.get('synthetic') for g in p.groups.values()):
        if group_by == 'capability':
            _once(p, "application map: group_by: capability with domains × layers (groups and rows:) — the domains win")
        _fold_data_and_owners(p, apps, lang)
        _domains_as_columns(p, apps, lang)
        return
    if group_by == 'capability':
        _group_by_capability(p, apps, lang)
    elif group_by and group_by != 'domain':
        _once(p, f"group_by: {group_by} is not known (domain, capability) — the input's groups are used")
    _fold_data_and_owners(p, apps, lang)
    _external_column(p, apps, lang)


OWNER_WORD = {'en': 'owner', 'fi': 'omistaja', 'fr': 'responsable', 'de': 'verantwortlich'}


def _fold_data_and_owners(p, apps: List[str], lang: str) -> None:
    """Data assets are named on the integration labels, owners on the cards: neither is drawn as a box
    on the application map (both stay in the document graph, so the presenter still shows them)."""
    data = [eid for eid, e in p.elements.items() if e['type'] == 'asset' and e.get('kind') == 'data'
            and e.get('group') is None]
    for d in data:
        p._hidden.add(d)
    if data:
        _once(p, f"application map: {len(data)} data asset(s) shown on the integration labels, not as cards", note=True)
    app_set = set(apps)
    folded = 0
    for oid, o in p.elements.items():
        if o['type'] != 'organisation' or o.get('group') is not None:
            continue
        rels = [r for r in p.relationships if oid in (r['source'], r['target'])
                and not ({r['source'], r['target']} - {oid}) <= p._hidden]   # links to hidden elements do not count
        if rels and all(r['source'] == oid and r['target'] in app_set and _verb_is(r['label'], 'manages') for r in rels):
            for r in rels:
                r['suppressed'] = True
                e = p.elements[r['target']]
                e['count_note'] = (e.get('count_note', '') + f" {OWNER_WORD[lang]}: {o['name']}").strip()
            p._hidden.add(oid)
            folded += 1
    if folded:
        _once(p, f"application map: {folded} owner organisation(s) named on their applications' cards, not drawn",
              note=True)


def _requiring_capabilities(p, app: str) -> List[Tuple[str, bool]]:
    """[(capability element id, primary?)] of the capabilities on the page that require `app`."""
    out = []
    for r in p.relationships:
        if r['target'] == app and p.elements[r['source']]['type'] == 'capability' and _verb_is(r['label'], 'requires'):
            out.append((r['source'], bool((r.get('options') or {}).get('primary'))))
    return out


def _area_of_capability(p, cap: str) -> str:
    g = p.elements[cap].get('group')
    while g is not None and p.groups[g].get('parent') is not None:
        g = p.groups[g]['parent']
    return p.groups[g]['name'] if g is not None else p.elements[cap]['name']


def _group_by_capability(p, apps: List[str], lang: str) -> None:
    labels = AREA_LABELS[lang]
    areas: Dict[str, List[str]] = {}
    order: List[str] = []
    hidden_caps = set()
    shown = 0
    for a in apps:
        if p.elements[a].get('group') is not None:
            continue                                      # an explicit group: wins
        caps = _requiring_capabilities(p, a)
        hidden_caps.update(c for c, _ in caps)
        primaries = [c for c, prim in caps if prim]
        if len(primaries) > 1:
            _once(p, f"'{p.elements[a]['name']}' has {len(primaries)} requires links marked primary — Shared strip")
        if len(primaries) == 1:
            area = _area_of_capability(p, primaries[0])
            others = {_area_of_capability(p, c) for c, _ in caps} - {area}
            if others:
                p.elements[a]['count_note'] = (p.elements[a].get('count_note', '') + f" +{len(others)} area(s)").strip()
        elif len({_area_of_capability(p, c) for c, _ in caps}) == 1:
            area = _area_of_capability(p, caps[0][0])
        elif caps:
            area = labels['shared']
        else:
            area = labels['none']
        if area not in areas:
            areas[area] = []
            order.append(area)
        areas[area].append(a)
        shown += len(caps)
    # Shared and "not required" last, in that order; areas otherwise in first-seen order of the input
    tail = [labels['shared'], labels['none']]
    order = [x for x in order if x not in tail] + [x for x in tail if x in areas]
    for n, area in enumerate(order, 1):
        gid = f"arch_area_{n}"
        _make_group(p, gid, area, areas[area])
    for c in hidden_caps:
        p._hidden.add(c)
    # the input's capability groups were the source of the areas: drawn empty they would only repeat them
    removed = {}
    for gid, g in list(p.groups.items()):
        if g.get('synthetic') or g['kind'] != 'group':
            continue
        members = _all_members(p, gid)
        if members and all(m in p._hidden for m in members):
            removed[gid] = g
    for gid in removed:
        del p.groups[gid]
    if removed:
        p._arch_removed_groups = {**(getattr(p, '_arch_removed_groups', None) or {}), **removed}
    if hidden_caps:
        _once(p, f"application map: grouped by capability — {len(hidden_caps)} capability(ies) shown as areas, "
                 f"{shown} requires link(s) shown by membership instead of edges", note=True)
    if labels['shared'] in areas:
        _once(p, f"application map: {len(areas[labels['shared']])} application(s) required by several areas without "
                 f"a {{primary: true}} requires link — placed in the {labels['shared']} strip", note=True)


def _all_members(p, gid: str) -> List[str]:
    g = p.groups[gid]
    out = list(g['members'])
    for sg in g.get('subgroups') or []:
        if sg in p.groups:
            out.extend(_all_members(p, sg))
    return out


def _make_group(p, gid: str, name: str, members: List[str], kind: str = 'group') -> None:
    p.groups[gid] = {'id': gid, 'kind': kind, 'name': name, 'members': list(members), 'tags': [], 'metrics': {},
                     'synthetic': SYNTH, 'parent': None, 'subgroups': []}
    for m in members:
        p.elements[m]['_arch_group'] = p.elements[m].get('group')
        p.elements[m]['group'] = gid


def _external_column(p, apps: List[str], lang: str) -> None:
    ext = [a for a in apps if 'external' in [t.lower() for t in p.elements[a].get('tags', [])]
           and p.elements[a].get('group') is None]
    if ext and any(g['kind'] == 'group' for g in p.groups.values()):
        _make_group(p, 'arch_external', AREA_LABELS[lang]['external'], ext)


def _domains_as_columns(p, apps: List[str], lang: str) -> None:
    """Domains (input groups) × layers (rows:): the groups become the matrix columns; [external]
    applications outside the groups get their own last column."""
    groups = [g for g in p.groups.values() if g['kind'] == 'group' and g.get('parent') is None]
    if any(g.get('subgroups') for g in groups):
        _once(p, "application map: nested domains with rows: — the rows are ignored (domains × layers needs one level)")
        return
    p._arch_stages = list(p.stages)
    p.stages = [g['name'] for g in groups]
    ext = [a for a in apps if 'external' in [t.lower() for t in p.elements[a].get('tags', [])]
           and p.elements[a].get('group') is None]
    if ext:
        p.stages.append(AREA_LABELS[lang]['external'])
        for a in ext:
            e = p.elements[a]
            e['_arch_stage'] = e.get('stage')
            e['stage'] = e.get('stage') or AREA_LABELS[lang]['external']
    for g in groups:
        for m in g['members']:
            e = p.elements[m]
            e['_arch_stage'] = e.get('stage')
            e['stage'] = e.get('stage') or g['name']
            e['_arch_group'] = e.get('group')
            e['group'] = None
    # the input groups are removed for this layout and restored by reset()
    p._arch_removed_groups = {g['id']: g for g in groups}
    for g in groups:
        del p.groups[g['id']]


def restore_removed_groups(p) -> None:
    for gid, g in (getattr(p, '_arch_removed_groups', None) or {}).items():
        p.groups[gid] = g
    p._arch_removed_groups = None


# ---- process chain --------------------------------------------------------------------------------------

def _process_tree(p) -> Tuple[List[str], Dict[str, List[str]]]:
    procs = [eid for eid, e in p.elements.items() if e['type'] == 'process']
    children: Dict[str, List[str]] = {}
    has_parent = set()
    for r in p.relationships:
        if r['source'] in procs and r['target'] in procs and r.get('kind') == 'tree':
            children.setdefault(r['source'], []).append(r['target'])
            has_parent.add(r['target'])
            r['suppressed'] = True
    roots = [x for x in procs if x not in has_parent]
    return roots, children


def prepare_chain(p) -> None:
    roots, children = _process_tree(p)
    if not roots:
        _once(p, "process_view: chain — no process on the page")
        return
    banded = any((p.elements[r].get('attrs') or {}).get('band') for r in roots)
    if banded:
        for r in roots:
            band = ((p.elements[r].get('attrs') or {}).get('band') or '').lower()
            if band not in BAND_ORDER:
                _once(p, f"W126 L1 process '{p.elements[r]['name']}' has no band (management, core, support) on a banded chain"
                         if not band else f"W126 band '{band}' on '{p.elements[r]['name']}' is not management, core or support")
            for c in children.get(r, []):
                cb = ((p.elements[c].get('attrs') or {}).get('band') or '').lower()
                if cb and cb != band:
                    _once(p, f"W126 L2 process '{p.elements[c]['name']}' has band '{cb}' but its L1 "
                             f"'{p.elements[r]['name']}' is '{band or 'none'}'")
    n = sum(1 for r in p.relationships if r.get('suppressed'))
    if n:
        _once(p, f"process chain: {n} contains link(s) shown by position (L2 under its L1), not as edges", note=True)
    p._arch_layout = ('chain', roots, children, banded)


def layout_chain(p, items: List[str]) -> Dict[str, Tuple[int, int]]:
    """L1 row(s) of pentagons, L2 (and L3 with depth: 3) stacked under each L1; bands as rows with a header."""
    _, roots, children, banded = p._arch_layout
    depth = 3 if str(p.view.get('depth') or '').strip() == '3' else 2
    sizes = {i: p._size_of(i) for i in items}
    positions: Dict[str, Tuple[int, int]] = {}
    import math
    col_w = int(math.ceil(max([sizes[r][0] for r in roots if r in sizes] + [180]) / 10) * 10)
    GAP_X, GAP_Y, ROW_GAP = 30, 20, 60          # ≥ 20 px: the collision sweep never moves a card
    x0, y = 60, 60
    p._left_reserve = 180 if banded else 0
    p._chain_headers = []
    rows: List[Tuple[Optional[str], List[str]]] = []
    if banded:
        for band in BAND_ORDER:
            members = [r for r in roots if ((p.elements[r].get('attrs') or {}).get('band') or '').lower() == band]
            if members:
                rows.append((band, members))
        rest = [r for r in roots if ((p.elements[r].get('attrs') or {}).get('band') or '').lower() not in BAND_ORDER]
        if rest:
            rows.append((None, rest))
    else:
        rows.append((None, roots))
    placed = set()
    for band, members in rows:
        x = x0
        row_bottom = y
        for r in members:
            if r not in sizes:
                continue
            positions[r] = (x, y)
            placed.add(r)
            cy = y + sizes[r][1] + 30
            stack = list(children.get(r, []))
            level = {c: 2 for c in stack}
            k = 0
            while k < len(stack):
                c = stack[k]
                k += 1
                if c not in sizes or c in placed:
                    continue
                indent = 16 if level[c] == 3 else 0
                positions[c] = (x + indent, cy)
                placed.add(c)
                cy += sizes[c][1] + GAP_Y
                if level[c] < depth:
                    for gc in children.get(c, []):
                        level[gc] = level[c] + 1
                        stack.insert(k, gc)
            row_bottom = max(row_bottom, cy)
            x += col_w + GAP_X
        if band and members:
            # anchored to the band's first L1 process: the canvas normalisation moves both together
            p._chain_headers.append((BAND_LABELS[_lang(p)][band], members[0], -180, 150))
        y = row_bottom + ROW_GAP
    rest = [i for i in items if i not in placed]
    hidden_deep = [i for i in rest if p.elements.get(i, {}).get('type') == 'process']
    if hidden_deep and depth == 2:
        for i in hidden_deep:
            p._hidden.add(i)
        _once(p, f"process chain: {len(hidden_deep)} L3 process(es) not drawn — depth: 3 shows them", note=True)
        rest = [i for i in rest if i not in hidden_deep]
    x = 60
    for i in rest:
        positions[i] = (x, y)
        x += sizes[i][0] + 40
    p._layout_handles_tree = True
    return positions


# ---- swimlane ----------------------------------------------------------------------------------------------

def prepare_swimlane(p) -> None:
    procs = [eid for eid, e in p.elements.items() if e['type'] == 'process' and e.get('group') is None]
    if not procs:
        _once(p, "process_view: swimlane — no process on the page")
        return
    # a decomposition on the page: the steps are the leaves; the parents are not steps of the flow
    parents = {r['source'] for r in p.relationships
               if r['source'] in procs and r['target'] in procs and r.get('kind') == 'tree'}
    if parents:
        for r in p.relationships:
            if r['source'] in parents and r['target'] in procs and r.get('kind') == 'tree':
                r['suppressed'] = True
        for x in parents:
            p._hidden.add(x)
        procs = [x for x in procs if x not in parents]
        _once(p, f"swimlane: {len(parents)} parent process(es) not drawn — the steps are the leaves of the "
                 f"decomposition (process_view: chain shows it)", note=True)
    actors = [eid for eid, e in p.elements.items() if e['type'] in ('organisation', 'people')]
    performer: Dict[str, str] = {}
    for r in p.relationships:
        if r['source'] in actors and r['target'] in procs and _verb_is(r['label'], 'performs'):
            performer.setdefault(r['target'], r['source'])
            r['suppressed'] = True
    lanes: Dict[str, List[str]] = {}
    order: List[str] = []
    for pr in procs:
        a = performer.get(pr)
        key = a or '_none'
        if key not in lanes:
            lanes[key] = []
            order.append(key)
        lanes[key].append(pr)
    # lane order: actors in input order, steps without a performer last
    order = [a for a in actors if a in lanes] + (['_none'] if '_none' in lanes else [])
    p._arch_stages = list(p.stages)
    p.stages = [p.elements[pr]['name'] for pr in procs]
    for pr in procs:
        e = p.elements[pr]
        e['_arch_stage'] = e.get('stage')
        e['stage'] = e['name']
    lang = _lang(p)
    unassigned = {'en': 'No performer', 'fi': 'Ei suorittajaa', 'fr': 'Sans exécutant', 'de': 'Ohne Ausführende'}[lang]
    for n, key in enumerate(order, 1):
        name = p.elements[key]['name'] if key != '_none' else unassigned
        _make_group(p, f"arch_lane_{n}", name, lanes[key], kind='lane')
        if key != '_none':
            p._hidden.add(key)
    p._no_stage_headers = True
    if performer:
        _once(p, f"swimlane: {len(set(performer.values()))} actor(s) drawn as lanes, {len(performer)} performs link(s) "
                 f"shown by lane membership", note=True)
    if '_none' in lanes:
        _once(p, f"swimlane: {len(lanes['_none'])} step(s) have no performer (organisation or people → performs)")
    # chips: the assets a step requires, as a line under the step; the assets themselves are not drawn
    if (p.view.get('chips') or 'assets').lower() != 'none':
        chipped = set()
        for r in p.relationships:
            if r['source'] in procs and p.elements[r['target']]['type'] == 'asset' and _verb_is(r['label'], 'requires'):
                p.elements[r['source']].setdefault('chips', []).append(p.elements[r['target']]['name'])
                r['suppressed'] = True
                chipped.add(r['target'])
        only_chips = [a for a in chipped if not any(
            (r['source'] == a or r['target'] == a) and not r.get('suppressed') for r in p.relationships)]
        for a in only_chips:
            p._hidden.add(a)
        if chipped:
            _once(p, f"swimlane: {len(chipped)} asset(s) shown as chips under the steps that require them", note=True)
