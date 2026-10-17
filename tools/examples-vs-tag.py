#!/usr/bin/env python3
"""examples-vs-tag.py — v2.5.0 examples change only where a feature changes them (test plan G05).

Every edgy-diagram expected-*.drawio of the pinned tag (default v2.4.0) is compared with the same file
today. Both are the generator's output for the same input with the canonical glyph tables
(EDGY_TEXT_TABLE_ONLY=1, regen-examples.sh); test_examples.py keeps today's files current, so this compares
the tag's generator with today's. The comparison ignores only the edgy* style markers
(compare-style-only.py). An example may differ only when it is listed, with the feature that changes it, in
tools/fixtures/v2.5.0-example-exceptions.txt.

Also checked:
- negative control: one cell moved by 1 px and one label character changed are both reported;
- the named regression tests still exist under their names.

Usage: python3 tools/examples-vs-tag.py [--tag v2.4.0]
Exit 0 pass, 1 an unlisted difference / a failed control / a missing test, 2 the tag cannot be read.
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = 'skills/documentation/edgy-diagram/examples'
EXCEPTIONS = os.path.join(REPO, 'tools', 'fixtures', 'v2.5.0-example-exceptions.txt')
NAMED = {
    'skills/architecture/edgy-assessment/scripts/test_model_diff.py': [
        'test_model_19_transition_draws_what_changes_and_lints_clean',
        'test_model_19_transition_names_the_data_an_integration_carries'],
    'skills/documentation/edgy-diagram/scripts/test_lint.py': ['test_w128_header_under_the_legend'],
}
_spec = importlib.util.spec_from_file_location('cso', os.path.join(REPO, 'tools', 'compare-style-only.py'))
cso = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cso)
KEYS = cso.DEFAULT_KEYS + ('edgyTrace', 'edgyNotation')


def git(*args):
    return subprocess.run(['git', '-C', REPO, *args], capture_output=True, text=True)


def ensure_tag(tag):
    if git('rev-parse', '-q', '--verify', f'refs/tags/{tag}').returncode == 0:
        return True
    git('fetch', '--depth=1', 'origin', 'tag', tag)          # a shallow CI checkout has no tags
    return git('rev-parse', '-q', '--verify', f'refs/tags/{tag}').returncode == 0


def exceptions():
    out = {}
    if os.path.isfile(EXCEPTIONS):
        for ln in open(EXCEPTIONS, encoding='utf-8'):
            ln = ln.strip()
            if ln and not ln.startswith('#'):
                name, _, why = ln.partition(' ')
                out[name] = why.strip()
    return out


def same(old, new):
    return cso.strip_keys(old, KEYS).splitlines() == cso.strip_keys(new, KEYS).splitlines()


def negative_control(xml):
    """Move one cell by 1 px and change one label character: each must be reported on its own."""
    moved = re.sub(r'(<mxGeometry x=")(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), xml, count=1)
    relabel = re.sub(r'value="([A-Za-z])', lambda m: 'value="' + ('Q' if m.group(1) != 'Q' else 'Z'), xml, count=1)
    return moved != xml and relabel != xml and not same(xml, moved) and not same(xml, relabel)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tag', default='v2.4.0')
    args = ap.parse_args(argv)
    if not ensure_tag(args.tag):
        print(f'examples-vs-tag: cannot read tag {args.tag} (git fetch --tags)', file=sys.stderr)
        return 2
    listed = exceptions()
    names = [p for p in git('ls-tree', '--name-only', args.tag, EXAMPLES + '/').stdout.split()
             if os.path.basename(p).startswith('expected-') and p.endswith('.drawio')]
    if not names:
        print(f'examples-vs-tag: no expected-*.drawio in {args.tag}', file=sys.stderr)
        return 2
    bad, used = [], set()
    for path in names:
        old = git('show', f'{args.tag}:{path}').stdout
        cur = os.path.join(REPO, path)
        base = os.path.basename(path)
        if not os.path.isfile(cur):
            bad.append(f'{base}: removed since {args.tag}')
            continue
        new = open(cur, encoding='utf-8').read()
        if same(old, new):
            continue
        if base in listed:
            used.add(base)
            continue
        bad.append(f'{base}: differs from {args.tag} and is not in the exceptions list')
        cso.compare(old, new, KEYS, base)
    for base in sorted(set(listed) - used):
        bad.append(f'{base}: listed as an exception but unchanged — remove it from the list')
    first = open(os.path.join(REPO, names[0]), encoding='utf-8').read()
    if not negative_control(first):
        bad.append('negative control: a 1 px move or a one-character label change was not reported')
    for f, tests in NAMED.items():
        src = open(os.path.join(REPO, f), encoding='utf-8').read()
        for t in tests:
            if not re.search(rf'^def {t}\(', src, re.M):
                bad.append(f'named regression {t} is missing from {f}')
    if bad:
        print('\n'.join(bad), file=sys.stderr)
        return 1
    print(f'examples-vs-tag: {len(names)} examples of {args.tag} unchanged ({len(used)} listed exceptions), '
          f'negative control reported, {sum(len(t) for t in NAMED.values())} named regressions present')
    return 0


if __name__ == '__main__':
    sys.exit(main())
