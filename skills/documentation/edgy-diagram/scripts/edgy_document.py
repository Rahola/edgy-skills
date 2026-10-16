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
import xml.etree.ElementTree as ET
from typing import List, Tuple

from edgy_parser import EDGYParser

PAGE_RE = re.compile(r'^\s*-\s*name:\s*"(.+?)"\s*$')
PAGES_RE = re.compile(r'^pages:\s*$')
_SLUG_RE = re.compile(r'[^a-z0-9]+')


def slugify(name: str) -> str:
    s = _SLUG_RE.sub('-', name.lower()).strip('-')
    return s or 'page'


def unique_slugs(names: List[str]) -> List[str]:
    """Deterministic, collision-free slugs for page names.

    Each name is slugified; if the slug is already taken (by an earlier page
    *or* by an earlier generated suffix such as `foo-2`), the lowest free
    `-N` suffix is used. Used for draw.io page ids and for per-page output
    file names, so neither can collide.
    """
    used = set()
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
        parser.parse_input(page_text)
        parsed.append((name or default_page_name(parser), parser, page_text))
    graph = edgy_graph.build_graph([(n, p) for n, p, _ in parsed if p is not None])
    result: List[Tuple[str, EDGYParser]] = []
    for name, parser, page_text in parsed:
        if parser is not None and parser.notation:
            attach_notation(parser, page_text, graph)
        if parser is not None:
            if edgy_views.is_derived(parser):
                edgy_views.materialize(parser, graph)
            if parser.draw:
                result.append((name, parser))
            continue
        mode, where = edgy_graph.expansion_of(page_text)
        nodes, problems = edgy_graph.expand_targets(graph, mode, where)
        base = name or 'view'
        stripped = edgy_graph.EXPAND_RE.sub('', edgy_graph.WHERE_RE.sub('', page_text))
        for node in nodes:
            p = EDGYParser()
            p.graph = graph
            p.parse_input(f"focus: {node['id']}\n" + stripped)
            if edgy_views.is_derived(p):
                edgy_views.materialize(p, graph)
            result.append((f"{base} · {node['id']} {node['name']}", p))
        if problems:
            holder = result[-1][1] if result else (parsed[0][1] or EDGYParser())
            for msg in problems:
                holder.warnings.append(msg)
                holder.errors.append(msg)
            if not result:
                result.append((base, holder))
    for (_, parser), slug in zip(result, unique_slugs([n for n, _ in result])):
        parser.page_id = slug
    if not result:
        raise ValueError("no page to draw — every page has draw: false")
    return (result, graph) if with_graph else result


def load_graph(text: str):
    """The document graph of an input (extension contract 1, entry point)."""
    return parse_document(text, with_graph=True)[1]


def attach_notation(parser: EDGYParser, page_text: str, graph) -> None:
    """A `notation: X` page is drawn by the registered handler of X (extension contract 1).
    Unknown or not installed → E013 on the page (fail closed: never drawn as EDGY)."""
    import edgy_notation
    mod = edgy_notation.load_module(parser.notation)
    if mod is None or not hasattr(mod, 'generate_page'):
        msg = edgy_notation.unsupported_message(parser.notation)
        parser.warnings.append(msg)
        parser.errors.append(msg)
        return
    parser.foreign = (mod, page_text, graph)


def _strip_declaration(xml: str) -> str:
    return re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml, count=1)


def build_mxfile(pages: List[Tuple[str, str]], host: str = 'edgy-skills') -> str:
    """Wrap one or more mxGraphModel XML strings into an uncompressed mxfile.

    No timestamps or random ids: output is reproducible so that regenerated
    example files diff cleanly.
    """
    parts = [f'<?xml version="1.0" encoding="utf-8"?>\n<mxfile host="{host}" agent="edgy_generator.py" compressed="false">']
    page_ids = unique_slugs([name for name, _ in pages])
    for (name, model_xml), page_id in zip(pages, page_ids):
        body = _strip_declaration(model_xml).strip()
        safe_name = name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
        parts.append(f'  <diagram id="{page_id}" name="{safe_name}">')
        parts.append('\n'.join('    ' + ln if ln else ln for ln in body.split('\n')))
        parts.append('  </diagram>')
    parts.append('</mxfile>\n')
    return '\n'.join(parts)


def load_pages_from_file(path: str) -> List[Tuple[str, ET.Element]]:
    """Read a .drawio file (bare model or mxfile) → [(page_name, mxGraphModel)]."""
    import base64
    import urllib.parse
    import zlib
    root = ET.parse(path).getroot()
    if root.tag == 'mxGraphModel':
        return [(None, root)]
    if root.tag != 'mxfile':
        raise ValueError(f'unexpected root element <{root.tag}>')
    pages = []
    for d in root.findall('diagram'):
        model = d.find('mxGraphModel')
        if model is None and d.text and d.text.strip():
            data = base64.b64decode(d.text.strip())
            model = ET.fromstring(urllib.parse.unquote(zlib.decompress(data, -15).decode('utf-8')))
        if model is not None:
            pages.append((d.get('name'), model))
    return pages
