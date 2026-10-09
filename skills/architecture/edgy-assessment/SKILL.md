---
name: edgy-assessment
version: "1.8.0"
description: >
  Comprehensive EDGY 23 Enterprise Design assessment: analysis, diagrams, and recommendations.
  Orchestrating skill that chains edgy-framework and edgy-diagram skills into a unified workflow.
  Locks PDF report layout via shared preamble (assets/pdf-preamble.md) while keeping analysis
  content adaptive per customer.
category: architecture
tags: [edgy, enterprise-design, architecture, analysis, assessment, diagram, fi, en, fr, de]
languages: [fi, en, fr, de]
agents:
  - claude-code
  - cursor
  - vibe
  - generic
inputs:
  - name: mode
    type: enum
    values: [assess, extract-model]
    default: assess
    description: >
      assess = full outside-in assessment (Phases 1–5). extract-model = build
      edgy-model.json from an EXISTING analysis markdown and facet TXT files
      (older deliveries without a model), so that edgy-deep-dive can run on them.
  - name: target
    type: text
    description: Company or organisation to assess (name and brief description)
  - name: sources
    type: text
    required: false
    description: Information sources (URLs, documents, materials). If not provided, use public sources.
  - name: language
    type: enum
    values: [fi, en, fr, de]
    default: fi
outputs:
  - type: directory
    description: >
      Directory containing: 1 analysis MD, 1 edgy-model JSON, 4 facet TXTs, 4 drawio diagrams.
      The edgy-model.json is the context object for edgy-deep-dive follow-up analyses.
---

# EDGY 23 Enterprise Design Assessment

## Purpose

This skill produces a comprehensive EDGY 23 assessment of a company or organisation. It combines analysis and visualisation into a unified workflow.

Use this skill when:
- You want to produce a full EDGY 23 assessment of a company
- You need both a written analysis and visual diagrams
- You want to identify coherence gaps and areas for improvement

**This skill uses internally:**
- `edgy-framework` — for producing the analysis
- `edgy-diagram` — for generating diagrams

**IMPORTANT:** Produce all output in the language specified by the `language` parameter (default: fi). Select the appropriate analysis template by language.

## Agent Instructions — Step-by-Step Workflow

### CRITICAL: Read these instructions completely before starting

This assessment produces **9 files**. Every phase is mandatory. DO NOT proceed to the next phase before the previous one is complete and meets quality requirements.

---

### Mode `extract-model` — a model for an existing delivery

Older deliveries have an analysis markdown and four TXT files but no
`edgy-model.json`, so `edgy-deep-dive` cannot run on them. In this mode skip
Phases 1 and 3–5 and:

1. Read `<company>-edgy-analysis.md` and the four `<company>-*.txt` files.
2. Fill `edgy-model.json` from them: every element from the TXT files
   (name = part before ` - `, description = the rest, tags from `[…]`),
   `nature`/`level` for capabilities from the analysis table, active
   `core_links` from the TXT relationships (only pairs in the 24-link table),
   `coherence` from section 5 (Strong/Good/Weak + contradictions + gaps),
   `suggested_deep_dives` from section 10 if present — otherwise derive at
   least three from sections 5 and 7 and mark `"source_section"` accordingly.
3. Validate: `python3 tools/validate-edgy-model.py <company>-edgy-model.json`.
4. Regenerate the TXT files from the model (`edgy_model_to_txt.py`) and diff
   them against the originals; differences are findings about the old
   delivery, not errors to hide.
5. Deliver the model plus a short note listing what had to be inferred.

### Phase 1: Data Collection

1. Gather information about the target company from available sources (websites, public materials, user-provided documents)
2. Identify the following:
   - Company basics (name, size, founding year, industry)
   - Purpose and values
   - Services/products
   - Customer segments
   - Technologies and resources
   - Organisational structure
   - Competitive situation and differentiators

**Minimum requirement:** You must have sufficient information to fill at least 12 EDGY elements (Purpose, Story, Content, Capability, Asset, Process, Task, Channel, Journey, Organisation, Product, Brand).

---

### Phase 2: EDGY Analysis (Markdown)

