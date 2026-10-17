#!/bin/bash
# edgy-skills — Generic Adapter
# Universaali skripti skillien lataamiseen haluamaasi hakemistoon
#
# Käyttö:
#   bash install.sh --skill edgy-framework --output ./skills/
#   bash install.sh --skill edgy-framework --output ./prompts/ --format raw
#   bash install.sh --skill edgy-framework --source=gh   # private repo

set -euo pipefail

# Lataa jaettu lähdestrategia
ADAPTER_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${ADAPTER_SCRIPT_DIR}/../_shared/source.sh"
source "${ADAPTER_SCRIPT_DIR}/../_shared/deps.sh"

log_info()  { echo -e "${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1" >&2; }

usage() {
  cat <<EOF
Käyttö: $0 --skill <skill-id> [--output <hakemisto>] [--format <raw|url>] [--source=local|gh|curl]

Optiot:
  --skill   <id>     Asennettavan skillin tunniste (pakollinen)
  --output  <dir>    Kohdehakemisto (oletus: ./skills/)
  --format  <mode>   'raw' = lataa tiedosto, 'url' = tulosta URL (oletus: raw)
  --source  <mode>   Pakota lähde: local|gh|curl (oletus: auto-detect)
  --list             Listaa kaikki saatavilla olevat skillit

Esimerkit:
  $0 --skill edgy-framework
  $0 --skill edgy-framework --output ./my-prompts/
  $0 --skill edgy-framework --format url
  $0 --skill edgy-framework --source=gh
  $0 --list
EOF
  exit 1
}

SKILL_ID=""
OUTPUT_DIR="./skills"
FORMAT="raw"
LIST_MODE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)    SKILL_ID="$2"; shift 2 ;;
    --output)   OUTPUT_DIR="$2"; shift 2 ;;
    --format)   FORMAT="$2"; shift 2 ;;
    --source=*) SOURCE_MODE="${1#--source=}"; shift ;;
    --source)   SOURCE_MODE="$2"; shift 2 ;;
    --list)     LIST_MODE=true; shift ;;
    -h|--help)  usage ;;
    *)          log_error "Tuntematon optio: $1"; usage ;;
  esac
done

if ! command -v python3 &>/dev/null; then
  log_error "python3 ei löydy."
  exit 1
fi

source_detect
log_info "Lähde: ${SOURCE_MODE}"

registry_file=$(deps_registry_override) || registry_file=$(source_fetch_registry) || exit 1

# Lista-moodi
if [[ "$LIST_MODE" == true ]]; then
  echo "Saatavilla olevat skillit:"
  python3 "$LOOKUP_TOOL" list --verbose "$registry_file"
  exit 0
fi

[[ -z "$SKILL_ID" ]] && usage

# Asennusjärjestys: riippuvuudet (requires) ensin. lookup-skill.py tarkistaa jokaisen id:n.
order=$(deps_install_order "$SKILL_ID" "$registry_file") || exit 1
mode="directory"
[[ "$SOURCE_MODE" == "curl" ]] && mode="skillmd"
while IFS= read -r sid; do
  [[ -z "$sid" ]] && continue
  deps_supports "$sid" "$registry_file" "generic" "$mode" || exit 1
done <<< "$order"

skill_path=$(python3 "$LOOKUP_TOOL" path "$SKILL_ID" "$registry_file") || exit 1

if [[ "$FORMAT" == "url" ]]; then
  # URL-tila olettaa public repon — varoita jos lähde ei ole curl
  if [[ "$SOURCE_MODE" != "curl" ]]; then
    log_warn "URL-tila tulostaa public-URLin; jos repo on private, raw-URL antaa 404."
  fi
  echo "${REGISTRY_BASE_URL}/${skill_path}/SKILL.md"
  exit 0
fi

# Lataa tiedosto(t): riippuvuudet ensin, sitten pyydetty skill
while IFS= read -r sid; do
  [[ -z "$sid" ]] && continue
  sid_path=$(python3 "$LOOKUP_TOOL" path "$sid" "$registry_file") || exit 1
  target_dir="${OUTPUT_DIR}/${sid}"
  [[ "$sid" != "$SKILL_ID" ]] && log_info "${SKILL_ID} requires ${sid} — installing it first"
  [[ -e "$target_dir" ]] && log_warn "overwriting ${sid} from $([[ "$SOURCE_MODE" == local ]] && echo 'the local checkout' || echo "$REGISTRY_BRANCH")"
  if ! source_fetch_skill_dir "$sid_path" "$target_dir"; then
    log_error "Lataaminen epäonnistui (skill: ${sid})"
    exit 1
  fi
  log_info "Skill '${sid}' ladattu → ${target_dir}"
done <<< "$order"
target_dir="${OUTPUT_DIR}/${SKILL_ID}"
echo ""
echo "Käyttö agentissasi:"
echo "  Lisää seuraava rivi promptiisi tai konfiguraatioosi:"
echo "  @${target_dir}/SKILL.md"
