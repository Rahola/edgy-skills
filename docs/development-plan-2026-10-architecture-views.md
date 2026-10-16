# EDGY skills development plan (2026-10, part 4): architecture views and an interactive presenter

**Revision 2 (2026-10-16) — proposal, not implemented.** Revision 1 was
reviewed by three reviewer agents (generator feasibility against the code,
EDGY / C4 modelling, presenter front-end); every accepted finding was checked
against `main` and is folded in. What changed is listed in §10. Follow-up to
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
   engagement with a strong visual effect — drill-down, highlighting,
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
| Application map | `map_type: asset` (grid / tree), `map_type: reference` (lanes, actors left, `[external]` right, integration bus) | assets carry no kind; no lifecycle overlay; `rows:` is ignored when `group:` is used (`edgy_parser.py` ~2069) and a group inside a lane is not supported (~462), so *domains × layers* is a new layout, not a reuse |
| Process map | `map_type: process` = one sequence row (`_layout_sequence`), `lane:`, `stages:` columns, matrix | no value chain (L1 row with L2 under each); lanes are derived from actors only in `map_type: task`, and only when the actor links to nothing but tasks (~2017) |
| Capability view | nested capability map; `edgy-deep-dive` pairwise map; `[focus]` tag (= thicker border, same as `{highlight}`) | no single-capability view; no page generation per element |
| Data | Asset tags already recommend `application` / `data` (`references/vocabulary.md` §Asset); flow verbs `flows [data]`, `transfers`, `sends` (`edgy_vocab.py` FLOW_VERBS) | no data-access verb, no CRUD |
| Actors | `people`, `organisation`, role model | reusable as is |
| C4 | — | no notation, shapes, lint or C4-PlantUML; the renderer knows only the EDGY shapes (`edgy_render.py` ~213) |
| Presentation | multi-page draw.io, native SVG/PNG preview, PDF report layout | **no interactive output** (coverage plan §2.11, P3) |
| Single source | `edgy-model.json` (shipped models: `schema_version "1.8"`), TXT pages, `edgy_model_to_txt.py`, ArchiMate export | the model stores **links between element types only** (`core_links`, one edge per type pair), `organisation` is a single object; there are no element-to-element relationships, so views cannot be derived from it yet |
| Document | `pages:` multi-page TXT (`edgy_document.py`) | **each page has its own parser** (`edgy_document.py` ~87): there is no document-level graph to derive one view from another |
| Ids in output | `{id: CAP-05}` rendered as subtext | draw.io cell ids are sequential (`"2"`, `"3"`, …); the model id is not machine-readable in the file |

What already helps: lanes, matrix, nested groups, status badges (`{rating:}`
+ `rating_palette:`), transition overlay (`{change:}`), `[external]`
placement, `layout_from:`, and the generator's style markers that the
linter reads (`edgyRole`, `edgyLang`). The new views are new layouts over
existing building blocks; the real new foundations are a **document graph**,
**model ids in the output**, **one new notation (C4)** and **one new output
(HTML)**.

## 2. Modelling decisions (EDGY mapping)

EDGY 23 has no *application* or *data* element; actors are People and
Organisation. Applications and data map onto **Asset**, following the Asset
tags the vocabulary already recommends, so they stay in the Architecture
facet and render in its colour:

| Concept | EDGY element | Marker | Notes |
|---------|--------------|--------|-------|
| Application / IT system | **Asset** | `{kind: application}` | also `kind: platform`, `kind: integration`; `[external]` as today |
| Data | **Asset** | `{kind: data}` | `{master: yes}`, `{owner: ORG-xx}`; *Object* stays the facet-neutral base element and is not used for data |
| Hosting (optional) | — | `{hosting: saas \| cloud \| on-prem}` | an attribute, not a kind |
| Actor | **People** (role, persona) or **Organisation** (unit, partner) | — | existing role-model conventions |
| Process | **Process** | — | level is derived from `contains` depth (L1 = value-chain stage), never typed twice |
| Capability | **Capability** | existing ids, nested groups | |

`kind`, `hosting`, `master`, `owner`, `technology` and `crud` join
`RESERVED_METRIC_KEYS` (`edgy_parser.py` ~277), otherwise they would be
printed on the card as "kind: application".

