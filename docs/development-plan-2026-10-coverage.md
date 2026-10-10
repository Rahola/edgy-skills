# EDGY skills development plan (2026-10, part 3): coverage — maps and diagrams the skills cannot produce yet

**Revision 1 (2026-10-10) — proposal, not yet implemented.** Follow-up to
[`development-plan-2026-10-semantics-and-layout.md`](development-plan-2026-10-semantics-and-layout.md),
whose Sprints 13–16 shipped as **v2.2.0** (edgy-diagram 2.6.0,
edgy-assessment 1.8.0, edgy-framework 1.5.0).

**Source — a coverage review, not field feedback.** The question was: *which
maps, diagrams and workflows does the bundle not handle yet, and where are
the shortcomings?* Three inputs were compared:

1. the 16 official EDGY 23 example maps
   (`skills/documentation/edgy-diagram/examples/official/`, patterns in
   `examples/official/decoded/PATTERNS.md`);
2. the generator's layout dispatch, options and lint/semantic rules on
   `main` (3619d8b);
3. the diagram kinds that assessment and target-state deliveries ask for
   beyond the 16 official maps (heat maps, touchpoint matrices, roadmaps,
   model diffs, hand-off to other tools).

Every claim below was verified by generating a probe input against `main`
and reading the resulting XML, preview and lint output; the probe inputs are
listed in Appendix A. All examples are fictional (Acme Transit).

> 🔒 No client material was used for this review. See the privacy rule in
> `CONTRIBUTING.md`.

---

## 1. What is covered today (baseline)

| Area | Covered | Note |
|------|---------|------|
| Map types | 16 EDGY types + `reference`, `summary`, `triad` | all official types have a layout |
| Layouts | grid, tidy tree, sequence, hub-and-spoke, purpose hierarchy, organisation role model, task inventory (lanes × stages) and path, triad ring, pairwise map | |
| Structure | one level of `group:` / `lane:`, automatic facet containers | **no nesting** (§2.1) |
| Overlays | transition (`change:`), `size`, `highlight`, `[focus]`, `{id}` | **no metric/status overlay** (§2.8) |
| Quality | lint E001–E011, W101–W121 (incl. layout quality, series), semantic review S001–S006 (**purpose maps only**, §2.9), qa.json | |
| Output | draw.io (multi-page), PNG/SVG/PDF via draw.io CLI, native SVG/PNG with presets, PlantUML | no ArchiMate export, no interactive output (§2.11) |
| Input | TXT, `pages:`, `layout_from: *.archimate#View` | **no draw.io as layout source** (§2.7) |
| Scale | 64 elements in 8 areas: 7.6 s, 0 errors, clean preview | large maps are not a problem |
| Analysis skills | reframing, intersections, identification, target-state mode, capability formulation, purpose semantic review, deep-dive lenses | thin on the Experience facet (§2.9) |

Maps that already match the official pattern well and need no action:
activity / journey / process rows, brand hub, asset tree, organisation tree
and role model, purpose hierarchy, people persona grid, story grid, channel
and content grids (with one level of `group:`).

## 2. Findings

Priority: **P0** blocks a common deliverable; **P1** forces manual draw.io
work or leaves a known error unflagged; **P2** quality or integration;
**P3** nice to have.

### 2.1 Nested groups are flattened (P0)

The official capability map is three-tier: outer area (facet colour) →
white sub-group → 130 × 60 leaves, 30–60 elements. The parser accepts
`group:` only at one level. A `group:` indented under another `group:`
becomes a *sibling* and the outer group is left empty:

```
  - group: "Customer Management"
    - group: "Sales"
      - capability: "Lead handling"
```

→ three sibling containers, "Customer Management" has no children and
lint reports **W106 container has no children**. No warning says the
nesting was ignored. Evidence: `edgy_parser.py` keeps a single
`current_group` and `group_indent`; `self.groups[...]` has no parent field.

Impact: the most common capability-map shape (area → sub-area → capability,
40–80 leaves as `edgy-framework` *Formulating capabilities* recommends)
cannot be produced without manual draw.io work.

### 2.2 `stages:` is ignored without lanes (P1)

