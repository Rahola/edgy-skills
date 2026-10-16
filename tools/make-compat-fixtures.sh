#!/usr/bin/env bash
# make-compat-fixtures.sh — write the 1.8 compatibility fixtures of the model tools.
#
# Runs edgy_model_to_txt.py (default and triad layout), edgy_model_diff.py
# (TXT + report + JSON) and edgy_model_to_archimate.py on every shipped 1.8
# model, from the scripts of the checkout given as $1 (default: this repo),
# into tools/fixtures/compat-1.8/. tools/test_model_compat.py regenerates the
# same outputs with the current scripts and requires them byte-identical.
#
# The fixtures were written once from origin/main at v2.3.0 (before schema 1.9):
#   git worktree add /tmp/main origin/main && bash tools/make-compat-fixtures.sh /tmp/main
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$REPO}"
A="$SRC/skills/architecture/edgy-assessment/scripts"
OUT="$REPO/tools/fixtures/compat-1.8"
rm -rf "$OUT" && mkdir -p "$OUT"
MODELS=(
  "skills/architecture/edgy-deep-dive/examples/sample-model.json"
  "skills/architecture/edgy-assessment/examples/model-diff/current-model.json"
  "skills/architecture/edgy-assessment/examples/model-diff/target-model.json"
)
cd "$REPO"
for m in "${MODELS[@]}"; do
  name=$(basename "$m" .json)
  python3 "$A/edgy_model_to_txt.py" "$m" --out "$OUT/$name" --prefix default >/dev/null
  python3 "$A/edgy_model_to_txt.py" "$m" --out "$OUT/$name" --prefix triad --layout triad >/dev/null
  python3 "$A/edgy_model_to_archimate.py" "$m" -o "$OUT/$name/archimate.xml" >/dev/null
done
D="skills/architecture/edgy-assessment/examples/model-diff"
mkdir -p "$OUT/diff"
python3 "$A/edgy_model_diff.py" "$D/current-model.json" "$D/target-model.json" --out "$OUT/diff/transition.txt" \
  --report "$OUT/diff/changes.md" >/dev/null
python3 "$A/edgy_model_diff.py" "$D/current-model.json" "$D/target-model.json" --json > "$OUT/diff/diff.json"
echo "compat fixtures: $(find "$OUT" -type f | wc -l) files in tools/fixtures/compat-1.8"
