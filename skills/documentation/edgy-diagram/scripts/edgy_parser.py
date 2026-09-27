#!/usr/bin/env python3
"""
EDGY Parser - Jäsennä EDGY-notaatiota ja generoi draw.io XML

Käyttää virallista EDGY 23 -väripalettia ja elementtimuotoja.
"""

import html
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

# ─── Relaatiotyypit: linkki / tietovirtanuoli / puu / vaikutusviiva ────────
#
# EDGY 23 erottaa kolme relaatiotyyppiä + oletus:
#
# 1. LINKKI (link) — nimetty rakenteellinen yhteys kahden elementin välillä
#    EDGY 23 määrittelee 24 virallista ydinlinkkiä (core links).
#    Tyyli: yhtenäinen viiva, suuntanuoli kohdepäässä
#
# 2. TIETOVIRTANUOLI (flow) — konkreettinen data/tieto/arvo/materiaali siirtyy
#    Käyttö: kun A tuottaa tai siirtää dataa, tietoa tai arvoa B:lle
#    Tyyli: yhtenäinen viiva, avoin nuolenpää kohdepäässä
#
# 3. PUU (tree) — hierarkkinen osa/kokonaisuus -suhde saman tyypin elementtien välillä
#    Käyttö: dekompositio, portfoliot, organisaatiohierarkiat
#    Tyyli: yhtenäinen viiva, ei nuolenpäätä, T-haarautuminen
#
# 4. VAIKUTUSVIIVA (influence) — kaikki muut relaatiot
#    Käyttö: A ohjaa, mahdollistaa, tuottaa tai mittaa B:tä; sanasto
#    INFLUENCE_RELATIONSHIPS. Kun mikään 24 ydinlinkistä ei sovi parille,
#    käytetään influence-verbiä — uutta Link-relaatiota ei keksitä.
#    Tyyli: katkoviiva, avoin nuolenpää

# ─── Viralliset EDGY 23 ydinlinkit (24 kpl) ──────────────────────────────
# Lähde: EDGY 23 Language Foundations, s. 57
# Kukin linkki on nimetty verbi joka ilmaisee suunnan: lähde → kohde
# Kaksikielinen: englannin verbi → suomen verbi

# Ydinlinkit, sallitut parit ja influence-sanasto tulevat generoidusta
# moduulista edgy_core_links.py (lähde: skills/_shared/edgy-core-links.yaml).
from edgy_core_links import (  # noqa: E402
    EDGY_CORE_LINKS,
    CORE_LINK_PAIRS,
    INFLUENCE_RELATIONSHIPS,
    core_link_pairs,
)

# Flow relationships → open arrowhead (data/value flows concretely)
# Supported in FI, EN, FR, DE
FLOW_RELATIONSHIPS = {
    'virtaa', 'siirtyy', 'tuottaa dataa', 'palauttaa',           # FI
    'flows', 'transfers', 'sends', 'receives', 'produces data', 'returns',  # EN
    'circule', 'transfère', 'produit des données', 'retourne',   # FR
    'fließt', 'überträgt', 'erzeugt Daten', 'gibt zurück',       # DE
}

# Tree hierarchy relationships → solid line, no arrowhead
# Supported in FI, EN, FR, DE
TREE_RELATIONSHIPS = {
    'sisältää', 'koostuu', 'jakaantuu',                           # FI
    'contains', 'decomposes', 'comprises',                         # EN
    'contient', 'comprend', 'se décompose',                        # FR
    'enthält', 'umfasst', 'zerlegt sich',                          # DE
}

# Viralliset EDGY 23 -värit (SVG stencileistä)
EDGY_COLORS = {
    # Identity facet - vihreä
    'purpose':      {'fill': '#80ffb7', 'stroke': '#fff'},
    'content':      {'fill': '#80ffb7', 'stroke': '#fff'},
    'story':        {'fill': '#80ffb7', 'stroke': '#fff'},
    # Architecture facet - sininen
    'capability':   {'fill': '#a6c0ff', 'stroke': '#fff'},
    'asset':        {'fill': '#a6c0ff', 'stroke': '#fff'},
    'process':      {'fill': '#a6c0ff', 'stroke': '#fff'},
    # Experience facet - pinkki
    'task':         {'fill': '#ff99bd', 'stroke': '#fff'},
    'channel':      {'fill': '#ff99bd', 'stroke': '#fff'},
    'journey':      {'fill': '#ff99bd', 'stroke': '#fff'},
    # Intersection-elementit
    'brand':        {'fill': '#ffd580', 'stroke': '#fff'},
    'product':      {'fill': '#e599ff', 'stroke': '#fff'},
    'organisation': {'fill': '#80eaff', 'stroke': '#fff'},
    # Peruselementit (Base Elements) — valkoinen täyttö, musta reunus
    'people':       {'fill': '#ffffff', 'stroke': '#262626'},
    'activity':     {'fill': '#ffffff', 'stroke': '#262626'},
    'object':       {'fill': '#ffffff', 'stroke': '#262626'},
    'outcome':      {'fill': '#ffffff', 'stroke': '#262626'},
}

# Muodot elementtityypeittäin (virallisista SVG-stencileistä)
# rounded_rect = pyöristetty suorakaide (path d="m17,1h88c8.8...")
# rect = suorakaide
# pentagon = nuolimuoto (polygon points)
EDGY_SHAPES = {
    'purpose':      'rounded_rect',
    'capability':   'rounded_rect',
    'task':         'rounded_rect',
    'outcome':      'rounded_rect',
    'content':      'rect',
    'asset':        'rect',
    'channel':      'rect',
    'brand':        'rect',
    'product':      'rect',
    'organisation': 'rect',
    'object':       'rect',
    'people':       'person',
    'story':        'pentagon',
    'process':      'pentagon',
    'journey':      'pentagon',
    'activity':     'pentagon',
}

# Facet-ryhmittely
IDENTITY_ELEMENTS = {'purpose', 'content', 'story'}
ARCHITECTURE_ELEMENTS = {'capability', 'asset', 'process'}
EXPERIENCE_ELEMENTS = {'task', 'channel', 'journey'}
INTERSECTION_ELEMENTS = {'brand', 'product', 'organisation'}
BASE_ELEMENTS = {'people', 'activity', 'outcome', 'object'}

