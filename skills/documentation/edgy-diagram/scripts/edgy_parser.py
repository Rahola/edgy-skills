#!/usr/bin/env python3
"""
EDGY Parser - Jäsennä EDGY-notaatiota ja generoi draw.io XML

Käyttää virallista EDGY 23 -väripalettia ja elementtimuotoja.
"""

import html
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

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
import edgy_geometry as _geo  # noqa: E402 — portit ja sivut samasta paikasta kuin renderöijä ja lintti
import edgy_text as _text     # noqa: E402 — tekstin mittaus glyyfitaulukoilla, sama kuin renderöijä ja lintti
import edgy_vocab as _vocab   # noqa: E402 — verbien kielet ja käännökset (ydinlinkit, influence, flow, tree)

# Flow relationships → open arrowhead (data/value flows concretely)
# Supported in FI, EN, FR, DE
FLOW_RELATIONSHIPS = {
    'virtaa', 'siirtyy', 'lähettää', 'vastaanottaa', 'tuottaa dataa', 'palauttaa',   # FI
    'flows', 'transfers', 'sends', 'receives', 'produces data', 'returns',          # EN
    'circule', 'transfère', 'envoie', 'reçoit', 'produit des données', 'retourne',  # FR
    'fließt', 'überträgt', 'sendet', 'empfängt', 'erzeugt daten', 'gibt zurück',    # DE (lower case: labels are lowered before the check)
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
    # EDGY extensions (not EDGY 23 map types): layered reference architecture, stakeholder summary,
    # planned ring of one primary element per type ("Further …" panels for the rest)
    'reference', 'summary', 'triad',
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
    'reference': 'reference',
    'summary': 'summary',
    'triad': 'triad',
}
# Stakeholder summary: max boxes per row before the parser warns
SUMMARY_MAX_PER_ROW = 4
ALL_ELEMENT_TYPES = (IDENTITY_ELEMENTS | ARCHITECTURE_ELEMENTS |
                     EXPERIENCE_ELEMENTS | INTERSECTION_ELEMENTS | BASE_ELEMENTS)

# Rakenne-elementit (eivät EDGY-elementtejä): ryhmä = container, kaista = taustakaista
STRUCTURE_TYPES = {'group', 'lane'}

# Facet-konttien vaaleat täyttövärit (facet: all / yksittäinen facet)
FACET_CONTAINER_FILLS = {
    'identity': '#e3ffee',
    'architecture': '#e6edff',
    'experience': '#ffe6ef',
    'group': '#eef2f7',      # käyttäjän määrittelemä ryhmä ilman fasettia
    'further': '#f3f4f6',    # triadin "Further <type>" -paneeli (rakenne, ei EDGY-elementti)
}
FACET_TITLES = {'identity': 'Identity', 'architecture': 'Architecture', 'experience': 'Experience'}

# Kokoluokat: S = kartta, M = kortti, L = palikka (sisältää alielementtejä)
SIZE_CLASSES = {'S': (120, 60), 'M': (200, 90), 'L': (270, 120)}

# ─── Muutoskerros (transition overlay) — EDGY:n LAAJENNUS, ei osa notaatiota ──
# Täyttöväri pysyy aina fasetin värinä; muutos näkyy vain reunassa (stroke).
CHANGE_PALETTE = {
    'keep':    ('#6b778c', False),
    'new':     ('#006644', False),
    'change':  ('#b26b00', False),
    'replace': ('#c25100', False),
    'remove':  ('#bf2600', False),
    'decide':  ('#bf2600', True),    # katkoviiva: päätös auki (ADR)
}
# ─── Tilamerkki (status badge) — EDGY:n LAAJENNUS lämpökartoille ───────────────
# Täyttö pysyy fasetin värinä; kypsyys / arvio näkyy kortin alareunan merkkinä ja omalla legendarivillään.
MATURITY_PALETTE = {1: '#d73027', 2: '#fc8d59', 3: '#fee08b', 4: '#91cf60', 5: '#1a9850'}
# rating: arvot saavat värin ensiesiintymisjärjestyksessä (värisokeille sopiva sarja); rating_palette: ohittaa
RATING_COLOURS = ('#4477aa', '#ee6677', '#228833', '#ccbb44', '#66ccee', '#aa3377', '#bbbbbb')
BADGE_H = 14          # merkin korkeus; kortti kasvaa BADGE_H + 4 px


def _badge_text_colour(fill: str) -> str:
    """Valkoinen teksti tummalle merkille, tumma vaalealle (suhteellinen luminanssi, WCAG)."""
    r, g, b = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return '#ffffff' if lum < 0.18 else '#1a1a1a'

CHANGE_SYNONYMS = {
    # fi
    'säilyy': 'keep', 'uusi': 'new', 'vahvistuu': 'new', 'muuttuu': 'change', 'yhdistyy': 'change',
    'laajenee': 'change', 'korvautuu': 'replace', 'poistuu': 'remove', 'päätettävä': 'decide',
    # en
    'keep': 'keep', 'new': 'new', 'strengthen': 'new', 'change': 'change', 'merge': 'change',
    'extend': 'change', 'replace': 'replace', 'remove': 'remove', 'decide': 'decide', 'open': 'decide',
    # fr
    'conserver': 'keep', 'nouveau': 'new', 'modifier': 'change', 'remplacer': 'replace',
    'supprimer': 'remove', 'à décider': 'decide',
    # de
    'bleibt': 'keep', 'neu': 'new', 'ändert sich': 'change', 'ersetzt': 'replace',
    'entfällt': 'remove', 'zu entscheiden': 'decide',
}
CHANGE_LABELS = {
    'keep': 'keep / säilyy', 'new': 'new, strengthen / uusi', 'change': 'change, merge / muuttuu',
    'replace': 'replace / korvautuu', 'remove': 'remove / poistuu', 'decide': 'decide (open, see ADR) / päätettävä',
}

