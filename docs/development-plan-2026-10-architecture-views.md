# EDGY skills development plan (2026-10, part 4): architecture views and an interactive presenter

**Revision 5 (2026-10-16) — LOCKED. Approved by the maintainer after the Vibe and Codex follow-up reviews on PR #7; implementation of v2.4.0 (Sprints 21a–24) has started on this branch. Deviations found during implementation are recorded in `AGENT_LOG.md` and in §12. Scope:
v2.4.0 = foundations, application / process / capability views and a
presenter-lite in core; v2.5.0 = a separate `edgy-c4` skill in this repo;
presenter effects only after workshop demand.** Revisions 1–3 were
reviewed by four reviewer agents (generator feasibility, EDGY / C4
modelling, presenter front-end, adversarial second round); revision 3 by
two external agents (Vibe by Mistral, Codex) on PR #7 and by three more
agents on the repository boundary (case for keeping, split design,
finding verification); revision 4 by Vibe and Codex again (both support
the scope; revision 5 settles the contracts they asked for). Every accepted finding was checked against `main`;
§10 maps each one to its change. Follow-up to
[`development-plan-2026-10-coverage.md`](development-plan-2026-10-coverage.md)
(v2.3.0: edgy-diagram 2.7.0, edgy-assessment 1.9.0, edgy-framework 1.6.0,
edgy-target-state 1.1.0).

**Source — a feature request, not a review.** The request was for five
deliverables the bundle cannot produce today:

1. an **application map** (the application landscape);
2. a **process map** (value chain and process decomposition);
3. a **capability view**: one capability with the processes, applications,
   data and actors around it;
4. **C4 diagrams** for each application (system context, containers);
5. a **dynamic single-page web app** that presents all EDGY diagrams of an
   engagement with a strong visual effect.

The baseline below was read from `main` (3aef09c). All examples are
fictional (Acme Transit).

> 🔒 No client material was used for this plan. See the privacy rule in
> `CONTRIBUTING.md`. A generated presentation embeds the whole model — it is
> a client deliverable and is never committed to this repo (§9).

---

## 0. Repository boundary (decision)

The question raised on PR #7: which of these belong in an EDGY skills
repository, and do the presenter and C4 belong in another repository?

| Feature | Where | Release | Why |
|---------|-------|---------|-----|
| F0 Foundations | core (`edgy-diagram`, `edgy-assessment`) | v2.4.0 | ids, document graph and schema improve every EDGY output; every extension depends on them |
| F1 Application map, F2 Process maps, F3 Capability view, F5 One model | core | v2.4.0 | EDGY views over the Architecture facet; new inputs to existing layouts |
| F6a Presenter-lite | core (`edgy-diagram`) | v2.4.0 | a standard-library export like `edgy_render.py`; decorates its SVG, computes no layout |
| F4 C4 | **separate skill in this repo**, `skills/documentation/edgy-c4/` | v2.5.0 | another notation with its own parser rules, shapes, lint and output; kept out of the 3,400-line EDGY parser, but in the same repo so it shares install, CI and release tags |
| F6b Presenter effects | deferred — a v2.5.0 plan if workshops ask for them | — | product-grade UI with its own test burden; built only against the published contract |

**Why not separate repositories.** The adapters read one `registry.yaml`
from one repo at one ref (`EDGY_SKILLS_REPO` / `EDGY_SKILLS_REF`,
`adapters/claude-code/install.sh`) and copy whole skill directories; a
second repo needs a second registry, paired release tags, changes to four
adapters and a duplicated CI. A C4 repo would also have to fork the parser,
layout and renderer shapes. A separate *skill* gets the separation without
those costs. A companion repo stays possible for F6b once the contract is
frozen.

**README correction.** `README.md` says the skills contain "no code that
runs on your machine except the optional validation tooling in `tools/`".
That is already untrue (the skills ship ~12,800 lines of Python: generator,
linter, renderer, model tools). v2.4.0 corrects the sentence: skills ship
standard-library Python scripts that run only when the agent calls them.

## 1. What is covered today (baseline)

