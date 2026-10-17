"""Stub notation handler h-index (test plan K01–K03, test_notation_core.py)."""
import re

XML = ('<mxGraphModel pageWidth="800" pageHeight="600"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
       '<mxCell id="2" value="{label}" style="rounded=0;fillColor=#1168bd;fontColor=#ffffff;edgyNotation=zz;" '
       'vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>'
       '</root></mxGraphModel>')


def _key(page_text, key):
    m = re.search(r'^\s*' + key + r':\s*(\S+)', page_text, re.M)
    return m.group(1) if m else ''


def page_id(page_text, graph):
    system = _key(page_text, 'focus') or _key(page_text, 'system')
    return 'zz-' + (_key(page_text, 'level') or 'page') + '-' + re.sub(r'[^a-z0-9]+', '-', system.lower()).strip('-')


def prepass(pages, graph):
    """K07-style: the index sees every page of the notation before any is drawn."""
    return {'systems': sorted(_key(t, 'system') for _n, t in pages)}, []


def generate_page(page_text, graph):
    return XML.format(label='index ' + ','.join(graph.notation_index['zz']['systems']))
