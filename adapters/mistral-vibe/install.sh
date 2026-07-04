#!/bin/bash
# edgy-skills — Mistral Vibe CLI adapter
# Downloads skills into ~/.mistral-vibe/skills/ and prints usage instructions.
#
# Usage:
#   bash install.sh edgy-framework
#   bash install.sh --list
#   bash install.sh edgy-assessment edgy-diagram
#
# Set EDGY_SKILLS_REPO to override the source repo (default: Rahola/edgy-skills).

set -euo pipefail

REPO="${EDGY_SKILLS_REPO:-Rahola/edgy-skills}"
REGISTRY_BASE_URL="https://raw.githubusercontent.com/${REPO}/main"
REGISTRY_URL="${REGISTRY_BASE_URL}/registry.yaml"
SKILLS_DIR="${HOME}/.mistral-vibe/skills"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1" >&2; }

usage() {
  cat <<EOF
Usage: $0 <skill-id> [skill-id2 ...]
       $0 --list

Options:
  --list    List all available skills

Examples:
  $0 edgy-framework
  $0 edgy-assessment edgy-diagram edgy-deep-dive
  $0 --list

Installs to: ${SKILLS_DIR}/<skill-id>/SKILL.md
Source repo: ${REPO} (override with EDGY_SKILLS_REPO=owner/repo)
EOF
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOOKUP_TOOL="${SCRIPT_DIR}/../../tools/lookup-skill.py"

# Fetch registry into a safe temp file
registry_file=$(mktemp "${TMPDIR:-/tmp}/edgy-skills-mistral-XXXXXX.yaml")
trap 'rm -f "$registry_file"' EXIT
curl -sf "$REGISTRY_URL" -o "$registry_file" || {
  log_error "Failed to download registry.yaml: $REGISTRY_URL"
  exit 1
}

# List mode
if [[ "${1:-}" == "--list" ]]; then
  echo "Available skills:"
  python3 "$LOOKUP_TOOL" list --verbose "$registry_file"
  exit 0
fi

[[ $# -eq 0 ]] && usage

SKILL_IDS=("$@")

for SKILL_ID in "${SKILL_IDS[@]}"; do
  skill_path=$(python3 "$LOOKUP_TOOL" path "$SKILL_ID" "$registry_file") || {
    log_error "Skill '${SKILL_ID}' not found. Run '$0 --list' to see available skills."
    continue
  }

  skill_url="${REGISTRY_BASE_URL}/${skill_path}/SKILL.md"
  target_dir="${SKILLS_DIR}/${SKILL_ID}"
  target="${target_dir}/SKILL.md"

  mkdir -p "$target_dir"
  curl -sf "$skill_url" -o "$target" || {
    log_error "Download failed: $skill_url"
    continue
  }

  log_info "Skill '${SKILL_ID}' installed → ${target}"
done

echo ""
echo "Use in Mistral Vibe CLI:"
echo "  mistral-vibe --system \"\$(cat ${SKILLS_DIR}/<skill-id>/SKILL.md)\""
echo ""
echo "Or load into a variable:"
echo "  SKILL=\$(cat ${SKILLS_DIR}/<skill-id>/SKILL.md)"
echo "  mistral-vibe --system \"\$SKILL\" --prompt 'Analyse X'"
