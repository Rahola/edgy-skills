---
name: edgy-framework
version: "1.2.1"
description: >
  EDGY 23 enterprise design analysis: challenge reframing, facet intersection analysis,
  and element identification from natural language.
category: architecture
tags: [edgy, enterprise-design, architecture, analysis, reframing, fi, en, fr, de]
languages: [fi, en, fr, de]
agents:
  - claude-code
  - cursor
  - generic
inputs:
  - name: mode
    type: enum
    values: [reframing, intersection, identify]
    description: >
      Analysis mode: reframing (challenge reframing), intersection (coherence check),
      identify (element identification)
  - name: challenge
    type: text
    description: Challenge, business description, or analysis subject in natural language
  - name: language
    type: enum
    values: [fi, en, fr, de]
    default: fi
outputs:
  - type: markdown
    description: Structured EDGY analysis in markdown format
---

# EDGY Framework Analysis Skill

## Purpose

This skill analyses enterprise challenges, business descriptions, and architectural decisions using the EDGY 23 language. It helps broaden perspectives from a single problem to holistic enterprise design.

Use this skill when:
- You want to reframe a challenge through EDGY facets (reframing)
- You need a coherence check at Organisation/Product/Brand intersections
- You want to identify EDGY elements from natural language

For visualisation, use the **edgy-diagram** skill.

**IMPORTANT:** Produce all output in the language specified by the `language` parameter (default: fi). Use the corresponding language column from the question matrix and output template below.

## Agent Instructions

### Mode 1: Reframing (Challenge Reframing)

When the user provides a challenge (e.g. "This train is too slow"), expand it to all 12 EDGY elements:

1. **Identify the original challenge** and its apparent facet
2. **Ask questions about each element** — what the challenge has to do with each element
3. **Identify hidden connections** — how the challenge affects different facets
4. **Propose an expanded perspective** — what is the true scope of the challenge

#### Reframing Question Matrix

For each challenge, use the question from the selected language column:

| Facet | Element | FI | EN | FR | DE |
|-------|---------|----|----|----|----|
| Identity | Purpose | Miten tämä liittyy yrityksen olemassaolon tarkoitukseen? | How does this relate to the organisation's reason for being? | Comment cela se rapporte-t-il à la raison d'être de l'organisation ? | Wie hängt das mit dem Daseinszweck der Organisation zusammen? |
| Identity | Story | Miten tämä vaikuttaa tarinaamme? Mitä kerromme tästä? | How does this affect our story? What do we tell about this? | Comment cela affecte-t-il notre histoire ? Qu'en disons-nous ? | Wie wirkt sich das auf unsere Geschichte aus? Was erzählen wir darüber? |
| Identity | Content | Mitä viestimme tästä? Miten kommunikoimme muutoksen? | What do we communicate about this? How do we convey the change? | Que communiquons-nous à ce sujet ? Comment transmettons-nous le changement ? | Was kommunizieren wir darüber? Wie vermitteln wir die Veränderung? |
| Architecture | Capability | Mitä kyvykkyyksiä tarvitaan? Puuttuuko jotain? | What capabilities are needed? Is anything missing? | Quelles capacités sont nécessaires ? Manque-t-il quelque chose ? | Welche Fähigkeiten werden benötigt? Fehlt etwas? |
| Architecture | Process | Mitkä prosessit ovat osallisia? Mitä pitää muuttaa? | Which processes are involved? What needs to change? | Quels processus sont impliqués ? Que faut-il changer ? | Welche Prozesse sind beteiligt? Was muss geändert werden? |
| Architecture | Asset | Mitä resursseja/järjestelmiä tämä koskee? | What resources/systems does this concern? | Quelles ressources/systèmes sont concernés ? | Welche Ressourcen/Systeme sind betroffen? |
| Experience | Task | Mitä tehtäviä ihmisillä on? Miten haaste vaikuttaa niihin? | What tasks do people have? How does the challenge affect them? | Quelles tâches les gens ont-ils ? Comment le défi les affecte-t-il ? | Welche Aufgaben haben die Menschen? Wie wirkt sich die Herausforderung auf sie aus? |
| Experience | Journey | Miten tämä näkyy asiakasmatkoissa? | How does this manifest in customer journeys? | Comment cela se manifeste-t-il dans les parcours clients ? | Wie zeigt sich das in den Customer Journeys? |
| Experience | Channel | Missä kanavissa tämä koetaan? | In which channels is this experienced? | Dans quels canaux cela est-il vécu ? | In welchen Kanälen wird das erlebt? |
| Intersection | Organisation | Miten organisaatio on järjestäytynyt tämän suhteen? | How is the organisation structured regarding this? | Comment l'organisation est-elle structurée à cet égard ? | Wie ist die Organisation diesbezüglich aufgestellt? |
| Intersection | Product | Mitkä tuotteet/palvelut liittyvät? | Which products/services are related? | Quels produits/services sont concernés ? | Welche Produkte/Dienstleistungen sind betroffen? |
| Intersection | Brand | Miten tämä vaikuttaa brändiimme ja maineeseen? | How does this affect our brand and reputation? | Comment cela affecte-t-il notre marque et notre réputation ? | Wie wirkt sich das auf unsere Marke und unseren Ruf aus? |

