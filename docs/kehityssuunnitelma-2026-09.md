# EDGY-skillien kehityssuunnitelma (2026-09)

Tämä suunnitelma perustuu **eri sessioissa tuotettujen EDGY-kaavioiden ja
-raporttien jälkikatselmukseen**. Aineisto käytiin läpi ohjelmallisesti
(muodot, värit, asettelu, linkkisemantiikka) ja visuaalisesti (render-
vertailu virallisiin EDGY 23 -karttoihin). Suunnitelma kertoo *mitä*
skilleissä pitää parantaa ja *miksi* — ei toista yksittäisten toimitusten
sisältöä.

> 🔒 Aineisto on peräisin yksityisistä toimeksiannoista. Tässä dokumentissa
> toimituksiin viitataan vain tunnuksilla **A–F** ja aggregaattilukuina.
> Ei asiakasnimiä, ei liiketoimintasisältöä (ks. `AGENT_LOG.md`:n
> tietosuojasääntö).

---

## 1. Katselmoitu aineisto

| Lähde | Määrä | Tuottaja | Skill |
|-------|------:|----------|-------|
| Assessment-toimitukset A–F | 6 kansiota | Claude Code (4), Mistral Vibe → Claude uudelleengenerointi (2) | `edgy-assessment` v1.0–1.2 |
| — facet-kaaviot (`*.drawio`) | 20 (+1 toimitus vain PNG-muodossa) | agentti kirjoitti XML:n suoraan | `edgy-diagram` |
| — syötteet (`*.txt`) | 24 | agentti | `edgy-diagram` |
| — analyysiraportit (`*-edgy-analysis.md`) | 6 (164–391 riviä) | agentti | `edgy-assessment` |
| Reframing-raportit | 2 | agentti | `edgy-framework` |
| `generated/`-kokeilut + ongelmaloki | 3 kaaviota, 1 loki | Mistral Vibe / Claude | `edgy-diagram` v1.0 |
| draw.io-autosave-varmuuskopiot (`.$*.bkp`) | 9 | ihminen (manuaalinen jälkieditointi) | — |
| Viralliset EDGY 23 -esimerkkikartat | 16 | Intersection Group | referenssi |
| Parserilla uudelleengeneroidut kaaviot samoista 24 syötteestä | 24 | `edgy_generator.py` v1.7 | vertailu |

Deep-dive-skillistä (`edgy-deep-dive`) ei ollut yhtään tuotosta katselmoitavana:
skill on uusi eikä yhdessäkään toimituksessa ollut sen edellyttämää
`edgy-model.json`-tiedostoa.

---

## 2. Päähavainnot

### 2.1 Kaksi rinnakkaista generointipolkua tuottavat eritasoista laatua

`edgy-diagram/SKILL.md` ohjeistaa: *"Generate draw.io XML directly — DO NOT
use Python scripts."* Samaan aikaan repossa on 1 266-rivinen `edgy_parser.py`,
jolla on 30 testiä (törmäystarkistus, dynaaminen leveys, legenda, ankkurit).
Vertailu samoista syötteistä:

| Mittari (tiedostoja, joissa ongelma) | Käsin kirjoitettu XML (n=20) | Parser (n=24) |
|--------------------------------------|-----------------------------:|--------------:|
| Legenda puuttuu (SKILL.md: *pakollinen*) | **16** | 0 |
| Negatiivisia koordinaatteja | **7** | 0 |
| Elementtejä sivun ulkopuolella | **6** | 0 |
| Teksti ei mahdu elementtiin¹ | **15** (121/287 elementtiä) | 8 (41/479) |
| Päällekkäisiä elementtejä | 0 | **3** |
| Reunoilla exit/entry-ankkurit | 0/20 | 24/24 |
| Ydinlinkin verbi väärällä elementtiparilla | 4 | 5² |
| Ei-ydinlinkki piirretty ydinlinkin tyylillä | **8** | 0 |

