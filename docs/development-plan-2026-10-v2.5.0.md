# EDGY skills development plan (2026-10, part 5): v2.5.0 — C4, realisation trace, presenter scope

**Revision 1 (2026-10-17) — DRAFT for agent review.** Nothing in this plan is
locked. This revision proposes a scope and asks the reviewers (Vibe, Codex,
Claude sub-agents) the open questions in §3, where each question carries a
recommendation. It follows the released v2.4.0 (tag `v2.4.0`, merge commit
`01a5dbe`) and takes over §4 of
[`development-plan-2026-10-architecture-views.md`](development-plan-2026-10-architecture-views.md):
F4 C4, F6b presenter effects and F7 realisation trace (revision 6 there).

> 🔒 No client material was used for this plan. All examples are fictional
> (Acme Transit; prompt tests Nordlake Ferries). See `CONTRIBUTING.md`.

---

## 0. How v2.5.0 is made (owner decision, 2026-10-17)

One branch, one draft PR, five phases. A phase ends only when its gate holds.

| # | Phase | Who | Output | Gate |
|---|-------|-----|--------|------|
| 1 | **Plan iteration** | Vibe, Codex, Claude sub-agents review; Claude revises | this plan, revisions 2…n; the review log in §10 | every finding answered; the §3 decisions taken by the owner; plan locked |
| 2 | **Test cases** | Claude drafts; Vibe and Codex review | `docs/testing/v2.5.0-agent-test-plan.md`: every feature's tests, agent tracks, quality rubric, human browser checks | reviewers agree the tests cover the plan's acceptance (§8) |
| 3 | **Development** | Claude, one commit per sprint | code, docs, examples, CHANGELOG | `tools/check.sh` green; CI green; every new rule and view has its test |
| 4 | **Testing** | Vibe, Codex, Claude sub-agents (fresh sessions, installed skills); a person for the browser checks | one report per agent on the PR | no open blocker or major finding |
| 5 | **Release** | Claude fixes the findings; owner approves, merges, tags | tag `v2.5.0` on the merge commit, GitHub Release from CHANGELOG | CONTRIBUTING → *Releasing* |

The test plan of v2.4.0 (`docs/testing/v2.4.0-agent-test-plan.md`) is the
template for phase 2: tracks per agent, must / must-not checks, pixel
review, a 6 × 0–2 quality rubric, a report template.

## 1. Baseline (v2.4.0, read from `main` at `01a5dbe`)

| Area | Today | Matters for |
|------|-------|-------------|
| Notation handlers | `scripts/edgy_notation.py`: a skill with `notation.json` (`{"notation": "c4", "contract": 1, "module": …}`) gets `generate_page` / `lint_page`; E013 fails closed, E012 forbids mixed pages; `edgyNotation` on every foreign cell | F4 — the hook exists; no handler ships |
| Renderer shapes | `edgy_render.py` draws EDGY shapes only | F4 needs a shape hook or handler-drawn SVG |
| Registry / install | `registry.yaml` has no `requires:`; adapters copy one skill directory each; `install.sh --all` swallows a failed skill (`install_skill … \|\| true`, then "Asennus valmis") — found by Vibe in v2.4.0 testing | F4 dependency on edgy-diagram; M1 |
| Model format | 1.9: `journey` is **one object without id**; `gaps` only on capabilities; capability `nature` mixes role (core / enabling / management) and value (differentiating / commodity) | F7 needs journey ids; M2 |
| Presenter | `presenter.js` 630 lines, five effects (cap), CSP with hashes, `connect-src 'none'`, headless self-test in CI, phone layout since `9384a7b` | F7 navigation; F6b |
| Document graph | ids, occurrences, relationships across pages, `expand: per-…` | F7 traversal; F4 L1 derivation |

## 2. Scope candidates

