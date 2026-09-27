"""
edgy_core_links.py — GENERATED FILE, DO NOT EDIT.

Source: skills/_shared/edgy-core-links.yaml
Regenerate with: python3 tools/render-core-links.py

Provides the EDGY 23 relationship vocabulary for edgy_parser.py and
edgy_lint.py: the 24 official core links with their allowed
(source, target) pairs in four languages, and the influence-verb
vocabulary used for every other relationship.
"""

LANGUAGES = ('en', 'fi', 'fr', 'de')

# (source, target, {'en': verb, 'fi': verb, 'fr': verb, 'de': verb}, group)
CORE_LINKS = [
    ('story', 'purpose', {'en': 'contextualises', 'fi': 'kontekstualisoi', 'fr': 'contextualise', 'de': 'kontextualisiert'}, 'identity'),
    ('content', 'purpose', {'en': 'expresses', 'fi': 'ilmaisee', 'fr': 'exprime', 'de': 'drückt aus'}, 'identity'),
    ('content', 'story', {'en': 'conveys', 'fi': 'välittää', 'fr': 'transmet', 'de': 'vermittelt'}, 'identity'),
    ('brand', 'story', {'en': 'evokes', 'fi': 'herättää', 'fr': 'évoque', 'de': 'evoziert'}, 'identity'),
    ('brand', 'purpose', {'en': 'represents', 'fi': 'edustaa', 'fr': 'représente', 'de': 'repräsentiert'}, 'identity'),
    ('capability', 'asset', {'en': 'requires', 'fi': 'vaatii', 'fr': 'nécessite', 'de': 'erfordert'}, 'architecture'),
    ('process', 'capability', {'en': 'realises', 'fi': 'toteuttaa', 'fr': 'réalise', 'de': 'realisiert'}, 'architecture'),
    ('process', 'asset', {'en': 'requires', 'fi': 'vaatii', 'fr': 'nécessite', 'de': 'erfordert'}, 'architecture'),
    ('product', 'capability', {'en': 'requires', 'fi': 'vaatii', 'fr': 'nécessite', 'de': 'erfordert'}, 'architecture'),
    ('process', 'product', {'en': 'creates', 'fi': 'luo', 'fr': 'crée', 'de': 'erzeugt'}, 'architecture'),
    ('task', 'journey', {'en': 'is part of', 'fi': 'on osa', 'fr': 'fait partie de', 'de': 'ist Teil von'}, 'experience'),
    ('task', 'channel', {'en': 'uses', 'fi': 'käyttää', 'fr': 'utilise', 'de': 'nutzt'}, 'experience'),
    ('journey', 'channel', {'en': 'traverses', 'fi': 'kulkee', 'fr': 'traverse', 'de': 'durchläuft'}, 'experience'),
    ('brand', 'task', {'en': 'supports', 'fi': 'tukee', 'fr': 'soutient', 'de': 'unterstützt'}, 'experience'),
    ('brand', 'journey', {'en': 'appears in', 'fi': 'näkyy', 'fr': 'apparaît dans', 'de': 'erscheint in'}, 'experience'),
    ('organisation', 'purpose', {'en': 'pursues', 'fi': 'tavoittelee', 'fr': 'poursuit', 'de': 'verfolgt'}, 'organisation'),
    ('organisation', 'story', {'en': 'authors', 'fi': 'kirjoittaa', 'fr': 'rédige', 'de': 'verfasst'}, 'organisation'),
    ('organisation', 'capability', {'en': 'has', 'fi': 'omistaa', 'fr': 'possède', 'de': 'besitzt'}, 'organisation'),
    ('organisation', 'process', {'en': 'performs', 'fi': 'suorittaa', 'fr': 'exécute', 'de': 'führt aus'}, 'organisation'),
    ('product', 'task', {'en': 'serves', 'fi': 'palvelee', 'fr': 'sert', 'de': 'bedient'}, 'product'),
    ('product', 'journey', {'en': 'features in', 'fi': 'esiintyy', 'fr': 'figure dans', 'de': 'erscheint in'}, 'product'),
    ('organisation', 'brand', {'en': 'builds', 'fi': 'rakentaa', 'fr': 'construit', 'de': 'baut auf'}, 'cross'),
    ('organisation', 'product', {'en': 'makes', 'fi': 'valmistaa', 'fr': 'fabrique', 'de': 'stellt her'}, 'cross'),
    ('product', 'brand', {'en': 'embodies', 'fi': 'ilmentää', 'fr': 'incarne', 'de': 'verkörpert'}, 'cross'),
]