Select the analysis template by `language` parameter:
- **fi**: `templates/analysis-template.md`
- **en**: `templates/analysis-template-en.md`
- **fr**: `templates/analysis-template-fr.md`
- **de**: `templates/analysis-template-de.md`

Produce the written analysis using the selected template.

**Outputs:** `<company>-edgy-analysis.md` and `<company>-edgy-model.json`

#### Phase 2a — PDF preamble injection (MANDATORY)

Every EDGY analysis MUST start with the canonical PDF preamble so that
the report always renders with the same visual layout (frontmatter, CSS,
legend, meta-table). Only the analysis content adapts per customer; the
visual scaffolding is locked.

1. Open `assets/pdf-preamble.md` and copy its entire contents to the
   very top of `<company>-edgy-analysis.md` (before section 1).
2. Replace **every** `{{...}}` placeholder with a concrete value. The
   language-specific defaults are listed in the comment block at the
   top of the selected template — use those verbatim unless the user
   has overridden them.
3. **Do NOT modify** the `<style>` block, the `pdf_options:` YAML, or
   the `.meta-table`, `.legend`, badge-shape and `.edgy-badge`
   structures. These are the locked layout — touching them produces
   inconsistent reports.
4. The method label must be exactly **"EDGY 23 Enterprise Design"**
   (in the analysis language). Do NOT write "Enterprise Design in a
   Box" — that framework does not exist; it is an erroneous phrasing
   that was accidentally copied into earlier deliveries.

Quality gate before continuing — all greps must succeed against the
analysis markdown:

```bash
F="<company>-edgy-analysis.md"
head -1 "$F" | grep -q "^---"       # frontmatter must be the very first line
grep -q "^pdf_options:"      "$F"
grep -q "<style>"            "$F"
grep -q "\.edgy-badge"       "$F"
grep -q 'class="legend"'     "$F"
grep -q 'class="meta-table"' "$F"
! grep -q "{{"               "$F"   # no leftover placeholders
grep -Eq "^## (10\. )?(Ehdotetut jatkoanalyysit|Suggested deep-dive|Analyses approfondies|Vorgeschlagene Vertiefungs)" "$F"   # section 10 present
```

The `head -1` check is critical: gray-matter (the parser md-to-pdf uses)
only recognises YAML frontmatter when `---` is the **very first line** of
the file. A preceding HTML comment or blank line silently breaks
`pdf_options:`, dropping the footer and margins without any error.

If any check fails, return to step 1.

#### edgy-model.json — Machine-readable EDGY model

After writing the analysis markdown, serialise the assessed EDGY model as JSON.
This file is the context object for `edgy-deep-dive` follow-up analyses.

```json
{
  "company": "Company Name",
  "assessed_at": "2026-04-29T10:00:00",
  "language": "fi",
  "elements": {
    "purpose":      { "name": "...", "description": "...", "tags": [] },
    "story":        { "name": "...", "description": "...", "tags": [] },
    "content":      { "name": "...", "description": "...", "tags": [] },
    "capability":   [{ "name": "...", "description": "...", "nature": "Core|Enabling|Management", "level": "Strategic|Operational|Foundational" }],
    "asset":        [{ "name": "...", "description": "..." }],
    "process":      [{ "name": "...", "description": "..." }],
    "task":         [{ "name": "...", "description": "..." }],
    "channel":      [{ "name": "...", "description": "..." }],
    "journey":      { "name": "...", "description": "...", "stages": [] },
    "organisation": { "name": "...", "description": "..." },
    "product":      [{ "name": "...", "description": "..." }],
    "brand":        { "name": "...", "description": "..." }
  },
  "core_links": [
    { "source": "organisation", "target": "capability", "verb_fi": "omistaa", "verb_en": "has" }
  ],
  "coherence": {
    "organisation": { "alignment": "Weak|Good|Strong", "contradictions": [], "gaps": [] },
    "product":      { "alignment": "Weak|Good|Strong", "contradictions": [], "gaps": [] },
    "brand":        { "alignment": "Weak|Good|Strong", "contradictions": [], "gaps": [] }
  },
  "suggested_deep_dives": [
    {
      "pair": ["capability", "organisation"],
      "lens": "dependency",
      "rationale": "...",
      "priority": "High|Medium|Low",
      "source_section": 5
    }
  ]
}
```

