# EDGY skills development plan (2026-10, part 2): semantic quality, localisation, layout consistency

**Revision 3 (2026-10-09) — implemented: Sprints 13–16 shipped as v2.2.0 (edgy-diagram 2.6.0, edgy-assessment 1.8.0, edgy-framework 1.5.0); decisions taken: layout-quality rules and card equalisation are on by default, both opt-out. Deviations from the proposal are recorded in `AGENT_LOG.md` (Sprints 13–16).** Follow-up to
[`development-plan-2026-10.md`](development-plan-2026-10.md), whose Sprints
8–12 shipped as **v2.1.0** (edgy-diagram 2.5.0, edgy-assessment 1.7.0).

**Source — Review E: field feedback from a delivery that re-laid out three
maps** (capability, task, purpose) with the v2.1.0 skills. Written as a
development proposal, not as a change to the skill instructions. Its
findings, in the reviewer's priority order:

- **P0** a purpose map that was structurally and visually clean was
  semantically wrong: development *actions* had been modelled as Purposes,
  and no check noticed;
- **P1** three valid maps of one series looked inconsistent (group widths,
  empty space and card widths vary with automatic content sizing) and the
  linter measures none of that;
- **P1** `language: fi` left `contains` and the legend in English, without a
  warning;
- **P1** no way to ask for equal-width, grid-aligned groups;
- **P2** `map_type: task` has no layout of its own; a publication preset for
  the native renderer; a machine-readable QA manifest so "0 warnings" is not
  mistaken for "visually approved".

Every code claim below was verified against `main` (665ca12).

> 🔒 The source is private client work. The organisation, its sector and
> the content of its maps are not named anywhere in this repository; the
> reviewer's client-specific correction section is deliberately omitted.
> Examples use Acme Oy / Acme Transit. See the privacy rule in
> `CONTRIBUTING.md`.

---

## 1. Key findings

### 1.1 A clean lint is not a correct model (P0)

Purpose elements held development measures ("build X", "introduce Y")
rather than reasons to exist or lasting target states; Outcomes mixed
confirmed metrics with proposed ones without saying which; `contains`
relationships asserted part-of hierarchies that were really influences.
`edgy_lint.py` checks notation, structure and geometry — by design it has no
opinion on whether a Purpose *is* a purpose. The reviewer asks for a
**semantic gate** that is machine-assisted but expert-approved: heuristics
may flag, a person decides.

### 1.2 Localisation stops at the vocabulary (P1)

`language:` (added in 2.5.0) only drives the triad panel headings. Verbs
are drawn exactly as written in the input: the Finnish tree verb
`sisältää` exists in `TREE_RELATIONSHIPS` (`edgy_parser.py:63`), but an
agent that writes `contains` in a `language: fi` map gets an English label
and no warning. The legend is fixed English with Finnish glosses
(`edgy_parser.py:1351-1354`: "Flow (tieto/arvo)", "Tree (hierarkia)"), the
strip legend and the transition rows likewise.

### 1.3 Automatic content sizing makes a series look inconsistent (P1)

Each element's width follows its own measured name
(`_get_element_size`), each group's width follows its widest member and
its member count (`_layout_group_members`: 2–4 columns by count), so three
maps of one delivery end up with different card widths, group widths and
amounts of empty space. Nothing in the linter measures balance, alignment,
size spread or canvas utilisation; W115 (text size at scale) is the only
publication-scale check.

### 1.4 No way to ask for a regular grid (P1)

The input has no document-level layout parameters: no fixed card width,
no "equal group width", no explicit column count for groups or for cards
inside a group. The reviewer re-laid the maps out by hand.

### 1.5 `map_type: task` is a grid, undocumented (P2)

`task` maps to the generic grid strategy (`MAP_TYPE_LAYOUT`); the skill's
map-type table lists it only in the grid row. The field need is a
stakeholder-grouped inventory (tasks by the people who do them) kept
apart from the task *path* (task → journey) — and no invented links to
make a picture look connected.

### 1.6 Publication output is assembled by hand (P2)

`--publication` crops the SVG (2.5.0) but margins, title / footnote area,
legend placement and the W115 scale test are still per-delivery decisions.
The draw.io CLI presets (`presentation`, `print`, `web`) do not apply to
the native renderer.

### 1.7 "0 warnings" and "visually approved" are not distinguishable (P2)

The generator prints lint and preview results to the terminal; nothing
records, per delivered file, what was checked, what the image size is, and
whether a human looked at the preview. The assessment skill's Phase 5
checklist asks for it, but the evidence is not machine-readable.

## 2. Scope decisions

