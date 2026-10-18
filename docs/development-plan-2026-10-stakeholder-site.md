# v2.6.0 discovery: a stakeholder site over one EDGY model

**Status:** discussion draft; **not a locked release plan**. A companion to
[`development-plan-2026-10-executive-walkthrough.md`](development-plan-2026-10-executive-walkthrough.md)
(the walkthrough note, "EW"). Findings here use the prefix **SS**.

**Date:** 2026-10-18. **Baseline:** v2.5.1 / main, plus the PR #11 demonstrator.

**Scope:** findings, candidate content responsibilities, open decisions and a
review plan. No skill, schema, presenter contract, registry or version changes.

**Dependency:** this note stays a discussion draft until the walkthrough in
PR #11 has had a human review (EW-07). The site inherits the walkthrough's
unverified assumptions, so its value depends on that hypothesis holding first.

## 1. The outcome worth exploring

The atlas helps somebody explore the model, and the walkthrough helps a
presenter lead one live discussion. Neither helps the **people around a
programme** come back to it on their own between meetings.
Examples are a sponsor, a steering group, a domain owner, a product team or a
partner.

A stakeholder site is a **persistent, asynchronous** composition of the same
model. Its reader arrives alone, on their own schedule, and asks:

1. What is this programme trying to achieve, and where are we now?
2. What is decided, what is proposed and what is still open?
3. What does it mean for *my* area?
4. What has changed since I last looked?
5. Where do I raise a question, and where do I see the answer?

The site also supports the **author's own rhythm**: update the model, rebuild,
see what changed, review it with stakeholders and carry open questions to the
next round.

This is a hypothesis drawn from the walkthrough feedback, not evidence that
stakeholders want a site. Section 9 tests it.

## 2. Three compositions over one graph

