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

**How they fit together:** run `edgy-assessment` for a full pass (it calls
`edgy-framework` and `edgy-diagram` internally), then `edgy-deep-dive` to explore
a specific intersection. `edgy-framework` and `edgy-diagram` also work
standalone.

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

**Rendering diagrams** — `edgy-diagram` uses the [draw.io CLI](https://github.com/jgraph/drawio-desktop)
or the plantuml-stdlib `<edgy/edgy>` library. These are external tools; the skill
degrades gracefully to emitting source XML/PUML if they are not installed.

## Repository layout

```
skills/            # the 4 EDGY skills (SKILL.md + assets/examples)
tools/             # validator, registry updater, privacy scanner, git hooks
registry.yaml      # machine-readable index of the skills
.github/workflows/ # CI: validation + privacy guard
```

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
