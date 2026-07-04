#!/usr/bin/env python3
"""
EDGY Generator - Pääskripti EDGY-kaavioiden generointiin
"""

import os
import sys
import argparse
from edgy_parser import EDGYParser
from edgy_to_plantuml import generate_plantuml

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

# Export-presetit: (format, extra draw.io CLI args)
# - presentation: 1920x1080 PNG, 150 DPI
# - print: A3 PDF, 300 DPI, valkoinen tausta
# - web: läpinäkyvä SVG
EXPORT_PRESETS = {
    'presentation': ('png', ['--width', '1920', '--scale', '1.5', '-b', '20']),
    'print':        ('pdf', ['--scale', '3.0', '-b', '30']),
    'web':          ('svg', ['-t', '-b', '10']),
}


def export_with_drawio_cli(input_path: str, output_path: str, format: str, extra_args: list = None) -> None:
    """Vie draw.io CLI:llä"""
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
            print("Warning: draw.io CLI not found. Skipping export.")
            return

        # Suorita vienti
        cmd = [drawio_cmd, '-x', '-f', format, '-e']
        if extra_args:
            cmd.extend(extra_args)
        else:
            cmd.extend(['-b', '10'])
        cmd.extend(['-o', output_path, input_path])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Successfully exported to {output_path}")
            # Poista väliaikainen .drawio tiedosto
            os.remove(input_path)
        else:
            print(f"Export failed: {result.stderr}")

    except Exception as e:
        print(f"Export error: {e}")


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
    parser.add_argument('--engine', choices=['drawio', 'plantuml'], default='drawio',
                       help='Render engine for png/svg/pdf (default drawio). Ignored for drawio/plantuml/puml formats.')
    parser.add_argument('--preset', choices=list(EXPORT_PRESETS.keys()),
                       help='Export preset (presentation/print/web) — ohittaa --format')
    parser.add_argument('--output', help='Output file path')

    args = parser.parse_args()

    extra_export_args = None
    if args.preset:
        args.format, extra_export_args = EXPORT_PRESETS[args.preset]

    # Lue syöte
    if os.path.exists(args.input):
        input_content = read_input_file(args.input)
    else:
        input_content = args.input

    # Jäsennä EDGY
    edgy_parser = EDGYParser()
    edgy_parser.parse_input(input_content)

    # Normalisoi formaatti
    fmt = 'puml' if args.format == 'plantuml' else args.format

    # PlantUML-source haara
    if fmt == 'puml':
        puml_content = generate_plantuml(edgy_parser)
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
        puml_content = generate_plantuml(edgy_parser)
        base = edgy_parser.map_type or edgy_parser.facet or 'edgy'
        if base == 'all':
            base = 'edgy'
        if args.output:
            output_path = args.output
            puml_path = os.path.splitext(args.output)[0] + '.puml'
        else:
            output_path = f"{base}-map.{fmt}"
            puml_path = f"{base}-map.puml"
        write_text_file(puml_content, puml_path)
        export_with_plantuml_cli(puml_path, output_path, fmt)
        return

    # Draw.io pipeline
    xml_content = edgy_parser.generate_xml()
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

    if fmt != 'drawio':
        export_with_drawio_cli(temp_drawio_path, output_path, fmt, extra_export_args)
    else:
        print(f"EDGY diagram created: {output_path}")

if __name__ == "__main__":
    main()
