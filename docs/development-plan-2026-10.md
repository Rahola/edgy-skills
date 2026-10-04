# EDGY skills development plan (2026-10): geometry fidelity, visual diagnostics, planned layouts

**Revision 1 (2026-10-04).** Follow-up to
[`development-plan-2026-09.md`](development-plan-2026-09.md), whose seven
sprints shipped as **v2.0.0** (edgy-diagram 2.4.1, edgy-framework 1.4.1,
edgy-assessment 1.6.1, edgy-deep-dive 1.1.0, edgy-target-state 1.0.1). This
plan merges two new sources that examined the same case independently:

- **Review C — planned-layout proposal.** An agent produced the four facet
  diagrams of an outside-in EDGY assessment with the v2.0.0 skills, found the
  `facet: all` map unreadable, re-drew the same model by hand as a planned
  ring layout and wrote a reference implementation (one geometry → draw.io
  XML + SVG, four lint-clean files). It proposes `map_type: triad`, a
  `primary` element flag, "Further …" panels, two new lint rules and straight
  edges in the native renderer.
- **Review D — renderer and report-layout findings.** A second agent analysed
  the same case from the code of `edgy_render.py`, `edgy_parser.py` and
  `edgy_lint.py` and from the final PDF. Seven findings F1–F7 on endpoint
  routing, label placement, visual validation, text metrics, the purpose-tree
  layout, canvas/legend composition and the value of structural maps.

Neither review saw the other. They reach the same root cause by different
routes: **a valid EDGY model and a clean structural lint do not guarantee a
readable published diagram**, because generation, rendering and validation do
not share one resolved geometry.

Every claim below that concerns the code was verified against `main`
(c3d6ed0) before it was written down; the line references are to that commit.

> 🔒 Both reviews originate from private client work. The case is referred to
> only by aggregate numbers. No client or organisation names, no business
> content, no file paths from the delivery (see the privacy rule in
> `CONTRIBUTING.md` and `AGENT_LOG.md`). The reference implementation is
> **not** copied into the repository; its geometry principles are.

---

## 1. Material reviewed

| Source | What | Numbers (aggregate) |
|--------|------|---------------------|
| Review C, the case | One outside-in assessment, English PDF; four generated facet diagrams + integrated view | Architecture facet 19 elements; `facet: all` map 2760 × 3960 px (height 1.4 × width); 24 core links; `edgy_lint.py` 0 errors / 0 warnings |
| Review C, reference implementation | Hand-planned ring layout of the same model | 4 draw.io files, lint-clean; `facet: all` page 1340 × 1030 px; every core link a straight line or a one-bend polyline; two intersection–intersection links detoured along the page edge |
| Review D, the report revision | Report-local patches to the renderer and report composition | 7 final diagram pages, 47 source–target relationships, 0 edge-through-box collisions after the patches; journey view 1740 × 940 → 1670 × 520 units with a horizontal legend |
| Repository state | `main` at v2.0.0 | 105 tests (51 + 16 + 15 + 15 + 8), `tools/check.sh` 13 steps green, 25 shipped examples lint-clean |

**Release-hygiene finding (Review D §1, verified 2026-10-04).** On the remote,
`refs/tags/v1.0.0` and `refs/tags/v2.0.0` both resolve to `c3d6ed0`, the v2
merge commit. The v1.0.0 tag was re-created after the merge and points to the
wrong commit; the initial public release is `bd5c34d`. Review D therefore
could not compare v1 and v2 and rightly refuses to call the case a
regression. This is a release error, not a code defect; see P0.1.

## 2. Key findings

### 2.1 The default `facet: all` layout does not scale (C)

`_prepare_facet_groups` lays every element of a facet in one column inside
the facet container. With 19 elements in one facet the page becomes a tall
strip; the 24 core links are `orthogonalEdgeStyle` edges routed straight
through the columns, so they cross each other and other boxes, and their
labels land on boxes. Neither alternative helps: `group:` containers take
over the layout and pile the linked elements at the bottom; `--engine
plantuml` routes edges well but ignores the facet structure and spreads
unlinked elements into a 4096 px wide grid.

