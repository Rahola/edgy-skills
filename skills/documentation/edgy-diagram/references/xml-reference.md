# draw.io XML reference for EDGY diagrams

Reference for reviewing generated output and for the hand-written fallback.
The generator (`scripts/edgy_generator.py`) produces all of this; the linter
(`scripts/edgy_lint.py`) checks it.

## Structure, shapes, palette and edge styles

### Base Structure

IMPORTANT: All `mxCell` elements are direct children of `<root>`.
Logical parent-child relationships are expressed via the `parent` attribute, NOT via XML nesting.

**File wrapper.** The generator writes an uncompressed `<mxfile>`; a bare
`<mxGraphModel>` (below) is also valid and is what the inline examples show.
Use the wrapper whenever there is more than one page, and never compress
(`compressed="false"`, no base64/deflate) so that the file stays reviewable
and diffable:

```xml
<?xml version="1.0" encoding="utf-8"?>
<mxfile host="edgy-skills" compressed="false">
  <diagram id="roles" name="Roles and actors">
    <mxGraphModel ...>...</mxGraphModel>
  </diagram>
  <diagram id="systems" name="Systems">
    <mxGraphModel ...>...</mxGraphModel>
  </diagram>
</mxfile>
```

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

The parser classifies every relationship by verb **and** element pair:

1. Verb is a core-link verb **and** (source type, target type) is one of its allowed pairs → **Link** (`endArrow=classic;endFill=1;`)
2. Verb is a core-link verb on any other pair → warning, drawn as **Influence** (the pair is not an official core link)
3. Verb is in `FLOW_RELATIONSHIPS` → **Flow** (`endArrow=open;endFill=0;`)
4. Verb is in `TREE_RELATIONSHIPS` → **Tree** (`endArrow=none;`)
5. Verb is in the influence vocabulary → **Influence** (`endArrow=open;endFill=0;dashed=1;`)
6. Any other verb → warning ("not in vocabulary"), drawn as **Influence**

The linter applies the same rules to finished files (E010 / E011 / W104 / W105).

All: `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;fontSize=11;` + arrow type

## CRITICAL: XML Well-Formedness

- **Edge cells** — Every edge `mxCell` MUST HAVE `<mxGeometry relative="1" as="geometry"/>` as a child element. Self-closing edge cells (e.g. `<mxCell ... edge="1" ... />`) are invalid and will not render.
- **All mxCell elements directly under root** — NO nested mxCell structures. Parent-child relationships are expressed via the `parent` attribute.
- **Escape XML special characters** in attribute values: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- **Unique id values** — Every `mxCell` must have a unique `id`. Start element IDs from 2 (0 and 1 are reserved).
- **No `--` in XML comments** — Double hyphen `--` is forbidden inside `<!-- -->` comments per XML specification.
- **UTF-8 encoding** — Always write files with UTF-8 encoding (`<?xml version="1.0" encoding="utf-8"?>`).


## Complete inline example (Identity facet, 3 elements + 2 relationships)

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