| Need | Closest existing feature | Gap |
|------|--------------------------|-----|
| Application map | `map_type: asset` (grid / tree), `map_type: reference` (lanes, actors left, `[external]` right, integration bus) | assets carry no kind; no lifecycle overlay; `rows:` is ignored when `group:` is used (`edgy_parser.py` ~2069) and a group inside a lane is not supported (~462), so *domains × layers* is a new layout |
| Process map | `map_type: process` = one sequence row (`_layout_sequence`), `lane:`, `stages:` columns, matrix | no value chain; lanes are derived from actors only in `map_type: task`, and only when the actor links to nothing but tasks (~2017) |
| Capability view | nested capability map; `edgy-deep-dive` pairwise map; `[focus]` tag (= thicker border) | no single-capability view; no page generation per element |
| Data | Asset tags already recommend `application` / `data` (`references/vocabulary.md` §Asset); flow verbs `flows`, `transfers`, `sends` | no data-access verb, no CRUD |
| Actors | `people`, `organisation`, role model | reusable as is |
| C4 | — | none |
| Presentation | multi-page draw.io, native SVG/PNG preview with `--preset presentation`, PDF report layout | **no interactive output** |
| Single source | `edgy-model.json` (shipped models: `schema_version "1.8"`), `edgy_model_to_txt.py`, model diff, ArchiMate export | links between element **types** only; `organisation` is one object; no `people` type; the validator (`tools/validate-edgy-model.py`) has no `oneOf` / `anyOf` |
| Document | `pages:` multi-page TXT (`edgy_document.py`) | **each page has its own parser** (~87); no document-level graph |
| Ids in output | `{id: CAP-05}` rendered as subtext | draw.io cell ids are sequential; relationships resolve by name only (`_find_element_id_by_value`, ~906) |
| Cross-skill scripts | `edgy_model_to_txt.py` imports `../../../documentation/edgy-diagram/scripts` | **works only in a repo checkout** — installed skills sit in `~/.claude/skills/<id>/`, so the import fails and the script exits (existing bug) |

What already helps: lanes, matrix, nested groups, status badges
(`{rating:}` + `rating_palette:`), transition overlay (`{change:}`),
`[external]` placement, `layout_from:`, and style markers the linter reads
(`edgyRole`, `edgyLang`).

## 2. Modelling decisions (EDGY mapping)

EDGY 23 has no *application* or *data* element; actors are People and
Organisation. Applications and data map onto **Asset**, following the Asset
tags the vocabulary already recommends, so they stay in the Architecture
facet and its colour:

| Concept | EDGY element | Marker | Notes |
|---------|--------------|--------|-------|
| Application / IT system | **Asset** | `{kind: application}` | also `kind: platform`, `kind: integration`; `[external]` as today |
| Data | **Asset** | `{kind: data}` | `{master: yes}`, `{owner: ORG-xx}`; Object stays the facet-neutral base element |
| Other resources | **Asset** | no kind, or `kind: material \| document \| …` | the capability view's resource band covers every asset, not only IT |
| Hosting (optional) | — | `{hosting: saas \| cloud \| on-prem}` | an attribute, not a kind |
| Actor | **People** or **Organisation** | — | existing role-model conventions |
| Process | **Process** | — | level derived from `contains` depth, never typed twice |
| Capability | **Capability** | existing ids, nested groups | |

`kind`, `hosting`, `master`, `owner`, `technology`, `crud`, `type`,
`criticality`, `data`, `container`, `time` and `gaps` join
`RESERVED_METRIC_KEYS` (`edgy_parser.py` ~277), otherwise they would be
printed on the card.

**Relationships.** The 24 core links do not change. New verbs are
**influence verbs** in `skills/_shared/edgy-core-links.yaml` (fi / en / fr /
de):

| Verb | Pair | Usage |
|------|------|-------|
| `stores` | asset (application) → asset (data) | system of record |
| `accesses` `{crud: R \| CU \| CRUD}` | process → asset (data) | one verb with an attribute, so a CRUD matrix can be drawn |
| `interacts with` | people / organisation → asset (application) | actor uses an application; not `uses`, which is core for task → channel only (E010). A working name: a sharper verb may replace it in Sprint 21a if it passes the core-spelling collision check |

Integrations reuse the flow verb **`transfers`** (asset → asset) with
`{data: AST-xx, technology: "REST"}`; the data name sits on a second label
line and the linter reads only the first line as the verb (changed in
Sprint 21; today it takes the whole value, `edgy_lint.py` ~509 / ~547). The
fi / fr / de spellings of new verbs must not equal any core-link spelling
(`käyttää`, `utilise`, `nutzt` are core `uses`); `render-core-links.py
--check` asserts it. No `precedes`: process order is input order, a `flows`
edge only for non-linear steps.

## 3. Features — v2.4.0 (core)

### F0 Foundations — P0

- **Document graph.** `edgy_document.py` builds one graph over all pages
  (elements by id, relationships with verb and attributes) before the
  per-page parsers run; single-page inputs keep today's code path.
- **Page expansion.** `expand: per-capability | per-application` (not
  `pages:`, the existing multi-page key), optionally `where: highlight` or
  a list of ids.
