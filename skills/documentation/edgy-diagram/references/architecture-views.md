# Architecture views (edgy-diagram 2.8.0)

The application map, the two process maps, the capability view and the two
matrices. Every view stays **EDGY notation**: applications and data are
Assets with `{kind: application | platform | integration | data}` (the
Asset tags EDGY recommends), processes are Processes, owners and performers
Organisations or People. The views are layouts over the same elements, and
one model drives all of them.

Examples (fictional Acme Transit): `examples/application-map.txt`,
`examples/application-by-capability-map.txt`,
`examples/process-chain-map.txt`, `examples/process-swimlane-map.txt`,
`examples/capability-view-map.txt`; the eval model
`examples/eval/architecture-views.txt` draws every view from one model page.

## One model, many views

A page with `draw: false` feeds the **document graph** and is not drawn.
Every element with an explicit `{id: …}` is one model element, wherever it
appears. A view page refers to it by id and never repeats it:

```
pages:
  - name: "Model"
    draw: false
    elements:
      - capability: "Sales in every channel" {id: CAP-05}
      - asset: "Fare engine" {id: APP-07, kind: application, time: invest}
      - asset: "Fare rules" {id: DAT-01, kind: data}
      - process: "Sell in every channel" {id: PRO-22}
      - organisation: "Fares team" {id: ORG-02}
    relationships:
      - "CAP-05" -> "APP-07": "requires" {primary: true}
      - "PRO-22" -> "CAP-05": "realises"
      - "PRO-22" -> "DAT-01": "accesses" {crud: R}
      - "ORG-02" -> "PRO-22": "performs"

  - name: "Application map"
    map_type: application          # an empty application / process / matrix page is derived from the graph
  - name: "Capability"
    map_type: capability-view
    expand: per-capability         # one page per capability ("Capability · CAP-05 …"), focus set per page
```

- `expand: per-capability | per-application | per-process` writes one page
  per element of that type (explicit ids only); `where: A, B` limits it to
  those ids, `where: highlight` to highlighted elements, `where: top` to the
  top of the `contains` hierarchy (L1 processes).
- `edgy_model_to_txt.py MODEL.json --views application,process-chain,process-swimlane,capability,capability-matrix,crud-matrix`
  (or `--views all`) writes this multi-page TXT from an `edgy-model.json`
  in format 1.9 (edgy-assessment). `all` leaves out a matrix the model
  cannot fill (no `requires` / no `accesses` relationships) and says so.
- Identity rules: two different definitions of one id, or one id twice on a
  page, are **E014**; a relationship to an id that exists nowhere is **E015**.
  An element without `{id:}` gets a slug id (`edgyIdSource=slug`) — fine on
  one page, never matched across views.

## Application map — `map_type: application`

| Key | Effect |
|-----|--------|
| `group:` | domains, as on every map |
| `rows: Channel, Core, Shared` + `{row: …}` | domains × layers matrix (domains become the columns) |
| `group_by: capability` | an application sits in the area of the capability that `requires` it — the link with `{primary: true}`, else the single requiring capability; several without a primary → **Shared** strip; none → **Not required by a capability**. The capabilities themselves are not drawn |
| `[external]` | **External systems** column |
| `{time: tolerate \| invest \| migrate \| eliminate}` | lifecycle badge (Gartner TIME, extension; fi / en / fr / de labels) |
| `{criticality: …}` or `{hosting: …}` | second badge |
| `edges: direct \| none` | integrations as edges (default up to 12) or counted on the cards |
| `ownership: required` | W124 becomes a warning |
| `route: auto \| none` | orthogonal routing through the channels between the cards (default on for this map) |

Integrations are `transfers` between assets with `{data: DAT-…, technology: …}`
— the label's second line names the data and the technology. Owners
(`manages` from an Organisation, or `{owner: ORG-…}`) and data assets are
folded onto the cards and labels, not drawn as cards; the generator prints a
`Note:` for each folding. **W124** an application without an owner (note by
default); **W125** an integration without a data asset.

## Process maps — `map_type: process`

- `process_view: chain` — the value chain / process landscape: L1 processes
  (no `contains` parent) as a row of pentagons, their L2 children stacked
  under each (`depth: 3` adds L3); `{band: management | core | support}` on
  the L1 processes gives three rows. **W126** an L1 without a band on a
  banded chain, or an L2 with another band than its parent.
- `process_view: swimlane` — one lane per Organisation or People that
  `performs` a step, the leaf steps as a staircase in input order, the assets
  a step `requires` as a chip line under it (`chips: assets`, default on).
  From a model, write one page per L1 process (`expand: per-process`,
  `where: top`): a single swimlane of every process is a staircase of
  unrelated steps.

## Capability view — `map_type: capability-view`

`focus: CAP-…` (or `expand: per-capability`) draws one capability in the
centre and five bands from the graph:

| Band | From |
|------|------|
| actors (top) | Organisation `has` the capability; Organisation / People `performs` its processes |
| processes (left) | Process `realises` it |
| resources (right) | Assets it `requires` (applications first) |
| data (below) | data Assets its processes `accesses`, CRUD on the label |
| products (bottom) | Product `requires` it |

