#!/usr/bin/env bash
# install-git-hooks.sh — asentaa paikallisen .git/hooks/pre-commit-tiedoston,
# joka ajaa tools/check.sh:n ennen jokaista committia.
#
# Tarkoitettu ei-Claude-Code-käyttäjille (Mistral Vibe, Cursor, generic,
# manuaaliset kontribuoijat) jotta he saavat saman suojan kuin Claude Code
# -käyttäjät .claude/settings.json-hookien kautta.
#
# Käyttö:
#   bash tools/install-git-hooks.sh

set -eu

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
    echo "Virhe: tämä ei ole git-repo. Aja repon juuressa." >&2
    exit 1
fi

HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOK_FILE="$HOOKS_DIR/pre-commit"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "Virhe: $HOOKS_DIR ei ole olemassa." >&2
    exit 1
fi

if [ -f "$HOOK_FILE" ]; then
    echo "Varoitus: $HOOK_FILE on jo olemassa."
    read -r -p "Korvataanko? [y/N] " ans
    case "$ans" in
        y|Y|yes) ;;
        *) echo "Peruttu."; exit 0 ;;
    esac
fi

cat > "$HOOK_FILE" <<'EOF'
#!/usr/bin/env bash
# pre-commit — asennettu tools/install-git-hooks.sh:lla.
# Ajaa saman validointiskriptin kuin CI ja Claude Code -hookit.
if [ "${SKIP_CHECK:-0}" = "1" ]; then
    exit 0
fi
exec bash "$(git rev-parse --show-toplevel)/tools/check.sh"
EOF
chmod +x "$HOOK_FILE"

echo "✓ Asennettu: $HOOK_FILE"
echo
echo "Tarkistus ajetaan automaattisesti ennen jokaista 'git commit':ia."
echo "Ohitus tarvittaessa:"
echo "  git commit --no-verify -m \"...\""
echo "  SKIP_CHECK=1 git commit -m \"...\""
echo
echo "Manuaalinen tarkistus: bash tools/check.sh"
