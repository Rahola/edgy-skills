#!/usr/bin/env python3
"""
edgy_notation.py — registry of notation handlers (extension contract 1).

A page in another notation than EDGY (C4 in edgy-c4, v2.5.0) is drawn and
validated by a *notation handler*: a skill that ships a `notation.json` next
to its SKILL.md:

    {"notation": "c4", "contract": 1, "module": "scripts/edgy_c4.py"}

The module may define

    generate_page(page_text: str, graph) -> str      # mxGraphModel XML of one page
    lint_page(cells: dict, page_name: str) -> list   # [(level, rule, message, cell_id)]

Every cell a handler writes carries `edgyNotation=<name>`. Core rules are
**fail closed**: the EDGY rules E009 (legend), W102 (palette) and W105
(vocabulary) are switched off only on pages of a *registered and installed*
notation. An unknown notation, or a known one whose handler is not
installed, is E013 — never a clean pass. EDGY and foreign cells on one page
are E012.

Handlers are found, in order, in:
  1. $EDGY_NOTATION_PATH (os.pathsep-separated directories; each is a skill
     directory or a directory of skill directories)
  2. the installed skills next to edgy-diagram (<skills dir>/*/notation.json)
  3. the repository checkout (skills/*/*/notation.json)

Standard library only.
"""

import importlib.util
import json
import os
from typing import Dict, List, Optional

CONTRACT = 1
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)                      # …/edgy-diagram
_CACHE: Dict[str, dict] = {}
_CACHE_KEY: Optional[str] = None


def _search_dirs() -> List[str]:
    dirs = [d for d in (os.environ.get('EDGY_NOTATION_PATH') or '').split(os.pathsep) if d]
    parent = os.path.dirname(SKILL_DIR)                 # installed: <skills dir>; checkout: skills/documentation
    dirs.append(parent)
    repo_skills = os.path.dirname(parent)               # checkout: skills/
    if os.path.basename(repo_skills) == 'skills':
        dirs.extend(os.path.join(repo_skills, c) for c in sorted(os.listdir(repo_skills))
                    if os.path.isdir(os.path.join(repo_skills, c)))
    return dirs


def handlers() -> Dict[str, dict]:
    """{notation: {'notation', 'contract', 'dir', 'module'}} of every registered handler."""
    global _CACHE_KEY, _CACHE
    key = os.environ.get('EDGY_NOTATION_PATH') or ''
    if _CACHE_KEY == key:
        return _CACHE
    found: Dict[str, dict] = {}
    for d in _search_dirs():
        if not os.path.isdir(d):
            continue
        cands = [d] + [os.path.join(d, c) for c in sorted(os.listdir(d)) if os.path.isdir(os.path.join(d, c))]
        for skill in cands:
            path = os.path.join(skill, 'notation.json')
            if not os.path.isfile(path):
                continue
            try:
                spec = json.load(open(path, encoding='utf-8'))
            except (OSError, ValueError):
                continue
            name = str(spec.get('notation') or '').lower()
            if name and name not in found and int(spec.get('contract', 0) or 0) == CONTRACT:
                found[name] = {**spec, 'notation': name, 'dir': skill}
    _CACHE_KEY, _CACHE = key, found
    return found


def handler(notation: str) -> Optional[dict]:
    return handlers().get((notation or '').lower())


def load_module(notation: str):
    """The handler module, or None when the notation is unknown or its module cannot be loaded."""
    h = handler(notation)
    if not h or not h.get('module'):
        return None
    path = os.path.join(h['dir'], h['module'])
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location(f"edgy_notation_{h['notation']}", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:          # a broken handler is an unavailable handler: E013, not a crash
        return None
    return mod


def unsupported_message(notation: str) -> str:
    known = ', '.join(sorted(handlers())) or 'none installed'
    return (f"E013 unsupported notation '{notation}' — no registered handler is installed (registered: {known}); "
            f"install the skill that draws it (e.g. edgy-c4 for c4) or remove the notation: key")
