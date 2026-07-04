#!/usr/bin/env python3
"""
skill-validator.py — Validoi SKILL.md-tiedostojen rakenne

Käyttö:
    python tools/skill-validator.py skills/
    python tools/skill-validator.py skills/documentation/meeting-minutes/
    python tools/skill-validator.py skills/documentation/meeting-minutes/SKILL.md
"""

import sys
import os
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Virhe: pyyaml ei ole asennettu. Aja: pip install pyyaml")
    sys.exit(1)

# Lisää tools/-hakemisto sys.path:iin jotta skill_utils löytyy
sys.path.insert(0, str(Path(__file__).parent))
from skill_utils import parse_frontmatter

REQUIRED_FIELDS = ["name", "version", "description", "category", "tags", "agents"]
VALID_CATEGORIES = ["coding", "architecture", "security", "documentation", "productivity"]
VALID_AGENTS = ["claude-code", "cursor", "mistral-vibe", "vibe", "generic", "github-coding-agent"]
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class ValidationError:
    def __init__(self, file_path: str, message: str, severity: str = "error"):
        self.file_path = file_path
        self.message = message
        self.severity = severity  # "error" tai "warning"

    def __str__(self):
        icon = "✗" if self.severity == "error" else "⚠"
        return f"  {icon} [{self.severity.upper()}] {self.message}"


def parse_skill_md(file_path: Path) -> tuple[dict | None, str | None]:
    """Parsii SKILL.md-tiedoston, palauttaa (frontmatter_dict, markdown_body)."""
    content = file_path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def validate_skill_file(file_path: Path) -> list[ValidationError]:
    """Validoi yksittäinen SKILL.md-tiedosto, palauttaa listan virheistä."""
    errors = []
    path_str = str(file_path)

    if not file_path.exists():
        errors.append(ValidationError(path_str, f"Tiedostoa ei löydy: {file_path}"))
        return errors

    frontmatter, body = parse_skill_md(file_path)

    if frontmatter is None:
        errors.append(ValidationError(
            path_str,
            "YAML frontmatter puuttuu tai on virheellinen. Tiedoston pitää alkaa '---'."
        ))
        return errors

    if not isinstance(frontmatter, dict):
        errors.append(ValidationError(path_str, "YAML frontmatter ei ole avain-arvo-rakenne."))
        return errors

    # Tarkista pakolliset kentät
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(ValidationError(path_str, f"Pakollinen kenttä puuttuu: '{field}'"))
        elif frontmatter[field] is None:
            errors.append(ValidationError(path_str, f"Pakollinen kenttä on tyhjä: '{field}'"))

    # Tarkista versio
    if "version" in frontmatter and frontmatter["version"] is not None:
        version = str(frontmatter["version"])
        if not VERSION_PATTERN.match(version):
            errors.append(ValidationError(
                path_str,
                f"Versio '{version}' ei ole semanttisessa muodossa (major.minor.patch). "
                f"Esim: '1.0.0'"
            ))

    # Tarkista kategoria
    if "category" in frontmatter and frontmatter["category"] is not None:
        cat = frontmatter["category"]
        if cat not in VALID_CATEGORIES:
            errors.append(ValidationError(
                path_str,
                f"Tuntematon kategoria: '{cat}'. Sallitut: {VALID_CATEGORIES}"
            ))

    # Tarkista agents-kenttä
    if "agents" in frontmatter and frontmatter["agents"] is not None:
        agents = frontmatter["agents"]
        if not isinstance(agents, list):
            errors.append(ValidationError(path_str, "'agents' pitää olla lista."))
        elif len(agents) == 0:
            errors.append(ValidationError(path_str, "'agents' lista on tyhjä — lisää vähintään yksi agentti."))
        else:
            for agent in agents:
                if agent not in VALID_AGENTS:
                    errors.append(ValidationError(
                        path_str,
                        f"Tuntematon agentti: '{agent}'. Sallitut: {VALID_AGENTS}",
                        severity="warning"
                    ))

    # Tarkista tags-kenttä
    if "tags" in frontmatter and frontmatter["tags"] is not None:
        tags = frontmatter["tags"]
        if not isinstance(tags, list):
            errors.append(ValidationError(path_str, "'tags' pitää olla lista."))
        elif len(tags) == 0:
            errors.append(ValidationError(
                path_str, "'tags' lista on tyhjä — lisää vähintään yksi tagi.", severity="warning"
            ))

    # Tarkista name vastaa hakemiston nimeä
    if "name" in frontmatter and frontmatter["name"] is not None:
        expected_name = file_path.parent.name
        actual_name = frontmatter["name"]
        if actual_name != expected_name:
            errors.append(ValidationError(
                path_str,
                f"'name' ('{actual_name}') ei vastaa hakemiston nimeä ('{expected_name}')",
                severity="warning"
            ))

    # Tarkista markdown-runko
    if not body:
        errors.append(ValidationError(
            path_str, "Markdown-runko YAML frontmatterin jälkeen on tyhjä.", severity="warning"
        ))
    else:
        # Tarkista että tärkeimmät osiot löytyvät — hyväksy minkä tahansa listatun
        # kielen otsikkosetti (monikielisten skillien tukemiseksi)
        languages = frontmatter.get("languages", ["fi"])
        if not isinstance(languages, list) or not languages:
            languages = ["fi"]

        expected_sections = {
            "fi": ["## Käyttötarkoitus", "## Ohjeet agentille"],
            "en": ["## Purpose", "## Agent Instructions"],
        }

        body_lower = body.lower()

        def _has_all(sections):
            return all(s.lower() in body_lower for s in sections)

        # Hyväksy jos minkä tahansa listatun kielen otsikot löytyvät kokonaisuudessaan
        matched_lang = next(
            (lang for lang in languages
             if lang in expected_sections and _has_all(expected_sections[lang])),
            None,
        )

        if matched_lang is None:
            # Raportoi puuttuvat primaarikielen mukaan
            primary_lang = languages[0]
            sections_to_check = expected_sections.get(primary_lang, expected_sections["fi"])
            for section in sections_to_check:
                if section.lower() not in body_lower:
                    errors.append(ValidationError(
                        path_str,
                        f"Suositeltu osio puuttuu: '{section}'",
                        severity="warning"
                    ))

    return errors


