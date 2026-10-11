# Changelog

Releases of the edgy-skills bundle are git tags. Each skill also carries its
own semantic version in its `SKILL.md` front matter and in `registry.yaml`.
Install a release with `EDGY_SKILLS_REF=<tag>` (see README → Versions).

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
