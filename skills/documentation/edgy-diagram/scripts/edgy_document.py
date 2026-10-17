#!/usr/bin/env python3
"""
edgy_document.py — Multi-page EDGY input and the draw.io `mxfile` wrapper.

Input format (everything before `pages:` applies to every page):

    facet: architecture          # optional document-level defaults
    pages:
      - name: "Roles and actors"
        elements:
          - organisation: "Board"
        relationships:
          - ...
      - name: "Responsibility matrix"
        map_type: organisation
        elements:
          - ...

A file without `pages:` is a single page whose name defaults to the map type
or facet. Each page is parsed by its own EDGYParser (own layout, own legend)
and becomes one <diagram> in an uncompressed <mxfile>, which is what draw.io
desktop, draw.io online and most wiki plugins expect.
"""

import re
import textwrap
import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple

from edgy_parser import EDGYParser

PAGE_RE = re.compile(r'^\s*-\s*name:\s*"(.+?)"\s*$')
PAGES_RE = re.compile(r'^pages:\s*$')
_SLUG_RE = re.compile(r'[^a-z0-9]+')


def slugify(name: str) -> str:
    s = _SLUG_RE.sub('-', name.lower()).strip('-')
    return s or 'page'


def unique_slugs(names: List[str], reserved=()) -> List[str]:
    """Deterministic, collision-free slugs for page names.

    Each name is slugified; if the slug is already taken (by an earlier page
    *or* by an earlier generated suffix such as `foo-2`), the lowest free
    `-N` suffix is used. Used for draw.io page ids and for per-page output
    file names, so neither can collide.
    """
    used = set(reserved)
    out = []
    for name in names:
        base = slugify(name)
        candidate, n = base, 2
        while candidate in used:
            candidate = f'{base}-{n}'
            n += 1
        used.add(candidate)
        out.append(candidate)
    return out


def split_pages(text: str) -> List[Tuple[str, str]]:
    """Return [(page_name, page_text)] — one entry for a single-page input."""
    lines = text.split('\n')
    head: List[str] = []
    pages: List[Tuple[str, List[str]]] = []
    in_pages = False
    for line in lines:
        if not in_pages:
            if PAGES_RE.match(line):
                in_pages = True
                continue
            head.append(line)
            continue
        m = PAGE_RE.match(line)
        if m:
            pages.append((m.group(1), []))
            continue
        if pages:
            pages[-1][1].append(line)
        elif line.strip() and not line.strip().startswith('#'):
            raise ValueError(f"content under 'pages:' must start with '- name: \"...\"', got: {line.strip()!r}")
    if not in_pages:
        return [(None, text)]
    if not pages:
        raise ValueError("'pages:' given but no '- name: \"...\"' entries follow")
    head_text = '\n'.join(head)
    return [(name, head_text + '\n' + '\n'.join(body)) for name, body in pages]


def default_page_name(parser: EDGYParser) -> str:
    base = parser.map_type or parser.facet or 'edgy'
    return 'edgy' if base == 'all' else base


