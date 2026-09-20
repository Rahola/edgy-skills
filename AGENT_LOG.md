# Agent Log

Tämä loki dokumentoi **tämän julkisen repon skillikehityksen päätökset** — mitä
tehtiin ja *miksi*. Git-historia kertoo *mitä* muuttui; tämä loki kertoo
perustelut.

> ⚠️ **TIETOSUOJASÄÄNTÖ — pakollinen.**
> Tämä repo on **julkinen**. Agenttilokiin **ei koskaan** kirjoiteta:
> - asiakas- tai toimeksiantonimiä,
> - asiakaskohtaisia analyyseja, tuloksia tai liiketoimintatietoa,
> - mitään mikä on peräisin yksityisistä toimeksiannoista.
>
> Kirjaa vain skillien ja repon **tekninen kehitys**. Jos joudut viittaamaan
> esimerkkidataan, käytä fiktiivistä yritystä (esim. *Acme Oy*). Yksityisten
> toimeksiantojen loki pidetään erillään, yksityisessä repossa — sitä ei
> koskaan porttata tänne.
>
> Automaattinen suoja: `tools/privacy-scan.sh` (ajetaan `check.sh`:ssä ja
> CI:ssä) blokkaa tunnetut asiakasnimet. Se ei kuitenkaan korvaa harkintaa.

---

### 2026-09-20 — Claude Code

**Assignment:** Retrospective review of EDGY diagrams and reports produced
across earlier sessions → development plan for the EDGY skills.

**Material (from the private upstream repo, not ported here):** 6 assessment
deliveries (20 drawio + 24 txt + 6 analysis MD), 2 reframing reports, 3
`generated/` experiments + issue log, 9 draw.io autosave backups, 16 official
EDGY 23 maps. The same 24 inputs were also regenerated with
`edgy_generator.py` v1.7 for comparison.

**Method:** programmatic scan (shape/colour per base type, legend, negative
and off-page coordinates, overlaps, text fit, core-link verb vs. allowed
pair, edge style) + approximate SVG render and visual comparison against the
official maps.

**Key findings (aggregates only, no client data):**
- The SKILL.md default "write the XML directly" systematically produces
  diagrams that violate the instruction's own CRITICAL rules: legend missing
  in 16/20, negative coordinates in 7/20, text overflow in 15/20 (42 % of
  elements), 0 anchored edges. Parser output: 0/0/8, but 3 overlaps and
  intersection elements placed far from their facets. 7/20 diagrams were
  fixed by hand in draw.io desktop.
- Link semantics leak: core-link verb on a wrong pair in 4/20, non-core
  link in core-link style in 8/20; no influence-verb vocabulary;
  `edgy_generator.py` never prints the parser's `warnings` list (a typo in
  the `facet:` value silently fell back to the identity default).
- Visually far from the official maps (containers, name/description
  separation, intersection placement). The draw.io CLI was unavailable in
  every session → the PDF pipeline needs a human.
- 0/6 deliveries contain `edgy-model.json` → `edgy-deep-dive` cannot run on
  existing models.

**Output:** `docs/development-plan-2026-09.md` — P0–P3 actions with
acceptance criteria, sprint split, metrics with baselines. Core
recommendation: LLM → semantic model → deterministic layout →
`edgy_lint.py`; direct XML only as a fallback, with lint.

**Notes for the next agents:**
- Do Sprint 1 (lint + printed warnings + pair validation + single core-link
  source) before layout work: the linter provides the baseline metrics.
- Once the linter exists, run it against old deliveries in the private repo
  and record only aggregates here.

---

### 2026-07-05 — Claude Code

**Toimeksianto:** EDGY-skillien poiminta yksityisestä upstream-reposta
tähän julkiseen `edgy-skills`-repoon ja julkaisukuntoon saattaminen.

**Mitä tuotiin:** Neljä toisistaan riippuvaa EDGY 23 -skilliä muodostavat
itsenäisen nipun:
- `skills/architecture/edgy-framework` (v1.2.0) — analyysi
- `skills/documentation/edgy-diagram` (v1.7.0) — renderöinti (draw.io/PlantUML)
- `skills/architecture/edgy-assessment` (v1.5.0) — orkestraattori
- `skills/architecture/edgy-deep-dive` (v1.0.0) — syväanalyysi

