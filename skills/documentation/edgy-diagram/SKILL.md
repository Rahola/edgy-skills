---
name: edgy-diagram
version: "1.7.0"
description: >
  Create EDGY-notation diagrams as draw.io XML or PlantUML source and export
  them to PNG/SVG/PDF. Uses the EDGY facet model with draw.io CLI or the
  plantuml-stdlib `<edgy/edgy>` library for rendering.
category: documentation
tags: [diagram, drawio, visualization, documentation, edgy, enterprise-design, fi, en, fr, de]
languages: [fi, en, fr, de]
agents:
  - claude-code
  - cursor
  - generic
inputs:
  - name: facet
    type: enum
    values: [identity, architecture, experience, all]
    description: EDGY facet (Identity, Architecture, Experience or All)
  - name: map_type
    type: enum
    values: [capability, organisation, outcome, journey, activity, process, purpose, brand, product, object, asset, channel, content, people, story, task]
    required: false
    description: >
      Map type (overrides facet layout). 16 types backed by 4 layout strategies
      (grid / tree / sequence / hub-and-spoke). See Map Types section.
      Note: pairwise deep-dive diagrams are documented separately and generated
      via direct XML by the edgy-deep-dive skill — they are not handled by
      edgy_parser.py.
  - name: elements
    type: text
    description: List of EDGY elements and their relationships
  - name: format
    type: enum
    values: [drawio, png, svg, pdf, plantuml, puml]
    default: drawio
    description: >
      Output format. `drawio` = draw.io XML; `plantuml`/`puml` = PlantUML
      source using `<edgy/edgy>` stdlib; `png`/`svg`/`pdf` = rendered image
      (engine selected via --engine).
  - name: engine
    type: enum
    values: [drawio, plantuml]
    default: drawio
    description: >
      Render engine for png/svg/pdf. `drawio` uses draw.io CLI; `plantuml`
      uses plantuml.jar or `plantuml` binary. Ignored when format is
      drawio/plantuml/puml.
  - name: language
    type: enum
    values: [fi, en, fr, de]
    default: fi
outputs:
  - type: file
    description: Generated EDGY diagram file (drawio, png, svg or pdf)
examples:
  - input: examples/identity-facet.txt
    output: examples/expected-identity.drawio
  - input: examples/architecture-facet.txt
    output: examples/expected-architecture.drawio
  - input: examples/experience-facet.txt
    output: examples/expected-experience.drawio
  - input: examples/full-edgy-map.txt
    output: examples/expected-full-edgy.drawio
  - input: examples/activity-map.txt
    output: examples/expected-activity.drawio
  - input: examples/process-map.txt
    output: examples/expected-process.drawio
  - input: examples/outcome-map.txt
    output: examples/expected-outcome.drawio
  - input: examples/asset-map.txt
    output: examples/expected-asset.drawio
  - input: examples/channel-map.txt
    output: examples/expected-channel.drawio
  - input: examples/content-map.txt
    output: examples/expected-content.drawio
  - input: examples/story-map.txt
    output: examples/expected-story.drawio
  - input: examples/people-map.txt
    output: examples/expected-people.drawio
  - input: examples/task-map.txt
    output: examples/expected-task.drawio
  - input: examples/brand-map.txt
    output: examples/expected-brand.drawio
  - input: examples/product-map.txt
    output: examples/expected-product.drawio
  - input: examples/object-map.txt
    output: examples/expected-object.drawio
  - input: examples/purpose-map.txt
    output: examples/expected-purpose.drawio
  - input: examples/purpose-map.txt
    output: examples/expected-purpose.puml
---

# EDGY Diagram Skill

## Purpose

This skill generates draw.io diagrams with EDGY notation and exports them to the desired format. It uses the EDGY facet model and draw.io CLI for diagram generation and export.

Use this skill when:
- You need an EDGY-notation diagram for enterprise architecture
- You want to visualise EDGY facet model elements and their relationships
- You need a diagram that follows the EDGY 23 standard

**IMPORTANT:** Use the relationship verb matching the `language` parameter from the core links table below.

## Agent Instructions

### Primary Method: Direct XML Generation

**Generate draw.io XML directly** — this is the primary and recommended method. DO NOT use Python scripts unless you are certain they can be executed.

1. **Parse EDGY elements** from user input (natural language → element types)
2. **Map elements to the facet model** and identify their relationships
3. **Generate draw.io XML directly** in mxGraphModel format per the specification below
4. **Write XML** to a `.drawio` file in the current working directory
5. **Validate output** — verify the file contains elements (see validation section below)
6. **If the user requests an export format** (png, svg, pdf), export using draw.io CLI

### Complete Inline Example (Identity facet, 3 elements + 2 relationships)

