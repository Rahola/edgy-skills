#!/usr/bin/env python3
"""Rebuild the fictional fixture, checking generated drift and its size budget.
This is repository verification, not a general-purpose presentation builder.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'docs/examples/executive-walkthrough'


def main():
    out = EXAMPLE / 'index.html'
    before = out.read_bytes()
    subprocess.run([sys.executable, str(EXAMPLE / 'build.py')], cwd=ROOT, check=True)
    after = out.read_bytes()
    # Restore the committed candidate on failure; this check must not leave a
    # rewritten artefact that can hide drift on a subsequent CI step.
    if before != after:
        out.write_bytes(before)
        print('walkthrough: generated index.html differs; rebuild and commit it', file=sys.stderr)
        return 1
    if len(after) > 512 * 1024:
        print('walkthrough: Acme fixture exceeds 512 KiB budget', file=sys.stderr)
        return 1
    print(f'walkthrough: byte-identical rebuild, {len(after)} bytes (budget 512 KiB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