**Karsittiin:** `edgy-assessment.zip`, `edgy-diagram/generated/` (asiakastuotoksia),
`__pycache__`. Muut upstream-skillit (28 kpl) jätettiin pois.

**Tietosuojasanitointi (päätös: fiktiivinen data):**
- Kaikki oikean asiakasyrityksen viittaukset esimerkeissä → `Acme Oy`
  (suomen taivutukset mukaan lukien).
- Yksi julkisen palvelun esimerkki → fiktiivinen `Nordia Transit`.
- `intersection-edgy-analysis.md/.pdf` **säilytettiin ennallaan**: se analysoi
  Intersection Groupia (EDGY:n julkiset tekijät, julkinen data) — ei
  yksityinen asiakas. Toimii assessmentin PDF-layoutin lukkoreferenssinä.
- EDGY 23 -viralliset esimerkkikartat (`edgy-diagram/examples/official/`)
  säilytettiin — Intersection Groupin julkaisemia, CC BY-SA 4.0.

**Tietosuojainfra rakennettu (kerroksellinen, painopiste paikallisessa):**
- `tools/privacy-scan.sh` — termit gitignored `.blocklist`-tiedostosta;
  tulostaa vain `tiedosto:rivi`, ei termiä. **Paikallinen** suoja (pre-commit),
  koska privaatti konteksti on ylläpitäjän koneella. Ei CI-secrettiä →
  asiakaslistaa ei kopioida pilveen.
- `tools/examples-heuristic.sh` — nimetön CI-muistutus examples/-muutoksista
  (turvallinen julkisissa lokeissa, ei sisällä nimiä).
- Agenttiohjeet: `CONTRIBUTING.md` + tämän lokin sääntöboxi.
- `privacy-scan` on osa `check.sh`:ta; CI:ssä se on no-op ilman `.blocklist`:ia.

**Lisenssi:** Apache-2.0. EDGY-johdannaiset (stensiilit, notaatio, viralliset
kartat) periytyvät Intersection Groupin **CC BY-SA 4.0** -velvoitteesta →
dokumentoitu `NOTICE`-tiedostossa.

**Validointi:** `bash tools/check.sh` — validator + registry-sync +
examples-refs + privacy-scan kaikki läpi. `registry.yaml` regeneroitu (4 skilliä).

**Katselmus (3 rinnakkaista subagenttia) + korjaukset:**
- *Hookit:* `.claude/settings.json` puuttui ja `.gitignore` sulki sen → 3 Claude
  Code -hookia oli kuollutta painoa. Lisätty settings.json + gitignore-poikkeus
  + hook-taulukko CONTRIBUTINGiin.
- *Laatu:* korjattu sed-jäänne `Acme'`→`Acme's`; erotettu kaksi ristiriitaista
  esimerkkiyritystä (deep-dive → `Globex Oy`, assessment pysyy `Acme Oy`);
  orpo `reference-identity.drawio` → `acme-identity.drawio`.
- *Tietoturva:* verdikti puhdas (PDF+binäärit skannattu). Laajennettu
  `privacy-scan --all` kaikkiin trackattuihin tiedostoihin (skooppi oli liian
  kapea). Fail-open on tietoinen valinta (paikallinen valvonta, ei CI-secretiä).

**Adapterit:** tuotu `adapters/` lähteestä sopeutettuna EDGY-skilleille (repo-URL
`Rahola/edgy-skills`, esimerkkiskillit → edgy-framework/assessment/diagram):
- `mistral-vibe/`, `cursor/`, `claude-code/`, `generic/` + jaettu `_shared/source.sh`
- `github-coding-agent/` **jätettiin pois tarkoituksella:** se on rakennettu
  `code-review-council`/`code-review`/`ea-council-review`-skillien ympärille joita
  tässä repossa ei ole, eikä sen käyttötapaus (Copilot-agentti koodikatselmukseen)
  sovi enterprise-design-skilleille. Lisätään takaisin jos koodikatselmusskillejä
  joskus tuodaan.
- README:hyn adapteritaulukko; kaikki install.sh:t syntaksitarkistettu.
