#!/usr/bin/env python3
"""compare-style-only.py — two draw.io files are equal once the edgy* style keys are removed.

Used once when the identity markers of extension contract 1 were introduced
(edgy-diagram 2.8.0): every regenerated expected-*.drawio must equal its
previous version except for the new `edgyId` / `edgyIdSource` / `edgyType` /
`edgyKind` / `edgyFacet` / `edgyOcc` style keys — geometry, labels and every
other style key unchanged. Also runnable on any pair:

  python3 tools/compare-style-only.py OLD.drawio NEW.drawio [--keys edgyId,edgyType]
  python3 tools/compare-style-only.py --git-ref HEAD FILE...   # compare with the committed version

Exit 0 equal, 1 different (prints the first differences).
"""
import argparse
import re
import subprocess
import sys

DEFAULT_KEYS = ('edgyId', 'edgyIdSource', 'edgyType', 'edgyKind', 'edgyFacet', 'edgyOcc')


def strip_keys(xml: str, keys) -> str:
    pat = re.compile(r'(?:' + '|'.join(re.escape(k) for k in keys) + r')=[^;"]*;')
    return pat.sub('', xml)


def compare(old: str, new: str, keys, label: str) -> bool:
    a, b = strip_keys(old, keys).splitlines(), strip_keys(new, keys).splitlines()
    if a == b:
        return True
    shown = 0
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f"{label}:{i + 1}\n  - {x.strip()[:160]}\n  + {y.strip()[:160]}")
            shown += 1
            if shown >= 5:
                break
    if len(a) != len(b):
        print(f"{label}: {len(a)} vs {len(b)} lines")
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--git-ref', help='compare each FILE with its version at this git ref')
    ap.add_argument('--keys', default=','.join(DEFAULT_KEYS))
    args = ap.parse_args(argv)
    keys = [k for k in args.keys.split(',') if k]
    ok = True
    if args.git_ref:
        for f in args.files:
            try:
                old = subprocess.run(['git', 'show', f'{args.git_ref}:{f}'], capture_output=True, text=True, check=True).stdout
            except subprocess.CalledProcessError:
                print(f"{f}: not in {args.git_ref} (new file) — skipped")
                continue
            ok &= compare(old, open(f, encoding='utf-8').read(), keys, f)
    else:
        if len(args.files) != 2:
            ap.error('give OLD and NEW, or --git-ref REF FILE...')
        ok = compare(open(args.files[0], encoding='utf-8').read(), open(args.files[1], encoding='utf-8').read(), keys,
                     args.files[1])
    print('style-only: equal' if ok else 'style-only: DIFFERENT')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
