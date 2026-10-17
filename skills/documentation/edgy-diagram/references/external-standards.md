# External standards and classifications — register and rationale

These are **EDGY skills**. EDGY 23 is the language of every map: its
elements, facets, colours and core links. Anything else the skills use comes
from outside EDGY, and this register records it: what it is, where it is
used, why it was chosen, how it stays subordinate to EDGY, and its source
and licence. A new external standard or classification enters the skills
only with an entry here (see *Admission rules*); a reviewer rejects one that
has none.

## Principles

1. **EDGY first.** Every drawn map stays valid EDGY: an external
   classification never adds an element type, never changes a fill colour
   (the fill is the facet) and never replaces a core link.
2. **An extension is visible.** It is drawn as a badge, a stroke, a layout
   or a cell, never as notation. It has its own legend section marked
   "(extension)", and the delivery says it is an extension.
3. **Opt-in.** Nothing external appears unless the input asks for it.
4. **Another notation is another skill.** A full foreign notation (C4,
   ArchiMate views, BPMN) is never drawn with EDGY shapes. It lives in a
   separate skill or in an export, behind the notation contract (`notation:`,
   E012 / E013, `references/extension-contract.md`), linked to EDGY elements
   by id.
5. **Credit and licence.** The source is named in the legend or the export.
   No third-party text, figure or template is copied. Only names, categories
   and the format required for interoperability are used.

## Admission rules

An external standard is added only when all of these hold:

| # | Question | Must be |
|---|----------|---------|
| 1 | Does it answer a question EDGY 23 alone cannot? | yes, named in the entry |
| 2 | Is it widely known to the audience (architects, management, IT)? | yes |
| 3 | Can it be shown without changing EDGY elements, fills or core links (badge, stroke, layout, matrix cell, export, separate skill)? | yes |
| 4 | Is the licence compatible with Apache-2.0 / CC BY-SA 4.0, and is attribution possible? | yes |
| 5 | Were alternatives considered? | listed in the entry |
| 6 | Is it opt-in and labelled as an extension? | yes |

## Register

### Gartner TIME — application lifecycle (in use, edgy-diagram 2.8.0)

| | |
|---|---|
| **What** | Gartner's four-way application portfolio classification: **T**olerate, **I**nvest, **M**igrate, **E**liminate. It judges business value and technical fitness together. |
| **Where** | `{time: …}` on an application Asset (application map, capability views); model field `time` (format 1.9); compared by `edgy_model_diff.py`. |
| **Question it answers** | Where to put money and where to retire. EDGY has Assets, but no notion of an asset's lifecycle state. |
| **Why this one** | The most widely used application portfolio classification in enterprise architecture practice. Four categories fit one badge, and they map directly onto decisions (keep, develop, move, retire). Management audiences already know it. |
| **Alternatives considered** | AWS / Gartner "R" migration strategies (rehost, refactor …): cloud-specific and too fine for a portfolio view. A free `{rating:}` label: possible, but then every delivery invents its own words. The 1–5 maturity scale: measures capability, not the lifecycle decision. |
| **How it stays subordinate to EDGY** | A badge in the card's first badge slot, with its own legend section "Lifecycle (Gartner TIME, extension)". The fill stays the facet colour. TIME is the **current** lifecycle judgement; the target state is shown with the transition overlay, never with TIME. |
| **Limits** | A judgement, not a measurement. A report states its basis (interviews, cost data, technical review). A maturity or rating badge takes the same slot, and the generator warns when TIME is hidden. |
| **Source and licence** | Gartner, Inc. (application portfolio management, "TIME" model). Only the four category names and their meaning are used; no Gartner material is reproduced. Credited in the legend. |

### C4 model — software architecture diagrams (planned, `edgy-c4` 0.1.0, v2.5.0)