¹ Heuristiikka: tekstin pituus vs. laatikon pinta-ala. Käsin kirjoitetuissa
kaavioissa käytettiin kiinteää 120×60 / 140×60 -kokoa vaikka nimi + kuvaus
oli 60–120 merkkiä.
² Parser ei validoi paria, vain suuntaa — sama syötevirhe siirtyy läpi.

**Lisäksi:** 7/20 toimituskaaviota on tallennettu draw.io-desktopilla
(`<mxfile host="Electron">`), ja autosave-varmuuskopiot osoittavat että
ihminen siirsi 4–20 elementtiä per kaavio käsin generoinnin jälkeen.
Manuaalinen korjauskierros on siis ollut osa jokaista toimitusta.

**Johtopäätös:** LLM:n suoraan kirjoittama XML rikkoo säännöllisesti juuri
ne säännöt, jotka SKILL.md luettelee "CRITICAL"-otsikon alla (legenda,
koordinaatit, tekstin mahtuminen). Parser noudattaa niitä mekaanisesti mutta
sen asettelu on tylsä ja intersection-elementit päätyvät kauas faseteistaan.
Nykyinen "kirjoita XML suoraan" -oletus on väärä; oikea työnjako on
**LLM → semanttinen malli → deterministinen layout → lint**.

### 2.2 Linkkisemantiikka vuotaa

- Ydinlinkin verbejä (`vaatii`, `toteuttaa`, `tavoittelee` …) on käytetty
  pareilla, jotka eivät ole EDGY 23:n 24 ydinlinkin joukossa (4 käsin
  kirjoitettua kaaviota, 5 parseroitua; sama syöte → sama virhe).
- Vapaita vaikutusverbejä (`mahdollistaa`, `ohjaa`, `tekee`, `tarjoaa`,
  `hallinnoi`, `heijastaa`) on piirretty ydinlinkin yhtenäisellä nuolella
  8 kaaviossa. Skillissä ei ole sanastoa hyväksytyille influence-verbeille,
  joten agentti keksii ne joka kerta.
- Yhdessä toimituksessa ä/ö on tuplaeskapoitu (`&amp;auml;`) → verbi
  `herättää` ei tunnistu koneellisesti ydinlinkiksi, vaikka näkyy oikein.
- Syötteessä `facet: all-facets` (kirjoitusvirhe) → parser putosi hiljaa
  `identity`-oletukseen. Parser kerää varoituksen `warnings`-listaan, mutta
  **`edgy_generator.py` ei koskaan tulosta sitä**.
- Ydinlinkkitaulukko on kopioitu neljään SKILL.md:hen (4 × 24 riviä). Ne
  ovat nyt synkassa, mutta jokainen muutos pitää tehdä neljästi.

### 2.3 Visuaalinen laatu jää kauas virallisista kartoista

Viralliset EDGY 23 -kartat (`examples/official/`) ovat 11/16 tapauksessa
**layout-only**: merkitys syntyy värillisistä ryhmäkontteista ja
kolmitasoisesta sisäkkäisyydestä, ei nuolista. Toimituskaaviot ovat
päinvastaisia: 5–24 elementtiä ja 8–20 pitkää, koko kaavion halki risteävää
nuolta ilman kontteja. Erot:

| Piirre | Viralliset kartat | Toimituskaaviot |
|--------|-------------------|-----------------|
| Facet-kontit / sarakeotsikot | aina | 4/20 (lisätty käsin) |
| Lehtielementin koko | 130×60, fontti 14 | 120×60, fontti 12, teksti ylivuotaa |
| Nimi vs. kuvaus | vain nimi laatikossa | `"Nimi - Kuvaus [tagit] {metriikat}"` samassa labelissa |
| Nuolet | vähän, lyhyitä, T-haaraisia | paljon, pitkiä, risteäviä, labelit shape-päällä |
| Intersection-elementit | fasettien *välissä* | kaavion alareunassa → 20 nuolta koko kaavion halki |

