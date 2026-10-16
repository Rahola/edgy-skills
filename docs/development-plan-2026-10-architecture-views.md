# EDGY skills development plan (2026-10, part 4): architecture views and an interactive presenter

**Revision 1 (2026-10-16) — proposal, not implemented.** Follow-up to
[`development-plan-2026-10-coverage.md`](development-plan-2026-10-coverage.md),
whose Sprints 17–20 shipped as **v2.3.0** (edgy-diagram 2.7.0,
edgy-assessment 1.9.0, edgy-framework 1.6.0, edgy-target-state 1.1.0).

**Source — a feature request, not a review.** The request was for five
deliverables the bundle cannot produce today:

1. an **application map** (the application landscape);
2. a **process map** (value chain and process decomposition);
3. a **capability view**: one capability with the processes, applications,
   data and actors around it;
4. **C4 diagrams** for each application (system context, containers);
5. a **dynamic single-page web app** that presents all EDGY diagrams of an
   engagement with a strong visual effect — navigation, zoom, highlighting,
   current → target transitions, a guided tour.

The baseline below was read from `main` (3aef09c). All examples are
fictional (Acme Transit).

> 🔒 No client material was used for this plan. See the privacy rule in
> `CONTRIBUTING.md`. A generated presentation embeds the whole model — it is
> a client deliverable and is never committed to this repo (§9).

---

## 1. What is covered today (baseline)

| Need | Closest existing feature | Gap |
|------|--------------------------|-----|
| Application map | `map_type: asset` (grid / tree), `map_type: reference` (lanes, actors left, `[external]` right, integration bus) | no notion of *application* vs. other assets; no lifecycle (TIME) overlay; no integration-flow labels; no grouping by capability or domain derived from links |
| Process map | `map_type: process` (sequence row), `lane:` swimlanes, `stages:` / matrix | no value chain (L1 row with L2 columns under each); no derived swimlanes by performing actor; no "uses application" chips |
| Capability view | nested capability map, `edgy-deep-dive` pairwise map, `focus` | no single-capability view with four bands; no `page per element` generation |
| Data | `object` element, generic verbs | no data-object conventions (master data, owner, CRUD); no asset → object verb in the vocabulary |
| Actors | `people`, `organisation`, role model | fine; needs to be reusable in all four new views |
| C4 | — | none: no C4 notation, shapes, lint or PlantUML C4 output |
| Presentation | multi-page draw.io, native SVG/PNG previews (`edgy_render.py`), PDF report layout | **no interactive output** (noted in coverage plan §2.11 as P3) |
| Single source | `edgy-model.json` (assessment schema), TXT pages, `edgy_model_to_txt.py`, ArchiMate export | model has no applications, integrations, data objects or C4 detail; every view is authored as its own TXT |

What already helps: the generator's lanes, matrix, nested groups, status
badges (`{rating:}` with `rating_palette:`), transition overlay
(`{change:}`), `[external]` placement and `layout_from:`. The new views are
mostly **new inputs to existing layouts**, plus one new notation (C4) and
one new output (HTML).

## 2. Modelling decisions (EDGY mapping)

EDGY 23 has no *application*, *data* or *actor* element. The plan maps them
onto EDGY base elements so every new view stays valid EDGY and the model
remains one graph:

| Concept | EDGY element | Marker | Notes |
|---------|--------------|--------|-------|
| Application / IT system | **Asset** | `{kind: application}` | also `kind: platform`, `kind: saas`, `kind: integration`; `[external]` as today |
| Data | **Object** | `{kind: data}` | `{master: yes}`, `{owner: ORG-xx}` |
| Actor | **People** (role, persona) or **Organisation** (unit, partner) | — | existing role model conventions |
| Process | **Process** | `{level: 1 \| 2 \| 3}` | L1 = value-chain stage |
| Capability | **Capability** | existing ids, nested groups | |