| | |
|---|---|
| **What** | Simon Brown's C4 model: hierarchical diagrams of a software system (Context, Containers, Components, Code). |
| **Where** | Planned as the separate `edgy-c4` skill: C4 levels 1–2 for one application (plan `docs/development-plan-2026-10-architecture-views.md`, §0 and §4). Not in v2.4.0; `notation: c4` is E013 until that skill is installed. |
| **Question it answers** | What an application is made of and how its parts talk to each other. EDGY stops at the Asset: an application is one card. Teams that build or buy the application need the next level. |
| **Why this one** | Widely adopted and lightweight, and notation-independent (it defines abstractions, not shapes), so it can be drawn with its own shapes beside EDGY. It also has a known text-to-diagram tradition. |
| **Alternatives considered** | The ArchiMate application layer: heavier, and already covered by the one-way export. UML component and deployment diagrams: too detailed for an architecture conversation. Drawing containers as EDGY Assets: rejected, because it would blur the EDGY Asset and break principle 4. |
| **How it stays subordinate to EDGY** | A separate skill and a separate notation page. E012 forbids mixing C4 and EDGY cells on one page. A C4 system is linked to its EDGY Asset by the same id, so the views connect without merging the notations. C4 is drawn only for applications in decided building blocks (plan §4). |
| **Source and licence** | c4model.com, Simon Brown; published under Creative Commons Attribution 4.0. Attribution in the `edgy-c4` skill and its legend. C4-PlantUML (MIT) only if it is vendored, with its notice. |

### ArchiMate 3.1 Open Exchange Format — export (in use, edgy-assessment)

| | |
|---|---|
| **What** | The Open Group's exchange file format for ArchiMate models. |
| **Where** | `edgy_model_to_archimate.py`: a one-way export of `edgy-model.json`. |
| **Question it answers** | How to hand the model to an architecture team whose system of record is an ArchiMate tool (Archi and others). |
| **Why this one** | The open, tool-neutral exchange format of the most common enterprise architecture modelling language. |
| **How it stays subordinate to EDGY** | Export only, one way: the EDGY model stays the source. Every element keeps `edgy:type`. The mapping is documented in the script header; relationships are Associations unless the meaning is exact (Access, Flow). |
| **Source and licence** | The Open Group (ArchiMate® is a registered trademark of The Open Group). The format is used for interoperability; no specification text is reproduced. |

### CRUD — data access (in use, edgy-diagram 2.8.0)

| | |
|---|---|
| **What** | Create, Read, Update, Delete: the four ways a process uses data. The process × data CRUD matrix comes from the information engineering tradition. |
| **Where** | `{crud: …}` on the influence verb `accesses` (process → data Asset); the second label line; capability view data band; `matrix: crud`; ArchiMate Access type. |
| **Question it answers** | Which process creates and which only reads a data set, so that the master and the copies can be seen. EDGY has no data-access semantics. |
| **Why this one** | Universally understood, four letters fit an edge label and a matrix cell, and it maps onto ArchiMate's Read / Write / ReadWrite. |
| **How it stays subordinate to EDGY** | An attribute of an influence verb (dashed line), never a core link. The matrix cells are decorations (`edgyRole=matrix`). |
| **Source and licence** | Common practice, no owner. |

### Process landscape bands — management, core, support (in use, edgy-diagram 2.8.0)