Guiding principle unchanged: EDGY notation, EDGY modelling guidance and
agent-agnostic stdlib tooling. Heuristics that touch *meaning* flag and
explain; they never decide.

| Item | Decision | Rationale |
|------|----------|-----------|
| Semantic review of purpose maps: task-verb heuristic for Purposes, Outcome without `measures`, provenance tags, `contains` justification | **In** (P0) as `edgy_semantic_review.py` + a reviewer checklist | Flags with explanations; the expert approves |
| Automatic semantic approval | **Out**, always | A heuristic must not certify a model |
| Provenance on elements (`[confirmed]` / `[analytical]` / `[proposed]` tags, `status:` on Outcomes) | **In** (P0) | Notation-level convention; carried into the report tables |
| Verb rendering in the `language:` of the map; legend localised; W116 mismatch warning | **In** (P1) | The vocabulary already has all four languages; this is the rendering side |
| Changing the canonical verb codes in the YAML / model | **Out** | Model stays language-neutral (`verb_en` is the key, as today) |
| Layout-quality rules W117–W120, on by default, `--no-layout-quality` to switch off | **In** (P1), warnings | Measurable, deterministic, no taste judgements; a warning that is off by default is never read |
| Document-level layout options: `card_width`, `equal_cards`, `group_columns`, `cards_per_row`, `equal_group_width`, `align_groups` | **In** (P1) | Direct field need; opt-in, default output unchanged except for the equalisation default below |
| Moderate equalisation of card sizes within one view **by default** (`equal_cards: false` to switch off) | **In** (P1) | The reviewer's "reasonable default"; regenerates shipped examples once |
| `map_type: task` stakeholder inventory layout; inventory vs path | **In** (P2) | Documented map type with its own layout, like `organisation` roles |
| Inventing relationships to fill a map | **Out**, stated in the skill | Same rule as "never drop links silently", in reverse |
| `--preset publication` / `presentation` for the native renderer | **In** (P2) | Margins, title band, legend placement, W115 at the preset scale |
| PDF page composition, captions, footer | **Out** of tooling (as before); checklist only | Per delivery |
| `qa.json` manifest per generator run | **In** (P2) | Separates lint result, visual-approval status and semantic-approval status |
| Series-level consistency check across several files (`--series`) | **In** (P2, small) | Acceptance test 1 needs it |
| Client-specific corrections from the review | **Out** | Not repository content |

## 3. Target state

```
model  ──►  semantic review (NEW, flags + checklist; expert approves)
   │
   ▼
input  ──►  generator: language-aware labels + legend; layout options; equal cards
   │
   ▼
lint:  structural E/W  ·  visual W111–W114  ·  layout quality W117–W120 (NEW, on by default)
   │                       ·  localisation W116 (NEW)  ·  scale W115
   ▼
preview / --preset publication  ──►  qa.json: counts, lint, image, language,
                                      visual_approval: pending → approved by <who>
```

## 4. Actions

Priorities as in the review: **P0** semantic gate, **P1** localisation,
layout consistency and layout options, **P2** task map, presets, manifest.
Items carry the review's section (E §x) they trace to.

### P0 — Semantic gate for purpose maps (edgy-framework 1.5.0, edgy-diagram 2.6.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P0.1 | **`scripts/edgy_semantic_review.py`** (edgy-diagram, stdlib; also callable as `edgy_lint.py --semantic`): reads the TXT input (and optionally `edgy-model.json`) and reports **S001** Purpose name starts with or contains a task verb (fi: kehitä, toteuta, rakenna, ota käyttöön, uudista, …; en: develop, implement, build, deploy, introduce, …; fr/de lists), **S002** Outcome with no `measures` relationship to a Purpose, **S003** Outcome without a provenance tag, **S004** Purpose with no provenance tag, **S005** `contains` between Purposes where the child name shares no noun with the parent (weak hint, lowest confidence), **S006** a metric-looking value (number + unit/%) inside a Purpose name. Output: text and `--json`, each finding with the rule, element, the *reason* and the question the reviewer should answer. Exit code is always 0 unless `--strict` — the tool never fails a build on meaning. | E §Täydennys 1–4, 6 | Fixture `fixture-s1-purpose-semantics.txt` (Acme Oy: two purposes written as actions, one Outcome without a link, one unlabelled provenance) → S001 × 2, S002 × 1, S003/S004 as written; the clean purpose example → 0 |
| P0.2 | **Provenance convention** in the input: tags `[confirmed]`, `[analytical]`, `[proposed]` on any element, and `{status: confirmed\|proposed}` on Outcomes (the metric status). The generator renders the status as the existing tag line; `edgy_model_to_txt.py` writes it from a new optional model field `provenance` / `metric_status`; the schema gains both. | E §Täydennys 2, 5 | Round trip model → TXT → drawio keeps the tags; lint W101 unaffected |
| P0.3 | **Reviewer checklist** in edgy-framework (*Purpose map semantic review*): Purpose = why / what value, never a measure or project; Outcome = verifiable result, metric separate, status visible; Capability / Process / Task = how; `contains` is a claim that needs a part-of justification, else an influence verb; confirmed vs analytical vs proposed stated separately. The checklist ends with an explicit sign-off line (`Semantic review: approved by <role>, <date>`) that the assessment report must carry. | E §Täydennys 1–5 | Checklist present; edgy-assessment Phase 2 and the template section 9 reference it |
| P0.4 | **Workflow**: edgy-assessment Phase 2 runs the semantic review on the purpose map input before Phase 3 and records the result in `qa.json` (P2.3) as `semantic_review: {findings: n, approved_by: null}`; delivery requires `approved_by` to be set by a person. | E §Täydennys hyväksymistestit | Chain test: a purpose map with an action-Purpose yields S001 and an unapproved manifest |

