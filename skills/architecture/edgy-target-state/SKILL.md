---
name: edgy-target-state
version: "1.0.0"
description: >
  Internal target-state architecture workflow on EDGY 23: strategy → purpose map,
  capability map and cards, guardrails, building-block hypothesis with transition
  overlay, work packages, decision records (via an external ADR skill), role model
  and a stakeholder summary. Orchestrates edgy-framework (target-state mode) and
  edgy-diagram (generator, lint, preview). Complements edgy-assessment, which is
  the outside-in assessment of a company from public sources.
category: architecture
tags: [edgy, enterprise-design, architecture, target-state, capability-map, roadmap, fi, en]
languages: [fi, en]
agents:
  - claude-code
  - cursor
  - generic
inputs:
  - name: programme
    type: text
    description: Name and scope of the target-state work (organisation or unit, horizon year)
  - name: sources
    type: text
    description: >
      Internal material: strategy documents (PDF/xlsx), meeting notes or minutes,
      an existing current-state model (.archimate or draw.io), interviews, existing
      wiki pages. Read before writing; never write to external systems unasked.
  - name: phases
    type: text
    required: false
    description: >
      Subset of phases 1–8 to run; default is all phases
  - name: language
    type: enum
    values: [fi, en]
    default: fi
outputs:
  - type: directory
    description: >
      <programme>-target-state/: purpose-map, capability-map, reference-architecture,
      organisation-roles and summary diagrams (.drawio + preview .svg/.png), capability
      cards, guardrails, building-block mirror table, work-package cards, decision list,
      and the target-state report (templates/target-state-report.md).
examples:
  - input: examples/acme-transit-brief.md
    output: examples/expected-acme-transit-target-state.md
---

# EDGY Target-State Architecture

## Purpose

This skill runs **internal target-state architecture work** on the EDGY 23
language: from strategy to a purpose map, a stable capability map with cards,
guardrails, a building-block hypothesis shown as a layered reference
architecture with a current → target overlay, work packages that each move
one block and are measured by one Outcome, a role model, and a one-picture
summary for stakeholders.

