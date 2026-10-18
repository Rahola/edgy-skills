# v2.6.0 discovery: an executive walkthrough, not just a diagram browser

**Status:** discussion draft and demonstrator; **not a locked release plan**.

**Date:** 2026-10-18. **Baseline:** v2.5.1 / main.

**Scope:** findings, an adaptable presentation approach, and a completely fictional offline HTML example. No production skill, model schema or presenter contract changes in this PR.

## 1. The outcome worth preserving

The strongest feedback on a recent generated presentation was that its author
could comfortably **present it to an executive team, progress through the
interactive sections while speaking, and discuss the material together**.
The benefit was the continuity of the conversation: a clear main argument,
places to pause, and detail available when somebody asks.

This is anticipated usefulness reported after reviewing an artefact. It is
**not evidence of a completed executive meeting, measured decision quality,
or a multi-user usability study**. No original organisation, analysis, source
material or business figures are reproduced here. The example is invented.

The desired experience:

1. The presenter explains *why we are discussing this* and *what needs a decision*.
2. The group follows a small number of meaningful steps.
3. A question can open evidence, a capability or the EDGY atlas.
4. The presenter returns to the same step and continues the argument.
5. The group leaves with a decision or a precise next question and owner.

The unit of progress is a **claim or decision question**, rather than a diagram
page or an animation. A useful section has a takeaway, evidence/status, and a
question for the room.

## 2. What already works in v2.5.x

Do not rebuild these capabilities or describe them as missing:

- generator-owned EDGY layouts and the native SVG preview;
- a self-contained offline presenter with CSP and no model upload;
- a card wall, pan/zoom, cross-view highlighting and element search;
- a realisation trace with drill-through, breadcrumbs, paging and history;
- explicit evidence statuses for model gaps and the C4 notation boundary;
- structural, visual and layout lint plus presenter self-tests.

The existing atlas is the **exploration layer**. The opportunity is an
optional **presentation/narrative layer** that can use it without changing
the underlying model or recomputing diagram layout.

## 3. Findings and candidate improvements

| ID | Finding | Candidate change | Why it matters |
|---|---|---|---|
| EW-01 | A diagram wall does not itself explain the argument. | Guide the agent to identify audience, purpose, main claim and decision before arranging sections. | A leader can follow the reasoning without learning the model first. |
| EW-02 | A single visual template would over-constrain different assignments. | Standardise semantic responsibilities and quality checks; allow the composition and appearance to vary. | A workshop, board discussion and analyst investigation need different structures. |
| EW-03 | Detail is useful when the discussion asks for it. | Progressive disclosure with a reliable return to the narrative position. | Exploration enriches the conversation without losing its thread. |
| EW-04 | Interactivity is useful when it answers a question. | Use a selector, comparison or drill-down only where it changes understanding. | Avoid decorative controls and false quantitative precision. |
| EW-05 | A conclusion can look equally authoritative whether sourced or proposed. | Keep evidence status, provenance and uncertainty visible next to the claim and in detail views. | The group can distinguish an observation from a recommendation. |
| EW-06 | Live facilitation has different needs from individual reading. | Optional presenter cues, discussion pauses, keyboard navigation and a visible next question. | The author can speak and listen rather than operate the interface continuously. |
| EW-07 | A promising artefact is not a validated product feature. | Test a narrated walkthrough with real reviewers before defining the production API. | Preserve what helped the discussion rather than copying a screenshot. |

### Supporting technical issues to investigate separately

- **Relationship provenance.** Preserve the source location and status of a
  relationship derived from an assessment table, not just the element's status.
  Assess how this fits extension contract 1 before changing writers or schemas.
- **Density.** A wide trace may need zoom despite clean structural lint. Make
  the opening view readable and the detail reachable; test actual viewport sizes.
- **C4 current-state vs target-state entry.** A source-backed existing-system
  context may have a different evidence need from a future design. This is a
  question for a separate decision; the current decided-building-block gate
  remains in force. Never infer unknown containers or weaken provenance.

## 4. Reusable contract, flexible presentation

These are proposed content responsibilities, **not a new JSON schema**:

| Responsibility | Example | Freedom retained |
|---|---|---|
| Audience and intent | executive decision / workshop / investigation | number and order of sections |
| Main argument | a claim and its implications | visual form and wording |
| Evidence | source id, provenance, date and scope | cards, annotations, appendix or drawer |
| Discussion | one useful question or decision | facilitation style |
| Detail | model ids, diagram pages and explanation | atlas, modal, panel or embedded view |
| Return | preserve section and relevant selection | routing/UI implementation |
| Outcome | decision, open item, owner, next step | export format and meeting process |

