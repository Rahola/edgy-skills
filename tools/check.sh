#!/usr/bin/env bash
# check.sh — yhteinen validointi-entry-point edgy-skills-repolle.
#
# Sama skripti, jota ajavat: CI (.github/workflows/validate-skills.yml),
# Claude Code -hookit (.claude/settings.json), git pre-commit (asennetaan
# tools/install-git-hooks.sh:lla) ja manuaalinen kontribuoija.
#
# Vaiheet: validator, registry-sync, examples-refs, core-links-sync,
# edgy-tests, edgy-geometry-tests, edgy-lint-tests, edgy-render-tests,
# edgy-structure-tests, edgy-tool-tests, edgy-model, edgy-eval, edgy-lint,
# privacy-scan.
#
# Käyttö:
#   bash tools/check.sh                          # täysi tarkistus
#   bash tools/check.sh --quick <polku>          # rajaa validator yhteen polkuun
#   bash tools/check.sh --no-registry            # ohita registry-sync
#   bash tools/check.sh --verbose                # täysi alavaiheiden output
#
# Exit-koodit:
#   0  kaikki tarkistukset OK
#   1  virhe — CI/pre-commit pitää blokata
#   2  ympäristövaroitus (esim. pyyaml puuttuu) — Claude Code -hookit eivät
#      blokkaa committia tähän, CI sen sijaan failaa (CI omistaa ympäristönsä
#      ja pyyamlin pitää olla asennettuna)

set -u

# Siirry repon juureen jos ollaan jossain alihakemistossa
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$REPO_ROOT"

MODE="full"
TARGET="skills/"
SKIP_REGISTRY=0
VERBOSE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --quick)
            MODE="quick"
            shift
            if [ $# -gt 0 ] && [ "${1:0:2}" != "--" ]; then
                TARGET="$1"
                shift
            fi
            ;;
        --no-registry)
            SKIP_REGISTRY=1
            shift
            ;;
        --verbose)
            VERBOSE=1
            shift
            ;;
        --help|-h)
            sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "check.sh: tuntematon argumentti: $1" >&2
            exit 1
            ;;
    esac
done

START_TS=$(date +%s)
EXIT_CODE=0
WARN=0

log_ok()    { printf '[check.sh] %-15s OK%s\n' "$1" "${2:+   ($2)}"; }
log_fail()  { printf '[check.sh] %-15s FAIL\n' "$1"; }
log_warn()  { printf '[check.sh] %-15s WARN  %s\n' "$1" "$2"; }

run_step() {
    # run_step <nimi> <komento...>
    local name="$1"; shift
    local out
    if [ "$VERBOSE" -eq 1 ]; then
        "$@"
        local rc=$?
    else
        out=$("$@" 2>&1)
        local rc=$?
    fi
    if [ $rc -eq 0 ]; then
        log_ok "$name"
    else
        log_fail "$name"
        if [ "$VERBOSE" -eq 0 ]; then
            printf '%s\n' "$out" >&2
        fi
        EXIT_CODE=1
    fi
    return $rc
}

# --- Vaihe 0: riippuvuustarkistus -------------------------------------------
if ! python3 -c "import yaml" 2>/dev/null; then
    log_warn "deps" "pyyaml puuttuu — aja: pip3 install pyyaml"
    exit 2
fi

# --- Vaihe 1: SKILL.md-validointi -------------------------------------------
if [ "$MODE" = "quick" ]; then
    run_step "validator" python3 tools/skill-validator.py "$TARGET"
else
    run_step "validator" python3 tools/skill-validator.py skills/
fi

# --- Vaihe 2: registry-sync-diff --------------------------------------------
if [ "$SKIP_REGISTRY" -eq 0 ]; then
    REG_TMP=$(mktemp)
    trap 'rm -f "$REG_TMP"' EXIT
    cp registry.yaml "$REG_TMP"
    if ! UPDATER_OUT=$(python3 tools/registry-updater.py 2>&1); then
        # Palauta alkuperäinen registry.yaml — updater on saattanut kirjoittaa
        # osittaisen tilan ennen kaatumistaan
        cp "$REG_TMP" registry.yaml
        log_fail "registry-sync"
        printf '%s\n' "$UPDATER_OUT" >&2
        EXIT_CODE=1
    else
        if python3 - "$REG_TMP" "registry.yaml" <<'PY' 2>/dev/null