### Mode 2: Intersection (Intersection Analysis)

Analyse coherence at three intersection points:

#### Organisation = Identity ∩ Architecture

| FI | EN | FR | DE |
|----|----|----|-----|
| Miten organisoidumme tiimeinä? Miten teemme yhteistyötä? | How do we organise as teams? How do we collaborate? | Comment nous organisons-nous en équipes ? Comment collaborons-nous ? | Wie organisieren wir uns als Teams? Wie arbeiten wir zusammen? |

Check: Does the organisational structure support capabilities? Does the organisation pursue its purpose?
Official links: organisation pursues purpose, organisation authors story, organisation has capability, organisation performs process

#### Product = Architecture ∩ Experience

| FI | EN | FR | DE |
|----|----|----|-----|
| Mitä teemme ja tarjoamme ihmisille? Mikä on työmme tulos? | What do we make and offer to people? What is the result of our work? | Que faisons-nous et offrons-nous aux gens ? Quel est le résultat de notre travail ? | Was machen und bieten wir den Menschen an? Was ist das Ergebnis unserer Arbeit? |

Check: Do products serve people's tasks? Do products require the right capabilities?
Official links: product requires capability, process creates product, product serves task, product features in journey

#### Brand = Identity ∩ Experience

| FI | EN | FR | DE |
|----|----|----|-----|
| Miten meidät koetaan? Mikä on maineemme ja imagomme? | How are we perceived? What is our reputation and image? | Comment sommes-nous perçus ? Quelle est notre réputation et notre image ? | Wie werden wir wahrgenommen? Was ist unser Ruf und unser Image? |

Check: Does the brand reflect the purpose? Do experiences support the brand promise?
Official links: brand represents purpose, brand evokes story, brand supports task, brand appears in journey

#### Coherence Check

For each intersection point, evaluate:

| FI | EN | FR | DE |
|----|----|----|-----|
| Linjakkuus | Alignment | Alignement | Ausrichtung |
| Ristiriidat | Contradictions | Contradictions | Widersprüche |
| Puutteet | Gaps | Lacunes | Lücken |
| Suositus | Recommendation | Recommandation | Empfehlung |

### Mode 3: Identify (Element Identification)

When the user provides a business description:

1. **Read the description** and identify EDGY elements
2. **Classify elements** by type (purpose, capability, task, etc.)
3. **Propose core links** — which of the 24 official core links apply. Each verb is valid only for its listed (source → target) pair. When no core link fits a pair, use an influence verb from the edgy-diagram skill's vocabulary (dashed line) — never invent a new Link
4. **Provide edgy-diagram input** — ready input for diagram generation

#### Official 24 EDGY Core Links

