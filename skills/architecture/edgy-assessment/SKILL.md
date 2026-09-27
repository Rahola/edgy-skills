---
name: edgy-assessment
version: "1.5.2"
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
- DO NOT write under 150 lines — that means the analysis is too shallow

---

### Phase 3: Facet TXT Files

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
python3 $G/edgy_generator.py <company>-identity.txt --output <company>-identity.drawio --preview
python3 $G/edgy_lint.py <company>-identity.drawio      # 0 errors required
# --preview wrote <company>-identity.svg (+ .png when Chromium is available): open it and check
# the preview checklist (edgy-diagram SKILL.md, "Preview loop") before moving on
```

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

#### Drawio XML Generation — Critical Instructions:

Every drawio file MUST contain:

```xml
<?xml version="1.0" encoding="utf-8"?>
<mxGraphModel dx="1440" dy="876" grid="1" gridSize="10" guides="1" tooltips="1"
              connect="1" arrows="1" fold="1" page="1" pageScale="1"
              pageWidth="1200" pageHeight="900" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- ELEMENTS AND RELATIONSHIPS GO HERE -->
    <!-- Each EDGY element = own mxCell (vertex="1") -->
    <!-- Each relationship = own mxCell (edge="1") -->
  </root>
</mxGraphModel>
```

#### Element mxCell structure:

```xml
<!-- Element (vertex) -->
<mxCell id="2" value="Element name - Description"
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;arcSize=30;fontStyle=1;fontSize=12;"
  vertex="1" parent="1">
  <mxGeometry x="80" y="100" width="120" height="60" as="geometry"/>
</mxCell>

<!-- Relationship (edge) -->
<mxCell id="10" value="contextualises"
  style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;endArrow=classic;endFill=1;"
  edge="1" source="3" target="2" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

#### Base Element Shapes — Each facet has one Outcome (rounded rect), one Activity (arrow), one Object (rectangle):

| Base Type | Identity | Architecture | Experience |
|-----------|----------|--------------|------------|
| **Outcome** (rounded rect) | Purpose | Capability | Task |
| **Activity** (arrow) | Story | Process | Journey |
| **Object** (rectangle) | Content | Asset | Channel |

Intersection elements (Brand, Product, Organisation) always use the rectangle (Object) shape.

#### EDGY 23 Colour Palette:

| Element | Colour | Shape |
|---------|--------|-------|
| Purpose | `#80ffb7` (green) | Rounded rectangle (`rounded=1;arcSize=30`) |
| Content | `#80ffb7` | Rectangle |
| Story | `#80ffb7` | Pentagon (`shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0`) |
| Capability | `#a6c0ff` (blue) | Rounded rectangle |
| Asset | `#a6c0ff` | Rectangle |
| Process | `#a6c0ff` | Pentagon |
| Task | `#ff99bd` (pink) | Rounded rectangle |
| Channel | `#ff99bd` | Rectangle |
| Journey | `#ff99bd` | Pentagon |
| Brand | `#ffd580` (yellow) | Rectangle |
| Product | `#e599ff` (violet) | Rectangle |
| Organisation | `#80eaff` (cyan) | Rectangle |

All elements: `whiteSpace=wrap;html=1;fillColor=<hex>;strokeColor=#fff;strokeWidth=2;fontStyle=1;fontSize=12;`

#### Relationship Styles:

| Type | Arrow | When |
|------|-------|------|
| Core link | `endArrow=classic;endFill=1;` | Official 24 core links |
| Flow | `endArrow=open;endFill=0;strokeWidth=2;` | Data flow (open arrowhead per EDGY spec) |
| Tree | `endArrow=none;` | Hierarchy (contains, comprises) |
| Influence | `endArrow=open;endFill=0;dashed=1;` | Other influence/guidance (default for non-standard verbs) |

All: `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;`

#### Quality Gate — CRITICAL CHECK:

**DO NOT write only the XML skeleton:**
```xml
<!-- THIS IS AN EMPTY DIAGRAM — INVALID OUTPUT -->
<mxCell id="0"/>
<mxCell id="1" parent="0"/>
```

**Every drawio file MUST pass `edgy_lint.py` with 0 errors.** In addition it MUST have:
- More than 2 mxCell elements (id=0 and id=1 are structural)
- Every EDGY element = own mxCell (`vertex="1"`, `value="..."`)
- Every relationship = own mxCell (`edge="1"`, `source="..."`, `target="..."`)
- Every edge mxCell MUST have `<mxGeometry relative="1" as="geometry"/>` as child
- File size MUST exceed 1000 bytes (empty skeleton is ~324 bytes)