```xml
<?xml version="1.0" encoding="utf-8"?>
<mxGraphModel dx="1440" dy="876" grid="1" gridSize="10" guides="1" tooltips="1"
              connect="1" arrows="1" fold="1" page="1" pageScale="1"
              pageWidth="1200" pageHeight="900" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Purpose (green rounded rectangle) -->
    <mxCell id="2" value="Sustainable technology partnership"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;arcSize=30;fontStyle=1;fontSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
    <!-- Story (green pentagon) -->
    <mxCell id="3" value="From Otaniemi to 200+ projects"
      style="shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;fontStyle=1;fontSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="280" y="100" width="140" height="60" as="geometry"/>
    </mxCell>
    <!-- Content (green rectangle) -->
    <mxCell id="4" value="Underpromise, overdeliver"
      style="whiteSpace=wrap;html=1;fillColor=#80ffb7;strokeColor=#fff;strokeWidth=2;fontStyle=1;fontSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="480" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
    <!-- Relationship: story contextualises purpose -->
    <mxCell id="5" value="contextualises"
      style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;endArrow=classic;endFill=1;"
      edge="1" source="3" target="2" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <!-- Relationship: content expresses purpose -->
    <mxCell id="6" value="expresses"
      style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;endArrow=classic;endFill=1;"
      edge="1" source="4" target="2" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

**This is a correct output.** Every EDGY element is its own mxCell (`vertex="1"`), every relationship is its own mxCell (`edge="1"`). Extend this by adding elements and relationships.

**Every diagram MUST also include a legend** in the bottom-right corner. Add these mxCells before `</root>` (adjust x/y to `pageWidth − 240`, `pageHeight − 220`):

```xml
<!-- Legend background -->
<mxCell id="leg0" value="" style="rounded=1;fillColor=#f5f5f5;strokeColor=#cccccc;" vertex="1" parent="1">
  <mxGeometry x="960" y="680" width="220" height="200" as="geometry"/>
</mxCell>
<mxCell id="leg1" value="&lt;b&gt;EDGY 23 — Legend&lt;/b&gt;" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=10;" vertex="1" parent="1">
  <mxGeometry x="968" y="684" width="204" height="18" as="geometry"/>
</mxCell>
<mxCell id="leg2" value="Identity (Purpose, Story, Content)" style="text;html=1;align=left;fillColor=#80ffb7;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="704" width="204" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg3" value="Architecture (Capability, Asset, Process)" style="text;html=1;align=left;fillColor=#a6c0ff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="722" width="204" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg4" value="Experience (Task, Channel, Journey)" style="text;html=1;align=left;fillColor=#ff99bd;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="740" width="204" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg5" value="Brand" style="text;html=1;align=left;fillColor=#ffd580;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="968" y="758" width="60" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg6" value="Product" style="text;html=1;align=left;fillColor=#e599ff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1032" y="758" width="60" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg7" value="Organisation" style="text;html=1;align=left;fillColor=#80eaff;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1100" y="758" width="72" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg8" value="" style="line;strokeColor=#cccccc;" vertex="1" parent="1">
  <mxGeometry x="968" y="776" width="204" height="6" as="geometry"/>
</mxCell>
<!-- Relationship type examples -->
<mxCell id="leg9" value="Link (core link)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="784" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg10" value="" style="edgeStyle=none;endArrow=classic;endFill=1;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="791" as="sourcePoint"/><mxPoint x="1000" y="791" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg11" value="Flow (data/value)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="800" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg12" value="" style="edgeStyle=none;endArrow=open;endFill=0;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="807" as="sourcePoint"/><mxPoint x="1000" y="807" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg13" value="Tree (hierarchy)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="816" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg14" value="" style="edgeStyle=none;endArrow=none;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="823" as="sourcePoint"/><mxPoint x="1000" y="823" as="targetPoint"/></mxGeometry>
</mxCell>
<mxCell id="leg15" value="Influence (guides)" style="text;html=1;align=left;fillColor=none;strokeColor=none;fontSize=9;" vertex="1" parent="1">
  <mxGeometry x="1004" y="832" width="164" height="14" as="geometry"/>
</mxCell>
<mxCell id="leg16" value="" style="edgeStyle=none;endArrow=open;endFill=0;dashed=1;strokeWidth=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry"><mxPoint x="968" y="839" as="sourcePoint"/><mxPoint x="1000" y="839" as="targetPoint"/></mxGeometry>
</mxCell>
```

### CRITICAL VALIDATION — Always check before saving

**A valid drawio file contains:**
- More than 2 mxCell elements (id=0 and id=1 are structural, not content)
- Every EDGY element = own mxCell (`vertex="1"`, `value="[element name]"`)
- Every relationship = own mxCell (`edge="1"`, `source="[id]"`, `target="[id]"`)
- Every edge mxCell must have `<mxGeometry relative="1" as="geometry"/>` as child
- File size > 1000 bytes
- Element count meets the `Min elements` threshold for the chosen `map_type` (see Map Types table). Below threshold the diagram looks sparse compared to the official EDGY 23 examples — increase the element count before exporting.

**COMMON FAILURE MODE — this produces an EMPTY diagram:**
```xml
<!-- INVALID: This is an empty diagram (~324 bytes) -->
<root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
</root>
```
If your output contains ONLY these two mxCell elements, the diagram is empty and invalid. You MUST add mxCell elements for every EDGY element and relationship.

### Alternative Method: Python Scripts

If you have a reliable Python execution environment, you can use `scripts/edgy_generator.py`:
```bash
python scripts/edgy_generator.py <input_file> --format drawio --output <output_file>
```
This is an alternative method — direct XML generation is preferred.

## EDGY Facet Model

EDGY consists of three main facets and three intersection elements.

### Base Elements

All facet elements are specialisations of these four base elements. Base elements are applicable to all facets.

| Type | Description | Shape | Example |
|------|-------------|-------|---------|
| `people` | Individuals who together create the enterprise or use products | Person shape | `- people: "Customers"` |
| `activity` | What is done or happens in the enterprise or ecosystem | Pentagon/arrow | `- activity: "Product development"` |
| `outcome` | Result or change in the enterprise or ecosystem | Rounded rectangle | `- outcome: "Customer satisfaction"` |
| `object` | Tangible or intangible structure | Rectangle | `- object: "Database"` |

### Identity (Why does the enterprise exist?)
- **Purpose** — The enterprise's fundamental reason for being
- **Content** — Messages, signals, communications
- **Story** — Shared narrative, history

### Architecture (How does the enterprise operate?)
- **Capability** — Capabilities, competencies
- **Asset** — Resources, property, systems
- **Process** — Processes, ways of working

### Experience (What role does the enterprise play in people's lives?)
- **Task** — Tasks, activities
- **Channel** — Channels, interactions
- **Journey** — Customer journeys

### Intersection Elements

These three elements serve as bridges between facets:

| Element | Connects Facets | Role |
|---------|----------------|------|
| **Brand** | Identity ↔ Experience | Brand, identity |
| **Product** | Architecture ↔ Experience | Products, services |
| **Organisation** | Identity ↔ Architecture | Organisation, structure |

When facet is `identity`: include Brand and Organisation
When facet is `architecture`: include Organisation and Product
When facet is `experience`: include Brand and Product
When facet is `all`: include all three

## Input Format

### Formal Syntax

```
facet: identity | architecture | experience | all
map_type: capability | organisation | journey | purpose   # optional, overrides facet layout

