#!/usr/bin/env python3
"""
Testiskripti EDGY-kaavioiden generoinnille
"""

import os
import sys
from edgy_parser import EDGYParser
from edgy_generator import main as generator_main

def test_identity_facet():
    """Testaa Identity-facetin jäsennys"""
    print("Testing Identity Facet...")

    parser = EDGYParser()

    input_text = """
facet: identity
elements:
  - purpose: "Yrityksen tarkoitus"
  - content: "Laadukas sisältö"
  - story: "Yhteinen tarina"
  - brand: "Brändi"
  - organisation: "Organisaatio"
relationships:
  - purpose -> content: "ohjaa"
  - purpose -> story: "muodostaa"
  - content -> brand: "vahvistaa"
"""

    parser.parse_input(input_text)

    # Tarkista elementit
    assert len(parser.elements) == 5, f"Expected 5 elements, got {len(parser.elements)}"

    # Etsi elementit tyypeittäin
    purpose_elements = [elem for elem in parser.elements.values() if elem['type'] == 'purpose']
    content_elements = [elem for elem in parser.elements.values() if elem['type'] == 'content']

    assert len(purpose_elements) == 1, f"Expected 1 purpose element, got {len(purpose_elements)}"
    assert len(content_elements) == 1, f"Expected 1 content element, got {len(content_elements)}"

    # Tarkista suhteet
    assert len(parser.relationships) == 3, f"Expected 3 relationships, got {len(parser.relationships)}"

    # Generoi XML
    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output
    assert 'fillColor=#80ffb7' in xml_output, "Identity color #80ffb7 not found in output"

    print("Identity Facet test passed")