def parse_document(text: str, with_graph: bool = False):
    """Parse a (possibly multi-page) input into [(page_name, parser)] — the pages to draw.

    Every page is parsed by its own EDGYParser; then one document graph is built over all
    of them (edgy_graph: model ids, occurrences, cross-page relationships, E014 / E015).
    `draw: false` pages are model pages: in the graph, not in the result. A page with
    `expand: per-capability | per-application | per-process` is a template: it becomes one
    page per matching model element (with `focus: <id>`), named "<page> · <id> <name>".
    Derived views (edgy_views) are filled from the graph after it is built. Every drawn
    parser gets its draw.io page id (`parser.page_id`, the same slug build_mxfile writes),
    the page half of `edgyOcc`. `with_graph=True` returns (pages, graph)."""
    import edgy_graph
    import edgy_views
    parsed: List[Tuple[str, EDGYParser, str]] = []
    templates: List[Tuple[int, str, str]] = []
    for idx, (name, page_text) in enumerate(split_pages(text)):
        if edgy_graph.expansion_of(page_text):
            templates.append((idx, name, page_text))
            parsed.append((name, None, page_text))
            continue
        parser = EDGYParser()
        # a notation: page keeps only its header keys here: its body is the handler's, never EDGY elements in the
        # document graph (no containers, C4 edges, E014 on a repeated id, vocabulary warnings) — F4-core, 2.9.0
        parser.parse_input(header_only(page_text) if notation_of(page_text) else page_text)
        parsed.append((name or default_page_name(parser), parser, page_text))
    graph = edgy_graph.build_graph([(n, p) for n, p, _ in parsed if p is not None])
    prepass_errors = notation_prepass([(n, t) for n, _p, t in parsed if notation_of(t)], graph)
    result: List[Tuple[str, EDGYParser]] = []
    for name, parser, page_text in parsed:
        if parser is not None and parser.notation:
            attach_notation(parser, page_text, graph, name)
        if parser is not None:
            if edgy_views.is_derived(parser):
                edgy_views.materialize(parser, graph)
                graph.add_page(name or default_page_name(parser), parser)
            if parser.draw:
                result.append((name, parser))
            continue
        mode, where = edgy_graph.expansion_of(page_text)
        if notation_of(page_text):
            result.extend(_expand_notation(name or 'view', page_text, mode, where, graph))
            continue
        if mode == 'trace':
            result.extend(_expand_trace(name or 'Trace', page_text, where, graph))
            continue
        nodes, problems = edgy_graph.expand_targets(graph, mode, where)
        base = name or 'view'
        stripped = edgy_graph.EXPAND_RE.sub('', edgy_graph.WHERE_RE.sub('', page_text))
        for node in nodes:
            p = EDGYParser()
            p.graph = graph
            p.parse_input(f"focus: {node['id']}\n" + stripped)
            if edgy_views.is_derived(p):
                edgy_views.materialize(p, graph)
            page_name = f"{base} · {node['id']} {node['name']}"
            graph.add_page(page_name, p)
            result.append((page_name, p))
        if problems:
            holder = result[-1][1] if result else (parsed[0][1] or EDGYParser())
            for msg in problems:
                holder.warnings.append(msg)
                holder.errors.append(msg)
            if not result:
                result.append((base, holder))
    for page, finding in prepass_errors:
        holder = next((p for n, p in result if n == page), result[0][1] if result else None)
        if holder is not None:
            _apply_finding(holder, finding)
    # fixed ids first (realisation trace: trace-<id>, notation pages: their handler's page_id), then the slugs of
    # the other pages around them
    fixed = {p.fixed_page_id for _, p in result if getattr(p, 'fixed_page_id', None)}
    rest = [(n, p) for n, p in result if not getattr(p, 'fixed_page_id', None)]
    for (_, parser), slug in zip(rest, unique_slugs([n for n, _ in rest], reserved=fixed)):
        parser.page_id = slug
    for _, parser in result:
        if getattr(parser, 'fixed_page_id', None):
            parser.page_id = parser.fixed_page_id
    if not result:
        raise ValueError("no page to draw — every page has draw: false")
    return (result, graph) if with_graph else result


TRACE_DIRECTION_RE = re.compile(r'^[ \t]*trace_direction:\s*(\S+)\s*$', re.M)


def _expand_trace(base: str, page_text: str, where, graph) -> List[Tuple[str, EDGYParser]]:
    """expand: trace — the index page, one page per element of the page set, and a list page for every band with
    more than MAX_BAND cards (edgy_trace). Ids are fixed (trace-<id>); cards link only to pages in the document."""
    import edgy_graph
    import edgy_trace
    import edgy_views
    m = TRACE_DIRECTION_RE.search(page_text)
    direction = (m.group(1).lower() if m else 'both')
    stripped = edgy_graph.EXPAND_RE.sub('', edgy_graph.WHERE_RE.sub('', page_text))
    nodes, notes, problems = edgy_trace.page_set(graph, where, direction)
    ids = {n['id'] for n in nodes}
    lists = {}
    for n in nodes:
        nbs = edgy_trace.neighbours(graph, n['id'])
        for band in ('above', 'centre', 'below'):
            if direction == 'down' and band == 'above' or direction == 'up' and band == 'below':
                continue
            if sum(1 for x in nbs if x['band'] == band) > edgy_trace.MAX_BAND:
                lists.setdefault(n['id'], []).append(band)
    list_ids = {edgy_trace.list_page_id(mid, b) for mid, bands in lists.items() for b in bands}

    def page(prefix: str, fixed: str) -> EDGYParser:
        p = EDGYParser()
        p.graph = graph
        p.parse_input(prefix + stripped)
        p.trace_pages = ids | list_ids
        p.fixed_page_id = fixed
        edgy_views.materialize(p, graph)
        return p

    out: List[Tuple[str, EDGYParser]] = []
    index = page("trace_index: yes\n", edgy_trace.INDEX_PAGE_ID)
    out.append((f"{base} · index", index))
    for n in nodes:
        p = page(f"focus: {n['id']}\n", edgy_trace.page_id(n['id']))
        name = f"{base} · {n['id']} {n['name']}"
        graph.add_page(name, p)
        out.append((name, p))
        for band in lists.get(n['id'], []):
            lp = page(f"focus: {n['id']}\ntrace_list: {band}\n", edgy_trace.list_page_id(n['id'], band))
            out.append((f"{name} · {band}", lp))
    total = len(nodes)
    index.notes.append(f"trace: {total} trace page(s) for {total} element(s), plus the index"
                       f"{f' and {len(list_ids)} list page(s)' if list_ids else ''}")
    if total > edgy_trace.SOFT_CAP_PAGES:
        index.notes.append(f"trace: {total} pages — consider a narrower where: (ids, highlight, from <id>)")
    index.notes.extend(notes)
    for cyc in edgy_trace.contains_cycles(graph):
        index.warnings.append("trace: contains cycle " + " → ".join(cyc) + " — a hierarchy cannot contain itself; "
                              "the chips show it once, never followed")
    for msg in problems:
        index.warnings.append(msg)
        index.errors.append(msg)
    return out


