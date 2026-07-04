# Paikallinen validointi — ilman CI/CD-automaatiota

Tämä dokumentti kertoo, miten skillit validoidaan paikallisesti ennen Pull Requestin tekemistä. Noudattamalla näitä ohjeita varmistat, että PR menee läpi myös kun CI/CD-pipeline on myöhemmin käytössä.

---

## Pikatarkistus

Kaikki validointivaiheet yhdellä komennolla — sama skripti jota CI ajaa
(validator + registry-sync + examples-refs + **privacy-scan**):

```bash
bash tools/check.sh
```

> 🔒 **Tietosuoja:** `privacy-scan` estää yksityisten asiakasnimien vuodon
> julkiseen repoon. Se on **paikallinen** suoja: kopioi `.blocklist.example` →
> `.blocklist`, lisää omat suojattavat termisi (tiedosto on `.gitignore`:ssa) ja
> asenna `bash tools/install-git-hooks.sh`. Ilman `.blocklist`-tiedostoa step
> ohittuu hiljaisesti — siksi se on no-op CI:ssä (asiakaslistaa ei tallenneta
> pilveen). CI ajaa sen sijaan nimettömän `examples/`-muistutuksen.

- **Claude Code -käyttäjät** saavat tämän automaattisesti `.claude/settings.json`-hookien kautta (PostToolUse SKILL.md-muokkauksen jälkeen, PreToolUse `git commit`-bashin yhteydessä).
- **Muut agentit (Vibe, Cursor, generic)** voivat asentaa saman tarkistuksen git-pre-commit-hookiksi kerralla: `bash tools/install-git-hooks.sh`.
- **Ohitus tarvittaessa:** `git commit --no-verify -m "WIP"` tai `SKIP_CHECK=1 git commit ...`.

Jäljellä oleva dokumentti kuvaa yksittäiset validointivaiheet käsin — hyödyllinen kun pikatarkistus löytää virheen ja haluat ymmärtää mitä työkalua ajetaan ja miksi.

---

## Esivalmistelut

### 1. Kloonaa repo ja siirry hakemistoon

```bash
git clone https://github.com/<your-org>/edgy-skills.git
cd edgy-skills
```

### 2. Asenna Python-riippuvuudet

```bash
pip install pyyaml
# tai
pip3 install pyyaml
```

Tarkista että Python 3.8+ on käytössä:

```bash
python3 --version
```

---

## Validointivaiheet

Suorita nämä **järjestyksessä** ennen jokaista Pull Requestia.

---

### Vaihe 1 — Validoi SKILL.md-rakenne

Tarkistaa pakolliset YAML-kentät, version muodon, kategorian ja agents-listan.

```bash
# Validoi kaikki skillit kerralla
python3 tools/skill-validator.py skills/

# Validoi vain oma uusi skill
python3 tools/skill-validator.py skills/<category>/<skill-name>/

# Validoi yksittäinen tiedosto
python3 tools/skill-validator.py skills/documentation/meeting-minutes/SKILL.md
```

**Odotettu tuloste (OK):**
```
Validoidaan 3 SKILL.md-tiedosto(a)...

✓ OK: skills/architecture/architecture-review/SKILL.md
✓ OK: skills/documentation/meeting-minutes/SKILL.md
✓ OK: skills/productivity/decision-log/SKILL.md

============================================================
Tarkistettu: 3 tiedostoa
Virheitä:    0
Varoituksia: 0

✓ Kaikki validoinnit läpi!
```

**Jos saat virheitä**, korjaa ne ennen jatkamista. Yleisimmät ongelmat:

| Virhe | Korjaus |
|-------|---------|
| `Pakollinen kenttä puuttuu: 'version'` | Lisää `version: 1.0.0` frontmatteriin |
| `Versio '1.0' ei ole semanttisessa muodossa` | Muuta muotoon `1.0.0` |
| `Tuntematon kategoria: 'docs'` | Käytä: `coding`, `architecture`, `security`, `documentation`, `productivity` |
| `'name' ei vastaa hakemiston nimeä` | Vaihda `name`-kenttä vastaamaan hakemiston nimeä |

---

### Vaihe 2 — Päivitä registry.yaml

Varmistaa että uusi skill näkyy koneluettavassa hakemistossa.

```bash
python3 tools/registry-updater.py
```

**Odotettu tuloste (uusi skill):**
```
Löydetty 4 SKILL.md-tiedostoa hakemistosta: skills

  ✓ architecture-review v2.0.1 (architecture)
  ✓ meeting-minutes v1.2.0 (documentation)
  ✓ decision-log v1.0.0 (productivity)
  ✓ your-new-skill v1.0.0 (coding)       ← uusi

Uudet skillit: your-new-skill

✓ registry.yaml päivitetty: registry.yaml
  Yhteensä 4 skilliä.
```

Tarkista muutos:
```bash
git diff registry.yaml
```

Committaa registry-muutos omaan committiin:
```bash
git add registry.yaml
git commit -m "chore: päivitä registry.yaml — lisätty your-new-skill"
```

---

### Vaihe 3 — Testaa hakutoiminto

Varmistaa että uusi skill löytyy tagihaulla.

