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

