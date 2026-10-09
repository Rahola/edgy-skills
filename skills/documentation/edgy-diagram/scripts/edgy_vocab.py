#!/usr/bin/env python3
"""
edgy_vocab.py — the relationship vocabulary by language, for rendering and lint.

The generated `edgy_core_links.py` (from skills/_shared/edgy-core-links.yaml)
holds the 24 core links and the influence verbs in four languages; the
parser adds the flow and tree verbs. This module turns them into two
questions the generator and the linter ask:

  languages_of(verb)              -> {'en', 'fi', …}   which languages spell a verb this way
  translate(verb, lang)           -> verb in `lang`, or None when unknown

The model keeps canonical verb codes (the English key); only the *label*
changes with `language:`. Standard library only.
"""

import os
import sys
from typing import Dict, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edgy_core_links import CORE_LINKS, INFLUENCE_VERBS, LANGUAGES  # noqa: E402

# Flow and tree verbs are defined in the parser as flat sets; their
# translations live here so they can be rendered per language.
FLOW_VERBS = [
    {'en': 'flows', 'fi': 'virtaa', 'fr': 'circule', 'de': 'fließt'},
    {'en': 'transfers', 'fi': 'siirtyy', 'fr': 'transfère', 'de': 'überträgt'},
    {'en': 'produces data', 'fi': 'tuottaa dataa', 'fr': 'produit des données', 'de': 'erzeugt Daten'},
    {'en': 'returns', 'fi': 'palauttaa', 'fr': 'retourne', 'de': 'gibt zurück'},
]
TREE_VERBS = [
    {'en': 'contains', 'fi': 'sisältää', 'fr': 'contient', 'de': 'enthält'},
    {'en': 'comprises', 'fi': 'koostuu', 'fr': 'comprend', 'de': 'umfasst'},
    {'en': 'decomposes', 'fi': 'jakaantuu', 'fr': 'se décompose', 'de': 'zerlegt sich'},
]

# verb (lower) → {lang: verb}: one row per vocabulary entry; a verb that is
# spelled the same in several entries (e.g. 'requires' on three core pairs)
# maps to the same translations, so merging rows is safe.
_ROWS: Dict[str, Dict[str, str]] = {}
_LANGS: Dict[str, Set[str]] = {}


def _add(row: Dict[str, str]) -> None:
    clean = {l: row[l] for l in LANGUAGES if row.get(l)}
    for lang, verb in clean.items():
        key = verb.lower().strip()
        _ROWS.setdefault(key, {}).update({l: v for l, v in clean.items() if l not in _ROWS.get(key, {})})
        _LANGS.setdefault(key, set()).add(lang)


for _s, _t, _verbs, _g in CORE_LINKS:
    _add(_verbs)
for _row in INFLUENCE_VERBS + FLOW_VERBS + TREE_VERBS:
    _add(_row)


def languages_of(verb: str) -> Set[str]:
    """Languages in which `verb` is a vocabulary entry (empty for free text)."""
    return set(_LANGS.get((verb or '').lower().strip(), ()))


def translate(verb: str, lang: str) -> Optional[str]:
    """`verb` rendered in `lang`, or None when the verb is not in the vocabulary
    or has no entry in that language. A verb already in `lang` returns itself."""
    row = _ROWS.get((verb or '').lower().strip())
    if not row:
        return None
    return row.get(lang)


def is_vocabulary(verb: str) -> bool:
    return (verb or '').lower().strip() in _ROWS
