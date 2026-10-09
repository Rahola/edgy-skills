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
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edgy_core_links import CORE_LINKS, CORE_LINK_ALIASES, INFLUENCE_VERBS, LANGUAGES  # noqa: E402

# Flow and tree verbs are defined in the parser as flat sets; their
# translations live here so they can be rendered per language.
FLOW_VERBS = [
    {'en': 'flows', 'fi': 'virtaa', 'fr': 'circule', 'de': 'fließt'},
    {'en': 'transfers', 'fi': 'siirtyy', 'fr': 'transfère', 'de': 'überträgt'},
    {'en': 'sends', 'fi': 'lähettää', 'fr': 'envoie', 'de': 'sendet'},
    {'en': 'receives', 'fi': 'vastaanottaa', 'fr': 'reçoit', 'de': 'empfängt'},
    {'en': 'produces data', 'fi': 'tuottaa dataa', 'fr': 'produit des données', 'de': 'erzeugt Daten'},
    {'en': 'returns', 'fi': 'palauttaa', 'fr': 'retourne', 'de': 'gibt zurück'},
]
TREE_VERBS = [
    {'en': 'contains', 'fi': 'sisältää', 'fr': 'contient', 'de': 'enthält'},
    {'en': 'comprises', 'fi': 'koostuu', 'fr': 'comprend', 'de': 'umfasst'},
    {'en': 'decomposes', 'fi': 'jakaantuu', 'fr': 'se décompose', 'de': 'zerlegt sich'},
]

# verb (lower) → {lang: verb}: the first row for a spelling; a verb spelled the
# same in several entries with the same translations (e.g. 'requires' on three
# core pairs) shares one row. A spelling whose translations differ by core-link
# pair (de 'erscheint in' = brand → journey 'appears in' / product → journey
# 'features in') keeps every candidate row in _CANDIDATES with the pairs it
# belongs to, and translate() picks by the relationship's (source, target).
_ROWS: Dict[str, Dict[str, str]] = {}
_LANGS: Dict[str, Set[str]] = {}
_CANDIDATES: Dict[str, List[Tuple[Dict[str, str], Optional[Set[Tuple[str, str]]]]]] = {}


def _add(row: Dict[str, str], pair: Optional[Tuple[str, str]] = None) -> None:
    clean = {l: row[l] for l in LANGUAGES if row.get(l)}
    for lang, verb in clean.items():
        key = verb.lower().strip()
        _ROWS.setdefault(key, {}).update({l: v for l, v in clean.items() if l not in _ROWS.get(key, {})})
        _LANGS.setdefault(key, set()).add(lang)
        cands = _CANDIDATES.setdefault(key, [])
        for crow, cpairs in cands:
            if crow == clean:
                if pair and cpairs is not None:
                    cpairs.add(pair)
                break
        else:
            cands.append((clean, {pair} if pair else None))


for _s, _t, _verbs, _g in CORE_LINKS:
    _add(_verbs, (_s, _t))
for _row in INFLUENCE_VERBS + FLOW_VERBS + TREE_VERBS:
    _add(_row)
# accepted alternative spellings (e.g. fi 'osa' for 'on osa'): same row, same languages as the canonical spelling
for _alias, _canonical in CORE_LINK_ALIASES.items():
    _row = _ROWS.get(_canonical.lower().strip())
    if _row:
        _ROWS[_alias.lower().strip()] = _row
        _LANGS[_alias.lower().strip()] = {l for l, v in _row.items() if v.lower().strip() == _canonical.lower().strip()}
        _CANDIDATES[_alias.lower().strip()] = _CANDIDATES.get(_canonical.lower().strip(), [(_row, None)])


def languages_of(verb: str) -> Set[str]:
    """Languages in which `verb` is a vocabulary entry (empty for free text)."""
    return set(_LANGS.get((verb or '').lower().strip(), ()))


def translate(verb: str, lang: str, pair: Optional[Tuple[str, str]] = None) -> Optional[str]:
    """`verb` rendered in `lang`, or None when the verb is not in the vocabulary
    or has no entry in that language. A verb already in `lang` returns itself.
    `pair` = (source type, target type) of the relationship picks the right row
    when one spelling belongs to several core links with different translations;
    without a pair, or when no candidate matches it, the first row wins."""
    key = (verb or '').lower().strip()
    cands = _CANDIDATES.get(key)
    if not cands:
        return None
    if pair and len(cands) > 1:
        for crow, cpairs in cands:
            if cpairs and pair in cpairs and crow.get(lang):
                return crow[lang]
    for crow, _cp in cands:
        if crow.get(lang):
            return crow[lang]
    return None


def is_vocabulary(verb: str) -> bool:
    return (verb or '').lower().strip() in _ROWS