Root cause: the layout does not distinguish the elements that *carry links*
from the elements that are *listed*, and edges are routed without regard to
where the elements ended up.

### 2.2 Explicit waypoints produce diagonal endpoint segments (D-F1)

`edgy_render.py:166` `_orthogonal()` returns `[p1] + points + [p2]` as soon
as waypoints exist. `edgy_parser.py:1056` distributes anchors over a side
between 0.15 and 0.85 when several edges share it, so the final port is not
the centre port the waypoints were computed for. The first and last segments
are then diagonal even when the middle of the route is perfectly orthogonal.

### 2.3 The native renderer ignores `label: source | middle | target` (D-F2)

The parser emits `mxGeometry x = -0.5 / 0 / 0.5` (documented in
`references/routing.md`); `edgy_render.py:338` always places the label at
`total / 2`. All three choices render at the midpoint, so the documented
remedy for crowded labels has no effect in the CLI-free preview.

### 2.4 Lint passes spaghetti (C §1, D-F3)

`edgy_lint.py` checks notation and structure. E008 (overlap) only compares
vertices with the *same parent*; W101 estimates text fit. Nothing checks
whether an edge passes through a third element, whether an edge label sits
on an element or another label, or whether a label or arrowhead leaves the
page. The 19-element map in §2.1 is therefore 0/0.

### 2.5 Text is measured with a constant factor; bold leaks into descriptions (D-F4)

`edgy_render.py:71` `wrap()` estimates width as characters × 0.56 × font
size; `edgy_render.py:264` passes `bold or bold_default`, so the cell-level
bold default is inherited by description rows meant to be lighter. The W101
estimate in lint uses the same kind of factor (0.55). Long bold titles fit
on paper and overflow in the picture.

### 2.6 The purpose-tree layout puts the parent over the leftmost child (D-F5)

`_layout_purpose` (`edgy_parser.py:1621`) lays the top purposes in a row
starting at `centre_x0` and the sub-purposes in a second row from the same
x; a parent is not centred over its children and no corridor is reserved, so
the branch to a distant child crosses the intervening boxes. The reviewer
worked around it with `layout_from:` coordinates — the mechanism exists, the
default does not.

### 2.7 Canvas and legend waste space; sparse maps shrink in the PDF (D-F6, C legend strip)

The legend is a 220 × 200 px box in the lower right corner
(`_append_legend_cells`, `edgy_parser.py:1108`); if content reaches it the
page is enlarged (`edgy_parser.py:953`). The renderer initialises its bounds
from the page size (`edgy_render.py:188`). A sparse journey map therefore
carries a large blank area, and fitting the whole SVG into a fixed report
image box makes the content small. Review C's strip legend (one 24 px band
along the bottom) and Review D's tight publication bounds address the same
problem from two sides.

### 2.8 Relationship views alone are a weak substitute for structural maps (D-F7)

The report improved markedly when a purpose map, a capability map grouped by
analytical domain and a journey map with a hand-off table were added
alongside the facet relationship views. The elements and ids were the same;
only the question each map answers differed.

### 2.9 Not a regression (D §1)

Both tags point to the same commit (§1), so there is no historical baseline
to compare. The plan treats the findings as defects of the current code, not
as regressions, and fixes the tags.

### 2.10 Already resolved or not an issue

| Item | Status |
|------|--------|
| Legend cells identified by colour or cell order (D-F6 note) | Resolved in 2.4.1: E009 detection is structural (title + ≥ 3 chips + ≥ 1 line sample) |
| Hand-placed positions for the purpose map (D-F5 workaround) | Supported today via `layout_from:`; §2.6 fixes the default |
| English legend by string-replacing another language (D-F6) | Not needed: the `language:` key already drives legend text |

## 3. Scope decisions: what belongs in this repository

