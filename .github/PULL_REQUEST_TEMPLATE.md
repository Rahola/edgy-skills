# Pull Request

## Tyyppi

- [ ] Uusi skill
- [ ] Olemassa olevan skillin päivitys
- [ ] Uusi adapteri
- [ ] Työkalu tai CI-muutos
- [ ] Dokumentaatio
- [ ] Muu: ___________

---

## Kuvaus

<!-- Lyhyt kuvaus muutoksesta ja sen tarkoituksesta -->

---

## Uusi skill — Checklist

Jos lisäät uuden skillin, tarkista kaikki:

### SKILL.md
- [ ] `name` vastaa hakemiston nimeä (kebab-case)
- [ ] `version` on semanttisessa muodossa (esim. `1.0.0`)
- [ ] `description` on selkeä ja kuvaa skillin tarkoituksen
- [ ] `category` on yksi sallituista: `coding`, `architecture`, `security`, `documentation`, `productivity`
- [ ] `tags` sisältää relevantit hakutunnisteet
- [ ] `agents` listaa tuetut agentit
- [ ] Markdown-runko sisältää osiot: Käyttötarkoitus, Ohjeet agentille, Tulostemalli
- [ ] Esimerkit ovat anonyymisoituja (ei oikeita nimiä)

### Hakemistorakenne
- [ ] Skill sijaitsee oikeassa kategoriahakemistossa: `skills/<category>/<skill-name>/`
- [ ] `SKILL.md` on luotu
- [ ] `prompts/`-alihakemisto on luotu (jos tarvitaan)

### Registry
- [ ] `registry.yaml` on päivitetty (`python tools/registry-updater.py`)
- [ ] `python tools/skill-validator.py skills/<category>/<skill-name>/` läpäisee ilman virheitä

### Testaus
- [ ] Testattu manuaalisesti vähintään yhdellä agentilla
- [ ] Tuloste vastaa `SKILL.md`:ssä kuvattua tulostemalia

---

## Olemassa olevan skillin päivitys

- [ ] `version` on kasvatettu (patch / minor / major)
- [ ] Breaking change → major-versio kasvatettu
- [ ] `registry.yaml` päivitetty

---

## Lisätietoja

<!-- Mikä tahansa lisäkonteksti, linkit, kuvakaappaukset -->
