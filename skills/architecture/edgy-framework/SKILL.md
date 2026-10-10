---
name: edgy-framework
version: "1.5.0"
description: >
  EDGY 23 enterprise design analysis: challenge reframing, facet intersection analysis,
  element identification from natural language, and modelling guidance for strategy
  documents (strategy → Purpose/Outcome mapping), capability formulation and the
  organisation role model.
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
    values: [reframing, intersection, identify, target-state]
    description: >
      Analysis mode: reframing (challenge reframing), intersection (coherence check),
      identify (element identification), target-state (internal target-architecture
      artefacts: purpose map, capability cards, building-block hypothesis, role model)
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
| Base | Outcome | Mikä mitattava tulos muuttuu? Millä mittarilla tiedämme sen? | Which measurable result changes? Which metric tells us? | Quel résultat mesurable change ? Quel indicateur nous le dit ? | Welches messbare Ergebnis ändert sich? Welche Kennzahl zeigt es? |

Outcome is a **base element**, not one of the 12 facet elements — which is
why KPIs are easily forgotten. Always answer the Outcome row; it anchors the
challenge to something measurable.

#### Base element vocabulary

| Base element | FI | FR | DE | Used for |
|--------------|----|----|----|----------|
| People | ihmiset | personnes | Menschen | actors who create or use the enterprise |
| Activity | toiminta | activité | Aktivität | initiatives, work packages, anything that is done |
| Outcome | tulos | résultat | Ergebnis | KPIs, target levels, measurable results |
| Object | kohde | objet | Objekt | tangible or intangible structures |

Use these names in legends and diagrams in the chosen language so that base
elements read consistently next to the facet elements.

### Mode 2: Intersection (Intersection Analysis)

Analyse coherence at three intersection points:

#### Organisation = Identity ∩ Architecture

| FI | EN | FR | DE |
|----|----|----|-----|
| Miten organisoidumme tiimeinä? Miten teemme yhteistyötä? | How do we organise as teams? How do we collaborate? | Comment nous organisons-nous en équipes ? Comment collaborons-nous ? | Wie organisieren wir uns als Teams? Wie arbeiten wir zusammen? |

Check: Does the organisational structure support capabilities? Does the organisation pursue its purpose?
Official links: organisation pursues purpose, organisation authors story, organisation has capability, organisation performs process

**Role-model check** (the generic question above is often too broad in
architecture work). For every block, procurement or definition ask *who
steers, procures, defines, produces, operates and approves it*:

| Role (Process) | FI | Question |
|----------------|----|----------|
| steers | ohjaa | who decides funding and portfolio priority? |
| procures | hankkii | who runs the tender and owns the contract? |
| defines | määrittelee | who writes requirements and accepts delivery? |
| produces | tuottaa | who builds and integrates? |
| operates | operoi | who runs, supports and monitors? |
| approves | hyväksyy | who signs off go-live and changes? |

Record roles × blocks as `organisation → process: performs` links and render
them with `map_type: organisation` (role model layout). An optional
*load view* (team × phase, number of simultaneous responsibilities) shows
where one small team carries several blocks at once; the skill gives no
threshold — state the load and let the organisation judge. A role with no
actor, or an actor with no role, is a finding.

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

### Mode 4: Target-state (internal target-architecture work)