Labelikäytäntö vaihtelee toimituksittain: `"Nimi - Kuvaus"`, `"Tyyppi Nimi"`,
`"Nimi | tagit"`. Yhtenäistä sääntöä ei ole.

### 2.4 Renderöinti ei toimi agenttiympäristöissä

draw.io CLI puuttui kaikista katselmoiduista sessioista (myös tästä).
PNG-viennit onnistuivat vain yhdessä toimituksessa (ihmisen koneella).
`edgy-assessment` Phase "PDF Report Generation" vaatii PNG-kaaviot
`--preset presentation`, joten PDF-putki on de facto rikki ilman ihmistä.
PlantUML-polku (`<edgy/edgy>` stdlib) on toteutettu, mutta sitä ei ole
kytketty assessment-workflowhun.

### 2.5 Heikommat mallit epäonnistuvat skillillä kokonaan

`generated/AGENT_LOG_EDGY_DIAGRAM_ISSUE.md` dokumentoi Mistral Vibe -session,
joka tuotti (a) tyhjiä 324 tavun tiedostoja, (b) `mxfile`-wrapperin
`mxStyle`-lapsilla, (c) lopulta XML:n jossa `mxCell`-solut ovat **sisäkkäin**
`id="1"`-solun alla — juuri se rakenne, jonka SKILL.md kieltää — eikä agentti
tunnistanut virhettä kymmenen yrityksen jälkeen. Kaksi toimitusta (A, B)
piti generoida kokonaan uudelleen Claude Codella.

Skill nojaa siihen, että agentti *lukee* ja *noudattaa* 978 riviä ohjetta.
Ei ole yhtään ajettavaa tarkistusta, joka kertoisi agentille "tämä tiedosto
on rikki" — paitsi `ls -la` tavukoko.

### 2.6 Assessment-tuotosten rakenne on ajan myötä eriytynyt

- 3/6 raporttia on ilman PDF-preamblea (tehty ennen v1.3.0:n lukittua
  layoutia); 3/6 preamblella. Vanhaa mallia ei voi ajaa uudella putkella.
- **0/6** toimituksessa on `edgy-model.json` → `edgy-deep-dive` ei ole
  käytettävissä yhdellekään olemassa olevalle asiakkaalle.
- Raporttien pituus 164–391 riviä; kaikilla sama 9-osioinen runko (hyvä),
  mutta osio 10 (ehdotetut jatkoanalyysit) puuttuu kaikista.
- Reframing-raportit (2 kpl) noudattavat `edgy-framework`-templatea hyvin;
  toisessa on lisätty ylimääräinen "Strategiset valinnat" -osio — templatessa
  voisi olla valinnainen paikka sille.

### 2.7 Dokumentaation koko ja päällekkäisyys

`edgy-diagram/SKILL.md` on 978 riviä (aiempi tavoite < 500). Legenda-XML
(17 solua) on kopioitu sanasta sanaan sekä `edgy-diagram`- että
`edgy-assessment`-skilliin. Sama pätee väripalettiin ja muotosääntöihin.
Kolme dokumenttia neljästä sisältää ohjeen "generoi XML suoraan" ja yksi
ohjeen "käytä parseria" — agentti saa ristiriitaisen signaalin.

---

## 3. Tavoitetila

1. **Yksi generointipolku:** agentti tuottaa *semanttisen mallin*
   (TXT/JSON), deterministinen työkalu tuottaa XML:n, ja lint hylkää
   virheelliset tiedostot ennen toimitusta. LLM ei enää sijoittele
   pikselikoordinaatteja.
2. **Kaaviot näyttävät EDGY 23 -kartoilta:** facet-kontit, nimi erillään
   kuvauksesta, intersection-elementit fasettien välissä, ydinlinkit
   lyhyinä ja oikein tyyliteltyinä.