**Relationships.** The 24 core links stay exactly as they are; core links
are used where EDGY has them (`process → capability: realises`,
`capability → asset: requires`, `process → asset: requires`,
`product → capability: requires`, `organisation → process: performs`,
`organisation → capability: has`, `organisation → asset: manages`
(influence)). New verbs are **influence verbs** in
`skills/_shared/edgy-core-links.yaml` (fi / en / fr / de), so W105 and
E010 keep working:

| Verb | Pair | Usage |
|------|------|-------|
| `stores` | asset (application) → asset (data) | the application is the system of record |
| `accesses` `{crud: R \| CU \| CRUD}` | process → asset (data) | one verb with an attribute, so a CRUD matrix can be drawn; no clash with core `creates` |
| `interacts with` | people / organisation → asset (application) | actor uses an application (needed for C4 context); deliberately **not** `uses`, which is core for task → channel only and would raise E010 |

Integrations reuse the existing flow verb **`transfers`** (asset → asset)
with `{data: AST-xx, technology: "REST"}`; the data name goes into the edge
subtext, not the verb, so W105 stays clean. No `precedes` verb: process
order is input order (as in the official process maps, which have no
edges), an explicit `flows` edge only for non-linear steps.

**C4 is not EDGY.** It is drawn as an **extension notation** on its own
pages (`notation: c4`), never mixed into an EDGY page. A C4 *software
system* is an Asset of `kind: application`; *containers* and *components*
exist only on C4 pages. C4 relationships carry a *description* and a
*technology*.

## 3. Features

### F0 Foundations — P0 (enabler for everything below)

- **Document graph.** `edgy_document.py` builds one graph over all pages
  (elements by id, relationships with verb and attributes) before the
  per-page parsers run. Every derived view reads from it.
- **Page expansion.** `expand: per-capability | per-application` (not
  `pages:`, which is the existing multi-page key) turns one view page into
  one page per element, optionally `where: highlight` or a list of ids.
- **Model ids in the output.** The generator writes
  `edgyId=<model id>;edgyType=<type>;edgyKind=<kind>;edgyFacet=<facet>`
  into each cell's style (draw.io keeps unknown style keys when the file is
  edited; precedent: `edgyRole`, `edgyLang`) and `edgyNotation=c4` on C4
  pages. No `<UserObject>` wrappers: the renderer and linter read
  `root.findall('mxCell')` and would silently lose wrapped cells.
- **Quote-aware `{…}` options.** Values are split on every comma today
  (`edgy_parser.py` ~451, ~831), so `technology: "Kotlin, Spring Boot"`
  would break.
- **Model schema `"1.9"`** (additive): `relationships[] {source_id,
  target_id, verb, attributes}`, `organisation` / `people` as arrays,
  `elements.asset[].kind`, C4 elements. `edgy_model_to_txt.py --views
  application,process,capability,c4` writes every view page from one model.
  Older models stay valid; type-level `core_links` remain for assessments.

### F1 Application map (`map_type: application`) — P0

- Applications as cards grouped by **domain** (`group:`, nesting allowed)
  or, with `group_by: capability`, by the capability area that `requires`
  them. An application required by several areas sits in its **primary**
  area — the `requires` link marked `{primary: true}`, else the first in
  input order — and shows "+n areas" in its subtext.
- Optional layers as rows (`rows: Channel, Core, Shared` + `{row: …}`);
  domains × layers is a **new layout** (rows are ignored with groups
  today). `[external]` column on the right as in the reference layout.
- **Lifecycle overlay** — Gartner TIME (`Tolerate / Invest / Migrate /
  Eliminate`) as a preset `rating_palette`, credited in the legend; it is
  a badge, so W123 guards the legend. Optional second badges:
  `{criticality: …}`, `{hosting: …}`. Cost stays a metric (EDGY lists
  cost for Asset).
- **Integrations** from `transfers`, data name and technology in the edge
  subtext; `edges: none | bus | direct` (default `bus` above 12
  integrations, the integration-bus pattern).