# Validointivakiot
VALID_FACETS = {'identity', 'architecture', 'experience', 'all'}
VALID_MAP_TYPES = {
    # Layout: tree decomposition
    'capability', 'organisation', 'outcome',
    # Layout: horizontal sequence (pentagon row)
    'journey', 'activity', 'process',
    # Layout: hub-and-spoke (central element + satellites)
    'purpose', 'brand', 'product', 'object',
    # Layout: grid (rows + columns)
    'asset', 'channel', 'content', 'people', 'story', 'task',
}

# Karttatyyppi → layout-strategia
MAP_TYPE_LAYOUT = {
    'capability': 'grid_tree',
    'organisation': 'tree',
    'outcome': 'grid_tree',
    'journey': 'sequence',
    'activity': 'sequence',
    'process': 'sequence',
    'purpose': 'hub_spoke',
    'brand': 'hub_spoke',
    'product': 'hub_spoke',
    'object': 'hub_spoke',
    'asset': 'grid',
    'channel': 'grid',
    'content': 'grid',
    'people': 'grid',
    'story': 'grid',
    'task': 'grid',
}
ALL_ELEMENT_TYPES = (IDENTITY_ELEMENTS | ARCHITECTURE_ELEMENTS |
                     EXPERIENCE_ELEMENTS | INTERSECTION_ELEMENTS | BASE_ELEMENTS)

# Ydinlinkkien parivalidointi: verbi → {(lähdetyyppi, kohdetyyppi), ...}
# Sama verbi voi olla sallittu usealle parille (esim. requires/vaatii:
# capability → asset, process → asset, product → capability).
CORE_LINK_DIRECTIONS = CORE_LINK_PAIRS

# Relaatiotyypit (kind) — määräävät reunan tyylin
RELATIONSHIP_KINDS = ('link', 'flow', 'tree', 'influence')