elements:
  - <element_type>: "<name>"
  - <element_type>: "<name> - <description>"

relationships:
  - "<source name>" -> "<target name>": "<relationship name>"
  # OR by type (only works if there is exactly one element of that type):
  - <source_type> -> <target_type>: "<relationship name>"
```

### Allowed Element Types

| Type | Facet | Example |
|------|-------|---------|
| `people` | Base | `- people: "Customers"` |
| `activity` | Base | `- activity: "Product development"` |
| `outcome` | Base | `- outcome: "Customer satisfaction"` |
| `object` | Base | `- object: "Database"` |
| `purpose` | Identity | `- purpose: "Sustainable value"` |
| `content` | Identity | `- content: "Professional communication"` |
| `story` | Identity | `- story: "Innovation story"` |
| `capability` | Architecture | `- capability: "Software development"` |
| `asset` | Architecture | `- asset: "Cloud infrastructure"` |
| `process` | Architecture | `- process: "Agile development"` |
| `task` | Experience | `- task: "Customer registration"` |
| `channel` | Experience | `- channel: "Website"` |
| `journey` | Experience | `- journey: "Customer journey"` |
| `brand` | Intersection | `- brand: "Trusted brand"` |
| `product` | Intersection | `- product: "SaaS platform"` |
| `organisation` | Intersection | `- organisation: "Team-based"` |

### Relationship Source/Target Matching Logic

In relationships, source and target are matched to elements in the following order:

1. **Exact match** — value matches the element name completely (preferred)
2. **Prefix match** — value matches the element name prefix before ` - ` separator
3. **Type match** — value matches the element type (e.g. `purpose`)

**IMPORTANT:** Use the element's exact name in quotes for relationships. This prevents incorrect matches when two elements have similar names (e.g. "Test" and "Test System").

### Labels (Tags and Metrics)

Elements can have tags in square brackets and metrics in curly braces:

```
elements:
  - capability: "Customer service" [in-house, differentiating]
  - asset: "CRM system" [application, owned] {cost: high, performance: good}
  - task: "Registration" [functional] {satisfaction: ok}
```

#### Recommended Tags by Element Type (EDGY 23)

| Element | Tags | Metrics |
|---------|------|---------|
| Capability | in-house/outsourced, innovating/differentiating/commodity | cost, performance |
| Asset | material/machine/document/application/data, owned/external | cost, expiry |
| Process | internal/shared, structured/non-structured, manual/automated/hybrid | automation, cost |
| Task | functional/emotional/social | satisfaction |
| Channel | digital/physical/hybrid, synchronous/asynchronous | usage, cost |
| Organisation | company/association/team/project, hierarchical/matrix | satisfaction, cost |
| Product | physical/digital/service | revenue, satisfaction |

#### Metric Colour Coding

| Value | Colour | Usage |
|-------|--------|-------|
| good / hyvä / bon / gut | Green | Positive state |
| ok / keskiverto / moyen / mittel | Yellow | Neutral state |
| bad / huono / mauvais / schlecht | Red | Negative state |
| low / matala / bas / niedrig | Green | Low cost etc. |
| high / korkea / élevé / hoch | Red | High cost etc. |

### Comments and Empty Lines

- Comments start with `#` and are ignored
- Empty lines are allowed anywhere

### Relationship Types

EDGY 23 defines four relationship types:

| Type | Visual Style | When to Use |
|------|-------------|-------------|
| **Link** (core link) | Solid line, directional arrow | Official 24 core links (below) |
| **Flow** | Solid line, open arrowhead | Data/information/value/material transfers concretely |
| **Tree** | Solid line, no arrowhead | Hierarchy: decomposition, portfolios, organisational structures |
| **Influence** | Dashed line, open arrowhead | Other influence/guidance (default) |

### Official 24 EDGY Core Links

These are the official named links from the EDGY 23 specification. Use the relationship verb matching the `language` parameter.

#### Identity Facet Links

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| story → purpose | contextualises | kontekstualisoi | contextualise | kontextualisiert |
| content → purpose | expresses | ilmaisee | exprime | drückt aus |
| content → story | conveys | välittää | transmet | vermittelt |
| brand → story | evokes | herättää | évoque | evoziert |
| brand → purpose | represents | edustaa | représente | repräsentiert |

