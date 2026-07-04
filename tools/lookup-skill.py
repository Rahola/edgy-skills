#!/usr/bin/env python3
"""
lookup-skill.py — Hae skillin tietoja registry.yaml:sta

Käyttö:
    python3 tools/lookup-skill.py path <skill-id> <registry.yaml>
    python3 tools/lookup-skill.py list <registry.yaml>
    python3 tools/lookup-skill.py list --verbose <registry.yaml>
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Lisää tools/-hakemisto sys.path:iin jotta skill_utils löytyy
sys.path.insert(0, str(Path(__file__).parent))
from skill_utils import load_registry as _load_registry_util


def load_registry(registry_file):
    return _load_registry_util(str(registry_file))


def cmd_path(skill_id, registry_file):
    """Tulosta skillin polku."""
    reg = load_registry(registry_file)
    for s in reg.get("skills", []):
        if s.get("id") == skill_id:
            path = s.get("path")
            if path is None:
                print(f"Virhe: skillillä '{skill_id}' ei ole path-kenttää", file=sys.stderr)
                sys.exit(1)
            print(path)
            sys.exit(0)
    print(f"Virhe: skilliä '{skill_id}' ei löydy", file=sys.stderr)
    sys.exit(1)


def cmd_list(registry_file, verbose=False):
    """Listaa kaikki skillit."""
    reg = load_registry(registry_file)
    for s in reg.get("skills", []):
        if verbose:
            version = s.get("version", "?")
            agents = ", ".join(s.get("agents", []))
            print(f"  {s.get('id', '?'):30} v{version:10} [{agents}]")
            print(f"    {s.get('description', '').strip()[:80]}")
        else:
            print(s.get("id", "?"))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "path":
        if len(sys.argv) != 4:
            print("Käyttö: lookup-skill.py path <skill-id> <registry.yaml>", file=sys.stderr)
            sys.exit(1)
        cmd_path(sys.argv[2], sys.argv[3])

    elif command == "list":
        verbose = "--verbose" in sys.argv
        args = [a for a in sys.argv[2:] if a != "--verbose"]
        if len(args) != 1:
            print("Käyttö: lookup-skill.py list [--verbose] <registry.yaml>", file=sys.stderr)
            sys.exit(1)
        cmd_list(args[0], verbose=verbose)

    else:
        print(f"Tuntematon komento: {command}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
