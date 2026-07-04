# Official EDGY 23 Example Maps

This folder contains the 16 official EDGY 23 example maps from Intersection Group, packaged with the skill as canonical references.

Each map is the original Intersection Railways example downloaded from the EDGY 23 specification.

## Files

| File | Map type | Notes |
|------|----------|-------|
| `activity map.drawio.xml` | activity | Base activities (pentagon row) |
| `asset map.drawio.xml` | asset | Architecture assets with relationships |
| `brand map.drawio.xml` | brand | Brand element + satellites |
| `capability map.drawio.xml` | capability | 3-tier nested capability decomposition |
| `channel map.drawio.xml` | channel | Channels grouped by type |
| `content map.drawio.xml` | content | Identity content grid |
| `journey map.drawio.xml` | journey | Customer journey stages |
| `object diagram.drawio.xml` | object | Generic object relationships |
| `organisation map.drawio.xml` | organisation | Org tree hierarchy |
| `outcome map.drawio.xml` | outcome | Outcomes with named links |
| `people map.drawio.xml` | people | Persona grid |
| `process map.drawio.xml` | process | Process flow |
| `product map.drawio.xml` | product | Product graph |
| `purpose map.drawio.xml` | purpose | Purpose grid |
| `story map.drawio.xml` | story | Story panels |
| `task map.drawio.xml` | task | Tasks grouped by journey stage |

The source files are stored in compressed mxGraph format. Decoded readable XML lives under `decoded/` and a per-map-type pattern summary is in `decoded/PATTERNS.md`.

## Importing into draw.io

To open one of these maps in draw.io:

1. Open draw.io desktop (or app.diagrams.net).
2. Use **File → Import → From... → Device** and select the `.drawio.xml` file.
3. The map opens as a new diagram you can edit.

Alternatively, **File → Open** also works for `.drawio.xml` files.

## Source

Original example pack: EDGY 23 specification, Intersection Group (https://intersection.group/).
