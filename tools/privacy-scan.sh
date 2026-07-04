#!/usr/bin/env bash
# privacy-scan.sh — estää yksityisten asiakas-/toimeksiantoreferenssien vuodon
# julkiseen repoon.
#
# Tämä repo on JULKINEN. Skillit on johdettu yksityisestä upstream-repostosta,
# jossa on asiakaskohtaista materiaalia. Tämä skanneri on viimeinen verkko:
# se etsii ennalta määriteltyjä salaisia termejä (asiakasnimet yms.) ja
# blokkaa niiden päätymisen committiin.
#
# TÄRKEÄÄ: termilista EI ole tässä repossa — se paljastaisi juuri ne
# referenssit joita halutaan suojata. Tämä on PAIKALLINEN suoja: lista luetaan
#   1. Paikallisesta `.blocklist`-tiedostosta repon juuressa (gitignored — ei
#      koskaan committiin). Ensisijainen suoja ylläpitäjän omille committeille.
#   2. (valinnainen) $PRIVACY_BLOCKLIST-ympäristömuuttujasta, jos haluat ajaa
#      skannerin omassa putkessasi. EI oletuksena kytketty tämän repon CI:hin —
#      asiakaslistaa ei tallenneta pilveen. Rivi- tai pystyviiva-eroteltu.
#
# Jos kumpaakaan lähdettä ei ole → skanneri ohitetaan hiljaisesti (esim. CI,
# jossa .blocklist:ia ei ole; tietosuoja hoidetaan siellä nimettömällä
# examples-heuristic.sh-muistutuksella + manuaalisella reviewilla).
#
# Osuma tulostetaan muodossa `tiedosto:rivinumero` — ITSE TERMIÄ EI KOSKAAN
# tulosteta, jotta julkiset CI-lokit eivät vuoda listaa.
#
# Käyttö:
#   bash tools/privacy-scan.sh              # skannaa staged-tiedostot (tai skills/)
#   bash tools/privacy-scan.sh --all        # skannaa koko skills/-puu
#
# Exit: 0 = puhdas / ohitettu, 1 = osuma (blokkaa commit/CI).

set -u

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

MODE="staged"
[ "${1:-}" = "--all" ] && MODE="all"

# --- Kerää termit molemmista lähteistä --------------------------------------
PATTERNS=()

if [ -f "$REPO_ROOT/.blocklist" ]; then
    while IFS= read -r line; do
        line="${line%%#*}"                       # riisu kommentit
        line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -n "$line" ] && PATTERNS+=("$line")
    done < "$REPO_ROOT/.blocklist"
fi

if [ -n "${PRIVACY_BLOCKLIST:-}" ]; then
    # Salli sekä rivinvaihto- että pystyviiva-erotellut listat
    while IFS= read -r line; do
        line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -n "$line" ] && PATTERNS+=("$line")
    done < <(printf '%s' "$PRIVACY_BLOCKLIST" | tr '|' '\n')
fi

if [ "${#PATTERNS[@]}" -eq 0 ]; then
    echo "[privacy-scan] ei termilistaa (.blocklist puuttuu, PRIVACY_BLOCKLIST tyhjä) — ohitetaan." >&2
    exit 0
fi

# Rakenna yksi case-insensitive ERE-vaihtoehtolauseke
JOINED="$(printf '%s|' "${PATTERNS[@]}")"
JOINED="${JOINED%|}"

# --- Valitse skannattavat tiedostot -----------------------------------------
if [ "$MODE" = "all" ]; then
    # Kaikki trackatut tiedostot — grep -I ohittaa binäärit. Näin myös
    # CONTRIBUTING/NOTICE/tools/**/.github/** tulevat skannatuiksi, ei vain
    # skills/. (Aiemmin skooppi oli liian kapea.)
    mapfile -t FILES < <(git ls-files 2>/dev/null)
else
    mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)
    # Jos ei staged-tiedostoja (esim. suora ajo), skannaa koko puu
    [ "${#FILES[@]}" -eq 0 ] && mapfile -t FILES < <(git ls-files 2>/dev/null)
fi

HITS=0
for f in "${FILES[@]}"; do
    [ -f "$f" ] || continue
    # -I ohittaa binäärit; -n antaa rivinumeron; -o EI käytetä ettei termi vuoda
    while IFS=: read -r lineno _; do
        [ -n "$lineno" ] || continue
        echo "  ⛔ $f:$lineno — estetty termi havaittu (ks. .blocklist)"
        HITS=$((HITS + 1))
    done < <(grep -inIE "$JOINED" "$f" 2>/dev/null)
done

if [ "$HITS" -gt 0 ]; then
    echo "" >&2
    echo "[privacy-scan] $HITS osuma(a) — commit/CI estetty. Poista yksityinen referenssi." >&2
    echo "  (Itse termiä ei tulosteta tarkoituksella, jotta julkiset lokit eivät vuoda listaa.)" >&2
    exit 1
fi

exit 0
