#!/usr/bin/env python3
"""
validate-edgy-model.py — Validate an edgy-model.json against
skills/architecture/edgy-assessment/assets/edgy-model.schema.json using only
the Python standard library (a small subset of JSON Schema: type, required,
properties, items, enum, minItems/maxItems, minLength, minimum/maximum,
pattern, $ref within the same document).

Usage:
  python3 tools/validate-edgy-model.py <model.json> [more.json ...]
  python3 tools/validate-edgy-model.py --schema other.schema.json model.json

Exit 0 when every file is valid, 1 otherwise. Findings are printed as
`file: <json-pointer>: message`.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = REPO / "skills" / "architecture" / "edgy-assessment" / "assets" / "edgy-model.schema.json"
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}


def resolve(ref, root):
    assert ref.startswith("#/"), f"only local refs supported: {ref}"
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(instance, schema, root, path, out):
    if "$ref" in schema:
        schema = resolve(schema["$ref"], root)
    t = schema.get("type")
    if t:
        py = TYPES[t]
        ok = isinstance(instance, py) and not (t in ("integer", "number") and isinstance(instance, bool))
        if not ok:
            out.append(f"{path or '/'}: expected {t}, got {type(instance).__name__}")
            return
    if "enum" in schema and instance not in schema["enum"]:
        out.append(f"{path or '/'}: {instance!r} is not one of {schema['enum']}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(f"{path}: string shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            out.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            out.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            out.append(f"{path}: {instance} > maximum {schema['maximum']}")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                out.append(f"{path or '/'}: missing required property '{key}'")
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                validate(instance[key], sub, root, f"{path}/{key}", out)
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            out.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            out.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(instance):
                validate(item, schema["items"], root, f"{path}/{i}", out)


def validate_model(model, schema):
    out = []
    validate(model, schema, schema, "", out)
    # semantic checks beyond the schema — every access is type-guarded, because
    # the schema pass above only *records* type errors; it does not stop here
    if not isinstance(model, dict):
        return out
    elems = model.get("elements")
    elems = elems if isinstance(elems, dict) else {}
    links = model.get("core_links")
    for i, link in enumerate(links if isinstance(links, list) else []):
        if not isinstance(link, dict):
            continue  # already reported as a type error
        if not any(k in link for k in ("verb_en", "verb_fi", "verb_fr", "verb_de")):
            out.append(f"/core_links/{i}: at least one verb_<lang> is required")
    dives = model.get("suggested_deep_dives")
    for i, dd in enumerate(dives if isinstance(dives, list) else []):
        if not isinstance(dd, dict):
            continue
        pair = dd.get("pair")
        for p in pair if isinstance(pair, list) else []:
            if isinstance(p, str) and p in elems and not elems[p]:
                out.append(f"/suggested_deep_dives/{i}: pair element '{p}' is empty in the model")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate edgy-model.json files")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    args = ap.parse_args(argv)
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    rc = 0
    for f in args.files:
        try:
            model = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"{f}: cannot read JSON: {e}")
            rc = 1
            continue
        findings = validate_model(model, schema)
        if findings:
            rc = 1
            for x in findings:
                print(f"{f}: {x}")
        else:
            print(f"{f}: valid")
    return rc


if __name__ == "__main__":
    sys.exit(main())