### P1 — Localisation (edgy-diagram 2.6.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P1.1 | **Verb rendering in the map language.** The parser already classifies every verb against the four-language vocabulary; with `language:` set it renders the label in that language when the verb is a known vocabulary entry in another language (`contains` → `sisältää`, `requires` → `vaatii`), keeping the canonical code internally. Unknown verbs stay as written. Opt-out: `translate_verbs: false`. | E §P1 käännökset | Finnish purpose map written with `contains` renders `sisältää`; merged labels (`a / b`) translate per part |
| P1.2 | **Legend in the map language**: box and strip legends, transition rows and the triad panel titles use one `LEGEND_TEXT[lang]` table (fi/en/fr/de); default `en` as today. | E §P1 käännökset | `language: fi` → "Linkki", "Virta", "Puu", "Vaikutus", "Siirtymä" etc.; E009 detection unchanged (structural) |
| P1.3 | **W116** label language mismatch: an edge label that is a vocabulary verb of a language other than the map's `language:` (only when `language:` is set). | E §P1 käännökset | Regression test: a `language: fi` purpose map with `contains` → W116 before P1.1's translation, 0 after; no English relationship label survives |
| P1.4 | `edgy_model_to_txt.py` already picks verbs by language; it additionally writes `language:` (2.5.0) — verify the chain in the model test for fi/fr/de. | E §P1 | Chain test per language: no W116 |

### P1 — Layout consistency (edgy-diagram 2.6.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P1.5 | **Layout-quality rules** (warnings, **on by default**; `edgy_lint.py --no-layout-quality` switches them off for a run, and `qa.json` records whether they ran): **W117** size spread — width or height of elements of one type varies by more than 25 % (max/min) within a page; **W118** alignment — group containers or top-level elements whose left edges or top edges differ by 1–12 px (near-aligned but not aligned) or whose gaps differ by more than 20 % in one row/column; **W119** balance — a group's area or the content's bounding box leaves one side with more than 35 % of the canvas empty while the other side is full (asymmetric empty space), or content utilisation of the page is below 45 %; **W120** aspect — content bounding-box ratio outside 0.5–2.0 unless the map type is a sequence. Each finding carries the numbers it measured. | E §P1 visuaalinen laadunvarmistus | The three-map series fixture (P1.8) → W117/W118 before P1.6, 0 after. Shipped examples: counts recorded as a baseline; the `edgy-lint-strict` gate (triad, purpose, F1/F5) must stay clean with the rules on, so the thresholds are tuned on those files first |
| P1.6 | **Layout options** at document level (and per page): `card_width: N` (every element of the page gets width N unless a size class says larger), `equal_cards: true\|false` (default **true**: elements of one type in one view take the width of the widest of them, capped at 280; heights follow), `group_columns: N` (containers laid out in N columns), `cards_per_row: N` (grid inside every container), `equal_group_width: true` (containers in one row share the widest width), `align_groups: grid` (containers snap to a common row/column grid; row height = tallest in the row). Applies to `group:` containers, the `capability` area layout and the triad panels. Options are validated with warnings. | E §P1 vakiomitoitus | A 2 × 2 capability map with `group_columns: 2, cards_per_row: 2, equal_group_width: true, align_groups: grid` places the four containers on exact rows and columns (`test_balanced_grid`) |
| P1.7 | **Default equalisation** (`equal_cards: true`) regenerates every shipped example once; previews looked at; the eval table records H/W and W117 counts before and after. | E §P1 | Byte-identity holds for inputs that set `equal_cards: false`; AGENT_LOG carries the aggregates |
| P1.8 | **Series fixture**: `examples/eval/series-acme-{capability,task,purpose}.txt`, three maps of one fictional delivery, and `edgy_lint.py --series a.drawio b.drawio c.drawio`: **W121** the files differ in legend placement, margins (content offset from the page edge), card width of a shared type or label font sizes. | E §Hyväksymistestit 1 | The series fixture generated with the same options → 0 W121; one file generated with `card_width: 300` → W121 |

