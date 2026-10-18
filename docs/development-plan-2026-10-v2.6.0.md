# v2.6.0 proposal: narrated walkthroughs and a persistent stakeholder site

**Status: awaiting owner review; implementation is not authorised yet.**
**Date:** 2026-10-18. **Baseline:** v2.5.1 plus PR #11 and PR #12, merged into
`docs/v2.6.0-executive-walkthrough` at `baa1034`.

This proposal consolidates [EW discovery](development-plan-2026-10-executive-walkthrough.md),
[SS discovery](development-plan-2026-10-stakeholder-site.md), the PR #12 review
and its follow-up. Discovery findings are hypotheses, not validated demand.
The owner requested this sequence: plan and test cases → accepted review
comments → development → independent agent tests → fixes and retests → PR and
release. The existing draft PR #11 carries the planning discussion; the final
implementation PR is a later deliverable.

## 1. Outcome and boundaries

Preserve the strongest observed preference: an author can naturally lead an
executive discussion, advance through meaningful interactive sections, inspect
evidence on demand and return without losing the conversation. Add an optional
place to revisit the same material between meetings.

Success has two distinct parts:

- **Mechanics:** consistent facts, reliable navigation, explicit authority,
  reproducible updates, accessible offline delivery and stable references.
- **Usefulness:** a person can follow the argument, understand the requested
  decision and use the result again. Agent checks cannot establish this alone.

One validated EDGY graph supplies diagrams and identifiers. Narrative, evidence,
decisions and questions are versioned companion content, not new EDGY elements.
The atlas remains the exploration layer. Layout stays generator-owned.
No customer data, backend, authentication service, telemetry or hosted deployment.

## 2. Recommended decisions for approval

These are **proposals**, not owner-approved decisions. Accepting the plan must
explicitly cover the choices below, or name the changes required.

| ID | Recommendation | Rationale / alternative deferred |
|---|---|---|
| P-01 / SD-1 | Add a small standard-library static composition builder alongside edgy-diagram, with agent guidance in the existing skills. | Reuses rendering and validation; do not introduce a new skill before demonstrating a separate workflow. |
| P-02 / SD-2 | Keep standalone offline walkthrough HTML; deliver the site as static `.html` pages with explicit relative links. | No server rewrite, clean-URL routing or browser fetch is required for local use. |
| P-03 / SD-3 | Use a versioned JSON companion manifest for machine-readable metadata and structured claims/logs, with local Markdown narrative and source files. | Standard-library parsing and validation. Reference existing ADRs as the authority where they already exist; do not create a competing approval log. Markdown rendering must escape HTML and support a deliberately small documented subset. |
| P-04 / SD-4 | Preserve immutable published snapshots and a content manifest for each published version; keep previous working build separately. | Readers can compare non-adjacent versions and cite historical content. Never require all historical pages to load at startup. |
| P-05 / SD-5 | One language per build, fixtures in Finnish and English. | Parallel translation trees and translation synchronisation are deferred. |
| P-06 / SD-6 | Explicit, human-confirmed migration mapping; diff-generated migration suggestions remain unconfirmed proposals. | IDs never reused; merges/splits are not inferred approvals. |
| P-07 / SD-7 | Share content identity and link helpers; keep walkthrough and site as optional compositions. | A site may link to archived standalone walkthroughs. A site must not be required to present a meeting. |
| P-08 | Keep stable addressability, not a compulsory information architecture. | Mandatory semantic responsibilities can be combined in pages or reordered; URL aliases survive. Reusable default layout is allowed, one mandatory theme/navigation tree is not. |
| P-09 | Treat narrative/site interaction as a separate composition contract. Leave the atlas's five-effect cap unchanged. | Any new atlas behaviour needs its own explicit contract decision; no quiet reinterpretation of the locked v2.5 plan. |
| P-10 | WCAG 2.1 AA minimum for both compositions, with automated and human checks. | This is the PR #12 requirement. Automated success is not a claim of full conformance. |

P-08 refines the SS note's "fixed structure" wording: stable routes do not
require the same menu, page count or storytelling structure for every audience.
C4 gating, core notation, existing graph schemas and the existing atlas contract
remain unchanged. Capability-nature changes, Experience schema expansion and
installer work are separate backlog items, not part of this release proposal.

## 3. Content and version contract to implement after approval

### 3.1 Build inputs and validation

A candidate `site.json` manifest references the model input, content records,
local source files, compositions and published snapshots. Validate it before
writing outputs. Publish its schema/version only during implementation.

