# Changelog

Releases of the edgy-skills bundle are git tags. Each skill also carries its
own semantic version in its `SKILL.md` front matter and in `registry.yaml`.
Install a release with `EDGY_SKILLS_REF=<tag>` (see README → Versions).

## Unreleased

Candidate v2.6.0 (human facilitation and assistive-technology acceptance pending):

- edgy-diagram 2.10.0: discussion-led presentation guidance; navigation API 1
  for explicit-ID targeting, initial routes and reliable local Back in srcdoc.
  Graph/notation contract 1 and the five atlas effects remain unchanged.
- Corrected fictional Acme walkthrough: return from every section, targeted
  atlas drill, escaped dynamic data and explicit embedded Back. CI checks its
  generated HTML, browser behaviour, accessibility findings and size budget.
- No stakeholder-site builder, content lifecycle or approval workflow is added.

- Zenodo DOI [10.5281/zenodo.23439782](https://doi.org/10.5281/zenodo.23439782) (all versions): a DOI badge in
  README and `doi:` in `CITATION.cff`. Metadata only.

## v2.5.1 — 2026-10

Authorship metadata only; no skill changes (every skill keeps its v2.5.0
version and content).

- `NOTICE` and README name the copyright holder: **Copyright 2026 Roope
  Ahola**, an independent spare-time project developed with AI assistance
  (Claude Code). It was "edgy-skills contributors" before.
- New `CITATION.cff`: GitHub shows "Cite this repository" with a ready
  citation.
- Releases up to v2.5.0 stay under the same licences (Apache-2.0, and CC
  BY-SA 4.0 for the EDGY-derived files); nothing about the licences
  changes.

## v2.5.0 — 2026-10

A click-through **realisation trace** from the customer's journey down to
the organisations and back up, **C4** diagrams for one application as a
separate `edgy-c4` skill, notation pages done properly in the core, model
format **1.10** and adapters that install dependencies and report failures.
Background: `docs/development-plan-2026-10-v2.5.0.md` (revision 4, locked;
§11 records the clarifications) and the test plan
`docs/testing/v2.5.0-agent-test-plan.md`.

| Skill | v2.4.0 | v2.5.0 |
|-------|--------|--------|
| edgy-diagram | 2.8.0 | **2.9.0** |
| edgy-assessment | 1.10.0 | **1.11.0** |
| edgy-framework | 1.7.0 | **1.8.0** |
| edgy-target-state | 1.2.0 | **1.3.0** |
| edgy-deep-dive | 1.1.1 | **1.1.2** |
| edgy-c4 | — | **0.1.0** (new; claude-code and generic) |

No breaking changes. Every v2.4.0 example regenerates byte-identically
(`check.sh` step `examples-vs-v2.4.0`, against the pinned tag), and every
1.9 and 1.8 model gives byte-identical TXT, diff and ArchiMate output
(`compat-1.9`, `compat-1.8`).

**edgy-diagram 2.9.0**
- **Realisation trace** (`map_type: trace`, `expand: trace`): levels
  journey → task / channel → product → capability → process / asset /
  people → organisation; one page per element with an id plus a trace
  index, each card linking to its own page (draw.io
  `UserObject link="data:page/id,…"`, unwrapped by the linter, the
  renderer and the presenter). One hop per page, bands by level,
  deterministic order, stable page ids `trace-<id>`; `where: ids |
  highlight | from X`, `trace_direction: both | down | up`; "+N more" list
  pages above 12 cards, edge-less crowded rows with the verbs in the row
  header, mixed rows split by type; **W129** empty band below an element
  with the W127 evidence statuses (`model_gaps[]`). Example
  `examples/trace-map.txt`; the eval model gains an Experience part.
- **Presenter drill-through** (inside effect 5 — still five effects): one
  Trace card on the wall, the "→" badge or a second click opens a card's
  trace page, `#/trace/<id>/…` routes with the browser history, a
  breadcrumb, "not found" for malformed routes; new self-test steps.
- **Notation pages done properly (F4-core):** a `notation:` page keeps only
  its header keys in the EDGY parser and never enters the document graph;
  `expand:` reaches the handler (E013 on one page without it); handlers may
  return findings `(severity, rule, message, subject)`, run a prepass over
  all their pages (`graph.notation_index`) and give pages fixed ids; a
  handler failure is one E013 error, no traceback, no file.
- **C4 badge (Q3):** an application card on the trace pages gets a separate
  "C4" badge linking to its C4 system context when the delivery has one;
  the card keeps its trace link.
- `edgyTrace` marker and SVG `data-link` / `data-trace` (extension
  contract 1, additive).

- **Visual check:** new rules **W130** (a line runs under another
  edge's label) and **W131** (two unrelated edges share a stretch of
  line). W111 also covers trace "+N more" cards and a route back through
  its own end. The router keeps labels off other lines and re-routes
  around labels placed later. The eval model is 0/0/0 under the new
  rules.
- A `{gaps:}` value that is not `band=status` is a warning. Messages from
  `draw: false` model pages are reported (E010). A missing input file is
  an error. The native SVG draws dashed person outlines.

**edgy-c4 0.1.0 (new)** — C4 L1 derived from the EDGY graph (Persons,
inferred Persons dashed, partner systems, `[external]` grey), L2 container
pages written by hand with boundary crossings from `{container:}` on EDGY
transfers, rules C001–C007, static shapes, legend "C4 model (Simon Brown,
CC BY 4.0)", page ids `c4-<level>-<system>`, L1 ↔ L2 links. draw.io only.

