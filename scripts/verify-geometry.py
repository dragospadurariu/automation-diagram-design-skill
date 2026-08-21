#!/usr/bin/env python3
"""Verify diagram geometry: label masks, connector routing, arrowhead landings.

SKILL.md §5 fixes the paint order as background -> zones -> arrows -> labels ->
nodes, and §6 sets the mandatory connector rules. This script enforces the
mechanical subset of both:

1. **Mask clipped by a later node** (§6 rule 6). A label mask that lands partly
   inside a node painted later is covered by the node fill; the text renders as
   a fragment sitting on the node border. A mask over a zone painted earlier is
   fine - zone eyebrows rely on this.
2. **Connectors running on top of each other** (§6 rule 3). Two axis-aligned
   segments from different connectors closer than 12px with overlapping span
   are not independently traceable.
3. **Stroke buried under a node** (§5 paint order). A connector segment passing
   through the interior of a node painted later disappears under the node fill.
4. **Mask too close to a stroke** (§6 rule 2). A label mask must keep a >=6px
   gap from every connector stroke - its own and everyone else's. Badge chips
   fully inside a node are exempt (strokes never enter a node - see check 3).
5. **Floating arrowhead** (§6 rule 4). A `marker-end` endpoint must land on the
   border of a shape (rect or circle) or on another connector's segment (a
   sequence lifeline), not hang in open canvas.

Shape heuristics follow the shipped templates:

* A node is a `<rect>` at least 60x40 - large enough for a title and sublabel.
* A label mask is a `<rect>` 20-200 wide and 8-14 tall - the masking plate that
  SKILL.md prescribes for arrow labels and zone eyebrows. The width cap covers
  the long mono plates shipped in example-sequence-oauth.html (128px) and the
  wider plates CJK labels need at the same glyph count.
* A mask fully contained in a node is a badge chip (`EXT`, `EDGE`, `ORIG`) and
  is legal.
* Connectors are `<path fill="none">` and `<line>` elements outside `<defs>`.
  Curve chords (Q/C/A elbow arcs) are tracked for continuity but skipped by the
  parallel check - only straight runs can shadow each other.
* Everything at or below the legend strip (the `legend-label` LEGEND text,
  including its separator rule 24px above) is exempt - legend swatches are
  display samples, not diagram geometry.

Usage:
    python3 scripts/verify-geometry.py --all
    python3 scripts/verify-geometry.py skills/automation-design/assets/example-x.html
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = ROOT / "skills/automation-design/assets"

RECT_RE = re.compile(
    r"<rect\b[^>]*?"
    r'\bx="(?P<x>-?[\d.]+)"\s+'
    r'y="(?P<y>-?[\d.]+)"\s+'
    r'width="(?P<w>[\d.]+)"\s+'
    r'height="(?P<h>[\d.]+)"',
    re.IGNORECASE,
)

NODE_MIN_W = 60.0
NODE_MIN_H = 40.0
MASK_MIN_W = 20.0
MASK_MAX_W = 200.0
MASK_MIN_H = 8.0
MASK_MAX_H = 14.0
EPSILON = 0.5

# Connector rules (SKILL.md §6)
PARALLEL_MIN_GAP = 12.0   # rule 3: offset parallel runs by >=12px
PARALLEL_MIN_SPAN = 6.0   # shared span shorter than this is elbow adjacency
MIN_SEG_LEN = 8.0         # ignore sub-elbow stubs in the parallel check
INTERIOR_INSET = 2.0      # border landings are legal; interiors are not
INTERIOR_MIN_CLIP = 4.0   # px of stroke buried under a node before reporting
MASK_CLEARANCE = 6.0      # rule 2: mask edge to stroke, minimum visible gap
LANDING_TOL = 2.0         # arrowhead must be within this of a shape border
LANDING_MIN_SIDE = 16.0   # smallest rect an arrow may land on (the gate box)
LEGEND_MARGIN = 24.0      # legend strip starts this far above the LEGEND text
TOL = 0.005               # float comparison slack

PATH_TAG_RE = re.compile(r"<path\b[^>]*>", re.IGNORECASE)
LINE_TAG_RE = re.compile(r"<line\b[^>]*>", re.IGNORECASE)
CIRCLE_TAG_RE = re.compile(r"<circle\b[^>]*>", re.IGNORECASE)
POLYGON_TAG_RE = re.compile(r"<polygon\b[^>]*>", re.IGNORECASE)
DEFS_RE = re.compile(r"<defs\b.*?</defs>", re.IGNORECASE | re.DOTALL)
# Decorative groups (animated tokens, mini-legend footers) are presentation,
# not routed diagram geometry. Non-greedy: a nested <g> inside one of these
# under-exempts, which only makes the check stricter.
DECOR_RE = re.compile(r'<g\b[^>]*aria-hidden="true"[^>]*>.*?</g>', re.IGNORECASE | re.DOTALL)
LEGEND_TEXT_RE = re.compile(
    r'<text\b[^>]*(?:class="[^"]*legend-label[^"]*"[^>]*>|>\s*LEGEND\b[^<]*</text>)',
    re.IGNORECASE,
)
ATTR_RES = {
    name: re.compile(rf'\b{name}="([^"]*)"', re.IGNORECASE)
    for name in (
        "d", "fill", "stroke", "marker-end",
        "x1", "y1", "x2", "y2", "cx", "cy", "r", "y", "points",
    )
}
D_TOKEN_RE = re.compile(r"[MmLlHhVvQqTtCcSsAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

# path-data parameter count per command (endpoint is always the last pair)
PARAM_COUNT = {"M": 2, "L": 2, "H": 1, "V": 1, "Q": 4, "T": 2, "C": 6, "S": 4, "A": 7, "Z": 0}


def attr(tag: str, name: str) -> str | None:
    match = ATTR_RES[name].search(tag)
    return match.group(1) if match else None


class Segment:
    __slots__ = ("x1", "y1", "x2", "y2", "curve")

    def __init__(self, x1, y1, x2, y2, curve=False) -> None:
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.curve = curve

    @property
    def horizontal(self) -> bool:
        return not self.curve and abs(self.y1 - self.y2) < TOL

    @property
    def vertical(self) -> bool:
        return not self.curve and abs(self.x1 - self.x2) < TOL

    @property
    def length(self) -> float:
        return ((self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"({self.x1:g},{self.y1:g})->({self.x2:g},{self.y2:g})"


class Connector:
    __slots__ = ("segments", "marker_end", "is_line", "line", "offset")

    def __init__(self, segments, marker_end, is_line, line, offset) -> None:
        self.segments, self.marker_end, self.is_line = segments, marker_end, is_line
        self.line, self.offset = line, offset

    @property
    def end(self) -> tuple[float, float] | None:
        if not self.segments:
            return None
        last = self.segments[-1]
        return (last.x2, last.y2)


class Circle:
    __slots__ = ("cx", "cy", "r")

    def __init__(self, cx, cy, r) -> None:
        self.cx, self.cy, self.r = cx, cy, r


def parse_path_segments(d: str) -> list[Segment]:
    segments: list[Segment] = []
    tokens = D_TOKEN_RE.findall(d)
    pos = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    command = None
    while pos < len(tokens):
        token = tokens[pos]
        if token.isalpha():
            command = token
            pos += 1
            if command.upper() == "Z":
                if cur != start:
                    segments.append(Segment(*cur, *start))
                cur = start
                continue
        if command is None:
            return []
        upper = command.upper()
        count = PARAM_COUNT.get(upper)
        if count is None or pos + count > len(tokens):
            break
        params = [float(t) for t in tokens[pos : pos + count]]
        pos += count
        relative = command.islower()
        base_x, base_y = (cur if relative else (0.0, 0.0))
        if upper == "H":
            nxt = (params[0] + base_x, cur[1])
        elif upper == "V":
            nxt = (cur[0], params[0] + base_y)
        else:
            nxt = (params[-2] + base_x, params[-1] + base_y)
        if upper == "M":
            cur = start = nxt
            command = "l" if relative else "L"  # implicit lineto on repeats
            continue
        segments.append(Segment(*cur, *nxt, curve=upper in "QTCSA"))
        cur = nxt
    return segments


def parse_connectors(source: str, dead_spans: list[tuple[int, int]]) -> list[Connector]:
    connectors: list[Connector] = []

    def dead(offset: int) -> bool:
        return any(a <= offset < b for a, b in dead_spans)

    for match in PATH_TAG_RE.finditer(source):
        tag = match.group(0)
        if dead(match.start()) or (attr(tag, "fill") or "").lower() != "none":
            continue
        d = attr(tag, "d")
        if not d:
            continue
        segments = parse_path_segments(d)
        if segments:
            connectors.append(
                Connector(
                    segments,
                    attr(tag, "marker-end") is not None,
                    False,
                    source.count("\n", 0, match.start()) + 1,
                    match.start(),
                )
            )
    for match in LINE_TAG_RE.finditer(source):
        tag = match.group(0)
        if dead(match.start()):
            continue
        coords = [attr(tag, name) for name in ("x1", "y1", "x2", "y2")]
        if any(value is None for value in coords):
            continue
        x1, y1, x2, y2 = (float(value) for value in coords)
        connectors.append(
            Connector(
                [Segment(x1, y1, x2, y2)],
                attr(tag, "marker-end") is not None,
                True,
                source.count("\n", 0, match.start()) + 1,
                match.start(),
            )
        )
    return connectors


def parse_circles(source: str, dead_spans: list[tuple[int, int]]) -> list[Circle]:
    circles: list[Circle] = []
    for match in CIRCLE_TAG_RE.finditer(source):
        if any(a <= match.start() < b for a, b in dead_spans):
            continue
        tag = match.group(0)
        values = [attr(tag, name) for name in ("cx", "cy", "r")]
        if all(value is not None for value in values):
            circles.append(Circle(*(float(value) for value in values)))
    return circles


def parse_polygons(source: str, dead_spans: list[tuple[int, int]]) -> list[list[Segment]]:
    polygons: list[list[Segment]] = []
    for match in POLYGON_TAG_RE.finditer(source):
        if any(a <= match.start() < b for a, b in dead_spans):
            continue
        raw = attr(match.group(0), "points")
        if not raw:
            continue
        values = [float(v) for v in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", raw)]
        points = list(zip(values[0::2], values[1::2]))
        if len(points) < 3:
            continue
        polygons.append(
            [
                Segment(*points[i], *points[(i + 1) % len(points)])
                for i in range(len(points))
            ]
        )
    return polygons


def legend_cutoff(source: str) -> float | None:
    best: float | None = None
    for match in LEGEND_TEXT_RE.finditer(source):
        y = attr(match.group(0), "y")
        if y is not None:
            best = max(best, float(y)) if best is not None else float(y)
    return best - LEGEND_MARGIN if best is not None else None


def seg_point_distance(seg: Segment, px: float, py: float) -> float:
    dx, dy = seg.x2 - seg.x1, seg.y2 - seg.y1
    if dx == dy == 0:
        return ((px - seg.x1) ** 2 + (py - seg.y1) ** 2) ** 0.5
    t = ((px - seg.x1) * dx + (py - seg.y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = seg.x1 + t * dx, seg.y1 + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def seg_seg_distance(a: Segment, b: Segment) -> float:
    if segments_intersect(a, b):
        return 0.0
    return min(
        seg_point_distance(a, b.x1, b.y1),
        seg_point_distance(a, b.x2, b.y2),
        seg_point_distance(b, a.x1, a.y1),
        seg_point_distance(b, a.x2, a.y2),
    )


def _orient(ax, ay, bx, by, cx, cy) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def segments_intersect(a: Segment, b: Segment) -> bool:
    d1 = _orient(a.x1, a.y1, a.x2, a.y2, b.x1, b.y1)
    d2 = _orient(a.x1, a.y1, a.x2, a.y2, b.x2, b.y2)
    d3 = _orient(b.x1, b.y1, b.x2, b.y2, a.x1, a.y1)
    d4 = _orient(b.x1, b.y1, b.x2, b.y2, a.x2, a.y2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    return False


def seg_rect_distance(seg: Segment, rect: Rect) -> float:
    inside = (
        rect.x <= seg.x1 <= rect.right and rect.y <= seg.y1 <= rect.bottom
    ) or (rect.x <= seg.x2 <= rect.right and rect.y <= seg.y2 <= rect.bottom)
    edges = [
        Segment(rect.x, rect.y, rect.right, rect.y),
        Segment(rect.right, rect.y, rect.right, rect.bottom),
        Segment(rect.right, rect.bottom, rect.x, rect.bottom),
        Segment(rect.x, rect.bottom, rect.x, rect.y),
    ]
    if inside:
        return 0.0
    return min(seg_seg_distance(seg, edge) for edge in edges)


def clip_length(seg: Segment, rect: Rect, inset: float) -> float:
    """Length of `seg` inside `rect` shrunk by `inset` (Liang-Barsky)."""
    x_min, y_min = rect.x + inset, rect.y + inset
    x_max, y_max = rect.right - inset, rect.bottom - inset
    if x_min >= x_max or y_min >= y_max:
        return 0.0
    dx, dy = seg.x2 - seg.x1, seg.y2 - seg.y1
    t0, t1 = 0.0, 1.0
    for p, q in (
        (-dx, seg.x1 - x_min),
        (dx, x_max - seg.x1),
        (-dy, seg.y1 - y_min),
        (dy, y_max - seg.y1),
    ):
        if p == 0:
            if q < 0:
                return 0.0
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return 0.0
    return (t1 - t0) * seg.length


def on_rect_border(px: float, py: float, rect: Rect, tol: float) -> bool:
    near_v = (abs(px - rect.x) <= tol or abs(px - rect.right) <= tol) and (
        rect.y - tol <= py <= rect.bottom + tol
    )
    near_h = (abs(py - rect.y) <= tol or abs(py - rect.bottom) <= tol) and (
        rect.x - tol <= px <= rect.right + tol
    )
    return near_v or near_h


class Rect:
    __slots__ = ("x", "y", "w", "h", "line", "offset")

    def __init__(self, x, y, w, h, line, offset) -> None:
        self.x, self.y, self.w, self.h = x, y, w, h
        self.line, self.offset = line, offset

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def __repr__(self) -> str:
        return f"({self.x:g},{self.y:g} {self.w:g}x{self.h:g})"


def parse_rects(source: str) -> list[Rect]:
    rects: list[Rect] = []
    for match in RECT_RE.finditer(source):
        rects.append(
            Rect(
                float(match.group("x")),
                float(match.group("y")),
                float(match.group("w")),
                float(match.group("h")),
                source.count("\n", 0, match.start()) + 1,
                match.start(),
            )
        )
    return rects


def overlap(a: Rect, b: Rect) -> tuple[float, float]:
    return (
        min(a.right, b.right) - max(a.x, b.x),
        min(a.bottom, b.bottom) - max(a.y, b.y),
    )


def contained(inner: Rect, outer: Rect) -> bool:
    return (
        inner.x >= outer.x - EPSILON
        and inner.y >= outer.y - EPSILON
        and inner.right <= outer.right + EPSILON
        and inner.bottom <= outer.bottom + EPSILON
    )


def check(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    dead_spans = [m.span() for m in DEFS_RE.finditer(source)]
    dead_spans += [m.span() for m in DECOR_RE.finditer(source)]
    rects = parse_rects(source)
    connectors = parse_connectors(source, dead_spans)
    circles = parse_circles(source, dead_spans)
    polygons = parse_polygons(source, dead_spans)
    cutoff = legend_cutoff(source)

    def legend_rect(rect: Rect) -> bool:
        return cutoff is not None and rect.y >= cutoff

    def legend_seg(seg: Segment) -> bool:
        return cutoff is not None and min(seg.y1, seg.y2) >= cutoff

    def legend_conn(conn: Connector) -> bool:
        return all(legend_seg(seg) for seg in conn.segments)

    nodes = [r for r in rects if r.w >= NODE_MIN_W and r.h >= NODE_MIN_H]
    masks = [
        r
        for r in rects
        if MASK_MIN_W <= r.w <= MASK_MAX_W and MASK_MIN_H <= r.h <= MASK_MAX_H
    ]

    findings: list[str] = []

    # 1. Mask clipped by a node painted later (§6 rule 6).
    for mask in masks:
        for node in nodes:
            if node.offset <= mask.offset:
                continue  # painted before the label; the label stays on top
            dx, dy = overlap(mask, node)
            if dx <= 1.0 or dy <= 1.0 or contained(mask, node):
                continue
            findings.append(
                f"{path.name}:{mask.line}: label mask {mask} is clipped by node "
                f"{node} declared later at line {node.line} (overlap {dx:g}x{dy:g}px)"
                f" - move the label onto a free segment of its connector"
            )
            break

    # Template files are component samplers: isolated demo arrows float in
    # open canvas by design, so only the label-clipping check applies.
    if path.name.startswith("template"):
        return findings

    live = [c for c in connectors if not legend_conn(c)]
    # Unmarked <line> elements are passive furniture (lane dividers, lifelines,
    # separator rules): they take arrowhead landings but are not routed
    # connectors, so the routing checks skip them.
    routed = [c for c in live if not (c.is_line and not c.marker_end)]
    # Directed connectors carry the arrowhead contract; undirected paths
    # (sequence lifelines drawn as paths) legitimately run under frames/plates.
    directed = [c for c in routed if c.marker_end]

    # 2. Parallel / collinear connector runs closer than 12px (§6 rule 3).
    for i, a in enumerate(routed):
        for b in routed[i + 1 :]:
            hit = None
            for sa in a.segments:
                if sa.curve or sa.length < MIN_SEG_LEN:
                    continue
                for sb in b.segments:
                    if sb.curve or sb.length < MIN_SEG_LEN:
                        continue
                    if sa.horizontal and sb.horizontal:
                        gap = abs(sa.y1 - sb.y1)
                        span = min(max(sa.x1, sa.x2), max(sb.x1, sb.x2)) - max(
                            min(sa.x1, sa.x2), min(sb.x1, sb.x2)
                        )
                    elif sa.vertical and sb.vertical:
                        gap = abs(sa.x1 - sb.x1)
                        span = min(max(sa.y1, sa.y2), max(sb.y1, sb.y2)) - max(
                            min(sa.y1, sa.y2), min(sb.y1, sb.y2)
                        )
                    else:
                        continue
                    if gap < PARALLEL_MIN_GAP - TOL and span > PARALLEL_MIN_SPAN:
                        hit = (sa, sb, gap, span)
                        break
                if hit:
                    break
            if hit:
                sa, sb, gap, span = hit
                findings.append(
                    f"{path.name}:{a.line}: connector segment {sa} runs {gap:g}px "
                    f"from segment {sb} of the connector at line {b.line} for "
                    f"{span:g}px - offset parallel runs by >={PARALLEL_MIN_GAP:g}px "
                    f"(SKILL.md §6 rule 3)"
                )

    # 3. Connector stroke buried under a node painted later (§5 paint order).
    # A transparent rect (region boundary, focus frame) hides nothing.
    def sees_through(rect: Rect) -> bool:
        tag_end = source.find(">", rect.offset)
        tag = source[rect.offset : tag_end if tag_end != -1 else rect.offset + 400]
        fill = (attr(tag, "fill") or "").strip().lower()
        return fill in ("none", "transparent")

    for conn in directed:
        for node in nodes:
            if node.offset <= conn.offset or legend_rect(node) or sees_through(node):
                continue
            buried = sum(
                clip_length(seg, node, INTERIOR_INSET) for seg in conn.segments
            )
            if buried > INTERIOR_MIN_CLIP:
                findings.append(
                    f"{path.name}:{conn.line}: connector stroke is buried for "
                    f"{buried:g}px under node {node} declared later at line "
                    f"{node.line} - route around the node or through open canvas"
                )

    # 4. Label mask too close to a connector stroke (§6 rule 2).
    for mask in masks:
        if legend_rect(mask) or any(contained(mask, node) for node in nodes):
            continue  # badge chips live inside nodes; strokes never enter them
        for conn in directed:
            worst = None
            for seg in conn.segments:
                if seg.curve or legend_seg(seg):
                    continue  # arc chords misstate where the curve really runs
                dist = seg_rect_distance(seg, mask)
                if dist < MASK_CLEARANCE - TOL and (worst is None or dist < worst[1]):
                    worst = (seg, dist)
            if worst:
                seg, dist = worst
                what = (
                    "sits on"
                    if dist == 0
                    else f"is only {dist:.1f}px from"
                )
                findings.append(
                    f"{path.name}:{mask.line}: label mask {mask} {what} the "
                    f"connector stroke {seg} at line {conn.line} - keep a "
                    f">={MASK_CLEARANCE:g}px gap (SKILL.md §6 rule 2)"
                )

    # 5. Arrowhead landing in open canvas (§6 rule 4).
    landing_rects = [
        r
        for r in rects
        if not legend_rect(r)
        and (
            (r.w >= LANDING_MIN_SIDE and r.h >= LANDING_MIN_SIDE)
            or (r.w >= 6.0 and r.h >= 40.0)  # sequence activation bars
        )
    ]
    for conn in directed:
        if conn.end is None:
            continue
        px, py = conn.end
        if any(on_rect_border(px, py, r, LANDING_TOL) for r in landing_rects):
            continue
        if any(
            abs(((px - c.cx) ** 2 + (py - c.cy) ** 2) ** 0.5 - c.r) <= LANDING_TOL
            or ((px - c.cx) ** 2 + (py - c.cy) ** 2) ** 0.5 < c.r
            for c in circles
        ):
            continue
        if any(
            seg_point_distance(edge, px, py) <= LANDING_TOL
            for polygon in polygons
            for edge in polygon
        ):
            continue
        if any(
            other is not conn
            and any(
                seg_point_distance(seg, px, py) <= LANDING_TOL
                for seg in other.segments
            )
            for other in live
        ):
            continue
        findings.append(
            f"{path.name}:{conn.line}: arrowhead ends at ({px:g},{py:g}) in open "
            f"canvas - land it on a shape border or another connector "
            f"(SKILL.md §6 rule 4)"
        )

    return findings


def targets(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return sorted(ASSET_DIR.glob("*.html"))
    return [Path(p) for p in args.files]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="HTML diagrams to check")
    parser.add_argument("--all", action="store_true", help="check every shipped asset")
    args = parser.parse_args()

    paths = targets(args)
    if not paths:
        parser.error("pass one or more files, or --all")

    findings: list[str] = []
    for path in paths:
        if not path.exists():
            findings.append(f"{path}: file not found")
            continue
        findings.extend(check(path))

    for finding in findings:
        print(finding)
    print(f"Summary: {len(paths)} file(s) checked, {len(findings)} finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
