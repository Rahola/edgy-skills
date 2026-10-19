# v2.6.0: discussion-led EDGY presentations and atlas integration

**Status:** scope approved by the owner on 2026-10-19; implementation authorised.
**Baseline:** v2.5.1 plus PR #11/#12 discovery. This revision replaces the broader
proposal at `1006df9`. The owner approved narrowing the scope after the Mistral
and Claude reviews. Their comments are proposals/reviews, not human test results.

## Outcome and scope

Help an agent compose a discussion-led presentation from a validated EDGY model:
a clear claim, evidence/status, question, useful detail and reliable return.
Keep the graph, diagram layout, five atlas effects and existing C4 gate intact.
Do not prescribe a theme, section count, sidebar, meeting duration or page tree.

| Decision | Approved direction |
|---|---|
| Tooling | No general composition builder or new skill. Extend the existing presenter's navigation contract and add agent guidance to edgy-diagram. |
| Public integration | Reuse extension contract 1 graph/SVG identity; add a small versioned same-origin JavaScript API and optional initial route. No network or postMessage command channel. |
| Identity | Link explicit model IDs. Preserve IDs on rename; do not promise cross-programme identity or permanent published website URLs. |
| Embedding | Support standalone and same-origin srcdoc. Provide explicit local Back in the embedding when browser History is unavailable; document the distinction. |
| Example | Keep Acme as a fictional, reproducible reference composition. Its builder assembles this one fixture, not user-authored content manifests. Maintain it under CI. |
| Quality | Safe text, CSP/offline, keyboard access, readable narrow layouts, print and a documented browser runner. WCAG 2.1 AA remains the accessibility target; automated checks do not certify it. |
| Outside this repo | No site.json, Markdown engine, decision workflow, snapshot archive, ID migration ledger, dependency-review/publication workflow or note-import pipeline. |

The stakeholder-site note remains discovery. If pursued, implement it over the
export/integration contract in an external project or existing platform. arch-ops
may own accepted knowledge/ADR lifecycles under its own decisions; it is not an
implicit destination for a new presentation platform.

## Work packages

1. **Example repairs:** remove hard-coded atlas indices, preserve every departure,
   escape data consistently, maintain focus on return, and put the generated
   example under rebuild-and-diff CI.
2. **Integration contract:** expose explicit-ID targeting, validated routes,
   navigation state and in-frame Back. Reuse existing occurrence/trace logic.
   Invalid targets leave the existing view intact. Initial routing works without
   relying on a srcdoc URL fragment. Keep CSP/network restrictions unchanged.
3. **Guidance:** explain how to build a discussion-led presentation, preserve
   provenance and return context, choose audience-specific composition and use
   the public integration seam. Link one concise reference from SKILL.md.
4. **Verification and packaging:** browser/contract regression cases, documented
   runner, size budget, clean installation and independent agent checks. Bump only
   changed skills and regenerate the registry. Prepare release notes for v2.6.0.

## Review dispositions

| Review | Disposition |
|---|---|
| PR #11 return bug, targeted drill, srcdoc history | Implement and test the existing presenter integration and corrected example. |
| PR #11 escaping, CI gap, private test adapter | Escape dynamic text; CI rebuild-and-diff; ship a reproducible optional Playwright runner. |
| Mistral scope / example builder | Bound and label builder as fixture-specific; no production engine under docs. Keep useful reproducible examples rather than an arbitrary one-demo limit. |
| Claude narrow scope | Adopt. Remove former I-2/I-4 and general content schema/workflows from this release. |
| Full-history/freshness/site concerns | Valid external-platform requirements; retained in SS discovery, not implemented in this repo. |
| Demand vs mechanics | Agent checks test mechanics. Human presentation and assistive-technology acceptance remain separate. |

## Gates and sequence

- **G0 passed:** owner approved this narrow scope and authorised implementation.
- **Early human feedback:** offer the corrected demo as soon as possible. The
  previous suggestion to block all implementation on HU-01 is superseded by the
  owner's explicit instruction to start. Do not claim HU-01 has happened.
- **G1:** implementation and author checks complete; freeze candidate commit.
- **G2:** independent agents test the same candidate (contract/architecture,
  security/navigation, browser/accessibility, packaging/reproducibility). Record
  actual models/environments; do not relabel a Codex run as Claude or Mistral.
- **G3:** fix/retest all critical/high defects; report accepted residual issues.
  A person performs HU-01 presentation and HU-02 assistive-technology review.
  Agent checks cannot supply these sign-offs. Prepare a draft implementation PR
  while human tasks remain pending; mark it ready only when acceptance is met.
- **G4:** green final checks, reviewed PR, coherent registry/changelog/packages,
  human acceptance recorded; merge and publish v2.6.0. Prior owner authorisation
  covers PR/release after these conditions; silence is not human test acceptance.

No hosting, automated decision approval or business-impact metrics are added.
See [the scoped test matrix](test-plan-2026-10-v2.6.0.md).
