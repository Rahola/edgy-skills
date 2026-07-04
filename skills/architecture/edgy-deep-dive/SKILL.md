---
name: edgy-deep-dive
version: "1.0.0"
description: >
  Targeted EDGY 23 deep-dive analysis of a specific element pair or facet combination.
  Requires an existing edgy-model.json produced by the edgy-assessment skill.
  Analyses the chosen elements through one of four analytical lenses (dependency,
  alignment, gaps, opportunities) using both direct core links and 2-hop paths.
  Produces a focused markdown report and a pairwise draw.io diagram.
category: architecture
tags: [edgy, enterprise-design, architecture, analysis, deep-dive, intersection, fi, en]
languages: [fi, en]
agents:
  - claude-code
  - cursor
  - generic
inputs:
  - name: model
    type: file
    description: >
      edgy-model.json produced by the edgy-assessment skill.
      Contains all 12 EDGY elements, active core links, coherence scores,
      and suggested deep-dive analyses for this company.
  - name: focus_elements
    type: array
    description: >
      2–3 EDGY element names to analyse. Use official names:
      purpose, story, content, capability, asset, process,
      task, channel, journey, organisation, product, brand.
      Examples: ["capability", "organisation"] or ["task", "channel", "journey"]
  - name: lens
    type: enum
    values: [dependency, alignment, gaps, opportunities, all]
    default: all
    description: >
      Analytical lens to apply.
      dependency   — how the elements need each other; critical dependencies
      alignment    — coherence between elements; contradictions
      gaps         — missing links or underdeveloped elements
      opportunities — competitive advantage or growth potential
      all          — all four lenses
  - name: language
    type: enum
    values: [fi, en]
    default: fi
    description: >
      Output language. Currently only fi and en are supported (output templates
      and lens-specific section headers are localised for these two only).
outputs:
  - type: markdown
    description: Focused deep-dive analysis with direct and 2-hop core-link analysis
  - type: file
    description: edgy-diagram-compatible TXT input for pairwise map
  - type: file
    description: draw.io diagram (pairwise layout, focus elements bold-bordered)
---

# EDGY Deep-Dive Analysis

## Purpose

This skill performs a **targeted analysis of a specific EDGY element pair** using
an existing company EDGY model as context. It traces both direct core links and
indirect (2-hop) paths between the chosen elements, then analyses their relationship
through the selected lens.

Use this skill when:
- You have completed an `edgy-assessment` and want to explore a specific element pair in depth
- The assessment's "Suggested deep-dive analyses" section identified a High-priority pair
- The client wants to understand how, for example, Architecture capabilities are
  structured relative to the Organisation, or how Products map to customer Tasks

**Prerequisite:** `edgy-assessment` must have been run and produced `<company>-edgy-model.json`.

**This skill produces:**
- `<company>-deep-dive-<elements>.md` — focused analysis report
- `<company>-deep-dive-<elements>.txt` — edgy-diagram input (pairwise map)
- `<company>-deep-dive-<elements>.drawio` — pairwise draw.io diagram

**IMPORTANT:** Produce all output in the language specified by the `language` parameter.

---

## Official 24 EDGY Core Links (reference for path tracing)

| Source → Target | FI | EN |
|-----------------|----|----|
| story → purpose | kontekstualisoi | contextualises |
| content → purpose | ilmaisee | expresses |
| content → story | välittää | conveys |
| brand → story | herättää | evokes |
| brand → purpose | edustaa | represents |
| capability → asset | vaatii | requires |
| process → capability | toteuttaa | realises |
| process → asset | vaatii | requires |
| product → capability | vaatii | requires |
| process → product | luo | creates |
| task → journey | on osa | is part of |
| task → channel | käyttää | uses |
| journey → channel | kulkee | traverses |
| brand → task | tukee | supports |
| brand → journey | näkyy | appears in |
| organisation → purpose | tavoittelee | pursues |
| organisation → story | kirjoittaa | authors |
| organisation → capability | omistaa | has |
| organisation → process | suorittaa | performs |
| product → task | palvelee | serves |
| product → journey | esiintyy | features in |
| organisation → brand | rakentaa | builds |
| organisation → product | valmistaa | makes |
| product → brand | ilmentää | embodies |

---

## Agent Instructions

### CRITICAL: Read the full instructions before starting

Do not skip phases. Every phase is required to produce a complete, grounded analysis.

---

### Phase 1: Load Context

1. Read the `model` file (edgy-model.json).
2. Extract the entries for all `focus_elements` from `elements`.
3. Note the coherence scores from `coherence` for any intersection elements in the focus.
4. Check `suggested_deep_dives` — if this exact pair was suggested, note its rationale and priority.