### P2 — Task map, presets, manifest (edgy-diagram 2.6.0, edgy-assessment 1.8.0)

| # | Action | Trace | Acceptance criterion |
|---|--------|-------|----------------------|
| P2.1 | **`map_type: task` stakeholder inventory**: tasks grouped by the People / Organisation that perform them — either explicit `group:` containers or derived from `performs` / `uses` relationships — in a matrix (stakeholders as rows, journey stages as columns when a `journey` with `stages` is present; otherwise one row per stakeholder). An **inventory** page (no edges) and a **path** page (task → journey `is part of`, task → channel `uses`) are documented as two map variants; the skill text states: never add a relationship to make a map look connected. | E §P2 tehtäväkartta | Example `task-stakeholder-map.txt` + expected; the inventory variant has 0 edges and lints clean including W111–W114 and `--layout-quality` |
| P2.2 | **Native presets** `--preset publication` and `--preset presentation` for `--engine native` / `--preview`: fixed margins (publication 24 px, presentation 48 px), optional title and footnote band (`title:` / `footnote:` document keys), legend placement (`strip` for publication, `box` for presentation), crop to content, and the W115 scale test at the preset's reference width (publication 160 mm at 300 dpi; presentation 1920 px). The draw.io CLI presets keep their names and semantics. | E §P2 julkaisuprofiili | Two outputs from one input differ only in margins, band and legend placement; `qa.json` records the preset and the W115 result |
| P2.3 | **`qa.json` manifest** written by the generator next to the `.drawio` (`--qa`, on by default with `--preview`): per page — element and edge counts by type, structural lint (errors / warnings / rules), visual lint (W111–W114), layout quality (if run), language check (W116), image size and ratio, preset, preview paths, generator warnings, and three approval fields that the tooling never sets: `visual_approval`, `semantic_approval`, `delivery_notes`. `edgy-eval.py` reads it instead of re-parsing. | E §P2 manifesti, hyväksymistesti 6 | Schema `assets/qa.schema.json`, validated in `check.sh`; a manifest with `visual_approval: null` is reported as *not approved* by the assessment Phase 5 check |
| P2.4 | **edgy-assessment 1.8.0**: Phase 2 semantic review (P0.4), Phase 3 `language:` and layout options passed from the model (`layout` block in `edgy-model.json`), Phase 4 series check across the four files, Phase 5 reads `qa.json` and requires both approval fields; templates section 9 states the provenance convention. | E §Hyväksymistestit 5–6 | Chain test: four files, `--series` clean, manifests present, approvals null → Phase 5 check fails until set |
| P2.5 | Docs: SKILL.md 2.6.0 (map-type table row for `task`, layout options, `language:` effect, presets, `--no-layout-quality`, `--series`, semantic review), `references/map-types.md`, `references/export.md`, CHANGELOG **v2.2.0**, registry. | — | `check.sh` green |

## 5. Sequencing and estimate

| Sprint | Scope | Estimate | Versions |
|--------|-------|----------|----------|
| 13 | P0.1–P0.4 semantic review, provenance, checklist, workflow hook | 3–4 working days | edgy-framework 1.5.0; edgy-diagram 2.6.0-dev; assessment 1.8.0-dev |
| 14 | P1.1–P1.4 verb and legend localisation, W116 | 2–3 working days | edgy-diagram 2.6.0-dev |
| 15 | P1.5–P1.8 layout-quality rules, layout options, equalisation default, series fixture | 5–6 working days | edgy-diagram 2.6.0-dev; shipped examples regenerated once |
| 16 | P2.1–P2.5 task map, native presets, `qa.json`, assessment workflow, docs | 4–5 working days | edgy-diagram **2.6.0**, edgy-assessment **1.8.0**, bundle **v2.2.0** |

Total 14–18 working days. Sprint 13 first: it needs no layout change and
closes the P0. Sprint 15 is the only one that changes existing output and
needs a visual review of the regenerated previews.