```bash
# Etsi omilla tageilla
python3 tools/skill-search.py --tag <your-tag>

# Listaa kaikki — tarkista että uusi skill näkyy
python3 tools/skill-search.py --list

# Etsi kategorialla
python3 tools/skill-search.py --category <your-category>

# Etsi agentilla
python3 tools/skill-search.py --agent claude-code
```

**Odotettu tuloste:**
```
Löydetty 1 skill(iä):

  your-new-skill                 v1.0.0      [claude-code, cursor, generic]
                                 Kategoria: coding
                                 Lyhyt kuvaus skillista...
```

Jos skill ei löydy haulla, tarkista että `tags`-kenttä frontmatterissa täsmää.

---

### Vaihe 4 — Testaa skill manuaalisesti agentilla

Kopioi SKILL.md:n sisältö agentillesi system promptiksi ja testaa se oikealla syötteellä.

#### Claude Code

```bash
# Lisää skill väliaikaisesti
mkdir -p ~/.claude/skills/your-new-skill
cp skills/<category>/your-new-skill/SKILL.md ~/.claude/skills/your-new-skill/SKILL.md
echo "@skills/your-new-skill" >> ~/.claude/CLAUDE.md

# Testaa Claude Codessa — anna agentille oikea syöte ja tarkista tuloste
```

#### Cursor

```bash
# Lisää skill .cursorrules-tiedostoon projektin juuressa
cat skills/<category>/your-new-skill/SKILL.md >> .cursorrules
# Avaa Cursor ja testaa
```

#### Mistral Vibe CLI

```bash
# Lataa skill ja käynnistä
mistral-vibe --system-file skills/<category>/your-new-skill/SKILL.md
# Anna oikea syöte ja tarkista tuloste
```

#### Manuaalinen testi (kaikki agentit)

1. Avaa `skills/<category>/your-new-skill/SKILL.md`
2. Kopioi koko tiedoston sisältö
3. Liitä se agentillesi system promptiksi
4. Anna esimerkkisyöte (`examples/`-hakemistosta tai keksimäsi)
5. Vertaa tuloste SKILL.md:n `## Tulostemalli`-osioon

**Tarkistuslista manuaaliselle testille:**
- [ ] Agentti ymmärtää tehtävän ilman lisäselvityksiä
- [ ] Tuloste noudattaa SKILL.md:ssä kuvattua rakennetta
- [ ] Kieliasetus toimii (fi/en) jos skill tukee molempia
- [ ] Mahdolliset pakolliset syötteet tunnistetaan oikein

---

### Vaihe 5 — Tarkista YAML-tiedostojen syntaksi

```bash
python3 -c "
import yaml, pathlib, sys
errors = []
for f in pathlib.Path('.').rglob('*.yaml'):
    if '.git' in str(f):
        continue
    try:
        yaml.safe_load(f.read_text())
        print(f'✓ {f}')
    except yaml.YAMLError as e:
        errors.append(f'{f}: {e}')
        print(f'✗ {f}: {e}')
if errors:
    sys.exit(1)
else:
    print()
    print('Kaikki YAML-tiedostot OK.')
"
```

---

## Koko validointiputki yhdellä komennolla

Kopioi tämä ja aja ennen jokaista PR:ää:

```bash
echo "=== Vaihe 1: Validoi SKILL.md ===" && \
python3 tools/skill-validator.py skills/ && \
echo "" && \
echo "=== Vaihe 2: Päivitä registry ===" && \
python3 tools/registry-updater.py && \
echo "" && \
echo "=== Vaihe 3: Testaa haku ===" && \
python3 tools/skill-search.py --list && \
echo "" && \
echo "=== Vaihe 4: Tarkista YAML ===" && \
python3 -c "
import yaml, pathlib, sys
errors = []
for f in pathlib.Path('.').rglob('*.yaml'):
    if '.git' in str(f): continue
    try: yaml.safe_load(f.read_text())
    except yaml.YAMLError as e: errors.append(str(e))
print(f'YAML-tiedostot: {\"OK\" if not errors else \"VIRHEITÄ\"}')
if errors: [print(e) for e in errors]; sys.exit(1)
" && \
echo "" && \
echo "=== Kaikki validoinnit läpi — valmis PR:ään! ==="
```

---

## Yleisimmät ongelmat

### `ModuleNotFoundError: No module named 'yaml'`

```bash
pip3 install pyyaml
```

### `python3: command not found`

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3 python3-pip

# Windows (WSL)
sudo apt install python3 python3-pip
```

### `registry.yaml ei ole ajan tasalla` -virhe CI:ssä

Aja paikallisesti ja committaa:
```bash
python3 tools/registry-updater.py
git add registry.yaml
git commit -m "chore: päivitä registry.yaml"
```

### Validator sanoo `'name' ei vastaa hakemiston nimeä`

SKILL.md:n `name`-kentän pitää täsmätä tarkalleen hakemiston nimeen:
```
skills/documentation/meeting-minutes/SKILL.md
                     ^^^^^^^^^^^^^^^ hakemiston nimi
```
```yaml
name: meeting-minutes   ← täsmää hakemiston nimeen
```

---

## CI/CD

Nämä samat vaiheet ajetaan automaattisesti `.github/workflows/validate-skills.yml`-workflowssa Pull Requesteissa. Paikallinen validointi nopeuttaa kehitystä ja estää turhat CI-epäonnistumiset.