<!-- edgy-links:begin format=flat4-fi -->
| Source → Target | FI | EN | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| story → purpose | kontekstualisoi | contextualises | contextualise | kontextualisiert |
| content → purpose | ilmaisee | expresses | exprime | drückt aus |
| content → story | välittää | conveys | transmet | vermittelt |
| brand → story | herättää | evokes | évoque | evoziert |
| brand → purpose | edustaa | represents | représente | repräsentiert |
| capability → asset | vaatii | requires | nécessite | erfordert |
| process → capability | toteuttaa | realises | réalise | realisiert |
| process → asset | vaatii | requires | nécessite | erfordert |
| product → capability | vaatii | requires | nécessite | erfordert |
| process → product | luo | creates | crée | erzeugt |
| task → journey | on osa | is part of | fait partie de | ist Teil von |
| task → channel | käyttää | uses | utilise | nutzt |
| journey → channel | kulkee | traverses | traverse | durchläuft |
| brand → task | tukee | supports | soutient | unterstützt |
| brand → journey | näkyy | appears in | apparaît dans | erscheint in |
| organisation → purpose | tavoittelee | pursues | poursuit | verfolgt |
| organisation → story | kirjoittaa | authors | rédige | verfasst |
| organisation → capability | omistaa | has | possède | besitzt |
| organisation → process | suorittaa | performs | exécute | führt aus |
| product → task | palvelee | serves | sert | bedient |
| product → journey | esiintyy | features in | figure dans | erscheint in |
| organisation → brand | rakentaa | builds | construit | baut auf |
| organisation → product | valmistaa | makes | fabrique | stellt her |
| product → brand | ilmentää | embodies | incarne | verkörpert |
<!-- edgy-links:end -->

## Output Templates

Use the output template matching the selected `language` parameter.

### Reframing Output

#### Finnish (fi)

```markdown
# EDGY Reframing: [Alkuperäinen haaste]

## Alkuperäinen näkökulma
[Minkä fasetin näkökulmasta haaste on alun perin esitetty]

## Laajennettu analyysi

### Identity
- **Purpose**: [Yhteys tarkoitukseen]
- **Story**: [Vaikutus tarinaan]
- **Content**: [Viestintätarpeet]

### Architecture
- **Capability**: [Kyvykkyystarpeet]
- **Process**: [Prosessivaikutukset]
- **Asset**: [Resurssitarpeet]

### Experience
- **Task**: [Tehtävävaikutukset]
- **Journey**: [Asiakasmatka]
- **Channel**: [Kanavat]

### Leikkaukset
- **Organisation**: [Organisaatiovaikutukset]
- **Product**: [Tuotevaikutukset]
- **Brand**: [Brändivaikutukset]

## Johtopäätös
[Haasteen todellinen laajuus ja suositellut toimenpiteet]
```

#### English (en)

```markdown
# EDGY Reframing: [Original Challenge]

## Original Perspective
[From which facet perspective was the challenge originally presented]

## Expanded Analysis

### Identity
- **Purpose**: [Connection to purpose]
- **Story**: [Impact on story]
- **Content**: [Communication needs]

### Architecture
- **Capability**: [Capability needs]
- **Process**: [Process impacts]
- **Asset**: [Resource needs]

### Experience
- **Task**: [Task impacts]
- **Journey**: [Customer journey]
- **Channel**: [Channels]

### Intersections
- **Organisation**: [Organisational impacts]
- **Product**: [Product impacts]
- **Brand**: [Brand impacts]

## Conclusion
[True scope of the challenge and recommended actions]
```

#### French (fr)

```markdown
# Recadrage EDGY : [Défi original]

## Perspective initiale
[De quelle perspective de facette le défi a-t-il été initialement présenté]

## Analyse élargie

### Identité
- **Purpose** : [Lien avec la raison d'être]
- **Story** : [Impact sur le récit]
- **Content** : [Besoins en communication]

### Architecture
- **Capability** : [Besoins en capacités]
- **Process** : [Impacts sur les processus]
- **Asset** : [Besoins en ressources]

### Expérience
- **Task** : [Impacts sur les tâches]
- **Journey** : [Parcours client]
- **Channel** : [Canaux]

### Intersections
- **Organisation** : [Impacts organisationnels]
- **Product** : [Impacts produit]
- **Brand** : [Impacts marque]

## Conclusion
[Portée réelle du défi et actions recommandées]
```