**Minimum requirement:** You must extract at least one element description and at least one active core link from the model before proceeding. If the model is missing or malformed, ask the user to run `edgy-assessment` first.

---

### Phase 2: Trace Core-Link Paths

Build the **link graph** for the focus elements:

#### Step 1 — Direct links (1-hop)
List every core link from the table above where *both* source and target are in `focus_elements`.

Example for `["capability", "organisation"]`:
- `organisation → capability: has` ✓ (direct)

#### Step 2 — 2-hop paths
List every path A → X → B (or B → X → A) where A and B are in `focus_elements` and X is any other element.

Example for `["capability", "organisation"]`:
- `organisation → process: performs` AND `process → capability: realises`
  → path: organisation **→(performs)→** process **→(realises)→** capability

#### Step 3 — Cross-check with active model links
From the model's `core_links` array, mark which of the above links are *active* (present in the model) vs. *theoretical* (in the framework but not observed in this company). An absent link that *should* exist is itself a gap finding.

Present results as a table:

| Path | Hops | Status | Verb(s) |
|------|------|--------|---------|
| organisation → capability | 1 | Active | omistaa |
| organisation → process → capability | 2 | Partial (process→capability missing) | suorittaa / toteuttaa |

---

### Phase 3: Deep Analysis by Lens

Run the analysis for each selected lens. Every finding must reference a specific element from the model (use element names, not generic statements).

#### Lens: Dependency (`dependency`)

Analyse how the focus elements structurally need each other:

- **Critical dependencies:** Which links are load-bearing? What breaks if the link is absent?
- **Direction of dependency:** Which element depends on the other, or is it mutual?
- **Bottlenecks:** If one element changes (e.g. a new capability is added), which element must change too?
- **Resilience:** Are there alternative paths that reduce single-point dependency?

Output format:
```markdown
### Riippuvuusanalyysi: [Elementti A] ↔ [Elementti B]

**Kriittiset riippuvuudet:**
- [elementti] vaatii [toinen elementti] koska ... (lähde: malli-elementti)

**Riippuvuuden suunta:** [yksisuuntainen A→B | molemminpuolinen]

**Pullonkaulat:**
- ...

**Vaihtoehtoiset polut:**
- ...
```

#### Lens: Alignment (`alignment`)

Analyse coherence and contradictions between the focus elements:

- **Alignment score per link:** Strong / Good / Weak — with justification
- **Contradictions:** Explicit conflicts between element descriptions or their relationship
- **Mismatches:** Areas where element A implies something that element B doesn't support
- **Root cause hypothesis:** Why does the misalignment exist?

Output format:
```markdown
### Yhdenmukaisu­usarvio: [Elementti A] ↔ [Elementti B]

| Linkki | Yhdenmukaisu­us | Perustelu |
|--------|----------------|-----------|
| organisation → capability | Weak | Org-rakenne on toiminnallinen, kyvykkyydet ovat asiakkuus­kohtaisia |

**Ristiriidat:**
- ...

**Juurisyyanalyysi:**
- ...
```

#### Lens: Gaps (`gaps`)

Identify missing links and underdeveloped elements:

- **Missing core links:** Links that should exist (per framework) but are absent from the model
- **Underdeveloped elements:** Elements with only superficial descriptions or no active links
- **Consequence of each gap:** What business problem does this gap cause?
- **Gap severity:** High (blocks strategic objectives) / Medium (slows delivery) / Low (nice to have)

Output format:
```markdown
### Puuteanalyysi: [Elementti A] ↔ [Elementti B]

| Puuttuva linkki | Pitäisi olla | Vaikutus | Vakavuus |
|----------------|-------------|---------|---------|
| process → capability | process toteuttaa capability | Prosessit eivät tue strategisia kyvykkyyksiä | High |

**Alikehittyneet elementit:**
- [elementti]: vain yksi kuvaus, ei aktiivisia linkkejä → ...
```

#### Lens: Opportunities (`opportunities`)

Identify where the element pair creates competitive advantage or growth potential:

- **Leverage points:** Where is the element pair unusually strong vs. industry baseline?
- **Compounding effects:** Where could investing in one element multiply value in the other?
- **Strategic asymmetry:** What can this company do with this element combination that competitors cannot?
- **Priority actions:** Top 3 actions to realise the opportunity, with responsible element

