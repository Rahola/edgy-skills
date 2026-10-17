#!/usr/bin/env python3
"""
edgy_paths.py — where the edgy-diagram scripts are, in a repo checkout and after an install.

The adapters copy every skill into its own directory (`~/.claude/skills/<id>/`),
so a path relative to the repository layout (`../../../documentation/edgy-diagram`)
only works in a checkout. Lookup order:

  1. $EDGY_DIAGRAM_SCRIPTS                     (explicit override)
  2. <skills dir>/edgy-diagram/scripts         (installed: sibling skill directory)
  3. <repo>/skills/documentation/edgy-diagram/scripts   (repository checkout)

The first directory that holds `edgy_core_links.py` wins. Standard library only.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

HERE = Path(__file__).resolve().parent


def candidates() -> List[Path]:
    out = []
    env = os.environ.get('EDGY_DIAGRAM_SCRIPTS')
    if env:
        out.append(Path(env).expanduser())
    out.append(HERE.parent.parent / 'edgy-diagram' / 'scripts')                       # installed
    out.append(HERE.parent.parent.parent / 'documentation' / 'edgy-diagram' / 'scripts')   # checkout
    return out


def diagram_scripts() -> Optional[Path]:
    for c in candidates():
        if (c / 'edgy_core_links.py').is_file():
            return c
    return None


def add_diagram_scripts_to_path() -> Optional[Path]:
    """Put the edgy-diagram scripts on sys.path; returns the directory or None when not found."""
    d = diagram_scripts()
    if d is not None and str(d) not in sys.path:
        sys.path.insert(0, str(d))
    return d


def not_found_message(tool: str) -> str:
    tried = ', '.join(str(c) for c in candidates())
    return (f"{tool}: cannot find the edgy-diagram scripts (tried {tried}). Install the edgy-diagram skill next to "
            f"this one, or set EDGY_DIAGRAM_SCRIPTS=<path to edgy-diagram/scripts>.")
