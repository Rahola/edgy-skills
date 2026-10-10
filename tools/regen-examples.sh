#!/usr/bin/env bash
# Regenerate every shipped expected-*.drawio (and expected-purpose.puml) of the
# edgy-diagram skill from its input. Run after a generator change; never edit
# the expected files by hand. Usage: bash tools/regen-examples.sh
set -euo pipefail
cd "$(dirname "$0")/../skills/documentation/edgy-diagram"   # layout_from: paths in the inputs are relative to the skill root
EX="examples"
GEN="scripts/edgy_generator.py"
for txt in "$EX"/*.txt; do
    name=$(basename "$txt" .txt)
    name=${name%-facet}
    name=${name%-map}
    python3 "$GEN" "$txt" --output "$EX/expected-$name.drawio" >/dev/null
done
python3 "$GEN" "$EX/purpose-map.txt" --format puml --output "$EX/expected-purpose.puml" >/dev/null
echo "regen-examples: $(ls "$EX"/expected-*.drawio | wc -l) drawio files + expected-purpose.puml regenerated"
