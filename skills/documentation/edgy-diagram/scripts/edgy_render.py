#!/usr/bin/env python3
"""
edgy_render.py — CLI-free preview of EDGY draw.io diagrams.

Renders every page of a .drawio file (bare mxGraphModel or mxfile) to SVG
with the Python standard library only, and to PNG when a headless Chromium /
Chrome binary is available. The output is an *approximation* of draw.io's
rendering (fonts, wrapping and edge routing differ) — good enough to review
layout, overlaps, text fit and routing before delivery, not a substitute for
the draw.io CLI export when publication quality is required.

Usage:
  python3 edgy_render.py FILE.drawio [--out DIR] [--no-png] [--scale 1.5]

Outputs <base>.svg / <base>.png for a single page, <base>-<page>.svg / .png
per page for multi-page files. Exit 0 when SVG was written (PNG is optional
and reported), 2 on unreadable input.

Chromium lookup order: $EDGY_CHROMIUM, then chromium / chromium-browser /
google-chrome / chrome / headless_shell on PATH, then well-known install
paths (Playwright browsers, macOS app bundle, Windows Program Files).
"""

import argparse
import glob
import html
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edgy_document import load_pages_from_file, slugify  # noqa: E402

CHAR_W = 0.55
LINE_H = 1.2
FONT = "Helvetica, Arial, sans-serif"


