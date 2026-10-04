#!/usr/bin/env python3
"""Tests for edgy_geometry.py — the geometry shared by parser, renderer and lint."""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgy_geometry as geo  # noqa: E402

A = (100.0, 100.0, 120.0, 60.0)      # centre (160, 130)
B = (400.0, 100.0, 120.0, 60.0)      # right of A, centre (460, 130)
C = (100.0, 400.0, 120.0, 60.0)      # below A, centre (160, 430)


def _horizontal_or_vertical(path):
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        assert abs(ax - bx) < 1e-6 or abs(ay - by) < 1e-6, f'diagonal segment {(ax, ay)} → {(bx, by)} in {path}'


def test_abs_box_resolves_parent_chain():
    xml = ('<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="g" vertex="1" parent="1"><mxGeometry x="100" y="50" width="400" height="300"/></mxCell>'
           '<mxCell id="h" vertex="1" parent="g"><mxGeometry x="20" y="30" width="200" height="200"/></mxCell>'
           '<mxCell id="e" vertex="1" parent="h"><mxGeometry x="5" y="6" width="50" height="40"/></mxCell>'
           '<mxCell id="x" edge="1" parent="1"><mxGeometry relative="1"/></mxCell></root>')
    cells = {c.get('id'): c for c in ET.fromstring(xml).findall('mxCell')}
    cache = {}
    assert geo.abs_box(cells, 'e', cache) == (125.0, 86.0, 50.0, 40.0)
    assert geo.abs_box(cells, 'x', cache) is None       # edges have no box
    assert geo.abs_box(cells, 'nope', cache) is None
    assert cache['e'] == (125.0, 86.0, 50.0, 40.0)      # cached


def test_choose_side_horizontal_wins_ties_and_opposite():
    assert geo.choose_side(A, B) == 'right'
    assert geo.choose_side(B, A) == 'left'
    assert geo.choose_side(A, C) == 'bottom'
    assert geo.choose_side(C, A) == 'top'
    diag = (400.0, 400.0, 120.0, 60.0)                  # exactly 45°: horizontal wins
    assert geo.choose_side(A, diag) == 'right'
    for s in geo.SIDES:
        assert geo.opposite(geo.opposite(s)) == s


def test_anchor_from_style_and_by_direction():
    st = {'exitX': '1', 'exitY': '0.25'}
    (x, y), side = geo.anchor(A, st, 'exit', B)
    assert (x, y, side) == (220.0, 115.0, 'right')
    (x, y), side = geo.anchor(A, {}, 'exit', C)       # no style → middle of the facing side
    assert (x, y, side) == (160.0, 160.0, 'bottom')
    _, side = geo.anchor(A, {'entryX': '0.5', 'entryY': '0.5'}, 'entry', B)
    assert side is None                                 # inside the box: no side


def test_distribute_spreads_ports():
    assert geo.distribute(1, 0) == 0.5
    assert geo.distribute(3, 0) == 0.15
    assert abs(geo.distribute(3, 1) - 0.5) < 1e-9
    assert geo.distribute(3, 2) == 0.85


def test_border_point_hits_the_border():
    x, y = geo.border_point(A, (460.0, 130.0))          # due east → right edge, centre height
    assert (x, y) == (220.0, 130.0)
    x, y = geo.border_point(A, (160.0, 1000.0))         # due south → bottom edge
    assert (x, y) == (160.0, 160.0)
    x, y = geo.border_point(A, (1000.0, 1000.0))        # diagonal → on the border, not outside
    assert abs(x - 220.0) < 1e-6 or abs(y - 160.0) < 1e-6
    assert 100.0 <= x <= 220.0 and 100.0 <= y <= 160.0
    assert geo.border_point(A, geo.centre(A)) == geo.centre(A)   # zero-length ray


def test_dedupe_removes_duplicates_and_collinear_points():
    path = [(0, 0), (0, 0), (10, 0), (20, 0), (20, 5), (20, 10), (30, 10)]
    assert geo.dedupe(path) == [(0.0, 0.0), (20.0, 0.0), (20.0, 10.0), (30.0, 10.0)]
    assert geo.dedupe([(1, 1), (1, 1)]) == [(1.0, 1.0)]
    # an out-and-back spike is a real detour, not a collinear redundancy
    spike = [(0, 0), (0, 100), (0, 0), (50, 0)]
    assert geo.dedupe(spike) == [(0.0, 0.0), (0.0, 100.0), (0.0, 0.0), (50.0, 0.0)]