def load_graph(text: str):
    """The document graph of an input (extension contract 1, entry point)."""
    return parse_document(text, with_graph=True)[1]


NOTATION_RE = re.compile(r'^notation:\s*([A-Za-z0-9-]+)\s*$', re.M)
_HEADER_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(\S.*)$')


def notation_of(page_text: str) -> Optional[str]:
    m = NOTATION_RE.search(textwrap.dedent(page_text or ''))
    return m.group(1).lower() if m else None


def header_only(page_text: str) -> str:
    """The `key: value` lines at the page's own indent (notation, level, system, focus, title, language …): what
    the EDGY parser may see of a notation page. Sections (`elements:`, `containers:`) and their bodies stay out."""
    return '\n'.join(ln for ln in textwrap.dedent(page_text or '').split('\n') if _HEADER_RE.match(ln))


def _apply_finding(parser: EDGYParser, finding) -> None:
    """A handler finding (severity, rule, message, subject[, page]) as a warning, note or error of the page."""
    sev, rule, msg, subject = (list(finding) + [None] * 4)[:4]
    text = f"{rule} {msg}" + (f" ({subject})" if subject not in (None, '') else '')
    sev = str(sev or '').lower()
    if sev == 'error':
        parser.errors.append(text)
    elif sev == 'note':
        parser.notes.append(text)
    else:
        parser.warnings.append(text)


def _split_output(out):
    """generate_page / prepass may return the value alone (the v2.4.0 form) or (value, findings)."""
    if isinstance(out, tuple) and len(out) == 2 and isinstance(out[1], (list, tuple)):
        return out[0], list(out[1])
    return out, []


def notation_prepass(pages: List[Tuple[str, str]], graph) -> List[Tuple[str, tuple]]:
    """Before any notation page is drawn, each notation's handler sees all its pages at once
    (`prepass(pages, graph)`, optional): what it returns becomes graph.notation_index[notation] — pages by
    level and system, containers by id — so page order never matters. Returns [(page name, finding)]."""
    import edgy_notation
    graph.notation_index = getattr(graph, 'notation_index', None) or {}
    findings: List[Tuple[str, tuple]] = []
    by_notation: dict = {}
    for name, text in pages:
        by_notation.setdefault(notation_of(text), []).append((name, text))
    for notation, group in by_notation.items():
        mod = edgy_notation.load_module(notation)
        if mod is None or not hasattr(mod, 'prepass'):
            continue                                   # E013 (no handler) is reported on each page itself
        try:
            index, found = _split_output(mod.prepass(group, graph))
        except Exception as e:                         # a broken handler fails closed, without a traceback
            findings.append((group[0][0], ('error', 'E013', f"notation handler '{notation}' failed in the prepass: "
                                                            f"{type(e).__name__}: {e}", None)))
            continue
        graph.notation_index[notation] = index if index is not None else {}
        for f in found:
            f = tuple(f)
            findings.append((f[4] if len(f) > 4 and f[4] else group[0][0], f[:4]))
    return findings


def attach_notation(parser: EDGYParser, page_text: str, graph, name: str = None) -> None:
    """A `notation: X` page is drawn by the registered handler of X (extension contract 1).
    Unknown or not installed → E013 on the page (fail closed: never drawn as EDGY). The handler runs here, at
    parse time, so its findings — (severity, rule, message, subject) — and its failures are input messages that
    stop the run before any file is written; `page_id(page_text, graph)` (optional) gives the page a fixed id."""
    import edgy_notation
    mod = edgy_notation.load_module(parser.notation)
    if mod is None or not hasattr(mod, 'generate_page'):
        msg = edgy_notation.unsupported_message(parser.notation)
        parser.warnings.append(msg)
        parser.errors.append(msg)
        return
    try:
        xml, findings = _split_output(mod.generate_page(page_text, graph))
        pid = mod.page_id(page_text, graph) if hasattr(mod, 'page_id') else None
    except Exception as e:
        parser.errors.append(f"E013 notation handler '{parser.notation}' failed on page '{name or 'page'}': "
                             f"{type(e).__name__}: {e}")
        return
    for f in findings:
        _apply_finding(parser, f)
    parser.foreign_xml = xml if isinstance(xml, str) else None
    if pid and re.match(r'^[a-z0-9][a-z0-9-]*$', str(pid)):
        parser.fixed_page_id = str(pid)


