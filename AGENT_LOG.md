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

### 2026-10-04 — Claude Code (Sprint 11: map_type triad, purpose-tree layout)

**Assignment:** development-plan-2026-10 P3.1–P3.4. The planned ring for
large models, and a purpose tree whose branches do not cross its children.

**Done:**
- `map_type: triad` (EDGY extension, opt-in) in `edgy_parser.py`: a slot
  table per facet (`facet: all` ring 1340 px wide; single-facet variants
  for identity / architecture / experience), one *primary* element per
  type (`{primary: true}`, else the first of its type; several → warning,
  first wins), straight `edgeStyle=none` core links drawn border to
  border, two intersection links detoured along the page edge with fixed
  ports and waypoints, a default label shift per slot pair (overridable
  with the new `{label_dx, label_dy}` relationship options, emitted as
  `<mxPoint as="offset">`), "Further <type>" panels (grey containers,
  chips sized by measured text, 1–4 columns) for the non-primary elements,
  links into a panel reported as a warning with the pair names — never
  dropped silently. `legend: strip` by default, `legend: box` wins when
  given; `group:` / `lane:` / `layout_from:` are ignored with a warning.
  Collision resolution and grid snapping are bypassed for the ring.
- `_layout_purpose` rewritten as a tidy tree: parent centred over its
  children, a 90 px corridor between rows, children entered from the top
  (`from: bottom, to: top` set on tree relationships), Outcomes in their
  own row beneath the purpose they measure (`from: top, to: bottom`), a
  wider child gap when a parent's own Outcomes rise through the child row,
  `label: source` where routes share a corridor. Fixture F5: 13 visual
  findings → 0.
- Examples `triad-all-facets.txt` (12 primaries, 23 further, all 24 core
  links, 2 reported links) and `triad-architecture.txt` (the 19-element
  field case as a ring + panels); both lint **0 errors / 0 warnings
  including W111–W114**. `references/map-types.md` has the slot tables.
  SKILL.md 2.5.0. 6 new tests.

**Regression guard:** without `map_type: triad` / `legend:`, every shipped
example regenerates byte-identical to Sprint 10 except the two purpose
maps, which change by design (P3.2).

**Remaining gap, recorded honestly:** the shipped examples that use the
default facet, lane and reference layouts still carry 48 W111 / 26 W112 /
1 W113 (10 files). Those layouts were not in this plan's scope; the
guidance now says to use `triad` for facet maps with many links, and the
eval set measures the rest. `check.sh` therefore keeps "0 errors" for
shipped examples; `--warnings-as-errors` is the bar for triad, purpose and
the fixtures F1/F5 (tested).

---

### 2026-10-04 — Claude Code (Sprint 10: text metrics, publication bounds, strip legend, --scale)

**Assignment:** development-plan-2026-10 P2.1–P2.4.

**Done:**
- `scripts/edgy_text.py` (stdlib): per-glyph advance widths of Helvetica and
  Helvetica-Bold (Adobe Core 14 metrics, which Arial matches), accents fall
  back to the base letter, `measure` / `wrap` / `lines_needed`; Pillow with
  a Liberation/Arimo/Arial font is used when present, never required
  (`EDGY_TEXT_TABLE_ONLY=1` forces the tables). The generator sizes boxes
  from the measured 14 px bold name (pentagon tip excluded from the text
  area) and wraps descriptions at 9 px normal; the preview wraps with the
  same function; W101 measures the same way and honours per-line
  `font-weight`. Description rows no longer inherit the cell's bold
  (`label_lines` returns an explicit weight per line) — F4.
- `--publication` (renderer, generator `--preview` / `--engine native`):
  viewBox from the bounding box of shapes, full routes, label boxes and
  legend plus a 24 px margin, no editor-page frame; an orientation hint
  (`landscape` / `portrait` / `square`) per page — F6.
- `legend: strip` input option: one 24 px band along the bottom (title, six
  short chips, four line samples; a second row when the page is narrow, a
  third for the transition overlay); the page height becomes content +
  band instead of the 900 px editor minimum. E009's structural detection is
  satisfied by construction. Default stays `box`.
- `edgy_lint.py --scale F` → W115 when a title, description or relation
  label falls below 6 pt (px × F × 0.75) at the report scale.
- Tests: 2 render, 1 lint, 2 structure; SKILL.md documents all four.

