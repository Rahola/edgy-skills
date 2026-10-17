#!/bin/bash
# edgy-skills — Mistral Vibe CLI adapter
# Downloads skills (SKILL.md only) into ~/.mistral-vibe/skills/ and prints usage instructions.
#
# Usage:
#   bash install.sh edgy-framework
#   bash install.sh edgy-assessment edgy-diagram
#   bash install.sh --all
#   bash install.sh --list
#   bash install.sh --source=local edgy-framework     # from this checkout, no network
#
# Source (auto-detect): the local checkout when this script runs inside one,
# else gh (authenticated), else curl. Force with --source=local|gh|curl.
# Set EDGY_SKILLS_REPO to override the source repo (default: Rahola/edgy-skills).
# Set EDGY_SKILLS_REF to install a released version (tag, branch or commit;
# default: main), e.g. EDGY_SKILLS_REF=v1.0.0 bash install.sh edgy-diagram
#
# Vibe installs SKILL.md only. A skill that needs its scripts (install: directory
# in the registry, e.g. edgy-c4) is refused with a message; --all skips it and
# names it. Any failure exits 1 and no success line is printed.

set -euo pipefail

ADAPTER_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${ADAPTER_SCRIPT_DIR}/../_shared/source.sh"
source "${ADAPTER_SCRIPT_DIR}/../_shared/deps.sh"

SKILLS_DIR="${HOME}/.mistral-vibe/skills"

log_info()  { echo -e "${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1" >&2; }

usage() {
  cat <<EOF
Usage: $0 [--source=local|gh|curl] <skill-id> [skill-id2 ...]
       $0 [--source=local|gh|curl] --all
       $0 --list

Options:
  --all     Install every skill that works with Vibe (SKILL.md only)
  --list    List all available skills

Installs to: ${SKILLS_DIR}/<skill-id>/SKILL.md
Source repo: ${REGISTRY_REPO} (override with EDGY_SKILLS_REPO=owner/repo)
EOF
  exit 1
}

ARGS=()
LIST_MODE=false
for arg in "$@"; do
  case "$arg" in
    --source=*) SOURCE_MODE="${arg#--source=}" ;;
    --list)     LIST_MODE=true ;;
    -h|--help)  usage ;;
    *)          ARGS+=("$arg") ;;
  esac
done

if ! command -v python3 &>/dev/null; then
  log_error "python3 not found."
  exit 1
fi

source_detect
registry_file=$(deps_registry_override) || registry_file=$(source_fetch_registry) || exit 1

if [[ "$LIST_MODE" == true ]]; then
  echo "Available skills:"
  python3 "$LOOKUP_TOOL" list --verbose "$registry_file"
  exit 0
fi

[[ ${#ARGS[@]} -eq 0 ]] && usage

install_one() {
  local skill_id="$1" skill_path target_dir target
  skill_path=$(python3 "$LOOKUP_TOOL" path "$skill_id" "$registry_file") || return 1
  target_dir="${SKILLS_DIR}/${skill_id}"
  target="${target_dir}/SKILL.md"
  mkdir -p "$target_dir"
  if ! source_fetch_file "${skill_path}/SKILL.md" > "${target}.tmp" || [[ ! -s "${target}.tmp" ]]; then
    rm -f "${target}.tmp"
    log_error "Download failed: ${skill_path}/SKILL.md"
    return 1
  fi
  mv "${target}.tmp" "$target"
  log_info "Skill '${skill_id}' installed → ${target}"
}

# Install a skill and its requirements; refuse a skill Vibe cannot run
install_skill() {
  local skill_id="$1" order sid
  order=$(deps_install_order "$skill_id" "$registry_file") || return 1
  while IFS= read -r sid; do
    [[ -z "$sid" ]] && continue
    deps_supports "$sid" "$registry_file" "vibe" "skillmd" || return 1
  done <<< "$order"
  while IFS= read -r sid; do
    [[ -z "$sid" ]] && continue
    install_one "$sid" || return 1
  done <<< "$order"
}

FAILED=()
if [[ "${ARGS[0]}" == "--all" ]]; then
  if ! all_ids=$(deps_list_or_fail "$registry_file"); then
    log_error "No skill list from the registry — nothing installed."
    exit 1
  fi
  while IFS= read -r skill_id; do
    skill_id="${skill_id%$'\r'}"
    [[ -z "$skill_id" ]] && continue
    if ! reason=$(deps_supports "$skill_id" "$registry_file" "vibe" "skillmd" 2>&1); then
      log_warn "Skipping ${skill_id}: ${reason}"
      continue
    fi
    install_skill "$skill_id" || FAILED+=("$skill_id")
  done <<< "$all_ids"
else
  for skill_id in "${ARGS[@]}"; do
    install_skill "$skill_id" || FAILED+=("$skill_id")
  done
fi

echo ""
if [[ ${#FAILED[@]} -gt 0 ]]; then
  log_error "Failed: ${FAILED[*]} (${#FAILED[@]} skill(s))."
  exit 1
fi
echo "Use in Mistral Vibe CLI:"
echo "  mistral-vibe --system \"\$(cat ${SKILLS_DIR}/<skill-id>/SKILL.md)\""
echo ""
echo "Or load into a variable:"
echo "  SKILL=\$(cat ${SKILLS_DIR}/<skill-id>/SKILL.md)"
echo "  mistral-vibe --system \"\$SKILL\" --prompt 'Analyse X'"
