---
name: edgy-diagram
version: "2.5.0"
description: >
  Create EDGY-notation diagrams as draw.io XML (multi-page mxfile) or PlantUML
  source and export them to PNG/SVG/PDF. Generator-first workflow
  (edgy_generator.py) with core-link pair validation, an influence-verb
  vocabulary, a drawio linter (edgy_lint.py) and a CLI-free SVG/PNG preview
  (edgy_render.py) that the agent must look at before delivery. Uses the EDGY facet model
  with draw.io CLI or the plantuml-stdlib `<edgy/edgy>` library for rendering.
category: documentation
tags: [diagram, drawio, visualization, documentation, edgy, enterprise-design, fi, en, fr, de]
languages: [fi, en, fr, de]
agents:
  - claude-code
  - cursor
  - generic
inputs:
  - name: facet
    type: enum
    values: [identity, architecture, experience, all]
    description: EDGY facet (Identity, Architecture, Experience or All)
  - name: map_type
    type: enum
    values: [capability, organisation, outcome, journey, activity, process, purpose, brand, product, object, asset, channel, content, people, story, task, reference, summary]
    required: false
    description: >
      Map type (overrides facet layout). 16 EDGY map types backed by layout
      strategies (grid / tree / sequence / hub-and-spoke / hierarchy / role model /
      area containers) plus two EDGY-extension layouts: `reference` (layered
      reference architecture with lanes) and `summary` (stakeholder picture).
      Note: pairwise deep-dive diagrams are documented separately and generated
      via direct XML by the edgy-deep-dive skill — they are not handled by
      edgy_parser.py.
  - name: elements
    type: text
    description: List of EDGY elements and their relationships
  - name: format
    type: enum
    values: [drawio, png, svg, pdf, plantuml, puml]
    default: drawio
    description: >
      Output format. `drawio` = draw.io XML; `plantuml`/`puml` = PlantUML
      source using `<edgy/edgy>` stdlib; `png`/`svg`/`pdf` = rendered image
      (engine selected via --engine).
  - name: engine
    type: enum
    values: [drawio, plantuml, native]
    default: drawio
    description: >
      Render engine for png/svg/pdf. `drawio` uses draw.io CLI; `plantuml`
      uses plantuml.jar or `plantuml` binary (one image per page for
      multi-page input); `native` is the pure-Python SVG renderer with PNG
      through headless Chromium when available (approximate, no pdf).
      Ignored when format is drawio/plantuml/puml.
  - name: language
    type: enum
    values: [fi, en, fr, de]
    default: fi
outputs:
  - type: file
    description: Generated EDGY diagram file (drawio, png, svg or pdf)
examples:  # representative subset — full list in examples/README.md
  - input: examples/identity-facet.txt
    output: examples/expected-identity.drawio
  - input: examples/full-edgy-map.txt
    output: examples/expected-full-edgy.drawio
  - input: examples/multipage-map.txt
    output: examples/expected-multipage.drawio
  - input: examples/capability-areas-map.txt
    output: examples/expected-capability-areas.drawio
  - input: examples/reference-architecture-map.txt
    output: examples/expected-reference-architecture.drawio
  - input: examples/archimate-positioned.txt
    output: examples/expected-archimate-positioned.drawio
---

# EDGY Diagram Skill

## Purpose

This skill generates draw.io diagrams with EDGY notation and exports them to the desired format. It uses the EDGY facet model and draw.io CLI for diagram generation and export.

Use this skill when:
- You need an EDGY-notation diagram for enterprise architecture
- You want to visualise EDGY facet model elements and their relationships
- You need a diagram that follows the EDGY 23 standard

**IMPORTANT:** Use the relationship verb matching the `language` parameter from the core links table below.

## Agent Instructions

### Generation workflow: generator → lint → preview

**Use the generator whenever Python 3 is available.** Write the TXT input,
generate, lint, preview, deliver. Write draw.io XML by hand only when Python
cannot run, and then only for diagrams under ~15 cells — still lint it later.

1. Parse the user's elements and relationships; verbs come from the
   core-link and influence vocabularies, never invented. No core link fits →
   influence verb (dashed), never a new solid Link.