3. **Koko putki toimii ilman ihmistä ja ilman draw.io-desktopia** (SVG/PNG
   syntyy Pythonilla tai PlantUML:llä).
4. **Yksi totuus ydinlinkeistä** — sanasto yhdessä tiedostossa, josta
   taulukot ja validointi johdetaan.
5. **Olemassa olevat toimitukset voi nostaa uudelle tasolle** ilman
   uudelleenanalyysiä (model extraction + regenerointi).

---

## 4. Toimenpiteet

Prioriteetit: **P0** = korjaa toistuvan laatuvirheen, **P1** = nostaa
lopputuloksen virallisten karttojen tasolle, **P2** = laajentaa
käyttökelpoisuutta, **P3** = siistintä.

### P0 — Laatuportti ja yksi generointipolku (edgy-diagram 1.7 → 2.0)

| # | Toimenpide | Perustelu (havainto) | Hyväksymiskriteeri |
|---|-----------|----------------------|--------------------|
| P0.1 | **`scripts/edgy_lint.py`** — riippumaton drawio-linter: XML hyvinmuodostuneisuus, ei sisäkkäisiä `mxCell`, reunoilla `mxGeometry`, ei negatiivisia/sivun ulkopuolisia koordinaatteja, ei päällekkäisyyksiä, tekstin mahtuvuus, legenda löytyy, värit paletista, muoto vastaa perustyyppiä, ydinlinkkiverbi vain sallitulla parilla, ei-ydinlinkki ei saa `endArrow=classic;endFill=1`. Tuottaa `file:line`-tyyliset löydökset ja exit code ≠ 0. | 2.1, 2.2, 2.5 | Ajettuna katselmoituihin 20 kaavioon löytää kaikki taulukon 2.1 virheet; ajettuna `examples/expected-*.drawio` → 0 virhettä; lisätty `tools/check.sh`:iin ja CI:hin. |
| P0.2 | **Käännä SKILL.md:n oletus:** ensisijainen polku on `edgy_generator.py` (+ lint). Suora XML sallitaan vain fallbackina, ja silloinkin `edgy_lint.py` on pakollinen ennen toimitusta. Sama muutos `edgy-assessment` Phase 4:ään ja `edgy-deep-dive` Phase 4:ään. | 2.1, 2.5, 2.7 | Kolmessa SKILL.md:ssä ei enää lukua "DO NOT use Python scripts"; workflow-kaavio: TXT → generator → lint → (render). |
| P0.3 | **Tulosta parserin varoitukset** generatorissa (`parser.warnings`) ja tee tuntemattomasta `facet`/`map_type`-arvosta virhe (exit 2) oletusarvon sijaan. | 2.2 | `facet: all-facets` → selkeä virhe, ei hiljaista identity-kaaviota. |
| P0.4 | **Ydinlinkkien parivalidointi parseriin:** `CORE_LINK_DIRECTIONS` laajennetaan sallituiksi (lähdetyyppi, kohdetyyppi, verbi) -kolmikoiksi kaikilla neljällä kielellä; väärä pari → varoitus + relaatio piirretään influence-tyylillä, ei ydinlinkkinä. | 2.2 | Testi: `organisation -> asset: "omistaa"` → varoitus, katkoviiva. |
| P0.5 | **Influence-verbisanasto** (`INFLUENCE_RELATIONSHIPS`, fi/en/fr/de: mahdollistaa, ohjaa, tukee*, tarjoaa, hallinnoi, heijastaa, vahvistaa …) SKILL.md:hen ja parseriin, jotta agentti valitsee listasta eikä keksi. (*`tukee` on myös ydinlinkki brand→task — dokumentoi ero.) | 2.2 | Sanasto SKILL.md:ssä; lint varoittaa sanaston ulkopuolisesta verbistä. |
| P0.6 | **Yksi lähde ydinlinkeille:** `skills/_shared/edgy-core-links.yaml` (24 riviä × 4 kieltä + sallitut parit). SKILL.md-taulukot generoidaan siitä (`tools/render-core-links.py`) ja `check.sh` varmistaa synkan. | 2.2, 2.7 | Neljä taulukkoa identtisiä koneellisesti; muutos yhdessä paikassa. |