Use this mode when the subject is your own (or your client's) organisation
and the goal is a **target architecture and the path to it**, not an
outside-in assessment. Inputs are internal: strategy documents, meeting
notes, an existing current-state model, interviews. The Experience facet is
optional at this stage. The orchestrating skill `edgy-target-state` runs the
phases end to end; this mode defines the artefacts.

Every artefact cites EDGY element ids (`PUR-`, `OUT-`, `CAP-`, `BB-`, `WP-`),
so documents and diagrams cross-reference. Keep artefacts short (see Output
length by mode).

| # | Artefact | EDGY anchor | Diagram (edgy-diagram) |
|---|----------|-------------|------------------------|
| 1 | **Purpose map** — mission, vision, focus areas (sub-Purposes), KPIs (Outcomes) | Purpose, Outcome, Content, Story, Organisation, Brand | `map_type: purpose` |
| 2 | **Capability map + cards** — stable home of requirements; cards at area / building-block level | Capability (`group:` per area), Process, Asset | `map_type: capability` with `group:` |
| 3 | **Guardrails** — principles that constrain decisions, each justified by a Purpose or Outcome id | Purpose, Outcome | — |
| 4 | **Building-block hypothesis** — about ten blocks, no product names, each mirrored against capabilities, guardrails and Outcomes | Asset / Capability, transition overlay | `map_type: reference` (lanes, `{change: …}`) |
| 5 | **Work packages** — one block from current to target, exactly one Outcome each, options compared (incumbent continues / re-tender / new supplier / shared service) | Activity → Outcome | optional `map_type: summary` |
| 6 | **Decision records** — via an external ADR skill if available; otherwise the 40-line template below | referenced by id | — |
| 7 | **Role model** — who steers, procures, defines, produces, operates, approves each block; optional load view | Organisation → Process `performs` | `map_type: organisation` |
| 8 | **Stakeholder summary** — who / does what / what results, 3–4 boxes, one paragraph | Organisation, Process, Outcome | `map_type: summary` |

**Capability card** (≤ 1 page):

```markdown
## CAP-05 Ticketing
**Area:** 2 Fares and ticketing · **Level:** 2 · **Nature:** differentiating · **Sourcing:** in-house
**What must be possible:** sell and validate fares in every channel, independent of supplier.
**Requirements:** R-1 … (functional) · Q-1 … (quality: availability, latency, accessibility)
**Data owned / master:** fare products (master: this capability); customer identity (master: CAP-01)
**Current implementer(s):** AST-01 Legacy fare engine (since 2014)
**Change pressure:** contract ends 2027; open-loop payments; account-based travel
**Measured by:** OUT-02 single ticket covers 95 % of trips
**Guardrails:** G-3 one master per data set · G-5 open interfaces
```

**Building-block mirror table** (one row per block):

| Block | Covers capabilities | Guardrails tested | Outcomes served | Change | Open decision |
|-------|---------------------|-------------------|-----------------|--------|---------------|
| BB-02 Account-based ticketing platform | CAP-03, CAP-05, CAP-06 | G-3 ✓ G-5 ✓ G-7 ? | OUT-02, OUT-03 | new | ADR-004 open-loop gateway |

**Work package card** (≤ 20 lines): scope (one block), Outcome (one id),
options A–D with the incumbent always as one option, dependencies, deadline,
decision needed by.

**Decision record** (≤ 40 lines, when no ADR skill is available): context,
options considered (including rejected ones and why), decision, consequences,
EDGY ids affected.

**Anti-patterns:** product names in building blocks; a work package with two
Outcomes or none; cards per level-2 leaf; a guardrail without a Purpose or
Outcome justification; padding any artefact to a length.

### Mapping strategy documents to EDGY

Strategy material (mission, vision, focus areas, KPIs, initiatives) maps to
EDGY as follows. The most common mistake is modelling strategic focus areas
as Story — they are **sub-Purposes**.

| Document part | EDGY element | Note |
|---------------|--------------|------|
| Mission, reason for being | Purpose (top level) | one |
| Vision | Purpose (top level) | separate, same level as the mission |
| Strategic focus areas / themes | Purpose (sub level) | purpose-map hierarchy: `mission contains focus area` — **never Story** |
| KPIs, target levels | Outcome (base) | under the focus area they measure: `KPI measures focus area`; target value in the subtext |
| Initiatives, actions, programmes | Activity (base) → work package | exactly one Outcome each |
| Values, promises, principles | Content | `content expresses purpose` |
| History, narrative, brochure text | Story | `story contextualises purpose` |
| Board, units, teams | Organisation | `organisation pursues purpose`, `authors story`, `performs process` |
| Service name, brand | Brand | `brand represents purpose` |

Render with `edgy-diagram` `map_type: purpose` (hierarchy layout; see the
input file *purpose-hierarchy-map.txt* among that skill's example inputs). Use `{id: PUR-01}` /
`{id: OUT-01}` so documents can cross-reference the elements.

**Anti-patterns:** focus areas as Story; KPIs left out because Outcome is a
base element; initiatives without an Outcome; a purpose map that is a
hub-and-spoke of slogans instead of a hierarchy.

### Formulating capabilities

A capability map is the **stable** side of target-state work: what the
enterprise must be able to do, and how well, independent of any system or
supplier. It changes only when the environment adds or removes a capability.

It has three uses:

1. **Home of requirements** — a requirement is written against a capability,
   never against a system.
2. **Coverage test** — when a solution is proposed, walk the map: every
   capability has an implementer, every piece of data has exactly one master.
3. **Situational picture** — current systems, change pressure and cost, one
   area at a time.

It is **not the unit of work**. Decisions and procurements are made on
building blocks (about ten); cards are written at that level; the map's leaves
are the cards' table of contents and checklist — not sixty documents. One
system spanning several capabilities is normal and often desirable; two
systems on one capability without a master decision is the problem.

Inside EDGY the card content is the architecture triad: capability = *what*,
`process realises capability` = *how it is done*, `capability requires asset`
= *with what*. A future capability (e.g. agent-based self-service) is modelled
the same way: asset = the service exposed to agents, process = how tools are
distributed.

**Helper questions when formulating a capability**

1. What must still be possible if the supplier changes tomorrow? (system independence)
2. Who suffers if it is missing — customer, driver, planner, finance? (business grounding)
3. State the result, not the doing: a noun ("travel account management"), not a verb ("we manage travel accounts").
4. Could it be procured separately? If yes, it is probably at the right level.
5. Which data does it own, and who is the master?
6. Which metric tells us it is good enough? (links to an Outcome)
7. Differentiating or commodity? In-house or outsourced? (the `[tags]` in edgy-diagram)
8. Which guardrail or principle constrains it? (links to the decision log)

**Granularity:** level 1 = 6–12 areas; level 2 = 40–80 capabilities; cards
and decisions at level 1 or building-block level. Render with `edgy-diagram`
`map_type: capability` and `group:` per area (see *capability-areas-map.txt* among that skill's example inputs).

**Anti-patterns:** naming capabilities after products or systems; one card
per level-2 leaf; a map that changes every time a system changes; mixing
processes ("we do X") into the capability list. `edgy_semantic_review.py`
asks about the first and the last of these on every map: S007 (system, tool
or unit as a capability), S008 (verb phrase), S009 (project or dated change
as a capability).

**Maturity and heat maps.** Status is an extension, never a fill colour:
`{maturity: 1–5}` or `{rating: differentiating}` on the capability draws a
badge with its own legend row (edgy-diagram, *status badges*). Say where the
rating comes from (interview, self-assessment, analysis) in the report.

### Formulating tasks, outcomes and the Experience facet

The Experience facet is the outside-in view: what people want to get done,
where they do it and how their journey unfolds. It goes wrong in the same
way every time — the organisation describes its own work and calls it the
customer's.

**Journey** — the stages a person goes through, in their order, named from
their side ("Plan a trip", "Travel", "Get help"), 5–8 stages. Stages are the
columns of a task map (`stages:`) and of a touchpoint matrix (`columns:`).

**Task** — what one person wants to get done at a stage, in their words:
"Get my money back", not "Process customer refund"; "Know when my bus
comes", not "Publish real-time data". Helper questions:

1. Who says this sentence — the person or an employee? (if an employee: it is a Process or Activity)
2. Would the person recognise the task without knowing the organisation? (system independence)
3. Is it one goal, not a sequence of steps? (steps are a journey or a process)
4. Which stage does it belong to (`{stage: …}`)? A task without a stage often has no customer.

**Channel** — where the interaction happens; classify every channel on two
axes, *physical / digital* and *synchronous / asynchronous* (the official
channel map, `rows:` × `columns:` in edgy-diagram), so gaps show as empty
cells.

**Touchpoint matrix** — journey stages as columns, channels or people as
rows, tasks in the cells: it shows which stage is served by which channel
and where a person is left alone.

**Outcome** — a verifiable result or changed state ("Shorter waiting times",
"More night-train passengers"), never an action ("Implement CRM"). Give it a
measure when one exists (`{kpi: …}`) and say whether the target is confirmed
or proposed (`{status: …}`); an outcome web links outcomes with influence
verbs (`enables`) from cause to effect.

`edgy_semantic_review.py` asks S010 when a task is phrased from the
organisation's side, S011 when an outcome is an action and S012 (a hint)
when an outcome has no measure while others on the page do. It flags; a
reviewer decides.

### Purpose map semantic review

A purpose map can be structurally and visually clean and still wrong: a
delivery in the field modelled development *measures* as Purposes, mixed
confirmed metrics with proposed ones and asserted `contains` hierarchies
that were really influences — and no linter noticed, because none of that is
notation. Before a purpose map is delivered, a reviewer (not a tool) answers
these questions; `edgy-diagram/scripts/edgy_semantic_review.py` (or
`edgy_generator.py --semantic-review`) raises the likely ones as S001–S006,
with the reason and the question — it flags, it never decides.

| # | Check | Rule of thumb |
|---|-------|---------------|
| 1 | **Purpose = why / what value is sought.** A lasting target state or reason to exist. | A name that starts with a task verb (develop, implement, build, deploy, introduce, roll out; kehittää, toteuttaa, rakentaa, ottaa käyttöön …) is an action, not a purpose. Ask what value the action serves and name *that*; the action goes to a Capability, Process or a roadmap item. (S001) |
| 2 | **Outcome = verifiable result.** Separate the result from its metric and say whether the metric is **confirmed** by the organisation or **proposed** by the analysis. Never invent target values. | `{status: confirmed}` / `{status: proposed}` on every Outcome; every Outcome `measures` a named Purpose. (S002, S003) |
| 3 | **Capability / Process / Task = with what / how.** Development measures belong here or in a separate roadmap, not in the purpose tree. | A purpose whose children are projects is a roadmap in disguise. |
| 4 | **Hierarchy is a claim.** Each `contains` asserts a part-of relationship; if the child merely *supports* or *influences* the parent, use an influence verb (dashed). | S005 hints where a contained element is itself an action or a metric. |
| 5 | **Provenance.** Say separately what is confirmed from public sources, what is an analytical interpretation and what is a proposal. | Tag every Purpose `[confirmed]`, `[analytical]` or `[proposed]` (fi: vahvistettu / analyyttinen / ehdotettu; fr/de equivalents); Outcomes carry `{status: …}` (row 2); other elements may be tagged, the review does not require it. (S004) |
| 6 | **Presentation language.** Relationship labels and the legend appear in the map's `language:`; the model keeps the canonical verb codes. | `language: fi` → `sisältää`, not `contains`. |

The review ends with an explicit sign-off that the assessment report (section
9) and the delivery note carry verbatim, in the report's language:

```
Semantic review: approved by <role>, <date> — S-findings answered: <n>
```

The edgy-assessment templates (section 9) carry the Finnish, French and
German equivalents of this line; those are valid sign-offs in a localised
report. A run with zero findings is **not** an approval; only the line is.

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

## Strategiset valinnat ja vaihtoehdot   <!-- valinnainen: kun haaste edellyttää valintaa -->
| Vaihtoehto | Mitä muuttuu (EDGY-elementit) | Hyödyt | Riskit |

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

## Strategic choices and alternatives   <!-- optional: when the challenge calls for a decision -->
| Option | What changes (EDGY elements) | Benefits | Risks |

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

## Choix stratégiques et alternatives   <!-- optionnel : lorsque le défi appelle une décision -->
| Option | Ce qui change (éléments EDGY) | Bénéfices | Risques |

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

## Strategische Optionen und Alternativen   <!-- optional: wenn die Herausforderung eine Entscheidung verlangt -->
| Option | Was sich ändert (EDGY-Elemente) | Nutzen | Risiken |

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

### Target-state Output

#### English (en)

```markdown
# Target state: [Programme]
**Scope:** [organisation / unit] · **Horizon:** [year] · **Status:** hypothesis H1

## 1 Purpose map (PUR-xx, OUT-xx)
## 2 Capability map and cards (CAP-xx)
## 3 Guardrails (G-x)
## 4 Building-block hypothesis (BB-xx)
## 5 Work packages (WP-xx)
## 6 Decisions (ADR-xxx)
## 7 Role model
## 8 Summary for stakeholders
```

#### Finnish (fi)

```markdown
# Tavoitetila: [Ohjelma]
**Rajaus:** [organisaatio / yksikkö] · **Aikajänne:** [vuosi] · **Tila:** hypoteesi H1

## 1 Purpose map (PUR-xx, OUT-xx)
## 2 Kyvykkyyskartta ja kortit (CAP-xx)
## 3 Reunaehdot (G-x)
## 4 Rakennuspalikkahypoteesi (BB-xx)
## 5 Työpaketit (WP-xx)
## 6 Päätökset (ADR-xxx)
## 7 Roolimalli
## 8 Yhteenveto sidosryhmille
```

A complete fictional example: `examples/target-state-example.md`.

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

### Output length by mode

Length is a signal of depth only for a full assessment. For architecture
work a long text is usually the wrong answer.

| Mode / artefact | Length |
|-----------------|--------|
| identify — full assessment (all facets) | at least 150 lines / 5,000 characters |
| reframing | 40–80 lines |
| intersection | 30–60 lines per intersection |
| target-state artefacts (see `edgy-target-state`): stakeholder summary | ≤ 200 words + 1 picture |
| target-state: capability card | ≤ 1 page |
| target-state: decision record | ≤ 40 lines |
| one paragraph next to a diagram | 3–6 sentences |

**DO NOT pad an artefact to reach a line count.** Stop when the reader has
what they need.

### Anti-patterns — DO NOT do this

- **DO NOT write one-line descriptions for elements** — "Purpose: To provide services" is too shallow. Write at least 2 sentences + analysis of how the element differentiates or impacts.
- **DO NOT skip coherence checks** — Every intersection element (Organisation, Product, Brand) MUST include a coherence assessment (Strong/Good/Weak + justification).
- **DO NOT give generic recommendations** — "Improve digital services" fits any company. Recommendations MUST reference specific EDGY elements and be organisation-specific.
- **DO NOT leave tables empty** — Capability table MUST have nature/level classification. Recommendations table MUST have priority levels.
- **DO NOT write under 150 lines in a full assessment** — that analysis is too shallow. For every other mode, follow the length table above.
- **DO NOT model strategic focus areas as Story** — they are sub-Purposes (see Mapping strategy documents to EDGY).

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
