#!/usr/bin/env python3
"""
registry-updater.py — Skannaa skills/-hakemiston ja päivittää registry.yaml

Käyttö:
    python tools/registry-updater.py
    python tools/registry-updater.py --dry-run
    python tools/registry-updater.py --skills-dir skills/ --registry registry.yaml
"""

import sys
import os
import argparse
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml")
    sys.exit(1)

# Lisää tools/-hakemisto sys.path:iin jotta skill_utils löytyy
sys.path.insert(0, str(Path(__file__).parent))
from skill_utils import parse_frontmatter, load_registry as _load_registry_util


def parse_skill_frontmatter(skill_file: Path) -> dict | None:
    """Parsii SKILL.md:n YAML frontmatterin."""
    content = skill_file.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(content)
    return frontmatter


def skill_to_registry_entry(skill_file: Path, skills_root: Path) -> dict | None:
    """Muuntaa SKILL.md:n registry.yaml-merkinnäksi."""
    frontmatter = parse_skill_frontmatter(skill_file)
    if not frontmatter or not isinstance(frontmatter, dict):
        return None

    required = ["name", "version", "category", "tags", "agents"]
    if not all(k in frontmatter for k in required):
        return None

    # Laske suhteellinen polku skills-juuresta
    skill_dir = skill_file.parent
    try:
        rel_path = skill_dir.relative_to(skills_root.parent)
    except ValueError:
        rel_path = skill_dir

    return {
        "id": frontmatter["name"],
        "path": str(rel_path).replace("\\", "/"),
        "version": frontmatter["version"],
        "category": frontmatter["category"],
        "tags": frontmatter.get("tags", []),
        "agents": frontmatter.get("agents", []),
        "description": str(frontmatter.get("description", "")).strip(),
    }


def load_registry(registry_path: Path) -> dict:
    """Lataa olemassa oleva registry.yaml tai palauttaa tyhjän rakenteen."""
    return _load_registry_util(str(registry_path))


def main():
    parser = argparse.ArgumentParser(description="Päivittää registry.yaml skills/-hakemiston perusteella")
    parser.add_argument("--skills-dir", default="skills", help="Skills-hakemisto (oletus: skills/)")
    parser.add_argument("--registry", default="registry.yaml", help="Registry-tiedosto (oletus: registry.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Näytä muutokset ilman kirjoittamista")
    args = parser.parse_args()

    # Yritä löytää skills-hakemisto suhteessa nykyiseen tai repo-juureen
    skills_dir = Path(args.skills_dir)
    if not skills_dir.exists():
        # Kokeile repo-juuresta
        repo_root = Path(__file__).parent.parent
        skills_dir = repo_root / args.skills_dir

    if not skills_dir.exists():
        print(f"Virhe: skills-hakemistoa ei löydy: {args.skills_dir}")
        sys.exit(1)

    registry_path = Path(args.registry)
    if not registry_path.exists():
        repo_root = Path(__file__).parent.parent
        registry_path = repo_root / args.registry

    # Skannaa kaikki SKILL.md-tiedostot
    skill_files = sorted(skills_dir.rglob("SKILL.md"))
    print(f"Löydetty {len(skill_files)} SKILL.md-tiedostoa hakemistosta: {skills_dir}")

    new_entries = []
    skipped = []

    for skill_file in skill_files:
        entry = skill_to_registry_entry(skill_file, skills_dir)
        if entry:
            new_entries.append(entry)
            print(f"  ✓ {entry['id']} v{entry['version']} ({entry['category']})")
        else:
            skipped.append(skill_file)
            print(f"  ⚠ Ohitettu (puutteellinen frontmatter): {skill_file}")

    if skipped:
        print(f"\n{len(skipped)} tiedostoa ohitettu puutteellisten metatietojen vuoksi.")

    # Luo päivitetty registry
    new_registry = {
        "version": f"{date.today().year}-{date.today().month}",
        "updated": date.today().isoformat(),
        "skills": new_entries,
    }

    # Näytä muutokset
    old_registry = load_registry(registry_path)
    old_ids = {s["id"] for s in old_registry.get("skills", [])}
    new_ids = {s["id"] for s in new_entries}

    added = new_ids - old_ids
    removed = old_ids - new_ids

    if added:
        print(f"\nUudet skillit: {', '.join(sorted(added))}")
    if removed:
        print(f"Poistetut skillit: {', '.join(sorted(removed))}")
    if not added and not removed:
        print("\nEi muutoksia skillilistaan.")

    if args.dry_run:
        print("\n[DRY RUN] registry.yaml ei päivitetty. Lopputulos olisi:")
        print(yaml.dump(new_registry, allow_unicode=True, sort_keys=False))
        return

    # Kirjoita registry.yaml
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(f"version: \"{new_registry['version']}\"\n")
        f.write(f"updated: \"{new_registry['updated']}\"\n\n")
        f.write("skills:\n")
        for skill in new_entries:
            f.write(f"  - id: {skill['id']}\n")
            f.write(f"    path: {skill['path']}\n")
            f.write(f"    version: {skill['version']}\n")
            f.write(f"    category: {skill['category']}\n")
            tags_str = ", ".join(skill['tags'])
            f.write(f"    tags: [{tags_str}]\n")
            agents_str = ", ".join(skill['agents'])
            f.write(f"    agents: [{agents_str}]\n")
            if skill.get('description'):
                # Kirjoita kuvaus multiline-muodossa jos pitkä
                desc = skill['description'].replace('\n', ' ')
                f.write(f"    description: >\n      {desc}\n")
            f.write("\n")

    print(f"\n✓ registry.yaml päivitetty: {registry_path}")
    print(f"  Yhteensä {len(new_entries)} skilliä.")


if __name__ == "__main__":
    main()