2. Write `<name>.txt` (Input Format below).
3. `python3 scripts/edgy_generator.py <name>.txt --output <name>.drawio --preview`
   — read every warning on stderr (wrong pair, unknown verb, layout notes);
   input errors (unknown `facet` / `map_type`) exit 2.
4. `python3 scripts/edgy_lint.py <name>.drawio` — **0 errors** required.
5. Open the preview (`<name>.svg` / `.png`), walk the *Preview loop*
   checklist, fix the **input**, regenerate. Never deliver a diagram you have
   not looked at.
6. Export png/svg/pdf if asked (Export section).

### XML essentials (details: `references/xml-reference.md`)

- Every `mxCell` is a direct child of `<root>`; containment is `parent="…"` with geometry relative to the parent. Never nest `<mxCell>` elements.
- Every edge has `<mxGeometry relative="1" as="geometry"/>`; ids are unique; XML special characters escaped once; UTF-8.
- Shapes follow the base type: Outcome → rounded rectangle (`rounded=1;arcSize=10`), Activity → pentagon (`shape=mxgraph.arrows2.arrow`), Object → rectangle, People → person. Brand / Product / Organisation are rectangles.
- Palette: Identity `#80ffb7`, Architecture `#a6c0ff`, Experience `#ff99bd`, Brand `#ffd580`, Product `#e599ff`, Organisation `#80eaff`; white stroke, width 2, bold 14 px label.
- Edge styles: Link `endArrow=classic;endFill=1`, Flow `endArrow=open;endFill=0`, Tree `endArrow=none`, Influence `endArrow=open;endFill=0;dashed=1`; all `edgeStyle=orthogonalEdgeStyle;rounded=1`.
- The generator wraps pages in an uncompressed `<mxfile>`; a bare `<mxGraphModel>` is also valid.
- A legend (element colours + line styles) is mandatory; the generator adds it.

### Validation — run the linter before delivery

```bash
python3 scripts/edgy_lint.py <name>.drawio                       # 0 errors required
python3 scripts/edgy_lint.py --warnings-as-errors <name>.drawio  # strict (shipped examples)
python3 scripts/edgy_lint.py --visual <name>.drawio              # W111–W114 only, JSON with coordinates
```

The linter checks structure (flat `mxCell` tree, edge geometry, dangling
source/target, duplicate ids), layout (no negative / off-page coordinates with
parent chains resolved, no overlaps > 30 %, text fits), notation (legend,
palette, intersection shapes, no type word in labels) and semantics (core-link
verb only on an allowed pair, non-core verb never in core-link style, verbs
from the vocabulary). Exit 1 = fix before delivery; warnings do not block but
must be read.

**Visual rules (W111–W114)** run on the same resolved geometry the preview
draws (`edgy_geometry.py`: ports, orthogonal joins, waypoints, label boxes),
so a clean structural lint is no longer mistaken for a readable picture:
W111 an edge passes through an element that is not its source or target,
W112 an edge label lies on an element, W113 a label lies on another label (a
parent → children fan with one verb is one bus and is allowed), W114 a label
or edge end leaves the page. They are warnings: fix them by moving the
element, adding `via:` waypoints, changing `from:`/`to:`, or using `label:
source|target`; `--visual` gives the cell ids and coordinates for a script to
act on. A delivery should have none; `--warnings-as-errors` enforces that.

**Language (W116).** With `language:` set, the generator renders the legend
and every vocabulary verb in that language (`contains` → `sisältää`,
`requires` → `vaatii`; the model keeps the canonical verb) and the linter
reads the map language from the legend title (`--language` overrides).
W116 fires when an edge label is a vocabulary verb of another language — an
English `contains` left in a Finnish map, for example. Free text is never
flagged.

