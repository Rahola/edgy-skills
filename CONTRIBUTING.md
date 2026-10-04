# Contributing to edgy-skills

Thanks for your interest! This repo packages EDGY 23 Enterprise Design as agent
skills. Contributions — fixes, new examples, translations, new EDGY skills — are
welcome.

## 🔒 Privacy first (read this)

This is a **public** repository. The skills originate from real consulting work,
so the number one rule is: **never commit private client or engagement data.**

- **No client / project names.** Not in skills, examples, `registry.yaml`,
  commit messages, or `AGENT_LOG.md`.
- **Use fictional examples.** When you need sample data, invent a company —
  the convention in this repo is **`Acme Oy`** (and `Nordia Transit` for the
  public-transport example).
- **`AGENT_LOG.md` records technical decisions only** — see the rule box at the
  top of that file.

**Local guard (recommended for maintainers).** `tools/privacy-scan.sh` runs as
part of `tools/check.sh` and blocks a list of private terms. The list is **never**
stored in the repo — it lives in a git-ignored `.blocklist` file on your machine,
where the private context actually is:

```bash
cp .blocklist.example .blocklist   # then add your own terms (never committed)
bash tools/install-git-hooks.sh    # runs check.sh (incl. privacy-scan) pre-commit
```

The guard prints only `file:line` on a hit — never the term itself. It is a
safety net for the maintainer's own commits, not a substitute for judgement.

**Why not enforce this in CI?** External contributors don't know the private
term list, so they can't leak it; and pushing that list into a CI secret would
just copy sensitive data into the cloud. The real risk is the maintainer's own
commits, which the local hook covers. CI instead runs a **nameless** reminder
(`tools/examples-heuristic.sh`) that flags changes under `examples/` for manual
review — safe to show in public logs because it contains no names.

## Skill format

Each skill is a directory under `skills/<category>/<skill-id>/` containing a
`SKILL.md` with YAML front matter + Markdown body. Required front-matter fields:

```yaml
---
name: skill-id                 # unique, kebab-case
version: 1.0.0                 # semver
description: >                 # 1–3 sentences
  What the skill does.
category: architecture         # architecture | documentation | ...
tags: [edgy, ...]
agents: [claude-code, cursor, generic]
---
```

See the existing EDGY skills for reference, and `VALIDATING.md` for the full
field list and local validation steps.

## Before opening a PR

```bash
pip install pyyaml
bash tools/check.sh            # validator + registry-sync + examples-refs + core-links-sync
                               # + edgy-tests + edgy-lint-tests + edgy-render-tests + edgy-structure-tests
                               # + edgy-model + edgy-eval + edgy-lint + privacy-scan
```

`check.sh` also runs the EDGY parser and linter tests and lints every
`.drawio` example shipped with a skill (`examples/**`, official maps
excluded). A shipped example must pass `edgy_lint.py` with 0 errors —
regenerate it from its `.txt` input with `edgy_generator.py` rather than
editing the XML by hand.

## Recording diagram quality in AGENT_LOG.md

When a session delivers EDGY diagrams (anywhere — this repo's examples or a
private engagement), record in `AGENT_LOG.md` the **lint result before and
after any manual fix**, as aggregates only:

```
Diagrams: 4 · lint before manual fixes: 0 errors / 3 warnings (W101×3) ·
after: 0 / 0 · preview looked at: yes · manual draw.io edits: none
```

Never include element names, client names or file paths from private work.
The point is the trend: if manual edits keep appearing, the generator or the
instructions need fixing — open an issue with the anonymised pattern.

## Eval set

`python3 tools/edgy-eval.py` generates and lints the fictional inputs in
`skills/documentation/edgy-diagram/examples/eval/` (plus the larger shipped
examples) and prints a metrics table. `check.sh` runs it; any lint error
fails. When you fix a layout problem that came from the field, add an input
that reproduces it to the eval set.

## Relationship vocabulary — one source

