#!/usr/bin/env python3
"""
lookup-skill.py — Hae skillin tietoja registry.yaml:sta

Käyttö:
    python3 tools/lookup-skill.py path <skill-id> <registry.yaml>
    python3 tools/lookup-skill.py list <registry.yaml>
    python3 tools/lookup-skill.py list --verbose <registry.yaml>
    python3 tools/lookup-skill.py requires <skill-id> <registry.yaml>   # asennusjärjestys: riippuvuudet ensin
    python3 tools/lookup-skill.py agents <skill-id> <registry.yaml>     # tuetut agentit, yksi per rivi
    python3 tools/lookup-skill.py install <skill-id> <registry.yaml>    # install-kenttä (tyhjä = SKILL.md riittää)

Every skill id — the requested one and every `requires` entry — must match
^[a-z0-9][a-z0-9-]*$ and is checked before it is used anywhere (v2.5.0, SEC01).
An unreadable registry, an empty one, a missing dependency or a dependency
cycle exits 1 with a message; nothing is printed to stdout then, so an adapter
never acts on a partial answer.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def fail(msg):
    print(f"Virhe: {msg}", file=sys.stderr)
    sys.exit(1)


def load_registry(registry_file):
    """The registry as a dict; exits 1 when it cannot be read or parsed."""
    path = Path(registry_file)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        fail(f"cannot read registry {registry_file}: {e.__class__.__name__}")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        fail(f"cannot read registry {registry_file}: not valid YAML")
    return data if isinstance(data, dict) else {}


def skills(reg):
    out = [s for s in (reg.get("skills") or []) if isinstance(s, dict)]
    return out


def check_id(skill_id, context="skill id"):
    if not isinstance(skill_id, str) or not SKILL_ID.match(skill_id):
        fail(f"invalid {context} {skill_id!r} (allowed: ^[a-z0-9][a-z0-9-]*$)")


def entry(reg, skill_id):
    check_id(skill_id)
    for s in skills(reg):
        if s.get("id") == skill_id:
            return s
    return None


def cmd_path(skill_id, registry_file):
    reg = load_registry(registry_file)
    s = entry(reg, skill_id)
    if s is None:
        fail(f"skilliä '{skill_id}' ei löydy")
    if s.get("path") is None:
        fail(f"skillillä '{skill_id}' ei ole path-kenttää")
    print(s["path"])


def cmd_list(registry_file, verbose=False):
    reg = load_registry(registry_file)
    entries = skills(reg)
    if not entries:
        fail(f"no skills listed in {registry_file}")
    for s in entries:
        if verbose:
            version = s.get("version", "?")
            agents = ", ".join(s.get("agents", []))
            print(f"  {s.get('id', '?'):30} v{version:10} [{agents}]")
            print(f"    {s.get('description', '').strip()[:80]}")
        else:
            print(s.get("id", "?"))


def install_order(reg, skill_id):
    """Dependencies first (depth-first, each once), the skill last. Every id is validated before use."""
    order, state = [], {}

    def visit(sid, path):
        check_id(sid, "skill id" if not path else f"requires entry of {path[-1]}")
        if state.get(sid) == "done":
            return
        if state.get(sid) == "visiting":
            cycle = path[path.index(sid):] + [sid]
            fail("dependency cycle: " + " → ".join(cycle))
        s = entry(reg, sid)
        if s is None:
            if path:
                fail(f"{path[-1]} requires {sid}, which is not in the registry")
            fail(f"skilliä '{sid}' ei löydy")
        state[sid] = "visiting"
        req = s.get("requires") or []
        if not isinstance(req, list):
            fail(f"requires of {sid} must be a list")
        for r in req:
            visit(r, path + [sid])
        state[sid] = "done"
        order.append(sid)

    visit(skill_id, [])
    return order


def cmd_requires(skill_id, registry_file):
    reg = load_registry(registry_file)
    print("\n".join(install_order(reg, skill_id)))


def cmd_agents(skill_id, registry_file):
    reg = load_registry(registry_file)
    s = entry(reg, skill_id)
    if s is None:
        fail(f"skilliä '{skill_id}' ei löydy")
    for a in s.get("agents") or []:
        print(a)


def cmd_install(skill_id, registry_file):
    reg = load_registry(registry_file)
    s = entry(reg, skill_id)
    if s is None:
        fail(f"skilliä '{skill_id}' ei löydy")
    print(s.get("install") or "")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    command, rest = args[0], args[1:]
    if command == "list":
        verbose = "--verbose" in rest
        rest = [a for a in rest if a != "--verbose"]
        if len(rest) != 1:
            fail("käyttö: lookup-skill.py list [--verbose] <registry.yaml>")
        cmd_list(rest[0], verbose=verbose)
        return
    handlers = {"path": cmd_path, "requires": cmd_requires, "agents": cmd_agents, "install": cmd_install}
    if command not in handlers:
        print(f"Tuntematon komento: {command}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)
    if len(rest) != 2:
        fail(f"käyttö: lookup-skill.py {command} <skill-id> <registry.yaml>")
    handlers[command](rest[0], rest[1])


if __name__ == "__main__":
    main()
