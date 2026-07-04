#!/usr/bin/env bash
# agent-log-reminder.sh — Claude Code Stop-hook.
#
# Kun Claude lopettaa vastaamisen, tarkistetaan onko skills/** tai
# registry.yaml muuttunut session aikana ilman AGENT_LOG.md-päivitystä.
# Jos muutos puuttuu lokista → pehmeä muistutus (decision: block).
# Käyttäjä voi sallia jatkamisen — tämä on signaali, ei lopullinen kielto.
#
# Stdin: Claude Coden hook-JSON (käytännössä tyhjä payload).
# Stdout: tyhjä tai JSON {"decision": "block", "reason": "..."}.

set -u

# jq tarvitaan decision-vastauksen generointiin. Ilman sitä ohitetaan
# muistutus hiljaisesti — viestin stderr:ään näkee käyttäjä, mutta agentti
# ei jää roikkumaan rikkoutuneeseen JSON-outputiin.
if ! command -v jq >/dev/null 2>&1; then
    echo "[agent-log-reminder] jq puuttuu — asenna 'apt install jq' tai 'brew install jq'. Hookki ohitettu." >&2
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] && exit 0
cd "$REPO_ROOT"

# Onko skill- tai registry-muutoksia (staged/unstaged)?
SKILL_CHANGES=$(git status --porcelain skills/ registry.yaml 2>/dev/null | grep -v '^$' || true)
[ -z "$SKILL_CHANGES" ] && exit 0

# Onko AGENT_LOG.md mukana muutosjoukossa?
LOG_CHANGED=$(git status --porcelain AGENT_LOG.md 2>/dev/null | grep -v '^$' || true)
[ -n "$LOG_CHANGED" ] && exit 0

# Muutoksia skillsissä mutta lokia ei päivitetty → muistuta
REASON="Skill-muutoksia havaittu (skills/ tai registry.yaml) mutta AGENT_LOG.md ei ole päivitetty tässä sessiossa.

Konventio (CONTRIBUTING.md#agenttiloki): lisää lyhyt merkintä AGENT_LOG.md:hen, joka kuvaa mitä tehtiin ja miksi. Git-historia ei riitä — loki dokumentoi *päätökset*, ei vain *muutoksia*.

Muutoksessa olevat tiedostot:
$SKILL_CHANGES

Jatka päivittämällä AGENT_LOG.md ennen committia."

jq -n --arg reason "$REASON" '{
    decision: "block",
    reason: $reason
}'
exit 0
