#!/usr/bin/env bash
# postedit-check.sh — Claude Code PostToolUse-hook.
#
# Ajetaan Edit|Write|MultiEdit-toimien jälkeen. Jos muokattu tiedosto on
# SKILL.md tai registry.yaml → ajaa nopea validointitarkistus ja palauttaa
# tuloksen additionalContext-kenttänä. EI keskeytä editiä — pelkkä signaali
# agentille että jokin on pielessä.
#
# Stdin: Claude Coden hook-JSON.
# Stdout: JSON {"hookSpecificOutput": {...}} jos relevantti, muuten tyhjä.

set -u

# jq tarvitaan hook-JSONin parsimiseen ja additionalContext-vastaukseen.
# Ilman sitä emme voi tarjota agentille palautetta — varoita stderr:n
# kautta ja jatka hiljaisesti.
if ! command -v jq >/dev/null 2>&1; then
    echo "[postedit-check] jq puuttuu — asenna 'apt install jq' tai 'brew install jq'. Hookki ohitettu." >&2
    exit 0
fi

INPUT="$(cat)"
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // ""')

# Vain SKILL.md tai registry.yaml laukaisevat tarkistuksen
case "$FILE_PATH" in
    */SKILL.md|registry.yaml|*/registry.yaml)
        ;;
    *)
        exit 0
        ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

# Aja --quick yhden tiedoston kohdalle. SKILL.md-tapauksessa kohde on
# tiedoston hakemisto; registry.yaml-tapauksessa skannataan kaikki skillit.
case "$FILE_PATH" in
    */SKILL.md)
        TARGET="$(dirname "$FILE_PATH")"
        OUTPUT=$(bash tools/check.sh --quick "$TARGET" 2>&1)
        ;;
    *)
        OUTPUT=$(bash tools/check.sh 2>&1)
        ;;
esac
RC=$?

# Onnistunut tarkistus → ei lisätä kontekstiin mitään (pidetään hiljaisena).
if [ $RC -eq 0 ]; then
    exit 0
fi

# Virhe tai varoitus → palautetaan additionalContext jotta agentti näkee
# tuloksen ja voi korjata ennen committia.
jq -n --arg ctx "$OUTPUT" '{
    hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: ("Skill-validointi varoitti muokatusta tiedostosta:\n" + $ctx)
    }
}'
exit 0