### P1 — Visuaalinen laatu virallisten karttojen tasolle (edgy-diagram 2.x)

| # | Toimenpide | Perustelu | Hyväksymiskriteeri |
|---|-----------|-----------|--------------------|
| P1.1 | **Facet-kontit `facet: all` -asetteluun:** kolme värillistä ryhmäkonttia (Identity / Architecture / Experience) otsikoilla, lehtielementit konttien sisällä (`parent`-viittaus), kontin koko sisällön mukaan. Sama `facet: identity/architecture/experience` -kaavioille (1 kontti + intersection-kontti). | 2.3 | Render vastaa `official/decoded/PATTERNS.md`:n konttityyliä; `expected-*.drawio` regeneroitu. |
| P1.2 | **Intersection-elementit fasettien väliin:** Organisation Identity- ja Architecture-sarakkeiden väliin pystysuuntaan keskitettynä, Product Architecture–Experience-väliin, Brand Identity–Experience-siltana (ylä- tai alareuna). Tavoite: ydinlinkit lyhenevät ja risteävät vähemmän. | 2.3 | Keskimääräinen ydinlinkin pituus `all`-kaaviossa pienenee ≥ 40 % katselmoiduilla syötteillä; ei nuolia, jotka ylittävät koko sivun leveyden. |
| P1.3 | **Label-standardi:** `<b>Nimi</b><br><font size=1>Kuvaus</font>` + tagit omalle riville pienellä (kuten toimituksen PNG-referenssissä). Leveys lasketaan *nimen* pituudesta, korkeus kuvausrivien määrästä. Kielletään `"Tyyppi Nimi"` -etuliite (tyyppi näkyy muodosta ja väristä). | 2.3, 2.1 | Lint: 0 tekstiylivuotoa 24 katselmoidulla syötteellä; fontti 14 nimelle. |
| P1.4 | **Reunojen reititys:** ankkurit hajautetaan jo nyt; lisäksi label sijoitetaan reunan keskipisteen sijaan lähelle kohdepäätä valkoisella taustalla (`labelBackgroundColor=#ffffff`), ja saman parin monta reunaa yhdistetään yhdeksi labeliksi `a / b`. | 2.3 | Visuaalinen tarkistus 3 katselmoidulla `all`-kaaviolla: labelit eivät peitä elementtejä. |
| P1.5 | **Päällekkäisyyskorjaus intersection-riville:** parserin 3 päällekkäisyyttä syntyivät kun Product-elementtejä oli 4–6 (yksi rivi ei riitä). Rivitys 3/rivi + törmäystarkistus myös intersection-elementeille. | 2.1 | `test_edgy.py`: uusi testi 6 productilla → 0 päällekkäisyyttä. |
| P1.6 | **Pure-Python SVG-vienti** (`--format svg --engine native`): approksimoiva renderöijä (rect/rounded/pentagon/person, tekstin rivitys, suorat reunat + labelit). Riittää PDF-upotukseen ja agentin *itsetarkastukseen* (screenshot Chromium-headlessillä on saatavilla useimmissa agenttiympäristöissä). draw.io CLI pysyy laatuvientinä kun se on. | 2.4 | `edgy_generator.py input.txt --format svg` toimii ilman draw.io:ta/Javaa; assessment-PDF syntyy ilman ihmistä. |
| P1.7 | **Näytä kaavio agentille ennen toimitusta:** SKILL.md:hen vaihe "renderöi SVG → katso → korjaa syötettä" (ei XML:ää). | 2.1 | Ohje + esimerkki; lint + render molemmat check-listalla. |

### P2 — Assessment- ja deep-dive-putken eheys (edgy-assessment 1.5 → 1.6, edgy-deep-dive 1.0 → 1.1)