Relationships: core links are used where EDGY has them (`process →
capability: realises`, `capability → asset: requires`, `process → asset:
requires`, `organisation → process: performs`, `organisation → capability:
has`). Four **extension verbs** are added to the shared vocabulary
(`skills/_shared/edgy-core-links.yaml`, `fi`/`en`/`fr`/`de`), flagged as
non-core so the linter keeps distinguishing them:

| Verb | Pair | Usage |
|------|------|-------|
| `stores` | asset → object | the application is the system of record |
| `reads` / `updates` | process → object | CRUD in a capability view (two verbs, not a matrix) |
| `exchanges` | asset → asset | integration; label carries `{data: OBJ-xx, protocol: REST}` |
| `uses` (existing verb, new pair) | people / organisation → asset | actor uses an application (needed for C4 context) |

**C4 is not EDGY.** It is drawn as an **extension notation** on its own
pages (`notation: c4`), never mixed into an EDGY page. A C4 *software
system* is an EDGY asset of `kind: application`; C4 *containers* and
*components* exist only in a `c4:` block under that asset. The legend on a
C4 page says "C4 model (Simon Brown, CC BY 4.0)" and `NOTICE` gains the
attribution.

## 3. Features

### F1 Application map (`map_type: application`) — P0

- Applications as cards, grouped by **domain** (`group:`, nesting allowed)
  or, with `group_by: capability`, by the capability area they are required
  by (derived from `capability → asset: requires`; an application required
  by two areas goes to the first and gets a "+1 area" subtext).
- Optional layers as lanes (`lanes: channel, core, shared, external`) —
  reuses the reference-architecture lane layout; `[external]` right column.
- **Lifecycle overlay** — TIME (`Tolerate / Invest / Migrate / Eliminate`)
  as a preset `rating_palette`, so it is a badge, not a fill (W123 already
  guards the legend).
- **Integration edges** from `exchanges`, label = data object name,
  protocol in small text; `edges: none | bus | direct` (default `bus` above
  12 integrations, reusing the integration-bus pattern).
- Transition overlay (`{change:}`) works unchanged.
- Lint: **W124** application without an owner (`organisation → asset:
  manages`); **W125** integration without a data object; semantic **S013**
  application named after a capability ("Ticketing" — the system is
  "Fare engine").

### F2 Process map (`map_type: process`, two variants) — P0

- **Value chain** (`process_view: chain`): L1 processes as chevrons in one
  row (official process shape), L2 processes stacked in a column under each
  L1 (from `contains`), L3 hidden unless `depth: 3`.
- **Swimlane** (`process_view: swimlane`): lanes derived from the actor that
  `performs` each process (as the task inventory already derives lanes),
  sequence from `precedes` or input order, applications used shown as small
  asset chips under the step (`chips: assets`), not as edges.
- Lint: **W126** L2 process without an L1 parent when `process_view:
  chain`; existing W111/W113 cover crossings.

### F3 Capability view (`map_type: capability-view`) — P0

One capability in the centre, four bands derived from the graph — nothing
is re-entered:

```
                 ┌──────── actors (organisation has / people perform) ────────┐
 processes  ───▶ │                 CAP-05  Ticketing                        │ ───▶ applications
 (realises)      │        maturity 3 · owner: Fare team · TIME: invest      │      (requires)
                 └──────── data objects (read / updated by the processes) ──┘
```

- `focus: CAP-05` draws one view; `pages: per-capability` draws one page
  per capability (optionally `where: highlight` or a list of ids).
- Second hop is opt-in (`hops: 2`): applications' data objects and
  integrations shown dimmed.
- A **capability × application matrix** page (`map_type:
  capability-matrix`) reuses the matrix layout: rows = capabilities,
  columns = applications, cell = badge (`requires` + TIME rating).
