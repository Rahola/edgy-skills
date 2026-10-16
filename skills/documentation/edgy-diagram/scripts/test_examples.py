#!/usr/bin/env python3
"""Golden test: every shipped examples/expected-*.drawio equals what the generator
writes for its input today (and expected-purpose.puml for purpose-map.txt).

Before 2.8.0 nothing checked this. Text is measured with the glyph tables (as in CI and
tools/regen-examples.sh); a local Pillow measures with real fonts and would differ by a
pixel here and there. A generator change that moves output must regenerate the examples
(bash tools/regen-examples.sh) in the same commit — the diff then shows the
change for review."""

import glob
import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

os.environ['EDGY_TEXT_TABLE_ONLY'] = '1'   # the examples are written with the glyph tables (regen-examples.sh)
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from edgy_document import parse_document, build_mxfile  # noqa: E402
from edgy_to_plantuml import generate_plantuml  # noqa: E402


def expected_name(txt: str) -> str:
    name = os.path.basename(txt)[:-4]
    for suffix in ('-facet', '-map'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return os.path.join(SKILL, 'examples', f'expected-{name}.drawio')


def test_every_expected_example_is_current():
    cwd = os.getcwd()
    os.chdir(SKILL)                     # layout_from: paths in the inputs are relative to the skill root
    stale = []
    try:
        inputs = sorted(glob.glob(os.path.join('examples', '*.txt')))
        assert inputs, 'no example inputs found'
        for txt in inputs:
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                pages = parse_document(open(txt, encoding='utf-8').read())
                xml = build_mxfile([(n, p.generate_xml()) for n, p in pages])
            target = expected_name(txt)
            if not os.path.exists(target) or open(target, encoding='utf-8').read() != xml:
                stale.append(os.path.relpath(target, SKILL))
        pages = parse_document(open(os.path.join('examples', 'purpose-map.txt'), encoding='utf-8').read())
        puml = ''.join(generate_plantuml(p) + ('\n' if i else '') for i, (_, p) in enumerate(pages))
        if open(os.path.join('examples', 'expected-purpose.puml'), encoding='utf-8').read() != puml:
            stale.append('examples/expected-purpose.puml')
    finally:
        os.chdir(cwd)
    assert not stale, f"stale examples (run: bash tools/regen-examples.sh): {', '.join(stale)}"


def main():
    test_every_expected_example_is_current()
    print('test_every_expected_example_is_current passed\n\nAll 1 example tests passed')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'\nTest failed: {e}')
        sys.exit(1)
