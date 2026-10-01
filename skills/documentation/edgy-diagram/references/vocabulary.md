# EDGY 23 vocabulary reference

Element types, the 24 official core links in four languages, flow and tree
keywords, recommended tags and metrics, and the natural-language → element
table. The core-link tables are generated from
`skills/_shared/edgy-core-links.yaml` — do not edit them here.

## Element types

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


## Official 24 EDGY core links

These are the official named links from the EDGY 23 specification. Use the relationship verb matching the `language` parameter. Each verb is valid **only** for the (source → target) pairs listed here; `requires` / `vaatii` is valid for three pairs, everything else for one.

<!-- edgy-links:begin format=grouped4 -->
#### Identity Facet Links

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| story → purpose | contextualises | kontekstualisoi | contextualise | kontextualisiert |
| content → purpose | expresses | ilmaisee | exprime | drückt aus |
| content → story | conveys | välittää | transmet | vermittelt |
| brand → story | evokes | herättää | évoque | evoziert |
| brand → purpose | represents | edustaa | représente | repräsentiert |

#### Architecture Facet Links

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| capability → asset | requires | vaatii | nécessite | erfordert |
| process → capability | realises | toteuttaa | réalise | realisiert |
| process → asset | requires | vaatii | nécessite | erfordert |
| product → capability | requires | vaatii | nécessite | erfordert |
| process → product | creates | luo | crée | erzeugt |

#### Experience Facet Links

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| task → journey | is part of | on osa | fait partie de | ist Teil von |
| task → channel | uses | käyttää | utilise | nutzt |
| journey → channel | traverses | kulkee | traverse | durchläuft |
| brand → task | supports | tukee | soutient | unterstützt |
| brand → journey | appears in | näkyy | apparaît dans | erscheint in |

#### Organisation Intersection Links (Identity ↔ Architecture)

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| organisation → purpose | pursues | tavoittelee | poursuit | verfolgt |
| organisation → story | authors | kirjoittaa | rédige | verfasst |
| organisation → capability | has | omistaa | possède | besitzt |
| organisation → process | performs | suorittaa | exécute | führt aus |

#### Product Intersection Links (Architecture ↔ Experience)

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| product → task | serves | palvelee | sert | bedient |
| product → journey | features in | esiintyy | figure dans | erscheint in |

#### Intersection Element Cross-Links

| Source → Target | EN | FI | FR | DE |
| ----------------- | ---- | ---- | ---- | ---- |
| organisation → brand | builds | rakentaa | construit | baut auf |
| organisation → product | makes | valmistaa | fabrique | stellt her |
| product → brand | embodies | ilmentää | incarne | verkörpert |
<!-- edgy-links:end -->

## Flow relationship keywords

| EN | FI | FR | DE | Usage |
|----|----|----|-----|-------|
| flows | virtaa | circule | fließt | Data/information flows from A to B |
| transfers | siirtyy | transfère | überträgt | Value/object transfers |
| produces data | tuottaa dataa | produit des données | erzeugt Daten | A produces data for B |
| returns | palauttaa | retourne | gibt zurück | Feedback flow |

Flow arrows can describe what flows: information, money, material, energy, attention.
Example syntax: `"System A" -> "System B": "flows [customer data]"`

## Tree hierarchy keywords

| EN | FI | FR | DE | Usage |
|----|----|----|-----|-------|
| contains | sisältää | contient | enthält | Whole contains part |
| comprises | koostuu | comprend | umfasst | Whole comprises parts |
| decomposes | jakaantuu | se décompose | zerlegt sich | Whole decomposes into parts |


## Recommended tags by element type (EDGY 23)

| Element | Tags | Metrics |
|---------|------|---------|
| Capability | in-house/outsourced, innovating/differentiating/commodity | cost, performance |
| Asset | material/machine/document/application/data, owned/external | cost, expiry |
| Process | internal/shared, structured/non-structured, manual/automated/hybrid | automation, cost |
| Task | functional/emotional/social | satisfaction |
| Channel | digital/physical/hybrid, synchronous/asynchronous | usage, cost |
| Organisation | company/association/team/project, hierarchical/matrix | satisfaction, cost |
| Product | physical/digital/service | revenue, satisfaction |

## Metric colour coding

| Value | Colour | Usage |
|-------|--------|-------|
| good / hyvä / bon / gut | Green | Positive state |
| ok / keskiverto / moyen / mittel | Yellow | Neutral state |
| bad / huono / mauvais / schlecht | Red | Negative state |
| low / matala / bas / niedrig | Green | Low cost etc. |
| high / korkea / élevé / hoch | Red | High cost etc. |


## Element identification from natural language

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


## Facet model

EDGY consists of three main facets and three intersection elements.

### Base Elements

All facet elements are specialisations of these four base elements. Base elements are applicable to all facets.

| Type | FI / FR / DE | Description | Shape | Example |
|------|--------------|-------------|-------|---------|
| `people` | ihmiset / personnes / Menschen | Individuals who together create the enterprise or use products | Person shape | `- people: "Customers"` |
| `activity` | toiminta / activité / Aktivität | What is done or happens in the enterprise or ecosystem | Pentagon/arrow | `- activity: "Product development"` |
| `outcome` | tulos / résultat / Ergebnis | Result or change — KPIs and target levels live here (`outcome measures purpose`) | Rounded rectangle | `- outcome: "Customer satisfaction"` |
| `object` | kohde / objet / Objekt | Tangible or intangible structure | Rectangle | `- object: "Database"` |

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