| # | Toimenpide | Perustelu | Hyväksymiskriteeri |
|---|-----------|-----------|--------------------|
| P2.1 | **`edgy-model.json`-ekstraktio vanhoista toimituksista:** `edgy-assessment`-skilliin tila `mode: extract-model`, joka lukee olemassa olevan analyysi-MD:n + 4 TXT:tä ja tuottaa mallin (elementit, aktiiviset ydinlinkit, koherenssi). Avaa deep-diven kaikille 6 nykyiselle toimitukselle. | 2.6 | `sample-model.json`-skeeman mukainen tuloste; `edgy-deep-dive` ajettavissa ekstraktoidulle mallille. |
| P2.2 | **JSON-skeema `edgy-model.json`:lle** (`assets/edgy-model.schema.json`) + validointi `check.sh`:ssä esimerkkimallille. Deep-dive validoi syötteensä skeemaa vasten Phase 1:ssä. | 2.6 | Rikkinäinen malli → selkeä virhe, ei hallusinoituja elementtejä. |
| P2.3 | **TXT ⇄ model.json -johdettavuus:** 4 facet-TXT:tä generoidaan mallista (`edgy_model_to_txt.py`) — ei käsin. Poistaa syöte/raportti-ristiriidat (esim. raportissa 5 kyvykkyyttä, kaaviossa 4). | 2.6, 2.2 | Assessment Phase 3 = skriptiajo; lint tarkistaa että TXT:n elementit ⊆ mallin elementit. |
| P2.4 | **Osio 10 (ehdotetut jatkoanalyysit) pakolliseksi quality gateen** grep-tarkistuksena, kuten preamblen tarkistukset. | 2.6 | `grep -q "## Ehdotetut jatkoanalyysit\|## Suggested deep-dive"` gate. |
| P2.5 | **Reframing-template:** valinnainen osio "Strategiset valinnat ja vaihtoehdot" (fi/en/fr/de) — käytetty jo kentällä. | 2.6 | Template + esimerkki päivitetty. |
| P2.6 | **PlantUML-polku assessment-workflowhun** vaihtoehtona SVG-natiiville, kun Java on saatavilla (`--engine plantuml`). | 2.4 | Phase 4 kuvaa kolme engineä ja valintajärjestyksen. |

### P3 — Dokumentaation siistintä ja ylläpidettävyys

| # | Toimenpide | Perustelu | Hyväksymiskriteeri |
|---|-----------|-----------|--------------------|
| P3.1 | `edgy-diagram/SKILL.md` 978 → < 500 riviä: siirrä legenda-XML, pairwise-XML ja map-type-ASCII-kuvat `references/`-tiedostoihin, joihin SKILL.md linkittää. | 2.7 | Validator OK; ohje mahtuu yhteen kontekstilukuun. |
| P3.2 | Poista legenda-XML:n ja väripaletin duplikaatit `edgy-assessment/SKILL.md`:stä → viittaus `edgy-diagram`iin. | 2.7 | Yksi kopio. |
| P3.3 | **Eval-setti:** 6 anonymisoitua syötettä (Acme Oy / Globex Oy / Nordia Transit) `examples/eval/`, joilla lint + render ajetaan CI:ssä; regressiomittarit (legenda, ylivuoto, päällekkäisyys, väärät parit) raportoidaan taulukkona. | 2.1 | CI-job `edgy-eval` vihreä; mittarit näkyvissä PR:ssä. |
| P3.4 | `AGENT_LOG`-käytäntö: jokaisesta toimituksesta kirjataan *lint-tulos ennen ja jälkeen manuaalikorjauksen* (anonyymisti), jotta laatutrendi näkyy. | 2.1 | Lokimalli CONTRIBUTING.md:ssä. |
| P3.5 | Poista tuplaeskapointi-riski: parser ja SKILL.md ohjeistavat `html=1`-labeleissa vain `&amp; &lt; &gt; &quot;` -eskapoinnin; ä/ö kirjoitetaan UTF-8:na. Lint varoittaa `&amp;[a-z]+;`-kuvioista. | 2.2 | Lint-sääntö + testi. |