Use this skill when:
- The subject is your own organisation (or a client's) and the inputs are
  internal: strategy, minutes, an existing current-state model, interviews
- The question is *what must we be able to do, how do we propose to do it,
  and in which order do we get there* — not an outside-in assessment
- Deliverables go to decision makers and procurement, so they must be short,
  cross-referenced by id, and visually consistent

Do **not** use it for an outside-in assessment of a company from public
sources — that is `edgy-assessment`. The Experience facet is optional here;
do not force Task/Channel/Journey if they are not in scope.

**This skill uses internally:**
- `edgy-framework` — `mode: target-state` (artefact definitions, strategy →
  EDGY mapping, capability formulation, role-model check)
- `edgy-diagram` — `edgy_generator.py`, `edgy_lint.py`, `edgy_render.py`
  (purpose, capability, reference, organisation and summary layouts,
  transition overlay)
- an **ADR skill** for decision records when one is available in the agent's
  skill set; otherwise the 40-line template in edgy-framework

**IMPORTANT:** Produce all output in the language given by `language`. Keep
every artefact within the length table in edgy-framework (*Output length by
mode*). Never pad.

## Agent Instructions

### CRITICAL: read the inputs first, write nothing external

1. Read every provided source before producing anything. Existing wiki pages
   and models are read-only until the user asks you to write.
2. Extract three lists before Phase 1: candidate Purposes/KPIs (from
   strategy), candidate capabilities and current systems (from the
   current-state model and interviews), and open decisions (from minutes).
3. Assign ids as you go: `PUR-`, `OUT-`, `CAP-`, `G-`, `BB-`, `WP-`, `ADR-`.
   Ids appear in diagram subtexts (`{id: …}`) and in every document.

### Phase 1 — Strategy → purpose map

1. Map the strategy document with the table *Mapping strategy documents to
   EDGY* (edgy-framework): mission and vision → top Purposes, focus areas →
   sub-Purposes (**never Story**), KPIs → Outcomes, initiatives → Activities.
2. Write `<programme>-purpose-map.txt` (`map_type: purpose`, `{id: PUR-xx}` /
   `{id: OUT-xx}`, `contains` for the hierarchy, `measures` for KPIs,
   Organisation and Brand present).
3. Generate, lint, preview:
   ```bash
   G=skills/documentation/edgy-diagram/scripts
   python3 $G/edgy_generator.py <programme>-purpose-map.txt --output <programme>-purpose-map.drawio --preview
   python3 $G/edgy_lint.py <programme>-purpose-map.drawio
   ```
4. One paragraph: what the map says and what was ambiguous in the strategy.

### Phase 2 — Capability map and cards

1. Formulate capabilities with the helper questions in edgy-framework
   (*Formulating capabilities*): nouns stating a result, system-independent,
   6–12 areas, 40–80 leaves. Never name a capability after a product.
2. Write `<programme>-capability-map.txt` (`map_type: capability`, one
   `group:` per area, `{id: CAP-xx}`, `{highlight: yes}` for first-round
   decision units). Generate, lint, preview.
3. Write cards (`templates/capability-card.md`) for the first-round decision
   units only — area or building-block level, ≤ 1 page each. A card names
   requirements, quality requirements, owned data and its master, current
   implementer, change pressure, measuring Outcome and constraining
   guardrails.
4. Coverage test: every capability has an implementer in the current state
   or an explicit gap; every data set has exactly one master. Gaps and
   double masters are findings.

### Phase 3 — Guardrails

Write `templates/guardrails.md`: 5–12 principles, each one sentence, each
justified by a `PUR-` or `OUT-` id. A guardrail without a justification is
removed. Guardrails are tested in Phase 4, not negotiated there.

### Phase 4 — Building-block hypothesis (H1)

1. Propose about ten building blocks without product names. Each block
   covers one or more capabilities.
2. Fill the mirror table (`templates/building-block-mirror.md`): block ×
   capabilities × guardrails (✓ / ✗ / ?) × Outcomes × change × open decision.
3. Write `<programme>-reference-architecture.txt` (`map_type: reference`):
   lanes for layers (channels → channel backend → core → shared services /
   integration), actors as Organisation/People outside lanes (left), external
   systems with `[external]` (right), `{change: keep|new|change|replace|
   remove|decide}` on every block and edge, one integration bus instead of a
   mesh. Generate, lint, preview. State in the delivery that the overlay is
   an EDGY extension.
4. Open decisions (`decide`) become ADR candidates.

### Phase 5 — Work packages

One card per block that changes (`templates/work-package.md`): scope (one
block, current → target), exactly one Outcome, options A–D with *the incumbent
continues* always as one option, dependencies on other work packages and
ADRs, deadline and decision date. Optionally render the roadmap as
`map_type: summary` or a multi-page file.

### Phase 6 — Decisions

If an ADR skill is available, call it for each open decision with the
mirror-table row and the guardrails as context, and record the resulting
ids. Otherwise use the ≤ 40-line template in edgy-framework. Rejected options
and the reason are mandatory.

### Phase 7 — Role model

Apply the role-model check (edgy-framework, Organisation intersection): for
each block, who steers, procures, defines, produces, operates and approves.
Write `<programme>-organisation-roles.txt` (`map_type: organisation`, roles
as Process, `performs` links). Generate, lint, preview. Add a load view
(team × phase, number of simultaneous responsibilities) when one team
appears under several roles; report the load, do not judge it.

### Phase 8 — Stakeholder summary

Write `<programme>-summary.txt` (`map_type: summary`): who (Organisation) /
does what (Process) / what results (Outcome), **3–4 boxes per row**, one
"used for" line. Generate, lint, preview. Write ≤ 200 words that a project
manager can read aloud in a minute. If they could not explain the picture
in 60 seconds, reduce it.

### Phase 9 — Report and delivery

1. Assemble `templates/target-state-report.md` (sections 1–8, each with its
   diagram reference and its short text).
2. Lint every `.drawio`; look at every preview; run the checklist from the
   edgy-diagram *Preview loop*.
3. Delivery (generic — this skill writes files only): one `.drawio` per
   diagram (all pages inside) plus one preview image per page, named
   `<programme>_<diagram>_v<N>.<ext>`; remove superseded versions when a new
   one is accepted; write into wikis, trackers or other external systems
   **only when the user asks**, and then place each diagram next to the
   section it belongs to (purpose map → strategy; capability map →
   capabilities; reference → building blocks; roles → governance; summary →
   front page).

## Output Template

See edgy-framework *Target-state Output* (en / fi) and
`templates/target-state-report.md`. The worked example
`examples/expected-acme-transit-target-state.md` shows the expected length
and tone for a fictional organisation.

## Quality Gate

- [ ] Every focus area is a sub-Purpose, no focus area is a Story
- [ ] Every KPI is an Outcome with `measures` to its Purpose
- [ ] Capabilities are system-independent nouns; 6–12 areas, 40–80 leaves
- [ ] Cards exist only for first-round decision units, each ≤ 1 page
- [ ] Every guardrail cites a `PUR-` or `OUT-` id
- [ ] About ten building blocks, no product names, every row of the mirror table filled
- [ ] Every work package has exactly one Outcome and the incumbent as an option
- [ ] Every open `decide` has an ADR id
- [ ] Every role has an actor and every actor a role, or the gap is a finding
- [ ] Summary ≤ 200 words, ≤ 4 boxes per row
- [ ] All diagrams: `edgy_lint.py` 0 errors, preview looked at, overlay declared as an extension
- [ ] Nothing written to external systems without an explicit request

## Anti-patterns

- DO NOT run the assessment template (12 elements, 150 lines) on internal work — use these artefacts
- DO NOT put product names into building blocks or capabilities
- DO NOT write a card per level-2 capability
- DO NOT give a work package two Outcomes, or none
- DO NOT write to a wiki or tracker before being asked
- DO NOT pad any artefact to a length

## Dependencies

- `edgy-framework` ≥ 1.4 (target-state mode)
- `edgy-diagram` ≥ 2.3 (`reference`, `summary`, `group:`, `lane:`, transition overlay)
- Optional: an ADR skill for decision records; headless Chromium for PNG previews
