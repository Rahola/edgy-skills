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
bash tools/check.sh            # validator + registry-sync + examples-refs + privacy-scan
```

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
