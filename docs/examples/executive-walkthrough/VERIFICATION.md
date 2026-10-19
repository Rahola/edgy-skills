# v2.6.0 candidate verification

**Release status:** not published; human facilitation and assistive-technology
acceptance remain pending. The owner approved the narrow scope and implementation
on 2026-10-19. This report records technical checks, not human acceptance.

## Candidate and scope

Final code candidate: `86847af274442d3b1fa3aa77dc3fe699e2b0b53f`.
The later evidence-only commit does not change skill code, templates, fixtures,
CI, registry or generated HTML. Retest results below identify their actual SHA.

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

## Final verification results

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