A production design could make this an agent-authored composition over a
validated graph and generated views. It should not require one dashboard,
sidebar, colour theme, slide count, meeting duration or company type.

Possible compositions include a short executive narrative, an open workshop,
a diagram atlas and a readable long-form report. The demonstrator chooses
one composition to make the trade-offs reviewable.

## 5. Fictional demonstrator

Open [`examples/executive-walkthrough/index.html`](examples/executive-walkthrough/index.html)
locally in a browser. The README in that directory explains rebuilding.

Acme Oy is an **invented field-service company**. Its observations, sources,
figures, targets, participants and options are fictional. The example asks
whether to pilot a shared service-handover practice. It demonstrates:

- a narrated route from purpose and an observed problem to options and a decision;
- explicit fictional observations, interpretation and proposal labels;
- optional facilitation notes and a discussion pause;
- clickable capability details and evidence without leaving the section;
- a real EDGY atlas generated from the fictional TXT, including trace links;
- a meeting note/decision capture area that exports Markdown locally;
- keyboard navigation, narrow-screen layout and print fallback.

The example is not a screenshot clone, an installed skill, a release, a new
EDGY notation or a change to the five-effect production presenter. Model
links belong to EDGY; narrative sections and meeting notes do not become
enterprise model elements. A recorded meeting position is not an approved
architecture decision or a persisted model change.

## 6. Proposed discovery sequence toward v2.6.0

1. **Owner review of this evidence.** Is narrated, discussion-friendly use the
   intended next outcome? Which audiences and languages matter first?
2. **Compare compositions.** Review this executive walkthrough alongside the
   existing atlas; later try a workshop or report composition with the same
   fictional facts. Identify shared responsibilities, not shared pixels.
3. **Test the content workflow with agents.** Ask different agents to prepare
   a discussion from the same material. Compare traceability, argument and
   facilitation, not byte-identical HTML.
4. **Decide architecture and scope.** Instruction-only guidance, a composition
   tool over the existing presenter, or a separate presentation skill are
   alternatives. Decide explicitly whether to revise the five-effect cap from
   the locked v2.5.0 plan. This demonstrator does not revise that decision.
5. **Lock acceptance and implementation plan.** Only then change production
   skill versions, schema/contracts, registry, CHANGELOG or release tags.

No calendar estimate or implementation commitment is made by this PR. Existing
v2.6.0 candidates in the v2.5.0 plan remain separate backlog items.

## 7. Review tasks and candidate acceptance

| Task | Observable success | Failure signal |
|---|---|---|
| Give a 10-minute executive introduction | reviewer can state the main argument and requested decision | presenter has to explain the UI or read inventory lists |
| Pause for a challenge to a claim | evidence and its status can be opened locally | source context is missing or a proposal looks confirmed |
| Follow a capability into a diagram | model ids agree across narrative, detail and atlas | a parallel model or contradictory labels appear |
| Return from detail | same narrative section and selection remain | the presenter must reconstruct the discussion position |
| Discuss alternatives | trade-offs and uncertainty are clear | invented scores/ROI imply measured certainty |
| Capture a next step | note, responsible person and next step can be exported | a local note is portrayed as formal approval |
| Use keyboard and narrow screen | controls reachable, main path readable, no horizontal overflow | focus trap or clipped content |
| Open offline | no external requests; essential content available | CDN, font, telemetry or API dependency |
| Print | main argument is visible, controls/notes do not obscure it | only the active section prints or an iframe is blank without fallback |

### Test scope for this PR

The existing repository gate still applies: `bash tools/check.sh`.
The example's generated diagrams must pass strict lint and be visually reviewed.
Browser checks cover navigation, disclosure/return, discussion capture/export,
atlas interactions, keyboard use, narrow screens, offline requests and print.
Browser outcomes and human facilitation review must be reported separately.
An agent/browser check is not an executive-session acceptance.

## 8. Explicitly out of scope

- replacing the atlas or copying its graph/search/layout implementation;
- imposing one mandatory presentation template;
- automatic executive summaries without source checks;
- fabricated metrics, confidence scores, controls or system components;
- collaborative backends, telemetry, hosting and external publication;
- installing/changing skills, changing release versions, or shipping v2.6.0;
- treating this single artefact review as validated usability research.
