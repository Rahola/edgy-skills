#!/usr/bin/env python3
"""validate-edgy-model.py — the checkout's entry point to the edgy-model validator.

The validator ships with edgy-assessment (scripts/validate_edgy_model.py), so an installed skill has it;
this file runs that code and re-exports its names for the tests. Usage and exit codes: see that module.
"""
import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "skills" / "architecture" / "edgy-assessment" / "scripts" / \
    "validate_edgy_model.py"
_spec = importlib.util.spec_from_file_location("validate_edgy_model", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})

if __name__ == "__main__":
    sys.exit(_mod.main())