Records have stable IDs, content kind, language, status, text, model references,
source references and review metadata. Exact field names are an implementation
review item, not a change to `edgy-model.json` in this plan. Reject duplicates,
unknown status values, unresolved required references, unsafe paths and invalid
migration chains. Required fields depend on kind, not on an all-purpose bag.

- Claims distinguish observation, interpretation and proposal next to the claim.
- Decisions carry authority/source, decision date and responsible role; support
  proposed, decided, superseded and rejected. Existing external ADRs are linked
  with a recorded revision and checked metadata, not silently scraped offline.
- Questions carry owner role, status and optional due date/resolution reference.
- Sources carry provenance, observation date, scope and a content revision/hash
  for local evidence. An external URL alone does not establish unchanged evidence.
- Audience compositions select/reorder canonical claims; audience-specific
  explanation can differ, but cannot silently replace the underlying fact/status.

### 3.2 Complete snapshots and change reporting

A published snapshot includes the graph, canonical narrative/claims, source
metadata, decisions, questions, migrations and a manifest of local content
hashes. Preserve enough local content to reproduce the historical presentation;
external evidence not archived is explicitly marked unavailable offline.
A release identifier is immutable: reject a second publication under the same
identifier with different content. Publication date is an explicit input.

Use `edgy_model_diff.py` only for the graph portion. Add companion-content diffs
for narrative, evidence, decisions and questions, including removal/status
changes. Report these even if the graph is byte-identical. Distinguish historical
snapshot comparison from current-state → target-state architecture comparison;
never imply that a later snapshot is an approved target state.

Determinism means identical declared inputs, including the baseline snapshot,
publication metadata and tool version, produce byte-identical outputs. Do not
inject the wall clock. Changed generator/template versions are build-provenance
changes, not architecture changes.

### 3.3 Stable links and history

Use explicit `.html` paths that work on a web host and under `file://`.
Provide both a stable current address and a version-qualified historical address.
For example `decisions/D-012.html` and `versions/v1/decisions/D-012.html`.
Current addresses show current status; historical pages visibly show their
snapshot/version and link to the current item without rewriting history.

IDs are unique within the programme and never reused. Renames retain the ID.
Removed, merged or split published IDs retain a tombstone with the explanation,
date and zero/one/many successors as appropriate. Removal need not have a
successor. Detect cycles, missing targets and duplicate/reused IDs. Link checks
cover older published versions, not just the immediately previous graph.
If no compatible atlas target exists, offer the relevant view/search with an
explicit limitation; do not fake an element drill. Decide any required atlas
hook separately under P-09 before altering the presenter contract.

### 3.4 Freshness and maintenance

Show separately: **built from**, **content as of**, and **last reviewed**.
Building today must not make old content appear reviewed today.

Track dependencies on model IDs, other claims, decisions and sources. A changed
or removed dependency creates a review item; propagate through declared
transitive dependencies with cycle protection. Do not auto-approve revisions or
cascade confirmed statuses. Retain confirmed text until explicitly edited;
show unresolved review status on affected content and in a maintenance report.
A publication gate rejects unresolved review items unless an accountable person
records an explicit, visible waiver with reason and scope. Preview builds may
show pending items. Detecting declared dependency changes cannot prove semantic
completeness; human review still checks missing dependencies and misleading text.
Measure author upkeep time in the human trial rather than inventing a saving.

### 3.5 Meeting notes and untrusted content

Walkthrough exports import as proposals only. Importing the same export twice
must not duplicate records. Conflicting exports produce a review conflict,
not last-writer-wins. Text claiming "approved" does not confer approval.
Confirmation is an authored, attributable action referencing the authority.

Render authored text, source titles and imports safely. Reject scriptable URLs,
path traversal and external active dependencies. Classification banners describe
content; access control belongs to the organisation's hosting environment.
Preserve the presenter's offline/CSP guarantees and EDGY attribution.

## 4. Implementation increments (only after approval)

| Increment | Deliverable | Exit evidence |
|---|---|---|
| I-1 Content contract | Companion schema/validator; canonical records; version manifests and fixtures. | Contract, negative validation and deterministic-input tests. |
| I-2 History and upkeep | Full-content diff, immutable snapshots, ID ledger/tombstones, review report. | Three-version cases plus non-adjacent history, source-only change and dependency tests. |
| I-3 Walkthrough | Flexible narrative composition over generated views; discussion/export; reliable return. | Existing demo behaviours retained, offline/browser/print and facilitation tests. |
| I-4 Site | Static page builder, canonical audience entries, decisions/questions, version navigation, local note import. | Links under file/HTTP, authority/import and complete change reporting tests. |
| I-5 Integration | Existing skill guidance, documentation, reproducible example, CI path coverage and release packaging. | Full repository gate and all required matrix cases. |

