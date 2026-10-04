#!/usr/bin/env python3
"""
edgy_geometry.py — one resolved geometry for EDGY draw.io diagrams.

Generation (edgy_parser), preview (edgy_render) and validation (edgy_lint)
need the same answers: where a cell sits in absolute page coordinates, where
an edge leaves and enters its boxes, which polyline it follows and where its
label lands. Keeping those answers in one module means the picture the
renderer draws is the picture the linter checks — and the geometry the
generator assumed when it computed waypoints.

Conventions (draw.io):
  * a box is (x, y, w, h) in absolute page pixels, parent chain resolved;
  * exitX/exitY and entryX/entryY in an edge style are fractions of the
    source / target box; 0 or 1 on one axis names the side;
  * <Array as="points"> are absolute waypoints between the ports;
  * an edge label's <mxGeometry relative="1" x="…" y="…"> gives the position
    along the path (x ∈ [-1, 1] → 0 … 100 % of the length) and the
    perpendicular offset in px; an <mxPoint as="offset"> child adds an
    absolute pixel offset.

Standard library only.
"""

import math
import re
from typing import Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Box = Tuple[float, float, float, float]

SIDES = ('left', 'right', 'top', 'bottom')
OUTWARD = 20.0        # px an orthogonal route steps away from a box before it may turn back
CHAR_W = 0.55         # average glyph width / font size — replaced by edgy_text when present
LABEL_H = 1.3         # label box height / font size
LABEL_PAD = 8.0       # horizontal padding of the white label backing


# ─── cells ───────────────────────────────────────────────────────────────────

def style_dict(style: Optional[str]) -> Dict[str, str]:
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


def geometry_of(cell) -> Optional[List[float]]:
    g = cell.find('mxGeometry')
    if g is None:
        return None
    return [float(g.get(k, 0) or 0) for k in ('x', 'y', 'width', 'height')]


def abs_box(cells: Dict[str, object], cid: Optional[str], cache: Optional[Dict[str, Optional[Box]]] = None) -> Optional[Box]:
    """Absolute (x, y, w, h) of vertex `cid`, parent chain resolved. None for
    edges, unknown ids and cells without geometry."""
    if cid is None:
        return None
    if cache is not None and cid in cache:
        return cache[cid]
    c = cells.get(cid)
    box = None
    if c is not None and c.get('vertex') == '1':
        g = geometry_of(c)
        if g is not None:
            x, y, w, h = g
            p = cells.get(c.get('parent'))
            guard = 0
            while p is not None and p.get('vertex') == '1' and guard < 50:
                pg = geometry_of(p)
                if pg:
                    x += pg[0]
                    y += pg[1]
                p = cells.get(p.get('parent'))
                guard += 1
            box = (x, y, w, h)
    if cache is not None:
        cache[cid] = box
    return box


# ─── boxes, sides, ports ────────────────────────────────────────────────────

def centre(box: Box) -> Point:
    x, y, w, h = box
    return (x + w / 2, y + h / 2)


def side_point(box: Box, side: str, frac: float = 0.5) -> Point:
    x, y, w, h = box
    return {
        'left': (x, y + h * frac), 'right': (x + w, y + h * frac),
        'top': (x + w * frac, y), 'bottom': (x + w * frac, y + h),
    }[side]


def opposite(side: str) -> str:
    return {'left': 'right', 'right': 'left', 'top': 'bottom', 'bottom': 'top'}[side]


def choose_side(box: Box, other: Box) -> str:
    """Side of `box` that faces `other`: horizontal wins ties (draw.io-like)."""
    cx, cy = centre(box)
    ox, oy = centre(other)
    dx, dy = ox - cx, oy - cy
    if abs(dx) >= abs(dy):
        return 'right' if dx >= 0 else 'left'
    return 'bottom' if dy >= 0 else 'top'


def distribute(count: int, index: int) -> float:
    """Spread `count` ports evenly over 0.15 … 0.85 of a side."""
    if count <= 1:
        return 0.5
    return 0.15 + (0.7 * index / (count - 1))