- **Identity: model id vs. occurrence.** Lookup by `{id:}`. The *model id*
  (`edgyId`) is canonical; each drawn *occurrence* has its own identity
  `edgyOcc=<page>/<cell>` that points to it. Rules in the document graph:
  - cross-view identity (derived views, highlight, diff, graph merge)
    **requires an explicit `{id:}`** — a missing id there is an error;
  - the type + name slug fallback is allowed only on standalone,
    single-page output, and is marked `edgyIdSource=slug` so no consumer
    treats it as stable;
  - the same id on several pages is normal (several occurrences);
  - the same id with conflicting type or name across pages → **E014**;
  - a duplicate id within one page → **E014**;
  - a relationship to an id that does not exist → **E015** (dangling);
  - a rename keeps the id and is reported by the diff as a rename, never
    as remove + add.
- **Model ids in the output.** The generator writes
  `edgyId=…;edgyType=…;edgyKind=…;edgyFacet=…` into each cell's style
  (draw.io keeps unknown style keys) and `edgyNotation=<name>` on pages of
  another notation. No `<UserObject>` wrappers (renderer and linter read
  `root.findall('mxCell')`).
- **Foreign-notation pages — fail closed.** The EDGY rules E009 (legend),
  W102 (colours) and W105 (verbs) are switched off only for `edgyNotation`
  values with a **registered notation handler** (a skill that declares the
  notation under the extension contract and is installed). An unknown
  value, or a known notation whose handler is not installed, gives **E013
  unsupported notation** — never a clean pass. **E012** flags EDGY and
  foreign cells on one page. A foreign-only page is validated by its
  handler; core reports which handler validated it. This is the hook
  `edgy-c4` uses in v2.5.0.
- **Options.** Quote-aware `{…}` splitting (values are split on every comma
  today, ~451 / ~831); relationship attributes `primary`, `crud`, `data`,
  `technology`, `container` added to the whitelist in
  `_parse_relationship_options` (~823) and kept in `rel['options']`.
- **Edge verb = first label line** in the linter.
- **Script location** (fixes the existing install bug). Cross-skill imports
  resolve, in order: `EDGY_DIAGRAM_SCRIPTS`, the sibling installed skill
  (`<skills dir>/edgy-diagram/scripts`), the repo-checkout path. SKILL.md
  files that use `G=skills/documentation/edgy-diagram/scripts` say how to
  find the installed path. An install test copies two skills the way the
  adapters do and runs `edgy_model_to_txt.py`.
- **Model schema `"1.9"`** (additive): `relationships[] {source_id,
  target_id, verb, attributes}`; `people` as a new element type;
  `organisation` as object **or** array; `id` required on elements
  referenced by `relationships[]`; `elements.asset[].kind`.
- **Migration contract — two separate promises.**
  - *Old input is accepted.* The validator gains `oneOf` / `anyOf` (it
    skips unknown keywords today, so `organisation` would go
    unvalidated); readers normalise with `_as_list` (already used by
    `edgy_model_to_txt.py`, `edgy_model_diff.py`,
    `edgy_model_to_archimate.py`); every shipped 1.8 model gives
    **byte-identical** TXT, diff and ArchiMate output (these outputs carry
    no style markers). Tests that index `["organisation"]["name"]`
    (`test_model_diff.py` ~50) use the normaliser; the assessment template
    and deep-dive text say "object or array".
  - *Old writers stay old.* Writers emit 1.9-only structures (arrays,
    `relationships[]`, `people`) only with `schema_version "1.9"`; a test
    asserts that a 1.8 write contains none of them.
  - *draw.io output does change — once, and only in style attributes.*
    The new markers (`edgyId`, `edgyOcc`, `edgyType`, …) land in every
    generated cell, so all `expected-*.drawio` examples are regenerated
    in Sprint 21a. A test compares old and new examples with the `edgy*`
    style keys removed and requires them to be identical — geometry,
    labels and every other style key unchanged (the coverage plan
    regenerated the box-legend examples the same way).
- **Extension contract** (new):
  `skills/documentation/edgy-diagram/references/extension-contract.md`
  with `assets/edgy-graph.schema.json` (document graph JSON) — style-marker
  grammar, `edgyNotation` values and which rules switch off, the SVG
  `data-*` / `class` / `data-role` attributes and their sanitising rules,
  the import entry points (`edgy_document.load_graph()`,
  `edgy_render.page_to_svg()`), notation-handler registration (for E013),
  and a contract number (`contract: 1`). Core CI runs a fixture-based
  contract test, so a break shows up here, not in an extension.
  **Designed against two consumers** before it is frozen: `edgy-c4` (needs
  graph, ids, notation registration, shape hook) and the deferred F6b
  presenter (needs SVG `data-*`, occurrences, paired states). The contract
  document has a section "changed because of the second consumer", so the
  contract is not shaped by `edgy-c4` alone.
