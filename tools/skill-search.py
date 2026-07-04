#!/usr/bin/env python3
"""
skill-search.py — CLI-työkalu skillien etsimiseen registry.yaml:sta

Käyttö:
    python tools/skill-search.py --tag meetings
    python tools/skill-search.py --tag meetings --lang fi
    python tools/skill-search.py --category documentation
    python tools/skill-search.py --agent claude-code
    python tools/skill-search.py --list
    python tools/skill-search.py install meeting-minutes --agent claude-code
"""

import sys
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml")
    sys.exit(1)

# Lisää tools/-hakemisto sys.path:iin jotta skill_utils löytyy
sys.path.insert(0, str(Path(__file__).parent))
from skill_utils import load_registry as _load_registry_util


def load_registry(registry_path: Path) -> dict:
    """Lataa registry.yaml."""
    if not Path(registry_path).exists():
        print(f"Virhe: registry.yaml ei löydy: {registry_path}")
        sys.exit(1)

    data = _load_registry_util(str(registry_path))

    if not isinstance(data, dict) or "skills" not in data:
        print("Virhe: registry.yaml on virheellinen tai tyhjä.")
        sys.exit(1)

    return data


def filter_skills(skills: list[dict], tags: list[str], lang: str | None,
                  category: str | None, agent: str | None) -> list[dict]:
    """Suodattaa skillit annettujen kriteerien perusteella."""
    results = skills

    if tags:
        for tag in tags:
            results = [s for s in results if tag.lower() in [t.lower() for t in s.get("tags", [])]]

    if lang:
        results = [s for s in results if lang.lower() in [t.lower() for t in s.get("tags", [])]]

    if category:
        results = [s for s in results if s.get("category", "").lower() == category.lower()]

    if agent:
        results = [s for s in results if agent.lower() in [a.lower() for a in s.get("agents", [])]]

    return results


def print_skills(skills: list[dict], verbose: bool = False):
    """Tulostaa skillit taulukkomuodossa."""
    if not skills:
        print("Ei tuloksia.")
        return

    print(f"Löydetty {len(skills)} skill(iä):\n")

    for skill in skills:
        agents_str = ", ".join(skill.get("agents", []))
        version = skill.get("version", "?")
        skill_id = skill.get("id", "?")
        category = skill.get("category", "?")

        print(f"  {skill_id:<30} v{version:<10} [{agents_str}]")
        print(f"  {'':30} Kategoria: {category}")

        if skill.get("description"):
            desc = skill["description"].strip().replace("\n", " ")
            if len(desc) > 80:
                desc = desc[:77] + "..."
            print(f"  {'':30} {desc}")

        if verbose:
            tags = ", ".join(skill.get("tags", []))
            print(f"  {'':30} Tagit: {tags}")
            print(f"  {'':30} Polku: {skill.get('path', '?')}")

        print()


def cmd_search(args, registry_path: Path):
    """Hae skillejä."""
    registry = load_registry(registry_path)
    skills = registry["skills"]

    tags = args.tag if args.tag else []
    results = filter_skills(
        skills,
        tags=tags,
        lang=args.lang,
        category=args.category,
        agent=args.agent
    )

    print_skills(results, verbose=args.verbose)

    if results:
        print("Asenna skill:")
        for skill in results:
            print(f"  python tools/skill-search.py install {skill['id']} --agent claude-code")


def cmd_list(args, registry_path: Path):
    """Listaa kaikki skillit."""
    registry = load_registry(registry_path)
    print(f"Registry versio: {registry.get('version', '?')} (päivitetty: {registry.get('updated', '?')})")
    print()
    print_skills(registry["skills"], verbose=args.verbose)


def cmd_install(args, registry_path: Path):
    """Asenna skill (delegoi adapter-skriptille)."""
    skill_id = args.skill_id
    agent = args.agent or "claude-code"

    registry = load_registry(registry_path)
    skills = registry["skills"]

    # Tarkista että skill löytyy
    found = next((s for s in skills if s["id"] == skill_id), None)
    if not found:
        print(f"Virhe: Skilliä '{skill_id}' ei löydy registrystä.")
        print("\nSaatavilla olevat skillit:")
        for s in skills:
            print(f"  - {s['id']}")
        sys.exit(1)

    # Delegoi adapter-skriptille
    repo_root = registry_path.parent
    adapter_script = repo_root / "adapters" / agent / "install.sh"

    if not adapter_script.exists():
        print(f"Virhe: Adapteria '{agent}' ei löydy: {adapter_script}")
        print(f"Saatavilla olevat adapterit: claude-code, cursor, generic")
        sys.exit(1)

    print(f"Asennetaan '{skill_id}' agentille '{agent}'...")
    import subprocess
    result = subprocess.run(["bash", str(adapter_script), skill_id], check=False)
    sys.exit(result.returncode)


def main():
    # Etsi registry.yaml
    script_dir = Path(__file__).parent
    registry_path = script_dir.parent / "registry.yaml"
    if not registry_path.exists():
        registry_path = Path("registry.yaml")

    parser = argparse.ArgumentParser(
        description="Etsi ja asenna skillejä Agent Skills Registrystä",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--registry", default=str(registry_path), help="Registry.yaml-polku")
    parser.add_argument("--verbose", "-v", action="store_true", help="Näytä lisätietoja")

    subparsers = parser.add_subparsers(dest="command")

    # Haku (oletus-komento)
    search_parser = subparsers.add_parser("search", help="Hae skillejä")
    search_parser.add_argument("--tag", action="append", help="Suodata tagilla (voi toistaa)")
    search_parser.add_argument("--lang", help="Suodata kielellä (fi, en)")
    search_parser.add_argument("--category", help="Suodata kategorialla")
    search_parser.add_argument("--agent", help="Suodata agentilla")
    search_parser.add_argument("--verbose", "-v", action="store_true")

    # Lista
    list_parser = subparsers.add_parser("list", help="Listaa kaikki skillit")
    list_parser.add_argument("--verbose", "-v", action="store_true")

    # Asennus
    install_parser = subparsers.add_parser("install", help="Asenna skill")
    install_parser.add_argument("skill_id", help="Asennettavan skillin ID")
    install_parser.add_argument("--agent", default="claude-code", help="Kohdeagentti (oletus: claude-code)")

    # Tue myös vanhan tyylin argumentteja ilman alikomentoa
    parser.add_argument("--tag", action="append", help="Suodata tagilla")
    parser.add_argument("--lang", help="Suodata kielellä")
    parser.add_argument("--category", help="Suodata kategorialla")
    parser.add_argument("--agent", help="Suodata agentilla")
    parser.add_argument("--list", action="store_true", help="Listaa kaikki skillit")

    args = parser.parse_args()
    reg_path = Path(args.registry)

    # Käsittele komennot
    if args.command == "install":
        cmd_install(args, reg_path)
    elif args.command == "list" or getattr(args, "list", False):
        cmd_list(args, reg_path)
    elif args.command == "search" or any([
        getattr(args, "tag", None),
        getattr(args, "lang", None),
        getattr(args, "category", None),
        getattr(args, "agent", None),
    ]):
        cmd_search(args, reg_path)
    else:
        # Oletus: listaa kaikki
        cmd_list(args, reg_path)


if __name__ == "__main__":
    main()
