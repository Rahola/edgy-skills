# Jaettu lähde-strategia edgy-skills-adaptereille.
#
# Käyttö (kutsuvasta skriptistä):
#
#   ADAPTER_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "${ADAPTER_SCRIPT_DIR}/../_shared/source.sh"
#
#   source_detect                                    # asettaa SOURCE_MODE
#   registry_file=$(source_fetch_registry)           # palauttaa registry-tiedoston polun
#   source_fetch_file <path-in-repo>                 # tulostaa tiedoston stdoutiin
#   source_fetch_skill_dir <skill_path> <target_dir> # kopioi koko skill-hakemiston
#
# Lähde-prioriteetti (auto-detect):
#   1) local — kutsuva skripti on repon sisällä (registry.yaml löytyy)
#   2) gh    — gh CLI autentikoitu (toimii private/public)
#   3) curl  — fallback (vain public)
#
# Pakota: aseta SOURCE_MODE=local|gh|curl ennen funktiokutsuja.
#
# Versio: EDGY_SKILLS_REF=<tagi|haara|commit> (oletus main), esim.
#   EDGY_SKILLS_REF=v1.0.0 bash install.sh edgy-diagram
# Koskee gh- ja curl-lähdettä. local-lähde käyttää repon nykyistä checkoutia
# (git checkout v1.0.0 ensin). Vanha nimi REGISTRY_BRANCH toimii yhä.
# Repo: EDGY_SKILLS_REPO=<owner/repo> (oletus Rahola/edgy-skills), vanha nimi REGISTRY_REPO.

REGISTRY_REPO="${EDGY_SKILLS_REPO:-${REGISTRY_REPO:-Rahola/edgy-skills}}"
REGISTRY_BRANCH="${EDGY_SKILLS_REF:-${REGISTRY_BRANCH:-main}}"
REGISTRY_BASE_URL="${REGISTRY_BASE_URL:-https://raw.githubusercontent.com/${REGISTRY_REPO}/${REGISTRY_BRANCH}}"

# Kutsuva skripti asettaa ADAPTER_SCRIPT_DIR ennen sourcea
: "${ADAPTER_SCRIPT_DIR:?ADAPTER_SCRIPT_DIR must be set before sourcing _shared/source.sh}"
LOCAL_REPO_ROOT="$(cd "${ADAPTER_SCRIPT_DIR}/../.." && pwd)"
LOOKUP_TOOL="${ADAPTER_SCRIPT_DIR}/../../tools/lookup-skill.py"

SOURCE_MODE="${SOURCE_MODE:-}"

# Värit, jos kutsuja ei niitä määrittänyt
: "${RED:=$'\033[0;31m'}"
: "${GREEN:=$'\033[0;32m'}"
: "${YELLOW:=$'\033[1;33m'}"
: "${NC:=$'\033[0m'}"

_SHARED_TMPFILES=()
_shared_cleanup() {
  for f in "${_SHARED_TMPFILES[@]:-}"; do
    [[ -n "$f" && -e "$f" ]] && rm -f "$f"
  done
  return 0
}
trap _shared_cleanup EXIT

_shared_tmp() {
  local f
  f="$(mktemp /tmp/edgy-skills.XXXXXX)"
  _SHARED_TMPFILES+=("$f")
  echo "$f"
}

source_detect() {
  if [[ -n "$SOURCE_MODE" ]]; then
    case "$SOURCE_MODE" in
      local|gh|curl) ;;
      *) echo "${RED}✗${NC} Tuntematon SOURCE_MODE: $SOURCE_MODE (sallitut: local, gh, curl)" >&2; exit 1 ;;
    esac
    return
  fi

  if [[ -f "${LOCAL_REPO_ROOT}/registry.yaml" ]]; then
    SOURCE_MODE="local"
    return
  fi

  if command -v gh &>/dev/null && gh auth status &>/dev/null; then
    SOURCE_MODE="gh"
    return
  fi

  if command -v curl &>/dev/null; then
    SOURCE_MODE="curl"
    return
  fi

  echo "${RED}✗${NC} Ei sopivaa lähdettä: ei paikallista repoa, gh ei autentikoitu, curl puuttuu." >&2
  exit 1
}