# ─── Legenda ja generoidut otsikot kielen mukaan (`language:`) ─────────────
# 'en' on nykyinen oletus (merkkijonot täsmälleen kuten ennen); EDGY-fasettien
# nimet (Identity/Architecture/Experience) ovat erisnimiä eikä niitä käännetä.
LEGEND_TEXT = {
    'en': {
        'title': 'EDGY 23 — Legend',
        'chips': ['Identity (Purpose, Story, Content)', 'Architecture (Capability, Asset, Process)',
                  'Experience (Task, Channel, Journey)', 'Brand', 'Product', 'Organisation'],
        'chips_short': ['Identity', 'Architecture', 'Experience', 'Brand', 'Product', 'Organisation'],
        'lines': ['Link (core link)', 'Flow (data/value)', 'Tree (hierarchy)', 'Influence (guides)'],
        'lines_short': ['Link', 'Flow', 'Tree', 'Influence'],
        'overlay': 'Transition (extension, stroke only)', 'overlay_short': 'Transition (extension)', 'maturity': 'Maturity (extension)', 'rating': 'Rating (extension)',
        'change': CHANGE_LABELS,
    },
    'fi': {
        'title': 'EDGY 23 — Selite',
        'chips': ['Identity (Tarkoitus, Tarina, Sisältö)', 'Architecture (Kyvykkyys, Resurssi, Prosessi)',
                  'Experience (Tehtävä, Kanava, Matka)', 'Brändi', 'Tuote', 'Organisaatio'],
        'chips_short': ['Identity', 'Architecture', 'Experience', 'Brändi', 'Tuote', 'Organisaatio'],
        'lines': ['Linkki (ydinlinkki)', 'Virta (tieto/arvo)', 'Puu (hierarkia)', 'Vaikutus (ohjaa)'],
        'lines_short': ['Linkki', 'Virta', 'Puu', 'Vaikutus'],
        'overlay': 'Siirtymä (laajennus, vain reunaviiva)', 'overlay_short': 'Siirtymä (laajennus)', 'maturity': 'Kypsyys (laajennus)', 'rating': 'Arvio (laajennus)',
        'change': {'keep': 'säilyy', 'new': 'uusi, vahvistuu', 'change': 'muuttuu, yhdistyy',
                   'replace': 'korvautuu', 'remove': 'poistuu', 'decide': 'päätettävä (avoin, ks. ADR)'},
    },
    'fr': {
        'title': 'EDGY 23 — Légende',
        'chips': ["Identity (Raison d'être, Récit, Contenu)", 'Architecture (Capacité, Actif, Processus)',
                  'Experience (Tâche, Canal, Parcours)', 'Marque', 'Produit', 'Organisation'],
        'chips_short': ['Identity', 'Architecture', 'Experience', 'Marque', 'Produit', 'Organisation'],
        'lines': ['Lien (lien fondamental)', 'Flux (données/valeur)', 'Arbre (hiérarchie)', 'Influence (guide)'],
        'lines_short': ['Lien', 'Flux', 'Arbre', 'Influence'],
        'overlay': 'Transition (extension, contour seul)', 'overlay_short': 'Transition (extension)', 'maturity': 'Maturité (extension)', 'rating': 'Évaluation (extension)',
        'change': {'keep': 'conserver', 'new': 'nouveau, renforcer', 'change': 'modifier, fusionner',
                   'replace': 'remplacer', 'remove': 'supprimer', 'decide': 'à décider (ouvert, voir ADR)'},
    },
    'de': {
        'title': 'EDGY 23 — Legende',
        'chips': ['Identity (Zweck, Geschichte, Inhalt)', 'Architecture (Fähigkeit, Ressource, Prozess)',
                  'Experience (Aufgabe, Kanal, Reise)', 'Marke', 'Produkt', 'Organisation'],
        'chips_short': ['Identity', 'Architecture', 'Experience', 'Marke', 'Produkt', 'Organisation'],
        'lines': ['Verknüpfung (Kernverknüpfung)', 'Fluss (Daten/Wert)', 'Baum (Hierarchie)', 'Einfluss (steuert)'],
        'lines_short': ['Verknüpfung', 'Fluss', 'Baum', 'Einfluss'],
        'overlay': 'Übergang (Erweiterung, nur Kontur)', 'overlay_short': 'Übergang (Erweiterung)', 'maturity': 'Reifegrad (Erweiterung)', 'rating': 'Bewertung (Erweiterung)',
        'change': {'keep': 'bleibt', 'new': 'neu, gestärkt', 'change': 'ändert sich, zusammengeführt',
                   'replace': 'ersetzt', 'remove': 'entfällt', 'decide': 'zu entscheiden (offen, siehe ADR)'},
    },
}
LEGEND_TITLES = {lang: t['title'] for lang, t in LEGEND_TEXT.items()}   # lint päättelee kartan kielen otsikosta
RESERVED_METRIC_KEYS = {'id', 'change', 'size', 'highlight', 'primary', 'stage', 'column', 'row', 'maturity', 'rating'}

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
        self.groups = {}         # group_id → {'name', 'members': [elem_id], 'kind': 'group'|'lane', 'tags'}
        self._computed_sizes = {}  # ryhmien/konttien lasketut koot
        self._child_positions = {}  # jäsenten sijainnit suhteessa ryhmään
        self._group_positions = {}  # ryhmien absoluuttiset sijainnit (viimeisin layout)
        self._layout_handles_tree = False
        self.uses_change_overlay = False
        self.rating_palette: Dict[str, str] = {}   # rating_palette: label=#hex, … — tilamerkin värit (laajennus)
        self.layout_from = None    # (archimate file, view name, scale, dx, dy) tai None
        self.legend = 'box'        # 'box' = laatikko oikeassa alakulmassa, 'strip' = kapea nauha alareunassa
        self._legend_explicit = False
        self.language = 'en'       # generoitujen tekstien kieli (legenda, triadin paneelit, verbit): fi | en | fr | de
        self._language_explicit = False
        self.translate_verbs = True  # language: asetettu → sanaston verbit renderöidään kartan kielellä (translate_verbs: false kytkee pois)
        # Asettelun vakiomitoitus (2.6.0): dokumenttitason avaimet
        self.card_width = None       # card_width: N — jokaisen laatikon leveys (ei person-hahmolle); kokoluokka voi olla suurempi
        self.equal_cards = True      # equal_cards: false — saman tyypin laatikot EIVÄT saa yhteistä leveyttä/korkeutta sivulla
        self.group_columns = None    # group_columns: N — kontit N sarakkeeseen
        self.cards_per_row = None    # cards_per_row: N — kontin sisäinen ruudukko N sarakkeeseen
        self.equal_group_width = False  # equal_group_width: true — kontit saavat leveimmän kontin leveyden
        self.align_groups = None     # align_groups: grid — kontit yhteiseen rivi/sarake-ruudukkoon (rivin korkeus = korkein)
        self.group_style = None      # group_style: official | light — None = official kun sisäkkäisiä ryhmiä on, muuten light
        self.stages = []             # stages: / columns: A, B, C — matriisin sarakkeet (tehtäväkartta: vaiheet)
        self.rows = []               # rows: X, Y — matriisin rivit (synteettiset kaistat), elementti {row: X}
        self.title = None            # title: — natiivipresettien otsikkonauha
        self.footnote = None         # footnote: — natiivipresettien alaviitenauha
        self._hidden = set()         # elementit, joita ei piirretä (tehtäväkartta: kaistaksi muuttunut sidosryhmä)
        self._stage_headers = []     # [(teksti, x, y, w)] sarakeotsikot kaistojen yläpuolelle
        self._size_override = {}   # elem_id → (w, h): layoutin pakottama koko (triad: kehän laatikot, paneelien sirut)
        self._triad_detours = {}   # (src, tgt) → (exit_side, entry_side, [(x, y), …]) kehää kiertävät linkit
        self._triad_hidden = set() # paneeleihin jäävät (ei-ensisijaiset) elementit: niiden linkkejä ei piirretä

    def parse_input(self, input_text: str) -> None:
        """Jäsennä käyttäjän syöte EDGY-elementeiksi"""
        lines = input_text.strip().split('\n')

        current_section = None
        current_group = None      # avoin (sisin) ryhmä/kaista (group_id)
        group_stack: List[Tuple[str, int]] = []   # avoimet ryhmät ulommasta sisimpään: (group_id, ryhmärivin sisennys)
        for raw_line in lines:
            indent = len(raw_line) - len(raw_line.lstrip())
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            # Ryhmä sulkeutuu kun sisennys palaa ryhmärivin tasolle tai alle (sisäkkäiset ryhmät pinona)
            if line.startswith('- '):
                while group_stack and indent <= group_stack[-1][1]:
                    group_stack.pop()
                current_group = group_stack[-1][0] if group_stack else None

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
            elif line.startswith('layout_from:'):
                # layout_from: path/to/model.archimate#View name [scale=1.0 dx=0 dy=0]
                spec = line.split(':', 1)[1].strip()
                self.layout_from = self._parse_layout_from(spec)
                continue
            elif line.startswith('language:'):
                # language: fi | en | fr | de — generoitujen otsikoiden kieli (verbit tulevat syötteestä sellaisinaan)
                lang_value = line.split(':', 1)[1].strip().lower()
                if lang_value in ('fi', 'en', 'fr', 'de'):
                    self.language = lang_value
                    self._language_explicit = True
                else:
                    self.warnings.append(f"Tuntematon language-arvo '{lang_value}' (sallitut: fi, en, fr, de), käytetään 'en'")
                continue
            elif line.startswith('translate_verbs:'):
                # translate_verbs: true | false — renderöidäänkö sanaston verbit kartan kielellä
                tv = line.split(':', 1)[1].strip().lower()
                if tv in ('true', 'false', 'yes', 'no', 'kyllä', 'ei'):
                    self.translate_verbs = tv in ('true', 'yes', 'kyllä')
                else:
                    self.warnings.append(f"Tuntematon translate_verbs-arvo '{tv}' (sallitut: true, false), käytetään 'true'")
                continue
            elif line.split(':')[0].strip() in self._LAYOUT_OPTION_KEYS:
                self._parse_layout_option(line)
                continue
            elif line.startswith('stages:') or line.startswith('columns:') or line.startswith('rows:'):
                # stages:/columns: Plan, Buy, Ride — matriisin sarakkeet; elementti kiinnittyy {stage: Buy} tai {column: Buy}
                # rows: Physical, Digital — matriisin rivit; elementti {row: Digital}; "none" tyhjentää
                key, _, raw = line.partition(':')
                values = [] if raw.strip().lower() in ('', 'none') else [x.strip() for x in raw.split(',') if x.strip()]
                if key.strip() == 'rows':
                    self.rows = values
                else:
                    self.stages = values
                continue
            elif line.startswith('title:') or line.startswith('footnote:'):
                key, _, raw = line.partition(':')
                setattr(self, key.strip(), raw.strip().strip('"') or None)
                continue
            elif line.startswith('rating_palette:'):
                # rating_palette: strategic=#228833, commodity=#bbbbbb — rating-merkin värit (EDGY-laajennus)
                for pair in line.split(':', 1)[1].split(','):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        v = v.strip().lower()
                        if re.fullmatch(r'#[0-9a-f]{6}', v):
                            self.rating_palette[k.strip().lower()] = v
                        else:
                            self.warnings.append(f"rating_palette: '{v}' is not a #rrggbb colour — ignored")
                continue
            elif line.startswith('legend:'):
                # legend: box (oletus) | strip — nauha alareunassa säästää kanvasta
                legend_value = line.split(':', 1)[1].strip().lower()
                if legend_value in ('box', 'strip'):
                    self.legend = legend_value
                    self._legend_explicit = True
                else:
                    self.warnings.append(f"Tuntematon legend-arvo '{legend_value}' (sallitut: box, strip), käytetään 'box'")
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
            # Tukee: - tyyppi: "nimi - kuvaus" [tag1, tag2] {metriikka: arvo, id: X, change: new}
            #        - group: "Alue"   (sisennetyt elementit kuuluvat ryhmään → container)
            #        - lane: "Kerros"  (sisennetyt elementit kuuluvat kaistaan → taustakaista)
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

                    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
                    metrics = {}
                    if metrics_str:
                        for pair in metrics_str.split(','):
                            if ':' in pair:
                                k, v = pair.split(':', 1)
                                metrics[k.strip()] = v.strip()

                    if element_type in STRUCTURE_TYPES:
                        group_id = f"{element_type}{len(self.groups) + 1}"
                        parent = current_group
                        kind = element_type
                        if parent is not None and self.groups[parent]['kind'] == 'lane':
                            # Kaistan sisällä ei ole kontteja: kaistan jäsenet ovat juuritasolla
                            self.warnings.append(f"{element_type} '{element_value}' inside lane "
                                                 f"'{self.groups[parent]['name']}' is not supported — placed at top level")
                            parent = None
                            group_stack.clear()
                        elif parent is not None and kind == 'lane':
                            self.warnings.append(f"lane '{element_value}' inside group '{self.groups[parent]['name']}' "
                                                 f"is drawn as a nested group — lanes are top-level bands")
                            kind = 'group'
                        self.groups[group_id] = {
                            'id': group_id, 'kind': kind, 'name': element_value,
                            'members': [], 'tags': tags, 'metrics': metrics,
                            'parent': parent, 'subgroups': [],
                        }
                        if parent is not None:
                            self.groups[parent]['subgroups'].append(group_id)
                        current_group = group_id
                        group_stack.append((group_id, indent))
                        continue

                    if element_type not in ALL_ELEMENT_TYPES:
                        self.warnings.append(f"Tuntematon elementtityyppi '{element_type}', käytetään oletustyyliä")

                    name, subtext = self._split_name(element_value)
                    element_id = f"{element_type}{len(self.elements) + 1}"
                    change = None
                    if 'change' in metrics:
                        change = CHANGE_SYNONYMS.get(metrics['change'].lower())
                        if change is None:
                            self.warnings.append(
                                f"Tuntematon change-arvo '{metrics['change']}' elementillä '{name}' "
                                f"(sallitut: {', '.join(CHANGE_PALETTE)}), ohitetaan")
                        else:
                            self.uses_change_overlay = True
                    size_class = metrics.get('size', '').upper() or None
                    if size_class and size_class not in SIZE_CLASSES:
                        self.warnings.append(f"Tuntematon size-arvo '{metrics['size']}' (sallitut: S, M, L), ohitetaan")
                        size_class = None
                    self.elements[element_id] = {
                        'type': element_type,
                        'value': element_value,
                        'name': name,
                        'subtext': subtext,
                        'id': element_id,
                        'ref': metrics.get('id'),
                        'change': change,
                        'size_class': size_class,
                        'highlight': metrics.get('highlight', '').lower() in ('1', 'true', 'yes', 'kyllä') or 'focus' in [t.lower() for t in tags],
                        'primary': metrics.get('primary', '').lower() in ('1', 'true', 'yes', 'kyllä'),   # triad: kantaa tyypin linkit
                        'tags': [t for t in tags if t.lower() != 'focus'],
                        'metrics': {k: v for k, v in metrics.items() if k not in RESERVED_METRIC_KEYS},
                        'stage': metrics.get('stage') or metrics.get('column'),   # matriisin sarake (stages:/columns:)
                        'row': metrics.get('row'),           # matriisin rivi (rows:)
                        'maturity': self._parse_maturity(metrics.get('maturity'), element_value),
                        'rating': (metrics.get('rating') or '').strip() or None,   # tilamerkki (laajennus)
                        'group': current_group,
                    }
                    if current_group is not None:
                        self.groups[current_group]['members'].append(element_id)

            # Jäsennä suhteet
            elif current_section == 'relationships' and line.startswith('- '):
                # Valinnaiset optiot aaltosulkeissa verbin jälkeen:
                #   {from: right, to: left, via: [(x,y),(x,y)], change: new, label: source}
                options = {}
                opt_match = re.search(r'\s*\{([^{}]*)\}\s*$', line)
                if opt_match:
                    options = self._parse_relationship_options(opt_match.group(1))
                    line = line[:opt_match.start()].rstrip()
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
                            'options': options,
                        })
                        if options.get('change'):
                            self.uses_change_overlay = True

    _LAYOUT_OPTION_KEYS = ('card_width', 'equal_cards', 'group_columns', 'cards_per_row', 'equal_group_width', 'align_groups',
                           'group_style')

    def _parse_layout_option(self, line: str) -> None:
        """Dokumenttitason asetteluvalinnat (2.6.0). Virheellinen arvo → varoitus ja oletus pysyy.

        card_width: N          laatikon leveys px (60–600), ei person-hahmolle; kokoluokka S/M/L voi olla leveämpi
        equal_cards: true|false  saman tyypin laatikot sivulla saavat leveimmän/korkeimman mitat (oletus true)
        group_columns: N       kontit N sarakkeeseen (karttatyyppi- ja facet-asettelu)
        cards_per_row: N       kontin sisäinen ruudukko N sarakkeeseen
        equal_group_width: true|false  kontit saavat leveimmän kontin leveyden (oletus false)
        align_groups: grid|none  kontit yhteiseen rivi/sarake-ruudukkoon; rivin kontit venyvät rivin korkeuteen
        group_style: official|light  official = virallisten karttojen kontit (ulompi fasetin värinen, sisempi
                               valkoinen); light = vaaleanharmaa rakennekontti. Oletus official kun ryhmiä on sisäkkäin.
        """
        key, _, raw = line.partition(':')
        key, value = key.strip(), raw.strip().lower()
        if key in ('card_width', 'group_columns', 'cards_per_row'):
            lo, hi = (60, 600) if key == 'card_width' else (1, 12)
            if value.isdigit() and lo <= int(value) <= hi:
                setattr(self, key, int(value))
            else:
                self.warnings.append(f"Virheellinen {key}-arvo '{raw.strip()}' (kokonaisluku {lo}–{hi}), ohitetaan")
        elif key in ('equal_cards', 'equal_group_width'):
            if value in ('true', 'false', 'yes', 'no', 'kyllä', 'ei'):
                setattr(self, key, value in ('true', 'yes', 'kyllä'))
            else:
                self.warnings.append(f"Tuntematon {key}-arvo '{raw.strip()}' (sallitut: true, false), ohitetaan")
        elif key == 'group_style':
            if value in ('official', 'light'):
                self.group_style = value
            else:
                self.warnings.append(f"Tuntematon group_style-arvo '{raw.strip()}' (sallitut: official, light), ohitetaan")
        elif key == 'align_groups':
            if value in ('grid', 'none'):
                self.align_groups = None if value == 'none' else value
            else:
                self.warnings.append(f"Tuntematon align_groups-arvo '{raw.strip()}' (sallitut: grid, none), ohitetaan")

    def _parse_maturity(self, raw, name: str):
        """{maturity: 1–5} → int; muu arvo → varoitus ja ohitus."""
        if raw is None:
            return None
        raw = str(raw).strip()
        if raw.isdigit() and 1 <= int(raw) <= 5:
            return int(raw)
        self.warnings.append(f"maturity '{raw}' on '{name}' is not 1–5 — ignored")
        return None

    def _badge_of(self, element: dict):
        """(teksti, väri) tilamerkille tai None. Kypsyys voittaa arvion, jos molemmat on annettu."""
        if element.get('maturity'):
            n = element['maturity']
            return f"{n}/5", MATURITY_PALETTE[n]
        r = element.get('rating')
        if r:
            return r, self._rating_colour(r)
        return None

    def _rating_colour(self, label: str) -> str:
        key = label.lower()
        if key in self.rating_palette:
            return self.rating_palette[key]
        seen = []
        for e in self.elements.values():
            v = (e.get('rating') or '').lower()
            if v and v not in self.rating_palette and v not in seen:
                seen.append(v)
        idx = seen.index(key) if key in seen else len(seen)
        return RATING_COLOURS[idx % len(RATING_COLOURS)]

    def _badge_legend_sections(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """Legendan tilamerkkiosiot: [(otsikko, [(väri, teksti)])] vain käytetyille arvoille."""
        L = self._legend_text()
        out = []
        mats = sorted({e['maturity'] for e in self.elements.values() if e.get('maturity') and e['id'] not in self._hidden})
        if mats:
            out.append((L['maturity'], [(MATURITY_PALETTE[m], f"{m}/5") for m in mats]))
        ratings = []
        for e in self.elements.values():
            r = e.get('rating')
            if r and not e.get('maturity') and e['id'] not in self._hidden and r.lower() not in [x.lower() for x in ratings]:
                ratings.append(r)
        if ratings:
            out.append((L['rating'], [(self._rating_colour(r), r) for r in ratings]))
        return out

    def _parse_layout_from(self, spec: str):
        """Jäsennä `layout_from: file.archimate#View [scale=S dx=X dy=Y]`."""
        parts = spec.split()
        opts = []
        while parts and '=' in parts[-1] and '#' not in parts[-1]:
            opts.insert(0, parts.pop())
        target = ' '.join(parts)          # tiedosto#Näkymän nimi (välilyönnit sallittu)
        if '#' not in target:
            self.warnings.append("layout_from: give file.archimate#View name or file.drawio#Page name — ignored")
            return None
        path, view = target.split('#', 1)
        scale, dx, dy = 1.0, 0.0, 0.0
        for o in opts:
            if '=' in o:
                k, v = o.split('=', 1)
                try:
                    if k == 'scale':
                        scale = float(v)
                    elif k == 'dx':
                        dx = float(v)
                    elif k == 'dy':
                        dy = float(v)
                except ValueError:
                    self.warnings.append(f"layout_from: virheellinen arvo {o}, ohitetaan")
        return (path.strip(), view.strip(), scale, dx, dy)

    def _positions_from_layout_source(self) -> Dict[str, Tuple[float, float]]:
        """layout_from: lähde tiedostopäätteen mukaan: .archimate → Archi-näkymä,
        .drawio / .xml → draw.io-sivu. Muu pääte → varoitus, oma asettelu."""
        path = self.layout_from[0].lower()
        if path.endswith('.archimate'):
            return self._positions_from_archimate()
        if path.endswith('.drawio') or path.endswith('.xml'):
            return self._positions_from_drawio()
        self.warnings.append(f"layout_from: {self.layout_from[0]} is neither .archimate nor .drawio / .xml — "
                             f"unsupported layout source, own layout used")
        return {}

    def _positions_from_drawio(self) -> Dict[str, Tuple[float, float]]:
        """Sijainnit olemassa olevalta draw.io-sivulta (esim. käsin säädetty edellinen toimitus):
        ylimmän tason elementit ja kontit (group:/lane:) kohdistetaan nimellä (sama
        nimisääntö kuin ArchiMate-lähteellä). Kontin sisäinen järjestys tulee generaattorista,
        joten käsin siirretty alue säilyy, alueen sisäinen korttisiirto ei.
        T(x, y) = ((x + dx) · S, (y + dy) · S)."""
        import base64
        import urllib.parse
        import zlib
        path, page_name, scale, dx, dy = self.layout_from
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as e:
            self.warnings.append(f"layout_from: {path} not readable ({e}) — own layout used")
            return {}
        models = []
        if root.tag == 'mxGraphModel':
            models.append(('', root))
        for d in root.findall('diagram'):
            m = d.find('mxGraphModel')
            if m is None and (d.text or '').strip():
                try:
                    raw = zlib.decompress(base64.b64decode(d.text.strip()), -15).decode('utf-8')
                    m = ET.fromstring(urllib.parse.unquote(raw))
                except Exception:          # pragma: no cover — rikkinäinen sivu ohitetaan
                    m = None
            if m is not None:
                models.append((d.get('name') or '', m))
        model = next((m for n, m in models if n.lower() == page_name.lower()), None)
        if model is None:
            names = ', '.join(n or '(unnamed)' for n, _ in models)
            self.warnings.append(f"layout_from: page '{page_name}' not found in {path} (pages: {names}) — own layout used")
            return {}
        cells = {c.get('id'): c for c in model.iter('mxCell')}
        boxes: Dict[str, Tuple[float, float]] = {}
        for cid, c in cells.items():
            style = c.get('style') or ''
            if c.get('vertex') != '1' or style.startswith('text;') or 'edgyRole=' in style \
                    or 'fillColor=#f5f5f5' in style:      # legendan tausta, tekstit ja otsikot eivät ole kohteita
                continue
            label = html.unescape(re.sub(r'<br\s*/?>', '\n', c.get('value') or '', flags=re.I))
            label = re.sub(r'<[^>]+>', '', label).strip().split('\n')[0].strip()
            box = _geo.abs_box(cells, cid)
            if label and box:
                boxes.setdefault(label.lower(), (box[0], box[1]))
        targets = {eid: {e['value'].lower(), (e.get('name') or '').lower()}
                   for eid, e in self.elements.items() if e.get('group') is None}
        targets.update({gid: {g['name'].lower()} for gid, g in self.groups.items()
                        if g.get('parent') is None and not g.get('synthetic')})
        positions: Dict[str, Tuple[float, float]] = {}
        matched = set()
        for key, cands in targets.items():
            for c in cands:
                if c in boxes:
                    vx, vy = boxes[c]
                    positions[key] = ((vx + dx) * scale, (vy + dy) * scale)
                    matched.add(c)
                    break
        if not positions:
            self.warnings.append(f"layout_from: no element or area matched page '{page_name}' — own layout used")
        return positions

    def _positions_from_archimate(self) -> Dict[str, Tuple[float, float]]:
        """Lue ArchiMate-näkymän (Archi .archimate) elementtien sijainnit ja
        kohdista ne EDGY-elementteihin nimen perusteella (case-insensitive;
        myös nimi ennen ' - ' / ' | ' -erotinta).

        T(x, y) = ((x + dx) · S, (y + dy) · S). Palauttaa {elem_id: (x, y)} vain
        niille elementeille, joille löytyi vastine. Elementit, joita näkymässä
        on mutta syötteessä ei, listataan varoitukseen ("puuttuu
        tavoitetilasta"), jotta nykytilan aukot näkyvät.
        """
        if not self.layout_from:
            return {}
        path, view_name, scale, dx, dy = self.layout_from
        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError) as e:
            self.warnings.append(f"layout_from: {path} ei luettavissa ({e}) — käytetään omaa asettelua")
            return {}
        root = tree.getroot()
        XSI = '{http://www.w3.org/2001/XMLSchema-instance}type'
        names_by_id = {}
        for el in root.iter():
            if el.get('id') and el.get('name') and not (el.get(XSI) or '').endswith('DiagramModel'):
                names_by_id[el.get('id')] = el.get('name')
        view = None
        for el in root.iter():
            if (el.get(XSI) or '').endswith('ArchimateDiagramModel') and el.get('name', '').lower() == view_name.lower():
                view = el
                break
        if view is None:
            self.warnings.append(f"layout_from: näkymää '{view_name}' ei löydy tiedostosta {path}")
            return {}
        view_boxes: Dict[str, Tuple[float, float]] = {}

        def walk(node, ox, oy):
            for child in node.findall('child'):
                b = child.find('bounds')
                if b is None:
                    continue
                x = ox + float(b.get('x', 0)); y = oy + float(b.get('y', 0))
                ref = child.get('archimateElement')
                name = names_by_id.get(ref) or child.get('name')
                if name:
                    view_boxes[name.lower()] = (x, y)
                walk(child, x, y)
        walk(view, 0.0, 0.0)

        positions: Dict[str, Tuple[float, float]] = {}
        matched = set()
        for eid, e in self.elements.items():
            cands = {e['value'].lower(), (e.get('name') or '').lower()}
            for c in cands:
                if c in view_boxes:
                    vx, vy = view_boxes[c]
                    positions[eid] = ((vx + dx) * scale, (vy + dy) * scale)
                    matched.add(c)
                    break
        missing = sorted(n for n in view_boxes if n not in matched)
        if missing:
            self.warnings.append(
                f"layout_from: näkymässä '{view_name}' on {len(missing)} elementtiä, joita ei ole tavoitetilassa: "
                + ", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")
                + " — merkitse ne poistuviksi tai lisää ne syötteeseen")
        if not positions:
            self.warnings.append(f"layout_from: yhtään elementtiä ei kohdistunut näkymään '{view_name}' — käytetään omaa asettelua")
        return positions

    @staticmethod
    def _split_name(value: str) -> Tuple[str, str]:
        """Jaa "Nimi - Kuvaus" tai "Nimi | alateksti" → (nimi, alateksti)."""
        for sep in (' | ', ' - ', ' — '):
            if sep in value:
                name, sub = value.split(sep, 1)
                return name.strip(), sub.strip()
        return value.strip(), ''

    def _parse_relationship_options(self, text: str) -> dict:
        """Jäsennä relaation optiot: from/to (sivu), via (taitepisteet), change, label."""
        options = {}
        via_match = re.search(r'via\s*:\s*\[([^\]]*)\]', text)
        if via_match:
            pts = re.findall(r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', via_match.group(1))
            options['via'] = [(float(x), float(y)) for x, y in pts]
            text = text[:via_match.start()] + text[via_match.end():]
        for pair in text.split(','):
            if ':' not in pair:
                continue
            k, v = pair.split(':', 1)
            k, v = k.strip().lower(), v.strip()
            if k in ('from', 'to'):
                if v.lower() in ('left', 'right', 'top', 'bottom'):
                    options[k] = v.lower()
                else:
                    self.warnings.append(f"Tuntematon {k}-arvo '{v}' (sallitut: left, right, top, bottom), ohitetaan")
            elif k in ('change', 'color'):
                change = CHANGE_SYNONYMS.get(v.lower())
                if change is None:
                    self.warnings.append(f"Tuntematon change-arvo '{v}' relaatiolla (sallitut: {', '.join(CHANGE_PALETTE)}), ohitetaan")
                else:
                    options['change'] = change
            elif k == 'label':
                if v.lower() in ('source', 'middle', 'target'):
                    options['label'] = v.lower()
                else:
                    self.warnings.append(f"Tuntematon label-arvo '{v}' (sallitut: source, middle, target), ohitetaan")
            elif k in ('label_dx', 'label_dy'):
                # tekstin siirtymä pikseleinä (draw.io: <mxPoint as="offset">)
                try:
                    options[k] = float(v)
                except ValueError:
                    self.warnings.append(f"Virheellinen {k}-arvo '{v}' (luku pikseleinä), ohitetaan")
            else:
                self.warnings.append(f"Tuntematon relaatio-optio '{k}', ohitetaan")
        return options

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

        # 2. Nimiosuma (nimi ennen " - " / " | " -erotinta)
        for element_id, element in self.elements.items():
            name = element.get('name') or self._split_name(element['value'])[0]
            if name.lower() == value_lower:
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
        """Rakenna elementin näyttöarvo: lihavoitu nimi, alateksti (id + kuvaus), tagit/metriikat.

        Label-standardi: `<b>Nimi</b>` ensimmäisellä rivillä; `[ID] kuvaus` pienellä
        toisella rivillä; tagit ja metriikat omalla rivillään. Tyyppiä ei toisteta
        nimessä — se näkyy muodosta ja väristä.
        """
        name = element.get('name') or element['value']
        subtext = element.get('subtext', '')
        ref = element.get('ref')
        tags = element.get('tags', [])
        metrics = element.get('metrics', {})

        if not subtext and not ref and not tags and not metrics:
            return html.escape(name)

        parts = [f'<b>{html.escape(name)}</b>']
        sub_bits = []
        if ref:
            sub_bits.append(f'[{html.escape(ref)}]')
        if subtext:
            sub_bits.append(html.escape(subtext))
        if sub_bits:
            parts.append('<font style="font-size:9px;color:#444444;font-weight:normal">' + ' '.join(sub_bits) + '</font>')

        # Metriikan värikoodaus
        metric_colors = {
            'good': '#2e7d32', 'hyvä': '#2e7d32', 'bon': '#2e7d32', 'gut': '#2e7d32',
            'ok': '#f57f17', 'keskiverto': '#f57f17', 'moyen': '#f57f17', 'mittel': '#f57f17',
            'bad': '#c62828', 'huono': '#c62828', 'mauvais': '#c62828', 'schlecht': '#c62828',
            'high': '#c62828', 'korkea': '#c62828', 'élevé': '#c62828', 'hoch': '#c62828',
            'low': '#2e7d32', 'matala': '#2e7d32', 'bas': '#2e7d32', 'niedrig': '#2e7d32',
        }
        label_parts = [html.escape(tag) for tag in tags]
        for k, v in metrics.items():
            color = metric_colors.get(v.lower(), '#666666')
            label_parts.append(f'<font color="{color}">{html.escape(k)}: {html.escape(v)}</font>')
        if label_parts:
            parts.append('<font style="font-size:9px;font-weight:normal">' + ' | '.join(label_parts) + '</font>')
        return '<br>'.join(parts)

    def _subtext_lines(self, element: dict, width: int) -> int:
        """Alatekstirivien määrä (id + kuvaus) annetulla leveydellä — mitattu 9 px
        normaalilla leikkauksella (edgy_text), ei merkkimäärällä."""
        sub = ' '.join(x for x in ((f"[{element['ref']}]" if element.get('ref') else ''), element.get('subtext', '')) if x)
        if not sub:
            return 0
        return _text.lines_needed(sub, max(width - 12, 40), self._SUB_FONT, bold=False)

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
    _TITLE_FONT = 14     # nimen fontti (fontStyle=1 → lihavoitu), sama kuin _get_element_style
    _SUB_FONT = 9        # alatekstin fontti (normaali leikkaus), sama kuin _build_display_value
    _WIDTH_PADDING = 20  # sisämarginaali molemmin puolin
    _MAX_WIDTH = 280     # leveimmän elementin yläraja

    def _get_element_size(self, element: dict, force_w: int = None) -> Tuple[int, int]:
        """Palauta elementin (leveys, korkeus). `force_w` ohittaa leveyden laskennan
        (equal_cards: yhteinen leveys, korkeus lasketaan siitä).

        - Leveys lasketaan NIMEN pituudesta (ei kuvauksesta): min 120 (rect),
          140 (pentagon), 60 (person), max 280, pyöristys 10:een.
        - Korkeus kasvaa alatekstiriveistä (id + kuvaus) ja tagi/metriikkarivistä.
        - `{size: S|M|L}` antaa minimikoon: S 120×60, M 200×90, L 270×120.
        - Ryhmille ja kaistoille koko tulee layoutista (_computed_sizes).
        """
        import math
        if element.get('type') in STRUCTURE_TYPES:
            return self._computed_sizes.get(element['id'], (300, 160))
        if force_w is None and element['id'] in self._size_override:   # layoutin pakottama koko (triad, equal_cards)
            return self._size_override[element['id']]
        shape = EDGY_SHAPES.get(element['type'], 'rect')

        if shape == 'pentagon':
            min_w, h = 140, 60
        elif shape == 'person':
            min_w, h = 60, 80
        else:
            min_w, h = 120, 60

        size_class = element.get('size_class')
        if size_class in SIZE_CLASSES:
            cw, ch = SIZE_CLASSES[size_class]
            min_w, h = max(min_w, cw), max(h, ch)

        name = element.get('name') or element.get('value', '')
        # Leveys NIMEN mitatusta leveydestä (14 px bold, edgy_text): pentagonin
        # nuolenkärki vie dx=20 px tekstialueesta
        tip = 20 if shape == 'pentagon' else 0
        text_w = _text.measure(name, self._TITLE_FONT, bold=True) + self._WIDTH_PADDING + tip
        w = max(min_w, min(text_w, self._MAX_WIDTH))
        if self.card_width and shape != 'person':
            w = max(self.card_width, cw if size_class in SIZE_CLASSES else 0)   # card_width: nimi rivittyy, kokoluokka voi olla leveämpi
        w = int(math.ceil(w / 10) * 10)
        if force_w is not None:
            w = int(force_w)

        # Nimi rivittyy jos se ei mahdu yhdelle riville — rivitys mitattuna, ei arvioituna
        name_lines = _text.lines_needed(name, max(w - 16 - tip, 40), self._TITLE_FONT, bold=True)
        extra = (name_lines - 1) * 18
        extra += self._subtext_lines(element, w) * 14
        if element.get('tags') or element.get('metrics'):
            extra += 16
        if element.get('maturity') or element.get('rating'):
            extra += BADGE_H + 4                 # tilamerkki kortin alareunassa (laajennus)
        if not size_class:
            h = h + extra if extra else h
        else:
            h = max(h, 60 + extra)
        h = int(math.ceil(h / 10) * 10)
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
        sizes = {eid: self._size_of(eid) for eid in positions}

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

        Sisällön vasen yläkulma on aina (MARGIN, MARGIN): sama marginaali
        jokaisella sivulla ja jokaisessa sarjan kartassa (lint W121).
        """
        MARGIN = 60
        if not positions:
            return
        min_x = min(x for x, y in positions.values())
        min_y = min(y for x, y in positions.values())
        shift_x = MARGIN - min_x
        shift_y = MARGIN + getattr(self, '_top_reserve', 0) - min_y
        if shift_x or shift_y:
            for eid in positions:
                x, y = positions[eid]
                positions[eid] = (x + shift_x, y + shift_y)

    def _snap_to_grid(self, positions: Dict[str, Tuple[int, int]]) -> None:
        """Pyöristä kaikki koordinaatit lähimpään 10:n kerrannaiseen."""
        for eid in positions:
            x, y = positions[eid]
            positions[eid] = (round(x / 10) * 10, round(y / 10) * 10)

    def _get_element_style(self, element) -> str:
        """Palauta EDGY-elementin draw.io-tyyli virallisen notaation mukaan.

        Hyväksyy elementtityypin (str) tai elementti-dictin. Dictillä lisätään
        muutoskerros (`change` → reunaväri/-paksuus, täyttö pysyy fasetin värinä)
        ja korostus (`[focus]` / `{highlight: yes}` → tumma paksu reuna).
        """
        if isinstance(element, dict):
            element_type = element['type']
        else:
            element_type, element = element, {}
        colors = EDGY_COLORS.get(element_type, {'fill': '#ffffff', 'stroke': '#262626'})
        shape = EDGY_SHAPES.get(element_type, 'rect')
        fill = colors['fill']
        stroke = colors['stroke'] if element_type in BASE_ELEMENTS else '#FFFFFF'
        stroke_width = 2
        extra = ''
        if element.get('change'):
            stroke, dashed = CHANGE_PALETTE[element['change']]
            stroke_width = 4
            if dashed:
                extra += 'dashed=1;dashPattern=8 4;'
        elif element.get('highlight'):
            stroke, stroke_width = '#555555', 4

        base = f"whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth={stroke_width};{extra}"
        if shape == 'rounded_rect':
            return f"rounded=1;{base}arcSize=10;verticalAlign=middle;fontStyle=1;fontSize=14;"
        elif shape == 'pentagon':
            return f"shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;{base}verticalAlign=middle;fontStyle=1;fontSize=14;"
        elif shape == 'person':
            return f"shape=mxgraph.basic.person;{base}verticalAlign=middle;fontStyle=1;fontSize=12;"
        else:  # rect
            return f"{base}verticalAlign=middle;fontStyle=1;fontSize=14;"

    def _effective_group_style(self) -> str:
        """group_style: annettu arvo, muuten official kun ryhmiä on sisäkkäin, muuten light."""
        if self.group_style:
            return self.group_style
        return 'official' if any(g.get('parent') is not None for g in self.groups.values()) else 'light'

    def _group_facet_fill(self, gid: str) -> Optional[str]:
        """Kontin kaikkien jälkeläiselementtien yhteinen fasettiväri (esim. #a6c0ff), muuten None
        (sekalaiset fasetit tai valkoiset perustyypit)."""
        fills, stack = set(), [gid]
        while stack:
            g = self.groups[stack.pop()]
            fills.update(EDGY_COLORS.get(self.elements[m]['type'], {}).get('fill', '#ffffff')
                         for m in g['members'] if m not in self._hidden)
            stack.extend(g.get('subgroups') or [])
        if len(fills) == 1:
            fill = fills.pop()
            return None if fill.lower() == '#ffffff' else fill
        return None

    def _get_group_style(self, group: dict) -> str:
        """Tyyli ryhmäkontille (container) tai kaistalle (lane).

        group_style official (virallinen EDGY 23 -kyvykkyyskartta): kontti jossa on aliryhmiä =
        jäsenten fasettiväri, valkoinen reuna; lehtikontti sisällä = valkoinen ilman reunaa;
        ylimmän tason lehtikontti = valkoinen, fasetin värinen reuna. Synteettiset facet- ja
        triad-kontit pitävät oman tyylinsä."""
        if group['kind'] == 'lane':
            return ("whiteSpace=wrap;html=1;fillColor=#f4f4f4;strokeColor=none;align=left;verticalAlign=top;"
                    "spacingLeft=8;spacingTop=4;fontColor=#555555;fontSize=11;fontStyle=1;")
        synthetic = group.get('synthetic')
        if self._effective_group_style() == 'official' and synthetic in (None, 'stage'):
            facet_fill = self._group_facet_fill(group['id'])
            if group.get('subgroups'):
                fill, stroke = facet_fill or FACET_CONTAINER_FILLS['group'], '#ffffff'
            elif group.get('parent') is not None:
                fill, stroke = '#ffffff', 'none'
            else:
                fill, stroke = '#ffffff', facet_fill or '#d0d4dc'
            return (f"rounded=1;arcSize=8;container=1;collapsible=0;whiteSpace=wrap;html=1;"
                    f"fillColor={fill};strokeColor={stroke};strokeWidth=2;align=left;verticalAlign=top;"
                    f"spacingLeft=10;spacingTop=4;fontSize=13;fontStyle=1;fontColor=#333333;edgyGroup=official;")
        fill = FACET_CONTAINER_FILLS.get(group.get('facet', 'group'), FACET_CONTAINER_FILLS['group'])
        stroke = '#d0d4dc' if group.get('facet') == 'further' else '#ffffff'
        return (f"rounded=1;arcSize=6;container=1;collapsible=0;whiteSpace=wrap;html=1;"
                f"fillColor={fill};strokeColor={stroke};strokeWidth=2;align=left;verticalAlign=top;"
                f"spacingLeft=10;spacingTop=4;fontSize=12;fontStyle=1;fontColor=#333333;")

    def _size_of(self, eid: str) -> Tuple[int, int]:
        """Koko elementille tai ryhmälle/kaistalle."""
        if eid in self.groups:
            return self._computed_sizes.get(eid, (300, 160))
        return self._get_element_size(self.elements[eid])

    def generate_xml(self) -> str:
        """Generoi draw.io XML EDGY-elementeistä. Sivukoko skaalautuu sisällön mukaan.

        Rakenne: kontit ja kaistat ensin (taustalle), sitten elementit (kontin
        lapset `parent`-viittauksella ja suhteellisin koordinaatein), sitten
        relaatiot (ankkurit, taitepisteet, muutosväri, yhdistetyt labelit) ja
        lopuksi legenda (+ muutoskerroksen rivit, jos kerros on käytössä).
        """
        import math as _math

        abs_pos = self._calculate_layout()              # kaikkien elementtien absoluuttiset sijainnit
        group_pos = self._group_positions               # ryhmien/kaistojen sijainnit
        sizes = {eid: self._get_element_size(self.elements[eid]) for eid in self.elements}
        positions = {**{eid: abs_pos[eid] for eid, e in self.elements.items() if e.get('group') is None},
                     **group_pos}                        # top-level-kohteet sivukokoa ja legendaa varten

        # Dynaaminen sivukoko: top-level bounding box + marginaali
        boxes = [(positions[i][0] + self._size_of(i)[0], positions[i][1] + self._size_of(i)[1]) for i in positions]
        if boxes:
            max_x = max(bx for bx, _ in boxes)
            max_y = max(by for _, by in boxes)
            page_width = max(1200, int(_math.ceil((max_x + 80) / 100) * 100))
            page_height = max(900, int(_math.ceil((max_y + 80) / 100) * 100))
        else:
            page_width, page_height = 1200, 900
        legend_mode = self._effective_legend()
        if legend_mode == 'strip':
            # Nauha alareunassa: sivun korkeus on sisältö + nauha, ei editorin 900 px oletus —
            # harva kartta ei huku tyhjään kanvakseen
            band_h = self._legend_strip_height(page_width)
            content_bottom = max((positions[i][1] + self._size_of(i)[1] for i in positions), default=0)
            page_height = max(300, int(_math.ceil((content_bottom + 30 + band_h + 16) / 10) * 10))
        else:
            # Legenda tarvitsee tilaa oikeasta alakulmasta: kasvata sivua jos sisältö ulottuu sinne
            legend_h = (self._LEGEND_BOX_H + (self._overlay_legend_height() if self.uses_change_overlay else 0)
                        + self._badge_legend_height())
            legend_w = 220
            for i in positions:
                x, y = positions[i]
                w, h = self._size_of(i)
                if x + w > page_width - legend_w - 40 and y + h > page_height - legend_h - 40:
                    page_height = int(_math.ceil((y + h + legend_h + 60) / 100) * 100)

        root = ET.Element("mxGraphModel", {
            "dx": str(page_width + 240), "dy": str(page_height - 24),
            "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1",
            "arrows": "1", "fold": "1", "page": "1", "pageScale": "1",
            "pageWidth": str(page_width), "pageHeight": str(page_height), "math": "0", "shadow": "0",
        })
        mx_root = ET.SubElement(root, "root")
        ET.SubElement(mx_root, "mxCell", {"id": "0"})
        ET.SubElement(mx_root, "mxCell", {"id": "1", "parent": "0"})

        next_id = 2
        element_mapping: Dict[str, str] = {}

        # 1) Ryhmät ja kaistat (taustalle, ennen elementtejä); sisäkkäinen kontti vanhempansa lapseksi
        for gid in sorted(self.groups, key=self._group_depth):
            group = self.groups[gid]
            if gid not in group_pos:
                continue
            gx, gy = group_pos[gid]
            parent_gid = group.get('parent')
            if parent_gid is not None and parent_gid in element_mapping:
                parent_cell = element_mapping[parent_gid]
                gx, gy = self._child_positions.get(gid, (20, 40))
            else:
                parent_cell = "1"
            gw, gh = self._size_of(gid)
            cell = ET.SubElement(mx_root, "mxCell", {
                "id": str(next_id), "value": html.escape(group['name']),
                "style": self._get_group_style(group), "vertex": "1", "parent": parent_cell,
            })
            ET.SubElement(cell, "mxGeometry", {"x": str(int(round(gx))), "y": str(int(round(gy))),
                                               "width": str(int(gw)), "height": str(int(gh)), "as": "geometry"})
            element_mapping[gid] = str(next_id)
            next_id += 1

        # 1b) Vaiheotsikot kaistojen yläpuolelle (edgyRole=header: lint lukee ne sisällöksi)
        lanes = [g for g in self.groups.values() if g['kind'] == 'lane' and g['id'] in group_pos]
        if self.stages and lanes:
            first = min(lanes, key=lambda g: group_pos[g['id']][1])
            lx, ly = group_pos[first['id']]
            col_w = max([self._get_element_size(self.elements[m])[0] for g in lanes for m in g['members']] + [120])
            for i, stage in enumerate(self.stages):
                cell = ET.SubElement(mx_root, "mxCell", {
                    "id": str(next_id), "value": html.escape(stage),
                    "style": "text;html=1;align=center;verticalAlign=middle;fontSize=12;fontStyle=1;fontColor=#333333;edgyRole=header;",
                    "vertex": "1", "parent": "1",
                })
                ET.SubElement(cell, "mxGeometry", {"x": str(int(round(lx + 20 + i * (col_w + 20)))), "y": str(int(round(ly - 30))),
                                                   "width": str(int(col_w)), "height": "24", "as": "geometry"})
                next_id += 1

        # 2) Elementit
        for idx, (elem_id, element) in enumerate(self.elements.items()):
            if elem_id in self._hidden:
                continue
            style = self._get_element_style(element)
            if elem_id in self._triad_hidden:
                style = style.replace('fontSize=14;', 'fontSize=12;')   # paneelisirut: pienempi otsikko
            w, h = sizes[elem_id]
            gid = element.get('group')
            if gid is not None and self.groups[gid]['kind'] == 'group' and gid in element_mapping:
                parent = element_mapping[gid]
                x, y = self._child_positions.get(elem_id, (20, 40))
            else:
                parent = "1"
                x, y = abs_pos.get(elem_id, (100 + idx * 160, 100))
            cell = ET.SubElement(mx_root, "mxCell", {
                "id": str(next_id), "value": self._build_display_value(element),
                "style": style, "vertex": "1", "parent": parent,
            })
            ET.SubElement(cell, "mxGeometry", {"x": str(int(round(x))), "y": str(int(round(y))),
                                               "width": str(w), "height": str(h), "as": "geometry"})
            element_mapping[elem_id] = str(next_id)
            next_id += 1
            badge = self._badge_of(element)
            if badge:
                # Kortin lapsisolu (suhteelliset koordinaatit): liikkuu kortin mukana draw.iossa;
                # edgyRole=badge → lint ei pidä sitä elementtinä eikä vaadi sille paletin väriä
                text, colour = badge
                bw = min(w - 12, max(36, int(_text.measure(text, 9, bold=True)) + 14))
                cell = ET.SubElement(mx_root, "mxCell", {
                    "id": str(next_id), "value": html.escape(text),
                    "style": (f"rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor={colour};strokeColor=#ffffff;"
                              f"strokeWidth=1;fontSize=9;fontStyle=1;fontColor={_badge_text_colour(colour)};edgyRole=badge;"),
                    "vertex": "1", "parent": element_mapping[elem_id]})
                ET.SubElement(cell, "mxGeometry", {"x": str(int((w - bw) / 2)), "y": str(int(h - BADGE_H - 4)),
                                                   "width": str(bw), "height": str(BADGE_H), "as": "geometry"})
                next_id += 1

        # 3) Relaatiot — yhdistä saman parin useat relaatiot yhdeksi reunaksi ("a / b")
        merged: Dict[Tuple[str, str], dict] = {}
        order: List[Tuple[str, str]] = []
        for rel in self.relationships:
            if rel['source'] not in element_mapping or rel['target'] not in element_mapping:
                continue
            key = (rel['source'], rel['target'])
            if key in merged:
                m = merged[key]
                if rel['label'] not in m['labels']:
                    m['labels'].append(rel['label'])
                if rel.get('kind') == 'link':
                    m['kind'] = 'link'
                m['options'] = {**rel.get('options', {}), **m['options']}
            else:
                merged[key] = {'source': key[0], 'target': key[1], 'labels': [rel['label']],
                               'kind': rel.get('kind'), 'options': dict(rel.get('options', {}))}
                order.append(key)

        from collections import defaultdict
        outgoing_by_side = defaultdict(list)
        incoming_by_side = defaultdict(list)
        valid_rels = []
        triad = self.map_type == 'triad'
        if triad and self._triad_hidden:
            # Paneeleihin jääneiden elementtien linkkejä ei piirretä — raportoidaan, ei pudoteta hiljaa
            dropped = [k for k in order if k[0] in self._triad_hidden or k[1] in self._triad_hidden]
            if dropped:
                names = ', '.join(f"{self.elements[s]['name']} → {self.elements[t]['name']}" for s, t in dropped[:6])
                self.warnings.append(
                    f"triad: {len(dropped)} relationship(s) not drawn (non-primary endpoint in a Further panel): "
                    f"{names}{' …' if len(dropped) > 6 else ''} — the report tables carry them")
                order = [k for k in order if k not in set(dropped)]
        for key in order:
            rel = merged[key]
            sx, sy = abs_pos[rel['source']]
            tx, ty = abs_pos[rel['target']]
            sw, sh = sizes[rel['source']]
            tw, th = sizes[rel['target']]
            exit_side = _geo.choose_side((sx, sy, sw, sh), (tx, ty, tw, th))
            entry_side = _geo.opposite(exit_side)
            if (rel.get('kind') == 'tree' and exit_side in ('left', 'right') and ty >= sy + sh + 20
                    and not triad):
                # Puun haara: lapsi kokonaan vanhemman alla → alareunasta yläreunaan (ei sivun kautta
                # sisarusten läpi, kun leveät laatikot tekevät vaakaerosta pystyeroa suuremman)
                exit_side, entry_side = 'bottom', 'top'
            # Samalla kaistalla samalla rivillä, ei vierekkäin → reititys yläkautta (U-muoto),
            # jotta reuna ei kulje välissä olevien elementtien läpi
            sg = self.elements[rel['source']].get('group')
            if (sg is not None and sg == self.elements[rel['target']].get('group')
                    and self.groups[sg]['kind'] == 'lane' and abs(sy - ty) < 5):
                members = self.groups[sg]['members']
                if abs(members.index(rel['source']) - members.index(rel['target'])) > 1:
                    exit_side = entry_side = 'top'
            exit_side = rel['options'].get('from', exit_side)
            entry_side = rel['options'].get('to', entry_side)
            valid_rels.append((rel, exit_side, entry_side))
            outgoing_by_side[(rel['source'], exit_side)].append(len(valid_rels) - 1)
            incoming_by_side[(rel['target'], entry_side)].append(len(valid_rels) - 1)

        _distribute = _geo.distribute        # porttien jako 0.15–0.85, sama kuin renderöijällä ja lintillä

        for vi, (rel, exit_side, entry_side) in enumerate(valid_rels):
            src_list = outgoing_by_side[(rel['source'], exit_side)]
            tgt_list = incoming_by_side[(rel['target'], entry_side)]
            src_idx, tgt_idx = src_list.index(vi), tgt_list.index(vi)
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
            anchor_style = (f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
                            f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;")
            style = self._get_edge_style(rel['labels'][0], rel['kind'])
            key = (rel['source'], rel['target'])
            if triad and not any(k in rel['options'] for k in ('label', 'label_dx', 'label_dy')):
                # oletussiirtymä tekstille: pois lähimmästä laatikosta, slot-parin mukaan
                pair = (self.elements[key[0]]['type'], self.elements[key[1]]['type'])
                shift = self._TRIAD_DETOUR_SHIFT.get(key in self._triad_detours and self._triad_detours[key][0]) \
                    if key in self._triad_detours else self._TRIAD_LABEL_SHIFT.get(pair)
                if shift:
                    rel['options'] = {**rel['options'], 'label_dx': shift[0], 'label_dy': shift[1]}
            if triad and key in self._triad_detours:
                # kehää kiertävä linkki: ortogonaalinen, kiinteät portit ja taitepisteet
                d_exit, d_entry, d_points = self._triad_detours[key]
                ex, ey = {'left': (0, 0.5), 'right': (1, 0.5), 'top': (0.5, 0), 'bottom': (0.5, 1)}[d_exit]
                nx, ny = {'left': (0, 0.5), 'right': (1, 0.5), 'top': (0.5, 0), 'bottom': (0.5, 1)}[d_entry]
                style += f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
                rel['options'] = {**rel['options'], 'via': d_points}
            elif triad:
                # suora viiva reunasta reunaan: draw.io laskee kehäpisteet keskipisteiden suoralta
                style = style.replace("edgeStyle=orthogonalEdgeStyle;rounded=1;", "edgeStyle=none;rounded=0;")
                pair = (self.elements[key[0]]['type'], self.elements[key[1]]['type'])
                if 'from' in rel['options'] or 'to' in rel['options']:
                    style += anchor_style
                elif pair in self._TRIAD_ANCHORS:
                    (ex, ey), (nx, ny) = self._TRIAD_ANCHORS[pair]
                    style += f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
            else:
                style += anchor_style
            change = rel['options'].get('change')
            if change:
                color, dashed = CHANGE_PALETTE[change]
                style += f"strokeColor={color};fontColor={color};strokeWidth=1.5;"
                if dashed:
                    style += "dashed=1;dashPattern=8 4;"
            cell = ET.SubElement(mx_root, "mxCell", {
                "id": str(next_id), "value": " / ".join(self._render_verb(v, (self.elements[rel['source']]['type'], self.elements[rel['target']]['type']))
                                                        for v in rel['labels']), "style": style,
                "edge": "1", "source": element_mapping[rel['source']],
                "target": element_mapping[rel['target']], "parent": "1",
            })
            geo_attrs = {"relative": "1", "as": "geometry"}
            label_pos = rel['options'].get('label')
            if label_pos == 'source':
                geo_attrs["x"] = "-0.5"
            elif label_pos == 'target':
                geo_attrs["x"] = "0.5"
            geo = ET.SubElement(cell, "mxGeometry", geo_attrs)
            if 'label_dx' in rel['options'] or 'label_dy' in rel['options']:
                # absoluuttinen tekstin siirtymä pikseleinä (sama sopimus renderöijässä ja lintissä)
                ET.SubElement(geo, "mxPoint", {"x": str(int(round(rel['options'].get('label_dx', 0)))),
                                               "y": str(int(round(rel['options'].get('label_dy', 0)))), "as": "offset"})
            if rel['options'].get('via'):
                arr = ET.SubElement(geo, "Array", {"as": "points"})
                for px, py in rel['options']['via']:
                    ET.SubElement(arr, "mxPoint", {"x": str(int(round(px))), "y": str(int(round(py)))})
            next_id += 1

        # 4) Legenda: laatikko oikeaan alakulmaan tai nauha alareunaan
        if legend_mode == 'strip':
            self._append_legend_strip(mx_root, next_id, page_width, page_height)
        else:
            self._append_legend_cells(mx_root, next_id, page_width, page_height)
        return self._prettify_xml(root)

    # Legendan värit ja viivatyylit; tekstit tulevat LEGEND_TEXT[language]-taulusta
    _CHIP_COLOURS = ("#80ffb7", "#a6c0ff", "#ff99bd", "#ffd580", "#e599ff", "#80eaff")
    _LINE_STYLES = ("endArrow=classic;endFill=1;strokeWidth=1;strokeColor=#333333;",
                    "endArrow=open;endFill=0;strokeWidth=1;strokeColor=#333333;",
                    "endArrow=none;strokeWidth=1;strokeColor=#333333;",
                    "endArrow=open;endFill=0;dashed=1;strokeWidth=1;strokeColor=#333333;")
    _STRIP_ROW = 24

    def _legend_strip_rows(self, page_width: int) -> int:
        """Rivimäärä: palat ja viivamallit yhdellä rivillä jos mahtuvat, muuten kahdella; muutoskerros omalla rivillään."""
        L = self._legend_text()
        chips_w = sum(18 + _text.measure(lbl, 9) + 6 + 14 for lbl in L['chips_short'])
        lines_w = sum(28 + 4 + _text.measure(lbl, 9) + 6 + 14 for lbl in L['lines_short'])
        rows = 1 if 130 + chips_w + lines_w <= page_width - 40 else 2
        return rows + (1 if self.uses_change_overlay else 0) + len(self._badge_legend_sections())

    def _legend_strip_base_rows(self, page_width: int) -> int:
        return self._legend_strip_rows(page_width) - (1 if self.uses_change_overlay else 0) - len(self._badge_legend_sections())

    def _badge_legend_height(self) -> int:
        return sum(26 + len(items) * 16 + 10 for _t, items in self._badge_legend_sections())

    def _legend_strip_height(self, page_width: int) -> int:
        return self._legend_strip_rows(page_width) * self._STRIP_ROW

    def _append_legend_strip(self, mx_root, start_id: int, page_width: int, page_height: int) -> None:
        """EDGY-legenda yhtenä kapeana nauhana sivun alareunassa (`legend: strip`).

        Täyttää E009:n rakenteellisen tunnistuksen: otsikkotekstisolu, ≥ 3
        värillistä palaa ja ≥ 1 irrallinen viivamalli (edge ilman source/target).
        """
        L = self._legend_text()
        rows = self._legend_strip_rows(page_width)
        row_h = self._STRIP_ROW
        band_h = rows * row_h
        y0 = page_height - 16 - band_h
        cid = start_id

        def text_cell(value, x, y, w, h, bold=False, size=9, extra=''):
            nonlocal cid
            style = (f"text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;"
                     f"fontSize={size};" + ("fontStyle=1;" if bold else "") + extra)
            cell = ET.SubElement(mx_root, "mxCell", {"id": str(cid), "value": value, "style": style, "vertex": "1", "parent": "1"})
            ET.SubElement(cell, "mxGeometry", {"x": str(int(x)), "y": str(int(y)), "width": str(int(w)), "height": str(int(h)), "as": "geometry"})
            cid += 1

        bg = ET.SubElement(mx_root, "mxCell", {
            "id": str(cid), "value": "",
            "style": "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#e5e5e5;strokeWidth=1;",
            "vertex": "1", "parent": "1"})
        ET.SubElement(bg, "mxGeometry", {"x": "20", "y": str(y0 - 4), "width": str(page_width - 40), "height": str(band_h + 8), "as": "geometry"})
        cid += 1

        x = 30
        text_cell(f"<b>{html.escape(L['title'])}</b>", x, y0, 120, row_h, bold=True, size=10, extra=self._lang_marker())
        x += 130
        for color, label in zip(self._CHIP_COLOURS, L['chips_short']):
            chip = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": "",
                "style": f"rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#ffffff;strokeWidth=1;",
                "vertex": "1", "parent": "1"})
            ET.SubElement(chip, "mxGeometry", {"x": str(x), "y": str(y0 + 6), "width": "14", "height": "12", "as": "geometry"})
            cid += 1
            tw = int(_text.measure(label, 9) + 6)
            text_cell(html.escape(label), x + 18, y0, tw, row_h)
            x += 18 + tw + 14
        base_rows = self._legend_strip_base_rows(page_width)
        if base_rows == 2:
            x, y_line = 160, y0 + row_h          # viivamallit toiselle riville
        else:
            y_line = y0
        for edge_style, label in zip(self._LINE_STYLES, L['lines_short']):
            arrow = ET.SubElement(mx_root, "mxCell", {"id": str(cid), "value": "", "style": f"edgeStyle=none;{edge_style}", "edge": "1", "parent": "1"})
            geo = ET.SubElement(arrow, "mxGeometry", {"relative": "1", "as": "geometry"})
            ET.SubElement(geo, "mxPoint", {"x": str(x), "y": str(y_line + 12), "as": "sourcePoint"})
            ET.SubElement(geo, "mxPoint", {"x": str(x + 28), "y": str(y_line + 12), "as": "targetPoint"})
            cid += 1
            tw = int(_text.measure(label, 9) + 6)
            text_cell(html.escape(label), x + 32, y_line, tw, row_h)
            x += 28 + 4 + tw + 14
        for n, (title, items) in enumerate(self._badge_legend_sections()):
            x, y_b = 30, y0 + (base_rows + (1 if self.uses_change_overlay else 0) + n) * row_h
            text_cell(f"<b>{html.escape(title)}</b>", x, y_b, 120, row_h, bold=True)
            x += 130
            for colour, label in items:
                key = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": "",
                    "style": f"rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor={colour};strokeColor=#ffffff;edgyRole=badge-key;",
                    "vertex": "1", "parent": "1"})
                ET.SubElement(key, "mxGeometry", {"x": str(x), "y": str(y_b + 6), "width": "22", "height": "11", "as": "geometry"})
                cid += 1
                tw = int(_text.measure(label, 9) + 6)
                text_cell(html.escape(label), x + 26, y_b, tw, row_h)
                x += 26 + tw + 14
        if self.uses_change_overlay:
            x, y_ov = 30, y0 + base_rows * row_h
            text_cell(f"<b>{html.escape(L['overlay_short'])}</b>", x, y_ov, 120, row_h, bold=True)
            x += 130
            for key, (color, dashed) in CHANGE_PALETTE.items():
                swatch = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": "",
                    "style": f"rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={color};strokeWidth=3;"
                             + ("dashed=1;dashPattern=4 2;" if dashed else ""),
                    "vertex": "1", "parent": "1"})
                ET.SubElement(swatch, "mxGeometry", {"x": str(x), "y": str(y_ov + 6), "width": "22", "height": "11", "as": "geometry"})
                cid += 1
                label = L['change'][key].split(' / ')[0]
                tw = int(_text.measure(label, 9) + 6)
                text_cell(html.escape(label), x + 26, y_ov, tw, row_h)
                x += 26 + tw + 14

    # Laatikkolegendan korkeus: otsikko 26 + 6 väririviä × 18 + erotin 10 + 4 viivariviä × 16 + alamarginaali 12
    # (2.6.0:n 200 px leikkasi viimeisen rivin, "Influence (guides)", laatikon reunan yli)
    _LEGEND_BOX_H = 220

    def _append_legend_cells(self, mx_root, start_id: int, page_width: int, page_height: int) -> None:
        """Lisää EDGY-legend draw.io-kaavion oikeaan alakulmaan."""
        # Legend-alueen mitat (+ muutoskerroksen rivit, jos käytössä)
        lw, lh = 220, self._LEGEND_BOX_H
        if self.uses_change_overlay:
            lh += self._overlay_legend_height()
        lh += self._badge_legend_height()
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

        L = self._legend_text()
        # Otsikkorivi
        title = ET.SubElement(mx_root, "mxCell", {
            "id": str(cid), "value": f"<b>{html.escape(L['title'])}</b>",
            "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=10;fontStyle=1;" + self._lang_marker(),
            "vertex": "1", "parent": "1"
        })
        ET.SubElement(title, "mxGeometry", {"x": str(lx + 8), "y": str(ly + 4), "width": str(lw - 16), "height": "18", "as": "geometry"})
        cid += 1

        # Elementtivärit
        elem_items = list(zip(("#80ffb7", "#a6c0ff", "#ff99bd", "#ffd580", "#e599ff", "#80eaff"), L['chips']))
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
        rel_items = list(zip(self._LINE_STYLES, L['lines']))
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

        # Muutoskerros (EDGY-laajennus): reunavärit — vain jos kaavio käyttää {change: …}
        if self.uses_change_overlay:
            oy = rel_y_start + len(rel_items) * 16 + 4
            sep2 = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": "",
                "style": "line;strokeColor=#cccccc;fillColor=none;", "vertex": "1", "parent": "1"})
            ET.SubElement(sep2, "mxGeometry", {"x": str(lx + 8), "y": str(oy), "width": str(lw - 16), "height": "6", "as": "geometry"})
            cid += 1
            title2 = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": f"<b>{html.escape(L['overlay'])}</b>",
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;fontStyle=1;",
                "vertex": "1", "parent": "1"})
            ET.SubElement(title2, "mxGeometry", {"x": str(lx + 8), "y": str(oy + 8), "width": str(lw - 16), "height": "16", "as": "geometry"})
            cid += 1
            for i, (key, (color, dashed)) in enumerate(CHANGE_PALETTE.items()):
                row_y = oy + 26 + i * 16
                swatch = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": "",
                    "style": f"rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor={color};strokeWidth=3;"
                             + ("dashed=1;dashPattern=4 2;" if dashed else ""),
                    "vertex": "1", "parent": "1"})
                ET.SubElement(swatch, "mxGeometry", {"x": str(lx + 8), "y": str(row_y + 2), "width": "22", "height": "11", "as": "geometry"})
                cid += 1
                txt = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": html.escape(L['change'][key]),
                    "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;",
                    "vertex": "1", "parent": "1"})
                ET.SubElement(txt, "mxGeometry", {"x": str(lx + 36), "y": str(row_y), "width": str(lw - 44), "height": "16", "as": "geometry"})
                cid += 1

        # Tilamerkit (EDGY-laajennus): kypsyys / arvio — vain käytetyt arvot
        by = rel_y_start + len(rel_items) * 16 + 4 + (self._overlay_legend_height() if self.uses_change_overlay else 0)
        for title, items in self._badge_legend_sections():
            sep3 = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": "", "style": "line;strokeColor=#cccccc;fillColor=none;", "vertex": "1", "parent": "1"})
            ET.SubElement(sep3, "mxGeometry", {"x": str(lx + 8), "y": str(by), "width": str(lw - 16), "height": "6", "as": "geometry"})
            cid += 1
            t3 = ET.SubElement(mx_root, "mxCell", {
                "id": str(cid), "value": f"<b>{html.escape(title)}</b>",
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;fontStyle=1;",
                "vertex": "1", "parent": "1"})
            ET.SubElement(t3, "mxGeometry", {"x": str(lx + 8), "y": str(by + 8), "width": str(lw - 16), "height": "16", "as": "geometry"})
            cid += 1
            for i, (colour, label) in enumerate(items):
                row_y = by + 26 + i * 16
                key = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": "",
                    "style": f"rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor={colour};strokeColor=#ffffff;edgyRole=badge-key;",
                    "vertex": "1", "parent": "1"})
                ET.SubElement(key, "mxGeometry", {"x": str(lx + 8), "y": str(row_y + 2), "width": "22", "height": "11", "as": "geometry"})
                cid += 1
                txt = ET.SubElement(mx_root, "mxCell", {
                    "id": str(cid), "value": html.escape(label),
                    "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;strokeColor=none;fillColor=none;fontSize=9;",
                    "vertex": "1", "parent": "1"})
                ET.SubElement(txt, "mxGeometry", {"x": str(lx + 36), "y": str(row_y), "width": str(lw - 44), "height": "16", "as": "geometry"})
                cid += 1
            by += 26 + len(items) * 16 + 10

    def _overlay_legend_height(self) -> int:
        return 26 + len(CHANGE_PALETTE) * 16 + 10


    def _calculate_layout(self) -> Dict[str, Tuple[int, int]]:
        """Laske top-level-asettelu. Palauttaa dict {id: (x, y)} elementeille ilman
        ryhmää sekä ryhmille/kaistoille; ryhmien jäsenten suhteelliset sijainnit
        tallentuvat `self._child_positions`-sanakirjaan.

        Pipeline:
        1. Facet-kontit (synteettiset ryhmät) kun map_type puuttuu
        2. Ryhmien sisäinen asettelu → koko
        3. Base layout top-level-kohteille (kaistat / karttatyyppi / facet)
        4. Tree-hierarkia (ellei layout hoitanut sitä itse)
        5. Törmäysresoluutio, canvas-normalisointi, grid snap
        """
        self._child_positions: Dict[str, Tuple[float, float]] = {}
        self._computed_sizes = {}
        self._layout_handles_tree = False
        self._size_override = {}
        self._triad_detours = {}
        self._triad_hidden = set()
        if self.map_type == 'triad':
            # Suunniteltu kehä: sijainnit, kontit ja paneelit tulevat slot-taulusta;
            # törmäysresoluutio ja ruudukkoon pyöristys ohitetaan tarkoituksella
            positions = self._layout_triad()
            self._group_positions = {gid: positions[gid] for gid in self.groups if gid in positions}
            result: Dict[str, Tuple[int, int]] = {}
            for eid, element in self.elements.items():
                gid = element.get('group')
                if gid is None:
                    result[eid] = positions.get(eid, (100, 100))
                else:
                    gx, gy = self._group_positions.get(gid, (0, 0))
                    rx, ry = self._child_positions.get(eid, (20, 40))
                    result[eid] = (gx + rx, gy + ry)
            return result
        self._hidden = set()
        self._stage_headers = []
        self._top_reserve = 0
        self._equalise_cards()
        self._prepare_facet_groups()
        self._prepare_task_lanes()
        self._prepare_matrix_rows()
        self._prepare_task_stages()

        # Sisimmät ensin: ylemmän ryhmän koko riippuu aliryhmien koosta
        for gid in sorted(self.groups, key=lambda g: -self._group_depth(g)):
            self._layout_group_members(gid, self.groups[gid])
        if self.equal_group_width:
            # Ylimmän tason kontit (ei kaistat, ei synteettiset facet-kontit) saavat leveimmän leveyden
            gids = [g for g, grp in self.groups.items() if grp['kind'] == 'group' and not grp.get('synthetic')
                    and grp.get('parent') is None]
            if gids:
                widest = max(self._computed_sizes[g][0] for g in gids)
                for g in gids:
                    self._computed_sizes[g] = (widest, self._computed_sizes[g][1])

        top_items = [eid for eid, e in self.elements.items() if e.get('group') is None and eid not in self._hidden]
        lanes = [gid for gid, g in self.groups.items() if g['kind'] == 'lane']
        containers = [gid for gid, g in self.groups.items() if g['kind'] == 'group' and g.get('parent') is None]

        if lanes and self.map_type == 'reference':
            positions = self._layout_reference(lanes, containers + top_items)
        elif lanes:
            positions = self._layout_lanes(lanes, containers + top_items)
        elif self.map_type == 'task' and self._task_path_targets(top_items):
            positions = self._layout_task_path(top_items)
        elif self.map_type:
            positions = self._calculate_map_type_layout(top_items, containers)
        else:
            positions = self._calculate_facet_layout(top_items, containers)

        if not self._layout_handles_tree:
            self._apply_tree_layout(positions)
        # Asemointi olemassa olevan ArchiMate-näkymän mukaan ("sama paikka = sama vastuualue")
        anchored = self._positions_from_layout_source() if self.layout_from else {}
        for eid, pos in anchored.items():
            if eid in positions:
                positions[eid] = pos
        if anchored:
            # kohdistamattomat top-level-elementit siirretään kohdistettujen alle, riviin
            max_y = max(positions[e][1] + self._size_of(e)[1] for e in anchored if e in positions)
            x = 60
            areas_anchored = any(e in self.groups for e in anchored)   # draw.io-lähde: myös alueet kohdistuvat
            for eid in list(positions):
                movable = (eid in self.elements and self.elements[eid].get('group') is None) or \
                    (areas_anchored and eid in self.groups and self.groups[eid].get('parent') is None)
                if eid not in anchored and movable:
                    positions[eid] = (x, max_y + 60)
                    x += self._size_of(eid)[0] + 40
        self._resolve_collisions(positions)
        self._normalize_to_canvas(positions)
        self._snap_to_grid(positions)

        # Palauta KAIKKIEN elementtien absoluuttiset sijainnit; ryhmät erikseen (sisäkkäiset: vanhemman ketju)
        self._group_positions = {}

        def _abs_group(g):
            if g in self._group_positions:
                return self._group_positions[g]
            parent = self.groups[g].get('parent')
            if parent is None:
                pos = positions.get(g)
            else:
                pp = _abs_group(parent)
                rx, ry = self._child_positions.get(g, (20, 40))
                pos = None if pp is None else (pp[0] + rx, pp[1] + ry)
            if pos is not None:
                self._group_positions[g] = pos
            return pos
        for gid in self.groups:
            _abs_group(gid)
        result: Dict[str, Tuple[int, int]] = {}
        for eid, element in self.elements.items():
            gid = element.get('group')
            if gid is None:
                result[eid] = positions.get(eid, (100, 100))
            else:
                gx, gy = self._group_positions.get(gid, (0, 0))
                rx, ry = self._child_positions.get(eid, (20, 40))
                result[eid] = (gx + rx, gy + ry)
        return result

    def _equalise_cards(self) -> None:
        """equal_cards (oletus): saman tyypin laatikot sivulla saavat leveimmän
        leveyden (max 280 ellei card_width/kokoluokka ole suurempi) ja siitä
        lasketun korkeimman korkeuden → yhtenäinen mitoitus, W117 ei laukea.
        Triad ohittaa tämän (kehän laatikot ovat jo yhtä kokoa)."""
        if not self.equal_cards:
            return
        by_type: Dict[str, List[str]] = {}
        for eid, e in self.elements.items():
            if e['type'] not in STRUCTURE_TYPES:
                by_type.setdefault(e['type'], []).append(eid)
        for members in by_type.values():
            if len(members) < 2:
                continue
            width = max(self._get_element_size(self.elements[m])[0] for m in members)
            sizes = {m: self._get_element_size(self.elements[m], force_w=width) for m in members}
            height = max(h for _, h in sizes.values())
            for m in members:
                self._size_override[m] = (width, height)

    # ---- tehtäväkartta: sidosryhmäinventaario ja polku ----------------------
    def _prepare_task_lanes(self) -> None:
        """map_type: task ilman kaistoja: jos People/Organisation-elementillä on
        relaatio tehtäviin, siitä tulee kaista (sidosryhmä) ja tehtävät sen
        jäseniä. Sidosryhmäelementtiä ja sen relaatioita ei piirretä — kaista
        kantaa ne (raportoidaan, ei pudoteta hiljaa). Kaistoja ei koskaan
        keksitä: ilman relaatioita tehtävät jäävät ruudukkoon tai polkuun."""
        for gid in [g for g, grp in self.groups.items() if grp.get('synthetic') == 'task']:
            for m in self.groups[gid]['members']:
                self.elements[m]['group'] = None
            del self.groups[gid]
        if self.map_type != 'task' or any(g['kind'] == 'lane' for g in self.groups.values()):
            return
        holders = [eid for eid, e in self.elements.items() if e['type'] in ('people', 'organisation')]
        tasks = {eid for eid, e in self.elements.items() if e['type'] == 'task' and e.get('group') is None}
        related: Dict[str, List[str]] = {}      # holder → every task it relates to (input order)
        other: Dict[str, int] = {}              # holder → relationships to something that is not a task
        for rel in self.relationships:
            s, t = rel['source'], rel['target']
            holder, task = (s, t) if s in holders and t in tasks else (t, s) if t in holders and s in tasks else (None, None)
            if holder:
                if task not in related.setdefault(holder, []):
                    related[holder].append(task)
            else:
                for h in (s, t):
                    if h in holders:
                        other[h] = other.get(h, 0) + 1
        # A stakeholder with a relationship to anything but a task stays a box: a lane cannot draw that edge
        for h in [h for h in related if other.get(h)]:
            self.warnings.append(f"task map: '{self.elements[h]['name']}' keeps its box — it has {other[h]} relationship(s) "
                                 f"to elements that are not tasks, which a lane could not draw")
            del related[h]
        if not related:
            return
        # A task sits in one lane (its first stakeholder); every other related stakeholder still becomes a
        # lane and names the shared task in its title, so no stakeholder stays a box with an edge.
        placed: Dict[str, str] = {}
        shared: Dict[str, List[str]] = {}
        for holder in holders:
            if holder not in related:
                continue
            own = [t for t in related[holder] if t not in placed]
            for t in own:
                placed[t] = holder
            shared[holder] = [t for t in related[holder] if t not in own]
            gid = f"lane_{holder}"
            name = self.elements[holder]['name']
            if shared[holder]:
                name += " (also: " + ", ".join(self.elements[t]['name'] for t in shared[holder]) + ")"
            self.groups[gid] = {'id': gid, 'kind': 'lane', 'name': name, 'members': own,
                                'tags': [], 'metrics': {}, 'synthetic': 'task'}
            for m in own:
                self.elements[m]['group'] = gid
            self._hidden.add(holder)
        n_rel = sum(1 for r in self.relationships if r['source'] in self._hidden or r['target'] in self._hidden)
        self.warnings.append(f"task map: {len(self._hidden)} stakeholder(s) drawn as lanes, {n_rel} stakeholder relationship(s) "
                             f"shown by lane membership instead of edges")
        for holder, extra in shared.items():
            if extra:
                self.warnings.append(f"task map: '{self.elements[holder]['name']}' shares {len(extra)} task(s) placed in another lane "
                                     f"({', '.join(self.elements[t]['name'] for t in extra)}) — named in the lane title, not drawn twice")

    # Karttatyypit, joilla on oma rakenteensa: sarakkeet/rivit eivät koske niitä
    _NO_MATRIX_MAP_TYPES = ('triad', 'purpose', 'reference', 'summary')

    def _map_label(self) -> str:
        return f"{self.map_type} map" if self.map_type else "map"

    def _prepare_matrix_rows(self) -> None:
        """rows: X, Y ilman kaistoja → yksi synteettinen kaista per rivi; elementti valitsee
        rivinsä {row: X}. Yhdessä columns:/stages:-avaimen kanssa tuloksena on matriisi
        (rivit × sarakkeet): kanavakartta 2 × 2, kosketuspistekartta, tiekartta.
        Riviton elementti jää kaistojen alle varoituksen kera; tyhjää riviä ei piirretä."""
        for gid in [g for g, grp in self.groups.items() if grp.get('synthetic') == 'row']:
            for m in self.groups[gid]['members']:
                self.elements[m]['group'] = None
            del self.groups[gid]
        if not self.rows or self.map_type in self._NO_MATRIX_MAP_TYPES:
            return
        if self.groups:
            self.warnings.append(f"{self._map_label()}: rows: ignored — the input already has groups or lanes")
            return
        keys = {r.lower(): r for r in self.rows}
        by_row: Dict[str, List[str]] = {r: [] for r in self.rows}
        for eid, e in self.elements.items():
            if eid in self._hidden or e.get('group') is not None:
                continue
            r = (e.get('row') or '').strip().lower()
            if r in keys:
                by_row[keys[r]].append(eid)
            else:
                self.warnings.append(f"{self._map_label()}: '{e['name']}' has no known row "
                                     f"(rows: {', '.join(self.rows)}) — placed below the rows")
        for n, r in enumerate(self.rows):
            if not by_row[r]:
                self.warnings.append(f"{self._map_label()}: row '{r}' has no elements — not drawn")
                continue
            gid = f"row_{n + 1}"
            self.groups[gid] = {'id': gid, 'kind': 'lane', 'name': r, 'members': by_row[r], 'tags': [],
                                'metrics': {}, 'synthetic': 'row', 'parent': None, 'subgroups': []}
            for m in by_row[r]:
                self.elements[m]['group'] = gid

    def _prepare_task_stages(self) -> None:
        """stages:/columns: ilman kaistoja ja ryhmiä: yksi kontti per sarake syötteen
        järjestyksessä, elementit allekkain sarakkeensa konttiin (virallinen tehtäväkartta:
        vaiheet). Tehtäväkartalla sarakkeisiin menevät tehtävät, eikä polkuvariantti
        (tehtävä → journey/channel) käytä sarakkeita. Sarakkeeton elementti jää konttien
        perään varoituksen kera; tyhjää saraketta ei piirretä."""
        for gid in [g for g, grp in self.groups.items() if grp.get('synthetic') == 'stage']:
            for m in self.groups[gid]['members']:
                self.elements[m]['group'] = None
            del self.groups[gid]
        if not self.map_type or self.map_type in self._NO_MATRIX_MAP_TYPES or not self.stages or self.groups:
            return
        if self.map_type == 'task':
            tasks = [eid for eid, e in self.elements.items() if e['type'] == 'task' and eid not in self._hidden]
            if self._task_path_targets(list(self.elements)):
                return
        else:
            tasks = [eid for eid in self.elements if eid not in self._hidden]
        if not tasks:
            return
        cols = {st.lower(): st for st in self.stages}
        by_stage: Dict[str, List[str]] = {st: [] for st in self.stages}
        for t in tasks:
            st = (self.elements[t].get('stage') or '').strip().lower()
            if st in cols:
                by_stage[cols[st]].append(t)
            else:
                self.warnings.append(f"{self._map_label()}: '{self.elements[t]['name']}' has no known stage "
                                     f"(stages: {', '.join(self.stages)}) — placed after the stage columns")
        for n, st in enumerate(self.stages):
            members = by_stage[st]
            if not members:
                self.warnings.append(f"{self._map_label()}: stage '{st}' has no "
                                     f"{'tasks' if self.map_type == 'task' else 'elements'} — no column drawn")
                continue
            gid = f"stage_{n + 1}"
            self.groups[gid] = {'id': gid, 'kind': 'group', 'name': st, 'members': members, 'tags': [],
                                'metrics': {}, 'synthetic': 'stage', 'layout': 'column',
                                'parent': None, 'subgroups': []}
            for m in members:
                self.elements[m]['group'] = gid

    def _task_path_targets(self, items: List[str]) -> bool:
        """Polkuvariantti: tehtävistä on relaatioita journey- tai channel-elementteihin."""
        types = {i: self.elements[i]['type'] for i in items}
        return any(types.get(r['source']) == 'task' and types.get(r['target']) in ('journey', 'channel')
                   for r in self.relationships)

    def _layout_task_path(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Tehtäväkartan polku: matkat ylärivillä, tehtävät keskirivillä syötejärjestyksessä,
        kanavat alarivillä — task → journey (is part of) nousee, task → channel (uses) laskee,
        kumpikaan ei kulje toisen tehtävän läpi. Muut elementit riviin alimmaksi."""
        positions: Dict[str, Tuple[int, int]] = {}
        sizes = {i: self._size_of(i) for i in items}
        by_type = lambda t: [i for i in items if self.elements[i]['type'] == t]  # noqa: E731
        journeys, tasks, channels = by_type('journey'), by_type('task'), by_type('channel')
        rest = [i for i in items if i not in journeys and i not in tasks and i not in channels]
        GAP_X, GAP_Y = 40, 110
        x0, y = 60, 60

        def row(ids: List[str], top: float, centre: float) -> float:
            total = sum(sizes[i][0] for i in ids) + GAP_X * (len(ids) - 1)
            x = max(x0, centre - total / 2)
            h = 0
            for i in ids:
                positions[i] = (x, top)
                x += sizes[i][0] + GAP_X
                h = max(h, sizes[i][1])
            return top + h

        task_w = sum(sizes[i][0] for i in tasks) + GAP_X * (len(tasks) - 1)
        centre = x0 + task_w / 2
        # Pystyportit oletuksena: matkaan ylös (top → bottom), kanavaan alas (bottom → top);
        # vaakasegmentti jää rivien väliin eikä kulje naapuritehtävän läpi. Syötteen from:/to: voittaa.
        for rel in self.relationships:
            if rel['source'] in tasks:
                opts = rel.setdefault('options', {})
                if rel['target'] in journeys:
                    opts.setdefault('from', 'top'); opts.setdefault('to', 'bottom')
                elif rel['target'] in channels:
                    opts.setdefault('from', 'bottom'); opts.setdefault('to', 'top')
        if journeys:
            y = row(journeys, y, centre) + GAP_Y
        if tasks:
            y = row(tasks, y, centre) + GAP_Y
        if channels:
            y = row(channels, y, centre) + GAP_Y
        if rest:
            row(rest, y, centre)
        return positions

    # ---- ryhmät ------------------------------------------------------------
    def _prepare_facet_groups(self) -> None:
        """Luo synteettiset facet-kontit kun käyttäjä ei ole määritellyt ryhmiä
        eikä karttatyyppiä: facet: all → Identity/Architecture/Experience,
        yksittäinen facet → yksi kontti fasetin omille elementeille."""
        if self.map_type or self.layout_from or any(not g.get('synthetic') for g in self.groups.values()):
            return  # layout_from: elementit pysyvät top-levelillä, jotta näkymän koordinaatit pätevät
        # idempotentti: poista aiemmat synteettiset
        for gid in [g for g, grp in self.groups.items() if grp.get('synthetic')]:
            for m in self.groups[gid]['members']:
                self.elements[m]['group'] = None
            del self.groups[gid]
        facets = {'identity': IDENTITY_ELEMENTS, 'architecture': ARCHITECTURE_ELEMENTS, 'experience': EXPERIENCE_ELEMENTS}
        wanted = list(facets) if self.facet == 'all' else [self.facet]
        for facet in wanted:
            members = [eid for eid, e in self.elements.items() if e['type'] in facets.get(facet, set())]
            if not members:
                continue
            gid = f"facet_{facet}"
            self.groups[gid] = {'id': gid, 'kind': 'group', 'name': FACET_TITLES[facet], 'members': members,
                                'tags': [], 'metrics': {}, 'synthetic': True, 'facet': facet,
                                'layout': 'column' if self.facet == 'all' else 'grid'}
            for m in members:
                self.elements[m]['group'] = gid

    def _layout_group_members(self, gid: str, group: dict) -> None:
        """Aseta ryhmän jäsenet ryhmän sisään (suhteelliset koordinaatit) ja laske ryhmän koko.

        - kontti: ruudukko 2–4 saraketta (tai yksi sarake facet: all -konteissa);
          tree-relaatiot ryhmän sisällä sisennetään hierarkiana
        - kaista: jäsenet yhdellä rivillä, rivitys kun leveys > 1100
        """
        members = group['members']
        PAD_X, PAD_TOP, PAD_BOTTOM, GAP = 20, 36, 20, 20
        if group.get('subgroups'):
            self._layout_parent_group(gid, group)
            return
        if not members:
            self._computed_sizes[gid] = (240, 100)
            return
        sizes = {m: self._get_element_size(self.elements[m]) for m in members}
        if group['kind'] == 'lane' and self.stages:
            # Matriisi: sarake = vaihe ({stage: X}), sarakeleveys sama joka kaistassa; useat
            # samaan vaiheeseen kuuluvat tehtävät pinotaan; vaiheeton tehtävä → viimeinen sarake + varoitus
            col_w = max([self._get_element_size(self.elements[m])[0] for g in self.groups.values() if g['kind'] == 'lane'
                         for m in g['members']] + [120])
            cols = {st.lower(): i for i, st in enumerate(self.stages)}
            stacks: Dict[int, List[str]] = {}
            for m in members:
                st = (self.elements[m].get('stage') or '').strip().lower()
                if st not in cols:
                    self.warnings.append(f"{self._map_label()}: '{self.elements[m]['name']}' has no known stage "
                                         f"(stages: {', '.join(self.stages)}) — placed in the last column")
                stacks.setdefault(cols.get(st, len(self.stages)), []).append(m)
            height = PAD_TOP
            for c, stack in stacks.items():
                y = PAD_TOP
                for m in stack:
                    self._child_positions[m] = (PAD_X + c * (col_w + GAP), y)
                    y += sizes[m][1] + GAP
                height = max(height, y)
            n_cols = len(self.stages) + (1 if len(self.stages) in stacks else 0)
            self._computed_sizes[gid] = (PAD_X * 2 + n_cols * col_w + (n_cols - 1) * GAP, height - GAP + PAD_BOTTOM)
            return
        if group['kind'] == 'lane':
            max_w = 1100
            x, y, row_h, width = PAD_X, PAD_TOP, 0, 0
            for m in members:
                w, h = sizes[m]
                if x > PAD_X and x + w > max_w:
                    x, y = PAD_X, y + row_h + GAP
                    row_h = 0
                self._child_positions[m] = (x, y)
                x += w + GAP * 2
                row_h = max(row_h, h)
                width = max(width, x)
            self._computed_sizes[gid] = (max(width, 400), y + row_h + PAD_BOTTOM)
            return
        n = len(members)
        member_set = set(members)
        tree_children: Dict[str, List[str]] = {}
        child_set = set()
        for rel in self.relationships:
            if rel.get('kind') == 'tree' and rel['source'] in member_set and rel['target'] in member_set:
                tree_children.setdefault(rel['source'], []).append(rel['target'])
                child_set.add(rel['target'])
        if tree_children:
            # Tidy tree ryhmän sisällä: juuret vierekkäin, alipuut alla leveyksien mukaan
            H_GAP, V_GAP = 30, 90
            cursor_x = PAD_X
            max_y = PAD_TOP

            def place(node, cx, top):
                nonlocal max_y
                w, h = sizes[node]
                self._child_positions[node] = (cx - w / 2, top)
                max_y = max(max_y, top + h)
                kids = tree_children.get(node, [])
                if not kids:
                    return
                widths = [self._subtree_width(k, tree_children, sizes, H_GAP) for k in kids]
                total = sum(widths) + (len(kids) - 1) * H_GAP
                c = cx - total / 2
                for k, kw in zip(kids, widths):
                    place(k, c + kw / 2, top + V_GAP)
                    c += kw + H_GAP

            roots = [m for m in members if m not in child_set]
            for r in roots:
                rw = self._subtree_width(r, tree_children, sizes, H_GAP)
                place(r, cursor_x + rw / 2, PAD_TOP)
                cursor_x += rw + H_GAP * 2
            # siirrä niin että vasen reuna on PAD_X
            min_x = min(x for x, _ in (self._child_positions[m] for m in members))
            shift = PAD_X - min_x
            width = 0
            for m in members:
                x, y = self._child_positions[m]
                self._child_positions[m] = (x + shift, y)
                width = max(width, x + shift + sizes[m][0])
            min_w = max(240, len(group['name']) * 7 + 40)
            self._computed_sizes[gid] = (max(width + PAD_X, min_w), max_y + PAD_BOTTOM)
            return
        if self.cards_per_row:
            cols = self.cards_per_row
        elif group.get('layout') == 'column':
            cols = 1
        else:
            cols = 2 if n <= 4 else 3 if n <= 9 else 4
        col_w = max(sizes[m][0] for m in members)
        x, y, row_h, width, height = PAD_X, PAD_TOP, 0, 0, 0
        for i, m in enumerate(members):
            if i and i % cols == 0:
                x, y = PAD_X, y + row_h + GAP
                row_h = 0
            w, h = sizes[m]
            self._child_positions[m] = (x, y)
            x += col_w + GAP
            row_h = max(row_h, h)
            width = max(width, x - GAP + PAD_X)
            height = y + row_h + PAD_BOTTOM
        min_w = max(240, len(group['name']) * 7 + 40)
        self._computed_sizes[gid] = (max(width, min_w), height)

    def _group_depth(self, gid: str) -> int:
        depth, g = 0, self.groups[gid].get('parent')
        while g is not None:
            depth, g = depth + 1, self.groups[g].get('parent')
        return depth

    def _layout_parent_group(self, gid: str, group: dict) -> None:
        """Kontti, jossa on aliryhmiä (virallisen kyvykkyyskartan kolme tasoa: alue → aliryhmä → kyvykkyys).

        Suorat jäsenelementit ensin tavallisena ruudukkona, aliryhmät niiden alle
        riveinä: sarakemäärä group_columns tai 1–3 → yhdelle riville, 4 → 2, muuten 3.
        Sarakkeen leveys = sarakkeen levein aliryhmä, rivin aliryhmät venyvät rivin
        korkeuteen (viralliset kartat: tasakorkeat alueet riveittäin)."""
        import math
        PAD_X, PAD_TOP, PAD_BOTTOM, GAP = 20, 36, 20, 20
        subs = group['subgroups']
        right, y = PAD_X, PAD_TOP
        if group['members']:
            self._layout_group_members(gid, {**group, 'subgroups': []})
            for m in group['members']:
                mx, my = self._child_positions[m]
                mw, mh = self._get_element_size(self.elements[m])
                right = max(right, mx + mw)
                y = max(y, my + mh + GAP)
        n = len(subs)
        cols = self.group_columns or (n if n <= 3 else 2 if n == 4 else 3)
        rows = [subs[i:i + cols] for i in range(0, n, cols)]
        col_w = [0] * cols
        for row in rows:
            for c, sg in enumerate(row):
                col_w[c] = max(col_w[c], int(math.ceil(self._computed_sizes[sg][0] / 10) * 10))
        for row in rows:
            row_h = int(math.ceil(max(self._computed_sizes[sg][1] for sg in row) / 10) * 10)
            x = PAD_X
            for c, sg in enumerate(row):
                self._child_positions[sg] = (x, y)
                self._computed_sizes[sg] = (col_w[c], row_h)
                x += col_w[c] + GAP
            right = max(right, x - GAP)
            y += row_h + GAP
        min_w = max(240, len(group['name']) * 8 + 40)
        self._computed_sizes[gid] = (max(right + PAD_X, min_w), y - GAP + PAD_BOTTOM)

    def _layout_lanes(self, lanes: List[str], others: List[str]) -> Dict[str, Tuple[int, int]]:
        """Kaistat päällekkäin ylhäältä alas; muut top-level-kohteet riviin kaistojen alle."""
        positions: Dict[str, Tuple[int, int]] = {}
        x0, y = 60, 60
        self._top_reserve = 40 if self.stages else 0   # sarakeotsikot kaistojen yläpuolelle
        width = max(self._computed_sizes[l][0] for l in lanes)
        for l in lanes:
            self._computed_sizes[l] = (width, self._computed_sizes[l][1])
            positions[l] = (x0, y)
            y += self._computed_sizes[l][1] + 30
        x = x0
        for item in others:
            w, h = self._size_of(item)
            positions[item] = (x, y + 20)
            x += w + 40
        return positions

    def _layout_reference(self, lanes: List[str], others: List[str]) -> Dict[str, Tuple[int, int]]:
        """Layered reference architecture (EDGY extension):

            [actors]  ┌ L1 channels ─────────┐  [externals]
            people /  ├ L2 core ─────────────┤  assets tagged
            organis.  ├ L3 shared services ──┤  [external]
                      └──────────────────────┘

        Lanes stack top-down in the middle; Organisation / People outside any
        lane form a left column, elements tagged `external` a right column;
        anything else goes below the lanes.
        """
        positions: Dict[str, Tuple[int, int]] = {}
        actors = [i for i in others if i in self.elements and self.elements[i]['type'] in ('organisation', 'people')]
        externals = [i for i in others if i in self.elements and i not in actors
                     and 'external' in [t.lower() for t in self.elements[i].get('tags', [])]]
        rest = [i for i in others if i not in actors and i not in externals]
        left_w = max([self._size_of(a)[0] for a in actors], default=0)
        x_lanes = 60 + (left_w + 60 if actors else 0)
        y = 60
        width = max(self._computed_sizes[l][0] for l in lanes)
        lane_tops = []
        for l in lanes:
            self._computed_sizes[l] = (width, self._computed_sizes[l][1])
            positions[l] = (x_lanes, y)
            lane_tops.append(y)
            y += self._computed_sizes[l][1] + 30
        total_h = y - 30 - 60
        # actors spread vertically along the lanes
        ay = 60
        step = max(total_h / max(len(actors), 1), 0)
        for i, a in enumerate(actors):
            positions[a] = (60, ay + i * step)
        ex = x_lanes + width + 60
        for i, e in enumerate(externals):
            positions[e] = (ex, ay + i * step)
        x = x_lanes
        for item in rest:
            w, h = self._size_of(item)
            positions[item] = (x, y + 20)
            x += w + 40
        return positions

    def _layout_summary(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Stakeholder summary (EDGY extension): three rows, max 4 boxes each.

            who          → Organisation / People
            does what    → Process / Activity
            what results → Outcome / Product / Object
            (anything else: a fourth row — e.g. "used for" items)
        """
        rows = [
            [i for i in items if self.elements[i]['type'] in ('organisation', 'people')],
            [i for i in items if self.elements[i]['type'] in ('process', 'activity')],
            [i for i in items if self.elements[i]['type'] in ('outcome', 'product', 'object')],
        ]
        placed = {i for r in rows for i in r}
        rows.append([i for i in items if i not in placed])
        for r in rows:
            if len(r) > SUMMARY_MAX_PER_ROW:
                self.warnings.append(
                    f"Summary: rivillä on {len(r)} laatikkoa (max {SUMMARY_MAX_PER_ROW}) — "
                    f"sidosryhmäkuva toimii 3–4 laatikolla per rivi; yhdistä tai pudota elementtejä")
        positions: Dict[str, Tuple[int, int]] = {}
        y = 60
        for r in rows:
            if not r:
                continue
            widths = [self._size_of(i)[0] for i in r]
            total = sum(widths) + 60 * (len(r) - 1)
            x = max(60, 600 - total / 2)
            row_h = 0
            for i in r:
                positions[i] = (x, y)
                x += self._size_of(i)[0] + 60
                row_h = max(row_h, self._size_of(i)[1])
            y += row_h + 90
        return positions

    def _layout_flow_grid(self, items: List[str], cols: int, x0: int = 60, y0: int = 60,
                          gap_x: int = 40, gap_y: int = 40) -> Dict[str, Tuple[int, int]]:
        """Ruudukko vaihtelevan kokoisille kohteille (ryhmät + elementit).

        align_groups: grid → sarakkeen leveys on sarakkeen levein kohde (kaikki rivit),
        rivin kontit venytetään rivin korkeimman korkeuteen: tarkat rivit ja sarakkeet."""
        import math
        positions: Dict[str, Tuple[int, int]] = {}
        if self.align_groups == 'grid' and items:
            rows = [items[i:i + cols] for i in range(0, len(items), cols)]
            col_w = [0] * cols
            for row in rows:
                for c, item in enumerate(row):
                    col_w[c] = max(col_w[c], int(math.ceil(self._size_of(item)[0] / 10) * 10))
            y = y0
            for row in rows:
                row_h = int(math.ceil(max(self._size_of(item)[1] for item in row) / 10) * 10)
                x = x0
                for c, item in enumerate(row):
                    positions[item] = (x, y)
                    if item in self.groups:      # kontti venyy rivin korkeuteen
                        self._computed_sizes[item] = (self._computed_sizes[item][0], row_h)
                    x += col_w[c] + gap_x
                y += row_h + gap_y
            return positions
        x, y, row_h = x0, y0, 0
        for i, item in enumerate(items):
            if i and i % cols == 0:
                # rivin korkeus pyöristetään ylös 10 px:iin: grid snap ei saa tehdä riviväleistä epätasaisia (W118)
                x, y, row_h = x0, y + int(math.ceil(row_h / 10) * 10) + gap_y, 0
            w, h = self._size_of(item)
            positions[item] = (x, y)
            x += w + gap_x
            row_h = max(row_h, h)
        return positions

    # ---- triad (EDGY-laajennus): suunniteltu kehä --------------------------
    #
    # facet: all                           yksittäinen facet (esim. architecture)
    #        ┌── Identity ───────┐                  [intersektio A]
    #        │ story  purpose  content │        ┌─ Facet ─────────────────┐
    #        └───────────────────┘              │ outcome-tyyppi  activity │
    #   [organisation]          [brand]         │        object            │
    # ┌ Architecture ┐   ┌ Experience ┐         └─────────────────────────┘
    # │ capability   │   │   task     │                  [intersektio B]
    # │ asset        │   │  channel   │           Further <type> -paneelit
    # │   process    │   │ journey    │
    # └──────────────┘   └────────────┘
    #            [product]
    #
    # Yksi ENSISIJAINEN elementti per tyyppi kantaa ydinlinkit ({primary: true},
    # muuten tyypin ensimmäinen). Muut elementit näkyvät "Further <tyyppi>"
    # -paneeleissa ilman viivoja; niiden linkit raportoidaan (ei pudoteta hiljaa).
    # Kaikki ydinlinkit ovat suoria viivoja reunasta reunaan; kaksi
    # intersektio–intersektio-linkkiä kiertää sivun reunaa.

    _TRIAD_W, _TRIAD_H = 210, 74          # kehän laatikko
    _TRIAD_PAGE_W = 1340                  # facet: all -kehän nimellisleveys
    # Tekstin oletussiirtymä (dx, dy) px suoralle viivalle slot-parin mukaan: poispäin lähimmästä laatikosta.
    # Ylikirjoitus relaatio-optiolla {label_dx: …, label_dy: …} tai {label: source|target}.
    _TRIAD_LABEL_SHIFT = {
        ('story', 'purpose'): (-45, 0), ('content', 'purpose'): (40, 0), ('content', 'story'): (0, -10),
        ('organisation', 'purpose'): (40, 20), ('organisation', 'story'): (-30, 0), ('organisation', 'brand'): (0, -10),
        ('organisation', 'capability'): (-25, 0), ('organisation', 'process'): (30, 0),
        ('brand', 'story'): (0, -10), ('brand', 'purpose'): (55, 60), ('brand', 'task'): (30, 0), ('brand', 'journey'): (-35, 0),
        ('capability', 'asset'): (-30, 0), ('process', 'capability'): (30, 0), ('process', 'asset'): (0, -10),
        ('task', 'journey'): (-35, 0), ('task', 'channel'): (30, 0), ('journey', 'channel'): (0, 12),
        ('product', 'capability'): (-35, 0), ('process', 'product'): (0, 12), ('product', 'task'): (35, 0),
        ('product', 'journey'): (0, 12),
    }
    _TRIAD_DETOUR_SHIFT = {'left': (45, -150), 'right': (-45, -150)}   # reunaa kiertävä linkki: teksti sivun sisäpuolelle
    # Kiinteät portit suorille viivoille, jotka muuten hipoisivat story-/content-laatikkoa pitkillä nimillä:
    # (exitX, exitY), (entryX, entryY)
    _TRIAD_ANCHORS = {
        ('organisation', 'purpose'): ((1, 0), (0.3, 1)),
        ('brand', 'purpose'): ((0, 0), (0.7, 1)),
    }
    _TRIAD_FURTHER_TITLE = {'en': 'Further', 'fi': 'Muut', 'fr': 'Autres', 'de': 'Weitere'}
    # Paneelin otsikon tyyppinimi monikossa, `language:`-avaimen mukaan (sama sanasto kuin edgy-framework)
    _TYPE_PLURAL = {
        'en': {'purpose': 'purposes', 'story': 'stories', 'content': 'content', 'capability': 'capabilities',
               'asset': 'assets', 'process': 'processes', 'task': 'tasks', 'channel': 'channels',
               'journey': 'journeys', 'organisation': 'organisations', 'product': 'products', 'brand': 'brands',
               'people': 'people', 'activity': 'activities', 'outcome': 'outcomes', 'object': 'objects'},
        'fi': {'purpose': 'tarkoitukset', 'story': 'tarinat', 'content': 'sisällöt', 'capability': 'kyvykkyydet',
               'asset': 'resurssit', 'process': 'prosessit', 'task': 'tehtävät', 'channel': 'kanavat',
               'journey': 'matkat', 'organisation': 'organisaatiot', 'product': 'tuotteet', 'brand': 'brändit',
               'people': 'ihmiset', 'activity': 'toiminnot', 'outcome': 'tulokset', 'object': 'objektit'},
        'fr': {'purpose': "raisons d'être", 'story': 'récits', 'content': 'contenus', 'capability': 'capacités',
               'asset': 'actifs', 'process': 'processus', 'task': 'tâches', 'channel': 'canaux',
               'journey': 'parcours', 'organisation': 'organisations', 'product': 'produits', 'brand': 'marques',
               'people': 'personnes', 'activity': 'activités', 'outcome': 'résultats', 'object': 'objets'},
        'de': {'purpose': 'Zwecke', 'story': 'Geschichten', 'content': 'Inhalte', 'capability': 'Fähigkeiten',
               'asset': 'Ressourcen', 'process': 'Prozesse', 'task': 'Aufgaben', 'channel': 'Kanäle',
               'journey': 'Reisen', 'organisation': 'Organisationen', 'product': 'Produkte', 'brand': 'Marken',
               'people': 'Personen', 'activity': 'Aktivitäten', 'outcome': 'Ergebnisse', 'object': 'Objekte'},
    }

    def _lang_marker(self) -> str:
        """`edgyLang=<lang>;` legendan otsikkosoluun vain kun `language:` on asetettu —
        lint W116 lukee kartan kielen tästä, ei otsikon tekstistä (oletuslegenda ei ole kielivalinta)."""
        return f"edgyLang={self.language};" if self._language_explicit else ''

    def _legend_text(self) -> dict:
        """Legendan ja generoitujen otsikoiden tekstit kartan kielellä (`language:`), oletus 'en'."""
        return LEGEND_TEXT.get(self.language, LEGEND_TEXT['en'])

    def _render_verb(self, verb: str, pair: Tuple[str, str] = None) -> str:
        """Sanaston verbi kartan kielellä kun `language:` on asetettu ja translate_verbs on päällä;
        vapaa teksti ja jo oikeankieliset verbit palautetaan sellaisinaan. Kanoninen koodi pysyy mallissa.
        `pair` (lähde-, kohdetyyppi) erottaa saman kirjoitusasun eri ydinlinkit (de 'erscheint in')."""
        if not (self._language_explicit and self.translate_verbs):
            return verb
        if self.language in _vocab.languages_of(verb):
            return verb
        translated = _vocab.translate(verb, self.language, pair)
        return translated if translated else verb

    def _effective_legend(self) -> str:
        """Triad käyttää nauhalegendaa, ellei käyttäjä ole valinnut toisin."""
        if self.map_type == 'triad' and not self._legend_explicit:
            return 'strip'
        return self.legend

    def _triad_slots(self) -> Tuple[Dict[str, Tuple[int, int, int, int]], Dict[str, Tuple[str, Tuple[int, int, int, int]]],
                     List[Tuple[str, str, str, str, int]]]:
        """Slot-taulu: {tyyppi: (cx, cy, w, h)}, kontit {facet: (otsikko, (x, y, w, h))} ja
        kiertoreitit [(lähdetyyppi, kohdetyyppi, exit, entry, reunan x)]."""
        W, H = self._TRIAD_W, self._TRIAD_H
        if self.facet == 'all':
            slots = {
                'purpose': (650, 80, 230, H), 'story': (400, 220, W, H), 'content': (910, 220, W, H),
                'organisation': (380, 400, W, H), 'brand': (920, 400, W, H),
                'capability': (230, 560, W, H), 'asset': (180, 720, W, H), 'process': (380, 840, W, H),
                'task': (1070, 560, W, H), 'channel': (1170, 720, W, H), 'journey': (920, 840, W, H),
                'product': (650, 900, W, H),
            }
            containers = {
                'identity': ('Identity', (260, 30, 800, 260)),
                'architecture': ('Architecture', (50, 500, 460, 410)),
                'experience': ('Experience', (790, 500, 500, 410)),
            }
            detours = [('organisation', 'product', 'left', 'left', 20), ('product', 'brand', 'right', 'right', 1310)]
            return slots, containers, detours
        if self.facet == 'identity':
            slots = {'purpose': (600, 98, 240, 76), 'story': (335, 270, 270, 80), 'content': (870, 270, 260, 64),
                     'organisation': (330, 482, W, 64), 'brand': (870, 482, W, 64)}
            containers = {'identity': ('Identity', (60, 30, 1080, 320))}
            return slots, containers, []
        if self.facet == 'architecture':
            a, b, obj = 'organisation', 'product', 'asset'
            left, right = 'capability', 'process'
            cont_h, obj_cy, b_cy = 330, 392, 532
        else:  # experience
            a, b, obj = 'brand', 'product', 'channel'
            left, right = 'task', 'journey'
            cont_h, obj_cy, b_cy = 440, 492, 652
        slots = {a: (600, 62, 220, 64), left: (230, 225, 240, 70), right: (970, 225, 240, 70),
                 obj: (600, obj_cy, 220, 64), b: (600, b_cy, 220, 64)}
        containers = {self.facet: (FACET_TITLES[self.facet], (60, 130, 1080, cont_h))}
        detours = [(a, b, 'right', 'right', 1150)]
        return slots, containers, detours

    def _triad_primary(self, type_name: str, members: List[str]) -> str:
        flagged = [m for m in members if self.elements[m].get('primary')]
        if len(flagged) > 1:
            names = ', '.join(self.elements[m]['name'] for m in flagged)
            self.warnings.append(f"triad: useampi {type_name} merkitty {{primary: true}} ({names}) — käytetään ensimmäistä")
        return flagged[0] if flagged else members[0]

    def _triad_chip_size(self, eid: str, width: int) -> int:
        """Paneelisirun korkeus: nimi (12 px bold) + id/kuvaus (9 px) rivitettynä sirun leveyteen."""
        e = self.elements[eid]
        name_lines = _text.lines_needed(e['name'], max(width - 16, 40), 12, bold=True)
        sub = ' '.join(x for x in ((f"[{e['ref']}]" if e.get('ref') else ''), e.get('subtext', '')) if x)
        sub_lines = _text.lines_needed(sub, max(width - 16, 40), 9) if sub else 0
        return max(46, 14 + name_lines * 15 + sub_lines * 12)

    def _layout_triad(self) -> Dict[str, Tuple[int, int]]:
        """Suunniteltu kehä (ks. luokan kommentti). Palauttaa top-level-sijainnit
        (kontit + konttien ulkopuoliset elementit); jäsenten suhteelliset
        sijainnit menevät _child_positions-sanakirjaan, koot _size_override /
        _computed_sizes -sanakirjoihin, kiertoreitit _triad_detours-sanakirjaan."""
        self._layout_handles_tree = True
        if self.layout_from:
            self.warnings.append("triad: layout_from ei ole tuettu kehäasettelun kanssa — ohitetaan")
            self.layout_from = None
        user_groups = [g for g, grp in self.groups.items() if not grp.get('synthetic')]
        if user_groups:
            self.warnings.append("triad: group:/lane:-rakenteet ohitetaan — kehä sijoittaa elementit itse")
        for gid in list(self.groups):
            for m in self.groups[gid]['members']:
                self.elements[m]['group'] = None
            del self.groups[gid]

        slots, containers, detours = self._triad_slots()
        facets = {'identity': IDENTITY_ELEMENTS, 'architecture': ARCHITECTURE_ELEMENTS, 'experience': EXPERIENCE_ELEMENTS}
        by_type: Dict[str, List[str]] = {}
        for eid, e in self.elements.items():
            by_type.setdefault(e['type'], []).append(eid)

        positions: Dict[str, Tuple[int, int]] = {}
        primaries: Dict[str, str] = {}
        for t, members in by_type.items():
            if t in slots:
                primaries[t] = self._triad_primary(t, members)
        # Kontit
        for facet, (title, (cx0, cy0, cw, ch)) in containers.items():
            gid = f"facet_{facet}"
            self.groups[gid] = {'id': gid, 'kind': 'group', 'name': title, 'members': [], 'tags': [], 'metrics': {},
                                'synthetic': True, 'facet': facet, 'layout': 'triad'}
            self._computed_sizes[gid] = (cw, ch)
            positions[gid] = (cx0, cy0)
        # Ensisijaiset kehälle
        for t, eid in primaries.items():
            cx, cy, w, h = slots[t]
            e = self.elements[eid]
            name_lines = _text.lines_needed(e['name'], w - 16, self._TITLE_FONT, bold=True)
            sub_lines = self._subtext_lines(e, w)
            h = max(h, 20 + name_lines * 18 + sub_lines * 14 + (16 if e.get('tags') or e.get('metrics') else 0))
            self._size_override[eid] = (w, h)
            facet = next((f for f, types in facets.items() if t in types and f"facet_{f}" in self.groups), None)
            if facet:
                gid = f"facet_{facet}"
                self.groups[gid]['members'].append(eid)
                e['group'] = gid
                gx, gy = positions[gid]
                self._child_positions[eid] = (cx - w / 2 - gx, cy - h / 2 - gy)
            else:
                positions[eid] = (cx - w / 2, cy - h / 2)
        # Kiertoreitit kehän reunaa pitkin
        for s_type, t_type, exit_side, entry_side, edge_x in detours:
            if s_type in primaries and t_type in primaries:
                s_cy, t_cy = slots[s_type][1], slots[t_type][1]
                self._triad_detours[(primaries[s_type], primaries[t_type])] = (exit_side, entry_side, [(edge_x, s_cy), (edge_x, t_cy)])
        # "Further <type>" -paneelit kehän alle
        ring_bottom = max([positions[g][1] + self._computed_sizes[g][1] for g in self.groups]
                          + [positions[e][1] + self._size_override[e][1] for e in primaries.values() if e in positions])
        page_w = self._TRIAD_PAGE_W if self.facet == 'all' else 1200
        margin, gap = (50 if self.facet == 'all' else 60), 20   # paneelit samaan vasempaan reunaan kuin facet-kontti (W118)
        panels = []   # (tyyppi, jäsenet, sarakkeet, leveys)
        for t, members in by_type.items():
            rest = [m for m in members if m != primaries.get(t)]
            if not rest:
                continue
            self._triad_hidden.update(rest)
            if len(rest) >= 5:
                panels.append((t, rest, 4, page_w - 2 * margin))
            elif len(rest) >= 2:
                panels.append((t, rest, 2, 400))
            else:
                panels.append((t, rest, 1, 240))
        panels.sort(key=lambda p: -p[3])
        y = ring_bottom + 40
        x, row_h = margin, 0
        lang_key = self.language if self.language in self._TRIAD_FURTHER_TITLE else 'en'
        plural = self._TYPE_PLURAL[lang_key]
        row_members: List[str] = []   # rivin paneelit venytetään rivin korkeimman korkeuteen (tasaiset rivit, W118)

        def stretch_row():
            for g in row_members:
                self._computed_sizes[g] = (self._computed_sizes[g][0], row_h)
            row_members.clear()

        for t, rest, cols, pw in panels:
            pad, top, cgap = 12, 30, 10
            cw = int((pw - 2 * pad - (cols - 1) * cgap) / cols)
            rows = -(-len(rest) // cols)
            heights = [max(self._triad_chip_size(m, cw) for m in rest[r * cols:(r + 1) * cols]) for r in range(rows)]
            ph = top + sum(heights) + (rows - 1) * cgap + pad
            if x > margin and x + pw > page_w - margin:
                stretch_row()
                x, y, row_h = margin, y + row_h + gap, 0
            gid = f"further_{t}"
            row_members.append(gid)
            title = f"{self._TRIAD_FURTHER_TITLE[lang_key]} {plural.get(t, t)}"
            self.groups[gid] = {'id': gid, 'kind': 'group', 'name': title, 'members': list(rest), 'tags': [],
                                'metrics': {}, 'synthetic': True, 'facet': 'further', 'layout': 'triad'}
            self._computed_sizes[gid] = (pw, ph)
            positions[gid] = (x, y)
            cy_rel = top
            for r in range(rows):
                for c, m in enumerate(rest[r * cols:(r + 1) * cols]):
                    self.elements[m]['group'] = gid
                    self._size_override[m] = (cw, heights[r])
                    self._child_positions[m] = (pad + c * (cw + cgap), cy_rel)
                cy_rel += heights[r] + cgap
            x += pw + gap
            row_h = max(row_h, ph)
        stretch_row()
        # Elementit, joilla ei ole slottia (peruselementit yms.): rivi paneelien alle
        placed = set(primaries.values()) | self._triad_hidden
        leftovers = [e for e in self.elements if e not in placed]
        if leftovers:
            ly = y + row_h + gap if panels else ring_bottom + 40
            lx = margin
            for e in leftovers:
                w, h = self._get_element_size(self.elements[e])
                positions[e] = (lx, ly)
                lx += w + 40
        return positions

    # ---- karttatyypit -----------------------------------------------------
    def _calculate_map_type_layout(self, items: List[str], containers: List[str]) -> Dict[str, Tuple[int, int]]:
        """Laske layout karttatyypin mukaan. Reititä strategiaan MAP_TYPE_LAYOUT-taulun kautta."""
        if containers and all(self.groups[c].get('synthetic') == 'stage' for c in containers):
            # Tehtäväkartan vaihesarakkeet: yksi rivi, tasakorkeat sarakkeet; vaiheettomat tehtävät alle
            cols = self.group_columns or len(containers)
            saved, self.align_groups = self.align_groups, 'grid'
            try:
                return self._layout_flow_grid(containers + items, cols)
            finally:
                self.align_groups = saved
        if containers:
            # Ryhmät (esim. kyvykkyysalueet) riveinä; irralliset elementit perään
            cols = self.group_columns or (2 if len(containers) <= 4 else 3)
            return self._layout_flow_grid(containers + items, cols)
        if self.map_type == 'purpose':
            return self._layout_purpose(items)
        if self.map_type == 'summary':
            return self._layout_summary(items)
        if self.map_type == 'organisation' and any(self.elements[i]['type'] == 'process' for i in items):
            return self._layout_organisation_roles(items)
        strategy = MAP_TYPE_LAYOUT.get(self.map_type, 'grid')
        if strategy == 'hub_spoke' and self.map_type != 'purpose' and self._tree_edges_among(items):
            # Portfolio (product), brändiarkkitehtuuri, objektin osat: puu, ei tähti (virallinen tuotekartta)
            return self._layout_forest(items)
        if self.map_type == 'outcome' and len(items) <= self._WEB_MAX and self._web_edges(items):
            return self._layout_layered(items)
        if strategy in ('grid', 'grid_tree'):
            return self._layout_grid(items)
        if strategy == 'tree':
            return self._layout_tree(items)
        if strategy == 'sequence':
            return self._layout_sequence(items)
        if strategy == 'hub_spoke':
            return self._layout_hub_spoke(items)
        return self._layout_grid(items)

    _WEB_MAX = 15        # tulosverkon kerrosasettelu enintään näin monelle elementille; isompi → sivuiksi

    def _tree_edges_among(self, items: List[str]) -> List[Tuple[str, str]]:
        member = set(items)
        return [(r['source'], r['target']) for r in self.relationships
                if r['label'].lower().strip() in TREE_RELATIONSHIPS and r['source'] in member and r['target'] in member]

    def _web_edges(self, items: List[str]) -> List[Tuple[str, str]]:
        """Suunnatut ei-puu-relaatiot elementtien välillä (tulosverkon linkit: enables, …)."""
        member = set(items)
        return [(r['source'], r['target']) for r in self.relationships
                if r['source'] in member and r['target'] in member and r['source'] != r['target']
                and r['label'].lower().strip() not in TREE_RELATIONSHIPS]

    def _layout_forest(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Puu(metsä) ylhäältä alas: jokainen juuri ja sen alipuu vierekkäin alipuun
        leveyden mukaan; puuhun kuulumattomat elementit riviin puun alle. _apply_tree_layout
        sijoittaa lapset juuren alle (tidy tree), joten tässä riittää juurten paikka."""
        tree_children: Dict[str, List[str]] = {}
        child_set = set()
        for src, tgt in self._tree_edges_among(items):
            if tgt not in tree_children.get(src, []):
                tree_children.setdefault(src, []).append(tgt)
            child_set.add(tgt)
        sizes = {i: self._size_of(i) for i in items}
        H_GAP, V_GAP = 40, 110
        in_tree = set(tree_children) | child_set
        roots = [i for i in items if i in tree_children and i not in child_set]

        def depth(n, seen=()):
            kids = [k for k in tree_children.get(n, []) if k not in seen]
            return 1 + max((depth(k, seen + (n,)) for k in kids), default=0)

        positions: Dict[str, Tuple[int, int]] = {}
        x, levels = 60, 1
        for r in roots:
            sw = self._subtree_width(r, tree_children, sizes, H_GAP)
            positions[r] = (x + sw / 2 - sizes[r][0] / 2, 60)
            for n in self._subtree_nodes(r, tree_children):
                positions.setdefault(n, (x, 60))      # _apply_tree_layout siirtää lapset juuren alle
            x += sw + H_GAP * 2
            levels = max(levels, depth(r))
        rest = [i for i in items if i not in in_tree]
        y = 60 + levels * V_GAP + 20
        x = 60
        for i in rest:
            positions[i] = (x, y)
            x += sizes[i][0] + H_GAP
        return positions

    @staticmethod
    def _subtree_nodes(root: str, tree_children: Dict[str, List[str]]) -> List[str]:
        out, stack, seen = [], [root], set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            out.append(n)
            stack.extend(tree_children.get(n, []))
        return out

    def _layout_layered(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Tulosverkko kerroksina vasemmalta oikealle: kerros = pisin polku lähteistä
        (syyt vasemmalla, vaikutukset oikealla), sykli katkaistaan syötejärjestyksessä.
        Kerroksen sisäinen järjestys edeltäjien keskiarvon mukaan (vähemmän risteyksiä);
        kerrokset pystysuunnassa keskitetty. Linkittömät elementit riviin alle.
        Kerrosväli jättää tilaa linkin tekstille."""
        edges = self._web_edges(items)
        succ: Dict[str, List[str]] = {i: [] for i in items}
        for a, b in edges:
            if b not in succ[a]:
                succ[a].append(b)
        # syklit: DFS syötejärjestyksessä, takaisinpäin osoittava linkki jätetään kerroksista pois
        order = {i: n for n, i in enumerate(items)}
        state: Dict[str, int] = {}
        dag: Dict[str, List[str]] = {i: [] for i in items}

        def dfs(n):
            state[n] = 1
            for m in succ[n]:
                if state.get(m) == 1:
                    continue                  # takaisinpäin: ei kerrosrajoitetta
                dag[n].append(m)
                if m not in state:
                    dfs(m)
            state[n] = 2
        for i in items:
            if i not in state:
                dfs(i)
        layer = {i: 0 for i in items}
        changed = True
        while changed:
            changed = False
            for a in items:
                for b in dag[a]:
                    if layer[b] < layer[a] + 1:
                        layer[b] = layer[a] + 1
                        changed = True
        linked = {a for a, _ in edges} | {b for _, b in edges}
        layers: Dict[int, List[str]] = {}
        for i in items:
            if i in linked:
                layers.setdefault(layer[i], []).append(i)
        preds: Dict[str, List[str]] = {i: [] for i in items}
        for a in items:
            for b in dag[a]:
                preds[b].append(a)
        rank: Dict[str, float] = {}
        for k in sorted(layers):
            if k > 0:
                layers[k].sort(key=lambda n: (sum(rank[p] for p in preds[n] if p in rank) / max(1, len([p for p in preds[n] if p in rank]))
                                              if any(p in rank for p in preds[n]) else order[n], order[n]))
            for idx, n in enumerate(layers[k]):
                rank[n] = idx
        sizes = {i: self._size_of(i) for i in items}
        col_w = max(sizes[i][0] for i in items)
        row_h = max(sizes[i][1] for i in items)
        GAP_X, GAP_Y = 140, 80                # GAP_X: tila linkin tekstille kerrosten välissä
        tallest = max((len(v) for v in layers.values()), default=1)
        positions: Dict[str, Tuple[int, int]] = {}
        for k, nodes in layers.items():
            offset = (tallest - len(nodes)) * (row_h + GAP_Y) / 2
            for idx, n in enumerate(nodes):
                positions[n] = (60 + k * (col_w + GAP_X), 60 + offset + idx * (row_h + GAP_Y))
        y = 60 + tallest * (row_h + GAP_Y) + 20
        x = 60
        for i in items:
            if i not in linked:
                positions[i] = (x, y)
                x += sizes[i][0] + 40
        return positions

    def _layout_grid(self, items: List[str] = None) -> Dict[str, Tuple[int, int]]:
        """Adaptiivinen ruudukko: sarakemäärä ≈ sqrt(N), välit elementtikoosta."""
        import math
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys()) if items is None else list(items)
        if not items:
            return positions
        sizes = {eid: self._size_of(eid) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        max_h = max(sizes[eid][1] for eid in items)
        x_start, y_start = 80, 80
        x_spacing = max(180, max_w + 40)
        y_spacing = max(100, max_h + 40)
        cols = max(2, min(5, int(math.sqrt(len(items)))))
        for i, eid in enumerate(items):
            row, col = divmod(i, cols)
            positions[eid] = (x_start + col * x_spacing, y_start + row * y_spacing)
        return positions

    def _layout_tree(self, items: List[str] = None) -> Dict[str, Tuple[int, int]]:
        """Puuhierarkia top-down: ensimmäinen elementti juureksi, loput rivinä alle."""
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys()) if items is None else list(items)
        if not items:
            return positions
        sizes = {eid: self._size_of(eid) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        x_spacing = max(200, max_w + 60)
        y_start = 60
        positions[items[0]] = (380, y_start)
        for i, eid in enumerate(items[1:]):
            positions[eid] = (80 + i * x_spacing, y_start + 120)
        return positions

    def _layout_sequence(self, items: List[str] = None) -> Dict[str, Tuple[int, int]]:
        """Vaakasuuntainen sekvenssi: kaikki elementit yhdellä rivillä vasemmalta oikealle."""
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys()) if items is None else list(items)
        if not items:
            return positions
        sizes = {eid: self._size_of(eid) for eid in items}
        max_w = max(sizes[eid][0] for eid in items)
        x_start, y_start = 60, 200
        x_spacing = max(180, max_w + 40)
        for i, eid in enumerate(items):
            positions[eid] = (x_start + i * x_spacing, y_start)
        return positions

    def _layout_hub_spoke(self, items: List[str] = None) -> Dict[str, Tuple[int, int]]:
        """Keskuselementti + säteittäiset elementit. Säde skaalautuu N:n ja koon mukaan."""
        import math
        positions: Dict[str, Tuple[int, int]] = {}
        items = list(self.elements.keys()) if items is None else list(items)
        if not items:
            return positions
        sizes = {eid: self._size_of(eid) for eid in items}
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
                positions[eid] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        return positions

    def _layout_purpose(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Purpose map hierarkiana (ei hub-and-spoke):

            [Organisation]   [Top purposes: mission, vision]   [Brand]
            [Content]        [Sub-purposes: focus areas …]      [Story]
                             [Outcomes (KPIs) under each sub-purpose]
                             [other elements]

        Tree-relaatiot (purpose → purpose) määräävät ali-Purposet; Outcome
        kiinnittyy Purposeen, jonka kanssa sillä on relaatio (esim. `measures`).
        """
        self._layout_handles_tree = True
        positions: Dict[str, Tuple[int, int]] = {}
        sizes = {eid: self._size_of(eid) for eid in items}
        by_type = lambda t: [i for i in items if self.elements[i]['type'] == t]  # noqa: E731
        tree_children, child_set = self._compute_tree_structure()
        purposes = by_type('purpose')
        pset = set(purposes)
        children = {p: [c for c in tree_children.get(p, []) if c in pset] for p in purposes}
        roots = [pid for pid in purposes if pid not in child_set]
        if not roots and purposes:
            roots = purposes[:1]
        outcomes = by_type('outcome')
        attach: Dict[str, List[str]] = {}
        loose_outcomes = []
        for o in outcomes:
            hit = None
            for rel in self.relationships:
                other = rel['target'] if rel['source'] == o else rel['source'] if rel['target'] == o else None
                if other in pset:
                    hit = other
                    break
            if hit:
                attach.setdefault(hit, []).append(o)
            else:
                loose_outcomes.append(o)
        H_GAP, V_GAP, O_GAP = 40, 90, 50    # sisarusväli, reittikäytävä rivien välissä, Outcome-rivin väli

        def row_width(ids: List[str]) -> float:
            return sum(sizes[i][0] for i in ids) + H_GAP * max(len(ids) - 1, 0)

        def kid_gap(p: str) -> float:
            """Lapsirivin väli: leveämpi kun vanhemman omat Outcomet nousevat lapsirivin läpi
            (`measures`-viiva ja sen teksti tarvitsevat käytävän lasten välissä)."""
            return H_GAP + 60 if attach.get(p) and children[p] else H_GAP

        def subtree_w(p: str) -> float:
            own = sizes[p][0]
            kids = sum(subtree_w(c) for c in children[p]) + kid_gap(p) * max(len(children[p]) - 1, 0)
            return max(own, kids, row_width(attach.get(p, [])))

        def subtree_bottom(p: str, top: float) -> float:
            """Alin y, jonka alipuu (lapset + omat Outcomet) tarvitsee."""
            bottom = top + sizes[p][1]
            if children[p]:
                bottom = max(subtree_bottom(c, top + sizes[p][1] + V_GAP) for c in children[p])
            if attach.get(p):
                bottom = bottom + O_GAP + max(sizes[o][1] for o in attach[p])
            return bottom

        def place(p: str, cx: float, top: float) -> None:
            """Vanhempi keskelle lastensa yläpuolelle; käytävä (V_GAP) lapsiriville;
            Outcomet omalle riville alipuun alle, keskitettynä."""
            w, h = sizes[p]
            positions[p] = (cx - w / 2, top)
            kids = children[p]
            kids_bottom = top + h
            if kids:
                widths = [subtree_w(c) for c in kids]
                gap = kid_gap(p)
                total = sum(widths) + gap * (len(kids) - 1)
                cursor = cx - total / 2
                for c, cw in zip(kids, widths):
                    place(c, cursor + cw / 2, top + h + V_GAP)
                    cursor += cw + gap
                kids_bottom = max(subtree_bottom(c, top + h + V_GAP) for c in kids)
                # Tidy tree: vanhempi lastensa LAATIKOIDEN keskipisteiden puoliväliin
                # (ei alipuiden leveyksien), jotta eri levyiset alipuut eivät vedä sitä sivuun
                first_c = positions[kids[0]][0] + sizes[kids[0]][0] / 2
                last_c = positions[kids[-1]][0] + sizes[kids[-1]][0] / 2
                positions[p] = ((first_c + last_c) / 2 - w / 2, top)
            outs = attach.get(p, [])
            if outs:
                oy = kids_bottom + O_GAP
                ox = cx - row_width(outs) / 2
                for o in outs:
                    positions[o] = (ox, oy)
                    ox += sizes[o][0] + H_GAP

        left_col = by_type('organisation') + by_type('content')
        right_col = by_type('brand') + by_type('story')
        left_w = max([sizes[i][0] for i in left_col], default=0)
        centre_x0 = 60 + (left_w + 80 if left_col else 0)
        y0 = 60
        cursor = centre_x0
        for r in roots:
            rw = subtree_w(r)
            place(r, cursor + rw / 2, y0)
            cursor += rw + H_GAP * 2
        centre_right = max([positions[i][0] + sizes[i][0] for i in positions], default=centre_x0 + 400)
        bottom = max([positions[i][1] + sizes[i][1] for i in positions], default=y0)
        # Irralliset Outcomet omalle riville
        if loose_outcomes:
            ox, oy = centre_x0, bottom + O_GAP
            for o in loose_outcomes:
                positions[o] = (ox, oy)
                ox += sizes[o][0] + H_GAP
            centre_right = max(centre_right, ox - H_GAP)
            bottom = oy + max(sizes[o][1] for o in loose_outcomes)
        # Vasen ja oikea sarake
        ly = y0
        for i in left_col:
            positions[i] = (60, ly)
            ly += sizes[i][1] + 30
        ry = y0
        for i in right_col:
            positions[i] = (centre_right + 60, ry)
            ry += sizes[i][1] + 30
        # Muut elementit alariville
        placed = set(positions)
        bx, by = centre_x0, max(bottom, ly, ry) + O_GAP
        for i in items:
            if i not in placed:
                positions[i] = (bx, by)
                bx += sizes[i][0] + H_GAP
        # Reititys: puuhaarat lähtevät vanhemman alareunasta ja tulevat lapsen yläreunaan
        # (käytävä rivien välissä); Outcomen `measures` nousee yläreunasta Purposen alareunaan
        attached = {o for group in attach.values() for o in group}
        for rel in self.relationships:
            s, t = rel['source'], rel['target']
            opts = rel.setdefault('options', {})
            if s in pset and t in children.get(s, []):
                opts.setdefault('from', 'bottom')
                opts.setdefault('to', 'top')
            elif s in attached and t in pset:
                opts.setdefault('from', 'top')
                opts.setdefault('to', 'bottom')
                if children.get(t):
                    opts.setdefault('label', 'source')   # linja ohittaa lapsirivin: teksti Outcomen päässä
            elif (s in left_col or s in right_col) and t in pset:
                opts.setdefault('label', 'source')     # sarakkeen linkit jakavat käytävän: teksti lähellä lähdettä
                # Useampi juuri: suora viiva sarakkeesta kauempaan juureen kulkisi lähemmän juuren
                # läpi → kierrä ylärivin yläpuolelta (ulos sivulle, ylös, yli, alas juuren yläreunaan)
                if len(roots) > 1 and t in roots and 'via' not in opts:
                    sx, sy = positions[s]
                    sw, sh = sizes[s]
                    tx, ty = positions[t]
                    tw = sizes[t][0]
                    nearest = min(roots, key=lambda r: abs(positions[r][0] - sx))
                    if nearest != t:
                        out_x = sx + sw + 30 if s in right_col else sx - 30
                        opts.setdefault('from', 'right' if s in right_col else 'left')
                        opts.setdefault('to', 'top')
                        opts['via'] = [(out_x, sy + sh / 2), (out_x, y0 - 30), (tx + tw / 2, y0 - 30)]
        return positions

    def _layout_organisation_roles(self, items: List[str]) -> Dict[str, Tuple[int, int]]:
        """Organisation map roolimallina: roolit (Process) sarakkeina ylärivissä,
        toimijat (Organisation) sen roolin alla jota ne suorittavat; toimijat ilman
        roolia omaan sarakkeeseen oikealle; muut elementit alariville."""
        positions: Dict[str, Tuple[int, int]] = {}
        sizes = {eid: self._size_of(eid) for eid in items}
        processes = [i for i in items if self.elements[i]['type'] == 'process']
        orgs = [i for i in items if self.elements[i]['type'] == 'organisation']
        performs: Dict[str, str] = {}
        for rel in self.relationships:
            if rel['source'] in orgs and rel['target'] in processes and rel['source'] not in performs:
                performs[rel['source']] = rel['target']
        GAP_X, GAP_Y = 40, 40
        x, y0 = 60, 60
        col_x: Dict[str, int] = {}
        for pid in processes:
            col_members = [o for o in orgs if performs.get(o) == pid]
            col_w = max([sizes[pid][0]] + [sizes[o][0] for o in col_members])
            positions[pid] = (x, y0)
            oy = y0 + sizes[pid][1] + GAP_Y + 20
            for o in col_members:
                positions[o] = (x, oy)
                oy += sizes[o][1] + GAP_Y
            col_x[pid] = x
            x += col_w + GAP_X
        unassigned = [o for o in orgs if o not in performs]
        if unassigned:
            oy = y0 + max(sizes[p][1] for p in processes) + GAP_Y + 20 if processes else y0
            for o in unassigned:
                positions[o] = (x, oy)
                oy += sizes[o][1] + GAP_Y
            x += max(sizes[o][0] for o in unassigned) + GAP_X
        max_y = max([py + sizes[i][1] for i, (px, py) in positions.items()], default=y0)
        bx, by = 60, max_y + GAP_Y + 20
        for i in items:
            if i not in positions:
                positions[i] = (bx, by)
                bx += sizes[i][0] + GAP_X
        return positions

    # ---- facet-layoutit ---------------------------------------------------
    def _calculate_facet_layout(self, items: List[str], containers: List[str]) -> Dict[str, Tuple[int, int]]:
        """EDGY Facet Model -asettelu konteilla.

        facet: all
        ┌ Identity ┐       ┌ Architecture ┐       ┌ Experience ┐
        │ Purpose  │ [Org] │ Capability   │ [Prod]│ Task       │
        │ Content  │       │ Asset        │       │ Channel    │
        │ Story    │       │ Process      │       │ Journey    │
        └──────────┘       └──────────────┘       └────────────┘
                      [ Brand — Identity ↔ Experience bridge ]
                      [ base elements: people, activity, outcome, object ]

        Intersection-elementit sijoittuvat niiden fasettien VÄLIIN joita ne
        yhdistävät (Organisation: Identity↔Architecture, Product:
        Architecture↔Experience, Brand: Identity↔Experience alhaalla keskellä).
        Yksittäinen facet: oma kontti (ruudukko) + intersection-elementit alle,
        3 per rivi.
        """
        positions: Dict[str, Tuple[int, int]] = {}
        sizes = {i: self._size_of(i) for i in items}
        gsize = {g: self._computed_sizes.get(g, (240, 100)) for g in containers}
        by_type = lambda t: [i for i in items if self.elements[i]['type'] == t]  # noqa: E731
        orgs, products, brands = by_type('organisation'), by_type('product'), by_type('brand')
        base = [i for i in items if self.elements[i]['type'] in BASE_ELEMENTS]
        placed = set()

        if self.facet == 'all':
            cols = {f: f"facet_{f}" for f in ('identity', 'architecture', 'experience') if f"facet_{f}" in containers}
            x, y0 = 60, 60
            col_x: Dict[str, int] = {}
            col_h = max([gsize[g][1] for g in cols.values()], default=300)

            def stack_between(items_, x_pos):
                """Pino intersection-elementit pystysuoraan konttien väliin, keskitettynä."""
                total = sum(sizes[i][1] for i in items_) + 20 * (len(items_) - 1)
                yy = y0 + max((col_h - total) / 2, 40)
                for i in items_:
                    positions[i] = (x_pos, yy)
                    placed.add(i)
                    yy += sizes[i][1] + 20

            gap_org = max([sizes[o][0] for o in orgs], default=0) + 80 if orgs else 60
            gap_prod = max([sizes[o][0] for o in products], default=0) + 80 if products else 60
            for f in ('identity', 'architecture', 'experience'):
                g = cols.get(f)
                if g:
                    positions[g] = (x, y0)
                    col_x[f] = x
                    x += gsize[g][0]
                if f == 'identity':
                    if orgs:
                        stack_between(orgs, x + 40)
                    x += gap_org
                elif f == 'architecture':
                    if products:
                        stack_between(products, x + 40)
                    x += gap_prod
            right_edge = x
            y = y0 + col_h + 60
            # Brand: silta Identity ↔ Experience, keskellä alhaalla
            if brands:
                total_w = sum(sizes[b][0] for b in brands) + 40 * (len(brands) - 1)
                bx = max(60, (60 + right_edge) / 2 - total_w / 2)
                for b in brands:
                    positions[b] = (bx, y)
                    placed.add(b)
                    bx += sizes[b][0] + 40
                y += max(sizes[b][1] for b in brands) + 40
            # Peruselementit ja muut
            bx = 60
            for i in items:
                if i not in placed and i not in positions:
                    positions[i] = (bx, y)
                    bx += sizes[i][0] + 40
            return positions

        # Yksittäinen facet
        x0, y0 = 60, 60
        y = y0
        if self.group_columns and containers:
            positions.update(self._layout_flow_grid(containers, self.group_columns, x0, y0))
            y = max(positions[g][1] + self._size_of(g)[1] for g in containers) + 40
        else:
            for g in containers:
                positions[g] = (x0, y)
                y += gsize[g][1] + 40
        inter = orgs + products + brands
        wrap = 3
        x, row_h = x0, 0
        for i, eid in enumerate(inter):
            if i and i % wrap == 0:
                x, y, row_h = x0, y + row_h + 30, 0
            positions[eid] = (x, y)
            placed.add(eid)
            x += sizes[eid][0] + 40
            row_h = max(row_h, sizes[eid][1])
        if inter:
            y += row_h + 40
        x = x0
        for i in items:
            if i not in positions:
                positions[i] = (x, y)
                x += sizes[i][0] + 40
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
        sizes = {eid: self._size_of(eid) for eid in positions}

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