**Regenerated once, as planned:** all 26 shipped `expected-*.drawio`
changed because box widths now follow measured text (mostly 10–30 px
narrower or wider, heights follow real wrapping). Every file still lints 0
errors; previews of the facet map, reference architecture, F4 fixture and
a strip-legend journey were looked at. Visual-rule aggregates after
regeneration: eval set 46 (reference architecture, was 52) / 79 / 13 / 8 /
6 / 1 — unchanged in kind, the layout work in Sprint 11 is what moves
them.

**Decisions:** glyph tables over a font dependency (the repo stays
stdlib-only and deterministic across machines); overflow policy is "widen
to 280 px, then wrap, then W101" — text is never scaled down. W115 reports
one finding per cell with its smallest text, so a scaled-down map yields
one line per box, not one per row.

---

### 2026-10-04 — Claude Code (Sprint 9: shared geometry, visual lint rules)

**Assignment:** development-plan-2026-10 P1.1–P1.4. One resolved geometry
for generator, preview and lint; fix the two renderer defects it exposed;
add the visual rules the field case slipped through.

**Done:**
- `scripts/edgy_geometry.py` (stdlib): absolute boxes through the parent
  chain, port distribution, side choice, border points, orthogonal route
  normalisation (end segments perpendicular to their side, an OUTWARD step
  when a waypoint lies behind the port, duplicates and *between*-collinear
  points removed — an out-and-back spike is a real detour and stays), label
  position as a fraction of arc length with perpendicular and absolute
  offsets, Liang–Barsky clipping, bounding boxes. 17 tests.
- `edgy_render.py` uses it: F1 (diagonal end segments with waypoints) and
  F2 (`label: source|middle|target` all drawn at the midpoint) are fixed;
  `edgeStyle=none` edges run border to border; `<mxPoint as="offset">` and
  relative `y` move labels. The parser takes `distribute()` and the side
  choice from the same module.
- `edgy_lint.py` W111–W114 on that geometry, `--visual` JSON with cell ids
  and coordinates, `Finding.coords`. Containers never count for W111; a
  one-verb fan from one source is a bus for W113.
- Tests: 4 render, 7 lint, `edgy-geometry-tests` step in `check.sh`.

**Baseline → after, aggregates.** Shipped examples (26 files): structural
0 errors / 0 warnings before and after; visual rules now report **83
warnings** (W111 × 49, W112 × 33, W113 × 1) in 10 files. Eval fixtures:
large single-facet map 79 visual findings, F5 purpose tree 13, F2 8, F4 6,
F1 1 (W113 — the diagonal segments themselves are gone). The generator's
output for every shipped example is byte-identical to before this sprint
(the parser refactor changed no behaviour), so the 83 are the *existing*
pictures measured honestly for the first time.

**Decision:** the shipped examples are not made visually clean in this
sprint. Most findings come from the single-column facet layout and the
purpose tree, which Sprint 11 replaces (`triad`, purpose re-layout); fixing
the inputs now would be redone. `check.sh` keeps "0 errors" for shipped
examples until then; `--warnings-as-errors` becomes the bar in Sprint 11.

---

### 2026-10-04 — Claude Code (Sprint 8: release hygiene, regression fixtures)

**Assignment:** `docs/development-plan-2026-10.md` P0.2–P0.3. Make the
findings of the two field reviews reproducible before changing any
algorithm, and write down how a release is cut so the tag mistake (v1.0.0
and v2.0.0 resolving to the same commit) cannot repeat.

**Done:**
- `CONTRIBUTING.md` — "Releasing (maintainers)": tag the merge commit after
  the merge, verify with `git ls-remote --tags`, Release notes = CHANGELOG
  entry, how to fix a tag that points at the wrong commit.
- Five fictional (Acme Oy) fixtures in `examples/eval/`, each reproducing
  one finding on the current generator/renderer/linter:
  F1 distributed ports + `via:` waypoints on all four sides (diagonal end
  segments in the native preview), F2 three label positions (all rendered
  at the midpoint), F4 long bold titles in all three shapes, F5 purpose tree
  with 4 children + 4 Outcomes + a second level (parent above the leftmost
  child, branches through sibling boxes), and `large-architecture-facet`
  (19 elements in one facet, 30 core links — edges through boxes, labels on
  boxes). The fixtures are in `edgy-eval.py`'s default set.
- `tools/edgy-eval.py` prints two new columns: **H/W** (page height / width
  of the worst page) and **Visual** (sum of W111–W115 once the linter has
  them).