class EDGYParser:
    def __init__(self):
        self.elements = {}
        self.relationships = []
        self.warnings = []   # ei-fataalit huomautukset (tulostetaan aina)
        self.errors = []     # syötevirheet, joiden kanssa generointi ei ole luotettava
        self.facet = "identity"  # oletus
        self.map_type = None     # None = facet-pohjainen oletus

    def parse_input(self, input_text: str) -> None:
        """Jäsennä käyttäjän syöte EDGY-elementeiksi"""
        lines = input_text.strip().split('\n')

        current_section = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Tunnista osiot
            if line.startswith('facet:'):
                facet_value = line.split(':')[1].strip().lower()
                if facet_value not in VALID_FACETS:
                    msg = (f"Tuntematon facet '{facet_value}' (sallitut: "
                           f"{', '.join(sorted(VALID_FACETS))}), käytetään oletusta 'identity'")
                    self.warnings.append(msg)
                    self.errors.append(msg)
                    facet_value = 'identity'
                self.facet = facet_value
                continue
            elif line.startswith('map_type:'):
                map_type_value = line.split(':')[1].strip().lower()
                if map_type_value not in VALID_MAP_TYPES:
                    msg = (f"Tuntematon map_type '{map_type_value}' (sallitut: "
                           f"{', '.join(sorted(VALID_MAP_TYPES))}), ohitetaan")
                    self.warnings.append(msg)
                    self.errors.append(msg)
                    map_type_value = None
                self.map_type = map_type_value
                continue
            elif line.startswith('elements:'):
                current_section = 'elements'
                continue
            elif line.startswith('relationships:'):
                current_section = 'relationships'
                continue

            # Jäsennä elementit
            # Tukee: - tyyppi: "nimi" [tag1, tag2] {metriikka: arvo}
            if current_section == 'elements' and line.startswith('- '):
                element_match = re.match(
                    r'-\s*(\w+):\s*"(.+?)"'
                    r'(?:\s*\[([^\]]*)\])?'       # valinnainen [tagit]
                    r'(?:\s*\{([^\}]*)\})?',       # valinnainen {metriikat}
                    line
                )
                if element_match:
                    element_type = element_match.group(1)
                    element_value = element_match.group(2)
                    tags_str = element_match.group(3)
                    metrics_str = element_match.group(4)

                    if element_type not in ALL_ELEMENT_TYPES:
                        self.warnings.append(f"Tuntematon elementtityyppi '{element_type}', käytetään oletustyyliä")

                    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
                    metrics = {}
                    if metrics_str:
                        for pair in metrics_str.split(','):
                            if ':' in pair:
                                k, v = pair.split(':', 1)
                                metrics[k.strip()] = v.strip()

                    element_id = f"{element_type}{len(self.elements) + 1}"
                    self.elements[element_id] = {
                        'type': element_type,
                        'value': element_value,
                        'id': element_id,
                        'tags': tags,
                        'metrics': metrics,
                    }

            # Jäsennä suhteet
            elif current_section == 'relationships' and line.startswith('- '):
                # Kokeile ensin lainausmerkeillä
                rel_match = re.match(r'-\s*"(.+?)"\s*->\s*"(.+?)":\s*"(.+)"', line)
                if not rel_match:
                    # Kokeile ilman lainausmerkkejä
                    rel_match = re.match(r'-\s*(\w+)\s*->\s*(\w+):\s*"(.+)"', line)

                if rel_match:
                    source = rel_match.group(1)
                    target = rel_match.group(2)
                    label = rel_match.group(3)

                    # Etsi elementtien IDt
                    source_id = self._find_element_id_by_value(source)
                    target_id = self._find_element_id_by_value(target)

                    if source_id and target_id:
                        kind = self._classify_relationship(
                            label, source_id, target_id
                        )
                        self.relationships.append({
                            'source': source_id,
                            'target': target_id,
                            'label': label,
                            'kind': kind,
                        })

    def _classify_relationship(self, label: str, source_id: str, target_id: str) -> str:
        """Luokittele relaatio tyyppiin link / flow / tree / influence ja
        validoi ydinlinkin (lähdetyyppi, kohdetyyppi) -pari EDGY 23 -spesifikaation
        mukaan.

        - Ydinlinkin verbi sallitulla parilla → 'link'
        - Ydinlinkin verbi väärällä parilla → varoitus, piirretään 'influence'
          (katkoviiva), koska pari ei ole virallinen ydinlinkki
        - Flow-/tree-sanaston verbi → 'flow' / 'tree'
        - Influence-sanaston verbi → 'influence'
        - Tuntematon verbi → varoitus, 'influence'
        """
        label_lower = label.lower().strip()
        source_type = self.elements.get(source_id, {}).get('type', '')
        target_type = self.elements.get(target_id, {}).get('type', '')

        allowed = core_link_pairs(label_lower)
        if allowed:
            if (source_type, target_type) in allowed:
                return 'link'
            expected = ', '.join(f"{a} → {b}" for a, b in sorted(allowed))
            self.warnings.append(
                f"Ydinlinkki '{label}': sallittu {expected}; "
                f"saatu {source_type} → {target_type} — ei virallinen ydinlinkki, "
                f"piirretään influence-tyylillä (katkoviiva)"
            )
            return 'influence'
        if label_lower in FLOW_RELATIONSHIPS:
            return 'flow'
        if label_lower in TREE_RELATIONSHIPS:
            return 'tree'
        if label_lower in INFLUENCE_RELATIONSHIPS:
            return 'influence'
        self.warnings.append(
            f"Relaatioverbi '{label}' ({source_type} → {target_type}) ei ole "
            f"ydinlinkki-, flow-, tree- eikä influence-sanastossa — piirretään "
            f"influence-tyylillä. Käytä sanaston verbiä (ks. SKILL.md, Influence verbs)."
        )
        return 'influence'

    def _validate_relationship_label(self, label: str, source_id: str, target_id: str) -> None:
        """Yhteensopivuus: validoi ydinlinkin pari (varoitus warnings-listaan)."""
        self._classify_relationship(label, source_id, target_id)

    def _find_element_id_by_value(self, value: str) -> str:
        """Etsi elementin ID sen arvolla.

        Hakujärjestys:
        1. Tarkka osuma (case-insensitive)
        2. Alkuosa-osuma (ennen ' - ' -erotinta)
        3. Case-insensitive substring-osuma (vain jos yksiselitteinen)
        4. Tyyppi-osuma (vain jos tyypillä on tasan yksi elementti)
        """
        value_lower = value.lower()

        # 1. Tarkka osuma
        for element_id, element in self.elements.items():
            if element['value'].lower() == value_lower:
                return element_id

        # 2. Alkuosa-osuma (ennen " - " -erotinta)
        for element_id, element in self.elements.items():
            prefix = element['value'].split(' - ')[0].strip()
            if prefix.lower() == value_lower:
                return element_id

        # 3. Case-insensitive substring-osuma (vain yksiselitteiset)
        substring_matches = [
            eid for eid, elem in self.elements.items()
            if value_lower in elem['value'].lower()
        ]
        if len(substring_matches) == 1:
            return substring_matches[0]

        # 4. Tyyppi-osuma (vain jos tasan yksi elementti kyseistä tyyppiä)
        type_matches = [
            eid for eid, elem in self.elements.items()
            if elem['type'] == value
        ]
        if len(type_matches) == 1:
            return type_matches[0]
        elif len(type_matches) > 1:
            self.warnings.append(
                f"Ambiguousi tyyppi-osuma '{value}': {len(type_matches)} elementtiä, "
                f"käytä tarkkaa nimeä relaatiossa"
            )

        return ""

    def _build_display_value(self, element: dict) -> str:
        """Rakenna elementin näyttöarvo HTML-muodossa labeleineen."""
        name = element['value']
        tags = element.get('tags', [])
        metrics = element.get('metrics', {})

        if not tags and not metrics:
            return html.escape(name)

        # Metriikan värikoodaus
        metric_colors = {
            'good': '#2e7d32', 'hyvä': '#2e7d32',
            'ok': '#f57f17', 'keskiverto': '#f57f17',
            'bad': '#c62828', 'huono': '#c62828',
            'high': '#c62828', 'korkea': '#c62828',
            'low': '#2e7d32', 'matala': '#2e7d32',
        }

        label_parts = []
        for tag in tags:
            label_parts.append(html.escape(tag))
        for k, v in metrics.items():
            color = metric_colors.get(v.lower(), '#666')
            label_parts.append(f'<font color="{color}">{html.escape(k)}: {html.escape(v)}</font>')

        labels_html = ' | '.join(label_parts)
        return f'<b>{html.escape(name)}</b><br><font style="font-size:9px">{labels_html}</font>'

    def _get_edge_style(self, label: str, kind: str = None) -> str:
        """Palauta relaation draw.io-tyyli relaatiotyypin mukaan.

        EDGY 23 relaatiotyypit:
        - Linkki (core link): nimetty yhteys → yhtenäinen viiva, suuntanuoli
        - Tietovirtanuoli (flow): data/arvo siirtyy → avoin nuolenpää
        - Puu (tree): hierarkia → yhtenäinen viiva, ei nuolenpäätä
        - Vaikutusviiva (influence): ohjaa/mahdollistaa → katkoviiva, avoin nuolenpää

        `kind` tulee _classify_relationship():sta; jos sitä ei ole annettu,
        luokitellaan pelkän verbin perusteella (ilman parivalidointia).
        """
        if kind is None:
            label_lower = label.lower().strip()
            if label_lower in EDGY_CORE_LINKS:
                kind = 'link'
            elif label_lower in FLOW_RELATIONSHIPS:
                kind = 'flow'
            elif label_lower in TREE_RELATIONSHIPS:
                kind = 'tree'
            else:
                kind = 'influence'
        base = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;html=1;"
            "jumpStyle=arc;jumpSize=8;orthogonalLoop=1;"
            "labelBackgroundColor=#ffffff;labelBorderColor=none;"
        )

        if kind == 'link':
            return base + "endArrow=classic;endFill=1;"
        elif kind == 'flow':
            return base + "endArrow=open;endFill=0;strokeWidth=2;"
        elif kind == 'tree':
            return base + "endArrow=none;"
        else:
            return base + "endArrow=open;endFill=0;dashed=1;"

    # Dynaamiset mitoitusvakiot
    _CHAR_WIDTH = 8      # arvioitu merkin leveys fontStyle=1;fontSize=14 bold
    _WIDTH_PADDING = 20  # sisämarginaali molemmin puolin
    _MAX_WIDTH = 280     # leveimmän elementin yläraja

    def _get_element_size(self, element: dict) -> Tuple[int, int]:
        """Palauta elementin (leveys, korkeus) muodon ja tekstipituuden mukaan.

        Leveys skaalautuu tekstin pituuden mukaan:
        - min 120 (rect/rounded_rect), 140 (pentagon), 60 (person)
        - max 280
        - pyöristetty ylös 10:n kerrannaiseksi (grid snap)
        """
        import math
        shape = EDGY_SHAPES.get(element['type'], 'rect')

        # Muotokohtainen minimikoko
        if shape == 'pentagon':
            min_w, h = 140, 60
        elif shape == 'person':
            min_w, h = 60, 80
        else:
            min_w, h = 120, 60

        # Tekstipohjainen leveys
        text_len = len(element.get('value', ''))
        text_w = text_len * self._CHAR_WIDTH + self._WIDTH_PADDING
        w = max(min_w, min(text_w, self._MAX_WIDTH))

        # Pyöristä ylös 10:n kerrannaiseksi
        w = int(math.ceil(w / 10) * 10)

        if element.get('tags') or element.get('metrics'):
            h += 20
        return w, h

    def _compute_edge_anchors(self, src_pos, src_size, tgt_pos, tgt_size) -> str:
        """Valitse exit/entry-kiinnittimet sen mukaan missä target on suhteessa sourceen.

        Palauttaa stringin joka voidaan liittää edge-tyylin perään, esim.
        'exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;'.
        """
        if src_pos is None or tgt_pos is None:
            return ""
        sx, sy = src_pos
        tx, ty = tgt_pos
        sw, sh = src_size
        tw, th = tgt_size
        # Source/target keskipisteet
        scx, scy = sx + sw / 2, sy + sh / 2
        tcx, tcy = tx + tw / 2, ty + th / 2
        dx, dy = tcx - scx, tcy - scy

        if abs(dx) >= abs(dy):
            # Vaakasuuntaa enemmän — käytä sivuja
            if dx >= 0:
                exit_x, entry_x = 1, 0
            else:
                exit_x, entry_x = 0, 1
            exit_y = entry_y = 0.5
        else:
            # Pystysuuntaa enemmän — käytä ylä-/alareunaa
            if dy >= 0:
                exit_y, entry_y = 1, 0
            else:
                exit_y, entry_y = 0, 1
            exit_x = entry_x = 0.5

        return (
            f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
            f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;"
        )

    def _resolve_collisions(self, positions: Dict[str, Tuple[int, int]]) -> None:
        """Sweep-and-Compact -törmäysresoluutio.

        Kaksi lajiteltua sweep-vaihetta (vaaka + pysty) varmistavat
        monotonisen konvergenssin: elementtejä työnnetään vain positiiviseen
        suuntaan, jolloin ketjureaktiot eivät tuota negatiivisia koordinaatteja.
        """
        if len(positions) < 2:
            return

        MARGIN = 20
        MAX_ITERATIONS = 10
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in positions}

        def _y_bands_overlap(a, b):
            """Tarkista limittävätkö kahden elementin y-alueet."""
            ay, ah = positions[a][1], sizes[a][1]
            by, bh = positions[b][1], sizes[b][1]
            return ay < by + bh + MARGIN and by < ay + ah + MARGIN

        def _x_bands_overlap(a, b):
            """Tarkista limittävätkö kahden elementin x-alueet."""
            ax, aw = positions[a][0], sizes[a][0]
            bx, bw = positions[b][0], sizes[b][0]
            return ax < bx + bw + MARGIN and bx < ax + aw + MARGIN

        for _iteration in range(MAX_ITERATIONS):
            moved = False

            # Vaakasweep: lajittele x:n mukaan, ryhmittele y-kaistaan
            ids_by_x = sorted(positions.keys(), key=lambda e: positions[e][0])
            for i in range(len(ids_by_x)):
                for j in range(i + 1, len(ids_by_x)):
                    a, b = ids_by_x[i], ids_by_x[j]
                    if not _y_bands_overlap(a, b):
                        continue
                    ax = positions[a][0]
                    aw = sizes[a][0]
                    bx = positions[b][0]
                    min_x = ax + aw + MARGIN
                    if bx < min_x:
                        positions[b] = (min_x, positions[b][1])
                        moved = True

            # Pystysweep: lajittele y:n mukaan, ryhmittele x-kaistaan
            ids_by_y = sorted(positions.keys(), key=lambda e: positions[e][1])
            for i in range(len(ids_by_y)):
                for j in range(i + 1, len(ids_by_y)):
                    a, b = ids_by_y[i], ids_by_y[j]
                    if not _x_bands_overlap(a, b):
                        continue
                    ay = positions[a][1]
                    ah = sizes[a][1]
                    by = positions[b][1]
                    min_y = ay + ah + MARGIN
                    if by < min_y:
                        positions[b] = (positions[b][0], min_y)
                        moved = True

            if not moved:
                return

    def _normalize_to_canvas(self, positions: Dict[str, Tuple[int, int]]) -> None:
        """Siirrä kaikki elementit positiiviseen canvas-tilaan.

        Varmistaa että min_x >= MARGIN ja min_y >= MARGIN.
        """
        MARGIN = 40
        if not positions:
            return
        min_x = min(x for x, y in positions.values())
        min_y = min(y for x, y in positions.values())
        shift_x = MARGIN - min_x if min_x < MARGIN else 0
        shift_y = MARGIN - min_y if min_y < MARGIN else 0
        if shift_x or shift_y:
            for eid in positions:
                x, y = positions[eid]
                positions[eid] = (x + shift_x, y + shift_y)

    def _snap_to_grid(self, positions: Dict[str, Tuple[int, int]]) -> None:
        """Pyöristä kaikki koordinaatit lähimpään 10:n kerrannaiseen."""
        for eid in positions:
            x, y = positions[eid]
            positions[eid] = (round(x / 10) * 10, round(y / 10) * 10)

    def _get_element_style(self, element_type: str) -> str:
        """Palauta EDGY-elementin draw.io-tyyli virallisen notaation mukaan"""
        colors = EDGY_COLORS.get(element_type, {'fill': '#ffffff', 'stroke': '#262626'})
        shape = EDGY_SHAPES.get(element_type, 'rect')

        fill = colors['fill']
        stroke = colors['stroke']

        if shape == 'rounded_rect':
            return (
                f"rounded=1;whiteSpace=wrap;html=1;"
                f"fillColor={fill};strokeColor=#FFFFFF;strokeWidth=2;"
                f"arcSize=10;verticalAlign=middle;fontStyle=1;fontSize=14;"
            )
        elif shape == 'pentagon':
            return (
                f"shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;"
                f"whiteSpace=wrap;html=1;"
                f"fillColor={fill};strokeColor=#FFFFFF;strokeWidth=2;"
                f"verticalAlign=middle;fontStyle=1;fontSize=14;"
            )
        elif shape == 'person':
            return (
                f"shape=mxgraph.basic.person;whiteSpace=wrap;html=1;"
                f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
                f"verticalAlign=middle;fontStyle=1;fontSize=12;"
            )
        else:  # rect
            return (
                f"whiteSpace=wrap;html=1;"
                f"fillColor={fill};strokeColor=#FFFFFF;strokeWidth=2;"
                f"verticalAlign=middle;fontStyle=1;fontSize=14;"
            )

    def generate_xml(self) -> str:
        """Generoi draw.io XML EDGY-elementeistä. Sivukoko skaalautuu sisällön mukaan."""
        import math as _math

        # Laske layout ensin dynaamisen sivukoon laskentaa varten
        positions = self._calculate_layout()
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in self.elements}

        # Dynaaminen sivukoko: bounding box + marginaali
        if positions:
            max_x = max(positions[eid][0] + sizes[eid][0] for eid in positions)
            max_y = max(positions[eid][1] + sizes[eid][1] for eid in positions)
            page_width = max(1200, int(_math.ceil((max_x + 80) / 100) * 100))
            page_height = max(900, int(_math.ceil((max_y + 80) / 100) * 100))
        else:
            page_width, page_height = 1200, 900

        root = ET.Element("mxGraphModel", {
            "dx": str(page_width + 240),
            "dy": str(page_height - 24),
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(page_width),
            "pageHeight": str(page_height),
            "math": "0",
            "shadow": "0"
        })

        # Luo root ja oletuskerros
        mx_root = ET.SubElement(root, "root")
        ET.SubElement(mx_root, "mxCell", {"id": "0"})
        ET.SubElement(mx_root, "mxCell", {"id": "1", "parent": "0"})

        # Lisää elementit (positions laskettu jo yllä dynaamiselle sivukoolle)
        element_id = 2  # Aloita ID:stä 2 (0 ja 1 varattu)
        element_mapping = {}

        for idx, (elem_id, element) in enumerate(self.elements.items()):
            style = self._get_element_style(element['type'])
            w, h = self._get_element_size(element)
            width, height = str(w), str(h)

            x, y = positions.get(elem_id, (100 + idx * 160, 100))
            x = int(round(x))
            y = int(round(y))

            display_value = self._build_display_value(element)

            cell_attrs = {
                "id": str(element_id),
                "value": display_value,
                "style": style,
                "vertex": "1",
                "parent": "1"
            }
            # Kaikki cellit ovat root:n suoria lapsia (EI parent_cell:n lapsia)
            cell = ET.SubElement(mx_root, "mxCell", cell_attrs)

            # Lisää geometria
            ET.SubElement(cell, "mxGeometry", {
                "x": str(x),
                "y": str(y),
                "width": width,
                "height": height,
                "as": "geometry"
            })

            element_mapping[elem_id] = str(element_id)
            element_id += 1

        # Lisää suhteet hajautetuilla ankkuripisteillä
        # Kerää ensin kaikki edget per elementti per sivu → hajota ankkurit tasaisesti
        from collections import defaultdict
        outgoing_by_side = defaultdict(list)  # (elem_id, side) → [rel_index, ...]
        incoming_by_side = defaultdict(list)

        valid_rels = []
        for rel_idx, relationship in enumerate(self.relationships):
            src_mapped = element_mapping.get(relationship['source'])
            tgt_mapped = element_mapping.get(relationship['target'])
            if src_mapped is None or tgt_mapped is None:
                continue

            src_pos = positions.get(relationship['source'])
            tgt_pos = positions.get(relationship['target'])
            src_size = self._get_element_size(self.elements[relationship['source']])
            tgt_size = self._get_element_size(self.elements[relationship['target']])

            # Määritä sivut (exit/entry) suhteellisten positioiden mukaan
            scx = src_pos[0] + src_size[0] / 2
            scy = src_pos[1] + src_size[1] / 2
            tcx = tgt_pos[0] + tgt_size[0] / 2
            tcy = tgt_pos[1] + tgt_size[1] / 2
            dx, dy = tcx - scx, tcy - scy

            if abs(dx) >= abs(dy):
                exit_side = 'right' if dx >= 0 else 'left'
                entry_side = 'left' if dx >= 0 else 'right'
            else:
                exit_side = 'bottom' if dy >= 0 else 'top'
                entry_side = 'top' if dy >= 0 else 'bottom'

            valid_rels.append((rel_idx, relationship, exit_side, entry_side))
            outgoing_by_side[(relationship['source'], exit_side)].append(len(valid_rels) - 1)
            incoming_by_side[(relationship['target'], entry_side)].append(len(valid_rels) - 1)

        # Laske hajautetut ankkuripisteet per elementti per sivu
        def _distribute(count, index):
            """Hajota ankkurit tasaisesti välille 0.15-0.85."""
            if count <= 1:
                return 0.5
            return 0.15 + (0.7 * index / (count - 1))

        for vi, (rel_idx, relationship, exit_side, entry_side) in enumerate(valid_rels):
            src_key = (relationship['source'], exit_side)
            tgt_key = (relationship['target'], entry_side)

            src_list = outgoing_by_side[src_key]
            tgt_list = incoming_by_side[tgt_key]
            src_idx = src_list.index(vi)
            tgt_idx = tgt_list.index(vi)

            # Lasketaan exit/entry koordinaatit
            if exit_side in ('left', 'right'):
                exit_x = 1.0 if exit_side == 'right' else 0.0
                exit_y = _distribute(len(src_list), src_idx)
            else:
                exit_y = 1.0 if exit_side == 'bottom' else 0.0
                exit_x = _distribute(len(src_list), src_idx)

            if entry_side in ('left', 'right'):
                entry_x = 0.0 if entry_side == 'left' else 1.0
                entry_y = _distribute(len(tgt_list), tgt_idx)
            else:
                entry_y = 0.0 if entry_side == 'top' else 1.0
                entry_x = _distribute(len(tgt_list), tgt_idx)

            anchor_style = (
                f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
                f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;"
            )

            cell_attrs = {
                "id": str(element_id + vi),
                "value": relationship['label'],
                "style": self._get_edge_style(relationship['label'], relationship.get('kind')) + anchor_style,
                "edge": "1",
                "source": element_mapping[relationship['source']],
                "target": element_mapping[relationship['target']],
                "parent": "1"
            }
            cell = ET.SubElement(mx_root, "mxCell", cell_attrs)
            ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

        # Lisää legend oikeaan alakulmaan
        legend_id_start = element_id + len(valid_rels)
        self._append_legend_cells(mx_root, legend_id_start, page_width, page_height)

        # Muunna XML:ksi
        return self._prettify_xml(root)

    def _append_legend_cells(self, mx_root, start_id: int, page_width: int, page_height: int) -> None:
        """Lisää EDGY-legend draw.io-kaavion oikeaan alakulmaan."""
        # Legend-alueen mitat
        lw, lh = 220, 200
        margin = 20
        lx = page_width - lw - margin
        ly = page_height - lh - margin

        cid = start_id

        # Taustasuorakulmio legendille
        bg = ET.SubElement(mx_root, "mxCell", {
            "id": str(cid), "value": "",
            "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#cccccc;strokeWidth=1;",
            "vertex": "1", "parent": "1"
        })
        ET.SubElement(bg, "mxGeometry", {"x": str(lx), "y": str(ly), "width": str(lw), "height": str(lh), "as": "geometry"})
        cid += 1

        # Otsikkorivi
        title = ET.SubElement(mx_root, "mxCell", {
            "id": str(cid), "value": "<b>EDGY 23 — Legend</b>",
            "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;",
            "vertex": "1", "parent": "1"
        })
        ET.SubElement(title, "mxGeometry", {"x": str(lx + 8), "y": str(ly + 4), "width": str(lw - 16), "height": "18", "as": "geometry"})
        cid += 1

        # Elementtivärit
        elem_items = [
            ("#80ffb7", "Identity (Purpose, Story, Content)"),
            ("#a6c0ff", "Architecture (Capability, Asset, Process)"),
            ("#ff99bd", "Experience (Task, Channel, Journey)"),
            ("#ffd580", "Brand"),
            ("#e599ff", "Product"),
            ("#80eaff", "Organisation"),
        ]
        for i, (color, label) in enumerate(elem_items):
            row_y = ly + 26 + i * 18
            dot = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": "",
                "style": f"rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#ffffff;strokeWidth=1;",
                "vertex": "1", "parent": "1"
            })
            ET.SubElement(dot, "mxGeometry", {"x": str(lx + 8), "y": str(row_y + 2), "width": "14", "height": "12", "as": "geometry"})
            cid += 1

            txt = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": html.escape(label),
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;",
                "vertex": "1", "parent": "1"
            })
            ET.SubElement(txt, "mxGeometry", {"x": str(lx + 26), "y": str(row_y), "width": str(lw - 34), "height": "16", "as": "geometry"})
            cid += 1

        # Viivaerottaja
        sep_y = ly + 26 + len(elem_items) * 18 + 2
        sep = ET.SubElement(mx_root, "mxCell", {
            "id": str(cid), "value": "",
            "style": "line;strokeColor=#cccccc;fillColor=none;",
            "vertex": "1", "parent": "1"
        })
        ET.SubElement(sep, "mxGeometry", {"x": str(lx + 8), "y": str(sep_y), "width": str(lw - 16), "height": "6", "as": "geometry"})
        cid += 1

        # Relaatiotyypit
        rel_items = [
            ("endArrow=classic;endFill=1;strokeWidth=1;strokeColor=#333333;", "Link (core link)"),
            ("endArrow=open;endFill=0;strokeWidth=1;strokeColor=#333333;", "Flow (tieto/arvo)"),
            ("endArrow=none;strokeWidth=1;strokeColor=#333333;", "Tree (hierarkia)"),
            ("endArrow=open;endFill=0;dashed=1;strokeWidth=1;strokeColor=#333333;", "Influence (ohjaa)"),
        ]
        rel_y_start = sep_y + 8
        for i, (edge_style, label) in enumerate(rel_items):
            row_y = rel_y_start + i * 16
            arrow = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": "",
                "style": f"edgeStyle=none;{edge_style}",
                "edge": "1", "parent": "1"
            })
            geo = ET.SubElement(arrow, "mxGeometry", {"relative": "1", "as": "geometry"})
            # sourcePoint ja targetPoint kuuluvat mxGeometry-elementin alle (ei mxCell:n alle)
            ET.SubElement(geo, "mxPoint", {"x": str(lx + 8), "y": str(row_y + 8), "as": "sourcePoint"})
            ET.SubElement(geo, "mxPoint", {"x": str(lx + 36), "y": str(row_y + 8), "as": "targetPoint"})
            cid += 1

            txt = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": html.escape(label),
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;",
                "vertex": "1", "parent": "1"
            })
            ET.SubElement(txt, "mxGeometry", {"x": str(lx + 40), "y": str(row_y), "width": str(lw - 48), "height": "16", "as": "geometry"})
            cid += 1

    def _calculate_layout(self) -> Dict[str, Tuple[int, int]]:
        """Laske elementtien asettelupositiot. Palauttaa dict {elem_id: (x, y)}.

        Pipeline:
        1. Base layout (facet tai map_type)
        2. Tree-hierarkia
        3. Sweep-and-Compact törmäysresoluutio
        4. Canvas-normalisointi (positiiviset koordinaatit)
        5. Grid snap (10px kerrannaiset)
        """
        # 1. Karttatyyppien erityislayoutit
        if self.map_type:
            positions = self._calculate_map_type_layout()
        else:
            positions = self._calculate_facet_layout()

        # 2. Sovella tree-hierarkia kaikkiin layoutteihin
        self._apply_tree_layout(positions)

        # 3. Ratkaise mahdolliset päällekkäisyydet
        self._resolve_collisions(positions)

        # 4. Varmista positiiviset koordinaatit
        self._normalize_to_canvas(positions)

        # 5. Kohdista 10px gridiin
        self._snap_to_grid(positions)

        return positions

    def _calculate_map_type_layout(self) -> Dict[str, Tuple[int, int]]:
        """Laske layout karttatyypin mukaan. Reititä strategiaan MAP_TYPE_LAYOUT-taulun kautta."""
        strategy = MAP_TYPE_LAYOUT.get(self.map_type, 'grid')
        if strategy == 'grid' or strategy == 'grid_tree':
            return self._layout_grid()
        if strategy == 'tree':
            return self._layout_tree()
        if strategy == 'sequence':
            return self._layout_sequence()
        if strategy == 'hub_spoke':
            return self._layout_hub_spoke()
        return self._layout_grid()

    def _layout_grid(self) -> Dict[str, Tuple[int, int]]:
        """Adaptiivinen ruudukko: sarakemäärä ≈ sqrt(N), välit elementtikoosta."""
        import math
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys())
        if not items:
            return positions
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        x_start, y_start = 80, 80
        x_spacing = max(180, max_w + 40)
        y_spacing = 100
        cols = max(2, min(5, int(math.sqrt(len(items)))))
        for i, eid in enumerate(items):
            row = i // cols
            col = i % cols
            positions[eid] = (x_start + col * x_spacing, y_start + row * y_spacing)
        return positions

    def _layout_tree(self) -> Dict[str, Tuple[int, int]]:
        """Puuhierarkia top-down: ensimmäinen elementti juureksi, loput rivinä alle.

        Tree-relaatiot (`_apply_tree_layout`) tarkentavat lapsipositiot myöhemmin.
        """
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys())
        if not items:
            return positions
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        x_spacing = max(200, max_w + 60)
        y_start = 60
        positions[items[0]] = (380, y_start)
        for i, eid in enumerate(items[1:]):
            positions[eid] = (80 + i * x_spacing, y_start + 120)
        return positions

    def _layout_sequence(self) -> Dict[str, Tuple[int, int]]:
        """Vaakasuuntainen sekvenssi: kaikki elementit yhdellä rivillä vasemmalta oikealle."""
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys())
        if not items:
            return positions
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        x_start, y_start = 60, 200
        x_spacing = max(180, max_w + 40)
        for i, eid in enumerate(items):
            positions[eid] = (x_start + i * x_spacing, y_start)
        return positions

    def _layout_hub_spoke(self) -> Dict[str, Tuple[int, int]]:
        """Keskuselementti + säteittäiset elementit. Säde skaalautuu N:n ja koon mukaan."""
        import math
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys())
        if not items:
            return positions
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        cx, cy = 500, 400
        min_gap = 60
        positions[items[0]] = (cx, cy)
        n = len(items) - 1
        if n > 0:
            circumference_needed = n * (max_w + min_gap)
            radius = max(220, circumference_needed / (2 * math.pi))
            for i, eid in enumerate(items[1:]):
                angle = 2 * math.pi * i / n - math.pi / 2
                positions[eid] = (cx + radius * math.cos(angle),
                                  cy + radius * math.sin(angle))
        return positions

    def _calculate_facet_layout(self) -> Dict[str, Tuple[int, int]]:
        """Laske elementtien asettelupositiot faceteittain.

        EDGY Facet Model -asettelu (facet: all):
        ┌─────────────┬─────────────────┬─────────────┐
        │  Identity   │  Architecture   │ Experience  │
        │  Purpose    │   Capability    │   Task      │
        │  Content    │   Asset         │   Channel   │
        │  Story      │   Process       │   Journey   │
        ├─────────────┼─────────────────┼─────────────┤
        │ Organisation│                 │             │
        │ (ID↔Arch)   │   Product       │             │
        │             │   (Arch↔Exp)    │             │
        │    Brand (ID↔Exp, koko leveys keskeinen)    │
        └─────────────┴─────────────────┴─────────────┘
        """
        positions = {}

        if self.facet == 'all':
            COL_GAP = 60   # väli sarakkeiden välillä
            MIN_COL_W = 240  # sarakkeen minimiarvoleveys
            y_start = 80
            y_spacing = 100

            identity_items = []
            architecture_items = []
            experience_items = []
            organisation_items = []
            product_items = []
            brand_items = []
            other_items = []

            for elem_id, element in self.elements.items():
                etype = element['type']
                if etype in IDENTITY_ELEMENTS:
                    identity_items.append(elem_id)
                elif etype in ARCHITECTURE_ELEMENTS:
                    architecture_items.append(elem_id)
                elif etype in EXPERIENCE_ELEMENTS:
                    experience_items.append(elem_id)
                elif etype == 'organisation':
                    organisation_items.append(elem_id)
                elif etype == 'product':
                    product_items.append(elem_id)
                elif etype == 'brand':
                    brand_items.append(elem_id)
                else:
                    other_items.append(elem_id)

            # Laske kunkin sarakkeen tarvitsema leveys elementtien ja alipuiden perusteella
            sizes = {eid: self._get_element_size(self.elements[eid]) for eid in self.elements}
            tree_children, child_set = self._compute_tree_structure()

            def _column_width(items):
                if not items:
                    return MIN_COL_W
                max_elem_w = max(sizes.get(eid, (120, 60))[0] for eid in items)
                max_tree_w = max(
                    (self._subtree_width(eid, tree_children, sizes) for eid in items),
                    default=0
                )
                return max(MIN_COL_W, max_elem_w, max_tree_w)

            id_col_w = _column_width(identity_items)
            arch_col_w = _column_width(architecture_items)
            exp_col_w = _column_width(experience_items)

            # Adaptiiviset sarakepositiot
            IDENTITY_X = 60
            ARCHITECTURE_X = IDENTITY_X + id_col_w + COL_GAP
            EXPERIENCE_X = ARCHITECTURE_X + arch_col_w + COL_GAP

            # Intersection-elementtien x-positiot sarakkeiden väliin
            ORGANISATION_X = (IDENTITY_X + id_col_w // 2 + ARCHITECTURE_X) // 2
            PRODUCT_X = (ARCHITECTURE_X + arch_col_w // 2 + EXPERIENCE_X) // 2
            BRAND_X = (IDENTITY_X + EXPERIENCE_X + exp_col_w // 2) // 2

            # Facet-elementit omiin sarakkeisiinsa
            for i, eid in enumerate(identity_items):
                positions[eid] = (IDENTITY_X, y_start + i * y_spacing)

            for i, eid in enumerate(architecture_items):
                positions[eid] = (ARCHITECTURE_X, y_start + i * y_spacing)

            for i, eid in enumerate(experience_items):
                positions[eid] = (EXPERIENCE_X, y_start + i * y_spacing)

            # Leikkauselementtien y-positio: oman fasetin elementtien maksimin alapuolella
            max_facet_rows = max(
                len(identity_items),
                len(architecture_items),
                len(experience_items),
                1
            )
            intersection_y = y_start + max_facet_rows * y_spacing + 40

            # Organisation: Identity ↔ Architecture -väliin
            for i, eid in enumerate(organisation_items):
                positions[eid] = (ORGANISATION_X, intersection_y + i * y_spacing)

            # Product: Architecture ↔ Experience -väliin
            for i, eid in enumerate(product_items):
                positions[eid] = (PRODUCT_X, intersection_y + i * y_spacing)

            # Brand: Identity ↔ Experience -silta, sijoitetaan kaavion alareunaan keskelle
            brand_y = intersection_y + max(
                len(organisation_items), len(product_items), 1
            ) * y_spacing + 40 if (organisation_items or product_items) else intersection_y
            for i, eid in enumerate(brand_items):
                positions[eid] = (BRAND_X + i * 200, brand_y)

            # Peruselementit (people, activity, outcome, object) omaan riviin
            base_y = brand_y + (y_spacing if brand_items else 0)
            base_items = [eid for eid in other_items if self.elements[eid]['type'] in BASE_ELEMENTS]
            non_base_items = [eid for eid in other_items if self.elements[eid]['type'] not in BASE_ELEMENTS]
            for i, eid in enumerate(base_items):
                positions[eid] = (IDENTITY_X + i * 180, base_y)

            # Muut tunnistamattomat elementit
            other_y = base_y + (y_spacing if base_items else 0)
            for i, eid in enumerate(non_base_items):
                positions[eid] = (IDENTITY_X + i * 180, other_y)

        else:
            # Yksittäinen facet: elementit kolmeen sarakkeeseen, intersection-elementit alariville
            x_start = 80
            y_start = 100
            x_spacing = 200
            y_spacing = 120
            cols = 3

            main_items = []
            intersection_items = []

            for elem_id, element in self.elements.items():
                if element['type'] in INTERSECTION_ELEMENTS:
                    intersection_items.append(elem_id)
                else:
                    main_items.append(elem_id)

            # Päätyypin elementit ruudukossa
            for i, elem_id in enumerate(main_items):
                row = i // cols
                col = i % cols
                positions[elem_id] = (x_start + col * x_spacing, y_start + row * y_spacing)

            # Leikkauselementit erilliselle alariville
            if intersection_items:
                main_rows = (len(main_items) + cols - 1) // cols
                inter_y = y_start + main_rows * y_spacing + 40
                inter_x_start = x_start + (cols - len(intersection_items)) * x_spacing // 2
                for i, elem_id in enumerate(intersection_items):
                    positions[elem_id] = (inter_x_start + i * x_spacing, inter_y)

        return positions

    def _compute_tree_structure(self) -> Tuple[Dict[str, List[str]], set]:
        """Palauta tree-relaatioiden parent→children -map ja child_set."""
        tree_children: Dict[str, List[str]] = {}
        child_set = set()
        for rel in self.relationships:
            if rel['label'].lower().strip() in TREE_RELATIONSHIPS:
                parent = rel['source']
                child = rel['target']
                tree_children.setdefault(parent, []).append(child)
                child_set.add(child)
        return tree_children, child_set

    def _subtree_width(self, node: str, tree_children: Dict[str, List[str]],
                       sizes: Dict[str, Tuple[int, int]], h_gap: int = 40) -> float:
        """Laske tree-alipuun kokonaisleveys rekursiivisesti."""
        children = tree_children.get(node, [])
        own_w = sizes.get(node, (120, 60))[0]
        if not children:
            return own_w
        total = sum(self._subtree_width(c, tree_children, sizes, h_gap) for c in children) + (len(children) - 1) * h_gap
        return max(own_w, total)

    def _apply_tree_layout(self, positions: Dict[str, Tuple[int, int]]) -> None:
        """Sijoita tree-relaation lapset vanhemman alle alipuiden leveyden mukaan.

        Rekursiivinen "tidy tree" -tyylinen layout: jokainen alipuu varaa
        leveyden joka on suurempi kuin sen omat lapsenlapset, jotta
        vierekkäiset alipuut eivät mene päällekkäin.
        """
        tree_children, child_set = self._compute_tree_structure()

        if not tree_children:
            return

        H_GAP = 40   # vaakavälit sisarusten välillä
        V_GAP = 110  # pystyväli vanhemmasta lapsiin
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in positions}

        def place_subtree(node: str, center_x: float, top_y: float) -> None:
            children = tree_children.get(node, [])
            if node in positions:
                w = sizes.get(node, (120, 60))[0]
                positions[node] = (center_x - w / 2, top_y)
            if not children:
                return
            child_widths = [self._subtree_width(c, tree_children, sizes, H_GAP) for c in children]
            total = sum(child_widths) + (len(children) - 1) * H_GAP
            cursor = center_x - total / 2
            for c, w in zip(children, child_widths):
                place_subtree(c, cursor + w / 2, top_y + V_GAP)
                cursor += w + H_GAP

        # Sovella jokaisen tree-juuren kohdalla (juuri = ei toisen tree-relaation lapsi)
        roots = [p for p in tree_children.keys() if p not in child_set]
        for root in roots:
            if root in positions:
                rx, ry = positions[root]
                rw = sizes.get(root, (120, 60))[0]
                place_subtree(root, rx + rw / 2, ry)

    def _prettify_xml(self, element: ET.Element, indent: str = '  ') -> str:
        """Muotoile XML luettavaan muotoon"""
        from xml.dom import minidom
        rough_string = ET.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent=indent, encoding='utf-8').decode('utf-8')


def main():
    """Testausfunktio"""
    parser = EDGYParser()

    # Esimerkkisyöte
    example_input = """
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

    parser.parse_input(example_input)
    xml_output = parser.generate_xml()
    print(xml_output)


if __name__ == "__main__":
    main()