Guiding principle (unchanged from the previous plan): the repository
packages **EDGY notation, EDGY-based modelling guidance and agent-agnostic
tooling with standard-library dependencies**. It does not package an
organisation's report pipeline or hard dependencies that an agent sandbox may
lack.

| Item | Decision | Rationale |
|------|----------|-----------|
| Shared geometry layer used by generator, renderer and lint (D-F1, D-F2, C §3.1) | **In** (P1) | The root cause; everything else builds on it |
| Visual diagnostics W111–W114 and `--visual` JSON (C §3.4, D-F3) | **In** (P1) | Notation-level quality gate; stdlib geometry |
| Font measurement with Pillow and a font file path (D-F4) | **Out** as a dependency; **In** as embedded glyph-width tables for the Helvetica/Arial family (stdlib) with optional Pillow measurement when it happens to be installed | draw.io exports with browser fonts anyway; a width table is far better than one constant and needs no install |
| Explicit `title` / `description` text styles; never shrink silently (D-F4) | **In** (P2) | Fixes the bold leak and the hidden overflow |
| Minimum rendered sizes at report scale (D-F4) | **In** (P2, lint `--scale`) | A warning, not a layout engine |
| Publication bounds, `--publication` export, orientation hint (D-F6) | **In** (P2) | The native SVG is what agents embed |
| `legend: strip` document option (C §3.1) | **In** (P2); `box` stays the default | Same EDGY semantics, less canvas |
| PDF composition: captions, page breaks, footer clearance, landscape pages (D-F6) | **Out** of tooling; **In** as a Phase 5 checklist line in edgy-assessment | Report pipeline is per delivery |
| `map_type: triad`, `{primary: true}`, "Further …" panels (C §3.1–3.2) | **In** (P3) as an **EDGY extension layout**, opt-in | Same status as `reference` and `summary`; the default `facet: all` output must stay unchanged |
| Inferring the primary element from link count (C §8) | **Out** for now | "Explicit flag, else first" is predictable |
| General "walk the ring" routing for N intersection links (C §8) | **Out** for now | Two fixed detours cover the 24 core links; document the limit |
| Purpose-tree re-layout (D-F5) | **In** (P3) | A default that needs `layout_from:` to be readable is a bug |
| Structural maps (purpose, capability, journey) in assessment Phase 4 (D-F7) | **In** (P4) as recommended optional outputs with the same ids | Modelling guidance; not every scope needs every map |
| Dropping relationships to clean up a view (D §5) | **Out**, always | The triad's panels are allowed only because non-drawn links are reported and the report tables carry them |
| Reference implementation code (C appendices) | Used as a **model**, not copied | Hard-coded coordinates, constant-factor `wrap()`, fixed label offsets are demonstrations |
| Provenance of the delivery (fonts, backends, installed bundle) (D §3.1) | **Out** (private delivery); the **fixtures** are In (P0) | Repo keeps what makes the failure reproducible |
| Tag fix and a release checklist (D §1) | **In** (P0) | A tag that points to the wrong commit is a defect of the repository |

## 4. Target state

A single pipeline in which each stage catches a different class of failure:

```
model validity      edgy-model.schema.json, tools/validate-edgy-model.py      (exists)
      ↓
input → generator   edgy_parser.py + edgy_geometry.py (NEW): one resolved geometry
      ↓
structural lint     E001–E011, W101–W110                                       (exists)
visual lint         W111–W114 on the same resolved geometry (NEW), --visual JSON
      ↓
preview             edgy_render.py: straight and orthogonal routes from the same
                    geometry, label fractions honoured, tight publication bounds
      ↓
publication check   edgy-assessment Phase 5: --warnings-as-errors, ratio limits,
                    final-PDF review at viewing scale (checklist)
```

For large models, `map_type: triad` gives a planned ring: Identity on top,
Architecture lower left, Experience lower right, Organisation / Product /
Brand between the facets they bridge, one primary element per type carrying
the core links, the remaining elements in "Further …" panels without lines.

## 5. Actions