#### Architecture Facet Links

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| capability → asset | requires | vaatii | nécessite | erfordert |
| process → capability | realises | toteuttaa | réalise | realisiert |
| process → asset | requires | vaatii | nécessite | erfordert |
| product → capability | requires | vaatii | nécessite | erfordert |
| process → product | creates | luo | crée | erzeugt |

#### Experience Facet Links

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| task → journey | is part of | on osa | fait partie de | ist Teil von |
| task → channel | uses | käyttää | utilise | nutzt |
| journey → channel | traverses | kulkee | traverse | durchläuft |
| brand → task | supports | tukee | soutient | unterstützt |
| brand → journey | appears in | näkyy | apparaît dans | erscheint in |

#### Organisation Intersection Links (Identity ↔ Architecture)

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| organisation → purpose | pursues | tavoittelee | poursuit | verfolgt |
| organisation → story | authors | kirjoittaa | rédige | verfasst |
| organisation → capability | has | omistaa | possède | besitzt |
| organisation → process | performs | suorittaa | exécute | führt aus |

#### Product Intersection Links (Architecture ↔ Experience)

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| product → task | serves | palvelee | sert | bedient |
| product → journey | features in | esiintyy | figure dans | erscheint in |

#### Intersection Element Cross-Links

| Source → Target | EN | FI | FR | DE |
|-----------------|----|----|----|----|
| organisation → brand | builds | rakentaa | construit | baut auf |
| organisation → product | makes | valmistaa | fabrique | stellt her |
| product → brand | embodies | ilmentää | incarne | verkörpert |

### Flow Relationship Keywords

| EN | FI | FR | DE | Usage |
|----|----|----|-----|-------|
| flows | virtaa | circule | fließt | Data/information flows from A to B |
| transfers | siirtyy | transfère | überträgt | Value/object transfers |
| produces data | tuottaa dataa | produit des données | erzeugt Daten | A produces data for B |
| returns | palauttaa | retourne | gibt zurück | Feedback flow |

Flow arrows can describe what flows: information, money, material, energy, attention.
Example syntax: `"System A" -> "System B": "flows [customer data]"`

### Tree Hierarchy Keywords

| EN | FI | FR | DE | Usage |
|----|----|----|-----|-------|
| contains | sisältää | contient | enthält | Whole contains part |
| comprises | koostuu | comprend | umfasst | Whole comprises parts |
| decomposes | jakaantuu | se décompose | zerlegt sich | Whole decomposes into parts |

## EDGY Element Identification from Natural Language

When the user provides a description in natural language, identify elements as follows:

| User expression (EN) | User expression (FI) | User expression (FR) | User expression (DE) | EDGY element |
|----------------------|---------------------|----------------------|---------------------|--------------|
| "people X", "staff X", "stakeholder X", "customer X" | "ihmiset X", "henkilöstö X", "sidosryhmä X", "asiakas X" | "personnes X", "personnel X", "partie prenante X", "client X" | "Menschen X", "Personal X", "Stakeholder X", "Kunde X" | `people` |
| "organisation X", "company X", "team X" | "organisaatio X", "yritys X", "tiimi X" | "organisation X", "entreprise X", "équipe X" | "Organisation X", "Unternehmen X", "Team X" | `organisation` |
| "system X", "platform X", "infrastructure X" | "järjestelmä X", "alusta X", "infrastruktuuri X" | "système X", "plateforme X", "infrastructure X" | "System X", "Plattform X", "Infrastruktur X" | `asset` |
| "capability X", "competence X" | "kyvykkyys X", "osaaminen X" | "capacité X", "compétence X" | "Fähigkeit X", "Kompetenz X" | `capability` |
| "product X", "service X" | "tuote X", "palvelu X" | "produit X", "service X" | "Produkt X", "Dienstleistung X" | `product` |
| "task X", "test X", "function X" | "tehtävä X", "testi X", "toiminto X" | "tâche X", "test X", "fonction X" | "Aufgabe X", "Test X", "Funktion X" | `task` |
| "process X", "workflow X" | "prosessi X", "työnkulku X" | "processus X", "flux de travail X" | "Prozess X", "Arbeitsablauf X" | `process` |
| "channel X", "interface X" | "kanava X", "käyttöliittymä X" | "canal X", "interface X" | "Kanal X", "Schnittstelle X" | `channel` |
| "purpose X", "mission X" | "tarkoitus X", "missio X" | "raison d'être X", "mission X" | "Zweck X", "Mission X" | `purpose` |
| "story X", "history X" | "tarina X", "historia X" | "histoire X", "récit X" | "Geschichte X", "Historie X" | `story` |
| "content X", "communication X" | "sisältö X", "viestintä X" | "contenu X", "communication X" | "Inhalt X", "Kommunikation X" | `content` |
| "brand X", "identity X" | "brändi X", "identiteetti X" | "marque X", "identité X" | "Marke X", "Identität X" | `brand` |
| "journey X", "customer path X" | "matka X", "asiakaspolku X" | "parcours X", "chemin client X" | "Reise X", "Kundenreise X" | `journey` |

## EDGY XML Structure

### Base Structure

IMPORTANT: All `mxCell` elements are direct children of `<root>`.
Logical parent-child relationships are expressed via the `parent` attribute, NOT via XML nesting.

```xml
<mxGraphModel dx="1440" dy="876" grid="1" gridSize="10" guides="1" tooltips="1"
              connect="1" arrows="1" fold="1" page="1" pageScale="1"
              pageWidth="1200" pageHeight="900" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- All elements and relationships here, as direct children of root -->
  </root>
</mxGraphModel>
```

