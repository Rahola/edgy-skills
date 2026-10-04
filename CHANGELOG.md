# Changelog

Releases of the edgy-skills bundle are git tags. Each skill also carries its
own semantic version in its `SKILL.md` front matter and in `registry.yaml`.
Install a release with `EDGY_SKILLS_REF=<tag>` (see README → Versions).

## v2.1.0 — 2026-10

Geometry fidelity, visual lint rules and a planned ring layout for large
models. Background: `docs/development-plan-2026-10.md` (two independent field
reviews of one assessment).

| Skill | v2.0.0 | v2.1.0 |
|-------|--------|--------|
| edgy-diagram | 2.4.1 | **2.5.0** |
| edgy-assessment | 1.6.1 | **1.7.0** |
| edgy-framework | 1.4.1 | 1.4.1 |
| edgy-deep-dive | 1.1.0 | 1.1.0 |
| edgy-target-state | 1.0.1 | 1.0.1 |

No breaking changes to the input format. Generated output changed once: box
widths follow measured text, so every shipped `expected-*.drawio` was
regenerated; the two purpose maps use the new tree layout.

**edgy-diagram 2.5.0**
- `scripts/edgy_geometry.py`: one resolved geometry (absolute boxes, ports,
  routes, label positions) shared by the generator, the preview and the
  linter. Fixes: diagonal end segments on orthogonal edges with waypoints;
  `label: source|middle|target` now render at 25 / 50 / 75 %;
  `edgeStyle=none` edges run border to border.
- Lint: **W111** edge through a foreign element, **W112** label on an
  element, **W113** label on a label, **W114** label or edge end off the
  page, **W115** text below 6 pt at `--scale`; `--visual` prints them as JSON
  with coordinates.
- `scripts/edgy_text.py`: Helvetica glyph-width tables (stdlib) for box
  sizing, wrapping and W101; description rows render in normal weight.
- `--publication` (renderer, `--preview`, `--engine native`): SVG/PNG
  cropped to the content with an orientation hint. `legend: strip`: one band
  along the bottom, page as tall as the content.
- `map_type: triad` (EDGY extension): planned ring with one primary element
  per type (`{primary: true}`), straight core links, two page-edge detours,
  "Further <type>" panels for the rest (their links are reported, not
  drawn). `{label_dx, label_dy}` relationship options.
- Purpose map re-laid out as a tidy tree: parent centred, routing corridor,
  Outcomes in their own row, no branch through a child box.
- Eval set: fixtures F1 / F2 / F4 / F5 and a 19-element single-facet map;
  `tools/edgy-eval.py` reports page ratio and visual-rule counts.

**edgy-assessment 1.7.0**
- `edgy-model.schema.json`: optional `primary` on elements and capabilities.
- `edgy_model_to_txt.py --layout triad`; core links follow the primary
  element; `scripts/test_model_to_txt.py` in `check.sh`.
- Phases 3–5: when to use the triad, `--visual` in the quality gate, the
  all-facets ratio limit, recommended structural maps (purpose, capability,
  journey) from the same model, a final-PDF review at viewing scale with
  `--scale` / `--publication`; templates section 9 explains the ring.

**Repository**
- `CONTRIBUTING.md` → *Releasing (maintainers)*: tag the merge commit after
  the merge and verify every tag resolves to a different commit.

## v2.0.0 — 2026-10

Generator-first EDGY diagrams with a linter and CLI-free preview, structure
for real architecture maps, and a new target-state workflow. Background and
rationale: `docs/development-plan-2026-09.md`.

| Skill | v1.0.0 | v2.0.0 |
|-------|--------|--------|
| edgy-diagram | 1.7.0 | **2.4.1** (major) |
| edgy-framework | 1.2.0 | 1.4.1 |
| edgy-assessment | 1.5.0 | 1.6.1 |
| edgy-deep-dive | 1.0.0 | 1.1.0 |
| edgy-target-state | — | **1.0.1** (new) |

**Breaking changes (edgy-diagram 2.x)**
- The default path is the Python generator + `edgy_lint.py` + preview; direct
  XML is a fallback for small diagrams only.
- Output is an uncompressed multi-page `<mxfile>` (use `--bare` for the old
  bare `<mxGraphModel>`).
- Elements inside `group:` containers (and the automatic facet containers)
  use draw.io `parent` references with relative geometry.
- Unknown `facet` / `map_type` values stop the generator (exit 2,
  `--lenient` to override); a failed `--preview` exits 3.
- A core-link verb on a pair that is not one of the 24 core links is drawn
  as influence (dashed) and reported; inputs relying on the old behaviour
  should switch to an influence verb.

**New**
- `edgy_lint.py`, `edgy_render.py` (SVG; PNG via headless Chromium), `pages:`,
  `group:`, `lane:`, label standard with `{id:}`, relationship options
  `{from, to, via, change, label}`, transition overlay (EDGY extension),
  purpose-hierarchy / role-model / capability-area / `reference` / `summary`
  layouts, `layout_from:` ArchiMate positioning.
- edgy-framework: strategy → EDGY mapping, capability formulation, Outcome,
  role-model check, `mode: target-state`, output length by mode.
- edgy-target-state: internal target-architecture workflow (new skill).
- edgy-assessment: model JSON schema + validator, TXT inputs derived from the
  model, `mode: extract-model`; edgy-deep-dive validates its model.
- Single vocabulary source `skills/_shared/edgy-core-links.yaml`, eval set and
  `tools/edgy-eval.py`, extended `tools/check.sh`.
- Adapters accept `EDGY_SKILLS_REF` (install a tag) and `EDGY_SKILLS_REPO`.

## v1.0.0 — 2026-07

Initial public release: edgy-framework 1.2.0, edgy-diagram 1.7.0,
edgy-assessment 1.5.0, edgy-deep-dive 1.0.0, adapters for Claude Code, Cursor,
Mistral Vibe and generic agents, validation tooling and privacy guard.
Note: the v1.0.0 adapters always install from `main`; to install v1.0.0 use a
v2.0.0+ adapter with `EDGY_SKILLS_REF=v1.0.0`, or a local checkout of the tag.
