#!/usr/bin/env python3
"""
skill_utils.py — Yhteinen apumoduuli skills-työkaluille

Sisältää jaetut funktiot:
  - parse_frontmatter(text): parsii YAML frontmatter SKILL.md-tiedostoista
  - load_registry(registry_path): lataa registry.yaml
"""

import sys

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml")
    sys.exit(1)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parsii YAML frontmatter SKILL.md-tiedostosta.

    Args:
        text: Tiedoston koko sisältö merkkijonona.

    Returns:
        (frontmatter_dict, markdown_body) — jos frontmatter puuttuu tai on
        virheellinen, frontmatter_dict on None ja markdown_body sisältää
        joko alkuperäisen tekstin tai virheviestin.
    """
    if not text.startswith("---"):
        return None, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text

    yaml_str = parts[1]
    markdown_body = parts[2].strip()

    try:
        frontmatter = yaml.safe_load(yaml_str)
        return frontmatter, markdown_body
    except yaml.YAMLError as e:
        return None, str(e)


def load_registry(registry_path: str) -> dict:
    """Lataa registry.yaml annetusta polusta.

    Args:
        registry_path: Polku registry.yaml-tiedostoon (str tai Path).

    Returns:
        Registry-sisältö dict-muodossa, tai tyhjä dict jos tiedostoa ei löydy.
    """
    import os
    from pathlib import Path

    path = Path(registry_path)
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}
