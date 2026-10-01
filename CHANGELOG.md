# Changelog

Releases of the edgy-skills bundle are git tags. Each skill also carries its
own semantic version in its `SKILL.md` front matter and in `registry.yaml`.
Install a release with `EDGY_SKILLS_REF=<tag>` (see README → Versions).

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