Priorities: **P0** = release hygiene and fixtures, **P1** = geometry layer and
visual diagnostics, **P2** = text and publication, **P3** = layouts, **P4** =
skill guidance and the assessment workflow. Items carry the Review C section
(C §x) or Review D finding (D-Fx) they trace to.

### P0 — Release hygiene and fixtures

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P0.1 | **Fix the tags**: move `v1.0.0` to `bd5c34d` (initial public release); `v2.0.0` stays at `c3d6ed0`. Manual, by the maintainer; the release notes already describe both versions. | D §1 | `git ls-remote --tags` shows two different commits; `EDGY_SKILLS_REF=v1.0.0` installs edgy-diagram 1.7.0 |
| P0.2 | **Releasing section in `CONTRIBUTING.md`**: tag the merge commit after merging, never before; check `git ls-remote --tags`; CHANGELOG entry per bundle version; skill versions in `registry.yaml` match SKILL.md. | D §1 | Section present; next release follows it |
| P0.3 | **Regression fixtures (Acme Oy) in `examples/eval/`**: `fixture-f1-ports-waypoints.txt` (several edges on one side, explicit `via:` based on centre ports, obstacles near both ends, all four sides), `fixture-f2-labels.txt` (three label positions), `fixture-f4-long-bold-title.txt`, `fixture-f5-purpose-tree.txt` (parent + 4 children + 4 measuring Outcomes, two levels, mixed sizes), `triad-large-architecture.txt` (19 elements in one facet, 24 core links). `tools/edgy-eval.py` gains columns for W111–W114 and the height/width ratio. | D §3.1, C §5 | Each fixture reproduces its finding on `main` before the fix (recorded as aggregates in `AGENT_LOG.md`) |

### P1 — Geometry layer and visual diagnostics (edgy-diagram 2.5.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P1.1 | **`scripts/edgy_geometry.py`** (stdlib): absolute coordinates through the parent chain (shared with E006/E007); port distribution on a side; border point for a straight edge (ray from centre, as in the reference implementation); route normalisation — orthogonal joins between the real port and the adjacent waypoint oriented by the port side, duplicate and collinear points removed, no segment pointing back into its own node; label point as a fraction of arc length plus a perpendicular offset; Liang–Barsky segment–rectangle intersection. The parser, the renderer and lint import it. | D-F1, D-F2, C §3.1 | `test_geometry.py` (≥ 12 tests) covers every function; parser and renderer no longer contain private copies |
| P1.2 | **Renderer fixes**: `_orthogonal()` uses the normalised route; `edgeStyle=none` draws a straight line border-to-border; waypoints give a polyline with the arrowhead on the last segment; label fraction = `(relative_x + 1) / 2` with `mxGeometry` offsets and the perpendicular default (25 px away from the nearest box); zero-length routes handled. | D-F1, D-F2, C §3.5 | Fixture F1 renders with no diagonal endpoint segment; F2 renders the three labels at 25 / 50 / 75 % |
| P1.3 | **Visual lint rules** on the same geometry: **W111** edge passes through a non-endpoint element (> 8 px inside), **W112** edge label overlaps an element (> 20 % of the label box), **W113** edge label overlaps another label, **W114** label or arrowhead outside the page. Containers do not trigger W111; a parent → children fan sharing one corridor (tree bus) does not trigger W113. `--visual` writes machine-readable findings (page, cell ids, coordinates); `--warnings-as-errors` promotes them. Rules docstring updated. | C §3.4, D-F3 | Hand-written XML with an edge through a third box → W111; the lint-clean 19-element map from §2.1 reproduced as a fixture → W111 + W112 > 0; triad output (P3.1) → 0 |
| P1.4 | **Baseline on shipped examples**: run W111–W114 over `examples/expected-*.drawio`, record the counts before and after as aggregates, fix the inputs that trigger them or document the intentional cases. `check.sh` runs `--warnings-as-errors` on the shipped examples once they are clean. | C §5 step 5 | `check.sh` step `edgy-lint` passes with visual rules enabled |