def style_dict(style: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for part in (style or '').split(';'):
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
            d[k] = v
        else:
            d[part] = '1'
    return d


def label_lines(value: str) -> List[Tuple[str, bool, Optional[float]]]:
    """Split a draw.io (html) label into (text, bold, fontsize-override) lines."""
    v = value or ''
    v = re.sub(r'<br\s*/?>', '\n', v, flags=re.I)
    v = re.sub(r'</?(div|p)[^>]*>', '\n', v, flags=re.I)
    out = []
    for raw in v.split('\n'):
        bold = bool(re.search(r'<b>|font-weight:\s*bold|<strong>', raw, re.I))
        m = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', raw, re.I)
        size = float(m.group(1)) if m else None
        text = html.unescape(re.sub(r'<[^>]+>', '', raw)).strip()
        if text:
            out.append((text, bold, size))
    return out


def wrap(text: str, width: float, fs: float) -> List[str]:
    maxc = max(int(width / (fs * CHAR_W)), 1)
    words = text.split()
    lines: List[str] = []
    cur = ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxc:
            lines.append(cur)
            cur = w
        else:
            cur = f'{cur} {w}'.strip()
    if cur:
        lines.append(cur)
    return lines or ['']


def esc(s: str) -> str:
    return html.escape(s, quote=True)


class Page:
    def __init__(self, model):
        self.model = model
        root = model.find('root')
        self.cells = {}
        self.order = []
        for c in (root.findall('mxCell') if root is not None else []):
            self.cells[c.get('id')] = c
            self.order.append(c.get('id'))
        self.page_w = float(model.get('pageWidth', 0) or 0)
        self.page_h = float(model.get('pageHeight', 0) or 0)
        self._abs: Dict[str, Tuple[float, float, float, float]] = {}

    def geom(self, c):
        g = c.find('mxGeometry')
        if g is None:
            return None
        return [float(g.get(k, 0) or 0) for k in ('x', 'y', 'width', 'height')]

    def abs_box(self, cid):
        if cid in self._abs:
            return self._abs[cid]
        c = self.cells.get(cid)
        if c is None or c.get('vertex') != '1':
            return None
        g = self.geom(c)
        if g is None:
            return None
        x, y, w, h = g
        p = self.cells.get(c.get('parent'))
        guard = 0
        while p is not None and p.get('vertex') == '1' and guard < 50:
            pg = self.geom(p)
            if pg:
                x += pg[0]
                y += pg[1]
            p = self.cells.get(p.get('parent'))
            guard += 1
        self._abs[cid] = (x, y, w, h)
        return self._abs[cid]


def _side_point(box, side, frac=0.5):
    x, y, w, h = box
    return {
        'left': (x, y + h * frac), 'right': (x + w, y + h * frac),
        'top': (x + w * frac, y), 'bottom': (x + w * frac, y + h),
    }[side]


def _anchor(box, st, prefix, other_box):
    """Point on the box border: from exitX/entryX style if present, else by direction."""
    kx, ky = f'{prefix}X', f'{prefix}Y'
    x, y, w, h = box
    if kx in st and ky in st:
        try:
            fx, fy = float(st[kx]), float(st[ky])
            fx = min(max(fx, 0.0), 1.0)
            fy = min(max(fy, 0.0), 1.0)
            side = 'left' if fx == 0 else 'right' if fx == 1 else 'top' if fy == 0 else 'bottom' if fy == 1 else None
            return (x + w * fx, y + h * fy), side
        except ValueError:
            pass
    if other_box is None:
        return (x + w / 2, y + h / 2), None
    ox, oy, ow, oh = other_box
    dx = (ox + ow / 2) - (x + w / 2)
    dy = (oy + oh / 2) - (y + h / 2)
    if abs(dx) >= abs(dy):
        side = 'right' if dx >= 0 else 'left'
    else:
        side = 'bottom' if dy >= 0 else 'top'
    return _side_point(box, side), side


def _orthogonal(p1, s1, p2, s2, points):
    """Polyline for an orthogonal edge; explicit waypoints win."""
    if points:
        return [p1] + points + [p2]
    (x1, y1), (x2, y2) = p1, p2
    if s1 in ('left', 'right') and s2 in ('left', 'right'):
        mx = (x1 + x2) / 2
        return [p1, (mx, y1), (mx, y2), p2]
    if s1 in ('top', 'bottom') and s2 in ('top', 'bottom'):
        my = (y1 + y2) / 2
        return [p1, (x1, my), (x2, my), p2]
    if s1 in ('left', 'right'):
        return [p1, (x2, y1), p2]
    if s1 in ('top', 'bottom'):
        return [p1, (x1, y2), p2]
    return [p1, p2]


def page_to_svg(page: Page, title: Optional[str] = None) -> str:
    parts: List[str] = []
    markers: Dict[str, str] = {}
    minx = miny = 0.0
    maxx = page.page_w or 0
    maxy = page.page_h or 0
    for cid in page.order:
        b = page.abs_box(cid)
        if b:
            minx = min(minx, b[0])
            miny = min(miny, b[1])
            maxx = max(maxx, b[0] + b[2])
            maxy = max(maxy, b[1] + b[3])

    def marker(kind: str, color: str) -> str:
        key = f'{kind}-{re.sub(r"[^a-zA-Z0-9]", "", color)}'
        if key not in markers:
            if kind == 'classic':
                markers[key] = (f'<marker id="{key}" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
                                f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')
            else:
                markers[key] = (f'<marker id="{key}" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
                                f'<path d="M0,0 L10,5 L0,10" fill="none" stroke="{color}" stroke-width="1.5"/></marker>')
        return key

    # vertices in document order (containers first as draw.io does)
    for cid in page.order:
        c = page.cells[cid]
        if c.get('vertex') != '1':
            continue
        box = page.abs_box(cid)
        if box is None:
            continue
        x, y, w, h = box
        st = style_dict(c.get('style'))
        fill = st.get('fillColor', '#ffffff')
        stroke = st.get('strokeColor', '#000000')
        sw = st.get('strokeWidth', '1')
        dash = ' stroke-dasharray="6,4"' if st.get('dashed') == '1' else ''
        opacity = ''
        if fill == 'none':
            fill = 'none'
        if stroke == 'none':
            stroke = 'none'
        shape = st.get('shape', '')
        is_text = 'text' in st and st.get('text') == '1'
        is_line = st.get('line') == '1'
        if is_line:
            parts.append(f'<line x1="{x}" y1="{y + h / 2}" x2="{x + w}" y2="{y + h / 2}" stroke="{stroke if stroke != "none" else "#cccccc"}" stroke-width="{sw}"/>')
            continue
        if not is_text:
            if 'arrows2.arrow' in shape:
                n = min(float(st.get('dx', 20) or 20), w * 0.3)
                pts = f'{x},{y} {x + w - n},{y} {x + w},{y + h / 2} {x + w - n},{y + h} {x},{y + h}'
                parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
            elif 'person' in shape:
                parts.append(f'<ellipse cx="{x + w / 2}" cy="{y + h * 0.22}" rx="{w * 0.22}" ry="{h * 0.2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
                             f'<path d="M{x},{y + h} v-{h * 0.35} a{w / 2},{h * 0.25} 0 0 1 {w},0 v{h * 0.35} z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            else:
                rx = 0.0
                if st.get('rounded') == '1':
                    arc = float(st.get('arcSize', 30) or 30)
                    rx = min(w, h) * arc / 200.0
                parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}{opacity}/>')
        elif fill not in ('none', '#ffffff', '') and fill.startswith('#'):
            # legend colour chip rendered as small text background
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}"/>')
        # label
        fs_default = float(st.get('fontSize', 12) or 12)
        bold_default = st.get('fontStyle') in ('1', '3', '5', '7')
        color = st.get('fontColor', '#000000')
        align = st.get('align', 'center')
        valign = st.get('verticalAlign', 'middle')
        pad_l = float(st.get('spacingLeft', 0) or 0)
        pad_t = float(st.get('spacingTop', 0) or 0)
        lines_spec = label_lines(c.get('value') or '')
        rows: List[Tuple[str, bool, float]] = []
        for text, bold, size in lines_spec:
            fs = size or fs_default
            for ln in wrap(text, max(w - 10 - pad_l, 20), fs):
                rows.append((ln, bold or bold_default, fs))
        if not rows:
            continue
        total_h = sum(fs * LINE_H for _, _, fs in rows)
        if valign == 'top':
            cy = y + pad_t + 2
        elif valign == 'bottom':
            cy = y + h - total_h - 2
        else:
            cy = y + (h - total_h) / 2
        for ln, bold, fs in rows:
            cy += fs
            if align == 'left':
                tx, anchor = x + 6 + pad_l, 'start'
            elif align == 'right':
                tx, anchor = x + w - 6, 'end'
            else:
                tx, anchor = x + w / 2, 'middle'
            weight = ' font-weight="bold"' if bold else ''
            parts.append(f'<text x="{tx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="{fs}" fill="{color}" text-anchor="{anchor}"{weight}>{esc(ln)}</text>')
            cy += fs * (LINE_H - 1)

    # edges
    for cid in page.order:
        c = page.cells[cid]
        if c.get('edge') != '1':
            continue
        st = style_dict(c.get('style'))
        g = c.find('mxGeometry')
        sb = page.abs_box(c.get('source')) if c.get('source') else None
        tb = page.abs_box(c.get('target')) if c.get('target') else None
        points: List[Tuple[float, float]] = []
        if g is not None:
            arr = g.find("Array[@as='points']")
            if arr is not None:
                for p in arr.findall('mxPoint'):
                    points.append((float(p.get('x', 0)), float(p.get('y', 0))))
        if sb is None or tb is None:
            if g is None:
                continue
            sp = g.find("mxPoint[@as='sourcePoint']")
            tp = g.find("mxPoint[@as='targetPoint']")
            if sp is None or tp is None:
                continue
            p1 = (float(sp.get('x', 0)), float(sp.get('y', 0)))
            p2 = (float(tp.get('x', 0)), float(tp.get('y', 0)))
            path = [p1] + points + [p2]
        else:
            p1, s1 = _anchor(sb, st, 'exit', tb)
            p2, s2 = _anchor(tb, st, 'entry', sb)
            if st.get('edgeStyle') in ('orthogonalEdgeStyle', 'elbowEdgeStyle') or points:
                path = _orthogonal(p1, s1, p2, s2, points)
            else:
                path = [p1, p2]
        color = st.get('strokeColor', '#000000')
        if color == 'none':
            color = '#000000'
        sw = st.get('strokeWidth', '1')
        dash = ' stroke-dasharray="6,4"' if st.get('dashed') == '1' else ''
        end = st.get('endArrow', 'classic')
        attrs = ''
        if end != 'none':
            kind = 'classic' if (end == 'classic' and st.get('endFill', '1') != '0') else 'open'
            attrs += f' marker-end="url(#{marker(kind, color)})"'
        start = st.get('startArrow', 'none')
        if start not in ('none', ''):
            kind = 'classic' if st.get('startFill', '1') != '0' else 'open'
            attrs += f' marker-start="url(#{marker(kind, color)})"'
        d = 'M ' + ' L '.join(f'{px:.1f},{py:.1f}' for px, py in path)
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{dash}{attrs}/>')
        # label near the middle of the path
        lab = ' '.join(t for t, _, _ in label_lines(c.get('value') or ''))
        if lab:
            total = sum(((path[i + 1][0] - path[i][0]) ** 2 + (path[i + 1][1] - path[i][1]) ** 2) ** 0.5 for i in range(len(path) - 1))
            target = total / 2
            mx, my = path[0]
            acc = 0.0
            for i in range(len(path) - 1):
                (ax, ay), (bx, by) = path[i], path[i + 1]
                seg = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
                if acc + seg >= target and seg > 0:
                    t = (target - acc) / seg
                    mx, my = ax + (bx - ax) * t, ay + (by - ay) * t
                    break
                acc += seg
            fs = float(st.get('fontSize', 11) or 11)
            lw = len(lab) * fs * CHAR_W + 8
            fc = st.get('fontColor', '#000000')
            # label sits just above the path so short edges stay visible
            ly = my - fs * 0.6
            parts.append(f'<rect x="{mx - lw / 2:.1f}" y="{ly - fs * 0.85:.1f}" width="{lw:.1f}" height="{fs * 1.3:.1f}" fill="#ffffff" fill-opacity="0.8"/>'
                         f'<text x="{mx:.1f}" y="{ly + fs * 0.2:.1f}" font-family="{FONT}" font-size="{fs}" fill="{fc}" text-anchor="middle">{esc(lab)}</text>')

    pad = 20
    vx, vy = minx - pad, miny - pad
    vw, vh = (maxx - minx) + 2 * pad, (maxy - miny) + 2 * pad
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}" width="{vw:.0f}" height="{vh:.0f}">\n'
            f'<title>{esc(title or "EDGY diagram")}</title>\n<defs>{"".join(markers.values())}</defs>\n'
            f'<rect x="{vx:.0f}" y="{vy:.0f}" width="{vw:.0f}" height="{vh:.0f}" fill="#ffffff"/>\n')
    if page.page_w and page.page_h:
        head += f'<rect x="0" y="0" width="{page.page_w:.0f}" height="{page.page_h:.0f}" fill="none" stroke="#e0e0e0" stroke-dasharray="4,4"/>\n'
    return head + '\n'.join(parts) + '\n</svg>\n'