**Baseline (before Sprint 9), aggregates:** 12 eval inputs, 0 generator
errors, 0 lint errors, 0 lint warnings — including the five fixtures that
are visibly defective in their previews. H/W: 0.36–0.75 (no input above
1.0; the single-facet layout is a grid, so the field case's 1.4 ratio comes
from a column layout in `facet: all` with one dominant facet, covered by
the triad work in Sprint 11). Visual: 0 everywhere, because the rules do
not exist yet — that is the gap Sprint 9 closes.

**Decisions:** the large single-facet fixture is named by what it is
(`large-architecture-facet.txt`), not by the layout that will fix it; the
`triad` examples come with Sprint 11. Fixture waypoints are computed from
the generated positions (ids add a 9 px line, so boxes are 120 × 80 and
rows sit at y = 80 / 200 / 320) and documented in the file header.

---

### 2026-10-02 — Claude Code

**Assignment:** Address the Copilot review on PR #2 (12 threads + one
summary-only finding). Every finding was reproduced before fixing; each fix
has a regression test.

**Fixed:**
- `edgy_lint.py`: legend detection is structural (legend title text cell +
  ≥ 3 palette chips + ≥ 1 free-standing line sample); an element *named*
  "Legend" or a cell id starting with `leg` no longer satisfies E009 nor
  hides an element from linting. Base elements (people / activity /
  outcome / object, white fill + dark or overlay stroke, or the person
  shape) are now linted like facet elements. Cell classification lives in
  `classify_cells()` and is shared with `tools/edgy-eval.py`. `--json`
  writes only JSON to stdout (summary to stderr). E005 logic simplified.
- `edgy_document.unique_slugs()`: collision-free page ids (`foo-3, foo,
  foo` → `foo-3, foo, foo-2`) used for `diagram/@id`, per-page preview
  files and per-page PlantUML outputs.
- `edgy_generator.py`: `--engine plantuml` renders every page
  (`<stem>-<page>.<ext>`) instead of the first only; `--preview` failure
  exits 3 instead of 0. Skill metadata lists `native` as an engine.
- `tools/edgy-eval.py`: parses the whole JSON report (it parsed one line,
  so lint errors were never counted) and counts elements with the linter's
  classification (the legend background was counted). Unreadable lint
  output now fails the eval.
- `tools/validate-edgy-model.py`: semantic checks are type-guarded, invalid
  items produce findings instead of a traceback.
- `edgy_model_to_txt.py`: exits with an explanation when the vocabulary
  module is missing or empty instead of silently writing TXTs without core
  links.
- `tools/render-core-links.py`: unpaired begin/end markers and listed files
  without markers are errors (they used to be skipped silently).
- `edgy-target-state`: phase selection covers phases 1–9.

**Not changed:** the AGENT_LOG nits (version numbers and example counts in
older entries) — log entries record the state at the time they were written.

**Validation:** 16 lint tests, 15 render tests, 8 new tool tests
(`tools/test_edgy_tools.py`, check.sh step `edgy-tool-tests`); all shipped
examples regenerate byte-identical and lint-clean; eval set 0 errors with
correct element counts. edgy-diagram 2.4.1, edgy-target-state 1.0.1.

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

**Sprint 2 (P0.7–P0.9), same day:**
- **`pages:` input + `mxfile` wrapper** (`edgy_document.py`): everything
  before `pages:` is a document-level default; each `- name:` page is parsed
  by its own parser (own layout and legend) and becomes one uncompressed
  `<diagram name="…">`. Single-page input also gets the wrapper by default
  (`--bare` restores the bare `mxGraphModel`). Output carries no timestamps
  or random ids, so regenerated files diff cleanly. Warnings are prefixed
  with the page name. Example: `examples/multipage-map.txt`.
- **CLI-free preview** (`edgy_render.py`): pure-Python SVG per page
  (containers via parent chains, pentagons, person, rounded corners from
  `arcSize`, html labels with word-wrap, exit/entry anchors, waypoints,
  orthogonal bends, per-colour arrow markers, dashed influence, legend
  chips); PNG through a headless Chromium/Chrome when one is found
  (`$EDGY_CHROMIUM`, PATH, Playwright browser dir, common install paths).
  Wired into the generator as `--preview` and `--engine native`
  (svg/png). Documented as approximate — the draw.io CLI stays the
  publication export.