- `edgy_model_to_txt.py --views` framework; each view adds itself.

### F1 Application map (`map_type: application`) — P0

- Applications grouped by **domain** (`group:`, nesting allowed) or, with
  `group_by: capability`, by the capability area that `requires` them. An
  application required by several areas sits in the area of its
  `{primary: true}` link; **without one it goes into a "Shared" strip** of
  the map with an info note — input order is never used.
- Optional layers as rows (`rows:` + `{row:}`); domains × layers is a new
  layout. `[external]` column on the right.
- **Lifecycle overlay** — Gartner TIME (`Tolerate / Invest / Migrate /
  Eliminate`) as an optional, labelled preset `rating_palette`, credited in
  the legend; a badge, never a fill. Optional second badge
  `{criticality:}` or `{hosting:}` — a second badge slot and legend keys
  are new work (`_badge_of`, ~1428).
- **Integrations** from `transfers`, data and technology on the second
  label line; several `transfers` on one pair (merged into one edge today,
  ~1450) list every data name. `edges: none | bus | direct` (default `bus`
  above 12).
- Transition overlay unchanged.
- Checks (parser / QA, from the document graph): **W124** application
  without an owner (`manages`) — **info by default**, a warning when the
  document sets `ownership: required` (edgy-target-state sets it; outside-in
  assessments rarely know owners); **W125** integration without a data
  asset; semantic **S013** asks "is this the system or the ability?" when
  an application's name equals or shares a stem with a capability it
  serves — a review question, never a demand to rename.

### F2 Process map (`map_type: process`, two variants) — P0

The default stays today's sequence row.

- **Value chain** (`process_view: chain`): L1 processes as the official
  pentagons in one row, L2 under each (from `contains`, stage-column
  layout), L3 with `depth: 3`; optional `band: management | core |
  support`.
- **Swimlane** (`process_view: swimlane`): one lane per actor that
  `performs` the process (lane derivation generalised from the task map),
  input order, used assets as chips under the step (`chips: assets`).
- **W126** on a banded chain: an L1 without `{band:}`, or an L2 with a band
  different from its parent.

### F3 Capability view (`map_type: capability-view`) — P0

One capability in the centre, five bands derived from the document graph:

```
                 ┌───── actors (organisation has / performs a realising process) ─────┐
 processes  ───▶ │                     CAP-05  Ticketing                              │ ───▶ resources
 (realises)      │        maturity 3 · owner: Fare team · TIME: invest                │      (requires: applications
                 └───── data (accessed by the processes, with CRUD) ──────────────────┘       and other assets)
                         products that require the capability (requires)
```

- `focus: CAP-05` draws one view; `expand: per-capability` one page per
  capability. The resource band shows every required asset, applications
  first, so the view also works for non-IT capabilities.
- `hops: 2` (opt-in) adds, dimmed: data stored by required applications,
  their integrations, outcomes the capability `contributes to`.
- **Matrices**: `map_type: capability-matrix` (capabilities × applications,
  cell = `requires` badge + TIME) and `matrix: crud` (processes × data).
- **W127 empty band with evidence status.** Written to a new `qa.json`
  array `model_gaps[] {rule, page, element_id, band, status}` — status
  `not_investigated` (default), `out_of_scope`, `unknown` or
  `confirmed_absent`, set with `{gaps: processes=out_of_scope}` on the
  focus element. Only `not_investigated` and `unknown` raise the warning;
  reports present `confirmed_absent` as a finding and the others as open
  questions, never the reverse. Additive to `qa.schema.json`.

### F5 One architecture model, many views — P0

One `edgy-model.json` (schema 1.9) or one multi-page TXT drives the
application map, both process maps, every capability view and the
matrices. `edgy_model_diff.py` covers the new keys;
`edgy_model_to_archimate.py` maps applications to *Application Component*,
data to *Data Object*, `stores` / `accesses` to *Access* (type from
`crud`), `transfers` to *Flow*.

### F6a Presenter-lite (`edgy_present.py`) — P1

**Output:** one self-contained `presentation.html` — no server, no CDN, no
network — built by a standard-library script from the draw.io file and the
document graph:

```
python edgy_present.py diagrams.drawio [--model model.json] -o presentation.html \
  [--title "Acme Transit target state"] [--theme dark]
```

**Architecture.** The presenter never computes layout: it inlines the
native SVG of `edgy_render.py` and decorates it. Renderer changes:

- each vertex in `<g class="el" data-id data-type data-kind data-facet>`
  with its shape and label lines; each edge in `<g class="edge" data-src
  data-tgt>`; legend cells `data-role="legend"`; ids from `edgyId`; cells
  without one shown, not interactive;