def find_chromium() -> Optional[str]:
    env = os.environ.get('EDGY_CHROMIUM')
    if env and os.path.isfile(env):
        return env
    for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable', 'chrome', 'headless_shell'):
        p = shutil.which(name)
        if p:
            return p
    patterns = [
        os.path.join(os.environ.get('PLAYWRIGHT_BROWSERS_PATH', ''), '*', 'chrome-linux', 'headless_shell'),
        os.path.join(os.environ.get('PLAYWRIGHT_BROWSERS_PATH', ''), '*', 'chrome-linux', 'chrome'),
        os.path.expanduser('~/.cache/ms-playwright/*/chrome-linux/headless_shell'),
        os.path.expanduser('~/.cache/ms-playwright/*/chrome-linux/chrome'),
        '/opt/pw-browsers/*/chrome-linux/headless_shell',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    ]
    for pat in patterns:
        if not pat.strip('*/'):
            continue
        for hit in sorted(glob.glob(pat)):
            if os.path.isfile(hit):
                return hit
    return None


def svg_to_png(svg_path: str, png_path: str, width: int, height: int, chromium: Optional[str] = None, scale: float = 1.5) -> bool:
    chromium = chromium or find_chromium()
    if not chromium:
        return False
    cmd = [chromium, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
           f'--force-device-scale-factor={scale}', f'--window-size={max(int(width), 200)},{max(int(height), 200)}',
           f'--screenshot={os.path.abspath(png_path)}', 'file://' + os.path.abspath(svg_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and os.path.isfile(png_path)


def render_file(path: str, out_dir: Optional[str] = None, png: bool = True, scale: float = 1.5, base: Optional[str] = None) -> List[dict]:
    """Render every page → [{'page', 'svg', 'png'}]; png is None when not produced."""
    pages = load_pages_from_file(path)
    if not pages:
        raise ValueError('no diagram pages found')
    out_dir = out_dir or os.path.dirname(os.path.abspath(path))
    os.makedirs(out_dir, exist_ok=True)
    base = base or re.sub(r'\.drawio(\.xml)?$', '', os.path.basename(path))
    chromium = find_chromium() if png else None
    results = []
    for i, (name, model) in enumerate(pages, 1):
        page = Page(model)
        svg = page_to_svg(page, name)
        stem = base if len(pages) == 1 else f'{base}-{slugify(name or str(i))}'
        svg_path = os.path.join(out_dir, stem + '.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        png_path = None
        if png and chromium:
            m = re.search(r'width="(\d+)" height="(\d+)"', svg)
            w, h = (int(m.group(1)), int(m.group(2))) if m else (1200, 900)
            candidate = os.path.join(out_dir, stem + '.png')
            if svg_to_png(svg_path, candidate, w, h, chromium, scale):
                png_path = candidate
        results.append({'page': name, 'svg': svg_path, 'png': png_path})
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Render EDGY draw.io diagrams to SVG (and PNG when Chromium is available)')
    ap.add_argument('file')
    ap.add_argument('--out', help='output directory (default: next to the input)')
    ap.add_argument('--no-png', action='store_true', help='write SVG only')
    ap.add_argument('--scale', type=float, default=1.5, help='PNG device scale factor (default 1.5)')
    args = ap.parse_args(argv)
    try:
        results = render_file(args.file, args.out, png=not args.no_png, scale=args.scale)
    except Exception as e:  # noqa: BLE001
        print(f'edgy-render: cannot render {args.file}: {e}', file=sys.stderr)
        return 2
    for r in results:
        label = f" [page {r['page']}]" if r['page'] else ''
        print(f"svg: {r['svg']}{label}")
        if r['png']:
            print(f"png: {r['png']}")
    if not args.no_png and not any(r['png'] for r in results):
        print('note: no Chromium/Chrome found — SVG only (set EDGY_CHROMIUM=<binary> or use the draw.io CLI for PNG)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
