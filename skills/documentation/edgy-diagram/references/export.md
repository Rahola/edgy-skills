# Export, PlantUML, official resources and the draw.io CLI

## Format Selection

Check user request for format preference:
- `/edgy-diagram identity: company purpose` → `identity.drawio`
- `/edgy-diagram png: architecture` → `architecture.drawio.png`
- `/edgy-diagram svg: experience` → `experience.drawio.svg`
- `/edgy-diagram pdf: full-edgy-map` → `full-edgy-map.drawio.pdf`

## Export Presets

Use `--preset` to apply ready-made export settings:

| Preset | Format | Käyttötarkoitus | CLI-argumentit |
|--------|--------|------------------|----------------|
| `presentation` | PNG | Esitykset (1920×1080, 150 DPI) | `--width 1920 --scale 1.5 -b 20` |
| `print` | PDF | Tulostettava (A3, 300 DPI) | `--scale 3.0 -b 30` |
| `web` | SVG | Läpinäkyvä tausta web-julkaisuun | `-t -b 10` |

Esimerkki: `python3 edgy_generator.py input.txt --preset presentation --output slide.png`

### Native presets (`--engine native`, `--preview`)

| Preset | Margin | Legend (unless the input sets one) | W115 reference width | Bands |
|--------|-------:|------------------------------------|----------------------|-------|
| `publication` | 24 px | `strip` | 605 px — a 160 mm report column at 96 dpi: the text is tested at the size it is printed | `title:` above, `footnote:` below |
| `presentation` | 48 px | `box` | 1920 px — a full-width slide | `title:` above, `footnote:` below |

Both crop to the content like `--publication`. When the input fixes
`legend:`, the same input rendered with both presets differs only in this
frame; without it the legend placement follows the preset (`strip` /
`box`) and the page layout changes with it. `qa.json` records the preset, the
scale and the W115 count. `--preset presentation` means the native preset
with `--engine native` or `--preview`, and the draw.io CLI preset with
`--engine drawio` and a PNG/PDF/SVG format.

```bash
python3 edgy_generator.py in.txt --output out.drawio --preview --preset publication
python3 edgy_render.py out.drawio --preset presentation --title "Purpose map" --footnote "Source: …"   # frame only, see below
```

`edgy_render.py --preset` applies the **frame only** of the preset to an
existing `.drawio`: margin, crop to content, title and footnote bands. The
legend placement is already in the file (the generator chose it), and the
standalone renderer runs no W115 check and writes no `qa.json`. For the full
preset — legend, text-size check at the reference width, manifest — generate
with `edgy_generator.py … --preview --preset <name>` (or `--engine native`).

## PlantUML output

