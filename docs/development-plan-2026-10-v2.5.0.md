# EDGY skills development plan (2026-10, part 5): v2.5.0 — C4, realisation trace, presenter scope

**Revision 2 (2026-10-17) — DRAFT for agent review.** Revision 1 was
reviewed by three Claude sub-agents: C4 feasibility against the code, the
trace / model / presenter, and an adversarial pass. They found three
blockers, 28 majors and 8 minors; §10 maps each one to its change. This
revision waits for Vibe and Codex on PR #8 and for the owner's decisions
in §3. Nothing is locked.

It follows the released v2.4.0 (tag `v2.4.0`, merge commit `01a5dbe`) and
takes over §4 of
[`development-plan-2026-10-architecture-views.md`](development-plan-2026-10-architecture-views.md):
F4 C4, F6b presenter effects and F7 realisation trace.

> 🔒 No client material was used for this plan. All examples are fictional
> (Acme Transit; prompt tests Nordlake Ferries). See `CONTRIBUTING.md`.

---

## 0. How v2.5.0 is made (owner decision, 2026-10-17)

One branch, one draft PR, five phases. A phase ends only when its gate holds.

| # | Phase | Who | Output | Gate |
|---|-------|-----|--------|------|
| 1 | **Plan iteration** | Vibe, Codex and Claude sub-agents review; Claude revises | this plan, revisions 2…n; the review log in §10 | every finding answered in §10; the owner has decided Q1–Q6; the plan is marked LOCKED |
| 2 | **Test cases** | Claude drafts; Vibe and Codex review | `docs/testing/v2.5.0-agent-test-plan.md` | every acceptance line of §8 has at least one test id; both reviewers agree |
| 3 | **Development** | Claude, one commit per sprint (§6) | code, docs, examples, CHANGELOG | `tools/check.sh` and CI green after every sprint; every new rule, view and hook has a test |
| 4 | **Testing** | Vibe, Codex, Claude sub-agents (fresh sessions, installed skills); a person for the browser and PDF checks | one report per agent on the PR | no open blocker or major finding; §8 met |
| 5 | **Release** | Claude fixes the findings (budgeted, §6); the owner approves, merges, tags and publishes the release | tag `v2.5.0` on the merge commit, GitHub Release from CHANGELOG | CONTRIBUTING → *Releasing*. This session cannot push tags, so the owner tags. |

The test plan of v2.4.0 (`docs/testing/v2.4.0-agent-test-plan.md`) is the
template for phase 2.

## 1. Baseline (v2.4.0, `main` at `01a5dbe`; verified by the reviewers)

