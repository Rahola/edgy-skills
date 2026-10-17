# Jaetut riippuvuus- ja tukifunktiot edgy-skills-adaptereille (v2.5.0).
#
# Käyttö (kutsuvasta skriptistä, kun LOOKUP_TOOL on asetettu):
#
#   source "${ADAPTER_SCRIPT_DIR}/../_shared/deps.sh"
#   registry_file=$(deps_registry_override) || registry_file=$(…fetch…)
#   deps_list_or_fail "$registry_file"            # skill-id:t, tai virhe ja exit-koodi 1
#   deps_install_order <skill-id> "$registry_file" # riippuvuudet ensin, skill viimeisenä
#   deps_supports <skill-id> "$registry_file" <agent> <mode>
#
# EDGY_SKILLS_REGISTRY=<polku> korvaa registry.yaml:n (testit ja paikalliset
# rekisterit). Kaikki skill-id:t tarkistetaan lookup-skill.py:ssä ennen kuin
# niitä käytetään polkuna tai komennossa.

: "${LOOKUP_TOOL:?LOOKUP_TOOL must be set before sourcing _shared/deps.sh}"

# Tulosta korvaava registry-polku, jos EDGY_SKILLS_REGISTRY on asetettu (paluuarvo 1 muuten)
deps_registry_override() {
  if [[ -n "${EDGY_SKILLS_REGISTRY:-}" ]]; then
    echo "$EDGY_SKILLS_REGISTRY"
    return 0
  fi
  return 1
}

# Listaa skill-id:t; tyhjä tai lukukelvoton rekisteri on virhe (ei koskaan "valmis")
deps_list_or_fail() {
  local registry_file="$1" out
  if ! out=$(python3 "$LOOKUP_TOOL" list "$registry_file"); then
    return 1
  fi
  if [[ -z "${out//[[:space:]]/}" ]]; then
    echo "Virhe: no skills listed in ${registry_file}" >&2
    return 1
  fi
  printf '%s\n' "$out"
}

# Asennusjärjestys: riippuvuudet ensin (transitiivisesti), pyydetty skill viimeisenä
deps_install_order() {
  python3 "$LOOKUP_TOOL" requires "$1" "$2"
}

# Tukeeko skill tätä adapteria? Tulostaa syyn stderriin, jos ei.
#   $3 = adapterin agentti-id (claude-code | generic | vibe | cursor)
#   $4 = asennustapa: directory (koko hakemisto) | skillmd (vain SKILL.md: vibe, cursor, curl-tila)
deps_supports() {
  local skill_id="$1" registry_file="$2" agent="$3" mode="$4" agents install
  agents=$(python3 "$LOOKUP_TOOL" agents "$skill_id" "$registry_file") || return 1
  install=$(python3 "$LOOKUP_TOOL" install "$skill_id" "$registry_file") || return 1
  local supported_list
  supported_list=$(printf '%s\n' "$agents" | grep -E '^(claude-code|generic)$' | paste -sd '/' - | sed 's#/# or #g')
  if ! printf '%s\n' "$agents" | grep -qx "$agent"; then
    echo "${skill_id} needs the ${supported_list:-$(printf '%s' "$agents" | paste -sd '/' -)} install (not ${agent})" >&2
    return 1
  fi
  if [[ "$install" == "directory" && "$mode" == "skillmd" ]]; then
    echo "${skill_id} needs the ${supported_list:-claude-code or generic} install: it installs scripts, not only SKILL.md" >&2
    return 1
  fi
  return 0
}
