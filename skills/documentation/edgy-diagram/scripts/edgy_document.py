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


def parse_document(text: str) -> List[Tuple[str, EDGYParser]]:
    """Parse a (possibly multi-page) input into [(page_name, parser)]."""
    result = []
    for name, page_text in split_pages(text):
        parser = EDGYParser()
        parser.parse_input(page_text)
        result.append((name or default_page_name(parser), parser))
    return result


def _strip_declaration(xml: str) -> str:
    return re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml, count=1)


def build_mxfile(pages: List[Tuple[str, str]], host: str = 'edgy-skills') -> str:
    """Wrap one or more mxGraphModel XML strings into an uncompressed mxfile.

    No timestamps or random ids: output is reproducible so that regenerated
    example files diff cleanly.
    """
    parts = [f'<?xml version="1.0" encoding="utf-8"?>\n<mxfile host="{host}" agent="edgy_generator.py" compressed="false">']
    seen = set()
    for i, (name, model_xml) in enumerate(pages, 1):
        slug = slugify(name)
        page_id = f'{slug}-{i}' if slug in seen else slug
        seen.add(slug)
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