| Id | Feature | Origin | Proposal |
|----|---------|--------|----------|
| F7 | Realisation trace: journey → task / channel → product → capability → process / asset / people → organisation, and back; one page per element; draw.io page links; presenter breadcrumb | owner request 2026-10-17 | **in** (P0) |
| F4 | `edgy-c4` skill 0.1.0: C4 Level 1 derived from the graph, Level 2 from C4 pages | plan part 4 §4 | **in** (P0), scope per Q2 |
| F6b | Presenter effects: edge draw-in, spotlight, impact trace, two-state morph, minimap, guided tour, presenter window | plan part 4 §4, deferred | **mostly out**, per Q1 |
| M1 | `install.sh --all` reports a failed skill and exits non-zero | Vibe, v2.4.0 testing | **in** (small) |
| M2 | Model format 1.10: journeys as an array with ids, `gaps` on every chain type; optional split of capability `nature` | F7; principles audit | **in** for F7; the split per Q4 |

## 3. Decisions for the reviewers and the owner

Each question has options and a recommendation. Reviewers: agree, object
with a reason, or add an option.

### Q1 — How far does the presenter go?

| Option | Content | Cost / risk |
|--------|---------|-------------|
| **A** | F7 navigation only: page links, breadcrumb, deep link `#/trace/…`, *back*. The effects cap becomes **5 + 1** (drill-through), written down as the new cap | smallest; reuses the zoom; one new self-test step |
| B | A + one or two F6b effects chosen now (candidates: *impact trace* between two elements; *guided tour* file with captions) | each effect: JS, CSP-safe, reduced-motion path, self-test, P03 in three browsers |
| C | A + all F6b | product-grade UI; the P03 burden grows with every effect; the single-file size budget tightens |
| D | Presenter moves to a companion repo against `contract: 1` | second registry and release train; nothing gained while one person maintains it |

**Recommendation: A.** The value of the presenter in v2.4.0 came from
showing that the views are one model. F7 adds the strongest version of
that, the click-through. Every F6b effect still has no workshop evidence
behind it. *Impact trace* overlaps F7: a trace page already shows what
depends on what. The rest of F6b stays deferred until a real engagement
asks for one. In that case it is a v2.6.0 plan item with its own P03
round.

### Q2 — How far does C4 go?

| Option | Content | Note |
|--------|---------|------|
| L1 only | System context derived from the document graph: People and organisations that `interacts with` the application → Person; the other `transfers` partners → Software System (`[external]` grey) | needs no new input; but answers only "who and what is around it" |
| **L1 + L2** | as above, plus Containers from hand-written C4 pages (`notation: c4`, `level: container`, `system: APP-07`, `- container: "Fare API" {technology: …}`) | the plan of part 4; containers are design knowledge, not in an EDGY model |
| L1 + L2 + L3 | plus Components | grows C4 into its own modelling framework; not EDGY's level |
| L2 in the model | containers as a 1.10 model field | puts a foreign notation's elements into the EDGY model — against principle 4 |

**Recommendation: L1 + L2, with L2 only from C4 pages.**
- **Drawing:** the draw.io C4 shapes (`mxgraph.c4.*`, probed first, with
  styled rectangles as the fallback). The handler draws its own preview
  SVG, so `edgy_render.py` needs only a pass-through for `edgyNotation`
  cells and no general shape hook.
- **C4-PlantUML output:** written for the PlantUML standard library
  (`!include <C4/C4_Container>`). Nothing is vendored or fetched.
- **Lint:** C001–C006 in the skill.
- **edgy-target-state:** draws C4 only for applications in a *decided*
  building block (unchanged from part 4).

### Q3 — How do C4 and the trace meet?

**Recommendation:** an application card on a trace page links to its C4
L1 page when `edgy-c4` is installed and the page exists; in the presenter
the breadcrumb continues into the C4 page. Without `edgy-c4` nothing
changes. One link, through the existing contract — no new contract version.

### Q4 — Model format 1.10: how much?

Required by F7: `journey` as an object (1.9) or an array of journeys
with `id`, using the same `oneOf` migration contract as `organisation` in
1.9, plus `gaps` on every chain type.

The open part is the capability `nature` field. Today it mixes two
classifications (see the register).

**Recommendation:** add the fields `role` (core / enabling / management)
and `value` (differentiating / commodity). Keep `nature` valid with a
deprecation note. The 1.9 byte-identical contract holds. If the
reviewers see this as scope creep, it moves to v2.6.0.

### Q5 — One release or two?

