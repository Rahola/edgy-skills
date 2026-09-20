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

**Toimeksianto:** Jälkikatselmus eri sessioissa tuotetuista EDGY-kaavioista ja
-raporteista → kehityssuunnitelma edgy-skilleille.

**Aineisto (yksityisestä upstream-reposta, ei porttattu tänne):** 6
assessment-toimitusta (20 drawio + 24 txt + 6 analyysi-MD), 2 reframing-
raporttia, 3 `generated/`-kokeilua + ongelmaloki, 9 draw.io-autosave-
varmuuskopiota, 16 virallista EDGY 23 -karttaa. Lisäksi samat 24 syötettä
uudelleengeneroitiin `edgy_generator.py` v1.7:llä vertailuksi.

**Menetelmä:** ohjelmallinen skannaus (muoto/väri per perustyyppi, legenda,
negatiiviset ja sivun ulkopuoliset koordinaatit, päällekkäisyys, tekstin
mahtuvuus, ydinlinkkiverbi vs. sallittu pari, reunatyyli) + approksimoiva
SVG-render ja visuaalinen vertailu virallisiin karttoihin.

**Päälöydökset (aggregaatit, ei asiakastietoa):**
- SKILL.md:n oletuspolku "kirjoita XML suoraan" tuottaa systemaattisesti
  ohjeen omia CRITICAL-sääntöjä rikkovia kaavioita: legenda puuttui 16/20,
  negatiivisia koordinaatteja 7/20, tekstiylivuotoa 15/20 (42 % elementeistä),
  0 ankkuroitua reunaa. Parseri: 0/0/8 mutta 3 päällekkäisyyttä ja
  intersection-elementit kauas faseteistaan. 7/20 kaaviota korjattu käsin
  draw.io-desktopissa.
- Linkkisemantiikka vuotaa: ydinlinkkiverbi väärällä parilla 4/20,
  ei-ydinlinkki ydinlinkin tyylillä 8/20; ei influence-verbisanastoa;
  `edgy_generator.py` ei tulosta parserin `warnings`-listaa (kirjoitusvirhe
  `facet:`-arvossa putosi hiljaa identity-oletukseen).
- Visuaalisesti kauas virallisista kartoista (kontit, nimi/kuvaus-erottelu,
  intersection-sijoittelu). draw.io CLI ei ole ollut saatavilla yhdessäkään
  sessiossa → PDF-putki vaatii ihmisen.
- 0/6 toimituksessa `edgy-model.json` → `edgy-deep-dive` ei ajettavissa
  vanhoille malleille.

**Tuotos:** `docs/kehityssuunnitelma-2026-09.md` — P0–P3-toimenpiteet
hyväksymiskriteereineen, sprinttijako, mittarit lähtötasoineen. Ydinsuositus:
LLM → semanttinen malli → deterministinen layout → `edgy_lint.py`; suora XML
vain fallbackina lintin kanssa.

**Huomiot seuraaville agenteille:**
- Sprint 1 (lint + varoitusten tulostus + parivalidointi + yksi ydinlinkki-
  lähde) ennen layout-töitä: lint antaa lähtötason mittarit.
- Kun lint on olemassa, aja se yksityisessä repossa vanhoihin toimituksiin ja
  kirjaa tänne vain aggregaatit.

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