- Transition overlay (`{change:}`) works unchanged.
- Checks: **W124** application without an owner (`manages`), **W125**
  integration without a data asset — raised by the **parser / QA** from the
  document graph (the linter only sees XML and owner edges are not drawn on
  this map); semantic **S013** application named after a capability
  ("Ticketing" — the system is "Fare engine").

### F2 Process map (`map_type: process`, two variants) — P0

The default stays today's sequence row, so existing inputs do not change.

- **Value chain** (`process_view: chain`): L1 processes as the official
  pentagon shapes in one row, L2 stacked under each (from `contains`, reusing
  the stage-column layout), L3 only with `depth: 3`. Optional
  `band: management | core | support` gives the classic process landscape
  (three horizontal bands).
- **Swimlane** (`process_view: swimlane`): one lane per actor that
  `performs` the process — the lane derivation generalised from the task
  map, accepting actors that also have other links — order by input order,
  applications used shown as small asset chips under the step
  (`chips: assets`), not as edges.
- Checks: **W126** the `contains` depth contradicts an explicit layer
  (e.g. an L2 placed in the L1 row); existing W111 / W113 cover crossings.

### F3 Capability view (`map_type: capability-view`) — P0

One capability in the centre, five bands derived from the document graph —
nothing is re-entered:

```
                 ┌───── actors (organisation has / performs a realising process) ─────┐
 processes  ───▶ │                     CAP-05  Ticketing                              │ ───▶ applications
 (realises)      │        maturity 3 · owner: Fare team · TIME: invest                │      (requires)
                 └───── data (accessed by the processes, with CRUD) ──────────────────┘
                         products that require the capability (requires)
```

- `focus: CAP-05` draws one view; `expand: per-capability` one page per
  capability.
- `hops: 2` (opt-in) adds, dimmed: data stored by the required
  applications, their integrations, and outcomes the capability
  `contributes to`.
- **Matrices** reuse the matrix layout: `map_type: capability-matrix`
  (rows = capabilities, columns = applications, cell = `requires` badge +
  TIME rating) and `matrix: crud` (rows = processes, columns = data, cell
  = CRUD letters).
