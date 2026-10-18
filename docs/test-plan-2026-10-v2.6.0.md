# v2.6.0 test plan: walkthrough and stakeholder site

**Status:** proposed; all cases below are **not run** for the future feature.
**Plan:** [implementation proposal](development-plan-2026-10-v2.6.0.md).
Tests become executable with the corresponding implementation increments.
Existing PR #11 demo checks do not count as passes for the new implementation.

## 1. Fixtures, execution and evidence

Use fictional Acme Oy only. Build three immutable snapshots from the same
canonical programme. All data, sources and decisions are invented.

- **v1:** baseline, proposed D-012, open Q-007, CAP-02 and CAP-05.
- **v2:** changed model relationship, human-authored decision confirmation,
  Q-007 resolved, changed source and dependent narrative.
- **v3:** CAP-02 merged into CAP-05 with a confirmed migration, D-012 superseded.
- Orthogonal mutations isolate narrative-only/source-only changes, split and
  deletion without successor, old ID reuse, unsafe text and conflicting imports.
- Two audience compositions and two different walkthrough compositions share
  canonical records. Finnish and English builds use separate explicit inputs.
- Use an external ADR fixture with a pinned revision, plus an unavailable source.

Each result records: case ID, candidate SHA, fixture revision, runner/model and
browser/OS/tool versions, steps/command, expected and actual result, pass/fail/
blocked/not-run, and relevant log/screenshot/artifact. An unavailable tool is
**blocked**, not pass. Browser logs include JS/CSP errors and attempted network
requests. Keep test data and reports fictional and safe for the public repo.

## 2. Automated and agent-executed cases

Owners below are independent test roles after development: **A** architecture
and content, **B** adversarial integrity, **C** browser/accessibility, **D**
reproducibility/release. Author tests may run throughout development; the formal
independent campaign begins only after G1 on a frozen SHA.

| ID | Owner / layer | Steps / mutation | Expected result |
|---|---|---|---|
| CT-01 | A / unit | Validate valid v1; separately duplicate an ID, omit a required decision source, use an unknown status. | Valid input accepted; each invalid mutation rejected with actionable record/path; no partial published output. |
| CT-02 | A / integration | Open the same claim through both audience entries, walkthrough and detail. | Canonical text, status, source and model IDs agree; different explanatory framing is allowed. |
| CT-03 | A / integration | Build two visibly different narrative compositions over the same records. | Order/layout can differ without graph duplication or a mandatory site navigation tree. |
| CT-04 | A / integration | Render a pinned external ADR and an unconfirmed local proposal; include rejected/superseded decisions. | Authority, revision and statuses visible; no second approval truth or promotion of proposal. |
| CT-05 | A / integration | Compare v1/v2 snapshots; separately render current/target architecture states. | Historical change is labelled as version change, not approved target state; existing state filters unchanged. |
| DF-01 | A / unit | Change only one graph relationship. | Delta identifies relationship and endpoints; unchanged records stay unchanged. |
| DF-02 | A / integration | Hold graph identical; change only narrative, then only evidence/source metadata. | Each relevant change appears in change summary; neither build reports "no changes". |
| DF-03 | A / integration | Change only decision status/date; resolve/remove a question. | Correct before/after entries visible with references; model change is not invented. |
| DF-04 | D / integration | Compare v1 directly with v3 after v2 exists. | Selected endpoints used; removed and changed records retained in history. |
| DF-05 | D / integration | Rebuild same inputs including publication metadata twice; then change builder version. | Byte-identical first pair; provenance change identified separately in second comparison. |
| HS-01 | B / integration | Open current D-012 link and v1-qualified D-012 after v3 publication. | Current link shows superseded status; historical link shows v1 proposal and snapshot warning. |
| HS-02 | B / integration | Merge CAP-02 into CAP-05; separately split another item into two. | Old IDs open tombstones with correct one/many successors and dates; no silent identity change. |
| HS-03 | B / negative | Remove a published ID without tombstone; reuse a v1 ID absent from v2. | Publication fails in both cases using full published ID history. |
| HS-04 | B / negative | Create migration cycle, unknown successor; then legitimate removal without successor. | Invalid mappings rejected; intentional deletion gets a truthful tombstone without invented replacement. |
| HS-05 | D / negative | Republish v1 with different content; rebuild identical v1. | Different content rejected; identical content is safe/idempotent. |
| FR-01 | A / integration | Rebuild old content with today's explicit build metadata. | Built-from changes do not advance content-as-of or last-reviewed. |
| FR-02 | A / integration | Change a model ID, a source and a dependent decision separately. | Direct and declared transitive dependent claims enter needs-review report with cause; unrelated claims unchanged. |
| FR-03 | B / negative | Publish with pending review; preview it; then apply explicit scoped waiver. | Publication blocked initially; preview labelled; waiver attributable and visible, never automatic approval. |
| FR-04 | B / unit | Include dependency cycle and missing dependency reference. | No infinite recursion; cycle handled/reported per documented policy; missing reference rejected. |
| IM-01 | B / integration | Import note saying "approved"; import same export twice. | Proposal only; stable identity prevents duplicate records; provenance retained. |
| IM-02 | B / negative | Import two conflicting exports for same meeting/item. | Conflict visible for human resolution; no silent overwrite or status escalation. |
| SE-01 | B / negative | Put scripts, HTML event handlers and javascript URLs in narrative, note and source title. | Inert escaped text or validation rejection; no execution, unsafe navigation or CSP weakening. |
| SE-02 | B / negative | Reference ../ outside content root, absolute system path and symlink escaping root; use unsafe output ID. | No read/write outside declared roots; actionable rejection. |
| BR-01 | C / browser | Present, change selection, open detail/atlas, navigate back twice. | Original narrative section and meaningful selection restored; browser history coherent. |
| BR-02 | C / browser | Capture discussion note, export, reopen resulting file as text. | Correct note/context/owner; no formal-approval implication; export stays local. |
| BR-03 | C / browser | Open index, old/current decision and model links under file:// and local HTTP. | Every internal destination works without server rewrites, fetch/CORS dependency or hidden fallback. |
| BR-04 | C / browser | Run offline with request interception and collect console/CSP errors. | Zero attempted external requests, JS errors or CSP violations; essential diagrams and content available. |
| BR-05 | C / browser | At 1440×1000 and 390×844 traverse full narrative and site. | No page-level horizontal overflow or clipped controls; diagrams may intentionally pan/zoom. |
| BR-06 | C / browser | Print all narrative sections and a representative site decision/history page. | Argument/evidence/version visible; no blank atlas region or hidden-only-current-section printout. |
| AC-01 | C / automated | Run accessibility scanner on every distinct page type and open/closed interactive states. | No unresolved detected violations against adopted AA rules; report scanner coverage/limits. |
| AC-02 | C / browser | Keyboard-only navigation; open/close dialog, escape, return focus; browser back. | All tasks reachable, visible focus and meaningful order; no traps; non-pointer alternative exists. |
| AC-03 | C / browser | Inspect semantic SVG/diagram alternatives, headings, labels, reduced-motion and 200% zoom/reflow. | Equivalent textual meaning and readable controls; motion preference respected. Human validation still required. |
| PK-01 | D / integration | Check internal links/assets across all snapshots and both compositions; simulate missing asset. | All references resolve; negative mutation fails validation. External links are not treated as offline evidence. |
| PK-02 | D / regression | Run full tools/check.sh on final candidate and existing presenter self-tests. | All required repository tests pass; no existing atlas, C4 gate, model or rendering regression. |
| PK-03 | D / CI | Change only docs/example HTML or composition inputs in a test branch. | Required composition/link/browser checks selected by CI paths; not silently skipped as in docs-only PRs. |
| PK-04 | D / release | Install skills from candidate release archive in a clean directory; build demo following docs. | All required scripts/templates present; no local paths or undeclared dependencies; outputs pass validation. |
| PK-05 | D / release | Compare skill versions, registry, changelog, package manifest, tag target and licence notices. | Coherent v2.6.0 bundle; unchanged skills are not needlessly version-bumped; EDGY attribution retained. |
| PV-01 | B / review | Inspect changed source/examples, exports, snapshots, logs and release package. | Fictional-only content; no customer data/secrets; classification label not portrayed as access enforcement. |