**Validate the model** before continuing — the schema lives in
`assets/edgy-model.schema.json`, the validator needs only the standard library:

```bash
python3 tools/validate-edgy-model.py <company>-edgy-model.json     # must print "valid"
```

Rules:
- `elements` must contain all 12 EDGY elements (Purpose, Story, Content, Capability, Asset, Process, Task, Channel, Journey, Organisation, Product, Brand)
- `core_links` lists only links that are *active* in this company (not all 24 theoretical links)
- `coherence` mirrors the intersection analysis from section 5
- `suggested_deep_dives` mirrors section 10 of the analysis; `source_section` points to which analysis section grounds the rationale

#### Official 24 EDGY Core Links — Reference Table

**CRITICAL:** `core_links` MUST only contain pairs from this table. Every `verb_en` and `verb_fi` must match exactly. Do NOT invent pairs (e.g. `organisation → asset`, `asset → channel` are not core links). Do NOT use wrong verbs (e.g. `"utilises"` for `process → capability` — correct is `"realises"`). `"ilmentää"/"embodies"` belongs to `product → brand`, NOT `brand → content`.

<!-- edgy-links:begin format=assessment -->
| Source | Target | verb_en | verb_fi |
| -------- | -------- | --------- | --------- |
| story | purpose | contextualises | kontekstualisoi |
| content | purpose | expresses | ilmaisee |
| content | story | conveys | välittää |
| brand | story | evokes | herättää |
| brand | purpose | represents | edustaa |
| capability | asset | requires | vaatii |
| process | capability | realises | toteuttaa |
| process | asset | requires | vaatii |
| product | capability | requires | vaatii |
| process | product | creates | luo |
| task | journey | is part of | on osa |
| task | channel | uses | käyttää |
| journey | channel | traverses | kulkee |
| brand | task | supports | tukee |
| brand | journey | appears in | näkyy |
| organisation | purpose | pursues | tavoittelee |
| organisation | story | authors | kirjoittaa |
| organisation | capability | has | omistaa |
| organisation | process | performs | suorittaa |
| product | task | serves | palvelee |
| product | journey | features in | esiintyy |
| organisation | brand | builds | rakentaa |
| organisation | product | makes | valmistaa |
| product | brand | embodies | ilmentää |
<!-- edgy-links:end -->

#### Mandatory sections (all 10 must be filled):

1. **Executive summary** — min 3 sentences, includes company basics and key analysis findings
2. **Identity facet** — Purpose, Story, Content — each at least 2 sentences + analysis
3. **Architecture facet** — Capability table (min 3 capabilities with nature/level classification), Asset (min 2), Process (min 2)
4. **Experience facet** — Task (min 3 tasks), Channel (table min 2 channels), Journey (visualisation)
5. **Intersection elements** — Organisation, Product, Brand — each with coherence assessment
6. **Strengths** — min 3 numbered, justified
7. **Development areas and gaps** — min 3 subsections, analytical
8. **Recommendations** — table: #, Recommendation, EDGY element, Priority (High/Medium/Low)
9. **Diagrams** — file listing as table
10. **Suggested deep-dive analyses** — min 3 follow-up analyses with element pair, rationale, priority

#### Section 10 — Suggested deep-dive analyses

After completing sections 1–9, add a final section:

```markdown
## Ehdotetut jatkoanalyysit

Nämä jatkoanalyysit on priorisoitu löydettyjen kehitysalueiden ja
koherenssiarvioiden perusteella. Käytä `edgy-deep-dive`-skilliä.

| # | Elementtipari | Linssi | Perustelu | Prioriteetti |
|---|---------------|--------|-----------|--------------|
| 1 | capability × organisation | dependency | Coherence Weak — org-rakenne ei tue kyvykkyyksiä | High |
| 2 | product × task | gaps | Product-task-linkitys epäselvä, 2 tehtävää ilman tuotetta | Medium |
| 3 | purpose × brand | alignment | Brändiviestintä ei vastaa tarkoitusta | Medium |
```

