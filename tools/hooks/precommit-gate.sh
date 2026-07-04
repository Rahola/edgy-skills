#!/usr/bin/env bash
# precommit-gate.sh — Claude Code PreToolUse-hook Bash-tooleille.
#
# Ennen kuin agentti ajaa `git commit`-bashia, ajetaan tools/check.sh.
# Jos validointi epäonnistuu → blokataan tool-call permissionDecision:llä
# "deny" ja annetaan agentille selkeä virheviesti reason-kentässä.
#
# Ohitukset:
#   - Komennossa "--no-verify" → sallitaan (matchaa native git-konvention)
#   - Ympäristössä SKIP_CHECK=1 → sallitaan
#
# Stdin: Claude Coden hook-JSON.
# Stdout: tyhjä (sallitaan) tai JSON {"hookSpecificOutput": {...}} (blokataan).

set -u

# jq tarvitaan hook-JSONin parsimiseen ja vastauksen generointiin. Jos se
# puuttuu, ei pystytä tuottamaan strukturoitua deny-vastausta — varoita
# käyttäjää stderr:n kautta ja salli komennon ajo (parempi vaihtoehto kuin
# blokata kaikki bash-komennot ympäristöasetuksen takia).
if ! command -v jq >/dev/null 2>&1; then
    echo "[precommit-gate] jq puuttuu — asenna 'apt install jq' tai 'brew install jq'. Hookki ohitettu." >&2
    exit 0
fi

INPUT="$(cat)"
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')

# Vain git commit -komennot kiinnostavat. PreToolUse Bash näkee kaiken
# bashin, joten tähden suodatuksen pitää tapahtua täällä.
case "$COMMAND" in
    *"git commit"*)
        ;;
    *)
        exit 0
        ;;
esac

# Ohitukset
case "$COMMAND" in
    *"--no-verify"*)
        exit 0
        ;;
esac
if [ "${SKIP_CHECK:-0}" = "1" ]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

OUTPUT=$(bash tools/check.sh 2>&1)
RC=$?

if [ $RC -eq 0 ]; then
    exit 0
fi

# Exit-koodi 2 = ympäristövaroitus (esim. pyyaml puuttuu). Älä blokkaa
# committia — kirjoita varoitus stderr:ään ja anna ajon jatkua.
if [ $RC -eq 2 ]; then
    echo "[precommit-gate] check.sh palautti varoituksen (exit 2):" >&2
    printf '%s\n' "$OUTPUT" >&2
    exit 0
fi

# Blokataan commit ja kerrotaan agentille mitä korjata.
REASON="Skill-validointi epäonnistui — commit estetty. Korjaa virheet ja yritä uudelleen.

$OUTPUT

Ohitus tarvittaessa: lisää 'git commit --no-verify' tai aja 'SKIP_CHECK=1 git commit ...'."

jq -n --arg reason "$REASON" '{
    hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
    }
}'
exit 0
