#!/usr/bin/env bash
# make-compat-fixtures-19.sh — write the 1.9 compatibility fixtures of the model tools.
#
# Runs edgy_model_to_txt.py (default, triad and --views all), edgy_model_diff.py
# (TXT, --full TXT, report, JSON) and edgy_model_to_archimate.py on 1.9 models,
# from the scripts of the checkout given as $1 (default: this repo), into
# tools/fixtures/compat-1.9/. tools/test_model_compat.py regenerates the same
# outputs with the current scripts and requires them byte-identical.
#
# The models: the shipped architecture-model.json, one with a single journey that
# has an id and relationships to it, and one with a 200-character element id
# (tools/fixtures/models-1.9/). The fixtures were written once from the v2.4.0 tag:
#   git worktree add /tmp/v240 v2.4.0 && bash tools/make-compat-fixtures-19.sh /tmp/v240
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$REPO}"
A="$SRC/skills/architecture/edgy-assessment/scripts"
OUT="$REPO/tools/fixtures/compat-1.9"
export EDGY_TEXT_TABLE_ONLY=1
rm -rf "$OUT" && mkdir -p "$OUT"
MODELS=(
  "skills/architecture/edgy-assessment/examples/architecture-model.json"
  "tools/fixtures/models-1.9/journey-with-id.json"
  "tools/fixtures/models-1.9/long-id.json"
)
cd "$REPO"
for m in "${MODELS[@]}"; do
  name=$(basename "$m" .json)
  python3 "$A/edgy_model_to_txt.py" "$m" --out "$OUT/$name" --prefix default >/dev/null
  python3 "$A/edgy_model_to_txt.py" "$m" --out "$OUT/$name" --prefix triad --layout triad >/dev/null
  python3 "$A/edgy_model_to_txt.py" "$m" --out "$OUT/$name" --prefix views --views all >/dev/null 2>&1
  python3 "$A/edgy_model_to_archimate.py" "$m" -o "$OUT/$name/archimate.xml" >/dev/null
done
CUR="skills/architecture/edgy-assessment/examples/architecture-model.json"
TGT="tools/fixtures/models-1.9/target-model.json"
mkdir -p "$OUT/diff"
python3 "$A/edgy_model_diff.py" "$CUR" "$TGT" --out "$OUT/diff/transition.txt" --report "$OUT/diff/changes.md" >/dev/null
python3 "$A/edgy_model_diff.py" "$CUR" "$TGT" --full --out "$OUT/diff/transition-full.txt" >/dev/null
python3 "$A/edgy_model_diff.py" "$CUR" "$TGT" --json > "$OUT/diff/diff.json"
echo "compat fixtures: $(find "$OUT" -type f | wc -l) files in tools/fixtures/compat-1.9"