EDGY-kaaviot voi tuottaa myös PlantUML-lähdetiedostona käyttämällä
plantuml-stdlib:n virallista `<edgy/edgy>`-kirjastoa
(https://plantuml.com/stdlib#7c3d1cde3762ae3b). PlantUML on tekstipohjainen
ja versionhallintaystävällinen — sopii diagram-as-code-workflowihin, CI/CD-
pipeineihin ja IDE-previewiin ilman draw.io-binääriä.

**Milloin käyttää:**
- Kaavio commitoidaan repoon ja diff:n halutaan pysyvän luettavana
- IDE-plugin (VS Code / IntelliJ) renderöi kaavion editorissa
- CI render Krokilla tai PlantUML-jar:lla ilman headless draw.io:ta

**Käyttö:**

```bash
# pelkkä .puml-lähdetiedosto, ei riippuvuuksia
python scripts/edgy_generator.py examples/purpose-map.txt \
    --format plantuml --output purpose.puml

# render PNG/SVG/PDF PlantUML-engineä käyttäen
python scripts/edgy_generator.py examples/purpose-map.txt \
    --format png --engine plantuml --output purpose.png
```

PNG/SVG/PDF-render vaatii joko `plantuml.jar`:n (osoitettu
`PLANTUML_JAR`-ympäristömuuttujalla tai sijoitettu vakiopolulle) tai
`plantuml`-binaarin PATHista. Jos kumpaakaan ei löydy, `.puml`-lähde
kirjoitetaan silti ja varoitus tulostuu.

**Mapping EDGY → PlantUML-makrot:**

| EDGY-elementti | PlantUML-makro |
|---|---|
| purpose, content, story, capability, asset, process, task, channel, journey | `$purpose(...)`, `$content(...)`, ... |
| brand, product, organisation | `$brand(...)`, `$product(...)`, `$organisation(...)` |
| people, activity, object, outcome | `$people(...)`, `$activity(...)`, `$object(...)`, `$outcome(...)` |
| Core link / influence | `$link(a, b, "label")` |
| Flow relationship | `$flow(a, b, "label")` |
| Tree relationship | `$tree(a, b, "label")` |

PlantUML auto-layoutaa elementit — pikselikoordinaatteja ei tarvita.
Element-ID:t (`purpose1`, `capability2`, ...) säilyvät identtisinä draw.io-
ulostulon kanssa.

**Esimerkki:** `examples/expected-purpose.puml`

## ArchiMate Open Exchange (from the model)

`edgy-assessment/scripts/edgy_model_to_archimate.py <model>.json -o <out>.xml`
writes the EDGY model (not a drawing) as ArchiMate 3.1 Open Exchange XML for
Archi and other ArchiMate tools: elements with documentation and the
properties `edgy:type`, `edgy:id`, `edgy:provenance`, `edgy:nature`,
`edgy:level`; core links as directed, named Associations between the primary
elements of two types; one view per facet map with the positions this
generator computes. One-way: edit the EDGY model and export again.

| EDGY 23 | ArchiMate 3.1 | Note |
|---------|---------------|------|
| Purpose | Goal | |
| Story | Meaning | |
| Content | Representation | |
| Capability | Capability | |
| Asset | Resource | |
| Process | BusinessProcess | |
| Task | BusinessProcess | the person's job, not the organisation's process — `edgy:type = task` |
| Channel | BusinessInterface | |
| Journey | ValueStream | |
| Organisation | BusinessActor | |
| Product | Product | |
| Brand | Value | |
| core link | Association (directed, named with the verb) | no Realization / Serving is inferred |

`--no-views` writes elements and relationships only. The reverse direction
— positions *from* an Archi view — is `layout_from: file.archimate#View`
(SKILL.md).

## Viralliset EDGY 23 -resurssit

Skillin mukana toimitetaan viralliset EDGY 23 -resurssit:
- `assets/stencils/EDGY_23_drawio_stencils.xml` — draw.io stencil -kirjasto.
  Lataa draw.io:hon: **File → Open Library...** ja valitse tiedosto. Tämän
  jälkeen viralliset EDGY-muodot löytyvät shapes-paneelista.
- `assets/stencils/svg/Shape-*.svg` — yksittäiset SVG-muodot (Purpose, Content,
  Story, Capability, jne.) sekä facet-ikonit (Identity/Architecture/Experience).
- `examples/official/*.drawio.xml` — 16 virallista esimerkkikarttaa (capability,
  journey, purpose, task, process, brand, …) referenssiksi.

Parser tuottaa suoraan virallisen EDGY 23 -väripaletin ja muodot (pyöristetyt
kulmat, valkoinen reunus, facet-värit) jotka vastaavat virallisten esimerkki-
karttojen tyyliä, joten stencil-kirjaston lataaminen draw.io:hon on tarpeen
vain silloin kun käyttäjä muokkaa kaaviota manuaalisesti draw.io:ssa.

## draw.io CLI

Export command: `drawio -x -f <format> -e -b 10 -o <output> <input.drawio>`

| Location | Path |
|----------|------|
| macOS | `/Applications/draw.io.app/Contents/MacOS/draw.io` |
| Linux | `drawio` (in PATH) |
| Windows | `"C:\Program Files\draw.io\draw.io.exe"` |