### P2 — Text and publication (edgy-diagram 2.5.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P2.1 | **`scripts/edgy_text.py`**: glyph-width tables for Helvetica regular and bold (AFM-derived, Latin-1 + common Nordic/French/German glyphs, fallback average for others); `measure(text, size, bold)`; optional Pillow measurement when `PIL` imports and a font is found, never required. `wrap()` in the renderer and W101 in lint use it. Explicit `title` and `description` styles (size, weight, colour) replace `bold or bold_default`; the parser's label standard sets description rows to normal weight. Overflow policy: widen the box (size class up) or warn — never scale text down silently. | D-F4 | Fixture F4: title fits or W101 fires; description rows are not bold in the SVG; estimate within ±10 % of Pillow on the fixture texts |
| P2.2 | **Publication bounds**: the renderer computes the bounding box of everything visible — shapes, wrapped text, full routes, arrowheads, labels, legend — plus a margin; `--publication` exports with that `viewBox` instead of the page; a one-line orientation hint on stderr (`landscape` when width > 1.2 × height). The editor page size is unchanged. | D-F6 | Fixture journey map: publication SVG area ≤ 1.15 × content bounding box; no label clipped (W114 = 0 on the tight bounds) |
| P2.3 | **`legend: strip`** document-level option (default `box`): a 24 px band along the bottom with the title, six colour chips and one line sample; satisfies E009; honours `language:`; works with the transition-overlay rows (second band). | C §3.1, D-F6 | `test_lint.py`: E009 does not fire on a strip legend; page height grows by the band only |
| P2.4 | **Lint `--scale <factor>`** → **W115** rendered font size below 6 pt at that scale (title, description, relation label separately). | D-F4 | The 19-element map at report scale → W115; the triad at the same scale → 0 |

### P3 — Layouts (edgy-diagram 2.5.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P3.1 | **`map_type: triad`** via the `MAP_TYPE_LAYOUT` dispatcher, for `facet: all` and single facets. A **slot table** (role → centre and size, derived from the page size — not literal pixel constants scattered in code) gives the ring: purpose top centre, story/content beside it, organisation and brand between the facets, capability/asset/process lower left, task/channel/journey lower right, product bottom centre; single-facet variant with intersection A on top, the three primaries as a triangle in the container, intersection B below. Core links are straight (`edgeStyle=none`) border-to-border; the two intersection links `organisation → product` and `product → brand` detour along the page edge with two waypoints; label displacement from the geometry layer, overridable with `{label_dx, label_dy}`. `{primary: true}` marks the element that carries the links (default: the first of its type; several → warning, first wins). Non-primary elements go to **"Further <type>" panels** (`container=1`, grey tint, grid of 1–4 columns, localised title fi/fr/de), with no edges inside; links to a non-primary endpoint are not drawn and are reported on stderr as a count and a list. `legend: strip` by default. `pages:` may set `triad` per page; `layout_from:` with `triad` warns and is ignored. | C §3.1–3.2, §8 | `test_edgy.py`: 12 primaries within ±2 px of the slot table; non-primaries inside a "Further" container with 0 edges; `primary` flag moves an element to the ring. `test_structure.py`: core links have `edgeStyle=none`, exactly 2 edges carry waypoints. All 24 core links visible once; height ≤ 1.2 × width; W111–W114 = 0 |
| P3.2 | **Purpose-tree re-layout**: parent centred over its children, a routing corridor above each child row, entry from the top, Outcomes in a separate row beneath their purposes with dashed `measures` arrows upward, stable sibling order, space allocated for labels; verified after port distribution. | D-F5 | Fixture F5: no branch intersects a child box (W111 = 0); two levels and mixed sizes stay readable |
| P3.3 | **Examples and docs**: `examples/triad-all-facets.txt` (12 primaries, 2–4 further per type, all 24 core links) and `examples/triad-architecture.txt` (9 capabilities, 5 assets, 5 processes, 4 products, 1 organisation) with `expected-triad-*.drawio`; `references/map-types.md` describes `triad` and the "Further" panel as an **EDGY extension** with the slot tables; `SKILL.md` 2.5.0 lists `triad`, `primary`, `legend`, `label_dx/dy`, `--publication`, `--visual`. | C §4 | `examples/README.md` updated; `check.sh` steps `examples-refs` and `edgy-lint` pass |
| P3.4 | **Regression guard**: without `map_type: triad` and without a `legend:` key the generator output for the existing `examples/*.txt` is byte-identical to the output *after* P1–P2 (the geometry and text fixes legitimately change those files once; P3 must not change them again). | C §7 | `git diff --stat examples/` after the P3 commit lists only new files |

