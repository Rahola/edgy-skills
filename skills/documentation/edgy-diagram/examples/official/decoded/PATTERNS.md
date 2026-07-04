# EDGY 23 Official Map Patterns

Layout patterns extracted from the 16 decoded official example maps in this folder. Use these as a template when generating an EDGY map of a given type.

## General observations

- **Most maps are layout-only**: 11 of 16 official maps contain zero edges. Elements communicate meaning through spatial grouping in coloured containers, not through explicit relationships.
- **Three-tier nesting** is the dominant container pattern: outer coloured group → inner white sub-group (`strokeColor=none`) → leaf elements with the facet colour.
- **Leaf size** is consistently **130×60** for boxes, **140×80** for pentagons, **130×50** for tighter hierarchies.
- **Stroke** is always white (`#FFFFFF`) with `strokeWidth=2`; outer containers also use white stroke; sub-group containers have `strokeColor=none`.
- **Font** is `fontSize=14` with bold sub-group titles using inline HTML.

## Per-map type patterns

| Map | Layout | Elements | Edges | Container nesting | Leaf colour |
|-----|--------|---------:|------:|-------------------|-------------|
| `activity` | Horizontal pentagon row | 6–10 | 0 | flat | varies (any facet activity) |
| `asset` | Tree decomposition | 6–10 | 5–8 | flat with edges | `#a6c0ff` (architecture) |
| `brand` | Hub-and-spoke around brand element | 5–10 | 4–8 | flat with edges | `#ffd580` (brand) |
| `capability` | 3-tier nested grouping | 30–60 | 0 | outer + sub-group + leaves | `#a6c0ff` (architecture) |
| `channel` | Grid grouped by channel type | 15–25 | 0 | sub-group + leaves | `#ff99bd` (experience) |
| `content` | Large dense grid | 40–70 | 0 | sub-group + leaves | `#80ffb7` (identity) |
| `journey` | Horizontal pentagon row | 5–8 | 0 | flat | `#ff99bd` (experience) |
| `object diagram` | Object + relationships graph | 8–15 | 6–12 | flat with edges | white / facet |
| `organisation` | Tree hierarchy top-down | 40–80 | 30–50 | tree edges + nodes | `#80eaff` (organisation) |
| `outcome` | Outcome web with named links | 6–12 | 6–12 | flat with edges | rounded rectangles |
| `people` | Persona grid | 10–50 | 0 | sub-group + leaves | varies |
| `process` | Pentagon row or grid | 4–8 | 0 | flat | `#a6c0ff` (architecture) |
| `product` | Product + components graph | 10–20 | 8–15 | flat with edges | `#e599ff` (product) |
| `purpose` | Purpose grid | 10–30 | 0 | flat | `#80ffb7` (identity) |
| `story` | Story panel grid | 8–15 | 0 | flat | `#80ffb7` (identity) |
| `task` | Task grid grouped by journey stage | 30–60 | 0 | sub-group + leaves | `#ff99bd` (experience) |

## Layout primitives

Four reusable layouts cover all 16 map types:

1. **Horizontal sequence** (`activity`, `journey`, `process` simple) — pentagon arrows, 140×80, x-step 160, single row.
2. **Grid** (`purpose`, `story`, `content`, `channel`, `task`, `people`, `brand` simple) — 4–6 columns, 130×60 leaves, 20px gap.
3. **Tree decomposition** (`capability`, `asset`, `organisation`, `outcome`) — nested containers or top-down tree edges.
4. **Hub-and-spoke** (`brand`, `product`, `object diagram`) — central element + 5–10 satellites with named relationships.

## Container styling reference

Outer group container (full facet colour):
```
rounded=1;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=2;fillColor=<facet>;fontSize=14;verticalAlign=top;arcSize=8;
```
Width: 200–900px (spans multiple sub-groups), height: 100–800px.

Sub-group container (white, no stroke):
```
rounded=1;whiteSpace=wrap;html=1;strokeWidth=2;fontSize=14;verticalAlign=top;fillColor=#FFFFFF;arcSize=10;strokeColor=none;
```
Width: 160–500px, height: 100–250px.

Leaf element (facet colour, white stroke):
```
rounded=1;whiteSpace=wrap;html=1;strokeColor=#FFFFFF;strokeWidth=2;fillColor=<facet>;fontSize=14;verticalAlign=middle;
```
Width: 130, height: 60 (50 in dense trees).

Pentagon leaf (activities):
```
shape=mxgraph.arrows2.arrow;dy=0;dx=22;notch=0;strokeColor=#FFFFFF;strokeWidth=2;fontSize=14;fillColor=<facet>;
```
Width: 140, height: 80.

## Element count thresholds (for validation)

Below these thresholds the map looks too sparse compared to official examples:

| Map type | Min elements | Recommended |
|----------|-------------:|------------:|
| `activity`, `journey`, `process` | 4 | 6–8 |
| `asset`, `outcome`, `brand`, `object diagram` | 5 | 7–10 |
| `purpose`, `story`, `product` | 6 | 10–15 |
| `capability`, `task`, `channel`, `content`, `people`, `organisation` | 8 | 15–30 |
