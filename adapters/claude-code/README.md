# Claude Code Adapter

Tämä adapteri integroi edgy-skills -skillit Claude Codeen.

## Miten Claude Code käyttää skillejä

Claude Code lukee skillien sisällön `~/.claude/skills/` -hakemistosta ja viittaukset `CLAUDE.md`-tiedostosta. Kun skill on asennettu, Claude Code voi käyttää sen ohjeita tehtävien suorittamiseen.

## Asennus

### Yksittäisen skillin asennus

```bash
bash adapters/claude-code/install.sh edgy-framework
```

### Useamman skillin asennus

```bash
bash adapters/claude-code/install.sh edgy-framework edgy-assessment edgy-diagram
```

### Kaikkien skillien asennus (varoitus: lataa paljon)

```bash
bash adapters/claude-code/install.sh --all
```

## Mitä install.sh tekee

1. Lataa `registry.yaml` repositoriosta
2. Etsii pyydetyn skillin polun
3. Lataa `SKILL.md` `~/.claude/skills/<skill-id>/SKILL.md`
4. Lisää viittauksen `~/.claude/CLAUDE.md`-tiedostoon

## CLAUDE.md-integraatio

Asennuksen jälkeen `~/.claude/CLAUDE.md` sisältää:

```markdown
## Available Skills

@skills/edgy-framework
@skills/edgy-assessment
@skills/edgy-diagram
```

## Vaatimukset

- `curl` — HTTP-pyyntöihin
- `yq` — YAML-parsintaan (tai Python fallback)
- Kirjoitusoikeus `~/.claude/` -hakemistoon