### P4 — Skill guidance and the assessment workflow (edgy-assessment 1.7.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P4.1 | **Model → TXT**: `assets/edgy-model.schema.json` gains optional `primary: boolean` on elements and capabilities; `edgy_model_to_txt.py --layout triad` writes `map_type: triad` and `{primary: true}` (explicit flag, else first element — the current convention); core links still between the primaries of each type pair. New `scripts/test_model_to_txt.py`, wired into `check.sh`. | C §3.3 | Acme Oy model → four TXT files → four diagrams → `--warnings-as-errors` clean, with no hand-written TXT |
| P4.2 | **Phases 3–5**: Phase 3 uses `--layout triad` when any facet has more than ~8 elements; Phase 4 recommends a purpose map (strategy → EDGY, framework 1.4.1), a capability map (`group:` per analytical domain, stated as grouping — not an org chart or an all-to-all claim) and a journey map with hand-off risks as optional structural maps **with the same ids as the model**; preview checklist adds "no edge passes through a box, no label on a box (W111/W112 = 0)" and the concrete limit "`facet: all` height ≤ 1.2 × width"; Phase 5 runs `edgy_lint.py --warnings-as-errors --visual` on every file and requires a look at the **final PDF pages at viewing scale** (captions, page breaks, footer clearance) — a checked SVG is not enough. | C §3.6, D-F7, D-F3, D §4 | Checklist lines present; the fictional example in the skill produces the structural maps from the same model |
| P4.3 | **Templates and bookkeeping**: `templates/analysis-template*.md` section 9 states that diagrams show one primary element per type with its core links, the other elements in Further panels, and that the tables carry the full detail; `registry.yaml` regenerated; `CHANGELOG.md` v2.1.0; `AGENT_LOG.md` entry with the technical decisions and before/after lint aggregates. | C §4 | `check.sh` `registry-sync` passes; CHANGELOG lists the extension status of `triad` |

## 6. Sequencing and estimate

One branch, one commit series per phase; `bash tools/check.sh` stays green
after every commit. P3 must not start before P1 is green, because the triad's
acceptance criteria are the visual rules.

| Phase | Scope | Estimate | Versions |
|-------|-------|----------|----------|
| Sprint 8 | P0.1–P0.3 (tags, releasing section, fixtures that fail on `main`) | 1 working day | — |
| Sprint 9 | P1.1–P1.4 (geometry layer, renderer fixes, W111–W114, baseline) | 5–6 working days | edgy-diagram 2.5.0-dev; `expected-*.drawio` regenerated once, with a visual review |
| Sprint 10 | P2.1–P2.4 (text metrics, publication bounds, strip legend, `--scale`) | 3–4 working days | edgy-diagram 2.5.0-dev |
| Sprint 11 | P3.1–P3.4 (triad, purpose tree, examples, regression guard) | 4–5 working days | edgy-diagram **2.5.0** |
| Sprint 12 | P4.1–P4.3 (schema, `--layout triad`, Phases 3–5, templates, CHANGELOG) | 2 working days | edgy-assessment **1.7.0**, bundle **v2.1.0** |