- repeated font attributes become CSS classes;
- **attribute hardening** — colours must match `#[0-9a-fA-F]{3,8}|none`,
  numbers must parse as floats, else a default. A security fix for every
  SVG consumer, presenter or not.

One live view in the DOM, the others in `<template>`. Graph embedded as
`json.dumps(...).replace('<', '\\u003c')`; text via `textContent` only;
hash parameters checked against known ids. CSP meta: `default-src 'none';
script-src 'sha256-…'; style-src 'sha256-…'; img-src data:; font-src
data:; connect-src 'none'; base-uri 'none'; form-action 'none'` — the page
cannot send the model anywhere.

**Five effects** — the ones that show "this is one model", chosen for
impact per line of code:

| Effect | What it does |
|--------|--------------|
| Card wall → zoom | all views as facet-coloured cards; a click tweens the SVG `viewBox` with a spring into the full view (crisp vector at every frame); *back* reverses |
| Cross-view highlight | hover / tap highlights an element and its 1-hop neighbours, dims the rest, and puts counter badges on the other views' cards where the same `edgyId` appears |
| Search | ⌘K / Ctrl+K palette over all elements and ids; jumps with the zoom |
| Current ↔ target (change annotations) | `T` switches a filter over the page's `{change:}` annotations with a cross-fade: *current* hides elements marked `new`, *target* hides elements marked `remove` (`replace` shows both, `decide` stays with a "?" badge); change badges pulse once. The `{change:}` overlay is a stroke colour on **one** diagram — there is no target model or target geometry — so the toggle is labelled "change annotations", never "target model", and does nothing on a page without annotations |
| Paging | ← / → step through pages in order (an implicit tour), `F` full-screen, deep links `#/view/<page>/<id>`, print stylesheet (one view per page) |

Overlays keep the facet fill: maturity / TIME / rating are shown by
enlarging the existing badges and adding a coloured outline ring (SKILL.md:
"a heat map keeps the facet fill"; W102). Light / dark **chrome**;
diagrams stay on a light paper card. `prefers-reduced-motion` turns every
animation into a cut.

**Effects cap.** These five are the whole F6a scope; a sixth effect goes to
F6b, no exceptions (a PR review check). F6a has its own acceptance (§9):
if it slips, it moves out of v2.4.0 without changing any graph or view
deliverable — no core feature depends on it. Keyboard-focusable elements with `aria-label`.
System font stack `Helvetica, Arial, "Liberation Sans", sans-serif`.

## 4. v2.5.0 and later (outside the v2.4.0 cut)

### F4 C4 — `edgy-c4` skill 0.1.0 (v2.5.0)

A separate skill in `skills/documentation/edgy-c4/` (own SKILL.md, version,
registry entry, `check.sh` step), built on the extension contract
(`contract: 1`) — it imports `edgy_document.load_graph()` and the renderer
entry point and never patches core files. Requires a `requires:` field in
the validator and registry (`requires: edgy-diagram >=2.8, contract 1`) and
transitive install in the adapters (Sprint 25).

- **Level 1 — System context**, derived from the document graph: People →
  Person; an internal Organisation acting as a user → Person; a partner's
  system → external Software System; out-of-scope systems grey; bus
  integrations shown as logical `transfers` with `technology: via <bus>`;
  warning when no Person interacts with the system.
- **Level 2 — Containers** on flat C4 pages (`notation: c4`, `level:
  container`, `system: AST-02`, `- container: "Fare API" {technology:
  "Kotlin, Spring Boot"}`, relationships in `relationships:` with
  description + `{technology:}`; boundary crossings attach via
  `{container: …}`).
- **L1 and L2 only.** Level 3 only if demand appears; it would grow C4 into
  its own modelling framework.
- `expand: per-application`; draw.io C4 shapes (`mxgraph.c4.*`, probed
  first; fallback styled rectangles) through a shape hook in the renderer;
  C4-PlantUML via `!include`; lint C001–C006 in the skill, E012 in core.
- **Conditional deliverable**: edgy-target-state draws C4 only for
  applications named in a decided building block — its building blocks are
  product-independent and many are not software systems.

### F6b Presenter effects (deferred)

Edge draw-in, spotlight mask, impact trace between two elements, a real
**two-state morph** (current and target pages paired with `{state: current
| target}` and matched by model id, FLIP to the target geometry), minimap, guided `tour:` file with captions, presenter
window (`window.open` + `postMessage`). A v2.5.0 plan only if workshops on
real engagements show demand; built against `contract: 1`, so it can also
live in a companion repo.

## 5. Scope decisions

- **v2.4.0 in:** F0, F1, F2, F3, F5, F6a, README correction.
- **v2.5.0:** `edgy-c4`; F6b if demanded.
- **Out:** live editing in the presenter; themable diagram colours; C4
  Level 4, deployment and dynamic diagrams; any hosted service.