- Lint: **W127** capability view with an empty band, explained (e.g. "no
  process realises CAP-05 — model gap, not a layout error"). This is a
  finding for the report, so it is also written to `qa.json`.

### F4 C4 diagrams per application (`notation: c4`) — P1

- **Level 1 — System context**: the application in the centre, actors
  (`uses`) above, other applications (`exchanges`) left/right, external
  systems grey. Derived from the model; no extra input needed.
- **Level 2 — Containers**: from the `c4:` block of the application:

  ```
  - asset: "Fare engine" {id: AST-02, kind: application}
    c4:
      - container: "Fare API" {technology: "Kotlin, Spring Boot"}
      - container: "Fare rules DB" {technology: "PostgreSQL", type: database}
      - container: "Admin UI" {technology: "React"}
      - "Admin UI" -> "Fare API": "updates fare rules" {protocol: "HTTPS/JSON"}
      - "Fare API" -> "Fare rules DB": "reads and writes" {protocol: "JDBC"}
  ```

  Relationships into and out of the system boundary come from F1's
  `exchanges` and are attached to the container named in `{via: …}`.
- **Level 3 — Components** only when a container has `components:`; no
  Level 4.
- `pages: per-application` → one context + one container page per
  application in a single draw.io file (`C4-L1 Fare engine`, `C4-L2 Fare
  engine`).
- Shapes: draw.io's C4 shape library (`mxgraph.c4.*`, to be confirmed in the
  Sprint 23 probe) with the standard C4 colours; native preview in
  `edgy_render.py`; PlantUML output via **C4-PlantUML** (`!include
  C4_Container.puml`) next to the existing `<edgy/edgy>` path.
- Lint **C001–C006**: element without a type, container without
  technology, relationship without a description, relationship without
  protocol across the boundary, person inside a system boundary, container
  page with no boundary.
- `edgy-framework` gets a short section on deriving C4 from the EDGY
  architecture facet (what is an application, where the boundary is, when
  Level 3 is worth drawing).

### F5 One architecture model, many views — P0 (enabler)

- `edgy-model.json` schema **1.3** (additive, optional keys): `assets[].kind`,
  `objects[]`, `integrations[]`, `assets[].c4`, `processes[].level`,
  `actors` as references to people / organisation. Assessment models
  without them stay valid.
- `edgy_model_to_txt.py --views application,process,capability,c4` writes
  the TXT pages for every view from one model, so a change to an
  application shows up in the application map, every capability view and
  its C4 pages at once.
- `edgy_model_diff.py` covers the new keys (integration added / removed,
  container changes).
- `edgy_model_to_archimate.py` maps applications to *Application
  Component*, data to *Data Object*, `exchanges` to *Flow*.

### F6 Presenter — dynamic single-page web app (`edgy_present.py`) — P1

**Output:** one self-contained `presentation.html` (no server, no CDN, works
offline and from an e-mail attachment), built by a Python standard-library
script from the draw.io file and the model:

```
python edgy_present.py model.json diagrams.drawio -o presentation.html \
  [--title "Acme Transit target state"] [--tour tour.txt] [--theme dark]
```

**Architecture.** The generator already computes positions; the presenter
reuses `edgy_render.py`'s SVG (one `<svg>` per page) with a `data-id`,
`data-type` and `data-facet` attribute on every element and edge group
(small change in the renderer), plus a JSON graph of the model embedded in
the page. All interactivity is vanilla JS + CSS over that SVG; no
framework, no build step. Target size: < 1.5 MB for 30 pages.

**Experience ("stunning", but in service of the content):**

