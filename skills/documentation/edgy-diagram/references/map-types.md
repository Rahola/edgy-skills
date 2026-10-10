# Map-type layout patterns

Input and layout sketches for every layout strategy, and the pairwise map
specification that `edgy-deep-dive` follows when authoring XML directly.

## Map type patterns

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

#### Task map — stakeholder inventory and path (task)

Two variants of one input (`examples/task-stakeholder-map.txt`, two pages).

**Inventory** — who does what at which journey stage. One `lane:` per
stakeholder; `stages:` gives the columns and every task picks its column
with `{stage: …}` (a task without a known stage goes to a trailing column
with a warning). Without lanes, a People or Organisation element that has
relationships to the tasks *becomes* the lane: it is not drawn as a box and
its relationships are shown by membership, reported on stderr. The
inventory has no edges because its input has no other relationships; a
relationship written between two tasks is drawn like anywhere else — never
add one to make a map look connected.

```
map_type: task
stages: Plan, Buy, Ride
elements:
  - lane: "Passenger"
    - task: "Plan a trip" {id: TSK-01, stage: Plan}
    - task: "Buy a ticket" {id: TSK-02, stage: Buy}
    - task: "Validate the ticket" {id: TSK-03, stage: Ride}
  - lane: "Driver"
    - task: "Check tickets" {id: TSK-05, stage: Ride}
```

```
              Plan            Buy             Ride
 Passenger  [Plan a trip]  [Buy a ticket]  [Validate the ticket]
 Driver                                    [Check tickets]
```

**Path** — which journey and channels a task touches. No lanes; the tasks
carry their core links `task → journey: is part of` and `task → channel:
uses`. Journeys sit above the task row (input order, left to right),
channels below; the ports are vertical by default so no link crosses a
neighbouring task.

```
                 [Daily commute]
     ↑ is part of    ↑          ↑
 [Plan a trip] [Buy a ticket] [Validate the ticket]
     ↓ uses          ↓ uses      ↓ uses
          [Mobile app]   [Ticket machine]
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

## Pairwise map

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


## Triad — planned ring (EDGY extension)

`map_type: triad` draws **one primary element per type** on a fixed ring and
puts every other element of that type into a "Further <type>" panel below
the ring, without lines. Core links are straight lines from border to
border; two intersection–intersection links detour along the page edge.
Links whose endpoint sits in a panel are reported on stderr (`triad: N
relationship(s) not drawn …`) — the report tables carry them, the picture
stays readable. The primary is `{primary: true}`, otherwise the first element
of its type. The strip legend is the default (`legend: box` overrides).
`group:`, `lane:` and `layout_from:` are ignored with a warning.

### Slots, `facet: all` (box 210 × 74, Purpose 230 × 74; centres)

| Element | centre (cx, cy) | Container (x, y, w, h) |
|---------|-----------------|------------------------|
| purpose | 650, 80 | Identity (260, 30, 800, 260) |
| story | 400, 220 | Identity |
| content | 910, 220 | Identity |
| organisation | 380, 400 | — |
| brand | 920, 400 | — |
| capability | 230, 560 | Architecture (50, 500, 460, 410) |
| asset | 180, 720 | Architecture |
| process | 380, 840 | Architecture |
| task | 1070, 560 | Experience (790, 500, 500, 410) |
| channel | 1170, 720 | Experience |
| journey | 920, 840 | Experience |
| product | 650, 900 | — |

Detours: `organisation → product` leaves left and runs down x = 20;
`product → brand` leaves right and runs up x = 1310. Default label shifts
per pair push the verb away from the nearest box (e.g. `story → purpose`
−45 px, `brand → purpose` +55/+60); override with `{label_dx, label_dy}`.

### Slots, single facet (page 1200 wide)

| Role | architecture | experience | identity |
|------|--------------|------------|----------|
| intersection A, top | organisation (600, 62) | brand (600, 62) | — |
| container | (60, 130, 1080, 330) | (60, 130, 1080, 440) | (60, 30, 1080, 320) |
| left (Outcome base type) | capability (230, 225) | task (230, 225) | story (335, 270) |
| right (Activity base type) | process (970, 225) | journey (970, 225) | content (870, 270) |
| centre, lower (Object base type) | asset (600, 392) | channel (600, 492) | purpose (600, 98) top centre |
| intersection B, below | product (600, 532) | product (600, 652) | organisation (330, 482), brand (870, 482) |

The `A → B` link detours along x = 1150. Panels start 40 px under the ring:
types with ≥ 5 further elements get a full-width 4-column panel, 2–4 a
400 px 2-column panel, one a 240 px panel; panels wrap into rows.

### When to use it

A facet map with more than ~8 elements in one facet, or any `facet: all`
map whose 24 core links stop being readable in the default column layout.
Use `edgy_lint.py --visual` to confirm: a triad output should report no
W111–W114. The ring is the overview; structural maps (purpose, capability,
journey) answer the detailed questions with the same ids.
