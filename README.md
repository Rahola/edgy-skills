# edgy-skills

Agent skills for **EDGY 23 Enterprise Design** — a set of composable skills that
let an AI coding agent (Claude Code, Cursor, and generic agents) run EDGY
analyses and produce EDGY-notation diagrams.

EDGY is the open visual language for Enterprise Design by the
[Intersection Group](https://intersection.group/) (CC BY-SA 4.0). These skills
package the framework as agent instructions: reframing challenges, analysing
facet intersections, and rendering draw.io / PlantUML diagrams from natural
language.

> Skills are Markdown instruction files (`SKILL.md`) plus supporting assets and
> examples. They contain no code that runs on your machine except the optional
> validation tooling in `tools/`.

## The skills

| Skill | Category | What it does |
|-------|----------|--------------|
| [`edgy-framework`](skills/architecture/edgy-framework/) | architecture | Challenge reframing, facet intersection analysis, element identification from natural language. |
| [`edgy-diagram`](skills/documentation/edgy-diagram/) | documentation | Render EDGY diagrams as draw.io XML or PlantUML and export to PNG/SVG/PDF. |
| [`edgy-assessment`](skills/architecture/edgy-assessment/) | architecture | Orchestrator — chains `edgy-framework` + `edgy-diagram` into a full assessment with a locked PDF report layout. |
| [`edgy-deep-dive`](skills/architecture/edgy-deep-dive/) | architecture | Targeted analysis of a specific element pair / facet combination from an existing assessment model. |
| [`edgy-target-state`](skills/architecture/edgy-target-state/) | architecture | Internal target-state architecture work: purpose map, capability map and cards, guardrails, building-block hypothesis with a current → target overlay, work packages, role model, stakeholder summary. |

**How they fit together:** run `edgy-assessment` for an outside-in pass on a
company (it calls `edgy-framework` and `edgy-diagram` internally), then
`edgy-deep-dive` to explore a specific intersection. For your own
organisation's target architecture run `edgy-target-state` instead.
`edgy-framework` and `edgy-diagram` also work standalone.

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

The adapters point at `Rahola/edgy-skills` by default — change the repo in the
scripts (or set the documented env var) if you use a fork.

**Generating and checking diagrams** — `edgy-diagram` ships a Python
generator (`edgy_generator.py`, standard library only) that turns a short TXT
model into draw.io XML, validates core-link pairs against the EDGY 23
vocabulary, a linter (`edgy_lint.py`) that must report 0 errors before a diagram is
delivered, and a CLI-free preview (`edgy_render.py`: SVG always, PNG when a
headless Chromium is found) that the agent looks at before delivering.
Multi-page inputs produce one draw.io file with several pages. Final
rendering to PNG/SVG/PDF uses the
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
skills/            # the 5 EDGY skills (SKILL.md + assets/examples)
skills/_shared/    # edgy-core-links.yaml — single source of the relationship vocabulary
tools/             # validator, registry updater, core-links renderer, privacy scanner, git hooks
docs/              # development plan / review notes
registry.yaml      # machine-readable index of the skills
.github/workflows/ # CI: validation + privacy guard
```

## Development plan

A review of diagrams and reports produced across earlier sessions, and the
resulting prioritised roadmap (P0–P3), lives in
[`docs/development-plan-2026-09.md`](docs/development-plan-2026-09.md).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). All PRs run
automated validation and a privacy guard. Please read the privacy convention
before adding examples.

## Licence

- Original skill instructions, tooling and CI: **Apache-2.0** (see [LICENSE](LICENSE)).
- EDGY 23 stencils, official example maps, and notation are **derived from EDGY
  by the Intersection Group** and remain under **CC BY-SA 4.0** — see [NOTICE](NOTICE)
  for exactly which files this covers and what the attribution/share-alike
  obligation means.