`hops: 2` adds the resources' stored data and integration partners as dimmed
context. An empty band is **W127** with an evidence status set on the focus
element — `{gaps: "products=out_of_scope; data=confirmed_absent"}`:

| Status | Reported as |
|--------|-------------|
| `not_investigated` (default), `unknown` | warning — an open question |
| `out_of_scope` | note |
| `confirmed_absent` | note; a report may present it as a finding |

Every W127 is also written to `qa.json` `model_gaps[]` (element, band,
status, page) — a model gap, never a layout error, and never a business
finding unless `confirmed_absent`.

## Matrices — `map_type: capability-matrix`

- default (`matrix: requires`): capabilities × applications, ● requires,
  ◉ the primary area.
- `matrix: crud`: processes × data assets with the CRUD letters of
  `accesses {crud: …}`.

The cells are decorations (`edgyRole=matrix`), the links they show are not
drawn as edges (reported as a `Note:`), and the legend defaults to a strip.

## Realisation trace — `expand: trace` (2.9.0)

The trace answers *what realises this?* from the customer's journey down to
the organisations, and *what does this serve?* back up. One page per element
with an id, linked by click:

```text
  - name: "Trace"
    map_type: trace
    expand: trace            # where: JRN-01, CAP-05 | highlight | from JRN-01
    legend: strip            # trace_direction: both (default) | down | up
```

| Level | Elements |
|-------|----------|
| 1 | Journey |
| 2 | Task, Channel |
| 3 | Product |
| 4 | Capability |
| 5 | Process, Asset, People |
| 6 | Organisation |

**A page** shows the focus and its **direct neighbours** (one hop) over the
trace links: *above* the lower levels (dimmed), *beside* the same level,
*below* the higher levels, grouped by level with a row header. Every edge
keeps its EDGY verb and direction. Links walked: *is part of*, *traverses*,
*uses*, *serves*, *features in*, *offers* (product → channel), *requires*,
*creates*, *realises*, *accesses*, *interacts with*, *performs*, *makes*,
*has*, *manages* and *contains* (people of an organisation; within one type,
*contains* gives the *part of / parts* chips). Flows are not walked, and
people → process is never drawn (E010).

**Pages and links.** `expand: trace` writes a **trace index** (journeys |
organisations) and one page per element with an id at levels 1–6; an element
without an id is counted in a note. `where:` narrows the set: ids,
`highlight`, or `from JRN-01` (everything reachable downwards; upwards with
`trace_direction: up`). Page ids are stable: `trace-<id>` (plus six hex
characters when the id has `/`, `:` or `.`), the index is `trace-index`. A
card links to its page (draw.io `UserObject link="data:page/id,…"`) only
when the page is in the document; the others are drawn without a link and
counted in a note. Above 100 pages a note suggests a narrower `where:`.

**Crowded bands.** More than 12 cards in a band: 11 cards and a "+N more"
card that links to a list page (`<page>-more-above|below`, a grid of 5).
A row of more than 8 cards draws no edges; the row header names the verbs
instead. A level row of more than 5 cards of several types (tasks and
channels) becomes one row per type.

**Gaps.** An empty *below* band is **W129** with the W127 evidence statuses,
set per element type with `{gaps: …}` and written to `qa.json`
`model_gaps[]`:

| Type | `gaps` keys | W129 checks |
|------|-------------|-------------|
| journey | tasks, channels, products | tasks |
| task | products, channels | products |
| channel | products | products |
| product | capabilities, processes, organisation | capabilities |
| capability | actors, processes, resources, data, products, organisation | processes, resources |
| process, asset, people | organisation (process also resources) | organisation |

W129 never runs on `up` pages or on organisations.

**From a model.** `edgy_model_to_txt.py model.json --views trace` (format
1.10 with the Experience links); it is not part of `--views all`.

**C4 badge.** When the delivery has a C4 system context of an application
(`notation: c4`, edgy-c4), its card on the trace pages gets a separate
"C4" badge linking there; the card keeps its trace link.

## Presenter

`edgy_generator.py … --present presentation.html` (or `edgy_present.py`)
writes one self-contained, offline HTML page of every view: card wall →
zoom, cross-view highlight with occurrence counts, ⌘K search, current ↔
target filter over `{change:}` annotations, paging, deep links and print.
It inlines the native preview SVG and computes no layout.

With a realisation trace the trace pages are **one Trace card** (the index).
The first click on a card inspects it; the "→" badge or a second click opens
its trace page. Routes are `#/trace/JRN-01/TSK-03/…` (each id
`encodeURIComponent`-encoded) in the browser history, so *back*, *forward*,
refresh and copied links work; a breadcrumb shows the path taken. A "C4"
badge opens the C4 page, and *back* returns to the trace. Drill-through is
part of effect 5 (paging and deep links): still five effects.

## Extension contract

The style markers (`edgyId`, `edgyType`, `edgyKind`, `edgyOcc`, `edgyRole`
…), the document graph JSON (`--graph`) and the SVG `data-*` attributes are
extension contract 1: `references/extension-contract.md`.