| Area | Today | Matters for |
|------|-------|-------------|
| Notation handlers | `skills/documentation/edgy-diagram/scripts/edgy_notation.py:9-21`: a skill with `notation.json` gets `generate_page(page_text, graph)` and `lint_page(cells, page_name)`. E013 fails closed and E012 forbids mixed pages. **But:** a `notation:` page body is still parsed as EDGY and enters the document graph (`edgy_document.py:116-123`, `edgy_parser.py:458`). `expand:` pages never reach the handler, so they fail open (`edgy_document.py:131-143`). A handler has no channel for findings, and the preview, presenter and PlantUML paths draw every page generically (`edgy_render.py:501-530`, `edgy_present.py:157`). | F4 needs core fixes first (F4-core) |
| Page links | draw.io stores a link on a `<UserObject link="data:page/id,…">` wrapping the cell. The linter, the renderer and the presenter read only bare `mxCell` (`edgy_lint.py:383`, `edgy_render.py:168`, `edgy_present.py:96`). Page ids are slugs of page names (`edgy_document.py:40-58`). | F7 clicking |
| `expand:` | one mode, one element type; an element without an id is an error (`edgy_graph.py:37-41, 225-235`) | F7 `expand: trace` |
| Registry / install | `registry.yaml` is rebuilt from SKILL.md frontmatter with fixed fields, so a `requires:` key would be dropped and fail `check.sh` (`tools/registry-updater.py:41-58`). **claude-code and generic copy the skill directory. Vibe and Cursor install SKILL.md only** (`mistral-vibe/install.sh:78-83`, `cursor/install.sh:61-77`), and curl mode does the same (`_shared/source.sh:171`). claude-code, Vibe and Cursor swallow a failed skill. `check.sh` runs no install test. | F4 install, M1 |
| Model format | 1.9: `journey` is one object (the schema does not forbid an `id` on it); `gaps` exists only on capabilities, with W127 band keys and `additionalProperties: false`. Compatibility fixtures exist only for 1.8 (`tools/fixtures/compat-1.8`). | M2 |
| EDGY links | `organisation → process` *performs* is the only core *performs*; `people → process` is **E010** (`edgy-core-links.yaml:43`, `edgy_lint.py:587`). No core link leaves a channel downwards; the influence verb `offers` (product → channel) exists (`:63`). | F7 link table |
| Presenter | `presenter.js` 630 lines, five effects (paging and deep links are effect 5, `:2, :479`); a card click means inspect + zoom; the hash route uses `replaceState`; phone layout since `9384a7b` | F7 drill-through |
| Eval model | `examples/eval/architecture-views.txt`: 65 chain elements (3 products, 12 capabilities, 16 processes, 28 assets, 1 people, 5 organisations); **no journey, task or channel**, no `makes` / `creates`; one `interacts with` | F7, F4 acceptance |

## 2. Scope

| Id | Feature | Status in revision 2 |
|----|---------|----------------------|
| F7 | Realisation trace (journey ↔ organisation), pages, links, presenter drill-through | **in**, P0 |
| F4-core | Notation pages done properly in edgy-diagram 2.9.0 (§4) | **in**, P0, needed by F4 |
| F4 | `edgy-c4` 0.1.0: L1 derived, L2 from C4 pages, draw.io output | **in**, P0, scope per Q2 |
| Q3 | Trace card → C4 L1 link | **in**, separate and droppable |
| M1 | Adapters report failed skills; install tests | **in**, P1 |
| M2 | Model format 1.10: journeys with ids, `gaps` on chain types | **in**, ships with F7 |
| D1 | Docs: migration 1.9 → 1.10, trace and C4 user guide, adapter support table, register update, edgy-framework journey / task / channel modelling | **in** |
| — | Capability `nature` split, C4-PlantUML, F6b effects, C4 L3 | **out** (v2.6.0 candidates) |

## 3. Decisions for the reviewers and the owner

Revision 2 records the Claude reviewers' answers. Vibe and Codex may still
object; then the owner decides.

| Q | Question | Revision 2 position | Reviewers |
|---|----------|---------------------|-----------|
| Q1 | How far does the presenter go? | **A: only the F7 drill-through, as part of effect 5** (paging and deep links). The cap stays at **5** effects. The rest of F6b waits for workshop evidence. | all three agree on A; the adversarial reviewer: keep the cap at 5 rather than "5 + 1" |
| Q2 | How far does C4 go? | **L1 + L2.** L2 comes only from C4 pages and never from the EDGY model. No L3. C4-PlantUML moves to 0.2.0. | agree; PlantUML output needs a core hook and cannot be checked in CI (no Java) |
| Q3 | How do C4 and the trace meet? | One link from an application card to its L1 page, through a core **C4 page index**. Without `edgy-c4`, the link is left out, never left dangling. | agree; it is core code, so it gets its own estimate |
| Q4 | Split the capability `nature` field? | **Deferred to v2.6.0.** 1.10 = journeys with ids + `gaps` keys only. | two reviewers: the split changes three writers and is unrelated to F7 / F4 |
| Q5 | One release or two? | **One v2.5.0, with separate acceptance for F7 and F4.** M2 ships with F7; M1 can ship alone; F4 needs F4-core. Sprints are split so the slip lines are real (§6). | agree, with the coupling fixed |
| Q6 | What is missing? | D1 docs; edgy-deep-dive 1.1.2 (it reads journey as one element); edgy-assessment emits the Experience links; a fix budget after testing | from the adversarial review |