## 6. Tests to add

| Test | File | Expectation |
|------|------|-------------|
| `test_semantic_task_verbs_four_languages`, `test_semantic_outcome_without_measures`, `test_semantic_provenance_tags`, `test_semantic_clean_example_is_silent` | new `test_semantic.py` | S001–S006 on the fixture; 0 on the shipped purpose examples; exit 0 without `--strict` |
| `test_verbs_render_in_map_language`, `test_legend_localised`, `test_w116_mismatch` | `test_structure.py`, `test_lint.py` | `contains` → `sisältää` under `language: fi`; legend strings per language; W116 only when `language:` is set |
| `test_equal_cards_default`, `test_card_width_option`, `test_balanced_grid`, `test_equal_group_width` | `test_structure.py` | widths equal per type; exact rows and columns for a 2 × 2 map |
| `test_w117_size_spread`, `test_w118_alignment`, `test_w119_balance`, `test_w120_aspect`, `test_w121_series` | `test_lint.py` | hand-made XML triggers each rule; options make the fixture clean |
| `test_task_inventory_has_no_edges`, `test_task_path_variant` | `test_structure.py` | inventory 0 edges; path only task → journey / channel |
| `test_native_presets_differ_only_in_frame` | `test_render.py` | same content bbox, different margins / band / legend |
| `test_qa_manifest_schema_and_approvals_null` | `test_render.py`, `tools/test_edgy_tools.py` | manifest validates; approvals null; eval reads it |
| `test_assessment_chain_requires_approvals` | `edgy-assessment/scripts/test_model_to_txt.py` | Phase 5 check fails on null approvals, passes when set |

## 7. Acceptance (the review's tests, made checkable)

1. Three maps of one series share margins, legend placement and text sizes → `--series` reports no W121.
2. A 2 × 2 balanced capability map has its groups on exact rows and columns → `test_balanced_grid`.
3. A Finnish purpose map shows relationship labels and the legend in Finnish → no W116, legend strings from `LEGEND_TEXT['fi']`.
4. No edge or label touches the wrong element → W111–W114 = 0 (exists since 2.5.0).
5. At least one PNG/SVG preview was looked at before delivery → `qa.json.visual_approval` set by a person.
6. Zero-error lint and visual approval are reported separately → `qa.json` fields are distinct; the assessment Phase 5 lists them on separate lines.
7. No Purpose is a development task; every Outcome measures a named Purpose and shows its status; every hierarchy link is justified → S001–S006 empty or each finding answered in the checklist; `semantic_approval` set.

## 8. Risks and limits

- **Heuristics on meaning.** S001 will miss nominalised actions ("digitalisation of X") and flag legitimate purposes that happen to contain a verb; the output is a question list, never a verdict, and the checklist is the gate.
- **Default equalisation changes output.** Every shipped example regenerates once more; the opt-out keeps byte-identity for inputs that want it.
- **Translation of verbs.** Only vocabulary verbs translate; free text stays. Mixed-language inputs get W116 so the author sees it.
- **Layout-quality thresholds** (25 %, 12 px, 35 %, 45 %, 0.5–2.0) are starting values; they are constants in one place and the eval set records how often they fire so they can be tuned.
- **Privacy.** Fixtures and examples are fictional; the review is referred to by its findings only.

---

## Appendix A. Traceability (Review E)

| E item | Plan item | Decision |
|--------|-----------|----------|
| Havaittu ongelma: inconsistent series, no balance measure, `contains` English, legend English | P1.5, P1.8, P1.1–P1.3 | In |
| P1 visual QA (balance, size spread, alignment, utilisation / aspect, scale text + legend) | P1.5 (W117–W120), W115 exists | In, on by default, `--no-layout-quality` opt-out |
| P1 complete translation coverage + regression test | P1.1–P1.3 | In |
| P1 standard-sized, aligned groups (`balanced-grid`, `group_columns`, `cards_per_row`, `card_width`, `equal_group_width`, `align_groups`) | P1.6, P1.7 | In; `layout: balanced-grid` expressed as the option set |
| P2 task map stakeholder layout; inventory vs path; no invented links | P2.1 | In |
| P2 publication profile for native rendering | P2.2 | In |
| P2 `qa.json` manifest | P2.3 | In |
| Acceptance tests 1–6 | §7 | In |
| Täydennys P0 semantic gate 1–6 | P0.1–P0.4 | In as flags + checklist; approval stays human |
| Täydennys: automatic heuristics must not decide | §2, P0.1 exit codes | Rule adopted |
| Client-specific correction section | — | Out (not repository content) |
