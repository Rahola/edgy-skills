# edgy-skills

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23439782.svg)](https://doi.org/10.5281/zenodo.23439782)

Agent skills for **EDGY 23 Enterprise Design** — a set of composable skills that
let an AI coding agent (Claude Code, Cursor, and generic agents) run EDGY
analyses and produce EDGY-notation diagrams.

EDGY is the open visual language for Enterprise Design by the
[Intersection Group](https://intersection.group/) (CC BY-SA 4.0). These skills
package the framework as agent instructions: reframing challenges, analysing
facet intersections, and rendering draw.io / PlantUML diagrams from natural
language.

> Skills are Markdown instruction files (`SKILL.md`) plus supporting assets,
> examples and standard-library Python scripts (generator, linter, renderer,
> presenter, model tools). The scripts run only when the agent calls them —
> no network access, no third-party packages — and `tools/` holds the
> repository's own validation tooling.

## The skills

| Skill | Category | What it does |
|-------|----------|--------------|
| [`edgy-framework`](skills/architecture/edgy-framework/) | architecture | Challenge reframing, facet intersection analysis, element identification from natural language. |
| [`edgy-diagram`](skills/documentation/edgy-diagram/) | documentation | Render EDGY diagrams as draw.io XML or PlantUML and export to PNG/SVG/PDF; architecture views (application, process, capability view, matrices) from one model, a click-through realisation trace from journey to organisation, and an offline presentation. |
| [`edgy-c4`](skills/documentation/edgy-c4/) | documentation | C4 model (Simon Brown) for one application: the L1 system context derived from the EDGY model, L2 container pages; a notation handler for `edgy-diagram` (needs it; claude-code and generic installs). |
| [`edgy-assessment`](skills/architecture/edgy-assessment/) | architecture | Orchestrator — chains `edgy-framework` + `edgy-diagram` into a full assessment with a locked PDF report layout. |
| [`edgy-deep-dive`](skills/architecture/edgy-deep-dive/) | architecture | Targeted analysis of a specific element pair / facet combination from an existing assessment model. |
| [`edgy-target-state`](skills/architecture/edgy-target-state/) | architecture | Internal target-state architecture work: purpose map, capability map and cards, guardrails, building-block hypothesis with a current → target overlay, work packages, role model, stakeholder summary. |

**How they fit together:** run `edgy-assessment` for an outside-in pass on a
company (it calls `edgy-framework` and `edgy-diagram` internally), then
`edgy-deep-dive` to explore a specific intersection. For your own
organisation's target architecture run `edgy-target-state` instead.
`edgy-framework` and `edgy-diagram` also work standalone.

## Principles

1. **EDGY 23 first.** Every map is valid EDGY: its element types, the
   facet colour as the fill, and the 24 core links. The linter enforces
   this; for example, E010 flags a core-link verb on a pair EDGY does not
   link, and W102 flags a fill outside the EDGY palette.
2. **Extensions are visible and opt-in.** Anything EDGY does not define is
   drawn only when the input asks for it, and only as a badge, stroke,
   layout or matrix cell. Examples are TIME, CRUD and the transition
   overlay. Its legend section is marked "(extension)", and the delivery
   says it is an extension.
3. **An external standard needs a register entry.** The entry in
   [`external-standards.md`](skills/documentation/edgy-diagram/references/external-standards.md)
   says what the standard answers that EDGY cannot, why it was chosen,
   what the alternatives were, and gives its source and licence.
4. **Another notation is another skill.** C4 is the planned `edgy-c4`
   skill, and ArchiMate is a one-way export. Neither is drawn with EDGY
   shapes on an EDGY page.
5. **Gaps are evidence, not guesses.** An empty part of a view is recorded
   as a model gap with an evidence status. It becomes a finding only when
   the absence is confirmed.
6. **Offline and dependency-free.** The scripts use only the Python
   standard library and never use the network. A generated presentation
   cannot send its model anywhere.
7. **No client material in the repository.** Examples are fictional, and a
   generated deliverable stays with the client
   (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## Using the skills

Each `SKILL.md` is agent-agnostic — you can always just paste its content into
your agent's system prompt. The [`adapters/`](adapters/) directory has per-agent
installers and usage guides:

| Agent | Adapter |
|-------|---------|
| Claude Code | [`adapters/claude-code/`](adapters/claude-code/) — installs to `~/.claude/skills/` + `CLAUDE.md` |
| Cursor | [`adapters/cursor/`](adapters/cursor/) — merges skills into `.cursorrules` |
| Mistral Vibe CLI | [`adapters/mistral-vibe/`](adapters/mistral-vibe/) — copy-paste + `install.sh` |
| Any / generic | [`adapters/generic/`](adapters/generic/) — download a skill to any directory |

The adapters point at `Rahola/edgy-skills` by default; set `EDGY_SKILLS_REPO`
to use a fork.

**What each adapter installs (v2.5.0).** A skill can need its whole
directory (scripts, assets, `notation.json`) and other skills
(`requires:` in its SKILL.md). The adapters install dependencies first, from
the same ref, and say so when they overwrite an older copy. A failed skill
fails the run (exit 1, named), as does an empty or unreadable skill list.

| Adapter | Installs | Skills that need their directory (`install: directory`, e.g. `edgy-c4`) |
|---------|----------|---------------------------------------------------------------------------|
| claude-code (local checkout) | the whole skill directory, dependencies first | installed |
| generic | the whole skill directory, dependencies first | installed |
| claude-code `--source=curl` | SKILL.md only | refused with a message |
| Mistral Vibe | SKILL.md only | refused; `--all` skips them and names them |
| Cursor | SKILL.md text merged into `.cursorrules` | refused; `--all` skips them and names them |

`EDGY_SKILLS_REGISTRY=<file>` points an adapter at another registry (tests).

### Versions

Releases are git tags (`v1.0.0`, `v2.0.0`, …); see [CHANGELOG.md](CHANGELOG.md).
`main` is the latest version. To install a specific release, set
`EDGY_SKILLS_REF` for any adapter:

```bash
EDGY_SKILLS_REF=v1.0.0 bash adapters/claude-code/install.sh --all   # previous generation
EDGY_SKILLS_REF=v2.0.0 bash adapters/claude-code/install.sh --all   # generator-first pipeline
EDGY_SKILLS_REF=v2.1.0 bash adapters/claude-code/install.sh --all   # + visual lint, triad layout
EDGY_SKILLS_REF=v2.2.0 bash adapters/claude-code/install.sh --all   # + semantic review, layout quality, qa.json
EDGY_SKILLS_REF=v2.3.0 bash adapters/claude-code/install.sh --all   # + official map shapes, badges, model diff, ArchiMate export
EDGY_SKILLS_REF=v2.4.0 bash adapters/claude-code/install.sh --all   # + architecture views from one model, presenter-lite
EDGY_SKILLS_REF=v2.5.0 bash adapters/claude-code/install.sh --all   # + realisation trace, edgy-c4, model format 1.10
EDGY_SKILLS_REF=v2.5.1 bash adapters/claude-code/install.sh --all   # same skills; copyright holder and CITATION.cff
```

When an adapter runs from a local clone it installs that checkout, so use
`git checkout v1.0.0` first. Pasting a SKILL.md directly? Open it from the tag
(`https://github.com/Rahola/edgy-skills/tree/v1.0.0/skills`).

**Generating and checking diagrams** — `edgy-diagram` ships a Python
generator (`edgy_generator.py`, standard library only) that turns a short TXT
model into draw.io XML, validates core-link pairs against the EDGY 23
vocabulary, a linter (`edgy_lint.py`) that must report 0 errors before a diagram is
delivered, and a CLI-free preview (`edgy_render.py`: SVG always, PNG when a
headless Chromium is found) that the agent looks at before delivering.
Multi-page inputs produce one draw.io file with several pages; `group:` and
`lane:` give containers and layered views, `{change: …}` adds a current →
target overlay, and `layout_from:` positions elements where they sit in an
existing ArchiMate view. `tools/edgy-eval.py` runs a fictional eval set
(60-leaf capability map, 19-block reference architecture) through generator
and linter. Final rendering to PNG/SVG/PDF uses the
[draw.io CLI](https://github.com/jgraph/drawio-desktop) or the plantuml-stdlib
`<edgy/edgy>` library; these are external tools and the skill degrades
gracefully to emitting source XML/PUML if they are not installed.

## Use-case examples

Once the skills are installed (or their `SKILL.md` pasted into your agent),
prompt in plain language. A few common workflows:

### 1. Assessment from a public website

Point the assessment at a company and its website — the agent gathers public
information and produces the full analysis, model and diagrams.

> *"Run an EDGY assessment of Acme Oy. Use their website https://acme.example
> as the primary source."*

Produces an analysis MD, an `edgy-model.json`, four facet TXTs and four draw.io
diagrams. Good starting point when you know the target but not the internals.

### 2. Assessment from your own / local materials

Feed the assessment your own documents — strategy decks, a product brief,
meeting notes, an intranet export — instead of (or alongside) public sources.

> *"Run an EDGY assessment of our team based on the files in `./strategy-2026/`
> and the product brief in `brief.md`. Language: English."*

The `sources` input accepts URLs **and** local paths/materials; the resulting
`edgy-model.json` becomes the context object for any follow-up deep-dive.

### 3. Reframing a specific problem

Use `edgy-framework` in `reframing` mode to broaden a single, narrow problem
into an enterprise-design view across EDGY facets — no full assessment needed.

> *"Reframe this challenge through EDGY: 'Customer churn is rising and support
> tickets keep growing.'"*

Returns a structured markdown reframing that surfaces the identity, experience
and architecture angles behind the stated symptom.

### 4. Deep-dive on a specific intersection

After an assessment, drill into a chosen pair or trio of elements through one
of four lenses (`dependency`, `alignment`, `gaps`, `opportunities`).

> *"Deep-dive the `capability` ↔ `organisation` pair in `edgy-model.json`
> through the `gaps` lens."*

Produces a focused report plus a pairwise diagram — useful for pinpointing
where the model is under-developed or where the biggest opportunities sit.

### 5. Just a diagram

Skip the analysis and render an EDGY-notation diagram straight from a
description with `edgy-diagram`.

> *"Draw an EDGY diagram of our customer-onboarding journey and export it to PNG."*

## Repository layout

```
skills/            # the 6 EDGY skills (SKILL.md + assets/examples)
skills/_shared/    # edgy-core-links.yaml — single source of the relationship vocabulary
tools/             # validator, registry updater, core-links renderer, privacy scanner, git hooks
docs/              # development plan / review notes
registry.yaml      # machine-readable index of the skills
.github/workflows/ # CI: validation + privacy guard
```

## Development plan

A review of diagrams and reports produced across earlier sessions, and the
resulting prioritised roadmap (P0–P3), lives in
[`docs/development-plan-2026-09.md`](docs/development-plan-2026-09.md); all
of it shipped in v2.0.0. The follow-up plan — geometry fidelity, visual lint
rules, publication bounds and the planned `triad` layout — is
[`docs/development-plan-2026-10.md`](docs/development-plan-2026-10.md)
(shipped in v2.1.0). The next plan — semantic review of purpose maps,
localisation of verbs and legend, layout consistency and options, task map,
native presets, QA manifest — is
[`docs/development-plan-2026-10-semantics-and-layout.md`](docs/development-plan-2026-10-semantics-and-layout.md)
(shipped in v2.2.0). The coverage review — maps and diagrams the
skills cannot produce yet (nested groups, stage and matrix layouts, product
trees, outcome webs, status overlay, wider semantic review, model diff,
ArchiMate export) — is
[`docs/development-plan-2026-10-coverage.md`](docs/development-plan-2026-10-coverage.md)
(shipped in v2.3.0). The next plan — application map, process map,
capability view (processes, applications, data, actors) and an interactive
single-page presenter for v2.4.0, then C4 diagrams per application as a
separate `edgy-c4` skill and a click-through realisation trace from
customer journey to organisation in v2.5.0 — is
[`docs/development-plan-2026-10-architecture-views.md`](docs/development-plan-2026-10-architecture-views.md)
(shipped in v2.4.0). The v2.5.0 plan — `edgy-c4`, the realisation trace
and how far the presenter goes — is
[`docs/development-plan-2026-10-v2.5.0.md`](docs/development-plan-2026-10-v2.5.0.md)
(shipped in v2.5.0; test plan
[`docs/testing/v2.5.0-agent-test-plan.md`](docs/testing/v2.5.0-agent-test-plan.md)).

A discussion draft toward **v2.6.0** explores a narrated, discussion-friendly
executive presentation over the existing atlas:
[`executive walkthrough findings`](docs/development-plan-2026-10-executive-walkthrough.md)
and a [fully fictional offline HTML demonstrator](docs/examples/executive-walkthrough/README.md).
It is a design experiment, not a locked plan or a new required presentation format.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). All PRs run
automated validation and a privacy guard. Please read the privacy convention
before adding examples.

## Licence

Copyright 2026 Roope Ahola — an independent, spare-time project, developed with
AI assistance (Claude Code). To cite it, use [CITATION.cff](CITATION.cff)
(GitHub's "Cite this repository") or the Zenodo DOI
[10.5281/zenodo.23439782](https://doi.org/10.5281/zenodo.23439782), which always resolves to the latest release.

- Original skill instructions, tooling and CI: **Apache-2.0** (see [LICENSE](LICENSE));
  a redistribution keeps [NOTICE](NOTICE) and its copyright line.
- EDGY 23 stencils, official example maps, and notation are **derived from EDGY
  by the Intersection Group** and remain under **CC BY-SA 4.0** — see [NOTICE](NOTICE)
  for exactly which files this covers and what the attribution/share-alike
  obligation means.