**edgy-assessment 1.11.0** — model format **1.10**: `journey` as an object
or an array with ids, `gaps` on the chain types with per-type keys, a
version gate; `--views trace` (opt-in, not in `--views all`); migration
notes 1.9 → 1.10 and the Experience links to emit.

**edgy-framework 1.8.0** — modelling journeys, tasks and channels with ids
and links for the trace. **edgy-target-state 1.3.0** — C4 only for
applications in decided building blocks. **edgy-deep-dive 1.1.2** — reads
a journey array.

**Testing (phase 4).** Claude (four sub-agents), Codex and Vibe tested
the candidate, and a person checked the browsers, draw.io desktop and the
PDF export. Every finding is fixed in this release: the reports and the
fixes are on PR #8, and plan §11 records the as-built choices.

**Adapters and tools** — `requires:` and `install: directory` in SKILL.md
front matter, the registry, the validator and `lookup-skill.py` (install
order, cycle and missing-dependency errors, ids validated first);
claude-code and generic install dependencies first from the same ref;
Vibe, Cursor and curl mode refuse directory skills (`--all` skips and names
them); every adapter exits 1 on a failed skill or an empty / unreadable
list; Vibe added to the agents of the five SKILL.md-only skills. New
`check.sh` steps: `adapter-install`, `trace-fixtures`, `edgy-notation-core`,
`edgy-c4`, `examples-vs-v2.4.0`.

## v2.4.0 — 2026-10

Architecture views: an application map, a value chain and swimlane process
maps, one capability view per capability and two matrices — all drawn from
one model, in EDGY notation (applications and data are Assets of a `kind`)
— plus a self-contained offline presentation of every view. Background:
`docs/development-plan-2026-10-architecture-views.md` (revision 5, locked;
deviations in its §12). C4 per application (`edgy-c4`) is v2.5.0.

| Skill | v2.3.0 | v2.4.0 |
|-------|--------|--------|
| edgy-diagram | 2.7.0 | **2.8.0** |
| edgy-assessment | 1.9.0 | **1.10.0** |
| edgy-framework | 1.6.0 | **1.7.0** |
| edgy-target-state | 1.1.0 | **1.2.0** |
| edgy-deep-dive | 1.1.0 | **1.1.1** |

No breaking changes. Every new input key and model field is opt-in; every
shipped 1.8 model gives byte-identical TXT, diff and ArchiMate output
(`tools/test_model_compat.py`). Generated draw.io output changed in style
keys only: every element cell carries the identity markers of extension
contract 1 (`edgyId`, `edgyType`, `edgyOcc` …) and every legend cell
`edgyRole=legend` — the regenerated examples differ from v2.3.0 only there
(`tools/compare-style-only.py`).

