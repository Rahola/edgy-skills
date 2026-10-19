# Discussion-led presentations from an EDGY model

Use this guidance when a user wants to present an assessment, architecture or
choice to a group. Produce a composition suited to the audience; the atlas alone
is an exploration layer. An interactive HTML deliverable is optional, not a new
required format. Reuse validated graph IDs and generator-owned diagrams.

1. Establish audience, purpose and the decision or question the meeting should
   advance. Start from the enterprise/customer concern, not the diagram inventory.
2. Build a short argument. Each meaningful section has a takeaway, supporting
   evidence and its status, and a useful question. A measured observation, an
   interpretation and a proposal must not look equally confirmed. Put scope,
   provenance and uncertainty next to the claim, not just in an appendix.
   Two illustrative cases do not establish the "largest" risk or a ranking;
   qualify such prioritisation as a hypothesis unless the evidence supports it.
3. Choose interactions only when they answer a question: comparing trade-offs,
   following a capability or inspecting evidence. Avoid decorative controls,
   invented scores/ROI and implied approvals. Missing evidence is not absence.
4. Make detail optional. Use generated views and the same explicit IDs as the
   graph; use the navigation API in `references/extension-contract.md` §7 to
   target a model element. The API lives in the generated atlas window; an
   embedding calls frame.contentWindow.EDGY_PRESENT, while a standalone atlas
   uses its own window. Read §7 for safe srcdoc/CSP assembly and back vs navigate.
   Do not make a presenter search manually after an
   "explore this capability" button. State honestly when a target is unavailable.
5. Save the narrative departure section, relevant selection and keyboard focus.
   Close detail or return from atlas to that point. Test sections on both sides
   of the atlas; never hard-code its index. Provide explicit atlas Back when
   srcdoc cannot use browser history. Keep atlas history separate from narrative.
6. Offer optional facilitator cues and pauses. A local meeting note can record
   a question, owner and next step, but is not an accepted ADR/model change.
   Explain in-memory lifetime and export locally before closing.
7. Test the main route, interruption and return, keyboard, narrow layout,
   print and offline/CSP. Use native controls, meaningful headings, visible focus
   and textual explanations for diagrams. Automated checks do not replace a
   person's screen-reader or facilitation review (WCAG 2.1 AA target).

Do not impose a theme, sidebar, section count, slide duration or page tree.
A board discussion, workshop and analyst deep-dive can use the same model in
very different compositions. Provide enough evidence to challenge the conclusion
without requiring the audience to learn EDGY first.

For HTML, escape model/source/import text at every insertion; keep authored
composition markup separate from data. Preserve offline operation and hash-pinned
CSP. The generated atlas must not upload its model. Let the host organisation
choose access control, approval process, persistent archives and publication.
These skills do not implement a general site builder or knowledge repository.

The repository's fictional Acme walkthrough (`docs/examples/executive-walkthrough/`)
is a reference composition and reproducible fixture, not a reusable site engine
or a template to copy verbatim. It is repository-only; installed agents can build
a different composition using the exported graph, SVG and API described here.
