# Routing by diagram size — reference for `edgy-diagram`

Rules and draw.io XML patterns for keeping edges readable as diagrams grow.
The generator applies the small/medium rules automatically; the large-diagram
patterns are expressed in the input (`lane:`, relationship options) or, for
hand-written XML, copied from here.

## Size classes

| Size | Cells | What to do |
|------|-------|------------|
| Small | < 10 | `edgeStyle=orthogonalEdgeStyle;rounded=1` is enough; the generator distributes exit/entry anchors |
| Medium | 10–25 | Every edge declares exit/entry sides (`{from: right, to: left}` when the automatic side is wrong); flows between rows share a horizontal channel (`via:`); labels near the source (`{label: source}`) or with a white backing (default) |
| Large | > 25 | Lanes (`lane:`) with elements ON the band; one integration bus (a wide Asset, `{size: L}`) instead of n×m edges; vertical channels between columns via `via:`; feedback loops with explicit waypoints whose x equals the target's centre; hide influence edges or move them to a second page |

Always run the preview loop: the picture, not the lint, shows spaghetti.

## Relationship options (input format)

```
- "Building blocks" -> "Capability map": "reveals gaps" {from: bottom, to: bottom, via: [(1515, 562), (695, 562)], change: replace, label: source}
```

| Option | Values | Effect |
|--------|--------|--------|
| `from` / `to` | `left`, `right`, `top`, `bottom` | overrides the automatic exit / entry side (`exitX/exitY`, `entryX/entryY`) |
| `via` | list of `(x, y)` page coordinates | explicit waypoints (`<Array as="points">`) — use after a first preview, when you know the coordinates |
| `change` (or `color`) | `keep`, `new`, `change`, `replace`, `remove`, `decide` (+ fi/fr/de synonyms) | transition-overlay colour on the edge (stroke + label) |
| `label` | `source`, `middle`, `target` | label position along the edge (`mxGeometry x = -0.5 / 0 / 0.5`) |

Several relationships between the same two elements are merged into one edge
whose label is `verb1 / verb2`; the core-link style wins if any of them is a
core link.

Edges between non-adjacent elements in the same lane row are routed over the
top automatically (both anchors on the top side), so they do not cross the
elements in between.

## XML patterns

### Explicit sides and waypoints (feedback loop)

```xml
<mxCell id="30" value="reveals gaps"
  style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=1.5;endArrow=open;endFill=0;dashed=1;
         exitX=0.5;exitY=1;entryX=0.5;entryY=1;labelBackgroundColor=#ffffff;"
  edge="1" source="c3" target="c1" parent="1">
  <mxGeometry relative="1" as="geometry" x="-0.5">
    <Array as="points"><mxPoint x="1515" y="562"/><mxPoint x="695" y="562"/></Array>
  </mxGeometry>
</mxCell>
```

### Lane (borderless band) — elements sit on it at root level

```xml
<mxCell id="20" value="L1 CUSTOMER CHANNELS"
  style="whiteSpace=wrap;html=1;fillColor=#f4f4f4;strokeColor=none;align=left;verticalAlign=top;
         spacingLeft=8;spacingTop=4;fontColor=#555555;fontSize=11;fontStyle=1;"
  vertex="1" parent="1">
  <mxGeometry x="40" y="100" width="1500" height="240" as="geometry"/>
</mxCell>
```

### Invisible anchor on a lane border

An actor or external system connects to the *layer*, not to one block. A 1×1
text cell on the lane border is the edge endpoint:

```xml
<mxCell id="21" value="" style="text;fillColor=none;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="40" y="220" width="1" height="1" as="geometry"/>
</mxCell>
```

(The generator does not emit anchors; add them by hand when a large hand-made
view needs them. The linter accepts them — they are `text` cells.)

### Integration bus instead of n×m edges

One wide Asset (`{size: L}` or wider) in the shared-services lane; every block
that integrates connects vertically to the bus. Replaces a mesh of edges with
n short vertical ones.

### Container (group) — children with relative geometry

```xml
<mxCell id="10" value="1 Customer and identity"
  style="rounded=1;arcSize=6;container=1;collapsible=0;whiteSpace=wrap;html=1;fillColor=#eef2f7;
         strokeColor=#ffffff;strokeWidth=2;align=left;verticalAlign=top;spacingLeft=10;spacingTop=4;fontSize=12;fontStyle=1;"
  vertex="1" parent="1">
  <mxGeometry x="60" y="120" width="520" height="200" as="geometry"/>
</mxCell>
<mxCell id="11" value="1.1 Customer data management"
  style="rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#a6c0ff;strokeColor=#ffffff;strokeWidth=2;fontSize=14;fontStyle=1;"
  vertex="1" parent="10">
  <mxGeometry x="20" y="40" width="150" height="60" as="geometry"/>   <!-- relative to id 10 -->
</mxCell>
```

Never nest `<mxCell>` elements in XML; containment is the `parent` attribute.
The linter and the renderer resolve the parent chain to absolute positions.