**edgy-diagram 2.8.0**
- **Document graph** over all pages: one model element per explicit
  `{id:}`, occurrences per page, cross-page relationships; **E014**
  conflicting or duplicate id, **E015** relationship to an unknown id;
  `draw: false` model pages; `expand: per-capability | per-application |
  per-process` with `where: ids | highlight | top`; `--graph` writes it as
  JSON (`assets/edgy-graph.schema.json`).
- **`map_type: application`**: domains, domains × layers (`rows:`) or
  `group_by: capability` areas with a Shared strip (no primary area) and an
  External systems column; Gartner TIME lifecycle badge `{time: …}` and a
  second badge (`{hosting: …}` / `{criticality: …}`); integrations as
  `transfers` with data and technology on a second label line; `edges:
  direct | none`; owners and data folded onto cards and labels; **W124**
  application without an owner (warning with `ownership: required`),
  **W125** integration without data.
- **Orthogonal routing** (`scripts/edgy_route.py`, `route: auto`) through
  the channels between cards, labels on the longest free segment.
- **`map_type: process`**: `process_view: chain` (L1 row, L2 stacked, L3
  with `depth: 3`, management / core / support bands, **W126**) and
  `process_view: swimlane` (lanes per performer, staircase, asset chips).
- **`map_type: capability-view`**: one capability with actors, processes,
  resources, data (CRUD) and products in five bands, `hops: 2` context;
  **W127** for an empty band with an evidence status (`{gaps: band=status}`)
  — `qa.json` gains `model_gaps[]` and `generator_notes[]`.
- **`map_type: capability-matrix`**: capabilities × applications (● / ◉
  primary) and `matrix: crud` (processes × data with CRUD letters).
- An empty application, process or matrix page is derived from the document
  graph — nothing is typed twice.
- **Presenter-lite** (`scripts/edgy_present.py`, `--present`): one offline
  HTML of every view — card wall → zoom, cross-view highlight, ⌘K search,
  current ↔ target filter over `{change:}` annotations, paging, deep links,
  print; CSP with sha256 hashes and `connect-src 'none'`; browser self-test
  in CI. `*presentation*.html` is git-ignored outside `examples/`. The card
  wall sizes its rows by content and has a phone layout (one column, the
  top bar wraps); the self-test checks in a narrow window that no card is
  flattened.
- **Extension contract 1** (`references/extension-contract.md`): style
  markers, graph JSON, SVG `data-*` groups (renderer hardened against
  attribute break-out), notation handlers that fail closed (**E013**
  unknown notation, **E012** mixed notations on one page).
- Routed maps, after the agent test round: one port list per card side for
  both directions, no shared trunks between different edges, labels off group
  titles and off other edges; `ownership: required` marks `no owner` on the
  card; a TIME value hidden by a maturity / rating badge is a warning. New lint
  **W128**: a header text (band header, matrix key) covered by the legend.
- Influence verbs `stores`, `accesses {crud:}`, `interacts with`
  (fi / en / fr / de); semantic question **S013** (application named like
  the capability it serves).
- Examples: application-map, application-by-capability-map,
  process-chain-map, process-swimlane-map, capability-view-map (strict lint
  gate); eval `architecture-views.txt` (12 capabilities, 18 applications, 10
  data assets, 6 actors) — `check.sh` step `edgy-architecture-views`
  requires 0 lint findings and 0 visual findings on every view.
- Golden test (`edgy-examples-golden`): every example is regenerated in
  `check.sh` and must equal its `expected-*` file. The gates and
  `tools/regen-examples.sh` measure text with the glyph tables
  (`EDGY_TEXT_TABLE_ONLY=1`), the backend CI has — a local Pillow with real
  fonts measures a pixel differently and must not move the examples.