**Semantic review (purpose maps).** Notation and geometry say nothing about
meaning: a purpose map can lint clean while its "purposes" are development
actions. `python3 scripts/edgy_semantic_review.py <name>.txt` (or
`edgy_generator.py … --semantic-review`) raises the questions a reviewer
must answer — S001 action as a Purpose, S002 Outcome measures nothing,
S003 / S004 missing provenance (`[confirmed]` / `[analytical]` /
`[proposed]`, `{status: confirmed|proposed}` on Outcomes), S005 `contains`
that may be an influence, S006 metric in a Purpose name — with the reason
and the question for each. It flags; it never decides: exit 0 unless
`--strict`, and zero findings is not an approval. The sign-off is a person's
(edgy-framework, *Purpose map semantic review*).

If the linter cannot run, check by hand that the file has more than the
two structural cells, one `vertex` per element, one `edge` with geometry per
relationship, and is larger than 1000 bytes.

### Generator reference

```bash
edgy_generator.py in.txt --output out.drawio [--preview] [--bare] [--lenient] [--publication]
edgy_generator.py in.txt --format svg|png --engine native --output out      # CLI-free render
edgy_generator.py in.txt --format png|svg|pdf [--engine drawio|plantuml|native] [--preset presentation|print|web]
edgy_generator.py in.txt --format plantuml --output out.puml
edgy_render.py out.drawio [--out DIR] [--no-png] [--publication]            # preview an existing file
edgy_lint.py out.drawio [--warnings-as-errors] [--visual] [--scale 0.4]     # lint; W115 below 6 pt at that scale
```

`--publication` crops the native SVG/PNG to the content (shapes, routes,
arrowheads, labels, legend) instead of the editor page and prints an
orientation hint (`landscape` / `portrait` / `square`) per page — use it for
the image that goes into a report, the plain preview for editing. Text is
measured with glyph tables (`scripts/edgy_text.py`, Helvetica/Arial metrics)
in the generator, the preview and the linter alike, so box widths, wrapping
and W101 agree; a long name widens the box up to 280 px and then wraps —
text is never shrunk silently.

Output is an uncompressed `<mxfile>` with one `<diagram>` per page (`--bare`
gives a bare `mxGraphModel`, single page only). The vocabulary the generator
validates against is generated from `skills/_shared/edgy-core-links.yaml`
into `scripts/edgy_core_links.py` — change the YAML, run
`tools/render-core-links.py`, never edit the module or the tables.

## EDGY Facet Model (summary)