| Feature | Effect |
|---------|--------|
| Overview | all views as a card wall (facet-coloured), staggered fade-in; click zooms the card into the full view |
| Semantic zoom | wheel / pinch with spring easing; labels fade by zoom level; minimap |
| Drill-down | capability on the capability map → its capability view → an application → its C4 context → containers; each step is an animated zoom into the clicked element (View Transitions API where available, FLIP animation otherwise) |
| Focus & trace | hover or tap highlights the element and its 1-hop neighbours **across all views**; others dim to 15 %; integration edges get a flowing dash animation in the direction of the flow |
| Current → target | a slider morphs the transition overlay: removed elements fade out, new ones grow in, changed ones pulse once |
| Heat overlays | toggle maturity / TIME / rating badges as a colour wash on the cards |
| Search | ⌘K / Ctrl+K palette over all elements and ids; jumps with a zoom animation |
| Guided tour | `tour:` steps (view, focus element, overlay, caption) played with ← / →, presenter notes on `N`, full-screen on `F` |
| Deep links | `#/view/capability-view/CAP-05?overlay=target` — shareable state |
| Themes | light / dark from tokens, EDGY facet colours kept in both; `prefers-reduced-motion` turns every animation into a cut |
| Print | a print stylesheet lays out one view per page (PDF hand-out) |

Accessibility: every element is focusable with the keyboard, `aria-label`
from name + type + id, focus ring visible, contrast checked against both
themes.

Tour input (TXT, same style as the generator):

```
tour:
  - view: "Capability map" {caption: "Twelve capabilities, three to invest in"}
  - view: "Capability map" {focus: CAP-05, overlay: maturity}
  - view: "CAP-05 Ticketing" {caption: "Two processes depend on the legacy fare engine"}
  - view: "C4-L1 Fare engine" {overlay: target}
```

## 4. Scope decisions

- **In:** the four views, the model extension, the presenter, skill
  instructions and examples.
- **Out:** live editing in the presenter (draw.io stays the editor);
  C4 Level 4 (code); deployment diagrams; dynamic C4 diagrams; any hosted
  service. A hosted viewer is only possible later by publishing the same
  HTML.
- **No external runtime dependency** in the presenter — fonts are system
  fonts; the generator stays standard-library Python.
- **C4 stays separate from EDGY pages** — mixing notations on one page is a
  lint error (C006), not a style choice.

## 5. Target state

| Skill | v2.3.0 | v2.4.0 |
|-------|--------|--------|
| edgy-diagram | 2.7.0 | **2.8.0** — application / process / capability-view / capability-matrix layouts, C4 notation, presenter |
| edgy-framework | 1.6.0 | **1.7.0** — modelling guidance for applications, data, actors and C4 |
| edgy-assessment | 1.9.0 | **1.10.0** — schema 1.3, views from the model, `presentation.html` as optional deliverable |
| edgy-target-state | 1.1.0 | **1.2.0** — application landscape and C4 per building block in the target-state pack; tour template |
| edgy-deep-dive | 1.1.0 | 1.1.0 (presenter can open a deep-dive pairwise map, no change) |

No breaking changes; all new keys are opt-in.

## 6. Sprints and estimate

| Sprint | Content | Estimate |
|--------|---------|----------|
| **21 — Model and application map** | vocabulary verbs, `kind:` / `level:` parsing, schema 1.3, `edgy_model_to_txt --views`, F1 with TIME preset, W124/W125, S013, example `application-map.txt` | 3–4 d |
| **22 — Process map and capability view** | F2 (chain, swimlane, chips), F3 (`focus`, `pages: per-capability`, `hops`, capability matrix), W126/W127, examples | 4 d |
| **23 — C4** | probe draw.io C4 shapes, C4 parser block, L1 derivation, L2/L3 layout, native preview, C4-PlantUML, C001–C006, `pages: per-application`, ArchiMate/diff mapping, NOTICE | 4–5 d |
| **24 — Presenter core** | renderer `data-*` attributes, `edgy_present.py` bundler, overview wall, zoom/pan, drill-down, cross-view highlight, search, deep links, themes, print | 4–5 d |
| **25 — Presenter effects and integration** | transition morph, heat overlays, flowing edges, tour mode, reduced motion, a11y pass, skill instructions (assessment, target-state), eval set, README, CHANGELOG, v2.4.0 | 3–4 d |