- **External standards register** (`references/external-standards.md`):
  every classification from outside EDGY (Gartner TIME, CRUD, process bands,
  swimlane layout, maturity / hosting badges, ArchiMate export, C4 planned)
  with what it answers, why it was chosen, alternatives, how it stays
  subordinate to EDGY, and its source and licence. CONTRIBUTING: no external
  standard without an entry; NOTICE names the third parties. An audit of
  every skill added the capability classification (nature, level,
  sourcing), the building-block / work-package terms (TOGAF-derived) and
  the strategy vocabulary, and lists the skills' own analysis constructs.
- **README: Principles** — EDGY 23 first, visible opt-in extensions, the
  register, another notation as another skill, gaps as evidence, offline,
  no client material.

**edgy-assessment 1.10.0**
- Model format **1.9** (additive): `relationships[]` between element ids,
  `elements.people`, `organisation` as an object or an array, asset `kind`,
  `hosting`, `owner`, `time`, `criticality`, `master`, capability `gaps`,
  process `band`.
  The validator supports `oneOf` / `anyOf` / `null` and rejects 1.9
  structures in a model that does not declare 1.9.
- `edgy_model_to_txt.py --views …|all`: one multi-page TXT with the model
  page and the architecture views (swimlanes one page per L1 process).
- `edgy_model_diff.py` compares asset attributes and `relationships[]`; for
  a 1.9 model the transition TXT draws only what changes (routed, lint-clean;
  `--full` draws everything);
  `edgy_model_to_archimate.py` maps applications to ApplicationComponent,
  platforms to Node, data to DataObject, `stores` / `accesses` to Access
  (accessType from `crud`), `transfers` to Flow, People to BusinessActor.
- Fix: the scripts find edgy-diagram after an install, not only in a
  checkout (`scripts/edgy_paths.py`).
- Example `examples/architecture-model.json` (1.9, fictional).

**edgy-framework 1.7.0**
- *Modelling applications, data and actors*: applications and data as
  Assets of a kind, owners and performers, primary capability, master data,
  integrations, TIME — and model gaps vs findings.
- Fix: the identify-mode capability table used other values for `nature`
  and `level` than the model schema; it now uses the schema's values.

**edgy-target-state 1.2.0**
- Optional application landscape and capability × application matrix from
  a 1.9 model, with `ownership: required`.

**edgy-deep-dive 1.1.1**
- `organisation` may be an object (1.8) or an array (1.9); install-aware
  script path.

## v2.3.0 — 2026-10

Coverage: the shapes of the official EDGY 23 maps that the generator could
not draw, a status overlay for heat maps, semantic questions beyond purpose
maps, a model diff and an ArchiMate export. Background:
`docs/development-plan-2026-10-coverage.md` (a coverage review against the
16 official example maps).

| Skill | v2.2.0 | v2.3.0 |
|-------|--------|--------|
| edgy-diagram | 2.6.0 | **2.7.0** |
| edgy-assessment | 1.8.0 | **1.9.0** |
| edgy-framework | 1.5.0 | **1.6.0** |
| edgy-target-state | 1.0.1 | **1.1.0** |
| edgy-deep-dive | 1.1.0 | 1.1.0 |

No breaking changes to the input format; every new key is opt-in or chosen
from the input. Generated output changed in two places: the box legend is
220 px high (the last line spilled over the 200 px box — every box-legend
example regenerated, only legend cells moved), and a tree edge whose child
sits below its parent leaves at the bottom (`expected-outcome.drawio`).

**edgy-diagram 2.7.0**
- **Nested `group:`** (any depth): the official three-tier capability map
  (area → sub-area → capability); `group_style: official | light` —
  official by default with nesting: area in the facet colour of what it
  holds, white sub-groups. Container rows use one fixed gap; areas per row
  drop when nested areas get too wide.
- **Stage columns**: `map_type: task` with `stages:` and no lanes → one
  column per stage (the official task map).
- **Matrix**: `rows:` × `columns:` (alias of `stages:`) with
  `{row: …, column: …}` for any grid-like map — the official channel map
  2 × 2, a journey touchpoint map, a transition roadmap (waves × areas).