def test_architecture_facet():
    """Testaa Architecture-facetin jäsennys"""
    print("Testing Architecture Facet...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Kehitysosaaminen"
  - asset: "Resurssit"
  - process: "Prosessit"
  - organisation: "Organisaatio"
  - product: "Tuote"
relationships:
  - capability -> process: "mahdollistaa"
  - asset -> capability: "tukee"
"""

    parser.parse_input(input_text)

    # Tarkista elementit
    assert len(parser.elements) == 5, f"Expected 5 elements, got {len(parser.elements)}"
    assert parser.elements['capability1']['type'] == 'capability'

    # Tarkista suhteet
    assert len(parser.relationships) == 2, f"Expected 2 relationships, got {len(parser.relationships)}"

    # Generoi XML
    xml_output = parser.generate_xml()
    assert 'fillColor=#a6c0ff' in xml_output, "Architecture color #a6c0ff not found in output"

    print("Architecture Facet test passed")

def test_experience_facet():
    """Testaa Experience-facetin jäsennys"""
    print("Testing Experience Facet...")

    parser = EDGYParser()

    input_text = """
facet: experience
elements:
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Matka"
  - brand: "Brändi"
  - product: "Tuote"
relationships:
  - task -> journey: "osa"
  - channel -> task: "mahdollistaa"
"""

    parser.parse_input(input_text)

    # Tarkista elementit
    assert len(parser.elements) == 5, f"Expected 5 elements, got {len(parser.elements)}"
    assert parser.elements['task1']['type'] == 'task'

    # Generoi XML
    xml_output = parser.generate_xml()
    assert 'fillColor=#ff99bd' in xml_output, "Experience color #ff99bd not found in output"

    print("Experience Facet test passed")

def test_full_edgy_map():
    """Testaa monifacet-kaavion jäsennys"""
    print("Testing Full EDGY Map...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - purpose: "Yrityksen tarkoitus"
  - capability: "Kehitysosaaminen"
  - task: "Tehtävä"
relationships:
  - purpose -> capability: "ohjaa"
  - capability -> task: "mahdollistaa"
"""

    parser.parse_input(input_text)

    # Tarkista elementit
    assert len(parser.elements) == 3, f"Expected 3 elements, got {len(parser.elements)}"

    # Tarkista suhteet
    assert len(parser.relationships) == 2, f"Expected 2 relationships, got {len(parser.relationships)}"

    # Generoi XML
    xml_output = parser.generate_xml()
    assert 'fillColor=#80ffb7' in xml_output, "Identity color not found"
    assert 'fillColor=#a6c0ff' in xml_output, "Architecture color not found"
    assert 'fillColor=#ff99bd' in xml_output, "Experience color not found"

    print("Full EDGY Map test passed")

def test_ambiguous_names():
    """Testaa relaatioiden osuma kun elementeillä on samankaltaiset nimet"""
    print("Testing Ambiguous Name Matching...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Testi"
  - asset: "Testijärjestelmä"
  - process: "Testiprosessi"
relationships:
  - "Testi" -> "Testiprosessi": "ohjaa"
  - "Testijärjestelmä" -> "Testi": "tukee"
"""

    parser.parse_input(input_text)

    assert len(parser.elements) == 3, f"Expected 3 elements, got {len(parser.elements)}"
    assert len(parser.relationships) == 2, f"Expected 2 relationships, got {len(parser.relationships)}"

    # Tarkista että "Testi" -> "Testiprosessi" osuu oikeisiin elementteihin
    rel1 = parser.relationships[0]
    source_elem = parser.elements[rel1['source']]
    target_elem = parser.elements[rel1['target']]
    assert source_elem['value'] == 'Testi', f"Expected source 'Testi', got '{source_elem['value']}'"
    assert target_elem['value'] == 'Testiprosessi', f"Expected target 'Testiprosessi', got '{target_elem['value']}'"

    # Tarkista että "Testijärjestelmä" -> "Testi" osuu oikeisiin elementteihin
    rel2 = parser.relationships[1]
    source_elem2 = parser.elements[rel2['source']]
    target_elem2 = parser.elements[rel2['target']]
    assert source_elem2['value'] == 'Testijärjestelmä', f"Expected source 'Testijärjestelmä', got '{source_elem2['value']}'"
    assert target_elem2['value'] == 'Testi', f"Expected target 'Testi', got '{target_elem2['value']}'"

    print("Ambiguous Name Matching test passed")

def test_all_facet_layout_order():
    """Testaa että facet 'all' -tilassa elementit sijoittuvat oikeisiin faset-sarakkeisiin"""
    print("Testing All-Facet Layout Order...")

    parser = EDGYParser()

    # Elementit sekajärjestyksessä (EI faset-ryhmittäin)
    input_text = """
facet: all
elements:
  - brand: "Brändi"
  - capability: "Kehitysosaaminen"
  - purpose: "Tarkoitus"
  - task: "Tehtävä"
  - organisation: "Organisaatio"
relationships:
  - "Tarkoitus" -> "Kehitysosaaminen": "ohjaa"
"""

    parser.parse_input(input_text)

    xml_output = parser.generate_xml()

    # Jäsennä XML ja tarkista positiot
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None:
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    # Suhteellinen sarakevalidointi: Identity < Architecture < Experience
    id_x = cells['Tarkoitus'][0]
    arch_x = cells['Kehitysosaaminen'][0]
    exp_x = cells['Tehtävä'][0]
    assert id_x < arch_x, f"Identity x ({id_x}) should be < Architecture x ({arch_x})"
    assert arch_x < exp_x, f"Architecture x ({arch_x}) should be < Experience x ({exp_x})"

    # Intersection-elementtien y-koordinaatin pitää olla suurempi kuin facet-elementtien
    facet_max_y = max(cells['Tarkoitus'][1], cells['Kehitysosaaminen'][1], cells['Tehtävä'][1])
    assert cells['Brändi'][1] > facet_max_y, "Brand should be below facet elements"
    assert cells['Organisaatio'][1] > facet_max_y, "Organisation should be below facet elements"

    # Organisation tulee olla Identity- ja Architecture-sarakkeiden välissä
    org_x = cells['Organisaatio'][0]
    assert id_x < org_x < exp_x, f"Organisation x ({org_x}) should be between Identity and Experience"

    print("All-Facet Layout Order test passed")

def test_invalid_relationship():
    """Testaa että virheellinen relaatio (tuntematon kohde) ohitetaan ilman kaatumista"""
    print("Testing Invalid Relationship Handling...")

    parser = EDGYParser()

    input_text = """
facet: identity
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
relationships:
  - purpose -> content: "ohjaa"
  - purpose -> olematon_elementti: "virheellinen"
"""

    parser.parse_input(input_text)

    assert len(parser.elements) == 2, f"Expected 2 elements, got {len(parser.elements)}"
    # Vain yksi relaatio pitäisi onnistua, toinen ohitetaan
    assert len(parser.relationships) == 1, f"Expected 1 valid relationship, got {len(parser.relationships)}"

    # XML generointi ei saa kaatua
    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output

    print("Invalid Relationship Handling test passed")

def test_prefix_matching():
    """Testaa alkuosa-osumaa (elementin nimi ennen ' - ' -erotinta)"""
    print("Testing Prefix Matching...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Asiakasjärjestelmät - Asiakastiedon hallinta"
  - asset: "Testijärjestelmä - Automaattitestaus"
relationships:
  - "Asiakasjärjestelmät" -> "Testijärjestelmä": "käyttää"
"""

    parser.parse_input(input_text)

    assert len(parser.relationships) == 1, f"Expected 1 relationship, got {len(parser.relationships)}"

    rel = parser.relationships[0]
    source = parser.elements[rel['source']]
    target = parser.elements[rel['target']]
    assert 'Asiakasjärjestelmät' in source['value'], f"Wrong source: {source['value']}"
    assert 'Testijärjestelmä' in target['value'], f"Wrong target: {target['value']}"

    print("Prefix Matching test passed")

def test_intersection_element_positions():
    """Testaa leikkauselementtien (Brand/Organisation/Product) x-positiot facet:all -tilassa"""
    print("Testing Intersection Element Positions in facet:all...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - purpose: "Tarkoitus"
  - capability: "Kyvykkyys"
  - task: "Tehtävä"
  - organisation: "Organisaatio"
  - product: "Tuote"
  - brand: "Brändi"
relationships:
  - "Tarkoitus" -> "Kyvykkyys": "ohjaa"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None:
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    # Suhteellinen sarakevalidointi: Identity < Architecture < Experience
    id_x = cells['Tarkoitus'][0]
    arch_x = cells['Kyvykkyys'][0]
    exp_x = cells['Tehtävä'][0]
    assert id_x < arch_x, f"Identity x ({id_x}) should be < Architecture x ({arch_x})"
    assert arch_x < exp_x, f"Architecture x ({arch_x}) should be < Experience x ({exp_x})"

    # Organisation: Identity- ja Architecture-sarakkeiden välissä
    org_x = cells['Organisaatio'][0]
    assert id_x < org_x < exp_x, f"Organisation x ({org_x}) should be between Identity and Experience"

    # Product: Architecture- ja Experience-sarakkeiden välissä
    prod_x = cells['Tuote'][0]
    assert arch_x <= prod_x, f"Product x ({prod_x}) should be >= Architecture x ({arch_x})"

    # Brand: Identity- ja Experience-sarakkeiden välissä
    brand_x = cells['Brändi'][0]
    assert id_x < brand_x < exp_x + 200, f"Brand x ({brand_x}) should be between Identity and Experience"

    # Kaikki leikkauselementit ovat facet-elementtien alapuolella
    facet_max_y = max(cells['Tarkoitus'][1], cells['Kyvykkyys'][1], cells['Tehtävä'][1])
    assert cells['Organisaatio'][1] > facet_max_y, "Organisation should be below facet elements"
    assert cells['Tuote'][1] > facet_max_y, "Product should be below facet elements"
    assert cells['Brändi'][1] >= cells['Organisaatio'][1], "Brand should be at same level or below Organisation"

    print("Intersection Element Positions test passed")


def test_tree_relationships():
    """Testaa puuhierarkian (tree) tunnistus ja layout"""
    print("Testing Tree Relationships...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "IT-palvelut"
  - capability: "Sovelluskehitys"
  - capability: "Infrastruktuuri"
relationships:
  - "IT-palvelut" -> "Sovelluskehitys": "sisältää"
  - "IT-palvelut" -> "Infrastruktuuri": "sisältää"
"""

    parser.parse_input(input_text)

    assert len(parser.elements) == 3, f"Expected 3 elements, got {len(parser.elements)}"
    assert len(parser.relationships) == 2, f"Expected 2 relationships, got {len(parser.relationships)}"

    # Generoi XML
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    # Tarkista edge-tyylit: "sisältää" on tree → ei nuolenpäätä
    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    assert 'sisältää' in edge_styles, "Edge 'sisältää' not found"
    assert 'endArrow=none' in edge_styles['sisältää'], \
        f"Tree 'sisältää' should have no arrowhead, got: {edge_styles['sisältää']}"

    # Tarkista layout: lapset ovat vanhemman alapuolella
    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None and cell.get('vertex') == '1':
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    assert cells['Sovelluskehitys'][1] > cells['IT-palvelut'][1], \
        "Child 'Sovelluskehitys' should be below parent 'IT-palvelut'"
    assert cells['Infrastruktuuri'][1] > cells['IT-palvelut'][1], \
        "Child 'Infrastruktuuri' should be below parent 'IT-palvelut'"
    assert cells['Sovelluskehitys'][1] == cells['Infrastruktuuri'][1], \
        "Siblings should be on same y level"

    print("Tree Relationships test passed")


def test_people_base_element():
    """Testaa People-peruselementin tunnistus ja renderöinti"""
    print("Testing People Base Element...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - people: "Asiakkaat"
  - purpose: "Tarkoitus"
  - capability: "Kyvykkyys"
"""

    parser.parse_input(input_text)

    assert len(parser.elements) == 3, f"Expected 3 elements, got {len(parser.elements)}"

    # Tarkista people-elementin tyyppi
    people_elems = [e for e in parser.elements.values() if e['type'] == 'people']
    assert len(people_elems) == 1, f"Expected 1 people element, got {len(people_elems)}"

    # Generoi XML ja tarkista person-muoto
    xml_output = parser.generate_xml()
    assert 'mxgraph.basic.person' in xml_output, "People element should use person shape"

    print("People Base Element test passed")


def test_map_type_journey():
    """Testaa journey-karttatyypin sekventiaalinen layout"""
    print("Testing Journey Map Type Layout...")

    parser = EDGYParser()

    input_text = """
map_type: journey
elements:
  - journey: "Harkitse"
  - journey: "Tutki"
  - journey: "Varaa"
  - journey: "Matkusta"
"""

    parser.parse_input(input_text)
    assert parser.map_type == 'journey', f"Expected map_type 'journey', got '{parser.map_type}'"

    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None and cell.get('vertex') == '1':
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    # Kaikki samalla y-tasolla (sekventiaalinen)
    y_values = [cells[v][1] for v in ['Harkitse', 'Tutki', 'Varaa', 'Matkusta']]
    assert len(set(y_values)) == 1, f"All journey steps should be on same y level, got: {y_values}"

    # X-positiot kasvavat vasemmalta oikealle
    x_values = [cells[v][0] for v in ['Harkitse', 'Tutki', 'Varaa', 'Matkusta']]
    assert x_values == sorted(x_values), f"Journey steps should be left-to-right, got: {x_values}"

    print("Journey Map Type Layout test passed")


def test_map_type_capability():
    """Testaa capability-karttatyypin ruudukkopohjainen layout"""
    print("Testing Capability Map Type Layout...")

    parser = EDGYParser()

    input_text = """
map_type: capability
elements:
  - capability: "IT-palvelut"
  - capability: "Sovelluskehitys"
  - capability: "Infrastruktuuri"
  - capability: "Tietoturva"
relationships:
  - "IT-palvelut" -> "Sovelluskehitys": "sisältää"
  - "IT-palvelut" -> "Infrastruktuuri": "sisältää"
"""

    parser.parse_input(input_text)
    assert parser.map_type == 'capability'

    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output

    # Varmista tree-relaatio: lapset ovat vanhemman alla
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None and cell.get('vertex') == '1':
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    assert cells['Sovelluskehitys'][1] > cells['IT-palvelut'][1], \
        "Child should be below parent in capability map"

    print("Capability Map Type Layout test passed")


def test_labels_tags_metrics():
    """Testaa elementtien tagit ja metriikat"""
    print("Testing Labels (Tags and Metrics)...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Asiakaspalvelu" [in-house, differentiating] {cost: high}
  - asset: "CRM" [application]
  - process: "Palveluprosessi"
"""

    parser.parse_input(input_text)

    assert len(parser.elements) == 3, f"Expected 3 elements, got {len(parser.elements)}"

    # Tarkista tagit ja metriikat
    cap = [e for e in parser.elements.values() if e['type'] == 'capability'][0]
    assert cap['tags'] == ['in-house', 'differentiating'], f"Wrong tags: {cap['tags']}"
    assert cap['metrics'] == {'cost': 'high'}, f"Wrong metrics: {cap['metrics']}"

    asset = [e for e in parser.elements.values() if e['type'] == 'asset'][0]
    assert asset['tags'] == ['application'], f"Wrong tags: {asset['tags']}"
    assert asset['metrics'] == {}, f"Expected empty metrics, got: {asset['metrics']}"

    proc = [e for e in parser.elements.values() if e['type'] == 'process'][0]
    assert proc['tags'] == [], f"Expected empty tags, got: {proc['tags']}"

    # Generoi XML ja tarkista HTML-labelit
    xml_output = parser.generate_xml()
    assert 'in-house' in xml_output, "Tag 'in-house' should appear in output"
    assert 'cost: high' in xml_output, "Metric 'cost: high' should appear in output"

    print("Labels (Tags and Metrics) test passed")


def test_core_link_styles():
    """Testaa virallisten EDGY-ydinlinkkien visuaalinen tyyli"""
    print("Testing Core Link Styles...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - organisation: "Organisaatio"
  - purpose: "Tarkoitus"
  - capability: "Kyvykkyys"
  - product: "Tuote"
  - task: "Tehtävä"
relationships:
  - "Organisaatio" -> "Tarkoitus": "tavoittelee"
  - "Tuote" -> "Tehtävä": "palvelee"
  - "Kyvykkyys" -> "Tuote": "mahdollistaa"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # "tavoittelee" on core link → suuntanuoli (classic)
    assert 'endArrow=classic' in edge_styles['tavoittelee'], \
        f"Core link 'tavoittelee' should have classic arrow, got: {edge_styles['tavoittelee']}"

    # "palvelee" on core link → suuntanuoli (classic)
    assert 'endArrow=classic' in edge_styles['palvelee'], \
        f"Core link 'palvelee' should have classic arrow, got: {edge_styles['palvelee']}"

    # "mahdollistaa" EI ole core link → vaikutusviiva, katkoviiva + avoin nuolenpää
    assert 'dashed=1' in edge_styles['mahdollistaa'] and 'endArrow=open' in edge_styles['mahdollistaa'], \
        f"Influence 'mahdollistaa' should be dashed with open arrow, got: {edge_styles['mahdollistaa']}"

    print("Core Link Styles test passed")


def test_edge_styles():
    """Testaa relaatioiden visuaalinen tyyli (tietovirtanuoli / linkki / vaikutusnuoli)"""
    print("Testing Edge Styles (flow / link / influence)...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Kyvykkyys"
  - asset: "Resurssi"
  - process: "Prosessi"
  - product: "Tuote"
relationships:
  - "Prosessi" -> "Tuote": "virtaa"
  - "Resurssi" -> "Kyvykkyys": "osa"
  - "Kyvykkyys" -> "Prosessi": "mahdollistaa"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # "virtaa" on TIETOVIRTANUOLI → avoin nuolenpää (EDGY spec)
    assert 'virtaa' in edge_styles, "Edge 'virtaa' not found"
    assert 'endArrow=open' in edge_styles['virtaa'] and 'endFill=0' in edge_styles['virtaa'], \
        f"Flow 'virtaa' should have open arrowhead (endArrow=open;endFill=0), got: {edge_styles['virtaa']}"

    # "osa" on ydinlinkkiverbi (task → journey), mutta tässä parina on
    # asset → capability → ei virallinen ydinlinkki → influence (katkoviiva) + varoitus
    assert 'osa' in edge_styles, "Edge 'osa' not found"
    assert 'dashed=1' in edge_styles['osa'], \
        f"Core verb 'osa' on a non-core pair should be drawn as influence, got: {edge_styles['osa']}"
    assert any("'osa'" in w and 'influence' in w for w in parser.warnings), \
        f"Expected wrong-pair warning for 'osa', got: {parser.warnings}"
    assert 'endArrow=open' in edge_styles['osa'] and 'endFill=0' in edge_styles['osa'], \
        f"Influence-styled 'osa' should have an open arrowhead, got: {edge_styles['osa']}"

    # "mahdollistaa" on VAIKUTUSVIIVA (oletus) → katkoviiva + avoin nuoli
    assert 'mahdollistaa' in edge_styles, "Edge 'mahdollistaa' not found"
    assert 'dashed=1' in edge_styles['mahdollistaa'], \
        f"Influence 'mahdollistaa' should be dashed, got: {edge_styles['mahdollistaa']}"
    assert 'endArrow=open' in edge_styles['mahdollistaa'], \
        f"Influence 'mahdollistaa' should have open arrow, got: {edge_styles['mahdollistaa']}"

    print("Edge Styles test passed")


def test_xml_entity_escaping():
    """Testaa XML-entiteettien escapointi erikoismerkeillä"""
    print("Testing XML Entity Escaping...")

    parser = EDGYParser()

    input_text = """
facet: identity
elements:
  - purpose: "A & B <C>"
  - content: "Sisältö \"arvo\""
relationships:
  - "A & B <C>" -> "Sisältö \\"arvo\\"": "ohjaa"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    # XML pitää olla validia — ET.fromstring ei saa kaatua
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_output)
    except ET.ParseError as e:
        raise AssertionError(f"Generated XML is not valid: {e}")

    # Varmista että erikoismerkit ovat escapoitu oikein
    assert '&amp;' in xml_output or '&' not in xml_output.split('value="')[1].split('"')[0] if 'A &' in xml_output else True

    print("XML Entity Escaping test passed")


def test_coordinate_grid_snapping():
    """Testaa koordinaattien pyöristys kokonaisluvuiksi"""
    print("Testing Coordinate Grid Snapping...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - purpose: "Tarkoitus"
  - capability: "Kyvykkyys"
  - task: "Tehtävä"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    for cell in root.iter('mxCell'):
        geom = cell.find('mxGeometry')
        if geom is not None and geom.get('x') is not None:
            x_val = geom.get('x')
            y_val = geom.get('y')
            # Koordinaattien pitää olla kokonaislukuja (ei desimaaleja)
            assert '.' not in x_val, f"x-coordinate should be integer, got: {x_val}"
            assert '.' not in y_val, f"y-coordinate should be integer, got: {y_val}"

    print("Coordinate Grid Snapping test passed")


def test_unmapped_edge_skipped():
    """Testaa että edge jolla on tuntematon source/target ohitetaan"""
    print("Testing Unmapped Edge Skipping...")

    parser = EDGYParser()

    input_text = """
facet: identity
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
relationships:
  - "Tarkoitus" -> "Sisältö": "ohjaa"
"""

    parser.parse_input(input_text)

    # Lisää manuaalisesti virheellinen relaatio (tuntematon elementti-ID)
    parser.relationships.append({
        'source': 'nonexistent_id',
        'target': 'purpose1',
        'label': 'testi'
    })

    # XML generointi ei saa kaatua
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    # Vain yksi malli-edge pitäisi olla (virheellinen ohitettu).
    # Legend-edgeillä ei ole source/target-attribuutteja — suodatetaan ne pois.
    edges = [c for c in root.iter('mxCell') if c.get('edge') == '1' and c.get('source')]
    assert len(edges) == 1, f"Expected 1 edge (invalid skipped), got {len(edges)}"

    print("Unmapped Edge Skipping test passed")


def test_invalid_facet():
    """Testaa tuntemattoman facet-arvon käsittely"""
    print("Testing Invalid Facet Value...")

    parser = EDGYParser()

    input_text = """
facet: nonexistent
elements:
  - purpose: "Tarkoitus"
"""

    parser.parse_input(input_text)
    assert parser.facet == 'identity', f"Invalid facet should default to 'identity', got '{parser.facet}'"
    assert any('Tuntematon facet' in w for w in parser.warnings), \
        f"Expected warning about unknown facet, got: {parser.warnings}"

    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output

    print("Invalid Facet Value test passed")


def test_invalid_map_type():
    """Testaa tuntemattoman map_type-arvon käsittely"""
    print("Testing Invalid Map Type...")

    parser = EDGYParser()

    input_text = """
map_type: nonexistent
elements:
  - capability: "Kyvykkyys"
"""

    parser.parse_input(input_text)
    assert parser.map_type is None, f"Invalid map_type should default to None, got '{parser.map_type}'"
    assert any('Tuntematon map_type' in w for w in parser.warnings), \
        f"Expected warning about unknown map_type, got: {parser.warnings}"

    print("Invalid Map Type test passed")


def test_unknown_element_type():
    """Testaa tuntemattoman elementtityypin käsittely"""
    print("Testing Unknown Element Type...")

    parser = EDGYParser()

    input_text = """
facet: identity
elements:
  - purpose: "Tarkoitus"
  - unknowntype: "Tuntematon"
"""

    parser.parse_input(input_text)
    assert len(parser.elements) == 2, f"Both elements should be parsed, got {len(parser.elements)}"
    assert any('Tuntematon elementtityyppi' in w for w in parser.warnings), \
        f"Expected warning about unknown element type, got: {parser.warnings}"

    # XML generointi ei saa kaatua
    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output

    print("Unknown Element Type test passed")


def test_empty_input():
    """Testaa tyhjän syötteen käsittely"""
    print("Testing Empty Input...")

    parser = EDGYParser()
    parser.parse_input("")

    assert len(parser.elements) == 0
    assert len(parser.relationships) == 0

    xml_output = parser.generate_xml()
    assert '<mxGraphModel' in xml_output

    print("Empty Input test passed")


def test_core_link_direction_warning():
    """Testaa ydinlinkin suuntavalidoinnin varoitus"""
    print("Testing Core Link Direction Warning...")

    parser = EDGYParser()

    # "tavoittelee" pitäisi olla organisation → purpose, mutta tässä on väärin päin
    input_text = """
facet: all
elements:
  - purpose: "Tarkoitus"
  - organisation: "Organisaatio"
relationships:
  - "Tarkoitus" -> "Organisaatio": "tavoittelee"
"""

    parser.parse_input(input_text)
    assert len(parser.relationships) == 1, "Relationship should still be created"
    assert any('Ydinlinkki' in w and 'tavoittelee' in w for w in parser.warnings), \
        f"Expected direction warning for 'tavoittelee', got: {parser.warnings}"

    print("Core Link Direction Warning test passed")


def test_layout_y_spacing():
    """Testaa y-välistys saman sarakkeen elementtien välillä"""
    print("Testing Layout Y-Spacing...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys"
  - asset: "Resurssi"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None and cell.get('vertex') == '1':
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    # Identity-sarakkeen y-välistys ≥ 60px
    identity_ys = sorted([cells[n][1] for n in ['Tarkoitus', 'Sisältö', 'Tarina']])
    for i in range(len(identity_ys) - 1):
        spacing = identity_ys[i + 1] - identity_ys[i]
        assert spacing >= 60, f"Identity y-spacing should be >= 60px, got {spacing}px"

    print("Layout Y-Spacing test passed")


def test_journey_map_x_spacing():
    """Testaa journey-karttatyypin x-välistys"""
    print("Testing Journey Map X-Spacing...")

    parser = EDGYParser()

    input_text = """
map_type: journey
elements:
  - journey: "Vaihe 1"
  - journey: "Vaihe 2"
  - journey: "Vaihe 3"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    cells = {}
    for cell in root.iter('mxCell'):
        value = cell.get('value', '')
        geom = cell.find('mxGeometry')
        if value and geom is not None and cell.get('vertex') == '1':
            cells[value] = (int(geom.get('x', '0')), int(geom.get('y', '0')))

    x_values = sorted([cells[f'Vaihe {i}'][0] for i in range(1, 4)])
    for i in range(len(x_values) - 1):
        spacing = x_values[i + 1] - x_values[i]
        assert spacing >= 80, f"Journey map x-spacing should be >= 80px, got {spacing}px"

    print("Journey Map X-Spacing test passed")


def test_french_core_links():
    """Test French core link verbs are recognised"""
    print("Testing French Core Links...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - organisation: "Organisation"
  - purpose: "Raison d'être"
  - capability: "Capacité"
  - product: "Produit"
  - task: "Tâche"
  - story: "Récit"
  - brand: "Marque"
relationships:
  - "Organisation" -> "Raison d'être": "poursuit"
  - "Produit" -> "Tâche": "sert"
  - "Organisation" -> "Récit": "rédige"
  - "Marque" -> "Raison d'être": "représente"
  - "Produit" -> "Marque": "incarne"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # All French verbs should be recognised as core links (classic arrow)
    for verb in ['poursuit', 'sert', 'rédige', 'représente', 'incarne']:
        assert verb in edge_styles, f"French core link '{verb}' not found in edges"
        assert 'endArrow=classic' in edge_styles[verb], \
            f"French core link '{verb}' should have classic arrow, got: {edge_styles[verb]}"

    print("French Core Links test passed")


def test_german_core_links():
    """Test German core link verbs are recognised"""
    print("Testing German Core Links...")

    parser = EDGYParser()

    input_text = """
facet: all
elements:
  - organisation: "Organisation"
  - purpose: "Daseinszweck"
  - capability: "Fähigkeit"
  - product: "Produkt"
  - task: "Aufgabe"
  - story: "Geschichte"
  - brand: "Marke"
relationships:
  - "Organisation" -> "Daseinszweck": "verfolgt"
  - "Produkt" -> "Aufgabe": "bedient"
  - "Organisation" -> "Geschichte": "verfasst"
  - "Marke" -> "Daseinszweck": "repräsentiert"
  - "Produkt" -> "Marke": "verkörpert"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # All German verbs should be recognised as core links (classic arrow)
    for verb in ['verfolgt', 'bedient', 'verfasst', 'repräsentiert', 'verkörpert']:
        assert verb in edge_styles, f"German core link '{verb}' not found in edges"
        assert 'endArrow=classic' in edge_styles[verb], \
            f"German core link '{verb}' should have classic arrow, got: {edge_styles[verb]}"

    print("German Core Links test passed")


def test_french_flow_and_tree():
    """Test French flow and tree relationship keywords"""
    print("Testing French Flow and Tree Relationships...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Capacité principale"
  - capability: "Sous-capacité"
  - asset: "Système A"
  - asset: "Système B"
relationships:
  - "Capacité principale" -> "Sous-capacité": "contient"
  - "Système A" -> "Système B": "circule"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # "contient" is a tree relationship → no arrowhead
    assert 'contient' in edge_styles, "French tree 'contient' not found"
    assert 'endArrow=none' in edge_styles['contient'], \
        f"French tree 'contient' should have no arrowhead, got: {edge_styles['contient']}"

    # "circule" is a flow relationship → open arrowhead (EDGY spec)
    assert 'circule' in edge_styles, "French flow 'circule' not found"
    assert 'endArrow=open' in edge_styles['circule'] and 'endFill=0' in edge_styles['circule'], \
        f"French flow 'circule' should have open arrowhead (endArrow=open;endFill=0), got: {edge_styles['circule']}"

    print("French Flow and Tree Relationships test passed")


def test_german_flow_and_tree():
    """Test German flow and tree relationship keywords"""
    print("Testing German Flow and Tree Relationships...")

    parser = EDGYParser()

    input_text = """
facet: architecture
elements:
  - capability: "Hauptfähigkeit"
  - capability: "Unterfähigkeit"
  - asset: "System A"
  - asset: "System B"
relationships:
  - "Hauptfähigkeit" -> "Unterfähigkeit": "enthält"
  - "System A" -> "System B": "fließt"
"""

    parser.parse_input(input_text)
    xml_output = parser.generate_xml()

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    edge_styles = {}
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            edge_styles[cell.get('value', '')] = cell.get('style', '')

    # "enthält" is a tree relationship → no arrowhead
    assert 'enthält' in edge_styles, "German tree 'enthält' not found"
    assert 'endArrow=none' in edge_styles['enthält'], \
        f"German tree 'enthält' should have no arrowhead, got: {edge_styles['enthält']}"

    # "fließt" is a flow relationship → open arrowhead (EDGY spec)
    assert 'fließt' in edge_styles, "German flow 'fließt' not found"
    assert 'endArrow=open' in edge_styles['fließt'] and 'endFill=0' in edge_styles['fließt'], \
        f"German flow 'fließt' should have open arrowhead (endArrow=open;endFill=0), got: {edge_styles['fließt']}"

    print("German Flow and Tree Relationships test passed")


def test_no_box_overlap():
    """facet:all 12 elementtiä — minkään elementtiparin bounding boxit eivät overlap."""
    print("Testing No Box Overlap (facet:all)...")

    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys A"
  - asset: "Resurssi A"
  - process: "Prosessi A"
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Polku"
  - brand: "Brändi"
  - product: "Tuote"
  - organisation: "Organisaatio"
""")
    positions = parser._calculate_layout()
    sizes = {eid: parser._get_element_size(parser.elements[eid]) for eid in positions}
    ids = list(positions.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ax, ay = positions[ids[i]]
            bx, by = positions[ids[j]]
            aw, ah = sizes[ids[i]]
            bw, bh = sizes[ids[j]]
            ox = min(ax + aw, bx + bw) - max(ax, bx)
            oy = min(ay + ah, by + bh) - max(ay, by)
            assert ox <= 0 or oy <= 0, \
                f"Overlap: {ids[i]} ({ax},{ay},{aw}x{ah}) vs {ids[j]} ({bx},{by},{bw}x{bh})"
    print("No Box Overlap test passed")


def test_tree_subtree_widths():
    """Tree-layout: juuri + 2 lasta + 3+3 lapsenlasta — alipuut eivät overlap."""
    print("Testing Tree Subtree Widths...")

    parser = EDGYParser()
    parser.parse_input("""
facet: architecture
elements:
  - capability: "Juuri"
  - capability: "Vasen"
  - capability: "Oikea"
  - capability: "V1"
  - capability: "V2"
  - capability: "V3"
  - capability: "O1"
  - capability: "O2"
  - capability: "O3"
relationships:
  - "Juuri" -> "Vasen": "sisältää"
  - "Juuri" -> "Oikea": "sisältää"
  - "Vasen" -> "V1": "sisältää"
  - "Vasen" -> "V2": "sisältää"
  - "Vasen" -> "V3": "sisältää"
  - "Oikea" -> "O1": "sisältää"
  - "Oikea" -> "O2": "sisältää"
  - "Oikea" -> "O3": "sisältää"
""")
    positions = parser._calculate_layout()
    # V3 (vasemman alipuun oikein) ei saa overlapata O1:n (oikean alipuun vasen) kanssa
    v3 = next(eid for eid, e in parser.elements.items() if e['value'] == 'V3')
    o1 = next(eid for eid, e in parser.elements.items() if e['value'] == 'O1')
    v3x, _ = positions[v3]
    o1x, _ = positions[o1]
    assert o1x > v3x + 100, f"V3 ({v3x}) ja O1 ({o1x}) liian lähekkäin — alipuut overlappaavat"
    print("Tree Subtree Widths test passed")


def test_radial_purpose_scaling():
    """Purpose-kartta 8 elementillä — vierekkäisten kulmaelementtien etäisyys > 140."""
    print("Testing Radial Purpose Scaling...")
    import math

    parser = EDGYParser()
    parser.parse_input("""
map_type: purpose
elements:
  - purpose: "Keskeinen tarkoitus"
  - outcome: "T1"
  - outcome: "T2"
  - outcome: "T3"
  - outcome: "T4"
  - outcome: "T5"
  - outcome: "T6"
  - outcome: "T7"
""")
    positions = parser._calculate_layout()
    outer = [eid for eid, e in parser.elements.items() if e['value'] != 'Keskeinen tarkoitus']
    coords = [positions[eid] for eid in outer]
    for i in range(len(coords)):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % len(coords)]
        dist = math.hypot(x1 - x2, y1 - y2)
        assert dist > 140, f"Vierekkäiset purpose-elementit liian lähellä: {dist:.0f}"
    print("Radial Purpose Scaling test passed")


def test_edge_anchors_horizontal():
    """Source vasemmalla, target oikealla → exitX=1;entryX=0."""
    print("Testing Edge Anchors (horizontal)...")

    parser = EDGYParser()
    parser.parse_input("""
facet: identity
elements:
  - purpose: "A"
  - story: "B"
relationships:
  - "A" -> "B": "ohjaa"
""")
    # Aseta positiot manuaalisesti — A vasemmalla, B oikealla
    parser._calculate_layout = lambda: {
        list(parser.elements.keys())[0]: (100, 200),
        list(parser.elements.keys())[1]: (500, 200),
    }
    xml_output = parser.generate_xml()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)
    edge_style = next(
        c.get('style') for c in root.iter('mxCell') if c.get('edge') == '1'
    )
    assert 'exitX=1' in edge_style and 'entryX=0' in edge_style, \
        f"Expected horizontal anchors exitX=1/entryX=0, got: {edge_style}"
    print("Edge Anchors test passed")


def _assert_no_overlaps(parser, positions, margin=0):
    """Apufunktio: tarkista ettei mikään elementtipari overlapaa."""
    sizes = {eid: parser._get_element_size(parser.elements[eid]) for eid in positions}
    ids = list(positions.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ax, ay = positions[ids[i]]
            bx, by = positions[ids[j]]
            aw, ah = sizes[ids[i]]
            bw, bh = sizes[ids[j]]
            ox = min(ax + aw + margin, bx + bw + margin) - max(ax - margin, bx - margin)
            oy = min(ay + ah + margin, by + bh + margin) - max(ay - margin, by - margin)
            assert ox <= 0 or oy <= 0, \
                f"Overlap: {ids[i]} ({ax},{ay},{aw}x{ah}) vs {ids[j]} ({bx},{by},{bw}x{bh})"


def _assert_positive_coords(positions, min_val=20):
    """Apufunktio: tarkista ettei mikään elementti ole negatiivisissa koordinaateissa."""
    for eid, (x, y) in positions.items():
        assert x >= min_val, f"Element {eid} x={x} < {min_val}"
        assert y >= min_val, f"Element {eid} y={y} < {min_val}"


def test_no_negative_coordinates():
    """facet:all 12 elementtiä — kaikki positiivisissa koordinaateissa."""
    print("Testing No Negative Coordinates (facet:all)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys A"
  - asset: "Resurssi A"
  - process: "Prosessi A"
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Polku"
  - brand: "Brändi"
  - product: "Tuote"
  - organisation: "Organisaatio"
""")
    positions = parser._calculate_layout()
    _assert_positive_coords(positions)
    print("No Negative Coordinates test passed")


def test_no_negative_coords_large_tree():
    """4-tasoinen puu, 15 elementtiä — ei negatiivisia koordinaatteja."""
    print("Testing No Negative Coords (large tree)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: architecture
elements:
  - capability: "Juurikyvykkyys"
  - capability: "A"
  - capability: "B"
  - capability: "C"
  - capability: "A1"
  - capability: "A2"
  - capability: "A3"
  - capability: "B1"
  - capability: "B2"
  - capability: "C1"
  - capability: "C2"
  - capability: "C3"
  - capability: "A1x"
  - capability: "A1y"
  - capability: "A2x"
relationships:
  - "Juurikyvykkyys" -> "A": "sisältää"
  - "Juurikyvykkyys" -> "B": "sisältää"
  - "Juurikyvykkyys" -> "C": "sisältää"
  - "A" -> "A1": "sisältää"
  - "A" -> "A2": "sisältää"
  - "A" -> "A3": "sisältää"
  - "B" -> "B1": "sisältää"
  - "B" -> "B2": "sisältää"
  - "C" -> "C1": "sisältää"
  - "C" -> "C2": "sisältää"
  - "C" -> "C3": "sisältää"
  - "A1" -> "A1x": "sisältää"
  - "A1" -> "A1y": "sisältää"
  - "A2" -> "A2x": "sisältää"
""")
    positions = parser._calculate_layout()
    _assert_positive_coords(positions)
    _assert_no_overlaps(parser, positions)
    print("No Negative Coords (large tree) test passed")


def test_no_negative_coords_all_map_types():
    """Joka karttatyyppi — ei negatiivisia koordinaatteja."""
    print("Testing No Negative Coords (all map types)...")

    for map_type in ['capability', 'organisation', 'journey', 'purpose']:
        parser = EDGYParser()
        elems = "\n".join(f'  - capability: "Elem {i}"' for i in range(6))
        rels = '  - "Elem 0" -> "Elem 1": "sisältää"\n  - "Elem 0" -> "Elem 2": "sisältää"'
        parser.parse_input(f"""
map_type: {map_type}
elements:
{elems}
relationships:
{rels}
""")
        positions = parser._calculate_layout()
        _assert_positive_coords(positions, min_val=0)

    print("No Negative Coords (all map types) test passed")


def test_dynamic_width_short_name():
    """Lyhyt nimi → minimileveys 120."""
    print("Testing Dynamic Width (short name)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: identity
elements:
  - purpose: "Lyhyt"
""")
    eid = list(parser.elements.keys())[0]
    w, h = parser._get_element_size(parser.elements[eid])
    assert w >= 120, f"Short name width should be >= 120, got {w}"
    print("Dynamic Width (short name) test passed")


def test_dynamic_width_long_name():
    """Pitkä nimi (25 merkkiä) → leveys > 120."""
    print("Testing Dynamic Width (long name)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: identity
elements:
  - purpose: "Tämä on pitkä elementin nimi"
""")
    eid = list(parser.elements.keys())[0]
    w, h = parser._get_element_size(parser.elements[eid])
    assert w > 120, f"Long name (25 chars) width should be > 120, got {w}"
    print("Dynamic Width (long name) test passed")


def test_dynamic_width_capped():
    """Hyvin pitkä nimi (50+ merkkiä) → leveys max 280."""
    print("Testing Dynamic Width (capped)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: identity
elements:
  - purpose: "Tämä on erittäin pitkä elementin nimi joka ylittää kaikki rajat helposti"
""")
    eid = list(parser.elements.keys())[0]
    w, h = parser._get_element_size(parser.elements[eid])
    assert w <= 280, f"Very long name width should be <= 280, got {w}"
    print("Dynamic Width (capped) test passed")


def test_no_overlap_20_elements_facet_all():
    """20 elementtiä kaikissa faseteissa — ei overlappia."""
    print("Testing No Overlap (20 elements facet:all)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus A"
  - purpose: "Tarkoitus B"
  - content: "Sisältö A"
  - content: "Sisältö B"
  - story: "Tarina"
  - capability: "Kyvykkyys A"
  - capability: "Kyvykkyys B"
  - asset: "Resurssi A"
  - asset: "Resurssi B"
  - process: "Prosessi"
  - task: "Tehtävä A"
  - task: "Tehtävä B"
  - channel: "Kanava A"
  - channel: "Kanava B"
  - journey: "Polku"
  - brand: "Brändi A"
  - brand: "Brändi B"
  - product: "Tuote"
  - organisation: "Organisaatio A"
  - organisation: "Organisaatio B"
""")
    positions = parser._calculate_layout()
    _assert_no_overlaps(parser, positions)
    print("No Overlap (20 elements facet:all) test passed")


def test_no_overlap_capability_12_with_tree():
    """12 kyvykkyyttä 3-tasoisella puulla — ei overlappia."""
    print("Testing No Overlap (capability 12 with tree)...")
    parser = EDGYParser()
    parser.parse_input("""
map_type: capability
elements:
  - capability: "Juuri"
  - capability: "A"
  - capability: "B"
  - capability: "C"
  - capability: "D"
  - capability: "A1"
  - capability: "A2"
  - capability: "B1"
  - capability: "B2"
  - capability: "C1"
  - capability: "D1"
  - capability: "D2"
relationships:
  - "Juuri" -> "A": "sisältää"
  - "Juuri" -> "B": "sisältää"
  - "Juuri" -> "C": "sisältää"
  - "Juuri" -> "D": "sisältää"
  - "A" -> "A1": "sisältää"
  - "A" -> "A2": "sisältää"
  - "B" -> "B1": "sisältää"
  - "B" -> "B2": "sisältää"
  - "C" -> "C1": "sisältää"
  - "D" -> "D1": "sisältää"
  - "D" -> "D2": "sisältää"
""")
    positions = parser._calculate_layout()
    _assert_no_overlaps(parser, positions)
    print("No Overlap (capability 12 with tree) test passed")


def test_no_overlap_long_names():
    """12 elementtiä pitkillä nimillä (20-30 merkkiä) — ei overlappia."""
    print("Testing No Overlap (long names)...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Kestävän teknologian kumppanuus"
  - content: "Asiakaslähtöinen sisältöstrategia"
  - story: "Digitaalisen muutoksen tarina"
  - capability: "Pilvipalveluiden kehittäminen"
  - asset: "Tietovaranto ja analytiikkapalvelut"
  - process: "Ketterä tuotekehitysprosessi"
  - task: "Käyttäjäkokemuksen parantaminen"
  - channel: "Monikanavainen asiakaspalvelu"
  - journey: "Asiakkaan digitaalinen polku"
  - brand: "Luotettava teknologiabrändi"
  - product: "Älykäs analytiikkatuote"
  - organisation: "Hajautettu asiantuntijaorganisaatio"
""")
    positions = parser._calculate_layout()
    _assert_no_overlaps(parser, positions)
    print("No Overlap (long names) test passed")


def test_minimum_gap_between_elements():
    """Kaikilla elementtipareilla >= 10px väli."""
    print("Testing Minimum Gap Between Elements...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys"
  - asset: "Resurssi"
  - process: "Prosessi"
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Polku"
  - brand: "Brändi"
  - product: "Tuote"
  - organisation: "Organisaatio"
""")
    positions = parser._calculate_layout()
    sizes = {eid: parser._get_element_size(parser.elements[eid]) for eid in positions}
    ids = list(positions.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ax, ay = positions[ids[i]]
            bx, by = positions[ids[j]]
            aw, ah = sizes[ids[i]]
            bw, bh = sizes[ids[j]]
            # Tarkista ettei ole overlappia 10px marginaalilla
            ox = min(ax + aw + 10, bx + bw + 10) - max(ax - 10, bx - 10)
            oy = min(ay + ah + 10, by + bh + 10) - max(ay - 10, by - 10)
            assert ox <= 0 or oy <= 0, \
                f"Gap < 10px: {ids[i]} vs {ids[j]}"
    print("Minimum Gap Between Elements test passed")


def test_facet_columns_dont_overlap():
    """facet:all — identity-sarakkeen oikea reuna ei leikkaa architecture-sarakkeen vasenta."""
    print("Testing Facet Columns Don't Overlap...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys"
  - asset: "Resurssi"
  - process: "Prosessi"
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Polku"
""")
    positions = parser._calculate_layout()
    sizes = {eid: parser._get_element_size(parser.elements[eid]) for eid in positions}

    # Etsi sarakkeiden rajat
    id_types = {'purpose', 'content', 'story'}
    arch_types = {'capability', 'asset', 'process'}
    exp_types = {'task', 'channel', 'journey'}

    id_max_x = max(positions[eid][0] + sizes[eid][0] for eid in positions
                   if parser.elements[eid]['type'] in id_types)
    arch_min_x = min(positions[eid][0] for eid in positions
                     if parser.elements[eid]['type'] in arch_types)
    arch_max_x = max(positions[eid][0] + sizes[eid][0] for eid in positions
                     if parser.elements[eid]['type'] in arch_types)
    exp_min_x = min(positions[eid][0] for eid in positions
                    if parser.elements[eid]['type'] in exp_types)

    assert id_max_x < arch_min_x, \
        f"Identity right edge ({id_max_x}) overlaps Architecture left edge ({arch_min_x})"
    assert arch_max_x < exp_min_x, \
        f"Architecture right edge ({arch_max_x}) overlaps Experience left edge ({exp_min_x})"
    print("Facet Columns Don't Overlap test passed")


def test_page_size_fits_content():
    """Dynaaminen sivukoko kattaa kaikki elementit marginaalilla."""
    print("Testing Page Size Fits Content...")
    parser = EDGYParser()
    parser.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
  - content: "Sisältö"
  - story: "Tarina"
  - capability: "Kyvykkyys"
  - asset: "Resurssi"
  - process: "Prosessi"
  - task: "Tehtävä"
  - channel: "Kanava"
  - journey: "Polku"
  - brand: "Brändi"
  - product: "Tuote"
  - organisation: "Organisaatio"
""")
    xml_output = parser.generate_xml()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    page_w = int(root.get('pageWidth', '1200'))
    page_h = int(root.get('pageHeight', '900'))

    # Tarkista kaikkien elementtien max-koordinaatit
    max_x, max_y = 0, 0
    for cell in root.iter('mxCell'):
        geom = cell.find('mxGeometry')
        if geom is not None and cell.get('vertex') == '1':
            x = int(geom.get('x', '0'))
            y = int(geom.get('y', '0'))
            w = int(geom.get('width', '0'))
            h = int(geom.get('height', '0'))
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

    assert page_w >= max_x, f"pageWidth ({page_w}) < max element right edge ({max_x})"
    assert page_h >= max_y, f"pageHeight ({page_h}) < max element bottom edge ({max_y})"
    print("Page Size Fits Content test passed")


def test_distributed_edge_anchors():
    """3 edgeä samaan elementtiin — ankkuripisteet hajautettu (eivät kaikki 0.5)."""
    print("Testing Distributed Edge Anchors...")
    parser = EDGYParser()
    parser.parse_input("""
facet: architecture
elements:
  - capability: "Keskus"
  - capability: "A"
  - capability: "B"
  - capability: "C"
relationships:
  - "A" -> "Keskus": "vaatii"
  - "B" -> "Keskus": "vaatii"
  - "C" -> "Keskus": "vaatii"
""")
    xml_output = parser.generate_xml()
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_output)

    entry_ys = []
    for cell in root.iter('mxCell'):
        if cell.get('edge') == '1':
            style = cell.get('style', '')
            import re
            m = re.search(r'entryY=([0-9.]+)', style)
            if m:
                entry_ys.append(float(m.group(1)))

    # Vähintään 2 eri entryY-arvoa (hajautettu, ei kaikki 0.5)
    unique_ys = set(entry_ys)
    assert len(unique_ys) >= 2, \
        f"Expected distributed entry anchors, got all same: {entry_ys}"
    print("Distributed Edge Anchors test passed")


def test_core_link_pair_validation():
    """Ydinlinkin verbi hyväksytään vain sallituilla (lähde, kohde) -pareilla"""
    print("Testing Core Link Pair Validation...")

    parser = EDGYParser()
    input_text = """
facet: architecture
elements:
  - organisation: "Organisaatio"
  - asset: "Järjestelmä"
  - process: "Prosessi"
  - product: "Tuote"
  - capability: "Kyvykkyys"
relationships:
  - "Organisaatio" -> "Järjestelmä": "omistaa"
  - "Prosessi" -> "Järjestelmä": "vaatii"
  - "Tuote" -> "Kyvykkyys": "requires"
  - "Organisaatio" -> "Prosessi": "suorittaa"
"""
    parser.parse_input(input_text)
    kinds = {r['label']: r['kind'] for r in parser.relationships}
    assert kinds['omistaa'] == 'influence', f"organisation → asset 'omistaa' is not a core link: {kinds}"
    assert kinds['vaatii'] == 'link', f"process → asset 'vaatii' is a core link: {kinds}"
    assert kinds['requires'] == 'link', f"product → capability 'requires' is a core link: {kinds}"
    assert kinds['suorittaa'] == 'link'
    wrong = [w for w in parser.warnings if 'Ydinlinkki' in w]
    assert len(wrong) == 1 and "'omistaa'" in wrong[0], f"Exactly one wrong-pair warning expected, got: {parser.warnings}"

    import xml.etree.ElementTree as ET
    root = ET.fromstring(parser.generate_xml())
    styles = {c.get('value'): c.get('style') for c in root.iter('mxCell') if c.get('edge') == '1'}
    assert 'dashed=1' in styles['omistaa'] and 'endArrow=open' in styles['omistaa']
    assert 'endArrow=classic' in styles['vaatii'] and 'dashed' not in styles['vaatii']

    print("Core Link Pair Validation test passed")


def test_influence_vocabulary():
    """Influence-sanaston verbit hyväksytään ilman varoitusta; tuntematon verbi varoittaa"""
    print("Testing Influence Vocabulary...")

    parser = EDGYParser()
    input_text = """
facet: all
elements:
  - process: "Prosessi"
  - outcome: "Mittari"
  - purpose: "Tarkoitus"
  - capability: "Kyvykkyys"
  - organisation: "Organisaatio"
relationships:
  - "Prosessi" -> "Mittari": "tuottaa"
  - "Mittari" -> "Tarkoitus": "measures"
  - "Kyvykkyys" -> "Tarkoitus": "edistää"
  - "Organisaatio" -> "Kyvykkyys": "tekee"
"""
    parser.parse_input(input_text)
    kinds = {r['label']: r['kind'] for r in parser.relationships}
    assert all(kinds[v] == 'influence' for v in ('tuottaa', 'measures', 'edistää', 'tekee')), kinds
    vocab_warnings = [w for w in parser.warnings if 'sanastossa' in w]
    assert len(vocab_warnings) == 1 and "'tekee'" in vocab_warnings[0], \
        f"Only the unknown verb 'tekee' should warn, got: {parser.warnings}"

    print("Influence Vocabulary test passed")


def test_errors_list_for_invalid_header():
    """Tuntematon facet/map_type kirjataan errors-listaan (generator exit 2)"""
    print("Testing Errors List For Invalid Header...")

    parser = EDGYParser()
    parser.parse_input("""
facet: all-facets
elements:
  - purpose: "Tarkoitus"
""")
    assert parser.errors and 'all-facets' in parser.errors[0], f"Expected an error entry, got: {parser.errors}"
    assert 'sallitut' in parser.errors[0], "Error should list the allowed values"

    ok = EDGYParser()
    ok.parse_input("""
facet: all
elements:
  - purpose: "Tarkoitus"
""")
    assert ok.errors == [], f"Valid header must not produce errors: {ok.errors}"

    print("Errors List For Invalid Header test passed")


def test_generated_vocabulary_module():
    """Sanasto tulee generoidusta moduulista ja kattaa 24 ydinlinkkiä neljällä kielellä"""
    print("Testing Generated Vocabulary Module...")

    from edgy_core_links import CORE_LINKS, CORE_LINK_PAIRS, INFLUENCE_RELATIONSHIPS, core_link_pairs
    assert len(CORE_LINKS) == 24, f"Expected 24 core links, got {len(CORE_LINKS)}"
    pairs = {(s, t) for s, t, _, _ in CORE_LINKS}
    assert len(pairs) == 24, "Every core link must be a distinct (source, target) pair"
    assert core_link_pairs('requires') == {('capability', 'asset'), ('process', 'asset'), ('product', 'capability')}
    assert core_link_pairs('erscheint in') == {('brand', 'journey'), ('product', 'journey')}
    assert core_link_pairs('osa') == {('task', 'journey')}, "Alias 'osa' must map to on osa"
    for verb in ('mahdollistaa', 'enables', 'permet', 'ermöglicht', 'tuottaa', 'measures'):
        assert verb in INFLUENCE_RELATIONSHIPS, f"'{verb}' missing from influence vocabulary"
    assert not (set(CORE_LINK_PAIRS) & INFLUENCE_RELATIONSHIPS), \
        "A verb must not be both a core-link verb and an influence verb"

    print("Generated Vocabulary Module test passed")


def main():
    """Run all tests"""
    print("Running EDGY Diagram Generator Tests...\n")

    try:
        test_identity_facet()
        test_architecture_facet()
        test_experience_facet()
        test_full_edgy_map()
        test_ambiguous_names()
        test_all_facet_layout_order()
        test_invalid_relationship()
        test_prefix_matching()
        test_intersection_element_positions()
        test_tree_relationships()
        test_people_base_element()
        test_map_type_journey()
        test_map_type_capability()
        test_labels_tags_metrics()
        test_core_link_styles()
        test_edge_styles()
        test_xml_entity_escaping()
        test_coordinate_grid_snapping()
        test_unmapped_edge_skipped()
        test_invalid_facet()
        test_invalid_map_type()
        test_unknown_element_type()
        test_empty_input()
        test_core_link_direction_warning()
        test_layout_y_spacing()
        test_journey_map_x_spacing()
        test_french_core_links()
        test_german_core_links()
        test_french_flow_and_tree()
        test_german_flow_and_tree()
        test_no_box_overlap()
        test_tree_subtree_widths()
        test_radial_purpose_scaling()
        test_edge_anchors_horizontal()
        # Vaihe 5: uudet layout-laadun testit
        test_no_negative_coordinates()
        test_no_negative_coords_large_tree()
        test_no_negative_coords_all_map_types()
        test_dynamic_width_short_name()
        test_dynamic_width_long_name()
        test_dynamic_width_capped()
        test_no_overlap_20_elements_facet_all()
        test_no_overlap_capability_12_with_tree()
        test_no_overlap_long_names()
        test_minimum_gap_between_elements()
        test_facet_columns_dont_overlap()
        test_page_size_fits_content()
        test_distributed_edge_anchors()
        # Sprint 1: sanasto ja parivalidointi
        test_core_link_pair_validation()
        test_influence_vocabulary()
        test_errors_list_for_invalid_header()
        test_generated_vocabulary_module()

        print("\nAll tests passed successfully")

    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
