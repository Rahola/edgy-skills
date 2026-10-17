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

1. Lukee `registry.yaml`:n (paikallinen checkout tai repositorio; `EDGY_SKILLS_REGISTRY` ohittaa)
2. Selvittää skillin riippuvuudet (`requires:`, esim. `edgy-c4` → `edgy-diagram`) ja asentaa ne
   ensin samasta refistä; vanhan kopion päälle kirjoittaessa se kertoo sen
3. Paikallisesta checkoutista kopioi koko skillin hakemiston `~/.claude/skills/<skill-id>/`
   (skriptit, assetit, `notation.json`); `--source=curl` lataa vain `SKILL.md`:n ja kieltäytyy
   skilleistä, joilla on `install: directory` (esim. `edgy-c4`)
4. Lisää viittauksen `~/.claude/CLAUDE.md`-tiedostoon
5. Epäonnistunut skilli, tyhjä tai lukukelvoton skillilista → exit 1 ja epäonnistuneet nimettynä,
   ei "Asennus valmis" -riviä

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