**Status (2026-10-04):** Sprints 8–12 are implemented in PR #4 (edgy-diagram
2.5.0, edgy-assessment 1.7.0, bundle v2.1.0) — see the `AGENT_LOG.md`
entries dated 2026-10-04. P0.1 (moving the `v1.0.0` tag) is a manual
maintainer action. P1.4 / P3.4 are met for the triad and purpose examples and
the F1/F5 fixtures (`check.sh` step `edgy-lint-strict`); the shipped examples
that use the default facet, lane and reference layouts still carry visual
warnings (48 W111 / 26 W112 / 1 W113 in 10 files) because those layouts were
outside this plan's scope — a follow-up plan item.

Total 15–18 working days. Sprint 8 is independent and should ship first: the
tag fix is a one-minute manual action and the fixtures make every later
sprint's acceptance measurable. Sprints 9–10 change the output of existing
examples once (by design) and need a human look at the regenerated previews;
Sprints 11–12 add new surface and must leave the old examples untouched.

## 7. Tests to add

| Test | File | Expectation |
|------|------|-------------|
| `test_border_point`, `test_normalise_route_*`, `test_label_fraction`, `test_segment_rect_intersection` | new `test_geometry.py` | Unit coverage of every function in `edgy_geometry.py`, including all four port sides and a zero-length route |
| `test_render_no_diagonal_endpoints` | `test_render.py` | Fixture F1: every segment of an orthogonal path has constant x or y |
| `test_render_label_fractions` | `test_render.py` | Fixture F2: label x-positions strictly increase for `source`, `middle`, `target` |
| `test_render_straight_edges` | `test_render.py` | Triad SVG: ≥ 20 `<line`/straight paths, exactly 2 polylines |
| `test_render_description_not_bold` | `test_render.py` | Description rows have no `font-weight="bold"` |
| `test_w111_edge_through_box`, `test_w112_label_on_box`, `test_w113_label_on_label`, `test_w114_outside_page` | `test_lint.py` | Hand-made XML triggers each rule; the triad example triggers none |
| `test_w111_allows_container_and_tree_bus` | `test_lint.py` | An edge through a container, and a parent→children fan, do not fire |
| `test_legend_strip_satisfies_e009` | `test_lint.py` | `legend: strip` → no E009 |
| `test_publication_bounds_tight` | `test_render.py` | `--publication` viewBox ≤ 1.15 × content bbox on the journey fixture |
| `test_triad_all_facets_positions`, `test_triad_further_panels`, `test_triad_primary_flag`, `test_triad_dropped_links_reported` | `test_edgy.py` | Slot positions ±2 px; non-primaries in a "Further" container with 0 edges; `primary` moves an element to the ring; stderr lists the non-drawn links |
| `test_triad_edges_straight` | `test_structure.py` | Core links `edgeStyle=none`; exactly 2 edges with `<Array as="points">` |
| `test_purpose_tree_no_crossing` | `test_structure.py` + lint | Fixture F5: W111 = 0, parent centred over children |
| `test_model_to_txt_layout_triad` | new `edgy-assessment/scripts/test_model_to_txt.py` | TXT starts with `map_type: triad`; primaries carry `{primary: true}` |

## 8. Success metrics and acceptance

- Tags: `v1.0.0` and `v2.0.0` resolve to different commits (P0.1).
- Orthogonal fixtures: no diagonal endpoint segment, no route re-entering its
  own node (D-F1).
- `label: source | middle | target` render at distinct positions consistent
  with the generator's geometry contract (D-F2).
- No unintended edge intersects a non-endpoint element, nested coordinates
  included; label collisions are diagnosed; structural and visual findings
  are reported separately (D-F3, W111–W114).
- Title, description and relation text fit their usable area without
  clipping or silent shrinking; descriptions are not bold (D-F4).
- Purpose-map branches do not cross child boxes (D-F5).
- Publication bounds include labels and arrowheads outside the node extents;
  the sparse-map SVG area is ≤ 1.15 × its content bounding box; the legend
  keeps EDGY semantics and follows `language:` (D-F6).