| | Atlas (v2.5.0) | Walkthrough (EW, PR #11) | Stakeholder site (this note) |
|---|---|---|---|
| Reader | an analyst exploring | a group led by a presenter | an individual, alone, over weeks |
| Time | one session | one meeting | the life of the programme |
| Unit of progress | a view | a claim or decision question | a decision, open question or change |
| State | none | in memory, exported as Markdown | versioned snapshots, authored logs |
| Delivery | one offline HTML | one offline HTML | a directory of static pages |

All three read the **same validated graph and generated views**. None
recomputes layout or keeps a parallel model. The site links into the atlas;
it does not replace it.

## 3. Findings

Every SS finding below is a **hypothesis**. None of them has been observed with
real stakeholders. SS-03 (audience entry pages) and SS-04 (decision log) in
particular are plausible but unverified. The fictional demonstrator (section 9)
tests the **mechanics**, not the **demand**. Only a real trial shows whether
people use these pages, and whether keeping them current is worth the effort
(SS-08).

| ID | Finding | Candidate direction | Why it matters |
|---|---|---|---|
| SS-01 | A meeting artefact is out of date the day after the meeting. | Rebuild the site from the model and authored files. Show *as of* date, model version and build provenance on every page. | Readers can trust what they see, or see that it is stale. |
| SS-02 | Stakeholders return to see what changed, not to re-read everything. | A "what changed since version N" page from two model snapshots, reusing `edgy_model_diff.py`, plus changes in decisions and open questions. | Returning readers find the delta in a minute. |
| SS-03 | Different groups need different entry points into the same facts. | Audience entry pages: the same claims and ids, filtered and ordered per audience, never separate content. | No drift between the "board version" and the "team version". |
| SS-04 | Decisions and open questions are scattered across meeting notes. | An authored decision log (proposed / decided / superseded) and an open-question list, each with a stable id, owner role and date. | One answer to "is this decided?". |
| SS-05 | Comments need a home, but a backend is a big commitment. | Stable deep links for every page, element, decision and question. Discussion happens in the organisation's existing tool, linking back. | Collaboration without the skills running a service. |
| SS-06 | Real programme content is confidential. | The build tool is generic and lives in this repo. Content, builds and hosting stay inside the organisation. | This public repo never holds client material. |
| SS-07 | Walkthrough notes are lost after the meeting (EW demonstrator). | Import an exported walkthrough note as *proposed* entries in the decision log or open questions. A person then confirms them in the authored files. | The meeting feeds the site, but a note never becomes a decision on its own. |
| SS-08 | **Maintenance load.** Somebody must write the narrative, keep the decision log and open questions current, and adjust them when the model changes. If that work happens outside the workflow that produces the model and views, the authored content is always older than the model. SS-01 then shows a fresh date over stale content. | Make maintenance part of the same agent workflow. A rebuild lists every authored item that refers to an id that changed in the model delta (SS-02), and flags it as *needs review*. The agent drafts the updates and a person confirms them. Measure the upkeep time in the real trial. | If upkeep costs more than the site saves, the site dies after a few versions. This is the likeliest failure mode, so it is a finding, not a footnote. |
| SS-09 | **Link stability has a price.** Stable URLs (SS-05) work only while ids stay stable. A model refactoring merges, splits or renames elements, so `model/CAP-02` breaks or points to the wrong thing. | An id migration policy: an id is never reused. A removed id keeps a **tombstone page** ("CAP-02 was merged into CAP-05 on 2026-11-03"), generated from an explicit `replaced_by` mapping or confirmed from the model delta's rename and remove pairs. The link checker fails a build that drops a published id without a tombstone. | This is the largest technical risk of the site, larger than the hosting choice: a broken or wrong link in last month's minutes undermines trust in everything else. |

## 4. Candidate content responsibilities

These are responsibilities, **not a page template or JSON schema**. The visual
composition stays free, as in EW-02.

| Responsibility | Content | Source of truth |
|---|---|---|
| Home | purpose, current decision questions, status, *as of* date | authored narrative + model |
| Audience entry | what this means for a group; links into the shared pages | authored narrative, model ids |
| Decision log | id, statement, status (proposed / decided / superseded), date, owner role, model ids affected, source | authored file (ADR-like) |
| Open questions | id, question, owner role, due, related ids, resolution link | authored file; walkthrough imports as proposals |
| What changed | model delta between snapshots; decision and question changes | `edgy_model_diff.py` + log diffs |
| Atlas | views, search, trace (existing presenter) | generator + presenter |
| Evidence | source id, provenance, date, scope (as in EW-05) | assessment sources |
| Primer | short EDGY reading guide and glossary | generic, shipped with the tool |
| Meeting archive | walkthroughs and exported notes per session | walkthrough outputs |

Every item has a **stable URL** (`decisions/D-012`, `questions/Q-007`,
`model/CAP-02`). The URLs survive rebuilds, so a link posted in a chat
or a minutes document keeps working, under the id migration policy of SS-09.
This needs the same "drill target" hook proposed in the PR #11 review: a link
can open the atlas at an element's view or trace.

**Composition freedom, restated for a site.** EW-02 and the walkthrough note's
§4 keep the visual composition free and require no single page template.
A site needs a **fixed structure**, because stable URLs and the responsibilities
above are its contract. The freedom of EW-02 therefore applies **within a
page** (its layout, order and visual form), not to the site's structure.
This is a refinement of EW-02, not a contradiction.

## 5. Build and versioning

- **Input:** the model (TXT or `edgy-model.json`), authored narrative and log
  files, sources, and optionally walkthrough exports.
- **Output:** a directory of static HTML pages with relative links and no
  network dependency. The CSP rules match the presenter's. It opens from a
  file share as well as from a web server.
- **Snapshots:** each build records the model version and keeps the previous
  snapshot's graph, so "what changed" is computed rather than written.
- **Determinism:** the same inputs give the same output, as for the generator
  and the PR #11 builder, so a rebuild without changes is a no-op diff.
- **Checks:** strict lint of all views; a link checker (no broken internal
  link, every referenced id exists, no published id dropped without a
  tombstone, per SS-09); a *needs review* list of authored items whose ids
  changed (SS-08); the presenter self-test; and an automated accessibility
  check against the requirement in §7.

## 6. Hosting and collaboration (outside the skills)

The skills produce files and stop there. Candidate places, to be verified
with a real organisation's constraints:

| Option | Fit | Risk to verify |
|---|---|---|
| Internal Git hosting with static pages | versioned, access-controlled, rebuild on commit | needs an internal pipeline |
| Intranet web server or file share | simplest | relative links and `file://` behaviour (see the PR #11 `srcdoc` note) |
| Document platforms (e.g. SharePoint, Confluence) | where stakeholders already are | many serve `.html` as a download or block scripts; may need the static PDF/print fallback or a link to a proper host |

Comments and approvals stay in existing tools (chat, minutes, tickets),
linking to stable URLs. A collaborative backend, authentication, telemetry
or a hosted service is out of scope for v2.6.0.

## 7. Privacy, confidentiality and authority

- Real content is never committed to this repository. Examples use the
  fictional Acme Oy only.
- Owner fields name a **role** by default. Personal names are an organisation's
  choice, and minimised.
- Every page shows a configurable classification banner (e.g. "internal").
- The site *displays* decisions; it never *makes* them. The status changes in
  the authored decision log, by a person, and the site shows who decided and
  when, as recorded there.
- Proposals, interpretations and observations keep their labels (EW-05) on
  every page they appear on.

**Accessibility is a requirement, not an option.** A site for real stakeholders
must meet **WCAG 2.1 AA** as a minimum. The same bar should apply to the
walkthrough (EW), because it is easier to lock now than to retrofit. An
automated check is necessary but not sufficient: the acceptance in §9 includes
a keyboard-only and a screen-reader pass by a person.

## 8. Open decisions

| ID | Decision | Options |
|---|---|---|
| SD-1 | Where the capability lives | instruction-only guidance; a builder in edgy-diagram; a new skill (e.g. `edgy-site`) that requires edgy-diagram |
| SD-2 | Delivery form | a directory of pages; one large file with internal routing (like the walkthrough) |
| SD-3 | Decision log format | Markdown ADR files; a section in the model TXT; a separate YAML file |
| SD-4 | Snapshot retention | previous build only; every tagged version |
| SD-5 | Languages | one per site; parallel language trees (fi/en) |
| SD-6 | Id migration source | an explicit `replaced_by` mapping in the model or site files; proposals from the model delta confirmed by a person; both |
| SD-7 | Relation to the walkthrough | separate tools sharing components; the walkthrough as one page type of the site |

## 9. Fictional demonstrator and review tasks

Reuse the Acme Oy facts from PR #11 and add **three model versions**
(for example: baseline, after a workshop, after a pilot decision). This shows
what changed, the decision log moving from proposed to decided, and
open questions being resolved.

| Task | Observable success | Failure signal |
|---|---|---|
| A sponsor's first visit (5 min) | states the goal, current status and next decision | has to open the atlas to understand the status |
| A return visit after version 2 | finds what changed without re-reading | the delta is buried or written by hand |
| A domain owner's view | sees only what touches their area, with the same ids | content differs from the shared pages |
| Follow a chat link to D-012 | lands on the decision; its model ids open in the atlas | broken or unstable link |
| Walkthrough note → site | the note appears as *proposed*; a person confirms it | a note shows as decided automatically |
| Stale build | the *as of* date and model version are visible | an old build looks current |
| Model refactoring (merge CAP-02 into another capability in version 3) | the old link opens a tombstone that points to the new id; the build fails without one | the link breaks or silently shows another element |
| Upkeep after a model change | the rebuild lists the authored items to review; the time to update them is recorded | authored pages silently refer to removed or renamed ids |
| Accessibility | automated WCAG 2.1 AA check passes; keyboard-only and screen-reader passes by a person | missing labels, focus traps, contrast failures |
| Offline / file share | opens without network; links work | blank pages or blocked scripts |
| Confidentiality | a fictional-only repo scan passes; a classification banner shows | real names or content in the repo |

As in EW-07, agent and browser checks are not stakeholder acceptance. One
real programme should try a fictionalised trial before any production
decision. That trial is also where the upkeep time of SS-08 is measured.

## 10. Place in the v2.6.0 discovery sequence

This note adds a composition to step 2 ("Compare compositions") of the
walkthrough note's §6, and three questions to step 1:

1. Is recurring, asynchronous stakeholder use a goal for v2.6.0, or a later
   release?
2. Which audiences come first (sponsor, steering group, domain owners, teams)?
3. Which hosting constraints are real for the first users (§6)?

The id migration policy (SS-09) and the upkeep workflow (SS-08) should be
designed before SD-1, because they decide whether the site is viable at all.
Decisions SD-1 to SD-7 belong to step 4. Nothing here changes the skills
until step 5 locks a plan.

## 11. Out of scope

- a collaborative backend, accounts, comment storage, telemetry or hosting
  operated by the skills;
- automatic decisions or status changes from meeting notes;
- generated summaries without source checks;
- dashboards with invented metrics, maturity scores or ROI;
- replacing the atlas or the walkthrough;
- real organisation content in this repository.