def anchor(box: Box, st: Dict[str, str], prefix: str, other: Optional[Box]) -> Tuple[Point, Optional[str]]:
    """Port on `box`: from exitX/exitY (prefix 'exit') or entryX/entryY
    ('entry') when present, else the middle of the side facing `other`.
    Returns (point, side); side is None for a port strictly inside the box."""
    kx, ky = f'{prefix}X', f'{prefix}Y'
    x, y, w, h = box
    if kx in st and ky in st:
        try:
            fx = min(max(float(st[kx]), 0.0), 1.0)
            fy = min(max(float(st[ky]), 0.0), 1.0)
        except ValueError:
            fx = fy = None
        if fx is not None:
            side = 'left' if fx == 0 else 'right' if fx == 1 else 'top' if fy == 0 else 'bottom' if fy == 1 else None
            return (x + w * fx, y + h * fy), side
    if other is None:
        return centre(box), None
    side = choose_side(box, other)
    return side_point(box, side), side


def border_point(box: Box, towards: Point) -> Point:
    """Point on the border of `box` on the ray from its centre to `towards`."""
    cx, cy = centre(box)
    x, y, w, h = box
    dx, dy = towards[0] - cx, towards[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    sx = (w / 2) / abs(dx) if dx else math.inf
    sy = (h / 2) / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return (cx + dx * s, cy + dy * s)


# ─── routes ─────────────────────────────────────────────────────────────────

def dedupe(path: Sequence[Point]) -> List[Point]:
    """Drop repeated points and the middle point of three collinear
    horizontal / vertical points."""
    out: List[Point] = []
    for p in path:
        if out and abs(out[-1][0] - p[0]) < 1e-6 and abs(out[-1][1] - p[1]) < 1e-6:
            continue
        out.append((float(p[0]), float(p[1])))
    changed = True
    while changed and len(out) > 2:
        changed = False
        for i in range(1, len(out) - 1):
            a, b, c = out[i - 1], out[i], out[i + 1]
            # only a point *between* its neighbours is redundant; a spike (out and back) is a real detour
            same_x = abs(a[0] - b[0]) < 1e-6 and abs(b[0] - c[0]) < 1e-6 and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
            same_y = abs(a[1] - b[1]) < 1e-6 and abs(b[1] - c[1]) < 1e-6 and min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
            if same_x or same_y:
                del out[i]
                changed = True
                break
    return out


def _side_towards(point: Point, towards: Point) -> str:
    dx, dy = towards[0] - point[0], towards[1] - point[1]
    if abs(dx) >= abs(dy):
        return 'right' if dx >= 0 else 'left'
    return 'bottom' if dy >= 0 else 'top'


def _join_start(port: Point, side: Optional[str], wp: Point) -> List[Point]:
    """Orthogonal points between a port and its first waypoint. The first
    segment is perpendicular to the side and leaves the box outward; a
    waypoint *behind* the port gets an OUTWARD step first."""
    px, py = port
    wx, wy = wp
    side = side or _side_towards(port, wp)
    if side in ('left', 'right'):
        d = 1 if side == 'right' else -1
        if (wx - px) * d >= 0:
            return [(wx, py)]
        ox = px + d * OUTWARD
        return [(ox, py), (ox, wy)]
    d = 1 if side == 'bottom' else -1
    if (wy - py) * d >= 0:
        return [(px, wy)]
    oy = py + d * OUTWARD
    return [(px, oy), (wx, oy)]


def _join_end(wp: Point, side: Optional[str], port: Point) -> List[Point]:
    """Mirror of _join_start for the last waypoint → entry port."""
    pts = _join_start(port, side, wp)
    return list(reversed(pts))


def orthogonal_route(p1: Point, s1: Optional[str], p2: Point, s2: Optional[str],
                     points: Sequence[Point] = ()) -> List[Point]:
    """Polyline for an orthogonal edge. With waypoints the end segments are
    made orthogonal to their sides (the F1 fix); without, a two- or
    three-segment elbow route."""
    points = [(float(x), float(y)) for x, y in points]
    if points:
        path = [p1] + _join_start(p1, s1, points[0]) + points + _join_end(points[-1], s2, p2) + [p2]
        return dedupe(path)
    (x1, y1), (x2, y2) = p1, p2
    if s1 in ('left', 'right') and s2 in ('left', 'right'):
        mx = (x1 + x2) / 2
        path = [p1, (mx, y1), (mx, y2), p2]
    elif s1 in ('top', 'bottom') and s2 in ('top', 'bottom'):
        my = (y1 + y2) / 2
        path = [p1, (x1, my), (x2, my), p2]
    elif s1 in ('left', 'right'):
        path = [p1, (x2, y1), p2]
    elif s1 in ('top', 'bottom'):
        path = [p1, (x1, y2), p2]
    else:
        path = [p1, p2]
    return dedupe(path)


def straight_route(sb: Box, tb: Box, points: Sequence[Point] = ()) -> List[Point]:
    """Straight line (or polyline through waypoints) from border to border."""
    points = [(float(x), float(y)) for x, y in points]
    first = points[0] if points else centre(tb)
    last = points[-1] if points else centre(sb)
    p1 = border_point(sb, first)
    p2 = border_point(tb, last)
    return dedupe([p1] + points + [p2])


def edge_path(sb: Optional[Box], tb: Optional[Box], st: Dict[str, str], points: Sequence[Point] = (),
              source_point: Optional[Point] = None, target_point: Optional[Point] = None) -> Optional[List[Point]]:
    """The polyline an edge follows, from its style, boxes and waypoints.

    * both boxes known, orthogonal/elbow style → orthogonal_route with ports
    * both boxes known, other style → straight; explicit exit/entry anchors
      are honoured, otherwise border points on the centre line
    * a box missing → sourcePoint / targetPoint (legend samples); None when
      those are missing too
    """
    points = [(float(x), float(y)) for x, y in points]
    if sb is not None and tb is not None:
        ortho = st.get('edgeStyle') in ('orthogonalEdgeStyle', 'elbowEdgeStyle')
        if ortho:
            p1, s1 = anchor(sb, st, 'exit', tb)
            p2, s2 = anchor(tb, st, 'entry', sb)
            return orthogonal_route(p1, s1, p2, s2, points)
        has_exit = 'exitX' in st and 'exitY' in st
        has_entry = 'entryX' in st and 'entryY' in st
        if not has_exit and not has_entry:
            return straight_route(sb, tb, points)
        p1 = anchor(sb, st, 'exit', tb)[0] if has_exit else border_point(sb, points[0] if points else centre(tb))
        p2 = anchor(tb, st, 'entry', sb)[0] if has_entry else border_point(tb, points[-1] if points else centre(sb))
        return dedupe([p1] + points + [p2])
    p1 = source_point if sb is None else None
    p2 = target_point if tb is None else None
    if sb is not None and target_point is not None:
        p1 = border_point(sb, points[0] if points else target_point)
    if tb is not None and source_point is not None:
        p2 = border_point(tb, points[-1] if points else source_point)
    if p1 is None or p2 is None:
        return None
    return dedupe([p1] + points + [p2])


def edge_points(edge_cell) -> Tuple[List[Point], Optional[Point], Optional[Point], Optional[Point], Optional[float], Optional[float]]:
    """Read an edge's <mxGeometry>: (waypoints, sourcePoint, targetPoint,
    offset point, relative x, y)."""
    g = edge_cell.find('mxGeometry')
    if g is None:
        return [], None, None, None, None, None
    pts: List[Point] = []
    arr = g.find("Array[@as='points']")
    if arr is not None:
        for p in arr.findall('mxPoint'):
            pts.append((float(p.get('x', 0) or 0), float(p.get('y', 0) or 0)))

    def pt(name):
        e = g.find(f"mxPoint[@as='{name}']")
        return (float(e.get('x', 0) or 0), float(e.get('y', 0) or 0)) if e is not None else None

    rx = g.get('x')
    ry = g.get('y')
    return (pts, pt('sourcePoint'), pt('targetPoint'), pt('offset'),
            float(rx) if rx not in (None, '') else None,
            float(ry) if ry not in (None, '') else None)


# ─── measuring along a path ──────────────────────────────────────────────────

def path_length(path: Sequence[Point]) -> float:
    return sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(len(path) - 1))