---

## 5. Toteutusjärjestys ja arvio

| Vaihe | Sisältö | Arvio | Versiot |
|-------|---------|-------|---------|
| Sprint 1 | P0.1–P0.6 | 3–4 työpäivää | edgy-diagram 2.0.0 (breaking: oletuspolku vaihtuu), edgy-assessment 1.5.1, edgy-deep-dive 1.0.1 |
| Sprint 2 | P1.1–P1.5 | 4–5 työpäivää | edgy-diagram 2.1.0, `expected-*.drawio` regeneroitu |
| Sprint 3 | P1.6–P1.7, P2.6 | 2–3 työpäivää | edgy-diagram 2.2.0 |
| Sprint 4 | P2.1–P2.5 | 3–4 työpäivää | edgy-assessment 1.6.0, edgy-deep-dive 1.1.0 |
| Sprint 5 | P3.1–P3.5 | 2 työpäivää | dokumentaatio, CI |

Sprint 1 kannattaa tehdä ensin ja ajaa lint kaikkiin vanhoihin
toimituksiin (yksityisessä repossa): se antaa lähtötason mittarit, joihin
sprintit 2–4 verrataan.

---

## 6. Onnistumisen mittarit

Mitataan `edgy_lint.py`:llä anonymisoidulla eval-setillä (P3.3) ja uusilla
toimituksilla:

| Mittari | Lähtötaso (katselmus) | Tavoite |
|---------|----------------------:|--------:|
| Kaavioita ilman legendaa | 80 % | 0 % |
| Kaavioita, joissa negatiivisia / sivun ulkopuolisia koordinaatteja | 35 % / 30 % | 0 % |
| Elementtejä, joiden teksti ei mahdu | 42 % | < 2 % |
| Ydinlinkkiverbi väärällä parilla | 20 % kaavioista | 0 % (lint estää) |
| Ei-ydinlinkki ydinlinkin tyylillä | 40 % kaavioista | 0 % |
| Manuaalisesti draw.io:ssa korjattuja toimituskaavioita | 35 % | < 10 % |
| Toimituksia, joissa `edgy-model.json` | 0/6 | 100 % uusista; 6/6 ekstraktoituna |
| PDF-raportti syntyy ilman ihmistä ja draw.io-desktopia | ei | kyllä |

---

## 7. Riskit ja rajaukset

- **Breaking change (P0.2):** oletuspolun vaihto vaatii, että parseri
  kattaa kaikki tapaukset, joita agentit ovat tähän asti tehneet käsin
  (otsikot, kontit, pairwise). Pairwise-layout lisätään parseriin ennen
  kuin `edgy-deep-dive` siirretään pois suorasta XML:stä.
- **Konttien `parent`-viittaus** muuttaa koordinaatit suhteellisiksi;
  lint ja SVG-renderöijä on toteutettava tämä huomioiden (P0.1 ennen P1.1).
- **Virallisten karttojen tyyli on layout-only**; facet-kaaviomme tarvitsevat
  silti ydinlinkit. Kompromissi: kontit + vain ydinlinkit näkyvinä, influence-
  linkit oletuksena piilossa (`--show-influence` näyttää).
- **Yksityisyys:** eval-setti (P3.3) tehdään fiktiivisistä yrityksistä;
  lint-ajoja oikeisiin toimituksiin tehdään vain yksityisessä repossa, ja
  julkiseen lokiin kirjataan vain aggregaatit.
- Tämä suunnitelma ei kata `archimate`- tai `c4`-skillejä, joilla on omat
  EDGY-mappauksensa upstreamissa; niiden yhteensovitus ydinlinkkisanastoon
  (P0.6) on erillinen työ.