Rules:
- Every row must be grounded in specific finding from sections 1–9 (cite section number)
- Pair must use official EDGY element names: purpose, story, content, capability, asset, process, task, channel, journey, organisation, product, brand
- Lens must be one of: dependency, alignment, gaps, opportunities, all
- At least one row must have priority High

#### Quality Gate — Check before proceeding:
- [ ] Analysis is at least 150 lines
- [ ] All 10 sections are filled
- [ ] Capability table has nature/level classification
- [ ] Intersection elements have coherence check (Strong/Good/Weak + justification)
- [ ] Recommendations table has priority levels
- [ ] Suggested deep-dives table has min 3 rows with element pairs and rationale
- [ ] Analysis is company-specific, NOT generic

#### Anti-patterns — DO NOT do this:
- DO NOT write one-line descriptions for elements (e.g. "Purpose: To provide services")
- DO NOT skip coherence checks on intersection elements
- DO NOT give generic recommendations that fit any company
- DO NOT leave tables empty or single-row
- DO NOT write under 150 lines — that means the analysis is too shallow (this rule is for the full assessment only; reframings, summaries and target-state artefacts follow the length table in edgy-framework, and are never padded to a line count)

---

### Phase 3: Facet TXT Files

**Generate the four TXT files from the model — do not write them by hand:**

```bash
python3 skills/architecture/edgy-assessment/scripts/edgy_model_to_txt.py <company>-edgy-model.json --prefix <company>
# when any facet has more than ~8 elements, or the all-facets map is unreadable:
python3 skills/architecture/edgy-assessment/scripts/edgy_model_to_txt.py <company>-edgy-model.json --prefix <company> --layout triad
```

This derives elements (`"Name - Description" [tags] {id: …}`) and the active
core links from `edgy-model.json`, so the diagrams can never disagree with
the analysis (an earlier review found reports with five capabilities and
diagrams with four). Edit the model, regenerate; never patch a TXT. The
format below documents what the script produces, and is the fallback when
Python is unavailable.

**Layout block.** An optional `layout` object in the model (`legend`,
`card_width`, `equal_cards`, `group_columns`, `cards_per_row`,
`equal_group_width`, `align_groups`, `title`, `footnote`) is written as
document keys into every TXT, so the four files share one legend placement,
card sizing and grid — `edgy_lint.py --series` (Phase 4) then reports
nothing. Set `language` in the model: the verbs and the legend render in
that language (W116 otherwise).

**Primary element.** A core link between two element *types* is drawn once,
between the primary element of each type: the one with `"primary": true` in
the model, otherwise the first of its type. Set the flag in the model when
the first element is not the one the story is about. `--layout triad` writes
`map_type: triad` into every TXT: the planned ring (edgy-diagram, EDGY
extension) with one primary per type and "Further <type>" panels for the
rest; links into a panel are reported on stderr, never drawn silently, and
the report's tables carry them.

Produce 4 text files in edgy-diagram skill input format:

1. **`<company>-identity.txt`** — Identity facet elements and relationships
2. **`<company>-architecture.txt`** — Architecture facet elements and relationships
3. **`<company>-experience.txt`** — Experience facet elements and relationships
4. **`<company>-all-facets.txt`** — All elements and relationships

#### TXT file format:

Use the core link verb matching the `language` parameter (see edgy-framework core links table).

```
facet: identity

elements:
  - purpose: "Element name - Detailed description" [tags]
  - story: "Element name - Detailed description" [tags]
  - content: "Element name - Detailed description" [tags]
  - brand: "Brand name - Description" [tags]
  - organisation: "Organisation name - Description" [tags]

relationships:
  - "story" -> "purpose": "contextualises"
  - "content" -> "purpose": "expresses"
  - "content" -> "story": "conveys"
  - "brand" -> "story": "evokes"
  - "brand" -> "purpose": "represents"
  - "organisation" -> "purpose": "pursues"
  - "organisation" -> "story": "authors"
  - "organisation" -> "brand": "builds"
```

