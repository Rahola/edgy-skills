#!/usr/bin/env python3
"""Adapter install contract (v2.5.0, sprint 25b; test plan G04 rows A1–A16, SEC01–SEC02).

Runs the four adapters (claude-code, generic, Vibe, Cursor) with --source=local and
synthetic registries (EDGY_SKILLS_REGISTRY=tools/fixtures/registries/*.yaml) into
temporary HOME / output directories:

- lookup-skill.py `requires`: install order, multi-hop, diamond, cycle, missing
  dependency, and ids rejected before any use (SEC01);
- dependency installs and the same-ref overwrite (sentinel);
- failures exit 1 with the skill named and no success line: a broken entry, an
  empty registry, an unreadable registry (a directory, so it fails for root too);
- SKILL.md-only installs (Vibe, Cursor, curl mode) refuse `install: directory`
  skills; --all skips them and names them;
- nothing is written outside the install root (SEC02).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "tools" / "fixtures" / "registries"
LOOKUP = REPO / "tools" / "lookup-skill.py"
ADAPTERS = REPO / "adapters"
SUCCESS = ("Asennus valmis", "Valmis!", "Use in Mistral Vibe CLI")


def run(cmd, registry=None, home=None, cwd=None, extra_env=None):
    env = {k: v for k, v in os.environ.items() if k not in ("EDGY_SKILLS_REGISTRY", "EDGY_NOTATION_PATH")}
    if registry is not None:
        env["EDGY_SKILLS_REGISTRY"] = str(registry)
    if home is not None:
        env["HOME"] = str(home)
    env.update(extra_env or {})
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd or REPO, timeout=120)
    return r.returncode, r.stdout + r.stderr


def lookup(*args):
    return run([sys.executable, str(LOOKUP), *args])


def listing(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*"))


def claude(args, registry, home, **kw):
    return run(["bash", str(ADAPTERS / "claude-code" / "install.sh"), "--source=local", *args], registry, home, **kw)


def generic(args, registry, home):
    return run(["bash", str(ADAPTERS / "generic" / "install.sh"), "--source=local", *args], registry, home)


def vibe(args, registry, home):
    return run(["bash", str(ADAPTERS / "mistral-vibe" / "install.sh"), "--source=local", *args], registry, home)


def cursor(args, registry, home):
    return run(["bash", str(ADAPTERS / "cursor" / "install.sh"), "--source=local", *args], registry, home, cwd=home)


def test_lookup_install_order():
    """A1–A5: transitive order, diamond once, cycle and missing dependency are errors."""
    rc, out = lookup("requires", "fx-plugin", str(REG / "deps.yaml"))
    assert rc == 0 and out.split() == ["fx-base", "fx-plugin"], out
    rc, out = lookup("requires", "fx-top", str(REG / "deps.yaml"))
    assert rc == 0 and out.split() == ["fx-base", "fx-mid", "fx-top"], out
    rc, out = lookup("requires", "fx-x", str(REG / "deps.yaml"))
    order = out.split()
    assert rc == 0 and order.count("fx-w") == 1 and order[-1] == "fx-x", out
    assert order.index("fx-w") < order.index("fx-y") and order.index("fx-w") < order.index("fx-z"), out
    rc, out = lookup("requires", "fx-x", str(REG / "cycle.yaml"))
    assert rc == 1 and "dependency cycle: fx-x → fx-y → fx-x" in out, out
    rc, out = lookup("requires", "fx-x", str(REG / "missing.yaml"))
    assert rc == 1 and "fx-x requires nope, which is not in the registry" in out, out
    # the real registry: every skill resolves
    for sid in lookup("list", str(REPO / "registry.yaml"))[1].split():
        rc, out = lookup("requires", sid, str(REPO / "registry.yaml"))
        assert rc == 0 and out.split()[-1] == sid, (sid, out)


def test_lookup_rejects_bad_ids_before_use():
    """SEC01: traversal, absolute paths and shell metacharacters are rejected; nothing runs."""
    with tempfile.TemporaryDirectory() as tmp:
        before = listing(tmp)
        for i in range(5):
            rc, out = run([sys.executable, str(LOOKUP), "requires", f"fx-sec{i}", str(REG / "sec.yaml")], cwd=tmp)
            assert rc == 1 and "invalid requires entry" in out, (i, out)
        for bad in ("../x", "/abs", "a;b", "$(id)", "UPPER"):
            rc, out = run([sys.executable, str(LOOKUP), "path", bad, str(REG / "deps.yaml")], cwd=tmp)
            assert rc == 1 and "invalid skill id" in out, (bad, out)
        assert listing(tmp) == before and not (Path(tmp) / "SENTINEL").exists()
    assert not (REPO / "SENTINEL").exists()


def test_claude_code_dependencies_and_overwrite():
    """A6, A9: the dependency is installed first; a reinstall overwrites from the same source and says so."""
    with tempfile.TemporaryDirectory() as home:
        rc, out = claude(["fx-plugin"], REG / "deps.yaml", home)
        skills = Path(home) / ".claude" / "skills"
        assert rc == 0, out
        assert sorted(p.name for p in skills.iterdir()) == ["fx-base", "fx-plugin"], out
        assert (skills / "fx-plugin" / "scripts" / "fx_plugin.py").is_file()
        assert (skills / "fx-plugin" / "notation.json").is_file()
        assert "fx-plugin requires fx-base" in out
        (skills / "fx-base" / "SKILL.md").write_text("SENTINEL-OLD", encoding="utf-8")
        rc, out = claude(["fx-plugin"], REG / "deps.yaml", home)
        assert rc == 0 and "overwriting fx-base from the local checkout" in out, out
        assert "SENTINEL-OLD" not in (skills / "fx-base" / "SKILL.md").read_text(encoding="utf-8")


def test_claude_code_failures():
    """A7, A8: a broken entry, an empty and an unreadable registry exit 1 without the success line."""
    with tempfile.TemporaryDirectory() as home:
        rc, out = claude(["--all"], REG / "broken.yaml", home)
        assert rc == 1 and "fx-broken" in out and not any(s in out for s in SUCCESS), out
        assert (Path(home) / ".claude" / "skills" / "fx-base").is_dir()
    for reg, needle in ((REG / "empty.yaml", "no skills listed"), (REG, "cannot read registry")):
        with tempfile.TemporaryDirectory() as home:
            rc, out = claude(["--all"], reg, home)
            assert rc == 1 and needle in out and not any(s in out for s in SUCCESS), (reg, out)
            skills = Path(home) / ".claude" / "skills"
            assert not skills.exists() or not any(skills.iterdir()), out


def test_generic_dependencies_and_failures():
    """A10, A11."""
    with tempfile.TemporaryDirectory() as tmp:
        outdir = Path(tmp) / "out"
        rc, out = generic(["--skill", "fx-plugin", "--output", str(outdir)], REG / "deps.yaml", tmp)
        assert rc == 0 and sorted(p.name for p in outdir.iterdir()) == ["fx-base", "fx-plugin"], out
        rc, out = generic(["--skill", "nope", "--output", str(outdir)], REG / "deps.yaml", tmp)
        assert rc == 1 and "nope" in out, out
        rc, out = generic(["--skill", "fx-broken", "--output", str(outdir)], REG / "broken.yaml", tmp)
        assert rc == 1 and "fx-broken" in out, out


def test_vibe_and_cursor_skillmd_only():
    """A12–A15: SKILL.md-only adapters skip / refuse install: directory skills; failures exit 1."""
    for name, fn, root in (("vibe", vibe, ".mistral-vibe/skills"), ("cursor", cursor, None)):
        with tempfile.TemporaryDirectory() as home:
            rc, out = fn(["--all"], REG / "deps.yaml", home)
            assert rc == 0, (name, out)
            assert "fx-plugin" in out and "needs the claude-code or generic install" in out, (name, out)
            if root:
                got = sorted(p.name for p in (Path(home) / root).iterdir())
                assert "fx-plugin" not in got and "fx-base" in got and len(got) == 7, (name, got)
                assert all(sorted(x.name for x in (Path(home) / root / d).iterdir()) == ["SKILL.md"] for d in got)
            else:
                rules = (Path(home) / ".cursorrules").read_text(encoding="utf-8")
                assert "# SKILL: fx-plugin" not in rules and "# SKILL: fx-base" in rules, rules[:300]
        with tempfile.TemporaryDirectory() as home:
            rc, out = fn(["fx-plugin"], REG / "deps.yaml", home)
            assert rc == 1 and "fx-plugin needs the claude-code or generic install" in out, (name, out)
            assert not any(s in out for s in SUCCESS), (name, out)
        for reg, needle in ((REG / "broken.yaml", "fx-broken"), (REG / "empty.yaml", "no skills listed"),
                            (REG, "cannot read registry")):
            with tempfile.TemporaryDirectory() as home:
                rc, out = fn(["--all"], reg, home)
                assert rc == 1 and needle in out and not any(s in out for s in SUCCESS), (name, reg, out)


def test_curl_mode_refuses_directory_skills():
    """A16: curl mode installs SKILL.md only, so an install: directory skill is refused before any download."""
    with tempfile.TemporaryDirectory() as home:
        rc, out = run(["bash", str(ADAPTERS / "claude-code" / "install.sh"), "--source=curl", "fx-plugin"],
                      REG / "deps.yaml", home)
        assert rc == 1 and "fx-plugin needs the claude-code or generic install" in out, out
        skills = Path(home) / ".claude" / "skills"
        assert not skills.exists() or not any(skills.iterdir())


def test_install_root_is_never_left():
    """SEC02: with hostile requires entries every adapter exits 1 and writes nothing outside its root."""
    with tempfile.TemporaryDirectory() as parent:
        home = Path(parent) / "home"
        home.mkdir()
        before = listing(parent)
        for fn, args in ((claude, ["fx-sec2"]), (vibe, ["fx-sec3"]), (cursor, ["fx-sec4"])):
            rc, out = fn(args, REG / "sec.yaml", home)
            assert rc == 1 and "invalid requires entry" in out, (fn.__name__, out)
        rc, out = generic(["--skill", "fx-sec0", "--output", str(home / "out")], REG / "sec.yaml", home)
        assert rc == 1 and "invalid requires entry" in out, out
        after = [p for p in listing(parent) if not p.startswith("home/")]
        assert after == [p for p in before if not p.startswith("home/")], after
        assert not any("SENTINEL" in p for p in listing(parent))
    assert not (REPO / "SENTINEL").exists()


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"{t.__name__} passed")
    print(f"\nAll {len(tests)} adapter install tests passed")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