| | |
|---|---|
| **What** | The usual three-way grouping of a process landscape. It derives from Porter's value chain (primary and support activities) with management processes added. |
| **Where** | `{band: management \| core \| support}` on L1 processes (`process_view: chain`, W126); model field `band` (format 1.9). |
| **Question it answers** | Which processes create value and which enable or steer. EDGY has Processes, but no classification of them. |
| **Why this one** | The default structure of process maps in most organisations, so readers recognise it at once. |
| **How it stays subordinate to EDGY** | Layout rows with headers. The cards stay EDGY Processes, and `contains` is shown by position. |
| **Source and licence** | Common practice (Porter's value chain as background), no owner. |

### Swimlane layout (in use, edgy-diagram 2.8.0)

| | |
|---|---|
| **What** | Lanes per actor with the steps in order: a layout widely known from BPMN and flowcharts. |
| **Where** | `process_view: swimlane`. |
| **Why this one** | It is the familiar way to show who does which step. |
| **How it stays subordinate to EDGY** | Only the lane idea is borrowed: no BPMN events, gateways or symbols. Lanes come from EDGY `performs`, and the steps are EDGY Processes. A BPMN model is not produced and is out of scope. |
| **Source and licence** | Common layout; BPMN (OMG) is not used. |

### Maturity scale 1–5 and free ratings (in use, edgy-diagram 2.7.0)

| | |
|---|---|
| **What** | A generic five-step maturity scale (`{maturity: 1–5}`) and free labels (`{rating: …}`) for heat maps. |
| **Why** | Capability heat maps are a common EDGY use, and EDGY says not to colour the fill. |
| **How it stays subordinate to EDGY** | A badge with a legend row "Maturity (extension)" or "Rating (extension)". |
| **Limits** | Not CMMI or any certified maturity model. The levels mean what the delivery defines, and the report must say so. |
| **Source and licence** | Generic, no owner. |

### Hosting and criticality labels (in use, edgy-diagram 2.8.0)

| | |
|---|---|
| **What** | `{hosting: saas \| cloud \| on-prem}` and `{criticality: …}` as the second badge on an application. |
| **Why** | Two facts architects ask about every application. The words follow common cloud usage (SaaS as in NIST's cloud service models). |
| **How it stays subordinate to EDGY** | Second badge slot, with its own legend section "(extension)". |
| **Source and licence** | Common terms, no owner. |

### Capability classification — nature, level, sourcing (in use, edgy-framework / edgy-assessment)

| | |
|---|---|
| **What** | Common capability-mapping attributes: **nature** (core, enabling, management; or differentiating, commodity), **level** (strategic, operational, foundational) and **sourcing** (in-house, outsourced). |
| **Where** | Model fields `nature` and `level` on a capability (`edgy-model.json`); the capability card and helper question 7 in edgy-framework; `[tags]` or `{rating:}` on the map. |
| **Question it answers** | Where to differentiate and where to buy. EDGY has Capabilities, but it does not classify them. |
| **Why this one** | Capability maps in enterprise architecture practice use these words, and management audiences already know them. They are written as attributes and tags, not as notation. |
| **How it stays subordinate to EDGY** | Card text, a tag or a rating badge. The fill stays the facet colour. |
| **Limits** | Two classifications share the field `nature`: core / enabling / management describes the role, differentiating / commodity the competitive value. A model picks one of them per delivery and says which. `level` is not the depth of the capability map; the card's "Level: 2" is the map depth. |
| **Source and licence** | Common practice, no owner. |

### Building blocks, work packages and waves (in use, edgy-target-state)

| | |
|---|---|
| **What** | Planning units of target-state work. A **building block** is a product-independent part of the target architecture. A **work package** is one change to one block. **Waves** are the order of the changes. The terms are common in enterprise architecture and derive from TOGAF's building blocks and work packages. |
| **Where** | edgy-target-state Phases 4–5: building-block hypothesis, mirror table, work-package cards, wave matrix. |
| **Question it answers** | How a target state is split into decisions and changes. EDGY describes the enterprise, not the change programme. |
| **Why this one** | Widely known to architects and IT. The terms are used as plain words, not as a method. |
| **How it stays subordinate to EDGY** | Blocks are drawn as EDGY elements on the reference map with the transition overlay. Work packages and waves are cards and a matrix layout. No TOGAF notation, metamodel or phase (ADM) is used. |
| **Source and licence** | Common practice. TOGAF® is a registered trademark of The Open Group. Only the general terms are used; no TOGAF text is reproduced. |

### Strategy vocabulary — mission, vision, focus areas, KPIs (in use, edgy-framework / edgy-target-state)

| | |
|---|---|
| **What** | The usual words of strategy documents. |
| **Where** | Purpose map: mission and vision become Purposes, focus areas sub-Purposes, KPIs Outcomes (`measures`), initiatives Activities. |
| **Why** | Strategy material arrives in these words. The skills map the words onto EDGY elements and draw nothing new. |
| **How it stays subordinate to EDGY** | A mapping table onto EDGY elements; the map is pure EDGY. |
| **Source and licence** | Common terms, no owner. |

### Architecture decision records (in use, edgy-framework / edgy-target-state)

| | |
|---|---|
| **What** | Short decision records (context, decision, consequences), as popularised by Michael Nygard. |
| **Where** | Target-state work: `decide` overlays become ADR candidates; an external ADR skill is used when available, otherwise a 40-line template. |
| **Why** | Decisions need a home outside the map. EDGY marks that a decision is open (`decide`), not what was decided. |
| **Source and licence** | Common practice; no text reproduced. |

## Not external — the skills' own EDGY extensions

The following were designed in this repository and are documented in
`SKILL.md`: the transition overlay (`{change: …}`, stroke only), the
`reference`, `summary` and `triad` layouts, the status badge mechanism, the
application, process and capability-view layouts, the presenter, and the
planned realisation trace (v2.5.0: it walks EDGY core links only). The
following analysis constructs are also the skills' own:

- the assessment's coherence scores and High / Medium / Low priorities;
- the four deep-dive lenses (dependency, alignment, gaps, opportunities);
- guardrails and the building-block mirror table;
- the model-gap statuses (W127).

They follow the same principles: the map stays valid EDGY, and the
extension is labelled in the legend and the delivery.
