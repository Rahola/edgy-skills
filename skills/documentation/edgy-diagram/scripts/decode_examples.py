"""Decode compressed draw.io <diagram> payloads into readable XML.

Walks examples/official/*.drawio.xml, extracts each <diagram> body,
base64-decodes, raw-deflate-inflates, URL-decodes, and writes
pretty-printed mxGraphModel XML under examples/official/decoded/.
"""

from __future__ import annotations

import base64
import re
import sys
import urllib.parse
import xml.dom.minidom
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "examples" / "official"
TARGET_DIR = SOURCE_DIR / "decoded"


def decode_diagram(payload: str) -> str:
    raw = base64.b64decode(payload)
    inflated = zlib.decompress(raw, -zlib.MAX_WBITS)
    return urllib.parse.unquote(inflated.decode("utf-8"))


def pretty(xml_text: str) -> str:
    dom = xml.dom.minidom.parseString(xml_text)
    return dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def process_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<diagram[^>]*>(.*?)</diagram>", text, re.DOTALL)
    if not match:
        return False, "no <diagram> element"
    payload = match.group(1).strip()
    try:
        xml_text = decode_diagram(payload)
    except Exception as exc:  # noqa: BLE001
        return False, f"decode failed: {exc}"
    try:
        formatted = pretty(xml_text)
    except Exception:
        formatted = xml_text
    out_path = TARGET_DIR / (path.stem + ".xml")
    out_path.write_text(formatted, encoding="utf-8")
    return True, str(out_path.relative_to(ROOT))


def main() -> int:
    if not SOURCE_DIR.exists():
        print(f"Source dir not found: {SOURCE_DIR}", file=sys.stderr)
        return 1
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SOURCE_DIR.glob("*.drawio.xml"))
    if not files:
        print(f"No .drawio.xml files in {SOURCE_DIR}", file=sys.stderr)
        return 1
    ok = fail = 0
    for path in files:
        success, msg = process_file(path)
        prefix = "OK " if success else "ERR"
        print(f"{prefix} {path.name}: {msg}")
        ok += success
        fail += not success
    print(f"\nDecoded {ok}/{ok + fail} files into {TARGET_DIR.relative_to(ROOT)}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
