#!/usr/bin/env python3
"""
edgy_text.py — text measurement for EDGY diagrams, standard library only.

draw.io and the native preview render labels in Helvetica / Arial. A single
"average character width" cannot tell `Ticketing` from `Illinois`, so long
bold titles that the estimate says fit end up overflowing the box. This
module measures with per-glyph advance widths of the Adobe Core 14
Helvetica and Helvetica-Bold fonts (the metrics Arial was designed to
match), falling back to the base letter for accented characters and to an
average for anything else.

When Pillow and a matching TrueType font happen to be installed the exact
font is used instead; nothing here requires them.

API
  measure(text, size, bold=False) -> px        width of one line
  wrap(text, width, size, bold=False) -> lines  greedy word wrap by measured width
  lines_needed(text, width, size, bold=False)  -> int
  backend() -> 'pillow:<font>' | 'table'
"""

import os
import unicodedata
from functools import lru_cache
from typing import List, Optional

# Advance widths in 1/1000 em (Adobe Core 14 AFM: Helvetica, Helvetica-Bold).
_REGULAR = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667, "'": 191, '(': 333, ')': 333,
    '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556,
    '4': 556, '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 278, ';': 278, '<': 584, '=': 584,
    '>': 584, '?': 556, '@': 1015, 'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
    'H': 722, 'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667, 'Q': 778,
    'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667, 'Y': 667, 'Z': 611, '[': 278,
    '\\': 278, ']': 278, '^': 469, '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556,
    'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556, 'o': 556,
    'p': 556, 'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500,
    'z': 500, '{': 334, '|': 260, '}': 334, '~': 584,
    '–': 556, '—': 1000, '•': 350, '…': 1000, '€': 556, '°': 400, '§': 556, '«': 556, '»': 556,
    '‘': 222, '’': 222, '“': 333, '”': 333, '×': 584, '≤': 584, '≥': 584, '−': 584, '→': 1000, '↔': 1000,
    'ß': 611, 'æ': 889, 'Æ': 1000, 'ø': 611, 'Ø': 778, 'þ': 556, 'ð': 556,
}
_BOLD = {
    ' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722, "'": 238, '(': 333, ')': 333,
    '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556,
    '4': 556, '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 333, ';': 333, '<': 584, '=': 584,
    '>': 584, '?': 611, '@': 975, 'A': 722, 'B': 722, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
    'H': 722, 'I': 278, 'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778, 'P': 667, 'Q': 778,
    'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667, 'Y': 667, 'Z': 611, '[': 333,
    '\\': 278, ']': 333, '^': 584, '_': 556, '`': 333, 'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556,
    'f': 333, 'g': 611, 'h': 611, 'i': 278, 'j': 278, 'k': 556, 'l': 278, 'm': 889, 'n': 611, 'o': 611,
    'p': 611, 'q': 611, 'r': 389, 's': 556, 't': 333, 'u': 611, 'v': 556, 'w': 778, 'x': 556, 'y': 556,
    'z': 500, '{': 389, '|': 280, '}': 389, '~': 584,
    '–': 556, '—': 1000, '•': 350, '…': 1000, '€': 556, '°': 400, '§': 556, '«': 556, '»': 556,
    '‘': 278, '’': 278, '“': 500, '”': 500, '×': 584, '≤': 584, '≥': 584, '−': 584, '→': 1000, '↔': 1000,
    'ß': 611, 'æ': 889, 'Æ': 1000, 'ø': 611, 'Ø': 778, 'þ': 611, 'ð': 611,
}
_AVERAGE = {False: 556, True: 611}

# Pillow + a metric-compatible TrueType font, when both exist. Never required.
_FONT_CANDIDATES = {
    False: ('LiberationSans-Regular.ttf', 'Arimo-Regular.ttf', 'Arial.ttf', 'arial.ttf', 'Helvetica.ttc', 'DejaVuSans.ttf'),
    True: ('LiberationSans-Bold.ttf', 'Arimo-Bold.ttf', 'Arial Bold.ttf', 'arialbd.ttf', 'Helvetica.ttc', 'DejaVuSans-Bold.ttf'),
}
_FONT_DIRS = ('/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts'),
              '/Library/Fonts', '/System/Library/Fonts', r'C:\Windows\Fonts')


@lru_cache(maxsize=4)
def _pillow_font(bold: bool, size: int):
    if os.environ.get('EDGY_TEXT_TABLE_ONLY'):
        return None
    try:
        from PIL import ImageFont  # type: ignore
    except Exception:
        return None
    for name in _FONT_CANDIDATES[bold]:
        for d in _FONT_DIRS:
            for root, _dirs, files in os.walk(d):
                if name in files:
                    try:
                        return ImageFont.truetype(os.path.join(root, name), size)
                    except Exception:
                        continue
    return None


def backend(bold: bool = False) -> str:
    f = _pillow_font(bold, 100)
    return f'pillow:{os.path.basename(f.path)}' if f is not None and getattr(f, 'path', None) else 'table'


def _glyph(ch: str, bold: bool) -> int:
    table = _BOLD if bold else _REGULAR
    if ch in table:
        return table[ch]
    base = unicodedata.normalize('NFD', ch)[0]       # ä → a, é → e, Å → A
    if base in table:
        return table[base]
    if unicodedata.category(ch).startswith('M'):      # combining mark on its own
        return 0
    return _AVERAGE[bold]


def measure(text: str, size: float, bold: bool = False) -> float:
    """Width in px of one line of `text` at font size `size` px."""
    if not text:
        return 0.0
    f = _pillow_font(bool(bold), 100)
    if f is not None:
        try:
            return f.getlength(text) * size / 100.0
        except Exception:
            pass
    return sum(_glyph(ch, bool(bold)) for ch in text) / 1000.0 * size


def wrap(text: str, width: float, size: float, bold: bool = False) -> List[str]:
    """Greedy word wrap to `width` px. A single word longer than the width
    stays on its own line (it overflows visibly rather than being cut)."""
    words = text.split()
    if not words:
        return ['']
    lines: List[str] = []
    cur = ''
    for w in words:
        cand = f'{cur} {w}'.strip()
        if cur and measure(cand, size, bold) > width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def lines_needed(text: str, width: float, size: float, bold: bool = False) -> int:
    return len(wrap(text, width, size, bold))


def fits(text: str, width: float, height: float, size: float, bold: bool = False, line_h: float = 1.25) -> bool:
    return lines_needed(text, width, size, bold) * size * line_h <= height


def choose_width(text: str, size: float, bold: bool, min_w: float, max_w: float, pad: float = 20.0,
                 step: float = 10.0) -> Optional[float]:
    """Smallest width (multiple of `step`, within [min_w, max_w]) on which
    `text` fits on one line; None when it needs wrapping even at max_w."""
    need = measure(text, size, bold) + pad
    if need > max_w:
        return None
    w = max(min_w, need)
    return float(int(-(-w // step)) * step)
