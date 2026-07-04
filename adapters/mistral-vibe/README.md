# Mistral Vibe CLI — using the EDGY skills

The fastest way to use a skill in Mistral Vibe CLI is to paste the skill content
into the prompt at the start of a session. Each `SKILL.md` is written so the
agent understands it directly — no installation required.

> Replace `Rahola/edgy-skills` in the URLs below with your fork/org if different.

---

## Quickest — copy & paste

### 1. Copy a skill's content to the clipboard

```bash
# macOS
curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md | pbcopy

# Linux
curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md | xclip -selection clipboard

# Windows (PowerShell)
curl https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md | Set-Clipboard
```

### 2. Paste this prompt at the start of the session

```
Use the skill instructions below in this session. Read the "Instructions for the
agent" section carefully and follow it.

[paste the SKILL.md content you copied]
```

### 3. Give the actual task

```
Here is the input to analyse:

[paste your challenge / company description / EDGY model]
```

---

## Available skills

| Skill | Description | Copy command |
|-------|-------------|--------------|
| `edgy-framework` | Challenge reframing + facet intersection analysis | `curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md` |
| `edgy-diagram` | EDGY-notation diagrams (draw.io / PlantUML) | `curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/documentation/edgy-diagram/SKILL.md` |
| `edgy-assessment` | Full EDGY 23 assessment (chains framework + diagram) | `curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-assessment/SKILL.md` |
| `edgy-deep-dive` | Deep-dive of a specific element pair / facet | `curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-deep-dive/SKILL.md` |

All skills: [registry.yaml](../../registry.yaml)

---

## If Mistral Vibe CLI supports a `--system` flag

You can pass the skill directly from the command line without copying:

```bash
# Single skill
mistral-vibe --system "$(curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md)"

# From a downloaded file
mistral-vibe --system-file ~/.mistral-vibe/skills/edgy-framework/SKILL.md
```

---

## Scripted install — skills always available

Use the adapter's installer to download skills into `~/.mistral-vibe/skills/`:

```bash
bash adapters/mistral-vibe/install.sh --list                 # list skills
bash adapters/mistral-vibe/install.sh edgy-framework         # install one
bash adapters/mistral-vibe/install.sh edgy-assessment edgy-diagram
```

Then use the local file:

```bash
mistral-vibe --system "$(cat ~/.mistral-vibe/skills/edgy-framework/SKILL.md)"
```

---

## Chaining skills (recommended EDGY flow)

`edgy-assessment` already orchestrates `edgy-framework` + `edgy-diagram`
internally, so for a full pass you usually only need the assessment skill. To
combine skills manually in one session:

```bash
# macOS — edgy-framework + edgy-diagram in one prompt
{
  curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/architecture/edgy-framework/SKILL.md
  echo -e "\n\n---\n"
  curl -s https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/documentation/edgy-diagram/SKILL.md
} | pbcopy
```

---

## Troubleshooting

**Skill not working as expected?**
- Make sure you pasted the whole `SKILL.md`, including the YAML front-matter
  block (`---` … `---`).
- Try appending to the prompt: *"Briefly confirm you understood the instructions
  before starting."*

**`curl` command fails?**
- Open the URL in a browser and copy the content manually.
- URL format: `https://raw.githubusercontent.com/Rahola/edgy-skills/main/skills/<category>/<skill-name>/SKILL.md`

---

## Diagram rendering note

`edgy-diagram` (and `edgy-assessment`, which uses it) can export PNG/SVG/PDF via
the [draw.io CLI](https://github.com/jgraph/drawio-desktop) or plantuml-stdlib.
Without those tools installed, the skill still emits draw.io XML / PlantUML
source you can render elsewhere.