### Base Element Types and Shape Inheritance

EDGY 23 defines three base element types. Each facet contains exactly one element of each base type, creating a consistent visual pattern across all facets:

| Base Type | Shape | Identity | Architecture | Experience |
|-----------|-------|----------|--------------|------------|
| **Outcome** | Rounded rectangle | Purpose | Capability | Task |
| **Activity** | Pentagon/arrow | Story | Process | Journey |
| **Object** | Rectangle | Content | Asset | Channel |

Intersection elements (Brand, Product, Organisation) use the **Object** (rectangle) shape.

**Critical:** When generating diagrams, ensure each element uses the shape inherited from its base type — not a uniform shape for the entire facet. For example, within the Identity facet (all green `#80ffb7`), Purpose is a rounded rectangle, Story is a pentagon/arrow, and Content is a plain rectangle.

### EDGY 23 Colour Palette (Official Stencil Colours)

| Element | Colour | Hex | Shape |
|---------|--------|-----|-------|
| Purpose | Green | `#80ffb7` | Rounded rectangle (`rounded=1;arcSize=30`) |
| Content | Green | `#80ffb7` | Rectangle |
| Story | Green | `#80ffb7` | Pentagon/arrow |
| Capability | Blue | `#a6c0ff` | Rounded rectangle (`rounded=1;arcSize=30`) |
| Asset | Blue | `#a6c0ff` | Rectangle |
| Process | Blue | `#a6c0ff` | Pentagon/arrow |
| Task | Pink | `#ff99bd` | Rounded rectangle (`rounded=1;arcSize=30`) |
| Channel | Pink | `#ff99bd` | Rectangle |
| Journey | Pink | `#ff99bd` | Pentagon/arrow |
| Brand | Yellow | `#ffd580` | Rectangle |
| Product | Violet | `#e599ff` | Rectangle |
| Organisation | Cyan | `#80eaff` | Rectangle |

All elements: `strokeColor=#fff` (white), `strokeWidth=2`, `fontStyle=1` (bold), `fontSize=12`

### Element Styles

| Shape | Elements | Style Addition | Size |
|-------|----------|---------------|------|
| Rounded rectangle | Purpose, Capability, Task, Outcome | `rounded=1;arcSize=30;` | 120×60 |
| Rectangle | Content, Asset, Channel, Brand, Product, Organisation, Object | (base style) | 120×60 |
| Pentagon/arrow | Story, Process, Journey, Activity | `shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;` | 140×60 |
| Person shape | People | `shape=mxgraph.basic.person;` | 60×80 |

All: `whiteSpace=wrap;html=1;fillColor=<hex>;strokeColor=#fff;strokeWidth=2;fontStyle=1;fontSize=12;`

### Relationship Lines (Edges)

EDGY 23 uses four visually distinct relationship types:

| Type | Visual Style | Example Relationships |
|------|-------------|----------------------|
| **Link** (core link) | Solid line, directional arrow | pursues, realises, requires, serves, creates, represents (official 24 core links) |
| **Flow** | Solid line, open arrowhead | flows, transfers, produces data, returns |
| **Tree** | Solid line, no arrowhead | contains, comprises, decomposes |
| **Influence** (default) | Dashed line, open arrowhead | guides, enables (anything not listed above) |

### Relationship Type Selection Algorithm

The parser determines relationship style automatically by name:

1. If name is in `EDGY_CORE_LINKS` dictionary → **Link** (`endArrow=classic;endFill=1;`)
2. If name is in `FLOW_RELATIONSHIPS` set → **Flow** (`endArrow=open;endFill=0;`)
3. If name is in `TREE_RELATIONSHIPS` set → **Tree** (`endArrow=none;`)
4. Otherwise → **Influence** (`endArrow=open;endFill=0;dashed=1;`)

All: `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;` + arrow type

## CRITICAL: XML Well-Formedness

- **Edge cells** — Every edge `mxCell` MUST HAVE `<mxGeometry relative="1" as="geometry"/>` as a child element. Self-closing edge cells (e.g. `<mxCell ... edge="1" ... />`) are invalid and will not render.
- **All mxCell elements directly under root** — NO nested mxCell structures. Parent-child relationships are expressed via the `parent` attribute.
- **Escape XML special characters** in attribute values: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- **Unique id values** — Every `mxCell` must have a unique `id`. Start element IDs from 2 (0 and 1 are reserved).
- **No `--` in XML comments** — Double hyphen `--` is forbidden inside `<!-- -->` comments per XML specification.
- **UTF-8 encoding** — Always write files with UTF-8 encoding (`<?xml version="1.0" encoding="utf-8"?>`).

## CRITICAL: Routing and Space Usage

- **Sufficient space between elements** — At least 80px horizontal and 60px vertical distance between elements
- **Align to grid** — All element x/y coordinates must be multiples of 10
- **Orthogonal routing** — Use `edgeStyle=orthogonalEdgeStyle;rounded=1` for all edges
- **Multiple edges to same element** — When multiple edges connect to the same element, use different connection points with `entryX`/`entryY` and `exitX`/`exitY` attributes (values 0–1) to avoid overlaps
- **Element width** — Width is dynamically calculated based on text length: min 120 (rectangles), min 140 (pentagons), min 60 (person), max 280. Formula: `max(min_width, min(len(text) * 8 + 20, 280))` rounded up to nearest 10

## EDGY Facet Model Layout (facet: all)

When the diagram contains all three facets (`facet: all`), elements are placed in three vertical columns with **adaptive column widths**. Column positions are dynamically calculated based on the widest element or subtree in each column, ensuring tree hierarchies don't overflow into adjacent columns.

