#!/usr/bin/env python3
"""
edgy_graph.py — the document graph: one model over every page of an input.

Each page of a (multi-page) TXT input is still parsed by its own EDGYParser
(own layout, own legend). This module adds what no single page can know:

  * one **model element per model id** (`{id: CAP-05}`) with every place it is
    drawn (its *occurrences*: page + element);
  * the relationships of the whole document, including the ones between
    elements that sit on different pages;
  * the identity rules of extension contract 1:

      E014  the same id with a conflicting type or name on two pages
            (a duplicate id on one page is caught by the parser, same code)
      E015  a relationship whose endpoint is on no page (dangling)

    An element without `{id:}` gets a slug id (type + name, `edgyIdSource=slug`).
    Slug ids are fine on a standalone page but never connect views: a derived
    view (capability view, application map from the model, …) requires
    explicit ids, and `require_explicit()` says which are missing.

  * **page expansion**: `expand: per-capability` / `per-application` turns one
    view page into one page per model element (`where: highlight` or a list of
    ids narrows it).

Standard library only. The graph is serialised by `to_json()` in the shape of
`assets/edgy-graph.schema.json` (extension contract, references/extension-contract.md).
"""

import re
from typing import Dict, Iterable, List, Optional, Tuple

GRAPH_CONTRACT = 1

# expand: per-<x> → the element type / asset kind that gets one page each
EXPAND_TARGETS = {
    'per-capability': ('capability', None),
    'per-application': ('asset', 'application'),
    'per-process': ('process', None),
}


class DocumentGraph:
    def __init__(self):
        self.nodes: Dict[str, dict] = {}          # model id → node
        self.edges: List[dict] = []               # {source, target, verb, kind, options, page}
        self.order: List[str] = []                # model ids in first-seen order
        self._by_name: Dict[Tuple[str, str], List[str]] = {}

    # ---- lookup -----------------------------------------------------------
    def get(self, mid: str) -> Optional[dict]:
        if mid in self.nodes:
            return self.nodes[mid]
        low = (mid or '').lower()
        for k, n in self.nodes.items():
            if k.lower() == low:
                return n
        return None

    def resolve(self, text: str) -> Optional[str]:
        """Model id for an endpoint written as an id or as a (unique) name."""
        node = self.get(text)
        if node:
            return node['id']
        low = (text or '').lower().strip()
        hits = [mid for mid, n in self.nodes.items()
                if n['value'].lower() == low or n['name'].lower() == low]
        return hits[0] if len(hits) == 1 else None

    def of_type(self, element_type: str, kind: Optional[str] = None) -> List[dict]:
        return [self.nodes[m] for m in self.order
                if self.nodes[m]['type'] == element_type and (kind is None or self.nodes[m].get('kind') == kind)]

    def out_edges(self, mid: str, verbs: Iterable[str] = None) -> List[dict]:
        vs = {v.lower() for v in verbs} if verbs else None
        return [e for e in self.edges if e['source'] == mid and (vs is None or e['verb'] in vs)]

    def in_edges(self, mid: str, verbs: Iterable[str] = None) -> List[dict]:
        vs = {v.lower() for v in verbs} if verbs else None
        return [e for e in self.edges if e['target'] == mid and (vs is None or e['verb'] in vs)]

    def add_page(self, name: str, parser) -> None:
        """Occurrences of a page drawn from the graph (derived view, expanded page): its elements are
        model elements already — no identity checks, only where they are drawn."""
        for eid, e in parser.elements.items():
            node = self.get(parser.model_id(e)[0])
            if node is not None and not any(pr is parser and x == eid for _n, pr, x in node['occurrences']):
                node['occurrences'].append((name, parser, eid))

    def require_explicit(self, mids: Iterable[str]) -> List[str]:
        """Model ids that are slugs — a derived view cannot use them for cross-view identity."""
        return [m for m in mids if m in self.nodes and not self.nodes[m]['explicit']]

    # ---- serialisation ----------------------------------------------------
    def to_json(self) -> dict:
        return {
            'contract': GRAPH_CONTRACT,
            'elements': [{
                'id': n['id'], 'id_source': 'explicit' if n['explicit'] else 'slug',
                'type': n['type'], 'name': n['name'], 'description': n['subtext'] or None,
                'kind': n.get('kind'), 'attributes': dict(n.get('attrs') or {}),
                'change': n.get('change'), 'tags': list(n.get('tags') or []),
                'occurrences': [{'page': p, 'page_id': pr.page_id, 'cell': pr.cell_of.get(eid)}
                                for p, pr, eid in n['occurrences']
                                if pr.page_id and pr.draw and (not pr.cell_of or eid in pr.cell_of)],   # drawn only
            } for n in (self.nodes[m] for m in self.order)],
            'relationships': [{
                'source': e['source'], 'target': e['target'], 'verb': e['verb'], 'kind': e['kind'],
                'attributes': {k: v for k, v in e['options'].items() if k in ('crud', 'data', 'technology',
                                                                               'container', 'primary', 'change')},
                'page': e['page'],
            } for e in self.edges],
        }


def _node_from(parser, eid: str) -> Tuple[str, bool, dict]:
    e = parser.elements[eid]
    mid, explicit = parser.model_id(e)
    return mid, explicit, e