Three facets, each with one Outcome / Activity / Object element: **Identity**
(Purpose, Story, Content — *why*), **Architecture** (Capability, Process,
Asset — *how*), **Experience** (Task, Journey, Channel — *what role in
people's lives*). Three intersection elements bridge them: **Organisation**
(Identity ↔ Architecture), **Product** (Architecture ↔ Experience), **Brand**
(Identity ↔ Experience). Four base elements (People, Activity, Outcome, Object)
apply to every facet; Outcome carries KPIs. `facet: identity` includes Brand
and Organisation, `architecture` Organisation and Product, `experience` Brand
and Product, `all` all three. Full tables: `references/vocabulary.md`.

## Input Format

### Formal Syntax

```
facet: identity | architecture | experience | all
map_type: capability | organisation | journey | purpose   # optional, overrides facet layout
legend: box | strip                                       # optional; strip = one band along the bottom, page as tall as the content
language: fi | en | fr | de                               # optional; legend, generated headings and vocabulary verbs render in this language
translate_verbs: true | false                             # optional (default true): with language: set, a vocabulary verb written in another language is rendered translated ("contains" → "sisältää"); the model keeps the canonical verb

elements:
  - <element_type>: "<name>"
  - <element_type>: "<name> - <description>" [tags] {id: X, change: new, size: M, primary: true, metric: value}
  - <element_type>: "<name> | <subtext>"
  - group: "<area name>"              # container; the indented elements below are its children
    - <element_type>: "<name>"
  - lane: "<layer name>"              # borderless band; the indented elements sit on it
    - <element_type>: "<name>"

relationships:
  - "<source name>" -> "<target name>": "<verb>"
  - "<source name>" -> "<target name>": "<verb>" {from: right, to: left, via: [(x,y)], change: replace, label: source, label_dx: -30, label_dy: 20}
  # OR by type (only works if there is exactly one element of that type):
  - <source_type> -> <target_type>: "<verb>"
```

Names are matched on the part before ` - ` / ` | ` (the *name*), so a
relationship can say `"Ticketing"` for `"Ticketing - sell and validate fares"`.

### Multi-page input (`pages:`) and ArchiMate positioning (`layout_from:`)

```
facet: architecture              # document-level default for every page
pages:
  - name: "Roles and actors"
    elements: …
    relationships: …
  - name: "Systems"
    map_type: asset
    elements: …
```

Each page gets its own layout and legend and becomes a draw.io tab; previews
are written per page (`<base>-<page>.svg`). Example: `examples/multipage-map.txt`.

`layout_from: current-state.archimate#View name [scale=1.5 dx=0 dy=0]` keeps
every element that matches a view element by name at the view's (scaled)
position — "same place = same responsibility" when a target state is shown
next to an existing ArchiMate current state. Unmatched elements go below;
view elements missing from the input are reported (mark them `remove` or
add them). Standard-library XML parsing, no Archi needed. Example:
`examples/archimate-positioned.txt`.

### Grouping, Lanes and Nesting

Containment is the `parent` attribute with geometry relative to the parent;
the generator handles it:

- **`group:`** → container (`container=1`): capability areas, blocks with
  nested capabilities, any Tree with more than three children. Members in a
  2–4-column grid or as a tidy tree when they have tree relationships; groups
  are placed in rows.
- **`lane:`** → borderless band with a title; members sit **on** it at root
  level so edges may cross lane borders. Lanes stack top-down; edges between
  non-adjacent members of a row are routed over the top.
- **Facet containers** are automatic: `facet: all` → Identity / Architecture /
  Experience containers with Organisation between the first two, Product
  between the last two, Brand below; a single facet → one container plus the
  intersection elements below, three per row. Your own `group:`s take over.

Groups and lanes are structure, not EDGY elements (no relationships, light
tint / light grey). Examples: `examples/capability-areas-map.txt`,
`examples/lanes-map.txt`; XML in `references/routing.md`.

### Relationship Source/Target Matching Logic

In relationships, source and target are matched to elements in the following order:

1. **Exact match** — value matches the element name completely (preferred)
2. **Prefix match** — value matches the element name prefix before ` - ` separator
3. **Type match** — value matches the element type (e.g. `purpose`)

**IMPORTANT:** Use the element's exact name in quotes for relationships. This prevents incorrect matches when two elements have similar names (e.g. "Test" and "Test System").

### Labels: name, subtext, id, tags and metrics

**Label standard.** The element shows its **name** in bold on the first line.
Everything else is small subtext: `[ID]` and the description on the second
line, tags and metrics on a third. The element's **width follows the name**,
its height grows with the subtext lines — so long descriptions no longer
overflow. Do **not** repeat the element type in the name (`"Capability
Ticketing"`): the type is shown by shape and colour, and the linter warns
(W109).

```
elements:
  - capability: "Ticketing - sell and validate fares in every channel" {id: CAP-05}
  - asset: "Fare engine | runs on-prem until 2027" [application, owned] {cost: high, size: M}
  - task: "Registration" [functional] {satisfaction: ok}
```

Reserved keys inside `{…}` (not rendered as metrics):

| Key | Values | Effect |
|-----|--------|--------|
| `id` | any short code (`PUR-01`, `CAP-05`, `ADR-004`) | rendered as `[ID]` in the subtext; use it for cross-references in documents |
| `change` | `keep`, `new`, `change`, `replace`, `remove`, `decide` (fi/fr/de synonyms accepted) | transition overlay — see below |
| `size` | `S` 120×60 (map), `M` 200×90 (card), `L` 270×120 (block) | minimum size class |
| `highlight` | `yes` | dark 4 px border, e.g. first-round decision units (same as the `[focus]` tag) |

Everything else in `{…}` is a metric and is colour-coded as before:

Recommended tags per element type (in-house/outsourced, differentiating/commodity, application/data, digital/physical …) and metric colour coding (good/ok/bad, low/high in four languages) are listed in `references/vocabulary.md`.

### Comments and Empty Lines

- Comments start with `#` and are ignored
- Empty lines are allowed anywhere

### Relationship Types

EDGY 23 defines four relationship types:

| Type | Visual Style | When to Use |
|------|-------------|-------------|
| **Link** (core link) | Solid line, directional arrow | Official 24 core links (below) |
| **Flow** | Solid line, open arrowhead | Data/information/value/material transfers concretely |
| **Tree** | Solid line, no arrowhead | Hierarchy: decomposition, portfolios, organisational structures |
| **Influence** | Dashed line, open arrowhead | Other influence/guidance (default) |

### Influence verbs (for everything that is not a core link)

Influence is the default relationship type: a dashed line with an open
arrowhead. Use one of these verbs (matching the `language` parameter) whenever
the pair is not one of the 24 core links — for example `capability → purpose`
or `process → outcome`. **Do not invent a new solid Link relationship**, and
do not reuse a core-link verb on a pair it does not belong to: the generator
and the linter flag such edges and draw them as influence.

<!-- edgy-links:begin format=influence -->
| EN | FI | FR | DE | Typical use |
| ---- | ---- | ---- | ---- | ------------- |
| enables | mahdollistaa | permet | ermöglicht | A makes B possible |
| guides | ohjaa | guide | steuert | A steers or constrains B |
| influences | vaikuttaa | influence | beeinflusst | generic influence when nothing more specific fits |
| offers | tarjoaa | offre | bietet | A makes B available (non-core product/channel pairs) |
| manages | hallinnoi | gère | verwaltet | A administers B (organisation → asset |
| reflects | heijastaa | reflète | spiegelt | B mirrors A (content → brand |
| strengthens | vahvistaa | renforce | stärkt | A reinforces B |
| defines | määrittelee | définit | definiert | A sets the scope or rules of B |
| depends on | riippuu | dépend de | hängt ab von | A cannot exist without B (non-core pairs; core pairs use requires) |
| produces | tuottaa | produit | bringt hervor | process → outcome: a process yields a measurable result |
| measures | mittaa | mesure | misst | outcome → purpose: an outcome (KPI) measures a purpose |
| contributes to | edistää | contribue à | trägt bei zu | capability → purpose or outcome: bridge when no core link exists |
<!-- edgy-links:end -->

`supports`/`tukee` is the core link brand → task; on any other pair it is
reported as a wrong pair — use `enables` or `strengthens` instead.

### Core links, flow and tree keywords (tables: `references/vocabulary.md`)

The 24 official core links (four languages, allowed pairs), the flow and
tree keywords, the recommended tags per element type and the natural-language
→ element table live in `references/vocabulary.md`. Rule of thumb: a core-link
verb is valid **only** for its listed source → target pair (`requires` /
`vaatii` for three pairs, everything else for one); flow = `flows`,
`transfers`, `produces data`, `returns`; tree = `contains`, `comprises`,
`decomposes`. Element types: `purpose content story capability asset process
task channel journey brand product organisation people activity outcome object`.

### Relationship options

```
- "Platform" -> "Legacy engine": "depends on" {from: top, to: bottom, via: [(760, 300)], change: replace, label: source}
```

`from` / `to` override the automatic exit and entry side; `via` adds explicit
waypoints (page coordinates — use after a first preview); `change` colours the
edge with the transition overlay; `label` moves the verb towards the source or
target. Two relationships between the same pair are merged into one edge
labelled `verb1 / verb2`. Full rules by diagram size: `references/routing.md`.

## Routing and space usage by diagram size

| Size | Cells | Rules |
|------|-------|-------|
| Small | < 10 | automatic: `edgeStyle=orthogonalEdgeStyle;rounded=1`, distributed anchors, ≥ 80 px horizontal and ≥ 60 px vertical spacing, coordinates on the 10 px grid |
| Medium | 10–25 | set `{from:, to:}` where the automatic side is wrong; share a channel with `via:`; `{label: source}` for short verbs |
| Large | > 25 | `lane:` bands, one integration bus (`{size: L}` Asset) instead of n×m edges, vertical channels, feedback loops with explicit waypoints; move influence edges to a second page |

Details and XML patterns (waypoints, lanes, invisible anchors, bus,
containers): `references/routing.md`. Whatever the size: preview, look, fix
the input.

## EDGY Facet Model Layout (facet: all)

Three facet containers side by side; the intersection elements sit **between
the facets they bridge**, so core links stay short:

```
┌ Identity ──┐         ┌ Architecture ─┐          ┌ Experience ┐
│ Purpose    │ [Org]   │ Capability    │ [Product]│ Task       │
│ Content    │         │ Asset         │          │ Channel    │
│ Story      │         │ Process       │          │ Journey    │
└────────────┘         └───────────────┘          └────────────┘
                 [ Brand — Identity ↔ Experience bridge ]
                 [ base elements: people, activity, outcome, object ]
```

Container width follows the widest member; Tree relationships inside a facet
are laid out as a tree inside the container. A single facet (`identity`,
`architecture`, `experience`) gives one container with a 2–4-column grid and
the intersection elements below it, three per row.

## Map Types

`map_type` overrides the facet layout. Thresholds come from the official
EDGY 23 example maps (`examples/official/decoded/PATTERNS.md`); below *Min*
the parser warns.

| Map type | Layout | Min | Recommended |
|----------|--------|----:|------------:|
| `capability` | **area containers** (`group:`) in rows; grid + tree without groups | 8 | 15–30 |
| `organisation` | **role model** when Process elements exist (roles as columns, actors under the role they `perform`); tree otherwise | 8 | 15–30 |
| `purpose` | **hierarchy**: top purposes → sub-purposes (`contains`) → Outcomes (`measures`); Organisation and Brand in the top row, Content left, Story right | 6 | 10–15 |
| `outcome` | grid + tree | 5 | 7–10 |
| `journey`, `activity`, `process` | sequence (pentagon row, left → right) | 4 | 6–8 |
| `brand`, `product`, `object` | hub-and-spoke | 5–6 | 7–15 |
| `asset`, `channel`, `content`, `people`, `story`, `task` | grid (`cols ≈ √N`) | 5–8 | 7–30 |
| `reference` *(extension)* | lanes top-down, Organisation/People left, `[external]` right, overlay strokes, one integration bus | 8 | 10–25 |
| `summary` *(extension)* | who / does what / what results; warns above 4 boxes per row | 3 | 6–10 |
| `triad` *(extension)* | **planned ring** for `facet: all` or one facet: one *primary* element per type carries the core links (`{primary: true}`, else the first of its type), straight border-to-border lines, two links detour along the page edge; the other elements sit in **"Further <type>" panels** without lines and their links are reported, not drawn; strip legend by default | 6 | 12 primaries + any number of further |

Never model focus areas as Story in a purpose map; formulate capabilities as
system-independent result nouns, 6–12 areas and 40–80 leaves (edgy-framework,
*Formulating capabilities*). Input/layout sketches per strategy and the
**pairwise map** spec used by `edgy-deep-dive`: `references/map-types.md`.
Examples: `examples/purpose-hierarchy-map.txt`,
`examples/organisation-roles-map.txt`, `examples/reference-architecture-map.txt`,
`examples/summary-map.txt`.

## Transition Overlay (EDGY extension — current → target state)

EDGY 23 has no notion of change; this overlay colours the **stroke only**,
the fill stays the facet colour, so the map stays valid EDGY. Say "EDGY
extension" in the delivery. `{change: …}` on elements (stroke width 4) and on
relationships (width 1.5, edge takes the colour of its change); the legend
gains a "Transition (extension)" block automatically.

| `change` | fi | stroke |
|----------|----|--------|
| `keep` | säilyy | `#6b778c` grey |
| `new` (strengthen) | uusi / vahvistuu | `#006644` green |
| `change` (merge, extend) | muuttuu | `#b26b00` amber |
| `replace` | korvautuu | `#c25100` orange |
| `remove` | poistuu | `#bf2600` red |
| `decide` (open, see ADR) | päätettävä | `#bf2600` red, dashed |

Example: `examples/transition-overlay.txt`.

## Preview loop (mandatory before delivery)

Lint finds structural and semantic errors; only a picture shows overlaps,
cut text, spaghetti routing and labels on boxes. Generate with `--preview`
(or run `edgy_render.py`), open the PNG/SVG and check:

- [ ] no edge passes through a box and no edge label lies on a box or another label — `edgy_lint.py --visual` must report nothing (W111–W114 = 0)
- [ ] every edge visibly starts and ends at an element; no diagonal end segments on orthogonal routes
- [ ] nothing cut off or overlapping; text fits its element
- [ ] legend clear of content; page height ≤ 1.5 × width (otherwise pages or another map type)
- [ ] no element twice; intersection elements between the facets they bridge
- [ ] a stakeholder could explain it in a minute — otherwise reduce or split

Fix the **input** (order, shorter names, `map_type`, fewer relationships,
pages) and regenerate; never patch the XML. Without Chromium the SVG opens in
any browser or IDE; the render is approximate but enough for this list.
Record in the delivery which preview was used.

## Error Handling

- **Unknown element type** → Use white rectangle: `fillColor=#ffffff;strokeColor=#262626` (warning)
- **Relationship source/target not found** → Skip relationship and warn user
- **Missing facet value** → Default: `identity`
- **Unknown `facet` or `map_type` value** (e.g. `all-facets`) → error, generator exits 2; fix the input (`--lenient` forces generation for debugging only)
- **Core-link verb on a pair that is not a core link** → warning, drawn as influence; change the verb or the pair
- **Verb outside the vocabulary** → warning, drawn as influence; pick a verb from the influence table
- **Preview cannot be written** (`--preview`) → error, generator exits 3 after writing the `.drawio`; a missing PNG (no Chromium) is not an error — the SVG is enough for the preview loop

## Export

| Need | Command |
|------|---------|
| draw.io file (default) | `edgy_generator.py in.txt --output out.drawio` |
| preview SVG/PNG, no CLI | `--preview` or `edgy_render.py out.drawio` |
| publication PNG/SVG/PDF | `--format png|svg|pdf` with the draw.io CLI; presets `--preset presentation|print|web` |
| PlantUML source / render | `--format plantuml`, or `--format png --engine plantuml` (uses `<edgy/edgy>` stdlib) |
| approximate PNG/SVG without CLI or Java | `--format png|svg --engine native` |
| report image cropped to content, orientation hint | `--publication` with `--preview`, `--engine native` or `edgy_render.py`; `legend: strip` in the input keeps the page tight |

Details, output naming, PlantUML macro mapping, the official EDGY 23 stencils
and draw.io CLI locations: `references/export.md`.

## Delivery

One diagram = one `.drawio` (all pages inside) plus one preview image per
page, named `<subject>_<diagram>_v<N>.<ext>`. Remove superseded versions when
a new one is accepted so readers never find two truths. Readers without a
draw.io plug-in see the image, so always ship the PNG (draw.io CLI export or
the native preview) next to the `.drawio`. Write into wikis, trackers or other
external systems only when the user asks, and then place each diagram next
to the section it belongs to. Say in the delivery which layouts are EDGY
extensions (transition overlay, `reference`, `summary`).

## Dependencies

- Python 3.7+ and `xml.etree.ElementTree` (standard library) — for `edgy_generator.py`, `edgy_lint.py`, `edgy_render.py` (SVG), the shared `edgy_geometry.py` / `edgy_text.py` and the generated `edgy_core_links.py`; Pillow is used for text measurement only when it happens to be installed together with a Liberation/Arimo/Arial font, never required
- Headless Chromium / Chrome — optional, for PNG previews from `edgy_render.py` (`EDGY_CHROMIUM=<binary>` overrides detection)
- draw.io CLI (for draw.io export to png/svg/pdf)
- PlantUML (`plantuml.jar` + Java, or `plantuml` binary) — optional, only
  required when rendering PlantUML output to png/svg/pdf. `.puml` source
  generation has no extra dependencies.