def test_orthogonal_route_without_waypoints():
    _horizontal_or_vertical(geo.orthogonal_route((220, 130), 'right', (400, 130), 'left'))
    p = geo.orthogonal_route((220, 115), 'right', (400, 145), 'left')
    assert p[0] == (220.0, 115.0) and p[-1] == (400.0, 145.0) and len(p) == 4
    _horizontal_or_vertical(p)
    p = geo.orthogonal_route((160, 160), 'bottom', (400, 430), 'left')      # mixed sides → one elbow
    assert p == [(160.0, 160.0), (160.0, 430.0), (400.0, 430.0)]


def test_orthogonal_route_with_waypoints_has_no_diagonal_end_segments():
    """F1: the port was spread to 0.15 of the side, the waypoints assume the centre."""
    port = (220.0, 109.0)                                 # right side of A at 0.15
    target = (400.0, 130.0)
    path = geo.orthogonal_route(port, 'right', target, 'left', [(300.0, 130.0), (300.0, 130.0)])
    _horizontal_or_vertical(path)
    assert path[0] == port and path[-1] == target
    # first segment leaves horizontally (perpendicular to the right side)
    assert path[1][1] == port[1]


def test_orthogonal_route_waypoint_behind_the_port_steps_outward_first():
    port = (220.0, 130.0)                                 # right side of A
    path = geo.orthogonal_route(port, 'right', (160.0, 400.0), 'top', [(60.0, 300.0)])
    _horizontal_or_vertical(path)
    assert path[1] == (220.0 + geo.OUTWARD, 130.0)       # out to the right before turning back
    assert all(not (100 < x < 220 and 100 < y < 160) for x, y in path[1:-1])   # never re-enters A


def test_orthogonal_route_all_four_sides():
    for side, port in (('left', (100.0, 130.0)), ('right', (220.0, 130.0)),
                       ('top', (160.0, 100.0)), ('bottom', (160.0, 160.0))):
        for wp in ((300.0, 300.0), (50.0, 50.0), (160.0, 300.0), (300.0, 130.0)):
            path = geo.orthogonal_route(port, side, (700.0, 700.0), 'left', [wp])
            _horizontal_or_vertical(path)
            # first segment is perpendicular to the side
            (x0, y0), (x1, y1) = path[0], path[1]
            if side in ('left', 'right'):
                assert abs(y1 - y0) < 1e-6
            else:
                assert abs(x1 - x0) < 1e-6


def test_straight_route_and_edge_path_dispatch():
    s = geo.straight_route(A, B)
    assert s == [(220.0, 130.0), (400.0, 130.0)]
    assert geo.edge_path(A, B, {'edgeStyle': 'none'}) == s
    o = geo.edge_path(A, B, {'edgeStyle': 'orthogonalEdgeStyle', 'exitX': '1', 'exitY': '0.15', 'entryX': '0', 'entryY': '0.5'})
    _horizontal_or_vertical(o)
    assert o[0] == (220.0, 109.0) and o[-1] == (400.0, 130.0)
    legend = geo.edge_path(None, None, {}, [], (10.0, 10.0), (40.0, 10.0))
    assert legend == [(10.0, 10.0), (40.0, 10.0)]
    assert geo.edge_path(None, None, {}, [], None, None) is None


def test_path_length_and_point_at():
    path = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0)]
    assert geo.path_length(path) == 150.0
    (x, y), (dx, dy) = geo.point_at(path, 75.0)
    assert (x, y) == (75.0, 0.0) and (dx, dy) == (1.0, 0.0)
    (x, y), (dx, dy) = geo.point_at(path, 125.0)
    assert (x, y) == (100.0, 25.0) and (dx, dy) == (0.0, 1.0)
    assert geo.point_at(path, 999.0)[0] == (100.0, 50.0)      # clamps to the end
    assert geo.point_at([(5.0, 5.0)], 3.0)[0] == (5.0, 5.0)    # zero-length route