Prefer an additive prototype inside I-1/I-2 before changing skill instructions.
Stop and return a concrete amendment for approval if implementation requires a
new skill, graph schema, atlas effect, mandatory composition or scope expansion.
All distributed files must be included in the registry/install/release packaging
where applicable, with no environment-specific paths.

## 5. Approval and delivery gates

| Gate | Required evidence | Decision |
|---|---|---|
| G0 Plan | Owner accepts this revision, P-01–P-10, scope and test plan; comments have recorded dispositions. | Only then begin production code/skill changes. |
| G1 Development complete | I-1–I-5 complete; author tests and full repository checks pass; known limitations documented. | Freeze a candidate SHA for independent tests. |
| G2 Independent testing | Four agent roles execute assigned tests on that SHA; evidence and findings recorded. | Fix defects, test fixes and affected scenarios on a new SHA. |
| G3 Acceptance | No open critical/high defects; remaining issues explicitly accepted; human walkthrough and accessibility tasks completed or clearly block release. | Prepare final implementation PR. |
| G4 Merge and release | PR reviewed; checks green on final merge candidate; version/registry/changelog/package verified; approved release scope. | Merge and publish v2.6.0 after all gates. |

The owner's instruction authorises the later PR and release once these gates
are met; do not ask for the same action again. Required human acceptance is
never inferred from silence, an agent report, a merge of a discovery note or
an earlier positive reaction to the HTML. Record acceptance against a revision.
No test has passed merely because its case is written in the plan.

### Review comment disposition

The following dispositions are proposed for owner acceptance. The issues remain
open until implementation/tests supply evidence; listing them is not a fix.

| Review item | Proposed disposition | Plan / verification |
|---|---|---|
| PR #11 return from section 10 / hard-coded atlas index | Accept; derive destinations from section IDs and capture every departure. | I-3; BR-01, BR-07. |
| PR #11 targeted drill | Accept semantic responsibility; approve a minimal initial-route hook if existing atlas routing cannot be reused. This reuses search/trace, not a sixth atlas effect. | P-09; BR-08; hook design reviewed before implementation. |
| PR #11 srcdoc history limitation | Accept; choose/test embedding and routing under file:// before promising browser trace history. An explicit in-composition Back/breadcrumb is required; do not silently swallow a limitation. | I-3; BR-01, BR-03, BR-08. |
| PR #11 escaping | Accept for all model/source/import text, not just one dialog. | §3.5; SE-01. |
| PR #11 CI and generated HTML drift | Accept; track example inputs/build scripts in CI and rebuild-and-diff committed HTML. | I-5; PK-03, PK-06. |
| PR #11 uncommitted browser adapter / reproducibility | Accept; publish supported setup/commands or a repo-owned runner; no private scratch adapter required. | I-5; PK-04, PK-06. |
| PR #11 builder location and composition freedom | Accept; propose existing tool home, two materially different compositions and no fixed section count. | P-01, P-08; CT-03. |
| PR #12 hypotheses and upkeep cost | Accept; separate mechanics from demand and record real upkeep effort. | §1, §3.4; HU-02, HU-04. |
| PR #12 ID stability, authority and accessibility | Accept; complete published-ID history, explicit confirmation and human accessibility review. | §3; HS/IM/AC cases and HU-03. |
| Follow-up full-content history and freshness | Accept; graph-only diff and build date cannot stand for complete/current content. | §3.2–3.4; DF-02, HS-01, FR-01. |


Keep dispositions in the planning PR and reference an approved commit SHA.
For each material comment record: ID, request, accepted/changed/deferred/rejected,
rationale, resulting plan/test IDs and owner acceptance if scope changes.
Unresolved plan-blocking comments keep G0 closed. Approval of the discussion
notes does not automatically approve these proposed implementation choices.

## 6. Independent agent tests and human review

Detailed steps and expected results are in the [test plan](test-plan-2026-10-v2.6.0.md).
After G1, assign independent roles: architecture/content; adversarial integrity;
browser/accessibility; reproducibility/release. Agents receive the same candidate
SHA, fixtures, required case IDs and evidence format. They must inspect outputs,
not simply repeat the author's summary. Implementation author cannot be the sole
acceptance reviewer. Distinct agents do not imply distinct model vendors.

If Claude or another vendor's execution environment is unavailable, prepare a
review packet for that runner and mark its assigned cases unexecuted. Do not
claim that a Codex subagent is a Claude run. Record model/tool/environment actually
used. Human screen-reader and facilitation acceptance remain separate.

Release evidence records commit, test results, limitations, human sign-off,
package/install verification and any explicitly accepted residual issues.