- **Mandatory preview loop** in edgy-diagram (new section with a
  six-point checklist), edgy-assessment Phase 4 + quality gate, and
  edgy-deep-dive Phase 4. Rule: fix the input, never the XML.
- 11 new tests in `test_render.py`; `check.sh` step `edgy-render-tests`.
  All 18 shipped examples regenerated in `mxfile` form and lint-clean.
- Versions: edgy-diagram 2.1.0, edgy-assessment 1.5.2, edgy-deep-dive 1.0.2.

**Sprint 3 (P1.1–P1.7), 2026-10-01 — edgy-diagram 2.2.0:**
- **Groups, lanes, nesting:** `group:` → `container=1` with children as
  `parent`-referenced cells in relative coordinates (grid 2–4 columns, or a
  tidy tree when the members have tree relationships); `lane:` → borderless
  band, members at root level, edges between non-adjacent members of a row
  routed over the top. Groups are placed in rows; lanes stack.
- **Facet containers:** `facet: all` now draws Identity / Architecture /
  Experience containers with Organisation between the first two, Product
  between the last two and Brand below as the Identity ↔ Experience bridge
  (review A finding 2.3: intersection elements used to sit at the bottom
  and pull 20 edges across the canvas). Single facet: one container + the
  intersection elements below, wrapped three per row (fixes the parser's
  overlaps with 4–6 products).
- **Label standard:** `<b>Name</b>` + small subtext (`[ID]` + description)
  + tags/metrics line; width follows the *name*, height the subtext.
  `"Name - Description"` and `"Name | subtext"` both work; reserved metric
  keys `id`, `change`, `size` (S/M/L), `highlight`. Name matching uses the
  part before the separator.
- **Relationship options** `{from, to, via, change, label}`; duplicate
  edges between a pair merge into `verb1 / verb2`.
- **Transition overlay** (documented as an EDGY extension): `{change: keep|
  new|change|replace|remove|decide}` colours the stroke only (width 4,
  `decide` dashed); edges carry the colour of their change; legend gains a
  "Transition (extension)" block automatically.
- **Map-type layouts:** purpose = hierarchy (top purposes → sub-purposes →
  Outcomes, Organisation/Brand top row, Content left, Story right);
  organisation = role model when Process elements exist; capability =
  area containers with `group:`.
- Lint: per-line text-fit (honours 9 px subtext), W109 (type word in the
  label), W110 (stroke outside white / base / overlay palette), overlay
  dashes allowed on core links. 12 new tests in `test_structure.py`;
  `references/routing.md` holds the routing rules and XML patterns. Five
  new examples; all 23 shipped examples lint-clean.

**Sprint 4 (P1.8–P1.10, P2.4, P2.5) — edgy-framework 1.3.0:**
- "Mapping strategy documents to EDGY" table (mission/vision → top Purpose,
  focus areas → sub-Purpose, KPIs → Outcome, initiatives → Activity with one
  Outcome, values → Content, narrative → Story) + anti-pattern "focus areas
  are never Story" (review B 3.1).
- "Formulating capabilities": the three uses, "not the unit of work", one
  system on many capabilities is normal, eight helper questions,
  granularity 6–12 / 40–80, anti-patterns (review B 3.2). Condensed line
  in edgy-diagram's capability-map pattern.
- Outcome row in the reframing matrix; base-element vocabulary fi/fr/de in
  both skills.
- Organisation intersection: role-model check (steers / procures / defines /
  produces / operates / approves) with an optional load view, no threshold.
- Output length by mode (assessment 150 lines; reframing 40–80; summary
  ≤ 200 words + 1 picture; card ≤ 1 page; decision ≤ 40 lines) and the
  anti-pattern "do not pad". edgy-assessment 1.5.3 scopes its 150-line rule
  to the full assessment.

**Sprint 5 (P2.1–P2.3, P2.9) — edgy-framework 1.4.0, edgy-diagram 2.3.0, new edgy-target-state 1.0.0:**
- edgy-framework `mode: target-state`: eight artefacts anchored in EDGY ids
  (purpose map, capability map + cards, guardrails, building-block
  hypothesis with mirror table, work packages with one Outcome each,
  decision records via an external ADR skill or a 40-line template, role
  model, stakeholder summary); card / mirror / work-package templates;
  output template fi/en; fictional worked example (Acme Transit).