```
Identity col     Organisation     Architecture col    Product      Experience col
┌──────────┐    ┌──────────┐     ┌──────────┐       ┌──────────┐ ┌──────────┐
│ Purpose  │    │          │     │Capability│       │          │ │  Task    │
│ Content  │    │          │     │  Asset   │       │          │ │  Channel │
│  Story   │    │          │     │  Process │       │          │ │  Journey │
└──────────┘    └──────────┘     └──────────┘       └──────────┘ └──────────┘
                ┌──────────┐                        ┌──────────┐
                │ Org (ID  │                        │ Product  │
                │ ↔ Arch)  │                        │(Arch↔Exp)│
                └──────────┘                        └──────────┘
                                 ┌──────────┐
                                 │  Brand   │
                                 │ (ID↔Exp) │
                                 └──────────┘
```

**Column sizing:** Each column's width = `max(240, widest_element, widest_subtree)`. Columns are separated by a 60px gap. Intersection elements are positioned adaptively between the columns they bridge.

## Map Types

When `map_type` is set, it overrides the `facet` layout and uses the map type's own layout. Sixteen map types map to four reusable layout strategies, derived from the official EDGY 23 example maps in `examples/official/` (decoded reference at `examples/official/decoded/PATTERNS.md`).

| Map Type | Layout strategy | Min elements | Recommended | Primary element type |
|----------|-----------------|-------------:|------------:|----------------------|
| `capability` | grid + tree | 8 | 15–30 | capability |
| `organisation` | tree (top-down) | 8 | 15–30 | organisation |
| `outcome` | grid + tree | 5 | 7–10 | outcome |
| `journey` | sequence (left → right) | 4 | 6–8 | journey |
| `activity` | sequence | 4 | 6–8 | activity |
| `process` | sequence | 4 | 6–8 | process |
| `purpose` | hub-and-spoke | 6 | 10–15 | purpose |
| `brand` | hub-and-spoke | 5 | 7–10 | brand |
| `product` | hub-and-spoke | 6 | 10–15 | product |
| `object` | hub-and-spoke | 5 | 7–10 | object |
| `asset` | grid | 5 | 7–10 | asset |
| `channel` | grid | 8 | 15–30 | channel |
| `content` | grid | 6 | 10–15 | content |
| `people` | grid | 8 | 15–30 | people |
| `story` | grid | 6 | 10–15 | story |
| `task` | grid | 8 | 15–30 | task |

**Layout strategies:**

- **grid** — adaptive rows × columns, `cols ≈ sqrt(N)`, 130×60 leaves with 20px gap. Suits taxonomies, persona panels, content catalogues.
- **tree** — first element becomes the root at the top centre; tree-relationship edges (`contains`, `comprises`, `decomposes`) drive the descent. Suits org charts, capability decomposition, outcome chains.
- **sequence** — single horizontal row of pentagon arrows, 140×80 each. Suits journey stages, activity flows, process steps.
- **hub-and-spoke** — first element at the centre, others on a circle whose radius scales with N. Suits a single anchor element (purpose, brand, product, object) surrounded by its supporting elements.