Output format:
```markdown
### Mahdollisuudet: [Elementti A] ↔ [Elementti B]

**Vipuvoimapisteet:**
- ...

**Kerrannaishyödyt:**
- [elementti A]:n vahvistaminen → vaikuttaa [elementti B]:hen koska ...

**Strateginen epäsymmetria:**
- ...

**Prioriteettiset toimenpiteet:**
1. [toimenpide] — vastuullinen elementti: [X] — vaikutus: High/Medium/Low
2. ...
3. ...
```

---

### Phase 4: Generate Pairwise Diagram Input

Produce `<company>-deep-dive-<elements>.txt` in edgy-diagram input format.

Include only:
- The focus elements themselves
- Their direct (1-hop) neighbours that participate in active links
- All core links between these elements

Mark focus elements with `[focus]` tag.

The TXT file is a human-readable specification — the `edgy_parser.py` does
not currently parse `pairwise` layouts, so the agent **generates the .drawio
XML directly** following the pairwise layout spec in
`skills/documentation/edgy-diagram/SKILL.md` (see "Pairwise Map" section).
Use the same `facet` / `elements` / `relationships` structure as other
edgy-diagram inputs for readability:

```
facet: architecture
focus: [capability, organisation]

elements:
  - capability: "Capability name - Description" [focus]
  - organisation: "Organisation name - Description" [focus]
  - process: "Process name - Description"   (neighbour via organisation→process→capability)

relationships:
  - "organisation" -> "capability": "omistaa"
  - "organisation" -> "process": "suorittaa"
  - "process" -> "capability": "toteuttaa"
```

Then author `<company>-deep-dive-<elements>.drawio` directly as XML following the pairwise layout rules:
- Focus elements: `strokeWidth=4` (bold border), same colour as their element type
- Neighbour elements: normal `strokeWidth=2`
- Direct core links: solid arrow + verb label
- 2-hop paths: dashed arrow (`dashed=1`) + intermediate element name as path label
- Layout: focus element A left column, focus element B right column, neighbours outside both

---

### Phase 5: Deliver and Suggest Next Step

1. Show the complete `<company>-deep-dive-<elements>.md` report.
2. End with a **"Seuraava jatkoanalyysi"** (Next deep-dive) suggestion block:

```markdown
## Seuraava jatkoanalyysi

Tämän analyysin löydösten perusteella suositellaan seuraavaa:

| Elementtipari | Linssi | Perustelu |
|---------------|--------|-----------|
| capability × process | gaps | [Puute löydettiin: process→capability-linkki puuttuu] |
| product × task | alignment | [Löydettiin tuote jolla ei ole task-linkkiä] |
```

The suggestion must be grounded in a specific finding from this analysis (reference phase 3 outputs).

---

## Output Template

### Finnish (fi)

```markdown
# EDGY Syväanalyysi: [Elementti A] × [Elementti B]
**Yritys:** [Nimi]
**Linssi:** [dependency | alignment | gaps | opportunities | all]
**Analysoitu:** [pvm]

---

## Linkkartta

[Phase 2 table — direct links and 2-hop paths]

---

## [Linssi-osio(t)]

[Phase 3 content]

---

## Yhteenveto

[2–3 lausetta päälöydöksistä ja suositellusta toimenpiteestä]

---

## Seuraava jatkoanalyysi

[Phase 5 suggestion table]
```

### English (en)

```markdown
# EDGY Deep-Dive: [Element A] × [Element B]
**Company:** [Name]
**Lens:** [dependency | alignment | gaps | opportunities | all]
**Analysed:** [date]

---

## Link Map

[Phase 2 table]

---

## [Lens section(s)]

[Phase 3 content]

---

## Summary

[2–3 sentences on key findings and recommended action]

---

## Next Deep-Dive

[Phase 5 suggestion table]
```

---

## Quality Gate

Before delivering, verify:
- [ ] All focus elements are present in the model (not invented)
- [ ] Link map contains at least 1 direct or 2-hop link
- [ ] Every finding references a specific element name from the model
- [ ] No generic statements ("the organisation should improve its capabilities") without specific grounding
- [ ] Pairwise diagram TXT contains `[focus]` tags on focus elements
- [ ] Next deep-dive suggestion is grounded in a finding from this analysis

## Anti-patterns

- DO NOT analyse elements that are not in the model without noting they are missing
- DO NOT write generic capability/organisation advice not grounded in model data
- DO NOT skip the link map — it is the structural foundation of the analysis
- DO NOT suggest the same element pair as the next deep-dive (suggest a new pair)

---

## Reference

See `examples/` for a complete deep-dive example:
- `examples/sample-model.json` — Globex Oy EDGY model (from edgy-assessment)
- `examples/expected-deep-dive.md` — capability × organisation, lens=dependency