def point_at(path: Sequence[Point], dist: float) -> Tuple[Point, Point]:
    """Point at `dist` along the path and the unit direction of its segment."""
    if len(path) == 1:
        return path[0], (1.0, 0.0)
    acc = 0.0
    for i in range(len(path) - 1):
        (ax, ay), (bx, by) = path[i], path[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        if seg == 0:
            continue
        if acc + seg >= dist:
            t = (dist - acc) / seg
            return (ax + (bx - ax) * t, ay + (by - ay) * t), ((bx - ax) / seg, (by - ay) / seg)
        acc += seg
    (ax, ay), (bx, by) = path[-2], path[-1]
    seg = math.hypot(bx - ax, by - ay) or 1.0
    return path[-1], ((bx - ax) / seg, (by - ay) / seg)


def label_fraction(relative_x: Optional[float]) -> float:
    """draw.io relative x ∈ [-1, 1] → fraction of the path length."""
    if relative_x is None:
        return 0.5
    return min(max((relative_x + 1.0) / 2.0, 0.0), 1.0)


def label_anchor(path: Sequence[Point], fraction: float = 0.5, perpendicular: float = 0.0,
                 offset: Point = (0.0, 0.0)) -> Point:
    """Label centre: `fraction` along the path, shifted `perpendicular` px to
    the left of the travel direction, plus an absolute `offset`."""
    if not path:
        return (0.0, 0.0)
    total = path_length(path)
    (px, py), (dx, dy) = point_at(path, total * fraction)
    nx, ny = -dy, dx
    return (px + nx * perpendicular + offset[0], py + ny * perpendicular + offset[1])


def approx_text_width(text: str, fs: float, bold: bool = False) -> float:
    """Width estimate of a single text line. edgy_text replaces this with
    glyph tables when available."""
    try:
        from edgy_text import measure  # noqa: WPS433 — optional, Sprint 10
        return measure(text, fs, bold)
    except Exception:  # pragma: no cover — fallback stays stdlib
        return len(text) * fs * CHAR_W * (1.08 if bold else 1.0)


def edge_label_box(path: Sequence[Point], text: str, fs: float, relative_x: Optional[float] = None,
                   relative_y: Optional[float] = None, offset: Optional[Point] = None,
                   bold: bool = False) -> Optional[Box]:
    """Box of an edge label as the renderer draws it: centred on the label
    anchor, raised fs × 0.6 above the path when no perpendicular offset is
    given so short edges stay visible."""
    if not text or len(path) < 2:
        return None
    perpendicular = relative_y if relative_y is not None else 0.0
    ax, ay = label_anchor(path, label_fraction(relative_x), perpendicular, offset or (0.0, 0.0))
    if relative_y is None and not offset:
        ay -= fs * 0.6
    w = approx_text_width(text, fs, bold) + LABEL_PAD
    h = fs * LABEL_H
    return (ax - w / 2, ay - h / 2, w, h)


# ─── collisions ──────────────────────────────────────────────────────────────

def clip_length(p: Point, q: Point, box: Box) -> float:
    """Length of the part of segment p→q that lies inside `box` (Liang–Barsky)."""
    x0, y0 = p
    x1, y1 = q
    bx, by, bw, bh = box
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for num, den in ((x0 - bx, -dx), (bx + bw - x0, dx), (y0 - by, -dy), (by + bh - y0, dy)):
        if den == 0:
            if num < 0:
                return 0.0
            continue
        t = num / den
        if den < 0:
            if t > t1:
                return 0.0
            t0 = max(t0, t)
        else:
            if t < t0:
                return 0.0
            t1 = min(t1, t)
    if t0 >= t1:
        return 0.0
    return math.hypot(dx, dy) * (t1 - t0)


def path_through_box(path: Sequence[Point], box: Box) -> float:
    """Total length of `path` inside `box`."""
    return sum(clip_length(path[i], path[i + 1], box) for i in range(len(path) - 1))


def rect_intersection(a: Box, b: Box) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ox = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    oy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return ox * oy


def bbox_of(boxes: Sequence[Box], points: Sequence[Point] = ()) -> Optional[Box]:
    """Bounding box of boxes and points."""
    xs: List[float] = []
    ys: List[float] = []
    for x, y, w, h in boxes:
        xs += [x, x + w]
        ys += [y, y + h]
    for x, y in points:
        xs.append(x)
        ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def outside_page(box: Box, page_w: float, page_h: float, tolerance: float = 0.0) -> bool:
    if not page_w or not page_h:
        return False
    x, y, w, h = box
    return x < -tolerance or y < -tolerance or x + w > page_w + tolerance or y + h > page_h + tolerance


def strip_html(value: Optional[str]) -> str:
    """Plain text of a draw.io html label (first line and the rest joined by newlines)."""
    import html as _html
    text = re.sub(r'<br\s*/?>', '\n', value or '', flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return _html.unescape(text)