def _expand_notation(base: str, page_text: str, mode: str, where, graph) -> List[Tuple[str, EDGYParser]]:
    """expand: on a notation page reaches the handler: one page per target, each with `focus: <id>`. Without a
    handler it is E013 on one holder page — never an empty page per target (the fail-open case of 2.8.0)."""
    import edgy_graph
    import edgy_notation
    notation = notation_of(page_text)
    if edgy_notation.load_module(notation) is None:
        holder = EDGYParser()
        holder.parse_input(header_only(edgy_graph.EXPAND_RE.sub('', edgy_graph.WHERE_RE.sub('', page_text))))
        msg = edgy_notation.unsupported_message(notation)
        holder.warnings.append(msg)
        holder.errors.append(msg)
        return [(base, holder)]
    nodes, problems = edgy_graph.expand_targets(graph, mode, where)
    stripped = textwrap.dedent(edgy_graph.EXPAND_RE.sub('', edgy_graph.WHERE_RE.sub('', page_text)))
    stripped = re.sub(r'^(focus|system):.*$\n?', '', stripped, flags=re.M)
    out: List[Tuple[str, EDGYParser]] = []
    for node in nodes:
        text = f"focus: {node['id']}\n" + stripped
        p = EDGYParser()
        p.parse_input(header_only(text))
        page_name = f"{base} · {node['id']} {node['name']}"
        attach_notation(p, text, graph, page_name)
        out.append((page_name, p))
    if problems or not out:
        holder = out[-1][1] if out else EDGYParser()
        for msg in problems or [f"expand: {mode} on a notation: {notation} page found no target"]:
            holder.warnings.append(msg)
            holder.errors.append(msg)
        if not out:
            out.append((base, holder))
    return out


def _strip_declaration(xml: str) -> str:
    return re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml, count=1)


def page_ids_of(pages) -> Optional[List[str]]:
    """The fixed page ids parse_document gave (trace pages link to them), or None for the default slugs."""
    ids = [getattr(p, 'page_id', None) for _, p in pages]
    return ids if ids and all(ids) else None


def build_mxfile(pages: List[Tuple[str, str]], host: str = 'edgy-skills', page_ids: List[str] = None) -> str:
    """Wrap one or more mxGraphModel XML strings into an uncompressed mxfile.

    No timestamps or random ids: output is reproducible so that regenerated
    example files diff cleanly.
    """
    parts = [f'<?xml version="1.0" encoding="utf-8"?>\n<mxfile host="{host}" agent="edgy_generator.py" compressed="false">']
    page_ids = page_ids or unique_slugs([name for name, _ in pages])
    for (name, model_xml), page_id in zip(pages, page_ids):
        body = _strip_declaration(model_xml).strip()
        safe_name = name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
        parts.append(f'  <diagram id="{page_id}" name="{safe_name}">')
        parts.append('\n'.join('    ' + ln if ln else ln for ln in body.split('\n')))
        parts.append('  </diagram>')
    parts.append('</mxfile>\n')
    return '\n'.join(parts)


def unwrap_links(model: ET.Element) -> ET.Element:
    """Unwrap draw.io wrapper objects in place: <UserObject|object id label link …><mxCell …/></…> becomes the
    inner <mxCell> with the wrapper's id, its label as value and its link as `link` — so every reader that walks
    root/mxCell (lint, render, present, QA) sees linked cards (realisation trace page links, 2.9.0)."""
    root = model.find('root') if model.tag != 'root' else model
    if root is None:
        return model
    for i, child in enumerate(list(root)):
        if child.tag not in ('UserObject', 'object'):
            continue
        inner = child.find('mxCell')
        if inner is None:
            continue
        inner.set('id', child.get('id') or inner.get('id') or '')
        if child.get('label') is not None:
            inner.set('value', child.get('label'))
        if child.get('link'):
            inner.set('link', child.get('link'))
        root.remove(child)
        root.insert(i, inner)
    return model


def load_pages_from_file(path: str) -> List[Tuple[str, ET.Element]]:
    """Read a .drawio file (bare model or mxfile) → [(page_name, mxGraphModel)]."""
    import base64
    import urllib.parse
    import zlib
    root = ET.parse(path).getroot()
    if root.tag == 'mxGraphModel':
        return [(None, unwrap_links(root))]
    if root.tag != 'mxfile':
        raise ValueError(f'unexpected root element <{root.tag}>')
    pages = []
    for d in root.findall('diagram'):
        model = d.find('mxGraphModel')
        if model is None and d.text and d.text.strip():
            data = base64.b64decode(d.text.strip())
            model = ET.fromstring(urllib.parse.unquote(zlib.decompress(data, -15).decode('utf-8')))
        if model is not None:
            pages.append((d.get('name'), unwrap_links(model)))
    return pages