- **No external runtime dependency**; generator and presenter stay
  standard-library Python.
- **The 24 core links do not change.**

## 6. Target state

| Skill | v2.3.0 | v2.4.0 | v2.5.0 |
|-------|--------|--------|--------|
| edgy-diagram | 2.7.0 | **2.8.0** — F0 (graph, ids, expansion, foreign-notation hook, contract), application / process / capability-view / matrix layouts, presenter-lite | 2.9.0 — shape hook for extensions |
| edgy-assessment | 1.9.0 | **1.10.0** — schema 1.9 + migration contract, views from the model, script-location fix, optional `presentation.html` | — |
| edgy-framework | 1.6.0 | **1.7.0** — modelling guidance for applications, data, actors | 1.8.0 — deriving C4 from the Architecture facet |
| edgy-target-state | 1.1.0 | **1.2.0** — optional application landscape when the model has `kind: application` assets; `ownership: required` | 1.3.0 — C4 L1/L2 for applications in decided building blocks |
| edgy-deep-dive | 1.1.0 | 1.1.1 — "organisation: object or array" | — |
| edgy-c4 | — | — | **0.1.0** |

No breaking changes for 1.8 inputs (migration contract in F0);
`map_type: process` keeps its current default.

## 7. Sprints and estimate

| Sprint | Content | Estimate |
|--------|---------|----------|
| **21a — Parser and graph** | document graph, identity rules (model id vs. occurrence, E014 / E015), `expand:`, style markers + one-time example regeneration with the style-only diff test, quote-aware options, relationship attributes, reserved keys, influence verbs (4 languages, collision check), first-line edge verb, script-location fix + install test | 5–6 d |
| **21b — Schema and contract** | schema 1.9, migration contract (validator `oneOf`, 1.8 byte-identical fixtures, 1.8-writer test), extension contract against two consumers + contract test, notation registration, E012 / E013 fail-closed, `--views` framework | 3–4 d |
| **22 — Presenter-lite** | renderer groups, `data-*`, hardening; `edgy_present.py`, CSP, the five effects, overlays as badges, chrome themes, print, `#selftest` — over today's map types | 5–6 d |
| **23 — Application and process maps** | F1 (domains × layers, Shared strip, TIME preset, second badge slot, integrations, W124 info/warning, W125, S013), F2 (chain, bands, swimlane, chips, W126), examples | 6–7 d |
| **24 — Capability view and release** | F3 (five bands, `hops`, matrices, W127 + `model_gaps[]`), F5 diff / ArchiMate mapping, eval set, skill instructions, README correction, CHANGELOG, **v2.4.0** | 5–6 d |
| *25 — edgy-c4 (v2.5.0)* | skill scaffold, `requires:` in validator / registry / adapters, renderer shape hook, L1 derivation, L2 layout, C001–C006, C4-PlantUML, target-state conditional | 6–7 d |
| *26 — Presenter effects (conditional)* | F6b items that workshops asked for | 4–5 d |

**v2.4.0 ≈ 24–28 working days**; v2.5.0 adds 6–7 days for C4 and up to 5
for effects. 21a and 21b are independent work packages, each reviewable on
its own; Sprint 22 needs only 21a. The presenter-lite comes in Sprint 22,
so there is a visible result after the second sprint.

## 8. Tests to add (v2.4.0)

- `test_edgy.py`: document graph across pages; `expand:`; quote-aware
  options; relationship attributes kept; reserved keys not printed;
  derived lanes, bands and levels; Shared strip; bus threshold; `edgyId` on
  every element cell.
- `test_lint.py`: E012; EDGY rules silent only on pages with a registered
  notation; **E013** for an unknown notation and for a known notation
  without its handler installed; new influence verbs accepted; `uses` on
  actor → asset still E010; first-line verb.
- Identity: same id on two pages → one model element, two occurrences;
  conflicting definitions and duplicate ids on a page → E014; dangling
  relationship → E015; slug ids marked `edgyIdSource=slug` and rejected
  for cross-view use; rename reported as a rename by the diff.
- Parser / QA: W124 (info vs. `ownership: required`), W125–W127,
  `model_gaps[]` statuses; `test_semantic.py`: S013 as a question.
- Model tools: validator `oneOf`; 1.8 fixtures byte-identical through
  to_txt, diff and ArchiMate; a 1.8 write contains no 1.9-only structure;
  1.9 arrays round-trip.
- Examples: every regenerated `expected-*.drawio` equals its previous
  version once the `edgy*` style keys are removed.
- Install: copy `edgy-assessment` and `edgy-diagram` as the adapters do and
  run `edgy_model_to_txt.py` from the copy.