#### German (de)

```markdown
# EDGY-Reframing: [Ursprüngliche Herausforderung]

## Ursprüngliche Perspektive
[Aus welcher Facetten-Perspektive wurde die Herausforderung ursprünglich dargestellt]

## Erweiterte Analyse

### Identität
- **Purpose**: [Verbindung zum Daseinszweck]
- **Story**: [Auswirkung auf die Geschichte]
- **Content**: [Kommunikationsbedarf]

### Architektur
- **Capability**: [Fähigkeitsbedarf]
- **Process**: [Prozessauswirkungen]
- **Asset**: [Ressourcenbedarf]

### Erfahrung
- **Task**: [Auswirkungen auf Aufgaben]
- **Journey**: [Customer Journey]
- **Channel**: [Kanäle]

### Schnittstellen
- **Organisation**: [Organisatorische Auswirkungen]
- **Product**: [Produktauswirkungen]
- **Brand**: [Markenauswirkungen]

## Fazit
[Tatsächlicher Umfang der Herausforderung und empfohlene Maßnahmen]
```

### Intersection Output

#### Finnish (fi)

```markdown
# EDGY Intersektioanalyysi: [Kohde]

## Organisation (Identity ∩ Architecture)
- **Linjakkuus**: [Arvio]
- **Ristiriidat**: [Lista]
- **Puutteet**: [Lista]
- **Suositus**: [Toimenpide]

## Product (Architecture ∩ Experience)
- **Linjakkuus**: [Arvio]
- **Ristiriidat**: [Lista]
- **Puutteet**: [Lista]
- **Suositus**: [Toimenpide]

## Brand (Identity ∩ Experience)
- **Linjakkuus**: [Arvio]
- **Ristiriidat**: [Lista]
- **Puutteet**: [Lista]
- **Suositus**: [Toimenpide]

## Kokonaiskoherenssi
[Yhteenveto ja priorisoidut suositukset]
```

#### English (en)

```markdown
# EDGY Intersection Analysis: [Subject]

## Organisation (Identity ∩ Architecture)
- **Alignment**: [Assessment]
- **Contradictions**: [List]
- **Gaps**: [List]
- **Recommendation**: [Action]

## Product (Architecture ∩ Experience)
- **Alignment**: [Assessment]
- **Contradictions**: [List]
- **Gaps**: [List]
- **Recommendation**: [Action]

## Brand (Identity ∩ Experience)
- **Alignment**: [Assessment]
- **Contradictions**: [List]
- **Gaps**: [List]
- **Recommendation**: [Action]

## Overall Coherence
[Summary and prioritised recommendations]
```

#### French (fr)

```markdown
# Analyse d'intersection EDGY : [Sujet]

## Organisation (Identité ∩ Architecture)
- **Alignement** : [Évaluation]
- **Contradictions** : [Liste]
- **Lacunes** : [Liste]
- **Recommandation** : [Action]

## Produit (Architecture ∩ Expérience)
- **Alignement** : [Évaluation]
- **Contradictions** : [Liste]
- **Lacunes** : [Liste]
- **Recommandation** : [Action]

## Marque (Identité ∩ Expérience)
- **Alignement** : [Évaluation]
- **Contradictions** : [Liste]
- **Lacunes** : [Liste]
- **Recommandation** : [Action]

## Cohérence globale
[Résumé et recommandations priorisées]
```

#### German (de)

```markdown
# EDGY-Schnittstellenanalyse: [Gegenstand]

## Organisation (Identität ∩ Architektur)
- **Ausrichtung**: [Bewertung]
- **Widersprüche**: [Liste]
- **Lücken**: [Liste]
- **Empfehlung**: [Maßnahme]

## Produkt (Architektur ∩ Erfahrung)
- **Ausrichtung**: [Bewertung]
- **Widersprüche**: [Liste]
- **Lücken**: [Liste]
- **Empfehlung**: [Maßnahme]

## Marke (Identität ∩ Erfahrung)
- **Ausrichtung**: [Bewertung]
- **Widersprüche**: [Liste]
- **Lücken**: [Liste]
- **Empfehlung**: [Maßnahme]

## Gesamtkohärenz
[Zusammenfassung und priorisierte Empfehlungen]
```

