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

### 2026-09-27 — Claude Code

**Assignment:** Sprint 1 of `docs/development-plan-2026-09.md` (P0.1–P0.6):
quality gate and a single generation path for the EDGY skills.

**Implemented:**
- **`edgy_lint.py`** (edgy-diagram/scripts): drawio linter for structure
  (flat `mxCell` tree, edge geometry, dangling source/target, duplicate
  ids), layout (negative / off-page coordinates with parent chains resolved,
  overlaps > 30 %, text-fit estimate), notation (legend, palette,
  intersection shapes) and semantics (core-link verb only on an allowed pair,
  non-core verb never in core-link style, vocabulary). Handles bare
  `mxGraphModel` and multi-page / compressed `mxfile`. 12 tests in
  `test_lint.py`. Run on the 20 reviewed deliveries it reproduces the
  review's findings (legend missing 16, negative coordinates, wrong pairs).
- **Generator-first default** in edgy-diagram, edgy-assessment (Phase 4) and
  edgy-deep-dive (lint step; pairwise stays hand-written until the generator
  supports it). "DO NOT use Python scripts" removed everywhere.
- **Parser warnings surfaced:** `edgy_generator.py` prints every warning to
  stderr; unknown `facet` / `map_type` is an error (exit 2, `--lenient` to
  override). Previously `facet: all-facets` silently became `identity`.
- **Core-link pair validation:** each verb carries its allowed (source,
  target) pairs — `requires`/`vaatii` for three pairs, `erscheint in` for
  two. A core verb on a wrong pair warns and is drawn as influence. The old
  `CORE_LINK_DIRECTIONS` mapped `requires` to one pair only, producing false
  warnings for `process → asset` and `product → capability`.
- **Influence vocabulary** (12 verbs × fi/en/fr/de, incl. `produces` for
  process → outcome and `measures` for outcome → purpose) with the rule "no
  core link fits → influence verb, never a new Link". Unknown verbs warn.
- **Single source:** `skills/_shared/edgy-core-links.yaml` →
  `tools/render-core-links.py` renders the SKILL.md tables (marker comments,
  five formats) and the generated `edgy_core_links.py`. `check.sh` fails if
  any copy is stale.
- `check.sh` gained `core-links-sync`, `edgy-tests`, `edgy-lint-tests` and
  `edgy-lint` (every shipped `.drawio` example, official maps excluded).

**Fixed on the way:** the skill's own example inputs used core-link verbs on
wrong pairs (`asset → capability: tukee`, `organisation → asset: omistaa`,
`brand → content: represents`, `organisation → purpose: toteuttaa`, …) and
two verbs outside any vocabulary. Corrected to proper core links or
influence verbs; all 17 `expected-*.drawio` regenerated and lint-clean. The
hand-written `acme-identity.drawio` (no legend, text overflow) is now
generated from a new `acme-identity.txt`. A DE collision (`erzeugt` was both
`creates` and `produces`) resolved with `bringt hervor`.

**Versions:** edgy-diagram 1.7.0 → 2.0.0 (default path changes),
edgy-assessment 1.5.1, edgy-deep-dive 1.0.1, edgy-framework 1.2.1.

**Notes for the next agents:**
- Sprint 2 (P0.7–P0.9): `mxfile` wrapper + `pages:`, pure-Python SVG
  preview, mandatory preview loop. The linter already accepts `mxfile`.
- E010 (core verb on a wrong pair) stays an error even though the parser
  draws such edges as influence: the fix belongs in the input.
- Adding a verb: edit the YAML, run the renderer, add a test.

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

**Revision 2 (2026-09-27):** merged written field feedback from a team that
used the skills for internal target-state architecture work (about 15
multi-page diagrams; feedback written against edgy-diagram 1.3 /
edgy-assessment 1.1). Added to the plan: mxfile wrapper + `pages:`, groups /
lanes / nesting with relative geometry, title + subtext + `id:` labels,
routing rules by diagram size, a clearly labelled transition overlay
(current → target, stroke only), per-map-type layout rules, strategy → EDGY
mapping and capability-formulation guidance in `edgy-framework`, and a
scoped `edgy-target-state` workflow. Explicitly scoped **out**: wiki/Confluence
delivery mechanics, transcript processing, Playwright as a dependency, a
second ADR skill; the parser's dashed Influence style already resolves one
feedback item. Section 3 of the plan records every in/out decision with its
rationale; Appendix A traces all 17 feedback items. The feedback document
itself is private and is not committed.

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
