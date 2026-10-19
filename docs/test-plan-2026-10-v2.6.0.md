# v2.6.0 scoped test plan

**Scope approved:** 2026-10-19. Supersedes the broad site test matrix at `1006df9`.
Tests become passes only when executed and recorded against a candidate SHA.
The HS/FR/IM site-series and content-diff workflow tests are out of this release.

## Fixtures and evidence

Use fictional Acme data and generated contract-test fixtures only. Test standalone
and same-origin srcdoc under file:// and HTTP, explicit IDs (including punctuation
and inert prototype-like keys), missing and slug-only IDs, and models with/without
trace pages. No customer content. Record case, candidate SHA, actual runner/model,
commands, expected/actual result, environment and evidence. Blocked is not pass.

| ID | Case and steps | Acceptance |
|---|---|---|
| NV-01 | Open each narrative section, enter atlas, return; reorder/insert sections. | Departure identified by section, including sources after atlas; selection and focus preserved. |
| NV-02 | Target an explicit ID via API; repeat without trace pages. | Opens its trace when available, otherwise drawn occurrence; inspector identifies exact ID without manual search. |
| NV-03 | Invalid/malformed routes, missing/slug-only IDs and model-only elements. | API returns failure; existing view retained; no invented target or silent fallback. |
| NV-04 | Enter via initial-route attribute and standalone fragment, including punctuation IDs. | Same target in srcdoc and standalone; fragment takes precedence for standalone links. |
| NV-05 | Drill several steps in srcdoc, call explicit Back; repeat standalone browser Back/Forward, duplicate A/B/A routes, branching, reload and host history state. | Local Back works without History support; native history uses entry identity rather than last matching route; inspector restored; host object state retained. |
| NV-06 | Switch target rapidly; reopen same ID; use API before frame ready. | Caller awaits load; calls settle deterministically, no stale zoom/focus or unexpected navigation. |
| CT-01 | Run existing graph/SVG/notation contract tests and new API tests. | Existing consumers unchanged; integration version and supported methods documented/tested. |
| SE-01 | Hostile strings in model/source/capability/options/journey; unsafe routes and prototype-like IDs. | Inert rendered text or explicit rejection, no execution or unsafe selector errors. |
| BR-01 | Navigation, detail/return, discussion export, cues, preserved option selection. | End-to-end narrative works; exported note is local and not formal approval. |
| BR-02 | Record JS/CSP errors/network attempts under file:// and local HTTP. | Zero errors/violations/external requests; no weakening to allow arbitrary scripts. |
| BR-03 | 1440×1000, 390×844, keyboard controls, Escape/focus return, 200% zoom, print. | No page overflow/clipping/focus trap; full narrative and diagram print fallback; semantic controls. |
| AC-01 | Automated accessibility scan of main path, dialog, loaded trace and open atlas Search; inspect findings. | Resolve detected serious/critical issues; document other findings and scanner limits. Not full WCAG certification. |
| RP-01 | Rebuild demo twice and compare bytes; verify committed HTML; measure size. | Byte-identical outputs, zero drift, fixture <= 512 KiB; budget is fixture-specific, not all EDGY deliveries. |
| RP-02 | Clean install changed skill directory and inspect/run its integration fixture. | Reference and assets shipped, no private scratch path/dependency; existing adapters remain compatible. |
| CI-01 | Inspect workflow selections; run full tools/check.sh plus reproducible browser runner. | docs/example and workflow changes trigger CI; rebuild-and-diff and browser tests execute. Missing browser fails CI visibly. |
| QA-01 | Different compositions from same skill/model; inspect meaning, evidence and IDs. | No fixed visual template; graph identity/provenance maintained; no invented metrics. |
| HU-01 | Person leads 10-minute presentation; reviewer asks an unexpected evidence question. | Reviewer can state argument/decision; presenter returns naturally. Record actual participant/date/acceptance. |
| HU-02 | Person uses keyboard and screen reader on narrative, detail and atlas route. | Record browser/assistive tech and task outcomes; fix blockers before human accessibility acceptance. |

## Independent testing and defects

After G1 use independent agents for (A) contract/architecture and guidance,
(B) adversarial safety/navigation, (C) browser/accessibility and (D) package/CI.
All use the frozen SHA and raw artefacts, not the author's verdict. Record actual
vendor/model; unavailable Claude/Mistral runners are not simulated by other agents.

Critical/high defects (execution/data leakage, wrong identity, broken main route,
misleading approval or essential inaccessible path) block release. Fix with a
meaningful regression case and retest affected scenarios on the new SHA. Run the
full required suite on the final candidate. Medium/low residual issues require
explicit disposition. Human tasks remain pending until a person completes them.

Each report records: case ID; SHA; runner/model/tools; steps; expected; actual;
pass/fail/blocked/not-run; evidence; defect/severity; retest SHA/result. Use the
same evidence index for final PR/release. No site lifecycle tests are claimed.