source_fetch_registry() {
  source_detect
  case "$SOURCE_MODE" in
    local)
      echo "${LOCAL_REPO_ROOT}/registry.yaml"
      ;;
    gh)
      local tmp; tmp="$(_shared_tmp)"
      if ! gh api "repos/${REGISTRY_REPO}/contents/registry.yaml?ref=${REGISTRY_BRANCH}" \
             -H "Accept: application/vnd.github.raw" > "$tmp" 2>/dev/null; then
        echo "${RED}✗${NC} registry.yaml:n haku epäonnistui (gh)." >&2
        return 1
      fi
      echo "$tmp"
      ;;
    curl)
      local tmp; tmp="$(_shared_tmp)"
      if ! curl -sfL "${REGISTRY_BASE_URL}/registry.yaml" -o "$tmp"; then
        echo "${RED}✗${NC} registry.yaml:n haku epäonnistui (curl). Repo voi olla private — käytä SOURCE_MODE=gh." >&2
        return 1
      fi
      echo "$tmp"
      ;;
  esac
}

# Tulosta yksittäisen tiedoston sisältö stdoutiin
# Käyttö: source_fetch_file <rel-path-from-repo-root>
source_fetch_file() {
  local rel_path="$1"
  source_detect
  case "$SOURCE_MODE" in
    local)
      cat "${LOCAL_REPO_ROOT}/${rel_path}"
      ;;
    gh)
      gh api "repos/${REGISTRY_REPO}/contents/${rel_path}?ref=${REGISTRY_BRANCH}" \
        -H "Accept: application/vnd.github.raw" 2>/dev/null
      ;;
    curl)
      curl -sfL "${REGISTRY_BASE_URL}/${rel_path}"
      ;;
  esac
}

# Kopioi koko skill-hakemiston sisältö target-hakemistoon
# Käyttö: source_fetch_skill_dir <skill_path> <target_dir>
source_fetch_skill_dir() {
  local skill_path="$1"
  local target_dir="$2"
  source_detect

  case "$SOURCE_MODE" in
    local)
      local src="${LOCAL_REPO_ROOT}/${skill_path}"
      if [[ ! -d "$src" ]]; then
        echo "${RED}✗${NC} Paikallista skill-hakemistoa ei löydy: ${src}" >&2
        return 1
      fi
      rm -rf "$target_dir"
      mkdir -p "$(dirname "$target_dir")"
      cp -r "$src" "$target_dir"
      ;;
    gh)
      local tarball; tarball="$(_shared_tmp)"
      if ! gh api "repos/${REGISTRY_REPO}/tarball/${REGISTRY_BRANCH}" > "$tarball" 2>/dev/null; then
        echo "${RED}✗${NC} Tarball-lataus epäonnistui (gh)." >&2
        return 1
      fi
      rm -rf "$target_dir"
      mkdir -p "$target_dir"
      local slashes="${skill_path//[^\/]/}"
      local strip=$(( ${#slashes} + 2 ))
      if ! tar -xzf "$tarball" -C "$target_dir" --strip-components="$strip" --wildcards "*/${skill_path}/*" 2>/dev/null; then
        echo "${RED}✗${NC} Tarballin purku epäonnistui (path: ${skill_path}, strip=${strip})." >&2
        return 1
      fi
      ;;
    curl)
      mkdir -p "$target_dir"
      if ! curl -sfL "${REGISTRY_BASE_URL}/${skill_path}/SKILL.md" -o "${target_dir}/SKILL.md"; then
        echo "${RED}✗${NC} SKILL.md:n lataus epäonnistui (curl): ${REGISTRY_BASE_URL}/${skill_path}/SKILL.md" >&2
        return 1
      fi
      echo "${YELLOW}⚠${NC} curl-tila lataa vain SKILL.md (ei alikansioita). Käytä SOURCE_MODE=gh tai paikallista repoa täydelle asennukselle." >&2
      ;;
  esac
}