The `edgy-deep-dive` skill generates **pairwise diagrams via direct XML
authoring** (not through `edgy_parser.py`). Layout rules and the XML pattern
are documented in the [Pairwise Map](#pairwise-map) section below as a
specification reference for that skill.

**Element-count thresholds:** below the `Min elements` value the diagram looks too sparse compared to the official EDGY 23 examples — the parser logs a warning. Use the `Recommended` range as the target.

### Map Type Patterns

Concrete input/output sketches per layout strategy. Pick the one that matches your `map_type`.

#### Grid (capability, asset, channel, content, people, story, task, outcome)

```
map_type: capability
elements:
  - capability: "IT Services"
  - capability: "Application Development" [in-house, differentiating]
  - capability: "Infrastructure" [outsourced, commodity]
  - capability: "Security" [in-house]
  - capability: "Data & Analytics"
  - capability: "Customer Support"
relationships:
  - "IT Services" -> "Application Development": "contains"
  - "IT Services" -> "Infrastructure": "contains"
  - "IT Services" -> "Security": "contains"
```

ASCII layout:
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ IT Services  │ │ App Dev      │ │ Infrastructure│
└──────────────┘ └──────────────┘ └──────────────┘
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Security     │ │ Data         │ │ Cust Support │
└──────────────┘ └──────────────┘ └──────────────┘
```

#### Tree (organisation)

```
map_type: organisation
elements:
  - organisation: "Group HQ"
  - organisation: "Operations"
  - organisation: "Engineering"
  - organisation: "Customer"
  - organisation: "Region North"
  - organisation: "Region South"
relationships:
  - "Group HQ" -> "Operations": "contains"
  - "Group HQ" -> "Engineering": "contains"
  - "Group HQ" -> "Customer": "contains"
  - "Operations" -> "Region North": "contains"
  - "Operations" -> "Region South": "contains"
```

ASCII layout:
```
                ┌───────────┐
                │ Group HQ  │
                └─────┬─────┘
        ┌─────────────┼─────────────┐
   ┌────┴────┐  ┌─────┴─────┐ ┌─────┴────┐
   │ Operations│ │Engineering│ │ Customer │
   └────┬─────┘  └───────────┘ └──────────┘
   ┌────┴────┐
   │Region N  │
   └─────────┘
```

#### Sequence (journey, activity, process)

```
map_type: journey
elements:
  - journey: "Consider travelling"
  - journey: "Explore options"
  - journey: "Plan trip"
  - journey: "Book tickets"
  - journey: "Travel"
  - journey: "Arrival"
```

ASCII layout:
```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Consider│▶│Explore│▶│Plan │▶│Book  │▶│Travel│▶│Arrive│
└──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘
```

#### Hub-and-spoke (purpose, brand, product, object)

```
map_type: brand
elements:
  - brand: "Nordic Trains"
  - story: "From rural rail to high-speed network"
  - content: "Underpromise, overdeliver"
  - task: "Buy ticket"
  - journey: "First-time traveller"
  - product: "Smart booking app"
relationships:
  - "Nordic Trains" -> "From rural rail to high-speed network": "evokes"
  - "Nordic Trains" -> "Underpromise, overdeliver": "represents"
  - "Nordic Trains" -> "Buy ticket": "supports"
```

ASCII layout:
```
                ┌──────────┐
                │  Story   │
                └──────────┘
       ┌──────────┐         ┌──────────┐
       │ Content  │         │ Journey  │
       └──────────┘         └──────────┘
                ┌──────────┐
                │  Brand   │  ← hub
                └──────────┘
       ┌──────────┐         ┌──────────┐
       │  Task    │         │ Product  │
       └──────────┘         └──────────┘
```

### Pairwise Map

> **Note:** Pairwise diagrams are not produced by `edgy_parser.py`. This
> section is the specification that the `edgy-deep-dive` skill follows when
> authoring `.drawio` XML directly.

The pairwise layout is designed for **edgy-deep-dive** outputs. It visualises
the relationship between 2–3 focus elements together with their immediate
(1-hop) neighbours, making dependencies and gaps visually explicit.

**TXT input format:**

Pairwise overrides the layout but the `facet` field is still required (it
defines the base palette and shape inheritance for the focus elements). Pick
the facet that best matches the focus elements (`all` is fine for cross-facet
pairs).

```
facet: architecture
map_type: pairwise
focus: [capability, organisation]

elements:
  - capability: "Capability name - Description" [focus]
  - organisation: "Organisation name - Description" [focus]
  - process: "Process name - Description"

relationships:
  - "organisation" -> "capability": "omistaa"
  - "organisation" -> "process": "suorittaa"
  - "process" -> "capability": "toteuttaa"
```

Rules:
- Elements tagged `[focus]` are the primary subject of the analysis
- Non-focus elements are neighbours (connected via a 1-hop link to at least one focus element)
- Maximum 8 elements total (2–3 focus + up to 5 neighbours)

**Pairwise layout:**

```
   Column A (focus[0])          Column B (focus[1])
   ┌──────────────────┐         ┌──────────────────┐
   │   Capability     │◄────────│  Organisation    │
   │   [focus, bold]  │ omistaa │  [focus, bold]   │
   └──────────────────┘         └─────────┬────────┘
         ▲                                │ suorittaa
         │ toteuttaa                      ▼
         └──────────────── Process ───────┘
                          (neighbour)
```

**mxCell rules for pairwise:**

- Focus elements: `strokeWidth=4` (bold border), normal EDGY colour for their element type
- Neighbour elements: `strokeWidth=2` (normal border), normal EDGY colour
- Direct core links (1-hop): solid arrow `endArrow=classic;endFill=1;strokeWidth=2`
- 2-hop paths through a neighbour: dashed connector `dashed=1;strokeWidth=1;strokeColor=#888888` from focus A to focus B with the intermediate element's name as edge label
- Layout: focus element A at x=80, focus element B at x=600; neighbours placed between (x=340) or to the outside depending on connectivity
- Minimum 120px vertical separation between elements

**Pairwise example XML:**

```xml
<!-- Focus element A — capability (blue, bold border) -->
<mxCell id="2" value="Cloud-arkkitehtuuri - AWS/Azure multi-cloud"
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#fff;strokeWidth=4;arcSize=30;fontStyle=1;fontSize=12;"
  vertex="1" parent="1">
  <mxGeometry x="80" y="200" width="200" height="70" as="geometry"/>
</mxCell>

<!-- Focus element B — organisation (cyan, bold border) -->
<mxCell id="3" value="Globex Oy - Toiminnallinen rakenne"
  style="rounded=0;whiteSpace=wrap;html=1;fillColor=#80eaff;strokeColor=#fff;strokeWidth=4;fontStyle=1;fontSize=12;"
  vertex="1" parent="1">
  <mxGeometry x="600" y="200" width="200" height="70" as="geometry"/>
</mxCell>

<!-- Neighbour — process (blue, normal border) -->
<mxCell id="4" value="Projektitoimitusmalli - Agile delivery"
  style="shape=mxgraph.arrows2.arrow;dy=0.6;dx=20;notch=0;whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#fff;strokeWidth=2;fontStyle=1;fontSize=12;"
  vertex="1" parent="1">
  <mxGeometry x="340" y="360" width="200" height="70" as="geometry"/>
</mxCell>

<!-- Direct link: organisation omistaa capability -->
<mxCell id="10" value="omistaa"
  style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;endArrow=classic;endFill=1;"
  edge="1" source="3" target="2" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>

<!-- 2-hop path: organisation → process → capability (dashed) -->
<mxCell id="11" value="suorittaa → toteuttaa"
  style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=1;fontSize=10;endArrow=open;endFill=0;dashed=1;strokeColor=#888888;"
  edge="1" source="3" target="2" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## Error Handling

- **Unknown element type** → Use white rectangle: `fillColor=#ffffff;strokeColor=#262626`
- **Relationship source/target not found** → Skip relationship and warn user
- **Missing facet value** → Default: `identity`

## Format Selection

Check user request for format preference:
- `/edgy-diagram identity: company purpose` → `identity.drawio`
- `/edgy-diagram png: architecture` → `architecture.drawio.png`
- `/edgy-diagram svg: experience` → `experience.drawio.svg`
- `/edgy-diagram pdf: full-edgy-map` → `full-edgy-map.drawio.pdf`

## Export Presets

Use `--preset` to apply ready-made export settings:

| Preset | Format | Käyttötarkoitus | CLI-argumentit |
|--------|--------|------------------|----------------|
| `presentation` | PNG | Esitykset (1920×1080, 150 DPI) | `--width 1920 --scale 1.5 -b 20` |
| `print` | PDF | Tulostettava (A3, 300 DPI) | `--scale 3.0 -b 30` |
| `web` | SVG | Läpinäkyvä tausta web-julkaisuun | `-t -b 10` |

Esimerkki: `python3 edgy_generator.py input.txt --preset presentation --output slide.png`

## PlantUML output

EDGY-kaaviot voi tuottaa myös PlantUML-lähdetiedostona käyttämällä
plantuml-stdlib:n virallista `<edgy/edgy>`-kirjastoa
(https://plantuml.com/stdlib#7c3d1cde3762ae3b). PlantUML on tekstipohjainen
ja versionhallintaystävällinen — sopii diagram-as-code-workflowihin, CI/CD-
pipeineihin ja IDE-previewiin ilman draw.io-binääriä.

**Milloin käyttää:**
- Kaavio commitoidaan repoon ja diff:n halutaan pysyvän luettavana
- IDE-plugin (VS Code / IntelliJ) renderöi kaavion editorissa
- CI render Krokilla tai PlantUML-jar:lla ilman headless draw.io:ta

**Käyttö:**

```bash
# pelkkä .puml-lähdetiedosto, ei riippuvuuksia
python scripts/edgy_generator.py examples/purpose-map.txt \
    --format plantuml --output purpose.puml

# render PNG/SVG/PDF PlantUML-engineä käyttäen
python scripts/edgy_generator.py examples/purpose-map.txt \
    --format png --engine plantuml --output purpose.png
```

PNG/SVG/PDF-render vaatii joko `plantuml.jar`:n (osoitettu
`PLANTUML_JAR`-ympäristömuuttujalla tai sijoitettu vakiopolulle) tai
`plantuml`-binaarin PATHista. Jos kumpaakaan ei löydy, `.puml`-lähde
kirjoitetaan silti ja varoitus tulostuu.

**Mapping EDGY → PlantUML-makrot:**

| EDGY-elementti | PlantUML-makro |
|---|---|
| purpose, content, story, capability, asset, process, task, channel, journey | `$purpose(...)`, `$content(...)`, ... |
| brand, product, organisation | `$brand(...)`, `$product(...)`, `$organisation(...)` |
| people, activity, object, outcome | `$people(...)`, `$activity(...)`, `$object(...)`, `$outcome(...)` |
| Core link / influence | `$link(a, b, "label")` |
| Flow relationship | `$flow(a, b, "label")` |
| Tree relationship | `$tree(a, b, "label")` |

PlantUML auto-layoutaa elementit — pikselikoordinaatteja ei tarvita.
Element-ID:t (`purpose1`, `capability2`, ...) säilyvät identtisinä draw.io-
ulostulon kanssa.

**Esimerkki:** `examples/expected-purpose.puml`

## Viralliset EDGY 23 -resurssit

Skillin mukana toimitetaan viralliset EDGY 23 -resurssit:
- `assets/stencils/EDGY_23_drawio_stencils.xml` — draw.io stencil -kirjasto.
  Lataa draw.io:hon: **File → Open Library...** ja valitse tiedosto. Tämän
  jälkeen viralliset EDGY-muodot löytyvät shapes-paneelista.
- `assets/stencils/svg/Shape-*.svg` — yksittäiset SVG-muodot (Purpose, Content,
  Story, Capability, jne.) sekä facet-ikonit (Identity/Architecture/Experience).
- `examples/official/*.drawio.xml` — 16 virallista esimerkkikarttaa (capability,
  journey, purpose, task, process, brand, …) referenssiksi.

Parser tuottaa suoraan virallisen EDGY 23 -väripaletin ja muodot (pyöristetyt
kulmat, valkoinen reunus, facet-värit) jotka vastaavat virallisten esimerkki-
karttojen tyyliä, joten stencil-kirjaston lataaminen draw.io:hon on tarpeen
vain silloin kun käyttäjä muokkaa kaaviota manuaalisesti draw.io:ssa.

## draw.io CLI

Export command: `drawio -x -f <format> -e -b 10 -o <output> <input.drawio>`

| Location | Path |
|----------|------|
| macOS | `/Applications/draw.io.app/Contents/MacOS/draw.io` |
| Linux | `drawio` (in PATH) |
| Windows | `"C:\Program Files\draw.io\draw.io.exe"` |

## Dependencies

- Python 3.7+ and `xml.etree.ElementTree` (standard library)
- draw.io CLI (for draw.io export to png/svg/pdf)
- PlantUML (`plantuml.jar` + Java, or `plantuml` binary) — optional, only
  required when rendering PlantUML output to png/svg/pdf. `.puml` source
  generation has no extra dependencies.