Tests should assert observable contracts, not mirror renderer implementation or
pixel-lock a single theme. Use focused fixtures instead of a combinatorial
cross-product of all layouts, languages, states and hosts. Add a regression case
for each corrected defect when it protects a meaningful behaviour.

## 3. Required human tasks (agents cannot sign these off)

| ID | Participant / task | Evidence and acceptance |
|---|---|---|
| HU-01 | Owner/presenter leads a 10-minute executive walkthrough; reviewer interrupts for evidence. | Reviewer can state purpose and requested decision; presenter returns to argument without reconstructing position. Record observations and explicit acceptance, not inferred approval. |
| HU-02 | Sponsor/domain reviewer visits independently, then returns after a later version. | Within five minutes identifies goal/status/next decision; finds delta and relevant domain impact without reading full atlas. Capture confusion and actual usage intent. |
| HU-03 | Human uses keyboard and a screen reader through main route, evidence, decision and history. | Record browser/assistive technology, labels/order/announcements and actual task results; resolve blockers before claiming AA acceptance. |
| HU-04 | Author updates narrative/evidence following model and source change. | Record upkeep minutes, missed dependencies and review effort. Owner explicitly judges usefulness against maintenance cost; do not invent a numeric threshold. |

For the release, use fictional content with representative reviewers. These
tasks establish acceptance for the bounded feature, not broad market demand.
Real programme adoption and its maintenance economics remain a later trial.
No fictional-data demo proves production hosting/access-control suitability.

## 4. Defects, retests and release criteria

- **Critical:** data disclosure, code execution, fabricated approval or history
  corruption. **High:** wrong canonical claim/status, broken historical identity,
  essential inaccessible path, failed offline build or main presentation flow.
  **Medium/low:** assess impact, affected users and workaround; not just appearance.
- All critical/high defects block G3. Other defects need an explicit disposition
  and owner acceptance if left open. A required case that is blocked/not run
  prevents its gate passing unless an explicit plan amendment changes scope.
- A fix gets its focused regression test plus affected independent cases on the
  new SHA. Re-run the complete required automated suite before final PR/release.
  Repeat human tasks if their path, content meaning or accessibility changed.
- Independent reports name the actual agent/model and candidate SHA. Different
  vendor testing happens only with a genuine runner; unavailable runners stay
  blocked or are reassigned transparently with approval of the test allocation.
- Final evidence index maps every required case to a result on the final SHA
  (or unchanged evidence with explicit impact assessment). No blanket "all tests
  passed" based only on the repository gate or an author's report.

## 5. Execution report template

```text
Candidate SHA / fixture revision:
Runner role / actual model / tools / environment:
Case ID:
Steps or command:
Expected:
Actual:
Status: pass | fail | blocked | not-run
Evidence:
Defect / severity / affected contract:
Retest SHA / result:
Human acceptance reference (if applicable):
```

The plan and case definitions are reviewable now. There is no completed
multi-agent campaign, stakeholder acceptance or release implied by this file.