- Triad: all 24 core links visible once in `facet: all`, each arrow visibly
  starts and ends, no label on a box, height ≤ 1.2 × width; single-facet map
  ≤ 1.0 × width before panels (C §7).
- Acme Oy model → `--layout triad` → four diagrams with no hand-written TXT,
  all clean under `--warnings-as-errors` (C §7).
- Existing `examples/*.txt` are byte-identical before and after the P3
  commit; `bash tools/check.sh` exits 0 after every commit.
- Field metric (private, aggregates only in `AGENT_LOG.md`): W111–W114
  count on the next real delivery before manual editing, and the number of
  manual draw.io edits per delivery (target: trend to zero, as in §7 of the
  previous plan).

## 9. Risks and scope limits

- **Changing shipped expected files.** P1 and P2 legitimately change the
  output of every existing example (ports, elbows, text wrapping). Mitigation:
  regenerate once in Sprint 9–10, review every preview visually, keep the
  diff in one commit, and enforce byte-identity from Sprint 11 onward (P3.4).
- **Width tables are not the export font.** draw.io renders with the
  viewer's browser fonts; the tables are a consistent approximation, within
  ±10 % of a measured font on the fixtures. Overflow policy is "widen or
  warn", so the residual error is visible, never hidden.
- **The triad hides links.** Only links to non-primary elements, only in
  `triad`, always reported, and the report tables carry them. The rule from
  Review D stands: a renderer never drops relationships silently.
- **Fixed detours.** Two page-edge routes cover the 24 core links; a model
  with more intersection–intersection links would need general ring routing.
  Documented as a limit of the extension.
- **Scope creep into PDF tooling.** Page composition stays per delivery; the
  repository contributes `--publication` bounds, the orientation hint and a
  checklist, nothing more.
- **Privacy.** All fixtures and examples use Acme Oy; the case is described
  by aggregates only; `tools/privacy-scan.sh` runs on every commit.

---

## Appendix A. Traceability

| Source | Item | Plan item | Decision |
|--------|------|-----------|----------|
| C §1 | `facet: all` unreadable at 19 elements; lint 0/0 | P1.3, P3.1, P0.3 | In |
| C §3.1 | `map_type: triad`, slot coordinates, straight edges, two detours, label offsets, `legend: strip` | P3.1, P1.1, P2.3 | In as extension |
| C §3.2 | "Further <type>" panels, non-drawn links reported | P3.1 | In as extension |
| C §3.3 | `primary` in schema, `--layout triad` | P4.1 | In |
| C §3.4 | W111, W112 | P1.3 | In (+ W113, W114) |
| C §3.5 | Renderer straight lines, polylines, label backing | P1.2 | In |
| C §3.6 | Phases 3–5, ratio limit, template sentence | P4.2, P4.3 | In |
| C §8 | Panel = extension; no primary inference; per-page triad; `layout_from` ignored; two detours enough | P3.1, P3.3 | Decided as proposed |
| C App. A–B | Reference implementation | — | Model only, not copied |
| D-F1 | Diagonal endpoint segments with waypoints | P1.1, P1.2, P0.3 | In |
| D-F2 | Label placement ignored | P1.1, P1.2, P0.3 | In |
| D-F3 | Lint misses visual collisions | P1.3, P1.4 | In |
| D-F4 | Constant-factor text metrics, bold inheritance | P2.1, P2.4, P0.3 | In (tables, not Pillow) |
| D-F5 | Purpose-tree crossings | P3.2, P0.3 | In |
| D-F6 | Canvas, legend, PDF composition | P2.2, P2.3 / Phase 5 checklist | In / Out (PDF pipeline) |
| D-F7 | Structural maps complement relationship views | P4.2 | In as recommendation |
| D §1 | Tags resolve to one commit; no regression claim | P0.1, P0.2, §2.9 | In |
| D §3.1 | Provenance of the delivery | P0.3 (fixtures only) | Out (private) |
| D §5 | Do not drop relationships to pass layout | §3, §9 | Rule adopted |