# Accepted alternative spellings: verb → canonical verb
CORE_LINK_ALIASES = {
    'osa': 'on osa',
}

# Influence verbs (non-core relationships → dashed line, open arrowhead)
INFLUENCE_VERBS = [
    {'en': 'enables', 'fi': 'mahdollistaa', 'fr': 'permet', 'de': 'ermöglicht', 'usage': 'A makes B possible'},
    {'en': 'guides', 'fi': 'ohjaa', 'fr': 'guide', 'de': 'steuert', 'usage': 'A steers or constrains B'},
    {'en': 'influences', 'fi': 'vaikuttaa', 'fr': 'influence', 'de': 'beeinflusst', 'usage': 'generic influence when nothing more specific fits'},
    {'en': 'offers', 'fi': 'tarjoaa', 'fr': 'offre', 'de': 'bietet', 'usage': 'A makes B available (non-core product/channel pairs)'},
    {'en': 'manages', 'fi': 'hallinnoi', 'fr': 'gère', 'de': 'verwaltet', 'usage': 'A administers B (organisation → asset'},
    {'en': 'reflects', 'fi': 'heijastaa', 'fr': 'reflète', 'de': 'spiegelt', 'usage': 'B mirrors A (content → brand'},
    {'en': 'strengthens', 'fi': 'vahvistaa', 'fr': 'renforce', 'de': 'stärkt', 'usage': 'A reinforces B'},
    {'en': 'defines', 'fi': 'määrittelee', 'fr': 'définit', 'de': 'definiert', 'usage': 'A sets the scope or rules of B'},
    {'en': 'depends on', 'fi': 'riippuu', 'fr': 'dépend de', 'de': 'hängt ab von', 'usage': 'A cannot exist without B (non-core pairs; core pairs use requires)'},
    {'en': 'produces', 'fi': 'tuottaa', 'fr': 'produit', 'de': 'bringt hervor', 'usage': 'process → outcome: a process yields a measurable result'},
    {'en': 'measures', 'fi': 'mittaa', 'fr': 'mesure', 'de': 'misst', 'usage': 'outcome → purpose: an outcome (KPI) measures a purpose'},
    {'en': 'contributes to', 'fi': 'edistää', 'fr': 'contribue à', 'de': 'trägt bei zu', 'usage': 'capability → purpose or outcome: bridge when no core link exists'},
]


def _build():
    verbs = {}
    pairs = {}
    for source, target, names, _group in CORE_LINKS:
        for verb in names.values():
            key = verb.lower()
            verbs[key] = 'link'
            pairs.setdefault(key, set()).add((source, target))
    for alias, canonical in CORE_LINK_ALIASES.items():
        key = alias.lower()
        verbs[key] = 'link'
        pairs[key] = set(pairs[canonical.lower()])
    influence = set()
    for entry in INFLUENCE_VERBS:
        for lang in LANGUAGES:
            influence.add(entry[lang].lower())
    return verbs, pairs, influence


# verb (lower-case) → 'link'   — every accepted core-link verb in any language
# verb (lower-case) → {(source_type, target_type), ...} — allowed pairs
# influence verbs (lower-case)
EDGY_CORE_LINKS, CORE_LINK_PAIRS, INFLUENCE_RELATIONSHIPS = _build()


def core_link_pairs(verb):
    """Allowed (source, target) pairs for a verb, or an empty set if it is not a core-link verb."""
    return CORE_LINK_PAIRS.get(verb.lower().strip(), set())


def is_core_link(verb):
    return verb.lower().strip() in EDGY_CORE_LINKS


def is_influence_verb(verb):
    return verb.lower().strip() in INFLUENCE_RELATIONSHIPS