- Check: **W127** empty band, explained ("no process realises CAP-05 —
  a model gap, not a layout error"); written to `qa.json` as a finding for
  the report.

### F4 C4 diagrams per application (`notation: c4`) — P1

- **Level 1 — System context**, derived from the document graph: the
  application in the centre; **People → Person**; an Organisation becomes a
  Person only when it is an internal unit acting as a user; a partner's
  system is an external Software System. Systems outside the scope are grey
  whether internal or external. Integration through a bus is shown as the
  logical `transfers` with `technology: via <bus>` — the integration
  platform is not drawn as a hub. Warning when no Person interacts with the
  system.
- **Level 2 — Containers**, flat syntax on a C4 page (the parser opens
  indented blocks only for `group:` / `lane:`, so no nested `c4:` block):

  ```
  notation: c4
  level: container
  system: AST-02
  elements:
    - container: "Fare API" {technology: "Kotlin, Spring Boot"}
    - container: "Fare rules DB" {technology: "PostgreSQL", type: database}
    - container: "Admin UI" {technology: "React"}
  relationships:
    - "Admin UI" -> "Fare API": "updates fare rules" {technology: "HTTPS/JSON"}
    - "Fare API" -> "Fare rules DB": "reads and writes" {technology: "JDBC"}
  ```

  Relationships across the boundary come from F1's `transfers` and attach
  to the container named in `{container: …}` (not `{via: …}`, which is the
  existing waypoint option).
- **Level 3 — Components** only when a page has `level: component`; no
  Level 4.
- `expand: per-application` → context + container pages per application
  in one draw.io file (`C4-L1 Fare engine`, `C4-L2 Fare engine`).
- Shapes: draw.io's C4 shapes (`mxgraph.c4.*`, probed first) with the
  standard C4 colours, fallback to styled rectangles; native preview gains
  the C4 shapes; PlantUML via **C4-PlantUML** (`!include C4_Container.puml`).
- Lint on pages marked `edgyNotation=c4`: EDGY rules E009 (legend), W102
  (colours) and W105 (verbs) are switched off, and **C001–C007** apply:
  element without a type; container without technology; relationship
  without a description; relationship without technology at container
  level; person inside a system boundary; container page without a
  boundary; **C007** EDGY and C4 cells on one page.
- `edgy-framework` gets a short section on deriving C4 from the EDGY
  architecture facet (what is an application, where the boundary is, when
  Level 3 is worth drawing).

### F5 One architecture model, many views — P0

Built on F0: one `edgy-model.json` (schema 1.9) or one multi-page TXT drives
the application map, both process maps, every capability view, the
matrices and the C4 pages; a renamed application changes everywhere on the
next regeneration. `edgy_model_diff.py` covers the new keys (integration
added / removed, kind / TIME changed, container changes);
`edgy_model_to_archimate.py` maps applications to *Application Component*,
data to *Data Object*, `stores` / `accesses` to *Access* (access type from
`crud`), `transfers` to *Flow*.

### F6 Presenter — dynamic single-page web app (`edgy_present.py`) — P1

**Output:** one self-contained `presentation.html` — no server, no CDN, no
network at all, works offline and as an e-mail attachment — built by a
standard-library Python script from the draw.io file and the document graph:

```
python edgy_present.py diagrams.drawio [--model model.json] -o presentation.html \
  [--title "Acme Transit target state"] [--tour tour.txt] [--theme dark]
```

**Architecture.** The presenter never computes layout. It inlines the
native SVG of `edgy_render.py` and decorates it; parsing draw.io in the
browser would be a second renderer, and a generator layout JSON would miss
hand-edited files. Renderer changes (specified, not "small"):

- wrap each vertex in `<g class="el" data-id data-type data-kind
  data-facet>` holding its shape and label lines, each edge in
  `<g class="edge" data-src data-tgt>` with its label; legend cells get
  `data-role="legend"`; ids come from the `edgyId` style marker (F0) —
  cells without one (hand-drawn) are shown but not interactive;
- repeated `font-family` / `font-size` attributes become CSS classes (size);
- **attribute hardening**: colours must match `#[0-9a-fA-F]{3,8}|none`,
  numbers must parse as floats, anything else falls back to a default —
  today style values go into attributes unescaped, which becomes XSS once
  the SVG is inlined in HTML.

Only the current view is live in the DOM; the others sit in `<template>`
and are cloned on entry (60 fps budget, no duplicate `<marker id>`s). The
graph is embedded as `json.dumps(...).replace('<', '\\u003c')`; labels,
captions, notes and search results are written with `textContent` only;
hash parameters are checked against known ids. A CSP meta —
`default-src 'none'; script-src 'sha256-…'; style-src 'sha256-…';
img-src data:; font-src data:; connect-src 'none'; base-uri 'none';
form-action 'none'` — makes it impossible for the page to send the model
anywhere.

**Experience — "stunning", in service of the content:**

| Feature | Effect |
|---------|--------|
| Overview | all views as a card wall (facet-coloured), staggered entrance; click zooms the card into the full view |
| Drill-down | capability map → capability view → application → C4 context → containers. Step 1: the source SVG's `viewBox` tweens with a spring to the clicked element's box (requestAnimationFrame, crisp vector at every frame, works everywhere); step 2: cross-fade to the target view (`document.startViewTransition` for the fade where available, CSS opacity otherwise). Breadcrumb trail; *back* plays the zoom in reverse |
| Edges draw in | on view entry, edges draw themselves (`stroke-dashoffset`), staggered outward from the focus element |
| Focus & trace | hover or tap highlights the element and its 1-hop neighbours **across all views** (counter badges on the other view cards); the rest dims, with a soft spotlight mask; only highlighted integration edges get a flowing dash in flow direction |
| Impact trace | pick two elements → the path between them lights up step by step (capability → process → application → data) |
| Current → target | press `T`: elements matched by `edgyId` glide to their target position (FLIP), removed ones fade out, new ones grow in, changed ones pulse once |
| Heat overlays | toggle maturity / TIME / rating as a colour wash on the cards |
| Zoom & pan | wheel / pinch with spring easing, minimap; description subtext hides below 8 px rendered size — no other label fading, the pages are laid out to be read whole |
| Search | ⌘K / Ctrl+K palette over all elements and ids; jumps with the drill-down zoom |
| Guided tour | `tour:` steps (view, focus, overlay, caption) with ← / →, full-screen on `F` |
| Presenter view | `P` opens a second window (`window.open` + `postMessage`): notes, next step, timer; the audience window follows |
| Deep links | `#/view/capability-view/CAP-05?overlay=target` — shareable state |
| Themes | light / dark **presenter chrome**; the diagrams stay on a light "paper" card (the renderer hard-codes white canvas and label boxes — themable diagrams are out of scope) |
| Print | a print stylesheet lays out one view per page (PDF hand-out) |

Motion: no `filter: blur / drop-shadow` during animation;
`prefers-reduced-motion` turns every animation into a cut. Accessibility:
every element focusable by keyboard, `aria-label` from name + type + id,
visible focus ring, contrast checked for both chrome themes. Fonts: system
stack `Helvetica, Arial, "Liberation Sans", sans-serif` (the renderer
measures text with Helvetica / Arial metrics), no embedded fonts.

Tour input (TXT, same style as the generator):

```
tour:
  - view: "Capability map" {caption: "Twelve capabilities, three to invest in"}
  - view: "Capability map" {focus: CAP-05, overlay: maturity}
  - view: "CAP-05 Ticketing" {caption: "Two processes depend on the legacy fare engine"}
  - view: "C4-L1 Fare engine" {overlay: target}
```

## 4. Scope decisions

- **In:** foundations (F0), the four views, the model extension, the
  presenter, skill instructions and examples.
- **Out:** live editing in the presenter (draw.io stays the editor);
  themable diagram colours; C4 Level 4, deployment and dynamic diagrams;
  any hosted service (the same HTML can be published later).
- **No external runtime dependency** — the presenter uses system fonts and
  no network; the generator stays standard-library Python.
- **C4 stays separate from EDGY pages** — mixing notations on one page is
  lint error **C007**, not a style choice.
- **The 24 core links do not change**; everything new is an influence verb,
  a flow verb or a C4 relationship.

## 5. Target state

| Skill | v2.3.0 | v2.4.0 |
|-------|--------|--------|
| edgy-diagram | 2.7.0 | **2.8.0** — document graph, page expansion, model ids in output, application / process / capability-view / matrix layouts, C4 notation, presenter |
| edgy-framework | 1.6.0 | **1.7.0** — modelling guidance for applications, data, actors and C4 |
| edgy-assessment | 1.9.0 | **1.10.0** — schema 1.9 with element relationships, views from the model, `presentation.html` as optional deliverable |
| edgy-target-state | 1.1.0 | **1.2.0** — application landscape and C4 per building block in the target-state pack; tour template |
| edgy-deep-dive | 1.1.0 | 1.1.0 (the presenter can open a pairwise map, no change) |

No breaking changes; all new keys are opt-in and `map_type: process`
keeps its current default.

## 6. Sprints and estimate

The presenter moves forward: it needs only F0's ids and the renderer, so the
user sees a working result after the second sprint, and every later sprint
adds its views to it.

| Sprint | Content | Estimate |
|--------|---------|----------|
| **21 — Foundations** | document graph, `expand:`, `edgyId` / `edgyType` / `edgyKind` / `edgyNotation` markers, quote-aware options, reserved keys, influence verbs (4 languages), schema 1.9, `edgy_model_to_txt --views` | 5–6 d |
| **22 — Presenter core** | renderer groups + `data-*` + attribute hardening, `edgy_present.py`, CSP, overview wall, drill-down zoom, cross-view highlight, search, deep links, chrome themes, print, `#selftest` — over today's map types | 5–6 d |
| **23 — Application map and process maps** | F1 (domains × layers layout, TIME preset, integrations, W124/W125, S013), F2 (chain with bands, swimlane with chips, W126), examples | 6–7 d |
| **24 — Capability view and matrices** | F3 (five bands, `hops`, capability matrix, CRUD matrix, W127 → qa.json), ArchiMate / diff mapping | 4–5 d |
| **25 — C4** | shape probe, C4 page parsing, L1 derivation, L2 / L3 layout, renderer C4 shapes, C4-PlantUML, C001–C007 and EDGY-rule switch-off, `expand: per-application` | 6–7 d |
| **26 — Presenter effects and release** | edge draw-in, spotlight, impact trace, current → target FLIP, heat overlays, tour, presenter window, reduced motion, a11y pass, skill instructions (assessment, target-state), eval set, README, CHANGELOG, v2.4.0 | 4–5 d |

Total ≈ **30–36 working days** (revision 1 said 18–22; it missed the
document graph, the id markers, the parser's option splitting, the lint
split for C4 and the renderer's shapes).

## 7. Tests to add

- `test_edgy.py`: document graph across pages; `expand:` page generation;
  quote-aware options; reserved keys not printed; `kind:` / `hosting:`;
  derived lanes, bands and process levels; bus threshold; `edgyId` written
  on every element cell.
- `test_lint.py`: C001–C007 each with a passing and a failing fixture; EDGY
  rules silent on `edgyNotation=c4` pages; new influence verbs accepted,
  `uses` on actor → asset still E010.
- Parser / QA warnings W124–W127 and `qa.json` entries; `test_semantic.py`:
  S013.
- `test_render.py`: every vertex / edge group carries `data-id`, ids unique
  per page and equal to the model ids; **hostile input** — a label
  `<script>` and a style `fillColor=#fff" onmouseover="x` — renders inert.
- `test_present.py` (new): HTML is self-contained (no `http(s)://`
  `src` / `href`), CSP present and its hashes match the inline script and
  style, embedded graph parses, every draw.io page appears once, the tour
  references existing views and ids, size budget (< 1.5 MB for 30 pages).
- **Browser self-test that runs in CI:** `presentation.html#selftest` does
  a drill-down, toggles an overlay, plays one tour step and writes the
  result and the `window.onerror` count into a DOM sentinel.
  `test_present.py` runs it with `edgy_render.find_chromium()` and
  `--headless --dump-dom` (standard library only; GitHub's `ubuntu-latest`
  runners ship Google Chrome, CI installs only `pyyaml`). Playwright
  screenshots stay a local tool for the eval report.
- `tools/edgy-eval.py`: eval model `eval/architecture-views.txt` (Acme
  Transit: 12 capabilities, 18 applications, 10 data assets, 6 actors,
  3 applications with C4 pages); every view generated from it with 0 errors
  and 0 visual findings; new `check.sh` step `edgy-architecture-views`.

## 8. Acceptance

1. From one fictional model the bundle produces, without manual draw.io
   work: an application map, a value chain and a swimlane process map, one
   capability view per capability, a capability × application and a CRUD
   matrix, and C4 L1 + L2 for every application with a C4 container page.
2. All of these pass `edgy_lint.py` with 0 errors (C4 pages under the C
   rules) and W108 / W111 / W113 = 0 in the eval set.
3. `presentation.html` passes the `#selftest` in headless Chromium in CI,
   drills from the capability map to a C4 container view in ≤ 3 clicks, and
   the tour plays end to end; with reduced motion there are no animations.
   Firefox and Safari are a manual release-checklist item.
4. A model change (rename an application) appears in every view and in the
   presenter after one regeneration.
5. `check.sh` green, privacy scan green (it also scans HTML), CHANGELOG and
   README updated.

## 9. Risks and limits

| Risk | Mitigation |
|------|------------|
| Applications and data are not EDGY elements | mapped to Asset with `kind:`, as the Asset tags already recommend; legend says "Asset (application)"; framework text explains the choice |
| Document graph changes the parser's page isolation | built as a pre-pass; single-page inputs keep today's code path; regression covered by every existing expected example |
| C4 shapes in draw.io differ between versions | probe first in Sprint 25; fall back to styled rectangles in the C4 colours |
| Presenter becomes a second renderer | it never computes layout; it only decorates the renderer's SVG |
| The presenter shows the native preview, which approximates draw.io | for publication quality use the draw.io CLI PNG / PDF; the presenter is for walking through the model |
| Effects hurt readability or performance | each effect in the F6 table has a purpose; one live view in the DOM; no filters during motion; reduced-motion path; effects off in print |
| XSS through labels or style values | attribute hardening in the renderer, `textContent` only, CSP with hashes, hostile-input tests |
| Presentation files leak client data | generated into the engagement folder only; `connect-src 'none'`; `.gitignore` pattern `*presentation*.html` outside `examples/`; privacy-scan scans HTML |
| Large landscapes (100+ applications) | grouping by domain, collapsed groups in the presenter, matrix page instead of edges |
| Licences | the C4 notation itself needs no licence; attribution is a courtesy on C4 legends and required only for copied C4 material; C4-PlantUML is referenced by `!include`, and if it is ever vendored its MIT notice goes into `NOTICE`; TIME credited to Gartner in the legend |

## 10. Changes from revision 1 (review findings)

| Finding (reviewer) | Change |
|--------------------|--------|
| `uses` actor → asset is not a core pair and raises E010 (feasibility, modelling) | new influence verb `interacts with`; core links stay 24 |
| no "extension verb" category; `precedes` undefined; `exchanges` duplicates `transfers` / `flows` (feasibility, modelling) | all new verbs are influence verbs; integrations use `transfers`; order is input order |
| data as Object contradicts the Asset tags in `vocabulary.md` (modelling) | data = Asset `{kind: data}` |
| `reads` / `updates` clash with core `creates`, no CRUD matrix (modelling) | one verb `accesses {crud:}` + CRUD matrix |
| model has no element-to-element relationships; version is already 1.8 (feasibility) | F0 / F5: `relationships[]`, arrays for actors, schema 1.9 |
| each page has its own parser (feasibility) | F0 document graph, Sprint 21 |
| `pages:` already reserved; `via` already an option (feasibility) | `expand:`; `{container: …}` |
| nested `c4:` block does not fit the parser; values split on commas (feasibility) | flat C4 page syntax; quote-aware options |
| new attributes print on the cards (feasibility) | reserved keys |
| linter sees only XML, C4 pages would trip E009 / W102 / W105 (feasibility) | style markers; W124–W127 as parser / QA checks; EDGY rules off on C4 pages |
| C006 used twice (modelling) | mixing notations is C007 |
| C4 uses *technology*, not *protocol*; Person mapping; grey scope; bus as hub (modelling) | F4 rewritten accordingly |
| `kind: saas` mixes kind and hosting (modelling) | `hosting:` attribute; optional criticality badge |
| capability view missed `product → capability: requires`; "people perform" is not a core link (modelling) | five bands; actors = organisation has / performs; outcomes opt-in via `hops: 2` |
| "+1 area" placement is arbitrary (modelling) | primary area via `{primary: true}` on the `requires` link |
| draw.io cell ids are sequential; no model id in the file (presenter) | `edgyId` style marker, no UserObject wrappers |
| renderer output is flat; style values unescaped → XSS (presenter) | specified grouping, attribute hardening, CSP, hostile-input tests |
| Playwright never runs in CI (presenter) | `#selftest` with headless Chrome `--dump-dom` |
| View Transitions cannot zoom inside SVG and blur vectors (presenter) | `viewBox` spring tween + cross-fade; FLIP for the current → target morph |
| dark theme conflicts with hard-coded renderer colours (presenter) | dark chrome, diagrams on a light paper card |
| effects: cut label fading, limit flowing dashes; add edge draw-in, spotlight, impact trace, presenter window (presenter) | F6 table |
| presenter could come earlier; estimate too low (presenter, feasibility) | presenter core is Sprint 22; 30–36 days over six sprints |

## Appendix A. Example inputs to add (all fictional)

| File | Content |
|------|---------|
| `examples/application-map.txt` | 18 applications in 4 domains × 3 layers, TIME badges, 14 integrations (bus) |
| `examples/process-chain-map.txt` | 5 L1 / 14 L2 processes (plan → sell → operate → inform → settle) in management / core / support bands |
| `examples/process-swimlane-map.txt` | ticket refund process, 4 actors, application chips |
| `examples/capability-view.txt` | `focus: CAP-05` and `expand: per-capability` variants, CRUD matrix page |
| `examples/c4-fare-engine.txt` | L1 + L2 for one application |
| `examples/eval/architecture-views.txt` | the eval model in §7 |
| `examples/presentation/tour.txt` | five-step tour over the eval model |
