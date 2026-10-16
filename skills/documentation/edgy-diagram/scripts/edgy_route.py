#!/usr/bin/env python3
"""
edgy_route.py — orthogonal edge routing around the cards of a page (edgy-diagram 2.8.0).

A dense map (the application map: 15–40 cards in a domains × layers matrix)
cannot be connected with the default elbow routes — they cut through the
cards in between (lint W111). This router finds an orthogonal path through
the free channels between the cards: a sparse grid of candidate lines just
outside every card edge (a classic connector router), searched with A* for the
shortest path with the fewest bends, preferring channels that no earlier edge
uses. The result is the exit side, the entry side and the bend points, which
the generator writes as `exitX/entryX` ports and `<Array as="points">`
waypoints — so draw.io, the native renderer and the linter all follow the
same path.

Standard library only. Deterministic: the same page always routes the same way.
"""

import heapq
from typing import Dict, List, Optional, Sequence, Tuple

Box = Tuple[float, float, float, float]
Point = Tuple[float, float]
MARGIN = 10.0            # channel line distance from a card edge (matrix gaps are 20 px: the line runs in the middle)
BEND = 60.0              # cost of a bend, in px of length
REUSE = 2000.0           # running along a segment an earlier edge already uses: two edges on one line read as one (a false link), so only when nothing else exists
SIDES = ('right', 'left', 'bottom', 'top')


def _port(box: Box, side: str, frac: float = 0.5) -> Point:
    x, y, w, h = box
    return {'right': (x + w, y + h * frac), 'left': (x, y + h * frac),
            'bottom': (x + w * frac, y + h), 'top': (x + w * frac, y)}[side]


def _stub(box: Box, side: str, m: float = MARGIN, frac: float = 0.5) -> Point:
    px, py = _port(box, side, frac)
    dx, dy = {'right': (m, 0), 'left': (-m, 0), 'bottom': (0, m), 'top': (0, -m)}[side]
    return (px + dx, py + dy)


def _blocked(a: Point, b: Point, obstacles: Sequence[Box]) -> bool:
    """Does segment a–b (axis-parallel) enter the interior of an obstacle?"""
    (x1, y1), (x2, y2) = a, b
    lo_x, hi_x = min(x1, x2), max(x1, x2)
    lo_y, hi_y = min(y1, y2), max(y1, y2)
    for ox, oy, ow, oh in obstacles:
        if lo_x < ox + ow and hi_x > ox and lo_y < oy + oh and hi_y > oy:
            return True
    return False


def route(source: Box, target: Box, obstacles: Sequence[Box], used: Optional[List[Tuple[Point, Point]]] = None,
          margin: float = MARGIN, label_size: Optional[Tuple[float, float]] = None,
          labels: Optional[List[Box]] = None, exit_port: Optional[Tuple[str, float]] = None,
          entry_port: Optional[Tuple[str, float]] = None) -> Optional[Tuple[str, str, List[Point], float]]:
    """(exit side, entry side, waypoints, label fraction) of an orthogonal path from `source` to `target`
    that keeps `margin` px from every obstacle, or None when no such path exists. `obstacles` may contain
    the two end boxes; `used` (segments of earlier edges) is extended with this path's segments.
    `exit_port` / `entry_port` = (side, fraction along it) pin the ends to the ports the generator will
    use when several edges share a side (second pass), so the stubs need no jog. The label
    fraction (0–1 along the path) puts a label of `label_size` on the longest segment where it covers no
    card and no earlier label (`labels`, extended with the chosen box)."""
    inflate = margin - 1.0
    others = [b for b in obstacles if b != source and b != target]
    obst = [(x - inflate, y - inflate, w + 2 * inflate, h + 2 * inflate) for x, y, w, h in others]
    ends = [(x - inflate, y - inflate, w + 2 * inflate, h + 2 * inflate) for x, y, w, h in (source, target)]
    xs, ys = set(), set()
    for x, y, w, h in list(others) + [source, target]:
        xs.update((x - margin, x + w + margin))
        ys.update((y - margin, y + h + margin))
    src_sides = [exit_port] if exit_port else [(s, 0.5) for s in SIDES]
    tgt_sides = [entry_port] if entry_port else [(s, 0.5) for s in SIDES]
    for box, sides in ((source, src_sides), (target, tgt_sides)):
        for s, f in sides:
            sx, sy = _stub(box, s, margin, f)
            xs.add(sx)
            ys.add(sy)
            px, py = _port(box, s, f)
            xs.add(px)
            ys.add(py)
    xs, ys = sorted(xs), sorted(ys)
    xi = {x: i for i, x in enumerate(xs)}
    yi = {y: i for i, y in enumerate(ys)}
    used = used if used is not None else []

    def inside_any(p: Point) -> bool:
        px, py = p
        return any(ox < px < ox + ow and oy < py < oy + oh for ox, oy, ow, oh in obst + ends)

    def reuse_cost(a: Point, b: Point) -> float:
        for (u1, u2) in used:
            if a[0] == b[0] == u1[0] == u2[0] and min(a[1], b[1]) < max(u1[1], u2[1]) and max(a[1], b[1]) > min(u1[1], u2[1]):
                return REUSE
            if a[1] == b[1] == u1[1] == u2[1] and min(a[0], b[0]) < max(u1[0], u2[0]) and max(a[0], b[0]) > min(u1[0], u2[0]):
                return REUSE
        return 0.0

    tcx, tcy = target[0] + target[2] / 2, target[1] + target[3] / 2
    goals = {_stub(target, s, margin, f): (s, f) for s, f in tgt_sides}
    heap = []
    best: Dict[Tuple[Point, str], float] = {}
    prev: Dict[Tuple[Point, str], Tuple[Optional[Tuple[Point, str]], Optional[str]]] = {}
    scx, scy = source[0] + source[2] / 2, source[1] + source[3] / 2
    for s, sf in src_sides:
        st = _stub(source, s, margin, sf)
        if inside_any(st) or _blocked(_port(source, s, sf), st, obst):
            continue
        facing = {'right': tcx > scx, 'left': tcx < scx, 'bottom': tcy > scy, 'top': tcy < scy}[s]
        cost = margin + (0 if facing else 40)
        d = 'h' if s in ('left', 'right') else 'v'
        key = (st, d)
        best[key] = cost
        prev[key] = (None, (s, sf))
        heapq.heappush(heap, (cost + abs(st[0] - tcx) + abs(st[1] - tcy), cost, st, d))
    end_key = None
    while heap:
        _f, cost, p, d = heapq.heappop(heap)
        if best.get((p, d), float('inf')) < cost:
            continue
        if p in goals:
            gs, gf = goals[p]
            need = 'h' if gs in ('left', 'right') else 'v'
            if not _blocked(p, _port(target, gs, gf), obst):
                end_key = (p, d, (gs, gf), cost + (BEND if d != need else 0))
                break
        i, j = xi.get(p[0]), yi.get(p[1])
        if i is None or j is None:
            continue
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                continue
            q = (xs[ni], ys[nj])
            if inside_any(q) or _blocked(p, q, obst):
                continue
            nd = 'h' if di else 'v'
            c = cost + abs(q[0] - p[0]) + abs(q[1] - p[1]) + (BEND if nd != d else 0) + reuse_cost(p, q)
            if c < best.get((q, nd), float('inf')):
                best[(q, nd)] = c
                prev[(q, nd)] = ((p, d), None)
                heapq.heappush(heap, (c + abs(q[0] - tcx) + abs(q[1] - tcy), c, q, nd))
    if end_key is None:
        return None
    p, d, (entry, entry_frac), _c = end_key
    pts = [p]
    key = (p, d)
    exit_side, exit_frac = None, 0.5
    while True:
        back, side = prev[key]
        if back is None:
            exit_side, exit_frac = side
            break
        pts.append(back[0])
        key = back
    pts.reverse()
    path = [_port(source, exit_side, exit_frac)] + pts + [_port(target, entry, entry_frac)]
    # waypoints = both end stubs (so a port the generator shifts along its side still joins inside the
    # channel) and every bend between them
    inner: List[Point] = []
    for k in range(2, len(path) - 2):
        a, b, c = path[k - 1], path[k], path[k + 1]
        if not ((a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1])):
            inner.append(b)
    bends = [path[1]] + inner + ([path[-2]] if len(path) > 3 else [])
    for k in range(len(path) - 1):
        used.append((path[k], path[k + 1]))
    return exit_side, entry, bends, _label_fraction(path, obstacles, label_size, labels)


