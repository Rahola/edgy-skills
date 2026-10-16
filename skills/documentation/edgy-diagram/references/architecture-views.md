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
  in format 1.9 (edgy-assessment).
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

## Presenter

`edgy_generator.py … --present presentation.html` (or `edgy_present.py`)
writes one self-contained, offline HTML page of every view: card wall →
zoom, cross-view highlight with occurrence counts, ⌘K search, current ↔
target filter over `{change:}` annotations, paging, deep links and print.
It inlines the native preview SVG and computes no layout.

## Extension contract

The style markers (`edgyId`, `edgyType`, `edgyKind`, `edgyOcc`, `edgyRole`
…), the document graph JSON (`--graph`) and the SVG `data-*` attributes are
extension contract 1: `references/extension-contract.md`.