### Identify Output

```markdown
# EDGY Element Identification: [Description Title]

## Identified Elements

| Element | Type | Facet |
|---------|------|-------|
| [name] | [type] | [facet] |

## Recommended Links

| Source → Target | Link |
|-----------------|------|
| [element] → [element] | [official core link] |

## Ready edgy-diagram Input

\```
facet: all
elements:
  - [type]: "[name]"
relationships:
  - "[source]" -> "[target]": "[link]"
\```
```

## Quality Requirements

### Minimum Element Counts (identify mode)

When producing an EDGY analysis in `identify` mode, the following minimum requirements apply:

| Facet | Element | Minimum | Requirement |
|-------|---------|---------|-------------|
| Identity | Purpose | 1 | At least 2 sentences + analysis |
| Identity | Story | 1 | At least 2 sentences + analysis |
| Identity | Content | 1 | At least 2 sentences + analysis |
| Architecture | Capability | 3 | Table: nature (differentiating/commodity) + level (core/supporting) |
| Architecture | Asset | 2 | Description + ownership + strategic significance |
| Architecture | Process | 2 | Description + how it realises capabilities |
| Experience | Task | 3 | Description + customer segment |
| Experience | Channel | 2 | Table: type + role |
| Experience | Journey | 1 | Visualisation (steps with arrows) |
| Intersection | Organisation | 1 | Coherence check mandatory |
| Intersection | Product | 1 | Coherence check mandatory |
| Intersection | Brand | 1 | Coherence check mandatory |

### Mandatory Sections (identify mode, full assessment)

- [ ] Section 1: Executive summary (min 3 sentences)
- [ ] Section 2: Identity facet (Purpose, Story, Content — each min 2 sentences)
- [ ] Section 3: Architecture facet (Capability table, Asset, Process)
- [ ] Section 4: Experience facet (Task, Channel table, Journey)
- [ ] Section 5: Intersection elements (Organisation, Product, Brand — each with coherence assessment)
- [ ] Section 6: Strengths (min 3 numbered, justified)
- [ ] Section 7: Development areas and gaps (min 3 subsections)
- [ ] Section 8: Recommendations table (#, Recommendation, EDGY element, Priority)
- [ ] Section 9: Diagrams (file listing)

### Minimum Output Length

Full assessment (identify mode, all facets): **at least 150 lines / 5,000 characters**.

### Anti-patterns — DO NOT do this

- **DO NOT write one-line descriptions for elements** — "Purpose: To provide services" is too shallow. Write at least 2 sentences + analysis of how the element differentiates or impacts.
- **DO NOT skip coherence checks** — Every intersection element (Organisation, Product, Brand) MUST include a coherence assessment (Strong/Good/Weak + justification).
- **DO NOT give generic recommendations** — "Improve digital services" fits any company. Recommendations MUST reference specific EDGY elements and be organisation-specific.
- **DO NOT leave tables empty** — Capability table MUST have nature/level classification. Recommendations table MUST have priority levels.
- **DO NOT write under 150 lines** — This means the analysis is too shallow.

## Examples

### Example 1: Reframing

**Input:** "Train tickets are too expensive"

**Output:**
- Purpose: Is low price part of our purpose? Or is our purpose sustainable transport?
- Capability: Is our pricing capability sound? Can we do dynamic pricing?
- Task: What is people's real task? "Travel cheaply" vs "Get there reliably"?
- Product: Should the product portfolio differentiate (basic/premium)?
- Brand: Do we want to be "cheap" or "valuable"?

See `examples/reframing-example.md` (Finnish) and `examples/reframing-example-en.md` (English) for full worked examples.

### Example 2: Intersection

**Input:** "Analyse Nordia Transit public transport service coherence"

**Output:** Intersection analysis at Organisation/Product/Brand intersection points, coherence check and recommendations.