## 4. Features

### F7 Realisation trace — P0

**Levels:**

| Level | Elements |
|-------|----------|
| 1 | Journey |
| 2 | Task, Channel |
| 3 | Product |
| 4 | Capability |
| 5 | Process, Asset, People |
| 6 | Organisation |

**Links.** The trace walks EDGY 23 core links, the v2.4.0 influence verbs
and the tree link `contains`. Every edge is drawn with its real verb and
direction. Flows are left out.

| Between levels | Links |
|----------------|-------|
| 1 ↔ 2 | task → journey *is part of* (core); journey → channel *traverses* (core) |
| 2 ↔ 2 | task → channel *uses* (core), shown beside the focus |
| 3 → 1, 2 | product → task *serves*; product → journey *features in* (core) |
| 3 → 2 | product → channel *offers* (influence), so a channel has products below it and no false W129 |
| 3 → 4 | product → capability *requires* (core) |
| 5 → 3 | process → product *creates* (core) |
| 5 → 4 | process → capability *realises*; capability → asset *requires* (core) |
| 5 ↔ 5 | process → asset *requires* (core); process → data asset *accesses*; people → asset *interacts with* (influence) |
| 6 → 3, 4, 5 | organisation → product *makes*, → capability *has*, → process *performs* (core); organisation → asset *manages* (influence) or `{owner:}` |
| 6 → 5 | organisation *contains* people (tree) |

`people → process` is not an EDGY link: it is E010 today, and the trace
does not draw it. People reach the trace through *interacts with* and
*contains*. The v2.4.0 swimlane is unchanged.

**Page.** `map_type: trace`, `focus: TSK-03`. The page has three bands:
- **above:** the linked elements of lower levels, small and dimmed;
- **centre:** the focus card, its *part of* / *parts* chips, and the
  linked elements of the same level;
- **below:** the linked elements of higher levels, grouped by level, with
  band headers.

`trace_direction: both | down | up`, default `both`. More than 12 cards in
a band are shown as 11 cards and a "+N more" card that links to a list
page. Every card hidden this way is counted in `generator_notes[]`.

**Pages from the graph.** `expand: trace` is a new multi-type mode. It
writes one page per element with an id at levels 1–6, plus a **trace
index** page drawn as a two-column list (journeys | organisations). An
element without an id is skipped and counted in a note, not an error.

| `where:` value | Pages written |
|----------------|---------------|
| ids | only those elements |
| `highlight` | the highlighted elements |
| `from JRN-01` (new) | the elements reachable from JRN-01 |

`edgy_model_to_txt.py --views trace` writes the same pages from a model.
`trace` is **not** part of `--views all`, so 1.9 output stays unchanged.

**Stable ids.** A trace page has the id `trace-<model id>`, independent of
its name and of the page order. The presenter's views JSON carries
`focus`. A test checks that the ids stay the same when an element is
renamed.

**Links in draw.io.** Every card with its own page is wrapped in
`<UserObject link="data:page/id,trace-…">`. The linter, the native
renderer and the presenter unwrap `UserObject` / `object` (id, `label`)
before they read cells, with a test. P03 checks that the links survive in
an exported PDF.

**Presenter (inside effect 5):**
- **Card wall:** the trace pages appear as one **Trace** card (the index
  page), not one card each.
- **Drill-through gesture:** the first click on a card inspects it, as
  today. A "→" badge on a linked card, or a second click, opens the card's
  trace page.
- **Navigation:**
  - `#/trace/JRN-01/TSK-03/…` routes use `pushState`, so the browser's
    *back* works;
  - a breadcrumb shows the path taken;
  - a new self-test step covers drill, breadcrumb and back.