import sys, yaml

def load_normalized(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if isinstance(data, dict):
        data = dict(data)
        data.pop("version", None)
        data.pop("updated", None)
    return data

before = load_normalized(sys.argv[1])
after = load_normalized(sys.argv[2])
sys.exit(0 if before == after else 1)
PY
        then
            # Palauta alkuperäinen registry.yaml — updaterin "updated"-kenttä
            # ja id-järjestys voivat muuttua ilman semanttista eroa
            cp "$REG_TMP" registry.yaml
            log_ok "registry-sync"
        else
            # Palauta alkuperäinen myös virhetilassa — käyttäjä ajaa
            # updaterin itse ja committaa muutoksen
            cp "$REG_TMP" registry.yaml
            log_fail "registry-sync"
            echo "  registry.yaml ei ole ajan tasalla." >&2
            echo "  Aja: python3 tools/registry-updater.py" >&2
            echo "  ja committaa muutos." >&2
            EXIT_CODE=1
        fi
    fi
fi

# --- Vaihe 3: examples-viittausten tarkistus --------------------------------
check_examples() {
    local missing=0
    local skill_dir skill_md example_ref example_path
    while IFS= read -r skill_dir; do
        skill_md="$skill_dir/SKILL.md"
        grep -q "examples/" "$skill_md" 2>/dev/null || continue
        while IFS= read -r example_ref; do
            example_path="$skill_dir/$example_ref"
            if [[ "$example_ref" == */ ]]; then
                [ -d "$example_path" ] || {
                    echo "  ⚠ Puuttuva esimerkkihakemisto: $example_path (viitattu $skill_md)"
                    missing=$((missing + 1))
                }
            elif [[ "$example_ref" == *"*"* ]]; then
                compgen -G "$example_path" > /dev/null || {
                    echo "  ⚠ Glob-pattern ei matsaa mitään: $example_path (viitattu $skill_md)"
                    missing=$((missing + 1))
                }
            else
                [ -f "$example_path" ] || {
                    echo "  ⚠ Puuttuva esimerkkitiedosto: $example_path (viitattu $skill_md)"
                    missing=$((missing + 1))
                }
            fi
        done < <(grep -oE 'examples/[^[:space:]`"]+' "$skill_md" | sort -u)
    done < <(find skills -name "SKILL.md" -exec dirname {} \;)
    return $missing
}

if examples_out=$(check_examples 2>&1); then
    log_ok "examples-refs"
else
    log_fail "examples-refs"
    printf '%s\n' "$examples_out" >&2
    EXIT_CODE=1
fi

# --- Vaihe 3b: EDGY-sanaston synkronointi ----------------------------------
# skills/_shared/edgy-core-links.yaml on ainoa lähde; SKILL.md-taulukot ja
# edgy_core_links.py generoidaan siitä. Vanhentunut kopio = FAIL.
run_step "core-links-sync" python3 tools/render-core-links.py --check

# --- Vaihe 3c: EDGY-parserin ja -lintin testit -------------------------------
EDGY_SCRIPTS="skills/documentation/edgy-diagram/scripts"
run_step "edgy-tests" python3 "$EDGY_SCRIPTS/test_edgy.py"
run_step "edgy-geometry-tests" python3 "$EDGY_SCRIPTS/test_geometry.py"
run_step "edgy-lint-tests" python3 "$EDGY_SCRIPTS/test_lint.py"
run_step "edgy-render-tests" python3 "$EDGY_SCRIPTS/test_render.py"
run_step "edgy-structure-tests" python3 "$EDGY_SCRIPTS/test_structure.py"
run_step "edgy-tool-tests" python3 tools/test_edgy_tools.py
run_step "edgy-model-tests" python3 skills/architecture/edgy-assessment/scripts/test_model_to_txt.py

# --- Vaihe 3c2: edgy-model.json-skeema + malli → TXT ------------------------
# Jokaisen repoon kuuluvan *model*.json-esimerkin on vastattava skeemaa, ja
# edgy_model_to_txt.py:n on tuotettava siitä parserille kelpaavat syötteet.
edgy_model_checks() {
    local models=()
    while IFS= read -r f; do models+=("$f"); done < <(
        find skills -path '*/examples/*' -name '*model*.json' | sort)
    [ ${#models[@]} -gt 0 ] || return 0
    python3 tools/validate-edgy-model.py "${models[@]}" || return 1
    local tmp
    tmp=$(mktemp -d)
    for m in "${models[@]}"; do
        python3 skills/architecture/edgy-assessment/scripts/edgy_model_to_txt.py "$m" --out "$tmp" --prefix model >/dev/null || { rm -rf "$tmp"; return 1; }
        for t in "$tmp"/model-*.txt; do
            python3 "$EDGY_SCRIPTS/edgy_generator.py" "$t" --output "$tmp/$(basename "$t" .txt).drawio" >/dev/null 2>"$tmp/warn.log" || { cat "$tmp/warn.log"; rm -rf "$tmp"; return 1; }
        done
        python3 "$EDGY_SCRIPTS/edgy_lint.py" -q "$tmp"/model-*.drawio || { rm -rf "$tmp"; return 1; }
    done
    rm -rf "$tmp"
}
run_step "edgy-model" edgy_model_checks

# --- Vaihe 3c3: eval-setti (isot fiktiiviset syötteet) -----------------------
run_step "edgy-eval" python3 tools/edgy-eval.py

# --- Vaihe 3d: EDGY-esimerkkikaavioiden lint --------------------------------
# Jokaisen skillin mukana toimitettavan .drawio-esimerkin on oltava lint-puhdas
# (0 virhettä; varoitukset sallitaan). Tämä on sama tarkistus, jonka agentti
# ajaa omalle tuotokselleen ennen toimitusta.
edgy_lint_examples() {
    local files=()
    while IFS= read -r f; do files+=("$f"); done < <(
        find skills -path '*/examples/*' \( -name '*.drawio' -o -name '*.drawio.xml' \) \
            -not -path '*/examples/official/*' | sort)
    [ ${#files[@]} -gt 0 ] || return 0
    python3 "$EDGY_SCRIPTS/edgy_lint.py" -q "${files[@]}"
}
run_step "edgy-lint" edgy_lint_examples

# --- Vaihe 3e: strict-portti visuaalisesti puhtaille asetteluille ------------
# Triad- ja purpose-esimerkit sekä fixtuurit F1 ja F5 on luvattu puhtaiksi myös
# visuaalisista säännöistä (W111–W114): --warnings-as-errors on tässä se portti.
edgy_lint_strict() {
    local ex="skills/documentation/edgy-diagram/examples"
    local tmp
    tmp=$(mktemp -d)
    for f in fixture-f1-ports-waypoints fixture-f5-purpose-tree; do
        python3 "$EDGY_SCRIPTS/edgy_generator.py" "$ex/eval/$f.txt" --output "$tmp/$f.drawio" >/dev/null 2>&1 || { rm -rf "$tmp"; return 1; }
    done
    python3 "$EDGY_SCRIPTS/edgy_lint.py" -q --warnings-as-errors \
        "$ex"/expected-triad-*.drawio "$ex"/expected-purpose.drawio "$ex"/expected-purpose-hierarchy.drawio "$tmp"/*.drawio
    local rc=$?
    rm -rf "$tmp"
    return $rc
}
run_step "edgy-lint-strict" edgy_lint_strict

# --- Vaihe 4: privacy-scan (asiakasreferenssien vuototarkistus) --------------
# Estää yksityisten asiakas-/toimeksiantonimien päätymisen julkiseen repoon.
# Paikallinen suoja: termilista gitignored .blocklist-tiedostosta (ei repossa).
# Ilman listaa step ohitetaan (exit 0), joten se ei riko kontribuoijia joilla
# ei ole listaa — eikä CI:tä (jossa .blocklist:ia ei ole).
run_step "privacy-scan" bash tools/privacy-scan.sh --all

# --- Yhteenveto -------------------------------------------------------------
ELAPSED=$(( $(date +%s) - START_TS ))
if [ $EXIT_CODE -eq 0 ] && [ $WARN -eq 0 ]; then
    echo "✓ kaikki tarkistukset läpi (${ELAPSED}s)"
fi
exit $EXIT_CODE