The official task map groups 30–60 tasks by journey stage ("Inspiration",
"Make first plans", …) with **no** stakeholder lanes and no containers. Our
inventory layout only builds stage columns when lanes exist or a People /
Organisation element is linked to the tasks. A task map with `stages:` and
`{stage: …}` but no lanes silently falls back to a 2-column grid; the stage
is dropped without a warning (probe: 6 tasks, 3 stages → grid at
x = 60 / 290, no headers).

### 2.3 Only one grouping axis (P1)

Three official or frequently requested maps are a **matrix**, not a row of
groups:

- channel map: *Physical / Digital* × *Synchronous / Asynchronous* (the
  official map has both axes as labels);
- journey touchpoint map: journey stages (columns) × channels or people
  (rows) with the tasks or touchpoints in the cells;
- transition roadmap: waves or quarters (columns) × capability areas (rows)
  with building blocks in the cells.

Today the lanes × stages matrix exists only inside `map_type: task`
(`_prepare_task_lanes`, `_layout_group_members` stage branch). The other
map types get `group:` for one axis only.

### 2.4 Product portfolio is drawn as a hub (P1)

The official product map is a portfolio **tree** (portfolio → product lines
→ products → cards) with composition marks. `map_type: product` always uses
hub-and-spoke; a 7-product probe with `contains` links produced two
**W111 edge passes through element** warnings because spokes cross the
ring. The organisation map already switches to a tidy tree when tree
relationships exist; product (and brand, object) do not.

### 2.5 Outcome web crosses itself (P2)

The official outcome map is a small web (6–12 outcomes, 6–12 named links).
`map_type: outcome` uses `grid_tree`: a grid, then a tree if tree
relationships exist. An 8-outcome / 8-link probe (`enables` chain with two
branches) produced W111 twice and W113 (overlapping edge labels). A layered
layout by link direction (causes left, effects right, longest path first)
would remove the crossings for webs of this size.

### 2.6 Container styling differs from the official maps (P2)

Our `group:` container is light grey (`#eef2f7`); the official outer
container is the facet colour with a white stroke and the sub-group is
white with no stroke. Readers who know the official maps read our grey
areas as "structure" rather than "capability area". Needed together with
§2.1 because the two tiers must look different.

### 2.7 Hand-adjusted draw.io positions are lost on regeneration (P1)

The skill says *never patch the XML, regenerate from TXT*. When a reviewer
has moved cards in draw.io, the next regeneration discards those positions.
`layout_from:` reads its file as an Archi `.archimate` model. A `.drawio`
file is parsed the same way, no view is found, and the warning says the
view is missing rather than that the format is unsupported
(`_positions_from_archimate`). Reusing an existing `.drawio` page as the position
source, matched by element name, would make "edit in draw.io, keep the
change, regenerate the rest" a supported loop instead of a dead end.

### 2.8 No metric or status overlay (P1)

Assessment and target-state deliveries routinely ask for a capability heat
map (maturity 1–5, strategic / commodity, owner, risk). The generator has
`change:` (stroke colour, a transition extension), `size:` and `highlight`
only; other `{key: value}` metrics are rendered as text. EDGY fixes the
fill to the facet colour, so a heat map must be an **extension with its
own legend row**, like the transition overlay: a corner badge or a
coloured status bar inside the card, never a fill change. Nothing flags a
map that colours fills by hand.

### 2.9 Semantic review stops at purpose maps (P1)

S001–S006 run only when `map_type == 'purpose'`
(`edgy_semantic_review.py:110`). The same class of error — valid structure,
wrong meaning — is common in the other delivered map types and is not
checked:

- capability map: system or team names as capabilities ("SAP", "Sales
  team"), verb phrases ("Manage fleet"), a capability that is really an
  activity or a project;
- task map: tasks phrased from the organisation's point of view ("Process
  refund") instead of the person's ("Get my money back");
- outcome map: outcomes that are activities ("Implement CRM") or have no
  measure.

`edgy-framework` has guidance for capabilities (*Formulating capabilities*)
but none for the Experience facet: Journey appears only in the
intersection questions and core-link lists, and there is no guidance on
journey stages, task wording, touchpoints or channel classes.

### 2.10 No model diff (P2)

The transition overlay needs every element tagged by hand
(`{change: new}`). Two `edgy-model.json` files (current and target) can be
compared mechanically: added, removed, renamed and re-linked elements →
TXT with `change:` tags → transition map. Today this is done by the agent
reading both models.

### 2.11 Export and hand-off (P2 / P3)

- **ArchiMate Open Exchange export (P2)** — the bundle *imports* ArchiMate
  positions (`layout_from:`) but cannot write an `.archimate` or Open
  Exchange file; architecture teams that keep Archi as the system of record
  must re-type the model. The mapping is mechanical (capability → Capability,
  process → Business Process, organisation → Business Actor, outcome →
  Outcome, asset → Resource, product → Product).
- **Interactive HTML page (P3)** — a clickable map with the capability card
  text on hover is a frequent ask for workshops; the native SVG renderer
  already has every element's geometry and text.
- **Mermaid — not pursued.** Mermaid has no EDGY shapes or facet colours;
  the PlantUML `<edgy/edgy>` library already covers the text-diagram case.

### 2.12 Uneven group rows (P2)

- W118 is right on an 8-area capability map (3 rows of equal-height
  containers): the gap between rows 1 and 2 is 44 px and between rows 2
  and 3 only 34 px. The row placement of `group:` containers does not use
  one fixed row gap.
- Group containers in a row keep their own heights (probe: 196 px and
  276 px side by side), so the official "equal-height areas per row" look
  needs manual trimming.

### 2.13 Accessibility palettes (P3)

Facet colours are fixed by EDGY. A grayscale print or a colour-vision
deficiency check (Identity green vs Organisation cyan, Experience pink vs
Product violet) has no support: no `palette: print` with hatch patterns,
no contrast report in qa.json.

## 3. Scope decisions

- **Stay inside EDGY 23 for the notation.** Nested groups, matrices, trees
  and the outcome web are layouts of EDGY elements. Status badges, the
  model diff and the roadmap are *extensions* and are drawn and legended
  as such, like the transition overlay and `triad`.
- **No free-form journey maps** (emotion curves, pain points, swimlanes
  with icons). The touchpoint matrix (§2.3) is the EDGY-faithful version.
- **No general graph layout engine.** The outcome web gets a layered
  layout for ≤ 15 nodes; above that the map is split (`pages:`), as the
  publication rule already says.
- **draw.io stays the deliverable; ArchiMate is an export.** No two-way
  synchronisation.
- **Defaults stay.** New layouts are chosen from the input (as the
  organisation and task maps already do); every new option is opt-in and
  documented in `map-types.md`; existing fixtures must not change
  (regression guard in `tools/check.sh`).

## 4. Target state

A user writes any of the 16 official maps as the official example shows it
(nesting, stage grouping, matrices, portfolio trees, outcome webs) and gets
a clean preview without manual draw.io work. The semantic reviewer flags
the common meaning errors in capability, task and outcome maps. A
maturity / status overlay and a current-vs-target diff are produced from
the model, legended as extensions. Positions adjusted in draw.io survive
regeneration. The model can be handed to Archi.

## 5. Actions

### P0 — Nested groups (edgy-diagram 2.7.0)

- **P0.1 Parser**: `group:` under `group:` (any depth, lanes only at the top
  level); `groups[gid]['parent']`; members of a sub-group are laid out
  inside it, sub-groups in a grid inside the parent; `group_columns`
  applies per level. Warning when a lane is nested.
- **P0.2 Styling**: `group_style: official` (default when nested groups
  exist, otherwise opt-in): outer = facet colour of its members when they
  share one, white stroke; sub-group = white, no stroke, bold title.
  `group_style: light` keeps today's grey.
- **P0.3 Lint**: W106 message names the likely cause (nested `group:` not
  supported before 2.7.0); new W122 when a container's facet colour does
  not match its members.
- **P0.4 Docs and examples**: `examples/capability-areas-nested.txt`
  (3 tiers, ~40 leaves, Acme Transit), `map-types.md` capability section,
  SKILL.md *Grouping, Lanes and Nesting*.

### P1 — Stage columns and matrices (edgy-diagram 2.7.0)

- **P1.1** `stages:` without lanes → stage headers and columns for
  `map_type: task` (official pattern), with a warning for tasks without a
  stage.
- **P1.2** Generalised matrix for grid map types: `columns:` (+ `{column:}`)
  and `rows:` (+ `{row:}`) or `lane:` as rows; reuse the task stage code
  (`_stage_headers`, `_layout_group_members` stage branch) so there is one
  implementation. Covers the channel 2 × 2, the journey touchpoint map
  (`map_type: journey` with `columns:` = stages, rows = channels/people,
  cells = tasks) and the roadmap (columns = waves).
- **P1.3** Group rows: one fixed gap between rows of containers (fixes the
  W118 finding in §2.12); equal row heights for containers in one row when
  `align_groups: grid`.

### P1 — Trees, webs and layout reuse (edgy-diagram 2.7.0)

- **P1.4** `map_type: product` (and `brand`, `object`): tidy tree when
  `contains` / `is composed of` tree relationships exist, hub-and-spoke
  otherwise — the same switch the organisation map has.
- **P1.5** `map_type: outcome`: layered layout by link direction when the
  map has ≥ 1 directed link and ≤ 15 outcomes; grid otherwise. Label
  placement reuses the W113 geometry so labels never overlap.
- **P1.6** `layout_from: file.drawio#Page name [scale dx dy]`: positions by
  element name from an existing draw.io page, chosen by file extension;
  unmatched elements go below with a warning (same contract as the
  ArchiMate source). An unsupported extension gets its own warning.

### P1 — Status overlay and semantic review (edgy-diagram 2.7.0, edgy-framework 1.6.0)

- **P1.7** `{status: …}` and `{maturity: 1–5}` reserved metrics → coloured
  status bar at the bottom of the card (fill stays the facet colour),
  legend row "Status (extension)" with the used values; `status_palette:`
  document key for custom labels; lint W123 when a card fill is not a
  facet colour (hand-coloured heat map).
- **P1.8** Semantic review for capability maps (S007 system/team name,
  S008 verb phrase, S009 activity-as-capability), task maps (S010
  organisation-voice task), outcome maps (S011 activity-as-outcome, S012
  outcome without measure). Vocabulary via `edgy_vocab.py` so fi/en/fr/de
  work; `edgy-framework` gains *Formulating tasks and outcomes* and an
  Experience-facet modelling section (journey stages, touchpoints, channel
  classes).
- **P1.9** `edgy-assessment` Phase 4b runs the extended review on every
  generated map, not only purpose maps; `qa.json` records the rule set.

### P2 — Diff and hand-off (edgy-assessment 1.9.0, edgy-diagram 2.7.0)

- **P2.1** `edgy_model_diff.py current.json target.json → transition.txt`:
  added / removed / renamed (fuzzy by name and id) / re-linked elements,
  `change:` tags, summary table; `edgy-target-state` uses it for the
  building-block transition map.
- **P2.2** `edgy_model_to_archimate.py`: ArchiMate 3.1 Open Exchange XML
  from `edgy-model.json` with one view per map; element and relationship
  mapping table in `references/export.md`; validated with the Open
  Exchange XSD in tests.
- **P2.3** CHANGELOG v2.3.0, README, registry, examples regenerated,
  `tools/check.sh` steps for diff and ArchiMate export.

### P3 — Later

- Interactive HTML export from the native renderer.
- `palette: print` (grayscale with hatch patterns) and a contrast line in
  qa.json.

## 6. Sequencing and estimate

| Sprint | Content | Skills |
|--------|---------|--------|
| 17 | P0.1–P0.4 nested groups and official styling; P1.1 stage columns; P1.3 lint noise | edgy-diagram 2.7.0 |
| 18 | P1.2 generalised matrix (channel, journey touchpoints, roadmap); P1.4 product tree; P1.5 outcome web; P1.6 draw.io layout source | edgy-diagram 2.7.0 |
| 19 | P1.7 status overlay; P1.8 semantic review S007–S012 and framework guidance; P1.9 assessment integration | edgy-diagram 2.7.0, edgy-framework 1.6.0, edgy-assessment 1.9.0 |
| 20 | P2.1 model diff; P2.2 ArchiMate export; P2.3 release v2.3.0 | edgy-assessment 1.9.0 |

Sprints 17 and 18 are independent of 19; 20 depends on 19 (the diff
produces status and change tags that the overlay draws). Each sprint ends
with `tools/check.sh` green, examples regenerated and a PR for review, as
before. Rough effort: Sprint 17 and 19 one day each, Sprint 18 two days,
Sprint 20 one day.

## 7. Tests to add

- `test_structure.py`: nested groups (3 tiers, parent chain, geometry
  relative to parent, lane-in-group warning); stage columns without lanes;
  matrix rows × columns for channel and journey; product tree switch;
  outcome layered order (every link points right); `layout_from` draw.io
  (matched positions kept, unmatched below).
- `test_lint.py`: W106 message, W122 facet mismatch, W123 non-facet fill.
- `test_structure.py` (group rows): equal gaps between all container rows
  of an 8-area map, so W118 stays silent.
- `test_render.py`: status bar inside the card bounds, legend row present
  only when the overlay is used, official container colours.
- `test_semantic.py`: S007–S012 in fi and en, one positive and one negative
  case each.
- `edgy-assessment/scripts/test_model_diff.py`: added / removed / renamed /
  re-linked; `test_model_to_archimate.py`: XSD-valid output, round-trip of
  element names.
- `tools/check.sh`: regression guard for all existing expected files
  (unchanged), new fixtures `examples/eval/fixture-f5-nested-groups.txt`,
  `fixture-f6-outcome-web.txt`, `fixture-f7-matrix.txt`.

## 8. Acceptance

- [ ] Every one of the 16 official maps can be written in TXT following
      its official shape and produces 0 lint errors, 0 W111/W113 and a
      clean preview (checked by a new `tools/official-shapes.sh` that
      generates 16 fictional probes, one per type).
- [ ] A 3-tier capability map with 40 leaves regenerates identically after
      a position edit in draw.io when `layout_from:` points at the edited
      file.
- [ ] A heat-mapped capability map keeps facet fills and carries the
      extension legend row; a hand-coloured fill is flagged.
- [ ] S007–S012 catch the examples in §2.9 in fi and en and stay silent on
      the shipped examples.
- [ ] The model diff of a new fictional current / target model pair
      (`examples/model-diff/`, built from `examples/transition-overlay.txt`)
      yields the same `change:` tags as that hand-tagged example.
- [ ] ArchiMate export opens in Archi with every element and relationship
      present.

## 9. Risks and limits

- **Nesting changes geometry code everywhere.** The flat `groups` dict is
  read by layout, lint helpers (`_container_boxes`), the renderer and the
  assessment `layout` block. Mitigation: parent field defaults to `None`,
  all existing expected files must stay byte-identical (regression guard).
- **Semantic rules on wording are language-sensitive.** The verb-phrase and
  organisation-voice heuristics need per-language word lists; start with
  fi/en, warn (never error), and keep the human semantic approval in
  qa.json as the gate.
- **ArchiMate mapping loses EDGY-specific meaning** (Story, Content,
  Journey have no exact ArchiMate type). Document the mapping, use
  Grouping / Business Event / Business Process with an `edgy:type`
  property, and state that the export is one-way.
- **Status overlay invites non-EDGY colouring.** The lint rule and the
  mandatory legend row are the guard; the SKILL.md states that the fill is
  never used for status.

## Appendix A. Probes used for the evidence (all fictional)

| § | Probe | Observed on `main` (3619d8b) |
|---|-------|------------------------------|
| 2.1 | `group:` → `group:` → 2 capabilities, two sub-groups, plus one flat group | 4 containers all siblings; outer has no children; W106 |
| 2.2 | `map_type: task`, `stages: Inspiration, Plan, Book`, 6 tasks with `{stage}`, no lanes | 2-column grid, no stage headers, no warning |
| 2.4 | `map_type: product`, 7 products, 6 `contains` links | hub-and-spoke; W111 × 2 |
| 2.5 | `map_type: outcome`, 8 outcomes, 8 `enables` links | grid; W111 × 2, W113 × 1 |
| 2.7 | `layout_from: existing.drawio#capability` | read as ArchiMate; warning "view not found", own layout used |
| 2.9 | `edgy_semantic_review.py` on a capability map | no S-findings possible (`is_purpose_map` gate) |
| 1 | `map_type: capability`, 8 groups × 8 capabilities, `--preview --preset publication` | 7.6 s, 0 errors, W109 (probe names) and W118 × 2 (§2.12) |
| 2.12 | same probe; and one row with groups of 3 and 8 members | row gaps 44 px / 34 px; containers 196 px and 276 px high in one row |