About 150 lines of JS, 30 of CSS and 30 of Python. The cap comment at
`presenter.js:2` says "five effects; drill-through belongs to 5".

**Gaps.** An empty *below* band on the way down is **W129**, with the W127
statuses, written to `model_gaps[]`. On the way up, an orphan (an asset
that no capability requires) is a note.

**Eval model.** Sprint 26 adds 2 journeys, about 8 tasks, 3 channels and
`makes` / `creates` / `offers` links to the eval model (fictional data):
about 80 trace pages. The example is `examples/trace-map.txt`.

### F4-core — edgy-diagram 2.9.0, P0 (from the C4 review)

1. A `notation:` page keeps only its header keys in the EDGY parser. Its
   body goes only to the handler and stays out of `build_graph`, so no
   containers or C4 edges appear in the graph, the presenter or the E014
   checks.
2. `expand:` pages call the handler as well. `notation: c4` with
   `expand: per-application` then produces one page per application, and
   without a handler it is **E013**, closing the fail-open case. `focus:`
   is accepted as well as `system:`.
3. **Findings channel:** `generate_page` may return `(xml, findings)`, and
   the core reports those findings as warnings or errors. This is an
   optional, compatible addition to contract §4, which stays at
   `contract: 1`.
4. **Drawing:** C4 pages use **static** styled rectangles and the existing
   `person` shape, with no probing of `mxgraph.c4.*`. The preview and the
   presenter therefore draw them through the generic renderer, and no
   `page_svg` hook is needed. The contract text that still promises a
   "shape hook" is corrected.
5. **C4 page index** in the document graph: (notation, level, system) →
   page id, for Q3.
6. The `{container:}` key on an EDGY `transfers` is an **opt-in extension
   key**. The EDGY render, TXT and ArchiMate paths ignore it, with a test.

### F4 `edgy-c4` 0.1.0 — P0

**Skill and install.**
- `skills/documentation/edgy-c4/` with its own SKILL.md, `notation.json`
  (`contract: 1`) and `scripts/edgy_c4.py`.
- `agents: [claude-code, generic]`. Vibe, Cursor and curl mode refuse
  edgy-c4 with a clear message, because they install SKILL.md only.
- `requires: [edgy-diagram]` goes into the frontmatter, the registry
  updater, the validator and `lookup-skill.py`. It has no version range:
  the adapters install one ref.

**L1 (`level: context`)** is derived from the graph:
- **Person:** People or organisations that *interact with* the
  application, or that *perform* a process which *requires* it.
- **Software System:** the other `transfers` partners. `[external]` ones
  are drawn grey.
- **Missing Person:** a **note**, not a warning, so the L1 page still
  passes strict lint.
- **Integration bus:** not modelled in 0.1.0. No input names a bus, and
  `via:` is already taken by the waypoint syntax.

**L2 (`level: container`)** comes from hand-written C4 pages:
- containers have ids: `- container: "Fare API" {id: C-FARE-API,
  technology: …}`;
- a relationship has a description and `{technology:}`;
- a boundary crossing names a container through `{container: C-…}` on the
  EDGY `transfers`.

**Rules.** Checked at generate time, because they need the graph:

| Rule | Checks |
|------|--------|
| C001 | `{container:}` names an unknown container |
| C002 | relationship without a description |
| C003 | L2 relationship without a technology |
| C004 | `system:` is not an application asset, or is a platform / integration kind |
| C005 | `system:` is not drawn on its L1 page |
| C006 | duplicate container id |

`lint_page` checks only geometry and text rules on a `.drawio` file.

**Output and docs.**
- Output is draw.io only. C4-PlantUML moves to 0.2.0.
- Legend "C4 model (Simon Brown, CC BY 4.0)". The register entry changes
  from *planned* to *in use* and is corrected (no PlantUML in 0.1.0).