**Recommendation: one v2.5.0, with separate acceptance for F7 and F4.**
If either slips, it moves to v2.6.0 without blocking the other, as F6a
was allowed to in v2.4.0. M1 and M2 ship with whichever goes first.

### Q6 — Anything missing?

Reviewers are asked to name what a v2.5.0 should contain that is not
here. Two candidates were left out on purpose:
- Identity facet links in the trace (brand, purpose): the chain stays in
  the Architecture and Experience facets in this release.
- A Level 3 C4 view.

## 4. Features

### F7 Realisation trace — P0

As specified in part 4, revision 6, §4 F7. In short:
- **Levels:** 1 journey, 2 task + channel, 3 product, 4 capability,
  5 process + asset + people, 6 organisation.
- **Links:** only EDGY core links and the v2.4.0 influence verbs, drawn
  with their real verb and direction. Flows are left out.
- **Page:** `map_type: trace` with *above*, *centre* and *below* bands.
  `trace_direction: both | down | up`, and "+N more" above 12 cards.
- **Pages from the graph:** `expand: trace` plus an index page (journeys
  are the entry points down, organisations up), and
  `edgy_model_to_txt.py --views trace`.
- **Clicking:** draw.io page links on every card that has a page, and in
  the presenter a breadcrumb, a deep link and *back*.
- **Gaps:** **W129** for an empty *below* band (statuses as in W127,
  written to `model_gaps[]`). An orphan on the way up is a note.

New in this plan:

- **The eval model needs an Experience part.** Today
  `eval/architecture-views.txt` has 65 chain elements: 3 products,
  12 capabilities, 16 processes, 28 assets, 1 people and 5 organisations.
  It has no journeys, tasks or channels. v2.5.0 adds 2 journeys,
  about 8 tasks and 3 channels, linked to its products, for about
  80 trace pages.
- **Page count and size.** Acceptance: `expand: trace` on the eval model
  generates in under 60 s, and the presentation stays inside the
  `--max-mb` budget, which scales with the page count. Above that, use
  `where: from JRN-01` or `where: <ids>`.
- **The index page** is drawn as a two-column list (journeys | organisations),
  not as a map, so it stays readable at any size.

### F4 `edgy-c4` 0.1.0 — P0

Following part 4, §4 F4 and the Q2 recommendation:

- **Skill:** `skills/documentation/edgy-c4/` with its own SKILL.md,
  `notation.json` (`contract: 1`) and `scripts/edgy_c4.py`
  (`generate_page`, `lint_page`, preview SVG).
- **Install dependency:**
  - `registry.yaml` and the validator get `requires: [edgy-diagram >=2.9]`;
  - the adapters install a required skill transitively and say so;
  - a missing requirement is an install error, not a warning.
- **L1:** `notation: c4`, `level: context`, `system: APP-07` derives the
  page from the graph:
  - Person: People and organisations that *interact with* the system;
  - Software System: the other systems it `transfers` to or from;
  - `[external]` systems are grey;
  - an integration through the bus is drawn as the logical link, with
    `technology: via <bus>`;
  - a warning when no Person interacts with the system.
- **L2:**
  - Container pages, with relationships described as text plus
    `{technology:}`.
  - A boundary crossing attaches to the right container through
    `{container: …}` on the EDGY `transfers`. The v2.4.0 parser already
    reserves the key.
- **Lint C001–C006** (initial list, to refine in review):
  - C001: a container outside a system boundary;
  - C002: a relationship without a description;
  - C003: a relationship without a technology on L2;
  - C004: a system id that is not an application asset;
  - C005: a Person with no relationship;
  - C006: an external system drawn as internal.
- **Outputs:** draw.io (C4 shapes) and C4-PlantUML (standard-library
  includes).
- **Legend:** "C4 model (Simon Brown, CC BY 4.0)", with the register entry
  moved from *planned* to *in use*.
- **edgy-target-state 1.3.0:** C4 L1 / L2 only for applications in a
  decided building block.

### M1 `install.sh --all` — P1

A failed skill is reported, counted and listed; the script exits 1 and
does not print "Asennus valmis" when anything failed. Same fix in the
Cursor and generic adapters if they share the pattern. Test: an install
with one broken registry entry exits 1 and names it.