def build_graph(pages) -> DocumentGraph:
    """Build the graph over `pages` = [(page_name, parser)] and write E014 / E015 into the
    pages' parsers (warnings + errors, like every other input error). Each parser gets
    `parser.graph`; relationships across pages are added to the graph, not drawn."""
    g = DocumentGraph()
    for name, parser in pages:
        parser.graph = g
        for eid, e in parser.elements.items():
            if e['type'] in ('group', 'lane'):
                continue
            mid, explicit, _ = _node_from(parser, eid)
            node = g.nodes.get(mid)
            if node is None:
                g.nodes[mid] = {
                    'id': mid, 'explicit': explicit, 'type': e['type'], 'name': e.get('name') or e['value'],
                    'value': e['value'], 'subtext': e.get('subtext') or '', 'kind': e.get('kind'),
                    'attrs': dict(e.get('attrs') or {}), 'metrics': dict(e.get('metrics') or {}),
                    'tags': list(e.get('tags') or []), 'change': e.get('change'),
                    'maturity': e.get('maturity'), 'rating': e.get('rating'),
                    'highlight': bool(e.get('highlight')),
                    'occurrences': [(name, parser, eid)],
                }
                g.order.append(mid)
                continue
            if explicit and (node['type'] != e['type'] or
                             node['name'].lower() != (e.get('name') or e['value']).lower()):
                msg = (f"E014 id '{mid}' is {e['type']} '{e.get('name') or e['value']}' here but "
                       f"{node['type']} '{node['name']}' on page '{node['occurrences'][0][0]}' — one id, one element; "
                       f"a rename keeps the id on every page")
                parser.warnings.append(msg)
                parser.errors.append(msg)
                continue
            node['occurrences'].append((name, parser, eid))
            node['highlight'] = node['highlight'] or bool(e.get('highlight'))
            # attributes written on a later occurrence complete the model element (first value wins)
            for k, v in (e.get('attrs') or {}).items():
                node['attrs'].setdefault(k, v)
            if not node.get('kind') and e.get('kind'):
                node['kind'] = e['kind']
    seen = set()
    for name, parser in pages:
        for rel in parser.relationships:
            s = parser.elements.get(rel['source'])
            t = parser.elements.get(rel['target'])
            if not s or not t:
                continue
            sm, tm = parser.model_id(s)[0], parser.model_id(t)[0]
            key = (sm, tm, rel['label'].lower())
            if key in seen:
                continue
            seen.add(key)
            g.edges.append({'source': sm, 'target': tm, 'verb': rel['label'].lower().strip(),
                            'kind': rel.get('kind'), 'options': dict(rel.get('options') or {}), 'page': name})
    for name, parser in pages:
        for src, tgt, label, options in parser.dangling:
            sm, tm = g.resolve(src), g.resolve(tgt)
            if sm and tm:
                key = (sm, tm, label.lower())
                if key not in seen:
                    seen.add(key)
                    g.edges.append({'source': sm, 'target': tm, 'verb': label.lower().strip(),
                                    'kind': None, 'options': dict(options or {}), 'page': name})
                continue
            missing = ' and '.join(f"'{x}'" for x, m in ((src, sm), (tgt, tm)) if not m)
            msg = (f"E015 relationship \"{src}\" -> \"{tgt}\": \"{label}\" — {missing} is on no page of the document "
                   f"(dangling); add the element, or fix the name / id")
            parser.warnings.append(msg)
            parser.errors.append(msg)
    return g


# ---- page expansion -----------------------------------------------------------

EXPAND_RE = re.compile(r'^[ \t]*expand:\s*(\S+)\s*$', re.M)
WHERE_RE = re.compile(r'^[ \t]*where:\s*(.+?)\s*$', re.M)


def expansion_of(page_text: str) -> Optional[Tuple[str, Optional[str]]]:
    m = EXPAND_RE.search(page_text or '')
    if not m:
        return None
    w = WHERE_RE.search(page_text)
    return m.group(1).strip().lower(), (w.group(1).strip() if w else None)


def expand_targets(graph: DocumentGraph, mode: str, where: Optional[str]) -> Tuple[List[dict], List[str]]:
    """(nodes that get a page, problems). `where: highlight` keeps highlighted elements, `where: top` the tops of
    the contains hierarchy (L1 processes), `where: A, B` a list of ids."""
    problems: List[str] = []
    if mode not in EXPAND_TARGETS:
        return [], [f"expand: {mode} is not known (known: {', '.join(EXPAND_TARGETS)})"]
    etype, kind = EXPAND_TARGETS[mode]
    nodes = graph.of_type(etype, kind)
    if where:
        if where.lower() == 'highlight':
            nodes = [n for n in nodes if _highlighted(graph, n)]
        elif where.lower() == 'top':
            # the top of each hierarchy: not contained by another element of the same type (L1 processes)
            inner = {e['target'] for e in graph.edges if e['verb'] == 'contains'
                     and (graph.get(e['source']) or {}).get('type') == etype}
            nodes = [n for n in nodes if n['id'] not in inner]
        else:
            ids = [x.strip() for x in where.split(',') if x.strip()]
            wanted = {i.lower() for i in ids}
            known = {n['id'].lower() for n in nodes}
            for i in ids:
                if i.lower() not in known:
                    problems.append(f"expand: where: {i} is not a {kind or etype} id of this document")
            nodes = [n for n in nodes if n['id'].lower() in wanted]
    slugs = [n['id'] for n in nodes if not n['explicit']]
    if slugs:
        problems.append(f"expand: {mode} needs explicit ids — {', '.join(slugs[:6])}"
                        f"{' …' if len(slugs) > 6 else ''} have none (write {{id: …}} on the element)")
        nodes = [n for n in nodes if n['explicit']]
    if not nodes:
        problems.append(f"expand: {mode} found no {kind or etype} with an explicit id in the document")
    return nodes, problems


def _highlighted(graph: DocumentGraph, node: dict) -> bool:
    return bool(node.get('highlight'))