- New orchestrating skill `edgy-target-state` (phases 1–9, quality gate,
  anti-patterns, generic delivery note; writes files only, never to
  external systems unasked). Scope follows plan §3: ADRs delegated, wiki
  mechanics out, Experience facet optional.
- edgy-diagram: `reference` layout (lanes top-down, actors left, `[external]`
  right, overlay strokes) and `summary` layout (who / does what / what
  results, warns above 4 boxes per row) — both labelled EDGY extensions;
  Delivery section; two examples; two tests.

**Sprint 6 (P2.6–P2.8) — edgy-assessment 1.6.0, edgy-deep-dive 1.1.0, edgy-framework 1.4.1:**
- `assets/edgy-model.schema.json` (JSON Schema 2020-12) + `tools/validate-edgy-model.py`
  (standard-library subset validator: type, required, properties, items,
  enum, min/max, pattern, local $ref, plus semantic checks). Deep-dive
  Phase 1 validates before reading; assessment validates after writing.
- `scripts/edgy_model_to_txt.py`: the four facet TXT inputs are derived
  from the model (elements with ids, active core links between primary
  elements) — Phase 3 is a script run, diagrams cannot disagree with the
  analysis any more. check.sh step `edgy-model` validates every shipped
  *model*.json, derives TXTs, generates and lints them.
- `mode: extract-model` in edgy-assessment: build a model from an existing
  analysis + TXT files (older deliveries), validate, regenerate TXTs and
  report the differences as findings.
- Section 10 (suggested deep-dives) added to the markdown quality gate as a
  grep; PNG engine order in the PDF phase: draw.io CLI → PlantUML → native,
  never stop because the CLI is missing.
- Reframing template: optional "Strategic choices and alternatives" section
  in fi/en/fr/de.

**Sprint 7 (P3.1–P3.6) — edgy-diagram 2.4.0, edgy-assessment 1.6.1:**
- `edgy-diagram/SKILL.md` 1 279 → 479 lines. Reference material moved to
  `references/`: `xml-reference.md` (structure, shapes, palette, edge
  styles, inline example with legend), `vocabulary.md` (element types, the
  generated core-link tables, flow/tree keywords, tags and metrics,
  natural-language table, facet model), `map-types.md` (layout sketches,
  pairwise spec), `export.md` (presets, PlantUML, official resources, draw.io
  CLI), `routing.md` (Sprint 3). `tools/render-core-links.py` now renders
  into `references/vocabulary.md`; the frontmatter lists a representative
  example subset, `examples/README.md` the full mapping.
- edgy-assessment: the duplicated XML / palette / legend blocks (170 lines)
  replaced by a diagram quality gate that points to edgy-diagram.
- **Eval set** `examples/eval/` (60-leaf capability map, 19-block / 30-edge
  reference architecture) + `tools/edgy-eval.py` metrics table; check.sh
  step `edgy-eval` fails on lint errors. CONTRIBUTING: record lint before /
  after manual fixes in this log (aggregates only).
- **`layout_from: file.archimate#View [scale dx dy]`**: elements matched by
  name keep the ArchiMate view's (scaled) position, unmatched ones go below,
  view elements missing from the input are reported. Standard-library XML
  parsing only; fictional `examples/current-state.archimate`.
- Layout-time warnings (summary row count, layout_from) are now printed by
  the generator too (they were only collected before).
- **Note for the upstream (private) repo:** its `generated/` folder still
  holds an issue log whose "final" XML nests `mxCell` elements — the exact
  structure the skill forbids. Delete or correct it there; this repo never
  had a copy.

**Review A → plan → implementation, closing note.** All seven sprints of
`docs/development-plan-2026-09.md` are implemented in PR #2. Baseline
metrics for the review's deliveries can now be reproduced with
`edgy_lint.py` (private repo) and the eval set shows 0 errors on the sizes
the field team needed (60-leaf capability map, 19-block reference view).

**Notes for the next agents:**
- Sprint 4–7 follow in the same PR; see the plan status line.
- Sprint 3 note: groups/lanes/nesting in the input format, facet
  containers, intersection placement, label standard, routing by size,
  transition overlay, per-map-type layout rules. The renderer and linter
  already resolve parent chains, so containers can land without touching
  them.
- Headless Chromium `--screenshot` sizes the PNG from the SVG's width/height;
  very tall diagrams (> 4000 px) may need `--scale 1`.
- The linter already accepts `mxfile`.
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