def _label_fraction(path: List[Point], obstacles: Sequence[Box], size: Optional[Tuple[float, float]],
                    labels: Optional[List[Box]]):
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(path, path[1:])]
    total = sum(lengths) or 1.0
    w, h = size or (60.0, 16.0)
    taken = labels if labels is not None else []
    order = sorted(range(len(lengths)), key=lambda k: (-lengths[k], k))
    def free(box):
        if box[0] < 0 or box[1] < 0:            # page coordinates start at 0: a label there leaves the page (W114)
            return False
        pad = (box[0] - 3, box[1] - 3, box[2] + 6, box[3] + 6)     # 3 px clearance: renderers differ slightly
        return not any(_overlap(pad, o) > 0.05 * w * h for o in list(obstacles) + taken)

    # the longest segment first, at any free position along it, before a shorter one: a label in the middle of
    # a long channel reads better than one squeezed beside a card at the end of a short stub. The preferred
    # positions come first, then every 5 % — the free gap between two rows of cards is often narrow
    ts = (0.5, 0.3, 0.7, 0.15, 0.85) + tuple(k / 20 for k in range(1, 20) if k not in (3, 6, 10, 14, 17))
    candidates = []
    for k in order:
        for t in ts:
            (x1, y1), (x2, y2) = path[k], path[k + 1]
            mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            box = (mx - w / 2, my - h / 2, w, h)
            frac = (sum(lengths[:k]) + lengths[k] * t) / total
            if free(box):
                taken.append(box)
                return frac
            candidates.append((box, frac))
    # no free spot on the path (a short edge between neighbours, a channel at the page edge): the label moves
    # beside the path — across the segment first, at every sampled position of the three longest segments
    for k in order[:3]:
        (x1, y1), (x2, y2) = path[k], path[k + 1]
        across = ((1, 0), (-1, 0)) if x1 == x2 else ((0, 1), (0, -1))
        along = ((0, 1), (0, -1)) if x1 == x2 else ((1, 0), (-1, 0))
        for d in range(10, 100, 10):      # further away a label reads as another edge's: least overlap instead
            for t in ts:
                mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                frac = (sum(lengths[:k]) + lengths[k] * t) / total
                for ux, uy in across + (along if d >= 20 else ()):
                    dx, dy = ux * d, uy * d
                    box = (mx + dx - w / 2, my + dy - h / 2, w, h)
                    if free(box):
                        taken.append(box)
                        return frac, (float(dx), float(dy))
    # nothing is free: the on-page position on the path that covers the least
    def cost(box):
        off = 1e9 if box[0] < 0 or box[1] < 0 else 0.0
        return off + sum(_overlap(box, o) for o in list(obstacles) + taken)
    box, frac = min(candidates, key=lambda c: cost(c[0]))
    taken.append(box)
    return frac


def _overlap(a: Box, b: Box) -> float:
    ox = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    oy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return ox * oy