- **Product / brand / object trees** when they have `contains` links
  (portfolio), hub-and-spoke otherwise.
- **Outcome web**: outcomes with directed links in layers, causes left,
  effects right (top-down when that would be too wide).
- **`layout_from: file.drawio#Page`**: areas and top-level elements moved in
  draw.io keep their place when the map is regenerated.
- **Status badges** (extension): `{maturity: 1–5}`, `{rating: …}`,
  `rating_palette:` — a badge on the card and a legend row; the fill stays
  the facet colour.
- Lint **W122** container coloured with a facet colour its elements do not
  carry; **W123** badge colour without a legend key; W106 and W102 explain
  the new options.
- Semantic review on every page: **S007–S012** (capability named after a
  system or unit, phrased as a verb, shaped like a project; task in the
  organisation's voice; outcome that is an action; outcome without a
  measure while others have one). `qa.json` records the rule set.
- Examples: capability-areas-nested, channel-matrix, transition-roadmap,
  product-portfolio, outcome-web, capability-heatmap (all in the strict
  lint gate); eval `official-shapes.txt` — one page per official map type,
  `check.sh` step `edgy-official-shapes` (0 errors, 0 visual findings).

**edgy-assessment 1.9.0**
- `scripts/edgy_model_diff.py`: current + target `edgy-model.json` →
  transition map TXT (`keep` / `change` / `new` / `remove`, core links per
  type pair, `--layout triad`) and a change table; `replace` and `decide`
  stay human judgements. Example pair `examples/model-diff/`.
- `scripts/edgy_model_to_archimate.py`: ArchiMate 3.1 Open Exchange XML,
  one view per facet map, `edgy:type` on every element.
- Phase 4b runs the semantic review on every map input.
- `edgy_model_to_txt.py`: a product without an `id` gets `PRD-xx`, no longer
  `PRO-xx` like a process (two elements of the all-facets map could share an
  id); the model diff uses the same scheme.

**edgy-framework 1.6.0**
- *Formulating tasks, outcomes and the Experience facet*: journey stages,
  tasks in the person's words, channel axes, touchpoint matrix, outcomes.
- Capability anti-patterns tied to S007–S009; heat maps as an extension.

**edgy-target-state 1.1.0**
- The transition overlay can be derived from two models with the diff; a
  wave plan is a `columns:` × `rows:` matrix.

## v2.2.0 — 2026-10

Semantic review of purpose maps, verbs and legend in the map language,
measured layout quality with standard-sized cards, a task map with
stakeholder lanes, native publication presets and a QA manifest with
human-only approvals. Background:
`docs/development-plan-2026-10-semantics-and-layout.md` (field feedback on
a delivered series of maps).

| Skill | v2.1.0 | v2.2.0 |
|-------|--------|--------|
| edgy-diagram | 2.5.0 | **2.6.0** |
| edgy-assessment | 1.7.0 | **1.8.0** |
| edgy-framework | 1.4.1 | **1.5.0** |
| edgy-deep-dive | 1.1.0 | 1.1.0 |
| edgy-target-state | 1.0.1 | 1.0.1 |

No breaking changes to the input format. Generated output changed once:
`equal_cards` is on by default (one size per element type and page) and
every layout starts its content at (60, 60), so every shipped
`expected-*.drawio` was regenerated; `equal_cards: false` restores measured
widths. The draw.io CLI presets keep their names and semantics.

**edgy-diagram 2.6.0**
- `scripts/edgy_semantic_review.py` (S001–S006, `--semantic-review` on the
  generator): action as a Purpose, Outcome that measures nothing, missing
  provenance (`[confirmed]` / `[analytical]` / `[proposed]`,
  `{status: …}` on Outcomes), `contains` that may be an influence, metric
  in a Purpose name. It asks; a reviewer signs off.
- `language:` renders the legend, the generated headings and every
  vocabulary verb in fi / en / fr / de (`translate_verbs: false` keeps the
  input spelling); lint **W116** label in another language than the map's.
