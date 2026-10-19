# v2.6.0 candidate verification

**Release status:** not published; human facilitation and assistive-technology
acceptance remain pending. The owner approved the narrow scope and implementation
on 2026-10-19. This report records technical checks, not human acceptance.

## Candidate and scope

Current code candidate: `cc7253e058f870f0e7ddc0f20e51771117de9d11`.
The initial campaign below tested `86847af274442d3b1fa3aa77dc3fe699e2b0b53f`;
its evidence-only follow-up was `47cdfc1`. External-review corrections and their
actual retest revisions are recorded separately below. Evidence-only commits
do not change the tested runtime, templates, fixtures, CI or registry.

Only edgy-diagram changes to 2.10.0 for the planned v2.6.0 bundle. The existing
atlas's five effects, graph/notation contract 1 and C4 entry gate are retained.
No generic site builder, content manifest, approval system, snapshot archive or
migration ledger was implemented. The example builder assembles one fictional
fixture. Production scripts stay offline and Python-standard-library-only;
Playwright/axe are optional repository test dependencies, pinned in CI.

## Independent campaign

Four separate Codex subagent contexts reviewed and exercised the frozen candidate.
These were OpenAI/Codex runs, **not Claude or Mistral executions**. The precise
underlying model identifier is not exposed to the session; no vendor diversity
is inferred. Reviewers received the source, scope and tasks, not the author's
verdict. Roles and evidence were separate from implementation.

| Role | Initial findings | Correction and verification |
|---|---|---|
| A: architecture, contract and guidance | A-01 incorrect/stale getState identity and dropped explicit trace-occurrence route; A-02 empty inspector after targeted trace opening. | Both resolved on d65c200 by independent original probe. Graph 13, static contract 5, notation 5, C4 8, architecture 15 table-only tests and normal-motion browser self-test passed. Two structurally different, model-grounded presentation outlines were produced from the guidance. |
| B: safety and navigation | B-01 native Back skipped fallback occurrence targets; B-02 malformed LF/CR IDs could cause partial navigation (outside documented ID grammar, defence-in-depth). | Both resolved on d65c200. 24 independent assertion groups and 18 runner executions passed in actual Chromium, covering file/HTTP, punctuation, inert keys, srcdoc and rejection without mutation. |
| C: browser and accessibility | C-01 loaded trace had nested controls/label mismatches; C-02 Search listbox lacked semantics; C-03 mobile hidden rail kept focusable links; C-04 Escape left focus in hidden Search. Later C-05 empty Search results had invalid listbox child semantics. | C-01–C-04 resolved on d65c200. C-05 resolved on 86847af. Independent final empty-search scan and keyboard/reopen/selection/focus tests passed; all C findings closed. |
| D: build, package and CI | Low evidence gap: CSP report array was unused and listener attached too late. | Fixed and verified by startup-blocked-inline negative control on d65c200. Fresh generic install copied 261/261 tracked skill files exactly; installed generator/presenter/API probe and nine adapter tests passed. |

Original full checks on the first candidate passed but did not cover all failing
states. The runner was expanded to include API identity/history regressions,
loaded trace, open and empty Search, mobile initial Tab and modal focus return.
Earlier green scans were not treated as proof that untested states were correct.

## Reproduction and environments

Run the commands in [browser setup](../../testing/v2.6.0-browser.md). Relevant checks:

```bash
python3 tools/check-walkthrough.py
node tools/test-walkthrough.cjs
bash tools/check.sh
bash adapters/generic/install.sh --skill edgy-diagram --source=local --output /tmp/edgy-clean
```

Local browser evidence: Chromium 153.0.8010.0, Playwright 1.62.1,
axe-core/playwright 4.14.0, Node 24.19.0 and Python 3.12.14. Constrained local
launch used the documented single-process flags. The legacy Chrome-CLI checks
used a local adapter to that actual browser; the new repository-owned browser
runner needs no private adapter. GitHub Actions also executes the native gate
and the pinned browser runner with its installed Chrome.

Deterministic diagram checks use EDGY_TEXT_TABLE_ONLY=1, as the repository gate
does. Default optional font metrics are not substituted for CI's text tables.
A standalone installed test fixture requiring optional C4 was not used as the
package oracle: a non-C4 installed generator/presenter/API fixture was executed,
while the complete source-repository gate includes C4.

## Initial campaign verification results

