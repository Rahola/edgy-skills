#!/usr/bin/env bash
# examples-heuristic.sh — nimetön tietosuojamuistutus.
#
# Ei sisällä yhtään asiakasnimeä, joten se on turvallinen julkisissa
# CI-lokeissa. Tarkoitus: kun PR lisää tai muuttaa tiedostoja `examples/`-
# tai `generated/`-kansioissa, muistuta katsomaan ettei mukana ole oikeaa
# asiakasdataa. EI kaada buildia — pelkkä signaali reviewaajalle.
#
# Käyttö: bash tools/examples-heuristic.sh

set -u

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

# CI:ssä vertaa PR:n base-refiin; muuten vertaa työpuun muutoksiin.
BASE="${GITHUB_BASE_REF:-}"
if [ -n "$BASE" ] && git rev-parse "origin/$BASE" >/dev/null 2>&1; then
    CHANGED=$(git diff --name-only --diff-filter=ACM "origin/$BASE"...HEAD 2>/dev/null)
else
    CHANGED=$(git diff --name-only --diff-filter=ACM 2>/dev/null; git diff --cached --name-only --diff-filter=ACM 2>/dev/null)
fi

FLAGGED=$(printf '%s\n' "$CHANGED" | grep -E '/(examples|generated)/' | sort -u || true)

if [ -z "$FLAGGED" ]; then
    echo "[examples-heuristic] ei muutoksia examples/ tai generated/ -kansioissa."
    exit 0
fi

echo "::notice::Tietosuojamuistutus — tämä PR muuttaa esimerkki-/generoituja tiedostoja."
echo ""
echo "Tarkista käsin ettei seuraavissa ole OIKEAA asiakas-/toimeksiantodataa"
echo "(käytä fiktiivisiä esimerkkejä, esim. \"Acme Oy\"):"
echo ""
printf '%s\n' "$FLAGGED" | sed 's/^/  - /'
echo ""
echo "Tämä on muistutus, ei virhe — build ei kaadu tähän."
exit 0
