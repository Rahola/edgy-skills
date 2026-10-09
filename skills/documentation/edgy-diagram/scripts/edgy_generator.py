#!/usr/bin/env python3
"""
EDGY Generator - Pääskripti EDGY-kaavioiden generointiin
"""

import os
import sys
import argparse
from edgy_parser import EDGYParser
from edgy_to_plantuml import generate_plantuml
from edgy_document import parse_document, build_mxfile, unique_slugs
import edgy_render
import edgy_qa

def read_input_file(file_path: str) -> str:
    """Lue syötetiedosto"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{file_path}' not found")
        sys.exit(1)

def write_drawio_file(xml_content: str, output_path: str) -> None:
    """Kirjoita draw.io tiedosto"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"Successfully created: {output_path}")
    except IOError as e:
        print(f"Error writing file: {e}")
        sys.exit(1)


def write_text_file(content: str, output_path: str) -> None:
    """Kirjoita tekstitiedosto (esim. .puml)."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created: {output_path}")
    except IOError as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

def report_parser_messages(pages, lenient: bool = False) -> None:
    """Tulosta parserien varoitukset stderr:iin; pysäytä syötevirheisiin.

    `pages` on lista (sivun nimi, EDGYParser). Varoitukset (esim. ydinlinkki
    väärällä parilla, tuntematon verbi) eivät estä generointia mutta
    näytetään aina. Virheet (tuntematon facet tai map_type) päättävät ajon
    exit-koodilla 2, ellei --lenient ole annettu.
    """
    if isinstance(pages, EDGYParser):
        pages = [(None, pages)]
    multi = len(pages) > 1
    n_warn = 0
    has_errors = False
    for name, edgy_parser in pages:
        prefix = f"[{name}] " if multi else ""
        for w in edgy_parser.warnings:
            print(f"Warning: {prefix}{w}", file=sys.stderr)
            n_warn += 1
        for e in edgy_parser.errors:
            print(f"Error: {prefix}{e}", file=sys.stderr)
            has_errors = True
    if has_errors and not lenient:
        print("Input has errors — fix the input or pass --lenient to generate anyway.",
              file=sys.stderr)
        sys.exit(2)
    if n_warn:
        print(f"{n_warn} warning(s) — see above.", file=sys.stderr)


def report_layout_warnings(pages, before_counts) -> None:
    """Tulosta layout-vaiheessa syntyneet varoitukset (summary-rivimäärä, layout_from …)."""
    multi = len(pages) > 1
    n = 0
    for (name, edgy_parser), before in zip(pages, before_counts):
        prefix = f"[{name}] " if multi else ""
        for w in edgy_parser.warnings[before:]:
            print(f"Warning: {prefix}{w}", file=sys.stderr)
            n += 1
    if n:
        print(f"{n} layout warning(s) — see above.", file=sys.stderr)


def render_preview(drawio_path: str, png: bool = True, publication: bool = False, preset: str = None,
                   heading: str = None, footnote: str = None):
    """CLI-vapaa esikatselu: SVG aina, PNG jos Chromium löytyy.

    Palauttaa render_file-tuloslistan, tai None jos SVG:tä ei saatu
    kirjoitettua — esikatselu on pakollinen vaihe, joten kutsuja päättää ajon
    virheeseen. Puuttuva PNG (ei Chromiumia) ei ole virhe: SVG riittää
    katselmointiin. `publication` rajaa kuvan sisältöön (ei editorisivuun);
    natiivi `preset` lisää marginaalin sekä otsikko-/alaviitenauhat.
    """
    try:
        results = edgy_render.render_file(drawio_path, png=png, publication=publication, preset=preset,
                                          heading=heading, footnote=footnote)
    except Exception as e:  # noqa: BLE001 — raportoidaan ja palautetaan virhe
        print(f"Error: preview failed: {e}", file=sys.stderr)
        return None
    if not results:
        print("Error: preview produced no pages", file=sys.stderr)
        return None
    for r in results:
        label = f" [page {r['page']}]" if r['page'] else ""
        print(f"Preview SVG: {r['svg']}{label}")
        if r['png']:
            print(f"Preview PNG: {r['png']}")
        if publication or preset:
            print(f"Orientation: {r.get('orientation', 'square')}{label}")
    if png and not any(r['png'] for r in results):
        print("Preview: no Chromium/Chrome found — SVG only. Open the SVG in a browser, "
              "or set EDGY_CHROMIUM=<binary> for PNG.")
    return results


# Export-presetit: (format, extra draw.io CLI args)
# - presentation: 1920x1080 PNG, 150 DPI
# - print: A3 PDF, 300 DPI, valkoinen tausta
# - web: läpinäkyvä SVG
EXPORT_PRESETS = {
    'presentation': ('png', ['--width', '1920', '--scale', '1.5', '-b', '20']),
    'print':        ('pdf', ['--scale', '3.0', '-b', '30']),
    'web':          ('svg', ['-t', '-b', '10']),
}


def export_with_drawio_cli(input_path: str, output_path: str, format: str, extra_args: list = None) -> bool:
    """Vie draw.io CLI:llä. Palauttaa True vain kun output_path on kirjoitettu."""
    try:
        # Tarkista että draw.io CLI on saatavilla
        import subprocess

        # Yritä löytää draw.io
        drawio_paths = [
            'drawio',
            '/Applications/draw.io.app/Contents/MacOS/draw.io',
            'C:\\Program Files\\draw.io\\draw.io.exe'
        ]

        drawio_cmd = None
        for path in drawio_paths:
            try:
                result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    drawio_cmd = path
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        if not drawio_cmd:
            print("Warning: draw.io CLI not found. Skipping export — the .drawio file is kept.", file=sys.stderr)
            return False

        # Suorita vienti
        cmd = [drawio_cmd, '-x', '-f', format, '-e']
        if extra_args:
            cmd.extend(extra_args)
        else:
            cmd.extend(['-b', '10'])
        cmd.extend(['-o', output_path, input_path])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Successfully exported to {output_path}")
            # Poista väliaikainen .drawio tiedosto
            os.remove(input_path)
            return True
        print(f"Export failed: {result.stderr}", file=sys.stderr)
        return False

    except Exception as e:
        print(f"Export error: {e}", file=sys.stderr)
        return False


def _find_plantuml_cmd():
    """Etsi PlantUML-suorittaja: PLANTUML_JAR ympäristömuuttuja,
    yleiset jar-polut tai `plantuml` PATHista. Palauta argumenttilista
    tai None.
    """
    import shutil
    import subprocess

    jar_env = os.environ.get('PLANTUML_JAR')
    candidate_jars = []
    if jar_env:
        candidate_jars.append(jar_env)
    candidate_jars.extend([
        os.path.expanduser('~/.local/share/plantuml/plantuml.jar'),
        '/usr/local/share/plantuml/plantuml.jar',
        '/usr/share/plantuml/plantuml.jar',
        'C:\\tools\\plantuml.jar',
        'C:\\Program Files\\PlantUML\\plantuml.jar',
    ])
    for jar in candidate_jars:
        if jar and os.path.isfile(jar):
            java = shutil.which('java')
            if java:
                return [java, '-jar', jar]

    plantuml_bin = shutil.which('plantuml')
    if plantuml_bin:
        return [plantuml_bin]

    return None


def export_with_plantuml_cli(input_path: str, output_path: str, format: str) -> None:
    """Render .puml -> png/svg/pdf PlantUML-toolilla."""
    import subprocess

    fmt_flag = {'png': '-tpng', 'svg': '-tsvg', 'pdf': '-tpdf'}.get(format)
    if not fmt_flag:
        print(f"Warning: PlantUML engine does not support format '{format}'. Keeping .puml only.")
        return

    base_cmd = _find_plantuml_cmd()
    if not base_cmd:
        print("Warning: PlantUML not found (set PLANTUML_JAR or install `plantuml`). Keeping .puml only.")
        return

    out_dir = os.path.dirname(os.path.abspath(output_path)) or '.'
    cmd = base_cmd + [fmt_flag, '-o', out_dir, input_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        print(f"PlantUML export error: {e}")
        return

    if result.returncode != 0:
        print(f"PlantUML export failed: {result.stderr.strip() or result.stdout.strip()}")
        return

    # PlantUML kirjoittaa <basename>.<ext>; nimeä halutuksi tarvittaessa
    base = os.path.splitext(os.path.basename(input_path))[0]
    produced = os.path.join(out_dir, f"{base}.{format}")
    if os.path.abspath(produced) != os.path.abspath(output_path):
        if os.path.exists(produced):
            os.replace(produced, output_path)
    print(f"Successfully exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='EDGY Diagram Generator')
    parser.add_argument('input', help='Input file path or direct input')
    parser.add_argument('--format', choices=['drawio', 'png', 'svg', 'pdf', 'plantuml', 'puml'], default='drawio',
                       help='Output format (drawio is default, plantuml/puml = PlantUML source)')
    parser.add_argument('--engine', choices=['drawio', 'plantuml', 'native'], default='drawio',
                       help='Render engine for png/svg/pdf (default drawio). native = pure-Python SVG '
                            '(+PNG via headless Chromium when available), no draw.io/Java needed; '
                            'approximate rendering, no pdf. Ignored for drawio/plantuml/puml formats.')
    parser.add_argument('--preset', choices=sorted(set(EXPORT_PRESETS) | set(edgy_render.NATIVE_PRESETS)),
                       help='draw.io CLI export preset (presentation/print/web — overrides --format), or a native preset '
                            '(publication/presentation) for --engine native and --preview: fixed margin, title/footnote '
                            'bands, legend placement, crop to content, W115 at the preset reference width. '
                            '"presentation" is the CLI preset with --engine drawio and the native one otherwise')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--preview', action='store_true',
                       help='After writing the .drawio, also write an SVG (and PNG when Chromium is '
                            'available) next to it for the mandatory look-before-delivery step')
    parser.add_argument('--bare', action='store_true',
                       help='Write a bare <mxGraphModel> instead of the default <mxfile> wrapper '
                            '(single-page input only)')
    parser.add_argument('--lenient', action='store_true',
                       help='Generate even when the input has errors (unknown facet/map_type); '
                            'by default such input exits with code 2')
    parser.add_argument('--publication', action='store_true',
                       help='Native SVG/PNG (--engine native, --preview) cropped to the content bounds '
                            'instead of the editor page; prints an orientation hint per page')
    parser.add_argument('--semantic-review', action='store_true',
                       help='Run edgy_semantic_review.py on the input and print its questions to stderr '
                            '(never blocks generation; a reviewer signs off — see edgy-framework)')
    parser.add_argument('--qa', dest='qa', action='store_true', default=None,
                       help='Write <output>.qa.json next to the .drawio: counts, lint, visual / layout / language '
                            'checks, preview sizes and the approval fields a person fills in (on by default with --preview)')
    parser.add_argument('--no-qa', dest='qa', action='store_false', help='Do not write the qa.json manifest')
    parser.add_argument('--no-layout-quality', action='store_true',
                       help='qa.json: run the lint without the layout-quality rules W117–W120 (recorded in the manifest)')

    args = parser.parse_args()

    # Natiivi preset (publication/presentation) koskee natiivirenderiä ja esikatselua; draw.io CLI:n
    # presentation/print/web säilyvät ennallaan kun viedään CLI:llä
    # - publication: native only. - presentation: native with --engine native or --format drawio (+ --preview),
    #   the draw.io CLI preset with --engine drawio and an image format. Unsupported combinations are refused,
    #   never silently rendered without the preset's margins and bands.
    native_preset = None
    extra_export_args = None
    native_render = (args.engine == 'native' and args.format in ('png', 'svg')) or (args.preview and args.format == 'drawio')
    native_requested = args.preset not in EXPORT_PRESETS or args.engine == 'native' or native_render
    if args.preset in edgy_render.NATIVE_PRESETS and native_requested:
        native_preset = args.preset
        if not native_render or args.format == 'pdf':
            print(f"Error: --preset {args.preset} is a native preset: use --engine native with --format png|svg, "
                  f"or --preview with the default .drawio output", file=sys.stderr)
            sys.exit(2)
    elif args.preset:
        args.format, extra_export_args = EXPORT_PRESETS[args.preset]   # draw.io CLI preset, e.g. --preset presentation --output slide.png
    if args.qa is None:
        args.qa = bool(args.preview)

    # Lue syöte
    if os.path.exists(args.input):
        input_content = read_input_file(args.input)
    else:
        input_content = args.input

    # Jäsennä EDGY (yksi tai useampi sivu)
    try:
        pages = parse_document(input_content)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    report_parser_messages(pages, args.lenient)
    if args.semantic_review:
        # Kysymykset kartan merkityksestä (S001–S006); eivät koskaan estä generointia
        import edgy_semantic_review
        findings = []
        for name, p in pages:
            findings.extend(edgy_semantic_review.review_parser(p, name if len(pages) > 1 else None))
        if findings:
            print(edgy_semantic_review.format_findings(findings, args.input), file=sys.stderr)
        n_q = sum(1 for f in findings if f['level'] == 'warning')
        print(f"Semantic review: {n_q} question(s), {len(findings) - n_q} hint(s) — a clean run is not an approval; "
              f"a reviewer signs off (edgy-framework, Purpose map semantic review).", file=sys.stderr)
    edgy_parser = pages[0][1]   # ensimmäinen sivu: oletusnimet ja PlantUML-engine
    if native_preset:
        # Presetin legendapaikka, ellei syöte ole valinnut: publication → strip, presentation → box
        for _, p in pages:
            if not p._legend_explicit:
                p.legend = edgy_render.NATIVE_PRESETS[native_preset]['legend']
    heading = [p.title for _, p in pages]        # one band per page: a page-level title:/footnote: overrides the head
    footnote = [p.footnote for _, p in pages]
    if args.bare and len(pages) > 1:
        print("Error: --bare supports single-page input only", file=sys.stderr)
        sys.exit(2)

    # Normalisoi formaatti
    fmt = 'puml' if args.format == 'plantuml' else args.format

    # PlantUML-source haara (monisivuinen syöte → useita @startuml-lohkoja)
    if fmt == 'puml':
        puml_content = ''.join(generate_plantuml(p) + ('\n' if i else '') for i, (_, p) in enumerate(pages))
        if args.output:
            output_path = args.output if args.output.endswith('.puml') else args.output + '.puml'
        else:
            base = edgy_parser.map_type or edgy_parser.facet or 'edgy'
            if base == 'all':
                base = 'edgy'
            output_path = f"{base}-map.puml"
        write_text_file(puml_content, output_path)
        return

    # PlantUML-engine PNG/SVG/PDF -renderille
    if args.engine == 'plantuml' and fmt in ('png', 'svg', 'pdf'):
        base = edgy_parser.map_type or edgy_parser.facet or 'edgy'
        if base == 'all':
            base = 'edgy'
        if args.output:
            stem, ext = os.path.splitext(args.output)
            ext = ext or f'.{fmt}'
        else:
            stem, ext = f"{base}-map", f".{fmt}"
        # Monisivuinen syöte: yksi kuva per sivu, deterministiset nimet <stem>-<sivu>.<ext>
        if len(pages) == 1:
            targets = [(stem, pages[0][1])]
        else:
            slugs = unique_slugs([name for name, _ in pages])
            targets = [(f"{stem}-{slug}", p) for slug, (_, p) in zip(slugs, pages)]
        for page_stem, page_parser in targets:
            puml_path = page_stem + '.puml'
            write_text_file(generate_plantuml(page_parser), puml_path)
            export_with_plantuml_cli(puml_path, page_stem + ext, fmt)
        return

    # Draw.io pipeline: oletuksena mxfile-kääre (pakkaamaton), jokainen sivu omana <diagram>-elementtinä
    before = [len(p.warnings) for _, p in pages]
    if args.bare:
        xml_content = edgy_parser.generate_xml()
    else:
        xml_content = build_mxfile([(name, p.generate_xml()) for name, p in pages])
    report_layout_warnings(pages, before)
    if args.output:
        if fmt != 'drawio':
            output_path = args.output
        else:
            output_path = args.output if args.output.endswith('.drawio') else args.output + '.drawio'
    else:
        facet = edgy_parser.facet if edgy_parser.facet != 'all' else 'edgy'
        base_name = f"{facet}-map"
        if fmt == 'drawio':
            output_path = f"{base_name}.drawio"
        else:
            output_path = f"{base_name}.drawio.{fmt}"

    temp_drawio_path = output_path if fmt == 'drawio' else output_path.replace(f'.{fmt}', '.drawio')
    write_drawio_file(xml_content, temp_drawio_path)

    def write_qa(previews, manifest=None):
        # qa.json: samat luvut evalille, assessmentin Phase 5:lle ja katselmoijalle; hyväksyntäkentät jäävät null.
        # CLI-vienti: manifesti rakennetaan ennen vientiä (lint lukee .drawion) mutta kirjoitetaan vasta kun vienti onnistui.
        if not args.qa:
            return
        manifest = manifest or build_qa(previews)
        qa_path = edgy_qa.write_manifest(temp_drawio_path, manifest)
        t = manifest['totals']
        print(f"QA manifest: {qa_path} — lint {t['lint_errors']}/{t['lint_warnings']}, visual {t['visual']}, "
              f"layout {t['layout_quality']}; visual_approval and semantic_approval are null until a person sets them")

    def build_qa(previews):
        gen_warnings = [w for _, p in pages for w in p.warnings]
        return edgy_qa.build_manifest(temp_drawio_path, pages, input_path=args.input if os.path.exists(args.input) else None,
                                      preset=native_preset, previews=previews, generator_warnings=gen_warnings,
                                      layout_quality=not args.no_layout_quality, output_path=output_path)

    if fmt != 'drawio' and args.engine == 'native':
        if fmt == 'pdf':
            print("Error: the native engine renders svg/png only; use --engine drawio for pdf", file=sys.stderr)
            sys.exit(2)
        results = edgy_render.render_file(temp_drawio_path, png=(fmt == 'png'),
                                          base=os.path.splitext(os.path.basename(output_path))[0],
                                          out_dir=os.path.dirname(os.path.abspath(output_path)),
                                          publication=args.publication, preset=native_preset,
                                          heading=heading, footnote=footnote)
        for r in results:
            label = f" [page {r['page']}]" if r['page'] else ""
            print(f"Successfully rendered: {r['png'] or r['svg']}{label}")
        if fmt == 'png' and not all(r['png'] for r in results):
            missing = [r['svg'] for r in results if not r['png']]
            print(f"Error: PNG not produced for {len(missing)} page(s) (no Chromium/Chrome found — set EDGY_CHROMIUM=<binary>, "
                  f"or use --format svg); the SVG files are kept{'; no qa.json written' if args.qa else ''}.", file=sys.stderr)
            sys.exit(1)
        write_qa(results)
    elif fmt != 'drawio':
        manifest = build_qa(None) if args.qa else None      # lint reads the .drawio, which the export removes on success
        if not export_with_drawio_cli(temp_drawio_path, output_path, fmt, extra_export_args):
            print(f"Error: {output_path} was not produced{'; no qa.json written' if args.qa else ''}. "
                  f"The .drawio file is kept at {temp_drawio_path}.", file=sys.stderr)
            sys.exit(1)
        if manifest is not None:            # --qa: name the delivery file confirmed above, then write
            manifest['output'] = os.path.basename(output_path)
            manifest['outputs'] = [os.path.basename(output_path)]
            write_qa(None, manifest)
    else:
        print(f"EDGY diagram created: {output_path}")
        previews = None
        if args.preview:
            previews = render_preview(output_path, publication=args.publication, preset=native_preset,
                                      heading=heading, footnote=footnote)
            if previews is None:
                print("The .drawio file was written but the mandatory preview was not — "
                      "fix the error above before delivery.", file=sys.stderr)
                sys.exit(3)
        write_qa(previews)

if __name__ == "__main__":
    main()