| Check | Result and actual candidate |
|---|---|
| Full repository gate | **PASS** on 86847af, independent role D, exit 0, 54 seconds. |
| Repository browser runner | **18/18 PASS** on 86847af, independently repeated by roles C and D. |
| Automated accessibility | **11 scanned states, zero violations** on 86847af, including loaded trace, Search and empty Search. |
| JS errors / CSP violations / external requests | **0 / 0 / 0** in final browser runs. Separate startup CSP negative control verified collection on d65c200. |
| Fixture rebuild and size | **PASS**, repeated byte-identical rebuild on 86847af; 306095 bytes (<512 KiB), SHA-256 `2795eacdc42655cc3b6f16fd1caffa2b3beffea411abec3e3b2e4d20c500b02c`. |
| Fresh package install | **PASS** on d65c200, 261/261 tracked files identical plus installed generator/presenter/API probe. Role D inspected final four-file diff and confirmed adapter/dependency/loading/API packaging coverage remains applicable. |
| Final-change impact | 86847af changes only empty Search semantics, its regression scan, contract coverage wording and regenerated HTML. API/identity/history fixes verified by A/B on d65c200 are unchanged and covered again by the final runner. |
| GitHub CI | Final code workflow [run 70](https://github.com/Rahola/edgy-skills/actions/runs/39200258167); status recorded in PR. Previous code workflow run 69 passed the full gate and browser step. |
| Open technical defects from campaign | **None** in assigned scope after retests. This does not imply absence of all possible defects or human accessibility acceptance. |

All recorded content is fictional. Browser tests capture JS/CSP errors and
external request attempts, assert zero, inspect both file:// and local HTTP,
exercise navigation/notes/export/print and run automated WCAG-tagged scans.
Automated accessibility findings are not certification of full AA conformance.

## External-review corrections and retests (2026-10-19)

Claude's [independent report](https://github.com/Rahola/edgy-skills/pull/11#issuecomment-6262335219)
and Mistral's [independent report](https://github.com/Rahola/edgy-skills/pull/11#issuecomment-6262423942)
both tested `47cdfc1`, before the corrections below. Claude executed browser
checks; Mistral's browser checks were blocked by missing system libraries.
Mistral's blocked checks are not counted as passes. Neither report establishes
HU-01 or HU-02 acceptance.

| Finding | Assessment and change |
|---|---|
| Claude L1: repeated A → B → A routes confused native and local Back | Reproduced functional defect, medium. `972becd` assigns session-scoped browser-entry identities and explicit local predecessors instead of guessing from the last matching route string. Host object state is retained. |
| Claude L2: trace inspector empty after return | Low contract/interaction ambiguity; resolved by restoring focal inspection on trace entry and return while preserving explicit occurrence targets. |
| Mistral: API ownership and embedding unclear | Documentation gap. Added standalone `window.EDGY_PRESENT` versus same-origin `frame.contentWindow.EDGY_PRESENT`, readiness and embedding examples. The API is not restricted to an iframe. |
| Mistral: back versus navigate and build output unclear | Documented local predecessor versus explicit destination, plus build stdout versus browser JSON evidence. No general reporting engine added. |
| Unsupported ranking in a sample presentation outline | Guidance now asks authors to qualify hypotheses and avoid unsupported superlatives/rankings. No invented prioritisation metric. |
| Independent follow-up A-F01: accepted trace filter lost on return | Medium residual defect, also present before the follow-up. `cc7253e` retains validated `?state=current|target` in canonical trace routes, restoring it on local/native return and reload. |

The repository runner gained four scenarios: repeated-route identity;
branch/host-state/reload; inspector restoration; and filtered trace return and
reload. Each includes the applicable file/HTTP cases. Page-request assertions
cover requests initiated by the tested page, not browser background traffic.

| Verification | Actual result and revision |
|---|---|
| Author full repository gate | **PASS** on `cc7253e`, exit 0, 59 seconds. |
| Author browser runner | **22/22 PASS** on `cc7253e`; 11 automated accessibility states clean, zero page errors, CSP violations or external page requests. |
| Independent role A, contract/guidance/history | **PASS** on `cc7253e`: own current/target filter return/reload/native assertions, invalid-route state retention and actual file-srcdoc local return. Graph 13, contract 5, notation 5, presenter static 7, normal-motion legacy selftest and shipped 22-case runner passed. A-F01 resolved; no remaining blocker found in assigned scope. |
| Independent role B, adversarial history | Repeated on `cc7253e`: 22 own assertion groups on file/HTTP, 284 deterministic model-checked mixed navigation operations and all 22 shipped runner scenarios passed. The earlier `972becd` report explicitly excluded trace filters; eight additional focused filter groups passed on current/target, initial/alias routes, local/native return, reload, filter clearing, invalid queries and multi-ID/index routes, including actual SVG state and inspector assertions. |
| Deterministic fixture | Full gate verifies byte-identical regeneration; latest committed HTML is 308659 bytes (<512 KiB). |
| GitHub Actions | [Run 73](https://github.com/Rahola/edgy-skills/actions/runs/39221555615) **PASS** on `cc7253e`. |

These follow-up roles are separate OpenAI Codex agent contexts, not new Claude
or Mistral executions. Local environment and constrained browser launch are as
recorded above. Only Chromium was exercised; deterministic exploration does
not establish exhaustive navigation coverage, concurrent native/API race
safety or human assistive-technology acceptance. Original failures and their
subsequent retests remain distinguished rather than replacing failed evidence
with a later suite pass.

## Remaining acceptance and release actions

| Requirement | Status |
|---|---|
| Owner-approved narrow plan and implementation | Complete (2026-10-19). |
| Independent technical review, fixes and regression checks | See final results above. |
| HU-01: person leads discussion and returns from an unexpected detail question | **Not performed; release requirement remains unmet.** |
| HU-02: person tests the main route with keyboard and a screen reader | **Not performed; release requirement remains unmet.** |
| PR review, green checks on merge candidate | Draft PR; review required. |
| Merge, v2.6.0 tag and published release | Not performed before human acceptance. |

Human sign-off should identify participant/role, date, candidate and actual task
outcome, including any accepted limitation. Do not infer it from an agent's
report, automated scan, plan approval or an earlier positive reaction to HTML.
If the human review requires code changes, retest affected cases and the full
required suite on the resulting candidate before release.
