# Fictional executive walkthrough

**Status:** fictional reference composition for v2.6.0. It is not an installed
site builder or a mandatory presentation format. The fixture-specific build.py
exists only to reproduce this example; generic content workflows are out of scope.

Open [`index.html`](index.html) locally in a browser. It is one self-contained
file: no server, network, package install, CDN or external font is required.
GitHub displays HTML source, so download the file or open it from a checkout.

Acme Oy is an invented field-service company. **All observations, source
documents, options and timelines are fictional.** None is customer material.
The Finnish UI demonstrates a leader-led discussion; the language and visual
composition are examples rather than a proposed fixed standard.

## A short walkthrough

1. Start at **Mitä päätämme?** and state the question for the meeting.
2. Advance with **Seuraava** or the arrow keys; Home returns to the start.
3. Turn on **Vetäjän muistiinpanot** for optional facilitation cues.
4. Use **Pysähdy keskusteluun** to record a question, next action and owner.
5. Open a source or capability to inspect detail; closing returns to the same
   section. The journey/option selection is retained.
6. **Tutki mallia** opens the generated atlas. **Palaa päälinjaan** returns to
   the point of departure, including from the sources section. Capability detail
   opens the exact model ID. **Edellinen mallinäkymä** uses the atlas's local
   history; browser Back inside local srcdoc is not promised.
7. Record the discussion direction and next step; export the Markdown note.
8. Try a narrow screen and the print view.

Notes and selections are in memory for this opening only. Export before
closing/reloading. Nothing is sent anywhere; recording a position is not
formal approval or an accepted ADR.

## Source and rebuild

| File | Responsibility |
|---|---|
| `model.txt` | Fictional EDGY elements and relationships; one shared graph. |
| `walkthrough.template.html` | One narrative composition, its controls and local note capture. |
| `build.py` | Calls the existing generator, strict linter, renderer and presenter; embeds the results and fictional source data; pins script/style hashes in CSP. |
| `index.html` | Generated single-file review artefact. |

From the repository root:

```bash
python3 docs/examples/executive-walkthrough/build.py
```

Python standard library only. The builder uses a temporary directory for the
`.drawio`, graph, SVG previews and atlas, embeds the required content, then
removes those temporary files. Diagram layout is owned by the existing tools;
the example does not implement another layout engine or edit generated XML.
`EDGY_TEXT_TABLE_ONLY=1` makes regeneration independent of optional font metrics.
The builder runs `edgy_lint.py --warnings-as-errors` before writing the HTML.

Read the findings and open questions in
[`../../development-plan-2026-10-executive-walkthrough.md`](../../development-plan-2026-10-executive-walkthrough.md).
For review, use §7 there: ask somebody to narrate the example and return from
an unexpected detail question. Automated browser success is not evidence of
executive-session usefulness.

## Boundaries

- The production guidance/API are documented in edgy-diagram 2.10.0. Graph
  contract 1, five atlas effects and the existing C4 gate remain unchanged.
- The narrative uses the same model ids as the embedded generated atlas.
- Source popovers explicitly describe fictional evidence and its limits.
- No fabricated measured ROI, maturity ratings or approved architecture decisions.
- No C4 diagram is needed for this composition; existing C4 entry rules stand.
- Feedback should distinguish reusable behaviour from this particular layout.

## Historical validation (2026-10-18, before v2.6.0 corrections)

- `build.py`: generation and strict diagram lint passed (10 views, 0 errors / 0 warnings).
- Rebuilding produced byte-identical `index.html` in the same environment.
- `bash tools/check.sh`: all repository checks passed, including the presenter browser test.
- Chromium headless 153: narrative navigation, keyboard, presenter cues,
  source/capability disclosure, selection retention, atlas search/return,
  discussion retention and Markdown export passed.
- Desktop 1440×1000 and mobile 390×844: no horizontal page overflow; no
  JavaScript/CSP errors and no external network requests were observed.
- All 10 generated diagram previews were visually reviewed by the agent.
  Print rendering produced 12 nonempty pages.
- The packaged headless shell was controlled with Playwright. A local,
  uncommitted CLI adapter supplied DOM/screenshot output to the repository's
  unchanged Chrome-CLI checks. It did not change test assertions or results.

This is agent/browser evidence. Human facilitation, assistive-technology,
Firefox and Safari review remain open; no executive-session acceptance is claimed.

## Current reproducible checks

Run `python3 tools/check-walkthrough.py` for byte-identical regeneration and
the fixture's 512 KiB size budget. `node tools/test-walkthrough.cjs` covers the
actual browser navigation, targeting, hostile text, offline/CSP, keyboard, print
and automated accessibility checks. Setup: [browser test guide](../../testing/v2.6.0-browser.md).
These run in CI for example and presenter changes. No private adapter is needed
by the new runner. Historical evidence above is not new human acceptance.