**Layout quality — MUST ALL pass:**
- No element at negative x or y coordinates (all elements visible on canvas)
- No two element bounding boxes overlap (minimum 10px gap between elements)
- `pageWidth`/`pageHeight` accommodate all elements with 40px margin
- Element widths match text length (min 120, max 280, dynamic based on name length)

#### Legend — Add to every drawio diagram:

Place a legend group in the bottom-right corner (x = pageWidth − 240, y = pageHeight − 220). The legend MUST include element colour chips and relationship line style examples:

```xml
<!-- Legend background -->
<mxCell id="leg0" value="" style="rounded=1;fillColor=#f5f5f5;strokeColor=#cccccc;" vertex="1" parent="1">
  <mxGeometry x="960" y="700" width="220" height="200" as="geometry"/>
</mxCell>
<!-- Legend title -->
<mxCell id="leg1" value="&lt;b&gt;EDGY 23 — Legend&lt;/b&gt;" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=10;" vertex="1" parent="1">
  <mxGeometry x="968" y="704" width="204" height="18" as="geometry"/>
</mxCell>
<!-- Identity chip -->
<mxCell id="leg2" value="Identity (Purpose, Story, Content)" style="text;html=1;align=left;fillColor=#80ffb7;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="724" width="204" height="16" as="geometry"/>
</mxCell>
<!-- Architecture chip -->
<mxCell id="leg3" value="Architecture (Capability, Asset, Process)" style="text;html=1;align=left;fillColor=#a6c0ff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="742" width="204" height="16" as="geometry"/>
</mxCell>
<!-- Experience chip -->
<mxCell id="leg4" value="Experience (Task, Channel, Journey)" style="text;html=1;align=left;fillColor=#ff99bd;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="760" width="204" height="16" as="geometry"/>
</mxCell>
<!-- Brand / Product / Organisation chips -->
<mxCell id="leg5" value="Brand" style="text;html=1;align=left;fillColor=#ffd580;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="778" width="60" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg6" value="Product" style="text;html=1;align=left;fillColor=#e599ff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1032" y="778" width="60" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg7" value="Organisation" style="text;html=1;align=left;fillColor=#80eaff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1100" y="778" width="72" height="16" as="geometry"/>
</mxCell>
<!-- Separator line -->
<mxCell id="leg8" value="" style="line;strokeColor=#cccccc;" vertex="1" parent="1">
  <mxGeometry x="968" y="796" width="204" height="6" as="geometry"/>
</mxCell>
<!-- Relationship type examples (edge cells) -->
<mxCell id="leg9" value="Link (core link)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="804" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg10" value="" style="edgeStyle=none;endArrow=classic;endFill=1;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="811" as="sourcePoint"/><mxPoint x="1000" y="811" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg11" value="Flow (data/value)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="820" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg12" value="" style="edgeStyle=none;endArrow=open;endFill=0;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="827" as="sourcePoint"/><mxPoint x="1000" y="827" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg13" value="Tree (hierarchy)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="836" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg14" value="" style="edgeStyle=none;endArrow=none;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="843" as="sourcePoint"/><mxPoint x="1000" y="843" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg15" value="Influence (guides)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="852" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg16" value="" style="edgeStyle=none;endArrow=open;endFill=0;dashed=1;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="859" as="sourcePoint"/><mxPoint x="1000" y="859" as="targetPoint"/></mxGeometry>
</mxCell>
```

Adjust `x`/`y` coordinates based on actual `pageWidth`/`pageHeight`. Legend IDs must not conflict with element and relationship IDs — use a high starting value (e.g. `leg0`, `leg1`, …).

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

#### Layout quality:
- [ ] `edgy_lint.py` reports 0 errors for all four drawio files
- [ ] Every diagram was previewed (`--preview` / `edgy_render.py`) and looked at; the preview checklist passed
- [ ] No elements at negative coordinates in any drawio file
- [ ] No overlapping elements in any drawio file (min 10px gap)
- [ ] All element text fits within element boundaries
- [ ] Facet columns are visually separated (Identity < Architecture < Experience)

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
   (`identity`, `architecture`, `experience`, `all`) in PNG format
   (`--preset presentation`) so they can be embedded into the PDF.

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