### M2 Model format 1.10 — P0 (for F7)

Journeys with ids, `gaps` on the chain types, and Q4's capability fields
if accepted. The migration contract stays: 1.9 and 1.8 models give
byte-identical TXT, diff and ArchiMate output, and the 1.9 writers stay 1.9.

## 5. Target state

| Skill | v2.4.0 | v2.5.0 |
|-------|--------|--------|
| edgy-diagram | 2.8.0 | **2.9.0**: `map_type: trace`, `expand: trace`, W129, page links, presenter drill-through, render pass-through for notation cells |
| edgy-assessment | 1.10.0 | **1.11.0**: model format 1.10, `--views trace` |
| edgy-framework | 1.7.0 | **1.8.0**: modelling journeys with ids; deriving C4 L1 from the Architecture facet |
| edgy-target-state | 1.2.0 | **1.3.0**: C4 for decided building blocks |
| edgy-deep-dive | 1.1.1 | 1.1.2 if 1.10 touches it |
| edgy-c4 | — | **0.1.0** |

## 6. Sprints and estimate

| Sprint | Content | Estimate |
|--------|---------|----------|
| 25 | M2 model 1.10 + migration fixtures; M1 install fix; `requires:` in registry, validator and adapters | 3–4 d |
| 26 | F7 traversal, `map_type: trace` layout, `expand: trace`, index page, page links, W129, `--views trace` | 5–6 d |
| 27 | F7 in the presenter: drill-through, breadcrumb, deep link, self-test; effects cap 5 + 1 | 2–3 d |
| 28 | F4 `edgy-c4`: scaffold, L1 derivation, L2 pages, shapes, preview, C001–C006, PlantUML, legend, register | 6–7 d |
| 29 | Q3 link trace ↔ C4, edgy-target-state 1.3.0, examples, eval, docs, CHANGELOG | 2–3 d |

Total about 18–23 days of development, before the testing round.

## 7. Test strategy (expanded in phase 2)

- **Unit and golden tests per feature:**
  - traversal levels and directions;
  - page-link targets;
  - W129 statuses;
  - 1.10 migration;
  - C4 derivation;
  - C001–C006;
  - the `requires:` install.
- **Gates:** examples `trace-map.txt` and `edgy-c4/examples/c4-fare-engine.txt`
  under strict lint. The eval model with `expand: trace` must pass lint,
  visual and layout checks at 0 / 0 / 0.
- **Agent tracks (fresh sessions, installed skills only):**
  - trace from a journey;
  - trace upward from an organisation;
  - C4 for one application;
  - C4 refused for an undecided building block;
  - a model gap reported as a gap.
- **Pixel review of every new page type.** Lint found none of the
  v2.4.0 showcase defects, so the review stays part of the gate.
- **Browser:**
  - a headless self-test step for drill-through, breadcrumb and back;
  - a person runs P03 again in Chrome, Firefox, Safari and on a phone.

## 8. Acceptance (draft)

- F7: from the eval model's journey, a reader reaches the organisation in
  ≤ 5 clicks and returns by *back* to the journey; every link resolves; all
  trace pages 0 / 0 / 0; W129 statuses in `model_gaps[]`.
- F4: L1 for every application of the example model without hand input;
  L2 from the example C4 page; strict lint clean; E012 / E013 behaviour
  unchanged; `edgy-c4` installs with its requirement and refuses without it.
- M1, M2 as in §4.
- No breaking change for 1.8 / 1.9 inputs; examples change only where a
  feature changes them, shown by `tools/compare-style-only.py`.

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| Trace pages explode on a large model | `where:` filters; size budget; index page as a list |
| C4 shapes differ between draw.io versions | probe `mxgraph.c4.*`, fall back to styled rectangles; the preview SVG is drawn by the handler |
| Effects creep back in | the cap is written as 5 + 1; anything else is v2.6.0 |
| Transitive install breaks an adapter | install tests per adapter in `check.sh` |
| 1.10 breaks old models | migration fixtures as in 1.9 |

## 10. Review log

*Empty: revision 1 awaits the phase 1 review.*