- Lint **W117–W120** layout quality, on by default (`--no-layout-quality`):
  size spread, near-alignment and uneven gaps, balance on grown pages,
  aspect; **W121** `--series` across the files of one delivery (legend
  placement, content margin, card width per type, font sizes). Every
  finding carries its numbers.
- Layout options `card_width`, `equal_cards` (default true),
  `group_columns`, `cards_per_row`, `equal_group_width`, `align_groups:
  grid`; uniform 60 px content margin; triad panels stretch to their row.
- `map_type: task` stakeholder **inventory** (lanes × `stages:` columns, no
  edges; a related People / Organisation element becomes the lane) and
  **path** (tasks → journey / channels, vertical ports);
  `examples/task-stakeholder-map.txt`.
- Native presets `--preset publication | presentation` for `--preview` and
  `--engine native`: margin, legend placement, `title:` / `footnote:`
  bands, crop to content, W115 at the preset's reference width.
- `qa.json` manifest (`--qa`, on with `--preview`; `scripts/edgy_qa.py`,
  `assets/qa.schema.json`): counts, lint, visual / layout / language /
  text-size checks, preview sizes, generator warnings, and the human-only
  fields `visual_approval`, `semantic_approval`, `delivery_notes`.
  `tools/edgy-eval.py` reads it (new **Layout** column).
- Eval fixtures `series-acme-*` and `fixture-s1-purpose-semantics`;
  `check.sh` steps `edgy-semantic-tests`, `edgy-series`, `edgy-qa`;
  `tools/regen-examples.sh`.

**edgy-assessment 1.8.0**
- Phase 4b semantic review of the purpose map with a sign-off line; Phase 3
  `language` and the model's `layout` block written into every TXT
  (`edgy-model.schema.json`); Phase 4 `--preset publication`, `--series`
  across the four files; Phase 5 reads `qa.json` and requires both
  approvals (`edgy_qa.py --require-approvals`), lint and approvals on
  separate lines; templates section 9 states the provenance convention.

**edgy-framework 1.5.0**
- *Purpose map semantic review* checklist: Purpose vs task, Outcome vs
  Purpose, provenance tags, when `contains` is an influence; sign-off line.

## v2.1.0 — 2026-10

Geometry fidelity, visual lint rules and a planned ring layout for large
models. Background: `docs/development-plan-2026-10.md` (two independent field
reviews of one assessment).

| Skill | v2.0.0 | v2.1.0 |
|-------|--------|--------|
| edgy-diagram | 2.4.1 | **2.5.0** |
| edgy-assessment | 1.6.1 | **1.7.0** |
| edgy-framework | 1.4.1 | 1.4.1 |
| edgy-deep-dive | 1.1.0 | 1.1.0 |
| edgy-target-state | 1.0.1 | 1.0.1 |

No breaking changes to the input format. Generated output changed once: box
widths follow measured text, so every shipped `expected-*.drawio` was
regenerated; the two purpose maps use the new tree layout.

**edgy-diagram 2.5.0**
- `scripts/edgy_geometry.py`: one resolved geometry (absolute boxes, ports,
  routes, label positions) shared by the generator, the preview and the
  linter. Fixes: diagonal end segments on orthogonal edges with waypoints;
  `label: source|middle|target` now render at 25 / 50 / 75 %;
  `edgeStyle=none` edges run border to border.
- Lint: **W111** edge through a foreign element, **W112** label on an
  element, **W113** label on a label, **W114** label or edge end off the
  page, **W115** text below 6 pt at `--scale`; `--visual` prints them as JSON
  with coordinates.
- `scripts/edgy_text.py`: Helvetica glyph-width tables (stdlib) for box
  sizing, wrapping and W101; description rows render in normal weight.
- `--publication` (renderer, `--preview`, `--engine native`): SVG/PNG
  cropped to the content with an orientation hint. `legend: strip`: one band
  along the bottom, page as tall as the content.