Total ≈ 18–22 working days. Sprints 21–23 and 24 are independent once the
renderer attributes from Sprint 24 exist; the presenter can be built
against today's map types first and gain the new views as they land.

## 7. Tests to add

- `test_edgy.py`: `kind:` / `level:` / `c4:` parsing; per-capability and
  per-application page expansion; derived lanes and bands; bus threshold.
- `test_lint.py`: W124–W127, C001–C006, each with a passing and a failing
  fixture.
- `test_semantic.py`: S013.
- `test_render.py`: every element/edge group carries `data-id`, the ids are
  unique per page and match the model ids.
- `test_present.py` (new): the HTML is self-contained (no `http(s)://`
  `src`/`href` outside comments), the embedded graph parses, every view in
  the draw.io file appears once, the tour references existing views and
  elements, file size budget.
- Browser smoke test (Playwright with the pre-installed Chromium, optional
  in CI): open the HTML, drill down CAP → C4 L2, toggle overlay, no console
  errors, screenshot for the eval report.
- `tools/edgy-eval.py`: eval model `eval/architecture-views.txt` (Acme
  Transit: 12 capabilities, 18 applications, 10 data objects, 6 actors,
  3 applications with `c4:`), all views generated from it with 0 errors and
  0 visual findings; new `check.sh` step `edgy-architecture-views`.

## 8. Acceptance

1. From one fictional model the bundle produces, without manual draw.io
   work: an application map, a value chain and a swimlane process map, one
   capability view per capability, a capability × application matrix, and
   C4 L1 + L2 for every application with a `c4:` block.
2. All of these pass `edgy_lint.py` with 0 errors and the preview shows no
   overlaps (W108/W111/W113 = 0 in the eval set).
3. `presentation.html` opens offline in Chromium, Firefox and Safari, drills
   from the capability map to a C4 container view in ≤ 3 clicks, and the
   tour plays end to end; with reduced motion there are no animations.
4. A model change (rename an application) appears in every view and in the
   presenter after one regeneration.
5. `check.sh` green, privacy scan green, CHANGELOG and README updated.

## 9. Risks and limits

| Risk | Mitigation |
|------|------------|
| Applications are not EDGY elements — purists may object | strict mapping to Asset with `kind:`; legend says "Asset (application)"; framework text explains the choice |
| C4 shapes in draw.io differ between versions | probe first in Sprint 23; fall back to plain styled rectangles with the C4 colour scheme |
| Presenter becomes a second renderer to maintain | it never computes layout — it only decorates the renderer's SVG |
| "Stunning" effects hurt readability or performance | every effect has a purpose in the table in F6; budget 60 fps on 200 elements; reduced-motion path; effects off in print |
| Presentation files leak client data | generated into the engagement folder only; `.gitignore` pattern `*presentation*.html` outside `examples/`; privacy-scan also scans HTML |
| Large landscapes (100+ applications) | application map groups by domain with collapsed groups in the presenter; matrix page instead of edges |
| C4 licence | C4 model is CC BY 4.0 — attribution in `NOTICE` and on C4 legends; no C4 text copied |

## Appendix A. Example inputs to add (all fictional)

| File | Content |
|------|---------|
| `examples/application-map.txt` | 18 applications in 4 domains, TIME badges, 14 integrations (bus) |
| `examples/process-chain-map.txt` | 5 L1 / 14 L2 processes (plan → sell → operate → inform → settle) |
| `examples/process-swimlane-map.txt` | ticket refund process, 4 actors, application chips |
| `examples/capability-view.txt` | `focus: CAP-05` and `pages: per-capability` variants |
| `examples/c4-fare-engine.txt` | L1 + L2 for one application |
| `examples/eval/architecture-views.txt` | the eval model in §7 |
| `examples/presentation/tour.txt` | five-step tour over the eval model |