**Minimum requirement per file:**
- Identity: min 3 core elements + 2 intersection elements + 5 relationships
- Architecture: min 7 elements (3 capability + 2 asset + 2 process) + 2 intersection elements + 5 relationships
- Experience: min 6 elements (3 task + 2 channel + 1 journey) + 2 intersection elements + 5 relationships
- All-facets: all facet elements combined + min 15 relationships

---

### Phase 4: Drawio Diagrams (4 pcs)

Generate a drawio diagram for each TXT file **with the edgy-diagram generator** and lint the result:

```bash
G=skills/documentation/edgy-diagram/scripts
python3 $G/edgy_generator.py <company>-identity.txt --output <company>-identity.drawio --preview --preset publication
python3 $G/edgy_lint.py <company>-identity.drawio      # 0 errors required
# --preview wrote <company>-identity.svg (+ .png when Chromium is available) and <company>-identity.qa.json:
# open the image and check the preview checklist (edgy-diagram SKILL.md, "Preview loop") before moving on
# series check across the four files of this delivery (legend placement, margins, card widths, fonts):
python3 $G/edgy_lint.py --series <company>-identity.drawio <company>-architecture.drawio <company>-experience.drawio <company>-all-facets.drawio
```

`--preset publication` (native preset: 24 px margin, strip legend, W115 at a
160 mm column, `title:` / `footnote:` bands from the model's layout block) is
the image for the report; `--preset presentation` for slides. The
`qa.json` written next to each `.drawio` carries the counts, the lint, the
visual / layout / language checks and the preview size; its
`visual_approval` and `semantic_approval` stay `null` until a person sets
them in Phase 5 (the semantic one after Phase 4b).

Read every generator warning: a core-link verb on a wrong pair or a verb
outside the vocabulary means the TXT file (and usually the analysis) is
wrong — fix it there. Write drawio XML by hand only when Python cannot be
executed, and lint the file as soon as it can. The XML specification below is
the reference for that fallback and for reviewing generated output.

**Outputs:**
1. `<company>-identity.drawio`
2. `<company>-architecture.drawio`
3. `<company>-experience.drawio`
4. `<company>-all-facets.drawio`

#### Diagram quality gate

The generator produces valid XML, shapes, palette, legend and layout; the
specification (XML structure, shapes, colours, legend) lives in the
edgy-diagram skill (`references/xml-reference.md`) and is **not repeated
here**. Before moving on, every one of the four files must pass:

- `edgy_lint.py` — 0 errors (structure, layout, notation, semantics)
- `edgy_lint.py --visual` reports nothing: no edge passes through a box, no
  edge label lies on a box or another label (W111–W114 = 0). If it does,
  switch the TXT files to `--layout triad` or fix the model; never patch
  the XML
- preview looked at (`--preview` / `edgy_render.py`) and the edgy-diagram
  *Preview loop* checklist passed: every edge visibly starts and ends,
  legend clear of content, **`all-facets` page height ≤ 1.2 × width**,
  single-facet maps not taller than wide before any "Further" panels,
  facet containers visually separated (Identity above or left of
  Architecture and Experience), intersection elements between the facets
  they bridge
- relationships use only the active core links from the model (a core-link
  verb on a wrong pair is a model error — fix the model, regenerate)
- `edgy_lint.py --series` over the four files reports no W121: one legend
  placement, one content margin, one card width per type, one font size
  across the delivery (set the model's `layout` block, never patch a file)

#### Structural maps (recommended, optional)

The four relationship views are the overview. When the assessment answers
a question they cannot show, add a structural map **from the same model and
with the same ids** (one disconnected second model is worse than none):

| Map | Question | How |
|-----|----------|-----|
| Purpose map | How do strategy and focus areas hang together? | `map_type: purpose`; mission / vision as top purposes, focus areas as sub-purposes (`contains`), KPIs as Outcomes (`measures`) — see edgy-framework *Strategy → EDGY* |
| Capability map | What does the enterprise need to be able to do? | `map_type: capability`, one `group:` per analytical domain. State in the report that the grouping is analytical, not an organisation chart or an all-to-all dependency claim |
| Journey map | Where does the experience break between stages? | `map_type: journey` for the lifecycle stages plus a hand-off / failure table in the report — a stage chain alone carries little analytical depth |

Add a map only when it answers a useful question for this company; do not
generate every map for every scope.

#### Phase 4b — Semantic review of the purpose map (MANDATORY when a purpose map is delivered)

A purpose map that lints clean can still be wrong in meaning (actions as
Purposes, proposed metrics shown as confirmed, influences drawn as
`contains`). After the purpose map TXT is written (structural maps above)
and before its diagram is generated:

1. Tag every element of the purpose map with its provenance —
   `[confirmed]` (public source), `[analytical]` (your interpretation) or
   `[proposed]` — and every Outcome with `{status: confirmed|proposed}`.
   For the four facet files `edgy_model_to_txt.py` writes the tags from the
   model's `provenance` fields; the purpose map is a structural map written
   from the same model (Phase 4 table), so its Outcomes and their
   `{status: …}` are written by the analyst — the model has no Outcome
   type.
2. Run the review and read every question:
   ```bash
   python3 skills/documentation/edgy-diagram/scripts/edgy_semantic_review.py <company>-purpose.txt
   ```
   S001 action as a Purpose, S002 Outcome measures nothing, S003 / S004
   missing provenance, S005 `contains` that may be an influence, S006 metric
   in a Purpose name. Fix the **model**, regenerate.
3. Walk the checklist in edgy-framework *Purpose map semantic review* and
   write the sign-off line into the report (section 9) and the delivery
   note: `Semantic review: approved by <role>, <date> — S-findings answered: <n>`.
   The tool never approves; a person does. Zero findings is not a sign-off.

If Python is unavailable and the XML must be written by hand, follow the
edgy-diagram inline example and lint it in the next environment that has
Python; the file must still contain more than the two structural cells, one
vertex per element, one edge with geometry per relationship, a legend, and
exceed 1000 bytes.

---

### Phase 5: Final Verification

Before completion, check ALL:

#### Files (10 pcs):
- [ ] `<company>-edgy-analysis.md` — analysis, min 150 lines, all 10 sections
- [ ] `<company>-edgy-model.json` — machine-readable EDGY model with suggested deep-dives
- [ ] `<company>-identity.txt` — Identity facet input
- [ ] `<company>-architecture.txt` — Architecture facet input
- [ ] `<company>-experience.txt` — Experience facet input
- [ ] `<company>-all-facets.txt` — All facets input
- [ ] `<company>-identity.drawio` — Identity diagram, >1000 bytes
- [ ] `<company>-architecture.drawio` — Architecture diagram, >1000 bytes
- [ ] `<company>-experience.drawio` — Experience diagram, >1000 bytes
- [ ] `<company>-all-facets.drawio` — All-facets diagram, >1000 bytes

#### Quality:
- [ ] Analysis is company-specific, not generic
- [ ] All 9 analysis sections are filled
- [ ] Diagrams contain elements and relationships (are not empty)
- [ ] Colour palette follows EDGY 23 standard
- [ ] Relationships use official 24 core links
- [ ] Output language matches `language` parameter

#### Approvals (`qa.json`, one per diagram):
- [ ] `python3 $G/edgy_qa.py --require-approvals <company>-*.qa.json` exits 0 — it lists the lint result and
      the two approvals on **separate lines**: zero lint findings is never an approval
- [ ] `visual_approval` set by the person who looked at every preview (name and date)
- [ ] `semantic_approval` set by the person who answered the semantic review (Phase 4b) — for a delivery
      with a purpose map, after every S-finding has an answer in the report
- [ ] `delivery_notes` carries anything the reader must know (a layout option that was switched off, a
      warning that was accepted and why)

#### Layout quality:
- [ ] `edgy_lint.py --warnings-as-errors --visual` passes for all four drawio files (0 errors, no W111–W114)
- [ ] `edgy_lint.py --series` over the four files reports no W121; the layout rules W117–W120 report nothing or each finding is answered in `delivery_notes`
- [ ] Every diagram was previewed (`--preview` / `edgy_render.py`) and looked at; the preview checklist passed
- [ ] No elements at negative coordinates in any drawio file
- [ ] No overlapping elements in any drawio file (min 10px gap)
- [ ] All element text fits within element boundaries (W101 = 0)
- [ ] `all-facets` page height ≤ 1.2 × width; facet containers visually separated
- [ ] **Final report pages looked at at the intended viewing size** — the SVG alone is not enough: check
      captions, page breaks and footer clearance on the PDF page, and run `edgy_lint.py --scale <report scale>`
      (no W115 = every title, description and relation label stays ≥ 6 pt). Use `--publication` for the
      embedded image so a sparse map is not shrunk by empty canvas

---

## Reference

See the `examples/` directory for completed assessment examples:
- `reference-analysis.md` (Finnish, lyhyt rakenne-esimerkki)
- `reference-analysis-en.md` (English)
- `intersection-edgy-analysis.md` + `intersection-edgy-analysis.pdf` —
  **täysimittainen referenssi-PDF**, joka osoittaa millaista raporttia
  käyttäjälle tulee tuottaa kun hän pyytää PDF-muotoista EDGY-analyysiä
  (kansilehti, sisällysluettelo, 12 elementin analyysi facet-kohtaisesti,
  intersection-elementit, suositukset, riskit, seuraavat askeleet).

**Reference caveat:** the intersection example is the **visual layout
reference** — colours, badges, legend, meta-table, footer. Its meta-table
"Method" row (line 54) still reads "EDGY 23 Enterprise Design in a Box
framework" — that wording is **legacy** and is preserved unchanged only
because it is a shipped customer deliverable. New analyses MUST use
`METHOD_LABEL = "EDGY 23 Enterprise Design"` (no "in a Box"); do not copy
the meta-table row verbatim from this reference.

Use these as quality and structure benchmarks.

## PDF Report Generation

When the user requests a PDF report (`pdf`, `raportti`, `report`, `--pdf`),
the visual layout is **locked** by the shared preamble — only the
analysis content changes per customer.

1. **Analysis markdown is already prepared** by Phase 2 + Phase 2a. The
   file contains the canonical `pdf_options:` frontmatter, `<style>`
   block, meta-table, legend and badge-shape row. If it does not, return
   to Phase 2a — do not proceed.

2. **Generate the four facet diagrams** with the `edgy-diagram` skill
   (`identity`, `architecture`, `experience`, `all`) as PNG so they can be
   embedded into the PDF. Engine order: draw.io CLI (`--preset presentation`,
   publication quality) when installed → `--engine plantuml` when Java and
   PlantUML are available → `--engine native` (pure Python SVG + headless
   Chromium PNG; approximate but always available). Never stop the pipeline
   because the draw.io CLI is missing.

3. **Canonical PDF conversion (only supported route):**
   ```bash
   md-to-pdf "<company>-edgy-analysis.md" \
     --launch-options '{"args":["--no-sandbox"]}'
   ```
   Requires `md-to-pdf >= 5.x` (Chromium-headless with clip-path +
   Flexbox support). Do NOT use `pandoc` or `weasyprint`: their
   rendering of clip-path/Flexbox does not match the
   intersection-edgy reference layout.

4. **Pre-conversion quality gate** (must all pass — same as Phase 2a):
   ```bash
   F="<company>-edgy-analysis.md"
   grep -q "^pdf_options:"      "$F"
   grep -q "<style>"            "$F"
   grep -q "\.edgy-badge"       "$F"
   grep -q 'class="legend"'     "$F"
   grep -q 'class="meta-table"' "$F"
   ! grep -q "{{"               "$F"
   ```

5. **Result must match** the reference layout
   `examples/intersection-edgy-analysis.pdf`: same margins, footer with
   company name and page number, identical CSS-rendered badges and
   coherence indicators, identical legend. Page count may differ by
   ±2 pages for similarly sized content; layout must be visually
   identical.

## Dependencies

- `edgy-framework` skill (for producing the analysis)
- `edgy-diagram` skill (for generating diagrams, colour palette and XML specification)