- Contract: fixture-based test of the style markers, graph JSON schema and
  SVG `data-*` attributes.
- `test_render.py`: groups carry `data-id`, unique per page, equal to the
  model ids; hostile label `<script>` and style `fillColor=#fff"
  onmouseover="x` render inert.
- `test_present.py`: HTML self-contained (no `http(s)://` `src` / `href`),
  CSP hashes match, graph parses, every page appears once, < 1.5 MB for
  30 pages; **browser self-test in CI**: `presentation.html#selftest`
  zooms, highlights, searches and toggles current → target, then writes
  the result and the `window.onerror` count to a DOM sentinel, run with
  `edgy_render.find_chromium()` and `--headless --no-sandbox
  --virtual-time-budget=15000 --dump-dom file://…#selftest` (GitHub's
  `ubuntu-latest` ships Chrome; CI installs only `pyyaml`). **No silent
  skip:** without Chrome the `check.sh` step prints a visible SKIP and
  exits 2 (the existing environment-warning code) locally, and fails with
  exit 1 in CI. The self-test also checks that `T` does nothing on a page
  without `{change:}` annotations.
- `tools/edgy-eval.py`: `eval/architecture-views.txt` (Acme Transit:
  12 capabilities, 18 applications, 10 data assets, 6 actors); every view
  with 0 errors and 0 visual findings; `check.sh` step
  `edgy-architecture-views`.

## 9. Acceptance (v2.4.0)

1. From one fictional model, without manual draw.io work: an application
   map, a value chain and a swimlane process map, one capability view per
   capability, a capability × application and a CRUD matrix.
2. All pass `edgy_lint.py` with 0 errors; W108 / W111 / W113 = 0 in the
   eval set.
3. Renaming an application changes every view after one regeneration, and
   the diff reports it as a rename.
4. Every shipped 1.8 model gives byte-identical TXT, diff and ArchiMate
   output; regenerated draw.io examples differ only in `edgy*` style keys;
   the installed-skill test passes; E013 fires for unregistered notations.
5. **Presenter-lite, separate acceptance** (F6a can be moved out of v2.4.0
   without touching 1–4): `presentation.html` passes `#selftest` in
   headless Chrome in CI and shows exactly the five effects; the
   current ↔ target toggle filters only annotated changes; with reduced
   motion there are no animations; Firefox and Safari on the manual
   release checklist.
6. `check.sh` and privacy scan green (privacy scan also scans HTML);
   CHANGELOG, README (including the corrected code sentence) updated.

## 10. Risks and limits

| Risk | Mitigation |
|------|------------|
| Applications and data are not EDGY elements | Asset with `kind:`, as the Asset tags recommend; legend says "Asset (application)" |
| Document graph changes page isolation | pre-pass; single-page inputs keep today's path; every expected example is a regression test |
| Schema change breaks consumers | migration contract and 1.8 fixtures (F0) |
| Extension contract drifts | contract number, fixture test in core CI, extensions never patch core files |
| Presenter becomes a second renderer | it computes no layout; effects capped at five in v2.4.0 |
| The presenter shows the native preview, which approximates draw.io | for publication quality use the draw.io CLI PNG / PDF |
| XSS through labels or style values | renderer hardening, `textContent`, CSP with hashes, hostile-input tests |
| Presentation files leak client data | engagement folder only; `connect-src 'none'`; `.gitignore` `*presentation*.html` outside `examples/`; privacy-scan scans HTML |
| Model gaps reported as business findings | `model_gaps[]` evidence status; only `confirmed_absent` is a finding |
| Licences | TIME credited to Gartner; C4 (v2.5.0): attribution a courtesy for the notation, C4-PlantUML MIT notice only if vendored |

## 11. Change log of this plan

**Revision 5 — follow-up reviews of revision 4 (Vibe, Codex).** Both
support the revision 4 scope; these are the contract details they asked to
settle before implementation.