The 24 EDGY core links, their allowed (source → target) pairs and the
influence-verb vocabulary live in **`skills/_shared/edgy-core-links.yaml`**.
The tables in the four SKILL.md files (between `<!-- edgy-links:begin -->`
and `<!-- edgy-links:end -->` markers) and the Python module
`skills/documentation/edgy-diagram/scripts/edgy_core_links.py` are generated
from it:

```bash
python3 tools/render-core-links.py          # regenerate all copies
python3 tools/render-core-links.py --check  # what check.sh / CI runs
```

Never edit the generated tables or module directly — change the YAML.

If you added or changed a skill, regenerate the registry and commit it:

```bash
python3 tools/registry-updater.py --skills-dir skills --registry registry.yaml
```

Add a short entry to `AGENT_LOG.md` describing **what** you changed and **why**
(technical decisions only — no client data).

## Automated checks (hooks)

The same `tools/check.sh` is wired into three places so validation is
consistent everywhere:

| Where | Trigger | Effect |
|-------|---------|--------|
| **Claude Code** — `.claude/settings.json` | `PostToolUse` on SKILL.md/registry edits | Runs `check.sh --quick`, feeds result back (non-blocking) |
| **Claude Code** — `.claude/settings.json` | `PreToolUse` on `git commit` | Runs `check.sh`, **blocks the commit** on failure |
| **Claude Code** — `.claude/settings.json` | `Stop` (session end) | Reminds to update `AGENT_LOG.md` if skills changed |
| **Other agents / humans** — `tools/install-git-hooks.sh` | git `pre-commit` | Runs `check.sh` before every commit |
| **CI** — `.github/workflows/validate-skills.yml` | PR / push | Runs `check.sh` + nameless privacy reminder |

The hooks run shell scripts (`tools/hooks/*.sh`), not Claude-specific logic, so
they are agent-agnostic. They need `jq` (degrade gracefully if absent). Bypass a
local hook when needed with `git commit --no-verify` or `SKIP_CHECK=1`.

## EDGY licensing

EDGY 23 is by the [Intersection Group](https://intersection.group/) under
CC BY-SA 4.0. Contributions that touch EDGY-derived assets (stencils, official
maps, notation) must preserve attribution and the share-alike obligation — see
[NOTICE](NOTICE). Original tooling/instructions are Apache-2.0.

## Pull request process

1. Fork and branch from `main`.
2. Make your change; run `bash tools/check.sh`.
3. Open a PR using the template. CI runs validation + a nameless privacy reminder.
4. A maintainer reviews and merges, verifying no private data in examples.

## Releasing (maintainers)

A release is a git tag `vMAJOR.MINOR.PATCH` on `main` plus a GitHub Release
whose notes are the matching `CHANGELOG.md` entry. The adapters install any
tag with `EDGY_SKILLS_REF=<tag>`, so a tag must point at the commit it claims
to describe.

1. Merge the PR first. Tag the **merge commit**, never the PR head and never
   a commit that is still on a branch.
2. Check that the skill versions in `SKILL.md` front matter match
   `registry.yaml` (`check.sh` → `registry-sync`) and that `CHANGELOG.md` has
   an entry for the bundle version.
3. Tag and push:

   ```bash
   git fetch origin main
   git tag -a vX.Y.Z <merge-commit> -m "edgy-skills vX.Y.Z"
   git push origin vX.Y.Z
   ```

4. Verify before publishing the release: `git ls-remote --tags origin` must
   show every tag on a **different** commit. Two tags on one commit means a
   release was created against the wrong target — fix the tag
   (`git tag -fa … && git push --force origin refs/tags/vX.Y.Z`) before
   anyone installs it.
5. Create the GitHub Release from the tag with the CHANGELOG entry as its
   notes. Mark the newest bundle as *latest*.

When the GitHub UI is used instead of the CLI, choose the target commit from
*Recent Commits*, not the branch name: a branch target resolves to whatever
the branch points at when the release is published.
