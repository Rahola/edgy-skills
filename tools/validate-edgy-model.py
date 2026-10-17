#!/usr/bin/env python3
"""
validate-edgy-model.py — Validate an edgy-model.json against
skills/architecture/edgy-assessment/assets/edgy-model.schema.json using only
the Python standard library (a small subset of JSON Schema: type, required,
properties, additionalProperties: false, items, enum, minItems/maxItems, minLength, minimum/maximum,
pattern, oneOf / anyOf, $ref within the same document).

Beyond the schema (model format 1.9, edgy-assessment 1.10.0):
  * every relationships[] source_id / target_id is the id of an element;
  * a model that uses a 1.9 structure (relationships[], elements.people,
    organisation as an array, asset kind / hosting / owner / time /
    criticality / master) must declare schema_version 1.9 or later — an old
    writer stays an old writer.

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
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool,
         "null": type(None)}


def resolve(ref, root):
    assert ref.startswith("#/"), f"only local refs supported: {ref}"
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(instance, schema, root, path, out):
    if "$ref" in schema:
        schema = resolve(schema["$ref"], root)
    for key in ("oneOf", "anyOf"):
        if key in schema:
            results = []
            for alt in schema[key]:
                sub = []
                validate(instance, alt, root, path, sub)
                results.append(sub)
            passing = sum(1 for r in results if not r)
            if key == "anyOf" and passing == 0 or key == "oneOf" and passing != 1:
                if passing > 1:
                    out.append(f"{path or '/'}: matches {passing} alternatives of oneOf, expected exactly one")
                else:
                    best = min(results, key=len)
                    out.append(f"{path or '/'}: matches none of the {key} alternatives ({best[0] if best else 'no detail'})")
    t = schema.get("type")
    if t:
        kinds = t if isinstance(t, list) else [t]
        ok = any(isinstance(instance, TYPES[k]) and not (k in ("integer", "number") and isinstance(instance, bool))
                 for k in kinds)
        if not ok:
            out.append(f"{path or '/'}: expected {' or '.join(kinds)}, got {type(instance).__name__}")
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
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in schema.get("properties", {}):
                    out.append(f"{path or '/'}: unknown property '{key}' (allowed: {', '.join(schema['properties'])})")
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
    if not str(schema.get("$id", "")).endswith("edgy-model.schema.json"):
        return out           # another schema (qa.json, edgy-graph): no edgy-model semantics
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
    out.extend(_relationship_ids(model, elems))
    out.extend(_version_gate(model, elems))
    dives = model.get("suggested_deep_dives")
    for i, dd in enumerate(dives if isinstance(dives, list) else []):
        if not isinstance(dd, dict):
            continue
        pair = dd.get("pair")
        for p in pair if isinstance(pair, list) else []:
            if isinstance(p, str) and p in elems and not elems[p]:
                out.append(f"/suggested_deep_dives/{i}: pair element '{p}' is empty in the model")
    return out


ASSET_19_KEYS = ("kind", "hosting", "owner", "time", "criticality", "master")


def _element_items(elems):
    for t, v in elems.items():
        for e in (v if isinstance(v, list) else [v]):
            if isinstance(e, dict):
                yield t, e


def _relationship_ids(model, elems):
    rels = model.get("relationships")
    if not isinstance(rels, list):
        return []
    ids = {e["id"] for _t, e in _element_items(elems) if isinstance(e.get("id"), str)}
    out = []
    for i, r in enumerate(rels):
        if not isinstance(r, dict):
            continue
        for k in ("source_id", "target_id"):
            v = r.get(k)
            if isinstance(v, str) and v not in ids:
                out.append(f"/relationships/{i}/{k}: '{v}' is not the id of an element of the model (E015 dangling)")
    return out


def _version(model):
    m = re.match(r"^(\d+)\.(\d+)$", str(model.get("schema_version") or "1.8"))
    return (int(m.group(1)), int(m.group(2))) if m else (1, 8)


def structures_19(model):
    """The 1.9 structures a model uses (empty for a pure 1.8 model)."""
    elems = model.get("elements") if isinstance(model.get("elements"), dict) else {}
    found = []
    if "relationships" in model:
        found.append("relationships[]")
    if "people" in elems:
        found.append("elements.people")
    if isinstance(elems.get("organisation"), list):
        found.append("organisation as an array")
    keys = sorted({k for e in (elems.get("asset") or []) if isinstance(e, dict) for k in ASSET_19_KEYS if k in e})
    if keys:
        found.append("asset " + " / ".join(keys))
    if any(isinstance(e, dict) and "gaps" in e for e in (elems.get("capability") or [])):
        found.append("capability gaps")
    if any(isinstance(e, dict) and "band" in e for e in (elems.get("process") or [])):
        found.append("process band")
    return found


def _version_gate(model, elems):
    used = structures_19(model)
    if used and _version(model) < (1, 9):
        return [f"/schema_version: the model uses 1.9 structures ({', '.join(used)}) but declares "
                f"{model.get('schema_version') or 'no version (1.8)'} — set schema_version to \"1.9\""]
    return []


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