def find_skill_files(path: Path) -> list[Path]:
    """Etsii kaikki SKILL.md-tiedostot annetusta polusta."""
    if path.is_file() and path.name == "SKILL.md":
        return [path]
    elif path.is_dir():
        return sorted(path.rglob("SKILL.md"))
    else:
        return []


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = Path(sys.argv[1])
    skill_files = find_skill_files(target)

    if not skill_files:
        print(f"Yhtään SKILL.md-tiedostoa ei löydy: {target}")
        sys.exit(1)

    total_errors = 0
    total_warnings = 0
    failed_files = []

    print(f"Validoidaan {len(skill_files)} SKILL.md-tiedosto(a)...\n")

    for skill_file in skill_files:
        errors = validate_skill_file(skill_file)
        file_errors = [e for e in errors if e.severity == "error"]
        file_warnings = [e for e in errors if e.severity == "warning"]

        if errors:
            status = "✗ VIRHE" if file_errors else "⚠ VAROITUS"
            print(f"{status}: {skill_file}")
            for error in errors:
                print(str(error))
            print()

            total_errors += len(file_errors)
            total_warnings += len(file_warnings)
            if file_errors:
                failed_files.append(skill_file)
        else:
            print(f"✓ OK: {skill_file}")

    print()
    print("=" * 60)
    print(f"Tarkistettu: {len(skill_files)} tiedostoa")
    print(f"Virheitä:    {total_errors}")
    print(f"Varoituksia: {total_warnings}")

    if failed_files:
        print(f"\nEpäonnistuneet tiedostot ({len(failed_files)}):")
        for f in failed_files:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n✓ Kaikki validoinnit läpi!")
        sys.exit(0)


if __name__ == "__main__":
    main()