| Finding (source) | Change |
|------------------|--------|
| Sprint 21 overloaded with two independent packages (Vibe 1) | split into 21a (parser and graph) and 21b (schema and contract) |
| Contract written against one consumer becomes consumer-shaped (Vibe 2) | contract designed against `edgy-c4` and F6b, with a "changed because of the second consumer" section |
| Effects may creep one at a time (Vibe 3) | explicit cap: a sixth effect goes to F6b; F6a has its own acceptance and can slip without touching the views (also Codex) |
| `interacts with` is vague (Vibe 4) | kept as a working name; a sharper verb may replace it in 21a if it passes the collision check |
| Self-test must not skip silently without Chrome (Vibe 5) | visible SKIP + exit 2 locally, exit 1 in CI |
| Slug fallback vs. required ids; same id on several pages, conflicts, duplicates, dangling links, renames undefined (Codex 1) | identity rules: model id vs. occurrence (`edgyOcc`), slug only on standalone output and marked, E014 / E015, rename kept as rename |
| Byte-identical 1.8 output contradicts the new style markers (Codex 2) | two promises: old input accepted (TXT / diff / ArchiMate byte-identical) and old writers stay old; draw.io examples regenerated once with a style-only diff test |
| Current → target cross-fade has no data contract (Codex 3, verified: `{change:}` is a stroke overlay on one diagram) | F6a toggles a filter over change annotations, labelled as such; the real two-state morph with paired pages moves to F6b |
| Foreign-notation exemption could pass unknown notations (Codex 4) | fail closed: exemption only for registered handlers, E013 otherwise |
| Estimate | v2.4.0 ≈ 24–28 days |

**Revision 4 — repository boundary and external reviews (Vibe, Codex;
three boundary agents).**

| Finding (source) | Change |
|------------------|--------|
| C4 and the full presenter are a different product / notation (Vibe, Codex) | §0: C4 → `edgy-c4` skill in this repo, v2.5.0; presenter split into F6a (core, v2.4.0) and F6b (deferred) |
| Separate repos cost a second registry, paired tags, four adapters, duplicated CI, a forked renderer (boundary agents) | separate skill, not separate repo; companion repo possible for F6b only |
| README "no code" sentence is already untrue (boundary agents) | corrected in v2.4.0 rather than used as a scope argument |
| Existing bug: cross-skill import works only in a repo checkout (split-design agent, verified) | F0 script location + install test |
| Extensions need a published interface (split-design agent) | F0 extension contract, graph JSON schema, contract test; E012 foreign-notation hook in core |
| Shared application placed by input order (Codex 1) | Shared strip without `{primary}` |
| S013 cannot infer an error from a name (Codex 2) | S013 is a review question |
| W127 must separate missing evidence from a real gap (Codex 3) | `model_gaps[]` with four statuses |
| Heat colour wash breaks the facet-fill rule (Codex 4) | overlays enlarge badges and add an outline ring |
| C4 "per building block" does not fit product-independent building blocks (Codex 5) | conditional: only applications in decided building blocks, v2.5.0 |
| organisation object → array needs a migration contract; validator has no `oneOf` (Codex 6, verified) | F0 migration contract |
| W124 noisy in outside-in assessments (Vibe) | info by default, warning with `ownership: required` |
| Resource band only for applications (Codex) | band shows every required asset |
| Presenter scope that still impresses (user-value agent) | five effects in F6a |

**Revision 3 — second review round (9 findings):** relationship options
are a whitelist; elements resolve by name only; a second label line broke
W105 / E010; edges on one pair are merged; no `people` type in the schema;
reserved keys incomplete; one badge slot; fi / fr / de spellings could equal
core `uses`; `--dump-dom` dumped before the self-test ended; Sprint 21 scope
and W126 corrected.

**Revision 2 — first review round (22 findings):** `uses` actor → asset
raises E010 → `interacts with`; no extension-verb category, no `precedes`,
`exchanges` duplicated `transfers`; data as Object contradicted the Asset
tags; `reads` / `updates` → `accesses {crud}`; model had no
element-to-element relationships; each page had its own parser; `pages:`
and `via` were taken; nested `c4:` block did not fit the parser; new
attributes printed on cards; the linter sees only XML; C4 *technology* not
*protocol*, Person mapping, grey scope; `kind: saas` mixed kind and
hosting; capability view missed `product → capability: requires`; draw.io
cell ids are sequential; renderer output flat and style values unescaped;
Playwright never runs in CI; View Transitions cannot zoom inside SVG; dark
theme conflicts with renderer colours; effects trimmed; estimate too low.

## Appendix A. Example inputs to add (all fictional)

| File | Release | Content |
|------|---------|---------|
| `examples/application-map.txt` | v2.4.0 | 18 applications in 4 domains × 3 layers, Shared strip, TIME badges, 14 integrations (bus) |
| `examples/process-chain-map.txt` | v2.4.0 | 5 L1 / 14 L2 processes in management / core / support bands |
| `examples/process-swimlane-map.txt` | v2.4.0 | ticket refund process, 4 actors, asset chips |
| `examples/capability-view.txt` | v2.4.0 | `focus: CAP-05`, `expand: per-capability`, `gaps:` statuses, CRUD matrix page |
| `examples/eval/architecture-views.txt` | v2.4.0 | the eval model in §8 |
| `skills/documentation/edgy-c4/examples/c4-fare-engine.txt` | v2.5.0 | L1 + L2 for one application |