def test_label_fraction_and_anchor():
    assert geo.label_fraction(None) == 0.5
    assert geo.label_fraction(-0.5) == 0.25
    assert geo.label_fraction(0.0) == 0.5
    assert geo.label_fraction(0.5) == 0.75
    assert geo.label_fraction(-3.0) == 0.0 and geo.label_fraction(3.0) == 1.0
    path = [(0.0, 0.0), (200.0, 0.0)]
    xs = [geo.label_anchor(path, geo.label_fraction(v))[0] for v in (-0.5, 0.0, 0.5)]
    assert xs == [50.0, 100.0, 150.0]                     # F2: three distinct positions
    x, y = geo.label_anchor(path, 0.5, perpendicular=10.0, offset=(3.0, 4.0))
    assert (x, y) == (103.0, 14.0)


def test_edge_label_box_is_centred_and_raised_by_default():
    path = [(0.0, 100.0), (200.0, 100.0)]
    box = geo.edge_label_box(path, 'requires', 11.0)
    assert box is not None
    x, y, w, h = box
    assert abs((x + w / 2) - 100.0) < 1e-6                # centred on the midpoint
    assert y + h / 2 < 100.0                              # raised above the path
    assert abs(w - (geo.approx_text_width('requires', 11.0) + geo.LABEL_PAD)) < 1e-6   # measured text + padding
    assert geo.edge_label_box(path, '', 11.0) is None
    assert geo.edge_label_box([(0.0, 0.0)], 'x', 11.0) is None
    with_y = geo.edge_label_box(path, 'requires', 11.0, relative_y=0.0)
    assert abs((with_y[1] + with_y[3] / 2) - 100.0) < 1e-6   # explicit y = 0 → on the path


def test_clip_length_liang_barsky():
    box = (100.0, 100.0, 100.0, 100.0)
    assert geo.clip_length((0.0, 150.0), (300.0, 150.0), box) == 100.0        # straight through
    assert geo.clip_length((0.0, 50.0), (300.0, 50.0), box) == 0.0            # misses
    assert geo.clip_length((150.0, 150.0), (150.0, 400.0), box) == 50.0       # starts inside
    assert abs(geo.clip_length((0.0, 0.0), (300.0, 300.0), box) - 100.0 * 2 ** 0.5) < 1e-6
    assert geo.clip_length((0.0, 100.0), (300.0, 100.0), box) == 100.0        # along the top edge counts as inside
    assert geo.path_through_box([(0.0, 150.0), (150.0, 150.0), (150.0, 400.0)], box) == 100.0


def test_rect_intersection_bbox_outside_page():
    assert geo.rect_intersection((0, 0, 10, 10), (5, 5, 10, 10)) == 25.0
    assert geo.rect_intersection((0, 0, 10, 10), (20, 20, 10, 10)) == 0.0
    assert geo.bbox_of([(0, 0, 10, 10), (20, 20, 10, 10)], [(50, 5)]) == (0.0, 0.0, 50.0, 30.0)
    assert geo.bbox_of([]) is None
    assert geo.outside_page((790.0, 10.0, 20.0, 10.0), 800.0, 600.0)
    assert not geo.outside_page((790.0, 10.0, 20.0, 10.0), 800.0, 600.0, tolerance=10.0)
    assert not geo.outside_page((-5.0, 0.0, 10.0, 10.0), 0.0, 0.0)            # no page size → never


def test_edge_points_reads_geometry():
    xml = ('<mxCell id="e" edge="1"><mxGeometry relative="1" x="-0.5" y="12" as="geometry">'
           '<Array as="points"><mxPoint x="10" y="20"/><mxPoint x="30" y="40"/></Array>'
           '<mxPoint x="3" y="4" as="offset"/></mxGeometry></mxCell>')
    pts, sp, tp, off, rx, ry = geo.edge_points(ET.fromstring(xml))
    assert pts == [(10.0, 20.0), (30.0, 40.0)] and sp is None and tp is None
    assert off == (3.0, 4.0) and rx == -0.5 and ry == 12.0
    assert geo.edge_points(ET.fromstring('<mxCell id="e" edge="1"/>')) == ([], None, None, None, None, None)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f'✓ {t.__name__}')
        except AssertionError as e:
            failed += 1
            print(f'✗ {t.__name__}: {e}')
    print(f'{len(tests) - failed}/{len(tests)} passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