- The C4 derivation guidance lives in edgy-c4's SKILL.md, **not** in
  edgy-framework (principle 4).

**edgy-target-state 1.3.0.** C4 only for applications in a *decided*
building block. This is a must check in the target-state prompt test, not
a rule in the skill, because edgy-c4 has no data about decisions.

### Q3 Trace ↔ C4 link — droppable

An application card on a trace page links to `c4-context-<APP id>` when
the C4 page index has that page. Without it, the card has no link.

### M1 Adapters — P1

claude-code, Vibe and Cursor count and list failed skills, exit 1, and do
not print "Asennus valmis" when anything failed. A new `check.sh` step
`adapter-install` runs claude-code and generic against a temporary
directory, including edgy-c4 with its requirement. It also runs one
broken registry entry, which must exit 1.

### M2 Model format 1.10 — ships with F7

- `journey`: one object (1.9) or an array of journeys with `id` (`oneOf`,
  as `organisation` in 1.9). A journey `id` and a journey array are gated
  as 1.10 structures.
- `gaps` on every chain type, from **one key set**: `tasks`, `channels`,
  `products`, `capabilities`, `processes`, `resources`, `actors`, `data`,
  `organisation`. The W127 keys keep their meaning. Each type allows the
  keys of its *below* levels.
- **New `compat-1.9` fixtures,** written with the v2.4.0 scripts: 1.9 and
  1.8 inputs give byte-identical TXT, diff and ArchiMate output.
- edgy-assessment emits the Experience links (*serves*, *features in*,
  *offers*) when it extracts a 1.10 model.
- edgy-deep-dive 1.1.2 reads a journey array.
- Migration notes 1.9 → 1.10 in edgy-assessment.

## 5. Target state

| Skill | v2.4.0 | v2.5.0 |
|-------|--------|--------|
| edgy-diagram | 2.8.0 | **2.9.0**: F7 trace, F4-core, page-link unwrapping, presenter drill-through |
| edgy-assessment | 1.10.0 | **1.11.0**: model format 1.10, `--views trace`, Experience links, migration notes |
| edgy-framework | 1.7.0 | **1.8.0**: modelling journeys, tasks and channels with ids and links |
| edgy-target-state | 1.2.0 | **1.3.0**: C4 for decided building blocks |
| edgy-deep-dive | 1.1.1 | **1.1.2**: journey array |
| edgy-c4 | — | **0.1.0** (claude-code, generic) |

If F7 slips, edgy-diagram 2.9.0 is F4-core alone, and M2 and the trace
docs slip with it. If F4 slips, edgy-diagram 2.9.0 still ships F4-core,
which is useful on its own: it closes the `expand:` fail-open.

## 6. Sprints and estimate

| Sprint | Content | Estimate |
|--------|---------|----------|
| 25a | M2: schema 1.10, gaps keys, version gate, `compat-1.9` fixtures, migration notes | 2–3 d |
| 25b | M1 adapters; `requires:` in frontmatter, updater, validator, lookup; `adapter-install` step | 3–4 d |
| 26 | F7 core: `expand: trace` mode, traversal, layout, index and list pages, stable ids, `UserObject` unwrapping, W129, `--views trace`, eval Experience part, `trace-map.txt` | 7–8 d |
| 27 | F7 presenter: Trace card, drill gesture, `pushState`, breadcrumb, self-test | 3 d |
| 28a | F4-core 1–6 | 3–4 d |
| 28b | F4 `edgy-c4`: L1 derivation, L2 pages, C001–C006, static shapes, legend, register, example `c4-fare-engine.txt` | 5–6 d |
| 29 | Q3 link; edgy-target-state 1.3.0; edgy-framework 1.8.0; edgy-deep-dive 1.1.2; D1 docs; CHANGELOG | 3 d |
| — | Fix budget after phase 4 (v2.4.0 needed several pixel-review rounds) | 4–5 d |