- `map_type: triad` (EDGY extension): planned ring with one primary element
  per type (`{primary: true}`), straight core links, two page-edge detours,
  "Further <type>" panels for the rest (their links are reported, not
  drawn). `{label_dx, label_dy}` relationship options.
- Purpose map re-laid out as a tidy tree: parent centred, routing corridor,
  Outcomes in their own row, no branch through a child box.
- Eval set: fixtures F1 / F2 / F4 / F5 and a 19-element single-facet map;
  `tools/edgy-eval.py` reports page ratio and visual-rule counts.

**edgy-assessment 1.7.0**
- `edgy-model.schema.json`: optional `primary` on elements and capabilities.
- `edgy_model_to_txt.py --layout triad`; core links follow the primary
  element; `scripts/test_model_to_txt.py` in `check.sh`.
- Phases 3–5: when to use the triad, `--visual` in the quality gate, the
  all-facets ratio limit, recommended structural maps (purpose, capability,
  journey) from the same model, a final-PDF review at viewing scale with
  `--scale` / `--publication`; templates section 9 explains the ring.

**Repository**
- `CONTRIBUTING.md` → *Releasing (maintainers)*: tag the merge commit after
  the merge and verify every tag resolves to a different commit.

## v2.0.0 — 2026-10

Generator-first EDGY diagrams with a linter and CLI-free preview, structure
for real architecture maps, and a new target-state workflow. Background and
rationale: `docs/development-plan-2026-09.md`.

| Skill | v1.0.0 | v2.0.0 |
|-------|--------|--------|
| edgy-diagram | 1.7.0 | **2.4.1** (major) |
| edgy-framework | 1.2.0 | 1.4.1 |
| edgy-assessment | 1.5.0 | 1.6.1 |
| edgy-deep-dive | 1.0.0 | 1.1.0 |
| edgy-target-state | — | **1.0.1** (new) |

**Breaking changes (edgy-diagram 2.x)**
- The default path is the Python generator + `edgy_lint.py` + preview; direct
  XML is a fallback for small diagrams only.
- Output is an uncompressed multi-page `<mxfile>` (use `--bare` for the old
  bare `<mxGraphModel>`).
- Elements inside `group:` containers (and the automatic facet containers)
  use draw.io `parent` references with relative geometry.
- Unknown `facet` / `map_type` values stop the generator (exit 2,
  `--lenient` to override); a failed `--preview` exits 3.
- A core-link verb on a pair that is not one of the 24 core links is drawn
  as influence (dashed) and reported; inputs relying on the old behaviour
  should switch to an influence verb.

**New**
- `edgy_lint.py`, `edgy_render.py` (SVG; PNG via headless Chromium), `pages:`,
  `group:`, `lane:`, label standard with `{id:}`, relationship options
  `{from, to, via, change, label}`, transition overlay (EDGY extension),
  purpose-hierarchy / role-model / capability-area / `reference` / `summary`
  layouts, `layout_from:` ArchiMate positioning.
- edgy-framework: strategy → EDGY mapping, capability formulation, Outcome,
  role-model check, `mode: target-state`, output length by mode.
- edgy-target-state: internal target-architecture workflow (new skill).
- edgy-assessment: model JSON schema + validator, TXT inputs derived from the
  model, `mode: extract-model`; edgy-deep-dive validates its model.
- Single vocabulary source `skills/_shared/edgy-core-links.yaml`, eval set and
  `tools/edgy-eval.py`, extended `tools/check.sh`.
- Adapters accept `EDGY_SKILLS_REF` (install a tag) and `EDGY_SKILLS_REPO`.

## v1.0.0 — 2026-07

Initial public release: edgy-framework 1.2.0, edgy-diagram 1.7.0,
edgy-assessment 1.5.0, edgy-deep-dive 1.0.0, adapters for Claude Code, Cursor,
Mistral Vibe and generic agents, validation tooling and privacy guard.
Note: the v1.0.0 adapters always install from `main`; to install v1.0.0 use a
v2.0.0+ adapter with `EDGY_SKILLS_REF=v1.0.0`, or a local checkout of the tag.