**Total about 30–36 days.** The order lets the slip lines hold: 25a → 26
→ 27 is F7; 25b → 28a → 28b is F4; 29 joins them.

**Cut list if it slips, in this order:**
1. the Q3 link;
2. edgy-target-state 1.3.0;
3. C4 L2 (ship L1 only);
4. all of F4 except F4-core.

F7, M2, M1 and F4-core are the last to go.

## 7. Test strategy (expanded in phase 2)

**Unit and golden tests:**
- the trace levels, link table and directions;
- `people → process` is never drawn;
- channel pages use *offers*;
- stable page ids;
- `UserObject` unwrapping in lint, render and present;
- W129 and the gaps keys;
- `compat-1.9`;
- notation page isolation (no graph leak);
- `expand:` with a handler, and without one (E013);
- the findings channel;
- C001–C006;
- `requires:` in the registry;
- the `adapter-install` step.

**Gates:**
- `trace-map.txt` and `c4-fare-engine.txt` pass strict lint;
- the eval model with `expand: trace` scores 0 / 0 / 0 for lint, visual
  and layout findings;
- the C4 L1 for every eval application passes strict lint.

**Agent tracks** (fresh sessions, installed skills only):
- a trace down from a journey;
- a trace up from an organisation;
- C4 for one application;
- C4 for an undecided building block, refused by edgy-target-state (must);
- a model gap reported as a gap;
- a 1.9 model migrated to 1.10.

**Pixel review and rubric** on every new page type: the trace, the index,
the list page, C4 L1 and C4 L2.

**People:**
- P03 again in Chrome, Firefox, Safari and on a phone, adding drill,
  breadcrumb, back and the PDF links;
- one person opens the C4 pages in draw.io desktop.

## 8. Acceptance

**F7**
- From the eval model's journey, every level down to organisation and
  back up is reachable by links.
- Every link resolves.
- Every trace page scores 0 / 0 / 0.
- W129 statuses are written to `model_gaps[]`.
- Hidden cards are counted in `generator_notes[]`.
- The page ids stay the same across a rename.
- Browser *back* works.

**F4-core**
- A notation page leaves nothing in the graph.
- `expand:` reaches the handler, and without a handler it is E013.
- Handler findings are reported.
- `{container:}` is ignored by the EDGY paths.

**F4**
- An L1 page exists for every application of the example and eval
  models. A missing Person is a note, and strict lint is clean.
- L2 comes from the example C4 page.
- C001–C006 are tested.
- edgy-c4 installs with its requirement on claude-code and generic, and
  is refused with a clear message on Vibe, Cursor and in curl mode.

**M1:** a broken entry exits 1 and names the skill.

**M2:** 1.9 and 1.8 inputs give byte-identical output; 1.10 validates.

**Quality**
- The pixel review of each new page type has **0 open findings**.
- The rubric scores **≥ 10 / 12 with no 0** on trace and C4 pages.
- Examples change only where a feature changes them
  (`tools/compare-style-only.py`).

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| Trace pages crowd the wall and the tab strip | one Trace card; `where:` filters; size budget |
| Output depends on the environment (as Pillow did in v2.4.0) | C4 shapes are static; no probe |
| Effects creep | the cap stays at 5; drill-through is part of effect 5 |
| An adapter breaks during install | the `adapter-install` step in `check.sh` |
| C4 knowledge leaks into EDGY skills | C4 guidance only in edgy-c4; the container key is opt-in and ignored by the EDGY paths |
| 1.10 breaks old models | `compat-1.9` and `compat-1.8` fixtures |
| Pictures that lint passes but people cannot read | pixel review and rubric are acceptance criteria, not advice |

## 10. Review log

**Revision 2 — three Claude sub-agent reviews of revision 1** (C4 vs
code; trace, model and presenter; adversarial). Every finding was checked
against `main`.

| Finding (source) | Severity | Change |
|------------------|----------|--------|
| Vibe and Cursor install SKILL.md only, so edgy-c4 would always be E013 (adv 1, C4 7) | blocker | §1 corrected; edgy-c4 `agents: [claude-code, generic]`; refused elsewhere |
| A C4 page body is parsed as EDGY and leaks into the graph (C4 1) | blocker | F4-core 1 |
| `people → process performs` is E010 (trace 1) | blocker | removed from the trace; people via *interacts with* and *contains* |
| `expand:` skips the handler and fails open (C4 2) | major | F4-core 2 |
| No findings channel (C4 3) | major | F4-core 3 |
| `lint_page` has no graph (C4 4) | major | C rules at generate time |
| No preview / presenter / PlantUML hook (C4 5) | major | static shapes via the generic renderer; PlantUML to 0.2.0 |
| `requires:` dropped by the registry updater; a version range is meaningless (C4 6) | major | frontmatter + updater + validator + lookup; no range |
| The bus rule has no input; `via` is taken (C4 8) | major | no bus in 0.1.0 |
| Q3 needs a C4 page index (C4 9) | major | F4-core 5 |
| L1 Persons empty for 17 of 18 (C4 10) | major | Persons also through *performs* → *requires*; a note, not a warning |
| Sprint 28 underestimated (C4 13; adv 11) | major | 28a + 28b; fix budget; total 30–36 d |
| M1 targets the wrong adapters (adv 2) | major | claude-code, Vibe, Cursor |
| No install tests exist (adv 3) | major | `adapter-install` step in 25b |
| C4 knowledge in edgy-framework; `{container:}` on EDGY edges (adv 4) | major | guidance in edgy-c4; F4-core 6 |
| The `mxgraph.c4` probe depends on the environment (adv 5) | major | static style |
| Register says PlantUML is used "only if vendored"; no Java in CI (adv 6) | major | PlantUML out of 0.1.0; register corrected |
| "5 + 1" effects is creep (adv 7) | major | drill-through inside effect 5 |
| Weak acceptance; pixel review not required (adv 8) | major | §8 Quality |
| An undecided building block is not skill data (adv 9) | major | a prompt-test must check |
| Q5 slip lines do not hold (adv 10) | major | sprints 25a / 25b / 28a; §5 slip text |
| `contains` is a tree link, not core (trace 2) | major | link rule names it |
| Channels have no link down, so false W129 (trace 3) | major | *offers* |
| Page links sit on `UserObject`, which three readers ignore (trace 4) | major | unwrapping in all three, with a test |
| Page ids change with a rename (trace 5) | major | `trace-<model id>`, `focus` in views JSON |
| `expand:` is single-type; a missing id is an error; no `from` (trace 6) | major | multi-type `trace` mode; note; `where: from` |
| The eval model has no Experience part (trace 7; adv) | major | added in sprint 26 |
| Two vocabularies for `gaps` keys (trace 8; adv 13) | major | one key set |
| No 1.9 fixtures; `trace` in `--views all` would change 1.9 output (trace 9) | major | `compat-1.9`; `trace` not in `all` |
| C001–C006 incomplete (C4 11) | minor | rule set rewritten |
| Register status and PlantUML text (C4 12) | minor | register update in 28b |
| Journey array is cheap (trace 10) | minor | 25a at 2–3 d |
| About 100 cards on the wall (trace 11) | minor | one Trace card |
| Card click already means inspect; `replaceState` breaks back (trace 12) | minor | drill gesture; `pushState` |
| `nature` split unrelated (adv 12; trace Q4) | minor | deferred to v2.6.0 |
| Wrong paths in §1 (adv 14) | minor | corrected |
| Q6: migration notes, deep-dive, framework guidance, user guide, adapter docs, example in a sprint (adv) | — | D1, M2, sprint 26 / 29 |

**Revision 1 (2026-10-17):** first draft.
