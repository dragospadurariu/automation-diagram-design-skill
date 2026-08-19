#!/usr/bin/env python3
"""Emit a native draw.io (.drawio) file from a generated diagram HTML.

Prototype for the dual-emitter experiment: does a ``.drawio`` derived from an
existing editorial diagram look close enough to the HTML, and is it pleasant to
edit in draw.io? This script answers that on real output instead of on a guess.

It deliberately reuses the *reading* half the verification scripts already do.
``verify-geometry.py`` classifies a node card as a rect at least 60x40, and this
emitter uses the same threshold, so "what counts as a node" stays one decision
in two places rather than two decisions that drift.

The pipeline is mechanical — there is no layout engine and no semantic model:

    HTML + inline SVG
        -> CSS cascade (rules by selector, then per element)
        -> SVG element census (rects, texts, paths, polygons, lines)
        -> classification (canvas / band / node / badge / mask / chip)
        -> mxGraphModel

Geometry is copied verbatim from the source, so the draw.io layout is identical
to the HTML layout by construction. Everything the editorial skin expresses in
CSS that draw.io has no vocabulary for -- letter-spacing, webfonts, motion --
is dropped and reported in the delta ledger printed at the end.

Usage:
    python3 mxgraph_emit.py <diagram.html> [--out PATH] [--report]

Exit codes: 0 ok, 2 unreadable / no <svg> block.
"""

from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"

# Same thresholds verify-geometry.py uses to decide "this rect is a node card".
NODE_MIN_W = 60.0
NODE_MIN_H = 40.0

# A label mask is a paper-filled rect punched behind arrow text. draw.io does
# the same job with labelBackgroundColor, so the mask itself is never emitted.
MASK_MIN_W, MASK_MAX_W = 20.0, 200.0
MASK_MIN_H, MASK_MAX_H = 8.0, 14.0

# How close a path endpoint must sit to a node edge to count as attached.
ATTACH_TOLERANCE = 8.0

MONO_HINT = ("mono", "Mono")


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(2)


TAG_RE = re.compile(r"""<([a-zA-Z][\w:.-]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(/?)>""")
ATTR_RE = re.compile(r"""([a-zA-Z_:][\w:.-]*)\s*(=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?""")


def quote_boolean_attributes(markup: str) -> str:
    """Give valueless attributes a value so ElementTree will accept the markup.

    The animated diagrams mark their steps with bare `data-motion-item`, which is
    fine in HTML5 and fatal in XML. Rewriting it to `data-motion-item="..."`
    changes nothing this emitter reads and keeps those files parseable.
    """

    def fix(match: re.Match[str]) -> str:
        name, attrs, close = match.group(1), match.group(2), match.group(3)
        if "=" not in attrs and not attrs.strip():
            return match.group(0)
        parts = [
            f"{key}{value}" if value else f'{key}="{key}"'
            for key, value in (
                (am.group(1), am.group(2)) for am in ATTR_RE.finditer(attrs)
            )
        ]
        joined = (" " + " ".join(parts)) if parts else ""
        return f"<{name}{joined}{close}>"

    return TAG_RE.sub(fix, markup)


def reject_unsafe_xml(xml: str, source: str) -> None:
    """Reject declarations that can make XML parsing expand external data.

    Same guard drawio_extract.py applies before handing markup to ElementTree.
    """
    upper = xml.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        fail(f"{source}: DTD and entity declarations are not supported")


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

FONT_LINK_RE = re.compile(
    r'<link[^>]+href="(https://fonts\.googleapis\.com/[^"]+)"', re.IGNORECASE
)
VAR_RE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
FONT_SHORTHAND_RE = re.compile(r"(\d+)\s+([\d.]+(?:px|rem|em))\s+(.+)")
LENGTH_RE = re.compile(r"(-?[\d.]+)\s*(px|rem|em|pt)?$")
COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)

# The declarations this emitter can act on. Everything else in the stylesheet
# describes page chrome draw.io has no vocabulary for, so it is never read and
# never carried around.
PAINT_PROPS = ("fill", "stroke", "stroke-width", "stroke-dasharray", "opacity")
TEXT_PROPS = ("font", "font-size", "font-family", "font-weight", "letter-spacing", "text-anchor")
READ_PROPS = frozenset(PAINT_PROPS + TEXT_PROPS)

# Paint and type inherit down the SVG tree; `opacity` composites the subtree it
# sits on and does not. A lane hairline drawn inside
# `<g class="rule" stroke-width=".8">` gets its weight from the group or nowhere.
INHERITED_PROPS = READ_PROPS - {"opacity"}

# Every readable property except the `font` shorthand also exists as an SVG
# presentation attribute, spelled identically.
ATTR_PROPS = PAINT_PROPS + tuple(p for p in TEXT_PROPS if p != "font")

# A compound step of a selector: an optional element type plus any classes.
COMPOUND_RE = re.compile(r"^([a-zA-Z][\w-]*)?((?:\.[\w-]+)+)?$")

# The pages never restyle the root, so a rem is the browser default.
ROOT_FONT_PX = 16.0


def css_px(value: str, default: float = 0.0) -> float:
    """A CSS length in px. Page chrome is sized in rem, SVG text in px, and a
    single unparsed declaration used to take the whole file down."""
    match = LENGTH_RE.match(value.strip().lower())
    if not match:
        return default
    size = float(match.group(1))
    unit = match.group(2) or "px"
    if unit in ("rem", "em"):
        return size * ROOT_FONT_PX
    if unit == "pt":
        return size * 4 / 3
    return size


@dataclass
class ClassStyle:
    fill: str = ""
    font_size: float = 0.0
    font_family: str = ""
    font_weight: str = ""
    letter_spacing: str = ""
    anchor: str = ""


@dataclass(frozen=True)
class Compound:
    """One `tag.class.class` step of a selector."""

    tag: str = ""
    classes: frozenset[str] = frozenset()

    def matches(self, tag: str, classes: frozenset[str]) -> bool:
        return (not self.tag or self.tag == tag) and self.classes <= classes


@dataclass
class Rule:
    """One selector's declarations, with what it takes to outrank another.

    Order alone is not the cascade: `svg .node` is written before
    `svg .node.focal` in every skin, but it is the second one that has to win on
    a focal card, and that is specificity, not position.
    """

    chain: tuple[Compound, ...]
    decls: dict[str, str]
    specificity: tuple[int, int]
    order: int

    def matches(self, chain: list[tuple[str, frozenset[str]]]) -> bool:
        """Match the rightmost compound against the element, then each ancestor
        compound against some ancestor, nearest first — a descendant combinator
        skips generations, so `svg .node` still matches a card inside a group."""
        if not self.chain[-1].matches(*chain[-1]):
            return False
        index = len(chain) - 2
        for compound in reversed(self.chain[:-1]):
            while index >= 0 and not compound.matches(*chain[index]):
                index -= 1
            if index < 0:
                return False
            index -= 1
        return True


@dataclass
class Stylesheet:
    rules: list[Rule] = field(default_factory=list)

    def declarations(self, chain: list[tuple[str, frozenset[str]]]) -> dict[str, str]:
        """The class cascade for one element: every matching rule applied
        weakest first, so the more specific — and, at equal specificity, the
        later — declaration is the one left standing."""
        hits = sorted(
            (rule for rule in self.rules if rule.matches(chain)),
            key=lambda rule: (rule.specificity, rule.order),
        )
        out: dict[str, str] = {}
        for rule in hits:
            out.update(rule.decls)
        return out


def parse_selector(selector: str) -> tuple[Compound, ...] | None:
    """A selector as its descendant chain, or None when it uses syntax this
    emitter cannot honour.

    Child, sibling, attribute and pseudo selectors are how the skins express
    motion state, which draw.io has no notion of. Treating `.motion-ready
    [data-motion-item]` as if it were `.motion-ready` would paint shapes the
    browser leaves alone, so a selector that is not understood drops its rule.
    """
    compounds = []
    for step in selector.split():
        match = COMPOUND_RE.match(step)
        if not match or not (match.group(1) or match.group(2)):
            return None
        names = (match.group(2) or "").split(".")[1:]
        compounds.append(Compound(match.group(1) or "", frozenset(names)))
    return tuple(compounds) or None


def declaration_map(body: str) -> dict[str, str]:
    """The readable declarations of a rule body or an inline `style=""`."""
    out: dict[str, str] = {}
    for decl in body.split(";"):
        prop, sep, value = decl.partition(":")
        prop, value = prop.strip().lower(), value.strip()
        if sep and value and prop in READ_PROPS:
            out[prop] = value
    return out


def parse_css(source: str) -> tuple[Stylesheet, dict[str, str]]:
    """Return (stylesheet, css variable -> value)."""
    block = re.search(r"<style>(.*?)</style>", source, re.S)
    if not block:
        return Stylesheet(), {}
    css = COMMENT_RE.sub(" ", block.group(1))

    variables = {f"--{name}": value.strip() for name, value in VAR_RE.findall(css)}

    sheet = Stylesheet()
    for order, (selector, body) in enumerate(RULE_RE.findall(css)):
        decls = declaration_map(body)
        if not decls:
            continue
        for name in selector.split(","):
            chain = parse_selector(name.strip())
            if chain is None:
                continue
            sheet.rules.append(
                Rule(
                    chain=chain,
                    decls=decls,
                    specificity=(
                        sum(len(c.classes) for c in chain),
                        sum(1 for c in chain if c.tag),
                    ),
                    order=order,
                )
            )
    return sheet, variables


def class_style(decls: dict[str, str]) -> ClassStyle:
    """The typed text style behind a computed declaration set.

    The `font` shorthand is expanded before the longhands so that a skin which
    states `font:` on a base rule and `font-size:` on the variant gets the
    variant's size, which is what it asked for.
    """
    style = ClassStyle()
    shorthand = FONT_SHORTHAND_RE.match(decls.get("font", ""))
    if shorthand:
        style.font_weight = shorthand.group(1)
        style.font_size = css_px(shorthand.group(2))
        style.font_family = shorthand.group(3).strip()
    if "font-weight" in decls:
        style.font_weight = decls["font-weight"]
    if "font-size" in decls:
        style.font_size = css_px(decls["font-size"])
    if "font-family" in decls:
        style.font_family = decls["font-family"]
    if "fill" in decls:
        style.fill = decls["fill"]
    if "letter-spacing" in decls:
        style.letter_spacing = decls["letter-spacing"]
    if "text-anchor" in decls:
        style.anchor = decls["text-anchor"]
    return style


def resolve_var(value: str, variables: dict[str, str], depth: int = 0) -> str:
    """Flatten var(--token) chains down to a literal color or font stack."""
    if depth > 6:
        return value
    match = re.fullmatch(r"var\((--[\w-]+)\)", value.strip())
    if not match:
        return value.strip()
    return resolve_var(variables.get(match.group(1), ""), variables, depth + 1)


def first_family(stack: str) -> str:
    """draw.io takes a single family name, not a CSS fallback stack."""
    head = stack.split(",")[0].strip().strip("'\"")
    return head or "Helvetica"


# ---------------------------------------------------------------------------
# SVG model
# ---------------------------------------------------------------------------


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    fill: str = ""
    stroke: str = ""
    stroke_width: str = ""
    dash: str = ""
    opacity: str = ""
    rx: float = 0.0
    # "rect" | "rhombus" | "ellipse" — the draw.io shape family this box maps to.
    kind: str = "rect"
    # Position in document paint order. SVG paints in document order, so what
    # a shape covers depends on what came before it — a label drawn under a
    # later opaque card is invisible in the browser, and only the order says so.
    order: int = 0

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.right and self.y <= py <= self.bottom

    def encloses(self, other: "Box", tol: float = 0.5) -> bool:
        """True when `other` sits entirely inside this box. Strictly smaller
        area is part of the test: two shapes tracing the same outline overlap,
        they do not contain each other, and treating them as nested would make
        each the other's parent."""
        return (
            self.w * self.h > other.w * other.h
            and self.x - tol <= other.x
            and self.y - tol <= other.y
            and self.right + tol >= other.right
            and self.bottom + tol >= other.bottom
        )


def painted(value: str) -> bool:
    """Whether a paint value actually puts ink down. `none` and `transparent`
    are declared paints that draw nothing — a rect whose only stroke is
    `transparent` is unstroked for every decision this emitter makes."""
    return bool(value) and value not in ("none", "transparent")


@dataclass
class Label:
    x: float
    y: float
    text: str
    classes: list[str]
    style: ClassStyle
    order: int = 0


@dataclass
class Connector:
    points: list[tuple[float, float]]
    stroke: str
    stroke_width: str
    dash: str
    arrow: bool
    opacity: str = ""


@dataclass
class Node:
    box: Box
    labels: list[Label] = field(default_factory=list)
    children: list[Box] = field(default_factory=list)
    child_labels: list[Label] = field(default_factory=list)
    # Index of the innermost node enclosing this one, when it is nested.
    parent_index: int | None = None
    # True when other nodes nest inside this one: a zone or frame, not a card.
    container: bool = False


D_TOKEN_RE = re.compile(r"([MLHVQCSTAZmlhvqcstaz])|(-?[\d.]+(?:e-?\d+)?)")

# Parameter count per path command. The on-curve endpoint is always the last
# two parameters of a group (the single parameter for H/V), which is why an
# arc's radii, rotation and flags can be read past without being understood.
PATH_ARITY = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "Q": 4, "S": 4, "C": 6, "A": 7, "Z": 0}


def path_points(d: str) -> list[tuple[float, float]]:
    """Flatten a path `d` to the on-curve points it visits. Control points are
    ignored — only the positions the pen lands on matter for endpoint
    resolution.

    Every command a browser accepts has to be tokenised, even the ones whose
    geometry is discarded: an unrecognised `A` dumps seven parameters into the
    previous command's number list and shifts every point after it. And a
    lowercase command is relative to the current point, not a stylistic
    variant — read as absolute, `a25 25 0 0 1 50 0` collapses onto the origin.
    """
    points: list[tuple[float, float]] = []
    cx = cy = sx = sy = 0.0

    def land(cmd: str, group: list[float]) -> None:
        nonlocal cx, cy, sx, sy
        op = cmd.upper()
        if op == "Z":
            cx, cy = sx, sy
            return
        relative = cmd.islower()
        if op == "H":
            cx = group[0] + (cx if relative else 0.0)
        elif op == "V":
            cy = group[0] + (cy if relative else 0.0)
        else:
            cx = group[-2] + (cx if relative else 0.0)
            cy = group[-1] + (cy if relative else 0.0)
        if op == "M":
            sx, sy = cx, cy
        points.append((cx, cy))

    command = ""
    numbers: list[float] = []

    def flush() -> None:
        if not command:
            numbers.clear()
            return
        arity = PATH_ARITY[command.upper()]
        if arity == 0:
            land(command, [])
        cmd, index = command, 0
        while arity and index + arity <= len(numbers):
            land(cmd, numbers[index : index + arity])
            index += arity
            # Extra coordinate pairs after a moveto are implicit linetos.
            if cmd in "Mm":
                cmd = "L" if cmd == "M" else "l"
        numbers.clear()

    for letter, num in D_TOKEN_RE.findall(d):
        if letter:
            flush()
            command = letter
        else:
            numbers.append(float(num))
    flush()
    return points


POINT_NUM_RE = re.compile(r"-?[\d.]+")


def poly_points(attr: str) -> list[tuple[float, float]]:
    """A polygon/polyline `points` attribute as coordinate pairs. The grammar
    allows commas, whitespace or both between numbers, and the skins use every
    spelling."""
    nums = [float(n) for n in POINT_NUM_RE.findall(attr or "")]
    return list(zip(nums[0::2], nums[1::2]))


def attr_float(el: ET.Element, name: str, default: float = 0.0, base: float | None = None) -> float:
    """An SVG geometry attribute as a number.

    SVG lengths may be percentages, and the backdrop rect of every editorial
    diagram is written `width="100%" height="100%"`. Read as 0 it stops being
    the canvas, and the page colour it carries is lost along with every rule
    that keys off the page colour. A percentage resolves against the viewBox,
    which is the only coordinate system these single-page diagrams have.
    """
    raw = el.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    try:
        if raw.endswith("%"):
            return default if base is None else float(raw[:-1]) / 100.0 * base
        return float(raw)
    except ValueError:
        return default


def text_content(el: ET.Element) -> str:
    return "".join(el.itertext()).strip()


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


@dataclass
class Scene:
    width: float
    height: float
    title: str
    description: str
    background: str
    bands: list[Box] = field(default_factory=list)
    rules: list[Connector] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    loose_boxes: list[Box] = field(default_factory=list)
    loose_labels: list[Label] = field(default_factory=list)
    edges: list[Connector] = field(default_factory=list)
    masks: list[Box] = field(default_factory=list)
    # Mask rects the source paints under a later opaque card: hidden in the
    # browser, so their text must not resurface in the export.
    occluded_masks: list[Box] = field(default_factory=list)
    occluded_texts: list[str] = field(default_factory=list)
    # Animation step groups (`data-motion-item`) flattened into one frame.
    motion_items: int = 0
    coincident_dropped: int = 0
    texture_dropped: int = 0
    # <use> icon instances dropped on purpose, counted per referenced symbol id.
    icons_dropped: dict[str, int] = field(default_factory=dict)


def build_scene(svg: ET.Element, sheet: Stylesheet, variables: dict[str, str]) -> Scene:
    view = (svg.get("viewBox") or "0 0 960 600").split()
    width, height = float(view[2]), float(view[3])

    title_el = svg.find(f"{{{SVG_NS}}}title")
    desc_el = svg.find(f"{{{SVG_NS}}}desc")
    scene = Scene(
        width=width,
        height=height,
        title=text_content(title_el) if title_el is not None else "",
        description=text_content(desc_el) if desc_el is not None else "",
        background="#ffffff",
    )

    rects: list[Box] = []
    labels: list[Label] = []

    def computed_style(
        el: ET.Element,
        chain: list[tuple[str, frozenset[str]]],
        inherited: dict[str, str],
    ) -> dict[str, str]:
        """Every declaration in force on one element, in CSS precedence order:
        inline `style=""` over presentation attribute over class rule over what
        the parent handed down.

        Reading paint from attributes alone leaves a class-styled skin unpainted,
        and an unpainted shape is not a subtle loss: it emits as an invisible
        cell that still sits in front of the card it covers and still wins that
        card's text. Tokens are flattened here so every consumer downstream —
        classification as much as emission — compares literal colours.
        """
        decls = {k: v for k, v in inherited.items() if k in INHERITED_PROPS}
        decls.update(sheet.declarations(chain))
        for prop in ATTR_PROPS:
            value = (el.get(prop) or "").strip()
            if value:
                decls[prop] = value
        decls.update(declaration_map(el.get("style", "")))
        return {k: resolve_var(v, variables) for k, v in decls.items()}

    def walk(parent: ET.Element, chain: list[tuple[str, frozenset[str]]], inherited: dict[str, str]):
        """Depth-first, skipping <defs> and everything under it — markers and
        patterns are paint machinery, not diagram content. Each element carries
        down the chain the cascade needs and the style its children inherit."""
        for child in parent:
            tag = child.tag.split("}")[-1]
            if tag == "defs":
                continue
            child_chain = chain + [(tag, frozenset((child.get("class") or "").split()))]
            style = computed_style(child, child_chain, inherited)
            yield child, tag, style
            yield from walk(child, child_chain, style)

    def outline(
        points: list[tuple[float, float]],
        closed: bool,
        css: dict[str, str],
        arrow: bool,
        order: int = 0,
    ) -> None:
        """File a hand-drawn outline — <path>, <polygon> or <polyline> — as
        either a shape or a connector. A closed, filled outline is a shape the
        skin drew itself, a decision diamond most often (four distinct corners
        map to draw.io's rhombus); everything open with extent is a connector.
        One decision for all three tags, so a diamond classifies the same way
        whether Mermaid spelled it as a path or a polygon."""
        fill = css.get("fill", "")
        if closed and points and fill and fill != "none":
            xs = [pt[0] for pt in points]
            ys = [pt[1] for pt in points]
            rects.append(
                Box(
                    x=min(xs),
                    y=min(ys),
                    w=max(xs) - min(xs),
                    h=max(ys) - min(ys),
                    fill=fill,
                    stroke=css.get("stroke", ""),
                    stroke_width=css.get("stroke-width", ""),
                    dash=css.get("stroke-dasharray", ""),
                    opacity=css.get("opacity", ""),
                    kind="rhombus" if len(set(points)) == 4 else "rect",
                    order=order,
                )
            )
        elif len(points) >= 2:
            scene.edges.append(
                Connector(
                    points=points,
                    stroke=css.get("stroke", ""),
                    stroke_width=css.get("stroke-width", ""),
                    dash=css.get("stroke-dasharray", ""),
                    arrow=arrow,
                    opacity=css.get("opacity", ""),
                )
            )

    root_chain = [("svg", frozenset((svg.get("class") or "").split()))]
    for order, (el, tag, css) in enumerate(
        walk(svg, root_chain, computed_style(svg, root_chain, {}))
    ):
        if el.get("data-motion-item") is not None:
            scene.motion_items += 1
        if tag == "rect":
            rects.append(
                Box(
                    x=attr_float(el, "x", base=width),
                    y=attr_float(el, "y", base=height),
                    w=attr_float(el, "width", base=width),
                    h=attr_float(el, "height", base=height),
                    fill=css.get("fill", ""),
                    stroke=css.get("stroke", ""),
                    stroke_width=css.get("stroke-width", ""),
                    dash=css.get("stroke-dasharray", ""),
                    opacity=css.get("opacity", ""),
                    rx=attr_float(el, "rx", base=width),
                    order=order,
                )
            )
        elif tag == "text":
            labels.append(
                Label(
                    x=attr_float(el, "x"),
                    y=attr_float(el, "y"),
                    text=text_content(el),
                    classes=(el.get("class") or "").split(),
                    style=class_style(css),
                    order=order,
                )
            )
        elif tag == "path":
            outline(
                path_points(el.get("d", "")),
                el.get("d", "").strip()[-1:] in "Zz",
                css,
                bool(el.get("marker-end")),
                order,
            )
        elif tag in ("polygon", "polyline"):
            outline(
                poly_points(el.get("points", "")),
                tag == "polygon",
                css,
                bool(el.get("marker-end")),
                order,
            )
        elif tag == "use":
            # An icon instance references a <symbol> in <defs>: a 24px glyph
            # built of hairline strokes. Decomposed into draw.io cells it would
            # be edit noise, not an icon, so the instance is dropped on purpose
            # — and counted, because a silent drop looks exactly like a bug.
            ref = (
                el.get("href")
                or el.get("{http://www.w3.org/1999/xlink}href")
                or ""
            ).lstrip("#") or "(unresolved)"
            scene.icons_dropped[ref] = scene.icons_dropped.get(ref, 0) + 1
        elif tag in ("circle", "ellipse"):
            cx, cy = attr_float(el, "cx"), attr_float(el, "cy")
            rx = attr_float(el, "r") or attr_float(el, "rx")
            ry = attr_float(el, "r") or attr_float(el, "ry")
            if rx and ry:
                rects.append(
                    Box(
                        x=cx - rx,
                        y=cy - ry,
                        w=rx * 2,
                        h=ry * 2,
                        fill=css.get("fill", ""),
                        stroke=css.get("stroke", ""),
                        stroke_width=css.get("stroke-width", ""),
                        dash=css.get("stroke-dasharray", ""),
                        opacity=css.get("opacity", ""),
                        kind="ellipse",
                        order=order,
                    )
                )
        elif tag == "line":
            connector = Connector(
                points=[
                    (attr_float(el, "x1"), attr_float(el, "y1")),
                    (attr_float(el, "x2"), attr_float(el, "y2")),
                ],
                stroke=css.get("stroke", ""),
                stroke_width=css.get("stroke-width", ""),
                dash=css.get("stroke-dasharray", ""),
                arrow=bool(el.get("marker-end")),
                opacity=css.get("opacity", ""),
            )
            (scene.edges if connector.arrow else scene.rules).append(connector)

    # --- rects: canvas, band, node, mask, loose --------------------------
    node_boxes: list[Box] = []
    remaining: list[Box] = []
    for box in rects:
        full_canvas = box.w >= scene.width - 0.5 and box.h >= scene.height - 0.5
        if full_canvas:
            # The canvas is paint, not content: a solid paper rect plus a dot
            # pattern laid over it. draw.io has a page colour and no page
            # pattern, so the colour is hoisted and the texture is reported.
            if box.fill.strip().startswith("url("):
                scene.texture_dropped += 1
            elif box.fill:
                scene.background = color(box.fill, scene.background, variables)
            continue
        if box.x <= 0.5 and box.w >= scene.width - 0.5:
            scene.bands.append(box)
            continue
        # verify-geometry's card thresholds catch the big rectangles. A
        # terminator pill or a decision diamond is smaller than a card but still
        # a node, and what separates it from a badge is that it carries a stroke.
        stroked_shape = box.stroke and box.w >= 24 and box.h >= 16
        if (box.w >= NODE_MIN_W and box.h >= NODE_MIN_H) or stroked_shape or box.kind != "rect":
            node_boxes.append(box)
            continue
        # A mask hides what is under it, so it has to be opaque. `color()`
        # answers with the opaque hex of an rgba() fill, which makes a 10%-white
        # role badge on white paper look exactly like a mask and disappear.
        # Colour alone is not the test either: a mask over a tinted lane is
        # painted the lane's tone, not the paper's, so a rect that matches
        # neither is still a mask when it does a mask's job — sitting punched
        # through a connector. The connector census is complete before any rect
        # is classified, so the role can be read directly.
        mask_shaped = (
            MASK_MIN_W <= box.w <= MASK_MAX_W
            and MASK_MIN_H <= box.h <= MASK_MAX_H
            and (alpha_of(box.fill) or 1.0) >= 1.0
            and painted(box.fill)
            and not box.stroke
        )
        is_mask = mask_shaped and (
            color(box.fill, "", variables) == scene.background
            or punched_through(box, scene.edges)
        )
        if is_mask:
            scene.masks.append(box)
            continue
        remaining.append(box)

    # A card is sometimes painted as two coincident rects: an opaque underlay
    # beneath a translucent skin, or a tint beneath an outline-only emphasis
    # ring. draw.io has one cell per shape; keeping both would leave an
    # unlabelled duplicate under every node — a trap the moment someone drags
    # the top card away. But the pair is one shape whose paint is split across
    # two layers, so each kind of paint comes from whichever layer defines it
    # (the top-painted layer winning where both do). Keeping the top rect
    # unconditionally turned every tint-plus-outline pair into a transparent
    # hole where the source shows its most emphasised shape.
    deduped: list[Box] = []
    for box in node_boxes:
        twin = next(
            (b for b in deduped if (b.x, b.y, b.w, b.h) == (box.x, box.y, box.w, box.h)),
            None,
        )
        if twin is None:
            deduped.append(box)
            continue
        if not painted(box.fill) and painted(twin.fill):
            box.fill = twin.fill
            box.opacity = box.opacity or twin.opacity
        if not painted(box.stroke) and painted(twin.stroke):
            box.stroke = twin.stroke
            box.stroke_width = box.stroke_width or twin.stroke_width
            box.dash = box.dash or twin.dash
        deduped[deduped.index(twin)] = box
        scene.coincident_dropped += 1

    # SVG paints in document order, and the skins rely on it: a transition
    # label whose mask strays over a state card is drawn first and then buried
    # under the opaque card, so the browser never shows it. The emitter draws
    # labels on top of everything, so the only faithful translation of a
    # buried mask is to drop it — with its text — and say so in the ledger.
    # A hidden label resurfacing over a card is a worse lie than a missing one.
    def opaque(box: Box) -> bool:
        try:
            faded = box.opacity != "" and float(box.opacity) < 1.0
        except ValueError:
            faded = False
        return painted(box.fill) and (alpha_of(box.fill) or 1.0) >= 1.0 and not faded

    visible_masks: list[Box] = []
    for mask in scene.masks:
        buried = any(
            box.encloses(mask) and box.order > mask.order and opaque(box)
            for box in deduped
        )
        (scene.occluded_masks if buried else visible_masks).append(mask)
    scene.masks = visible_masks

    # A lane inset past an actor gutter never touches x=0, so the x-test above
    # misses it. What makes a lane a lane is its shape and its company, not its
    # left edge: a wide unstroked stripe spanning most of the canvas, stacked
    # with at least one sibling of the same x and width, with node cards
    # sitting inside the family. A lone wide rect — a layer row, a hero card —
    # keeps its label and stays a node.
    stripes: dict[tuple[float, float], list[Box]] = {}
    for box in deduped:
        is_stripe = (
            box.kind == "rect"
            and not painted(box.stroke)
            and box.w >= scene.width * 0.75
            and box.h <= scene.height / 2
        )
        if is_stripe:
            stripes.setdefault((round(box.x), round(box.w)), []).append(box)
    for family in stripes.values():
        cards_inside = any(
            stripe.encloses(box)
            for stripe in family
            for box in deduped
            if box not in family
        )
        if len(family) < 2 or not cards_inside:
            continue
        for lane in family:
            deduped.remove(lane)
            scene.bands.append(lane)

    scene.nodes = [Node(box=b) for b in deduped]

    # A node that encloses other nodes is a container — a zone, trust boundary
    # or group frame — not a card. Naming its parent here lets emission nest
    # the cards into it, so dragging the frame in draw.io takes its contents
    # along instead of sliding an empty rectangle out from under them. The
    # innermost enclosure is the parent: a card in a zone in a region belongs
    # to the zone, and the zone to the region.
    def area(node: Node) -> float:
        return node.box.w * node.box.h

    for index, node in enumerate(scene.nodes):
        enclosing = [
            j for j, other in enumerate(scene.nodes) if j != index and other.box.encloses(node.box)
        ]
        if enclosing:
            node.parent_index = min(enclosing, key=lambda j: area(scene.nodes[j]))
            scene.nodes[node.parent_index].container = True

    # Every mask matches one paper recipe, but not every mask annotates an
    # arrow: a zone prints its title on the same paper chip. A masked text has
    # exactly two possible owners — the connector it is punched through, or
    # the frame it captions — and the closer of the two is the owner. An
    # annotation mask sits on its connector (that is the mask's whole job); a
    # frame title sits where the skins put frame titles, tucked inside the
    # frame's top edge, far from any line. The bottom and side borders make no
    # claim: an arrow label may drift right up against a border of a zone it
    # merely overlaps, and only the title position marks a caption. A losing
    # chip stops being a mask and returns to the small-rect pool, where it
    # becomes the frame's badge and keeps its text.
    kept_masks: list[Box] = []
    for mask in scene.masks:
        cx, cy = mask.x + mask.w / 2, mask.y + mask.h / 2
        edge_distance = min(
            (
                point_to_segment(cx, cy, *c.points[i], *c.points[i + 1])
                for c in scene.edges
                for i in range(len(c.points) - 1)
            ),
            default=1e9,
        )
        title_distance = min(
            (cy - node.box.y for node in scene.nodes if node.box.encloses(mask)),
            default=1e9,
        )
        (remaining if title_distance < edge_distance else kept_masks).append(mask)
    scene.masks = kept_masks

    # --- attach small rects and text to their node -----------------------
    # Ownership goes to the innermost enclosure, never the first one painted:
    # containers are painted before the cards they hold, so first-in-document
    # order hands a zone every enclosed card's text and badges and ships the
    # cards empty. A badge must sit entirely inside its owner — a bar that
    # sticks out of a frame is on the frame, not of it, and re-parenting it
    # would drag it along when the frame moves.
    for box in remaining:
        owner = min(
            (n for n in scene.nodes if n.box.encloses(box)),
            key=area,
            default=None,
        )
        (owner.children if owner else scene.loose_boxes).append(box)  # type: ignore[union-attr]

    for label in labels:
        # Text on a buried mask is as invisible as the mask itself.
        if any(mask.contains(label.x, label.y) for mask in scene.occluded_masks):
            scene.occluded_texts.append(label.text)
            continue
        # A label on a paper mask is an arrow annotation by construction —
        # the mask exists to punch the text through a connector. It belongs to
        # the edge pass even when a zone or frame happens to enclose it.
        if any(mask.contains(label.x, label.y) for mask in scene.masks):
            scene.loose_labels.append(label)
            continue
        owner = min(
            (n for n in scene.nodes if n.box.contains(label.x, label.y)),
            key=area,
            default=None,
        )
        if owner is None:
            scene.loose_labels.append(label)
            continue
        # Text sitting on a badge belongs to the badge, not to the card body.
        on_child = any(c.contains(label.x, label.y) for c in owner.children)
        (owner.child_labels if on_child else owner.labels).append(label)

    for node in scene.nodes:
        node.labels.sort(key=lambda item: item.y)

    return scene


# ---------------------------------------------------------------------------
# mxGraphModel emission
# ---------------------------------------------------------------------------


def shape_prefix(box: Box) -> str:
    """Map a source shape to its draw.io style head."""
    if box.kind == "rhombus":
        return "rhombus;"
    if box.kind == "ellipse":
        return "ellipse;"
    arc = round(box.rx / min(box.w, box.h) * 100) if box.rx else 0
    return f"rounded={1 if box.rx else 0};arcSize={arc};"


def esc(value: str) -> str:
    return htmllib.escape(value, quote=True)


def color(value: str, fallback: str = "none", variables: dict[str, str] | None = None) -> str:
    """A source paint value as something draw.io's style vocabulary defines.

    The skin paints in brand tokens, so the token table is part of reading a
    colour, not a later step: an unresolved `var(--accent)` reaches draw.io as
    literal text and paints nothing. draw.io then knows hex and `none` only —
    rgba() collapses to its opaque hex (the alpha is re-emitted by `paint`),
    and the CSS keyword `transparent` is spelled `none`.
    """
    value = resolve_var(value or "", variables or {})
    if not value or value.startswith("url("):
        return fallback
    if value == "transparent":
        return "none"
    match = re.fullmatch(r"rgba?\(([^)]+)\)", value)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        r, g, b = (int(float(p)) for p in parts[:3])
        return f"#{r:02x}{g:02x}{b:02x}"
    return value


def paint(prefix: str, value: str, fallback: str = "none", variables: dict[str, str] | None = None) -> str:
    """Emit `<prefix>Color` plus `<prefix>Opacity` when the source color carries
    alpha. draw.io keeps fill and stroke opacity as separate style keys, so an
    rgba() token survives translation intact rather than flattening to opaque.
    """
    resolved = resolve_var(value or "", variables or {})
    bits = f"{prefix}Color={color(resolved, fallback)}"
    alpha = alpha_of(resolved)
    if alpha is not None:
        bits += f";{prefix}Opacity={alpha * 100:g}"
    return bits


def alpha_of(value: str) -> float | None:
    match = re.fullmatch(r"rgba\(([^)]+)\)", (value or "").strip())
    if not match:
        return None
    parts = [p.strip() for p in match.group(1).split(",")]
    return float(parts[3]) if len(parts) == 4 else None


def opacity_bits(value: str) -> str:
    """The SVG `opacity` attribute fades a whole shape, fill and stroke alike;
    draw.io spells the same thing `opacity`, in percent. Dropped, a hairline
    badge outline drawn at .45 reads twice as heavy as it does in the HTML."""
    try:
        alpha = float((value or "").strip())
    except ValueError:
        return ""
    if alpha >= 1.0:
        return ""
    return f"opacity={max(alpha, 0.0) * 100:g};"


def dash_bits(dasharray: str) -> str:
    """A dashed outline is never decoration in these diagrams — it is the
    legend key for "planned" or "gap", so a solid outline says the wrong thing.
    draw.io's dashPattern is the SVG dasharray with spaces instead of commas."""
    pattern = " ".join((dasharray or "").replace(",", " ").split())
    if not pattern or pattern == "none":
        return ""
    return f"dashed=1;dashPattern={pattern};"


def font_source(family: str, sheet: str) -> str:
    """draw.io renders a non-installed family only if the cell says where to get
    it. mxGraph's `fontSource` takes a URL-encoded stylesheet URL — undocumented
    in the AI reference, but it is what turns the editorial type back on."""
    if not sheet or not family:
        return ""
    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}&display=swap"
    return "fontSource=" + quote(url, safe="")


def font_style_bits(style: ClassStyle, variables: dict[str, str], sheet: str = "") -> str:
    family = first_family(resolve_var(style.font_family, variables)) if style.font_family else ""
    bits = []
    if family:
        bits.append(f"fontFamily={family}")
        source = font_source(family, sheet)
        if source:
            bits.append(source)
    if style.font_size:
        bits.append(f"fontSize={style.font_size:g}")
    weight = style.font_weight or ""
    if weight and weight.isdigit() and int(weight) >= 600:
        bits.append("fontStyle=1")
    fill = color(style.fill, "", variables)
    if fill and fill != "none":
        bits.append(f"fontColor={fill}")
    return ";".join(bits)


def estimate_width(text: str, style: ClassStyle, variables: dict[str, str]) -> float:
    size = style.font_size or 8.0
    family = resolve_var(style.font_family, variables)
    ratio = 0.62 if any(hint in family for hint in MONO_HINT) else 0.55
    return max(len(text) * size * ratio, size * 2)


def node_label(node: Node, variables: dict[str, str]) -> str:
    """Fold the card's stacked text lines into one HTML label.

    Emitting each line as its own cell would be more faithful, but then editing
    a node title means hunting for a sub-element. One label per card is the
    whole point of shipping .drawio.
    """
    lines = []
    for index, label in enumerate(node.labels):
        style = label.style
        fill = color(style.fill, "", variables)
        size = style.font_size or 9.0
        family = first_family(resolve_var(style.font_family, variables))
        css = f"font-size:{size:g}px;font-family:{esc(family)}"
        if fill:
            css += f";color:{fill}"
        weight = style.font_weight
        if weight and weight.isdigit() and int(weight) >= 600:
            css += ";font-weight:600"
        if style.letter_spacing:
            css += f";letter-spacing:{style.letter_spacing}"
        lines.append(f'<span style="{css}">{esc(label.text)}</span>')
        if index < len(node.labels) - 1:
            lines.append("<br>")
    return "".join(lines)


def edge_endpoint(
    point: tuple[float, float], targets: list[tuple[str, Box]]
) -> tuple[str, float, float] | None:
    """Resolve a path endpoint to (cell id, exitX, exitY) if it lands on an
    emitted vertex's boundary.

    Every vertex is a candidate, not only node cards: a sequence message
    terminates on an activation bar, and the bar is a badge or a loose chip,
    never a node. Among the shapes whose boundary the point touches, the
    nearest edge wins and the smaller shape breaks the tie — an endpoint on a
    bar inside a combined fragment belongs to the bar, not the frame around it.
    Returns None for legend arrows and other free-floating connectors, which
    keep explicit coordinates instead."""
    px, py = point
    best: tuple[str, float, float] | None = None
    best_key: tuple[float, float] | None = None
    for cid, box in targets:
        if not (box.w and box.h):
            continue
        near_x = box.x - ATTACH_TOLERANCE <= px <= box.right + ATTACH_TOLERANCE
        near_y = box.y - ATTACH_TOLERANCE <= py <= box.bottom + ATTACH_TOLERANCE
        if not (near_x and near_y):
            continue
        edge_distance = min(
            abs(px - box.x), abs(px - box.right), abs(py - box.y), abs(py - box.bottom)
        )
        if edge_distance > ATTACH_TOLERANCE:
            continue
        key = (edge_distance, box.w * box.h)
        if best_key is None or key < best_key:
            best = (cid, (px - box.x) / box.w, (py - box.y) / box.h)
            best_key = key
    return best


def point_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def punched_through(box: Box, connectors: list[Connector]) -> bool:
    """Whether a connector runs through (or hard against) this box — the job
    description of a label mask. The box's own height is the reach: a mask
    exists to hide the line under its text, so a line farther away than the
    mask is tall was never being hidden by it."""
    cx, cy = box.x + box.w / 2, box.y + box.h / 2
    return any(
        point_to_segment(cx, cy, *c.points[i], *c.points[i + 1]) <= box.h
        for c in connectors
        for i in range(len(c.points) - 1)
    )


def furniture_style(box: Box, variables: dict[str, str]) -> str:
    """The shared style head of the small furniture — badges and chips.

    `spacing=0` alone does not centre a label in a pill-sized box: draw.io's
    HTML label path keeps its default side spacing unless spacingLeft and
    spacingRight are zeroed explicitly, and the residue is worth ~4px of lean
    plus ~6px of vertical sag at these sizes — on an 18x10 role badge the text
    escapes the pill entirely. Measured, not theorised: a probe of the same
    18x10/16x8 pills against centre hairlines, rendered by embed.diagrams.net
    at 6x and centroid-read per axis, puts every other combination (wrap on or
    off, html=0, overflow=fill/width, bold, Helvetica) off-centre on at least
    one axis, while wrap + spacing=0 + spacingLeft=0 + spacingRight=0 reads
    dx = dy = -0.08px on both pill sizes.
    """
    return (
        f"{shape_prefix(box)}html=1;whiteSpace=wrap;"
        f"{paint('fill', box.fill, variables=variables)};"
        f"{paint('stroke', box.stroke, variables=variables)};"
        f"verticalAlign=middle;align=center;spacing=0;spacingLeft=0;spacingRight=0;"
        f"{dash_bits(box.dash)}{opacity_bits(box.opacity)}"
    )


def edge_annotations(
    edges: list[Connector], labels: list[Label], masks: list[Box]
) -> dict[int, list[Label]]:
    """Assign every arrow annotation to the connector that owns it.

    Proximity alone is not the test of what an annotation is. A legend caption
    sits right beside its sample arrow and would match on distance, but it is
    a caption, not an annotation — stealing it hides the arrow behind the
    label background. The source draws a real annotation on a paper mask
    punched through the connector (style-guide's label-mask primitive), so
    mask membership is the exact — and the only — membership signal.

    Distance then decides ownership and nothing else. Resolving from the
    connector side under a distance cut-off bound only the branch labels
    sitting close to their stroke and let the ones nudged further out fall
    through to standalone text, so one diagram's exit labels moved with their
    edges and their siblings did not. Resolving from the label side, each
    masked label binds to its nearest connector, however far it was nudged.
    """
    owners: dict[int, list[Label]] = {}
    for label in labels:
        if not any(mask.contains(label.x, label.y) for mask in masks):
            continue
        best, best_distance = None, 1e9
        for index, connector in enumerate(edges):
            if len(connector.points) < 2:
                continue
            distance = min(
                point_to_segment(label.x, label.y, *connector.points[i], *connector.points[i + 1])
                for i in range(len(connector.points) - 1)
            )
            if distance < best_distance:
                best, best_distance = index, distance
        if best is not None:
            owners.setdefault(best, []).append(label)
    return owners


def emit(scene: Scene, variables: dict[str, str], name: str, sheet: str = "") -> tuple[str, list[str]]:
    deltas: list[str] = []
    out: list[str] = []
    counter = {"n": 0}

    def cell_id(prefix: str) -> str:
        counter["n"] += 1
        return f"{prefix}-{counter['n']}"

    def vertex(cid: str, value: str, style: str, box: Box, parent: str = "1") -> None:
        # `value` arrives as HTML (inner text already HTML-escaped). It lands in
        # an XML attribute, so the markup itself gets escaped once more here —
        # draw.io unescapes the attribute, then renders what's left as HTML.
        px, py = (box.x, box.y)
        if parent != "1":
            px, py = box.x - parent_origin[parent][0], box.y - parent_origin[parent][1]
        out.append(
            f'        <mxCell id="{cid}" value="{esc(value)}" style="{style}" vertex="1" parent="{parent}">\n'
            f'          <mxGeometry x="{px:g}" y="{py:g}" width="{box.w:g}" height="{box.h:g}" as="geometry"/>\n'
            f"        </mxCell>"
        )

    parent_origin: dict[str, tuple[float, float]] = {}

    # Every shape a connector may terminate on, as (cell id, absolute box).
    # Nodes, badges and chips all qualify — sequence messages end on activation
    # bars, which are badges or chips, never nodes. Bands are left out on
    # purpose: a lane's boundary runs the width of the canvas, and an arrow
    # crossing lanes would glue itself to furniture instead of a shape.
    attachables: list[tuple[str, Box]] = []

    def text_cell(label: Label, parent: str = "1") -> None:
        """One positioned text as its own cell. Standalone captions and the
        titles of container frames both land here: folding a frame's texts into
        a centred cell label would move them to the middle of the frame, while
        a text child keeps the source position and still travels with the frame
        when it is dragged."""
        cid = cell_id("text")
        style = label.style
        width = estimate_width(label.text, style, variables)
        size = style.font_size or 8.0
        anchor = style.anchor or "start"
        if anchor == "middle":
            x, align = label.x - width / 2, "center"
        elif anchor == "end":
            x, align = label.x - width, "right"
        else:
            x, align = label.x, "left"
        box = Box(x=x, y=label.y - size * 1.15, w=width, h=size * 1.7)
        bits = font_style_bits(style, variables, sheet)
        text_style = f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;spacing=0;"
        if bits:
            text_style += bits + ";"
        if style.letter_spacing:
            value = (
                f'<span style="letter-spacing:{style.letter_spacing}">{esc(label.text)}</span>'
            )
            deltas.append(
                f"letter-spacing {style.letter_spacing} on '{label.text}' emitted as inline CSS "
                "(not a draw.io style key — verify it renders)"
            )
        else:
            value = esc(label.text)
        vertex(cid, value, text_style, box, parent=parent)

    # --- lane bands ------------------------------------------------------
    for band in scene.bands:
        style = (
            f"{shape_prefix(band)}html=1;{paint('fill', band.fill, variables=variables)};strokeColor=none;"
            f"{opacity_bits(band.opacity)}movable=0;resizable=0;"
        )
        vertex(cell_id("band"), "", style, band)

    # --- hairline rules --------------------------------------------------
    for rule in scene.rules:
        (x1, y1), (x2, y2) = rule.points[0], rule.points[-1]
        cid = cell_id("rule")
        style = (
            f"endArrow=none;html=1;{paint('stroke', rule.stroke, '#000000', variables)};"
            f"strokeWidth={rule.stroke_width or 1};"
            f"{dash_bits(rule.dash)}{opacity_bits(rule.opacity)}"
        )
        out.append(
            f'        <mxCell id="{cid}" style="{style}" edge="1" parent="1">\n'
            f'          <mxGeometry relative="1" as="geometry">\n'
            f'            <mxPoint x="{x1:g}" y="{y1:g}" as="sourcePoint"/>\n'
            f'            <mxPoint x="{x2:g}" y="{y2:g}" as="targetPoint"/>\n'
            f"          </mxGeometry>\n"
            f"        </mxCell>"
        )

    # --- node cards ------------------------------------------------------
    # Parents first: a nested cell's geometry is relative to its parent, so the
    # parent's origin must be on file before any child is written. Sorting by
    # nesting depth is enough — a parent always encloses its children, so it is
    # always shallower — and the sort is stable, so document (paint) order
    # survives among siblings.
    def nesting(index: int) -> int:
        depth, parent = 0, scene.nodes[index].parent_index
        while parent is not None:
            depth, parent = depth + 1, scene.nodes[parent].parent_index
        return depth

    node_ids: list[str] = [""] * len(scene.nodes)
    for index in sorted(range(len(scene.nodes)), key=nesting):
        node = scene.nodes[index]
        cid = cell_id("node")
        node_ids[index] = cid
        parent_origin[cid] = (node.box.x, node.box.y)
        attachables.append((cid, node.box))
        parent = node_ids[node.parent_index] if node.parent_index is not None else "1"
        box = node.box
        style = (
            f"{shape_prefix(box)}whiteSpace=wrap;html=1;"
            f"{paint('fill', box.fill, variables=variables)};"
            f"{paint('stroke', box.stroke, variables=variables)};"
            f"strokeWidth={box.stroke_width or 1};verticalAlign=middle;align=center;"
            f"{dash_bits(box.dash)}{opacity_bits(box.opacity)}"
        )
        if node.container:
            # A frame enclosing other cards is a container cell, and its texts
            # stay where the source drew them. Folded into the cell label they
            # would render centred over the nested cards — a zone title
            # migrating to the middle of the zone.
            vertex(cid, "", style + "container=1;collapsible=0;", box, parent=parent)
            for label in node.labels:
                text_cell(label, parent=cid)
        else:
            vertex(cid, node_label(node, variables), style, box, parent=parent)

        for child in node.children:
            child_id = cell_id("badge")
            attachables.append((child_id, child))
            texts = [lbl for lbl in node.child_labels if child.contains(lbl.x, lbl.y)]
            value = esc(texts[0].text) if texts else ""
            bits = font_style_bits(texts[0].style, variables, sheet) if texts else ""
            child_style = furniture_style(child, variables)
            if bits:
                child_style += bits + ";"
            vertex(child_id, value, child_style, child, parent=cid)

    # --- free-floating boxes (step chips, legend swatches) ---------------
    for box in scene.loose_boxes:
        cid = cell_id("chip")
        attachables.append((cid, box))
        inside = [lbl for lbl in scene.loose_labels if box.contains(lbl.x, lbl.y)]
        value = esc(inside[0].text) if inside else ""
        bits = font_style_bits(inside[0].style, variables, sheet) if inside else ""
        for lbl in inside:
            scene.loose_labels.remove(lbl)
        style = furniture_style(box, variables)
        if bits:
            style += bits + ";"
        vertex(cid, value, style, box)

    # --- edges -----------------------------------------------------------
    annotations = edge_annotations(scene.edges, scene.loose_labels, scene.masks)
    consumed_labels: list[Label] = []
    trunk_endpoints = 0
    for edge_index, connector in enumerate(scene.edges):
        cid = cell_id("edge")
        start = edge_endpoint(connector.points[0], attachables)
        end = edge_endpoint(connector.points[-1], attachables)
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;"
            f"{paint('stroke', connector.stroke, '#000000', variables)};"
            f"strokeWidth={connector.stroke_width or 1};"
            "endArrow=blockThin;endFill=1;endSize=6;"
        )
        style += dash_bits(connector.dash) + opacity_bits(connector.opacity)
        if not connector.arrow:
            style = style.replace("endArrow=blockThin;endFill=1;endSize=6;", "endArrow=none;")
        if start:
            style += f"exitX={start[1]:g};exitY={start[2]:g};exitDx=0;exitDy=0;"
        if end:
            style += f"entryX={end[1]:g};entryY={end[2]:g};entryDx=0;entryDy=0;"

        owned = annotations.get(edge_index, [])
        value = ""
        if owned:
            # Two masks along one connector are two lines of the same label —
            # the edge has one value, and html=1 makes <br> a line break.
            value = "<br>".join(esc(label.text) for label in owned)
            consumed_labels.extend(owned)
            # The mask's own fill is the label background: over a tinted lane
            # the mask is painted the lane's tone, and the page colour would
            # sit on it like a paler sticker.
            lead = owned[0]
            mask = next((m for m in scene.masks if m.contains(lead.x, lead.y)), None)
            backing = color(mask.fill, scene.background, variables) if mask else scene.background
            style += f"labelBackgroundColor={backing};"
            bits = font_style_bits(lead.style, variables, sheet)
            if bits:
                style += bits + ";"

        attrs = [f'id="{cid}"', f'value="{esc(value)}"', f'style="{style}"', 'edge="1"', 'parent="1"']
        if start:
            attrs.append(f'source="{start[0]}"')
        if end:
            attrs.append(f'target="{end[0]}"')
        out.append(f"        <mxCell {' '.join(attrs)}>")
        out.append('          <mxGeometry relative="1" as="geometry">')
        for terminal, endpoint, which in (
            (start, connector.points[0], "sourcePoint"),
            (end, connector.points[-1], "targetPoint"),
        ):
            if terminal:
                continue
            x, y = endpoint
            out.append(f'            <mxPoint x="{x:g}" y="{y:g}" as="{which}"/>')
            # An unbound endpoint sitting on another connector's path is a
            # junction — half an org chart's branches fork off a shared trunk.
            # It stays a fixed coordinate: binding edge-to-edge would let the
            # router pick the attachment point and dissolve the trunk shape.
            if any(
                other is not connector
                and any(
                    point_to_segment(x, y, *other.points[i], *other.points[i + 1]) <= ATTACH_TOLERANCE
                    for i in range(len(other.points) - 1)
                )
                for other in scene.edges
            ):
                trunk_endpoints += 1
        # Interior bends are the drawn route. jgraph's XML reference steers
        # AI-authored diagrams away from waypoints, but that advice is for
        # diagrams with no intended geometry — here the source geometry IS the
        # spec, and without the waypoints draw.io's router replaces the route
        # (a sequence self-message collapses from a loop to a stub).
        if len(connector.points) > 2:
            out.append('            <Array as="points">')
            for x, y in connector.points[1:-1]:
                out.append(f'              <mxPoint x="{x:g}" y="{y:g}"/>')
            out.append("            </Array>")
        out.append("          </mxGeometry>")
        out.append("        </mxCell>")

    for label in consumed_labels:
        if label in scene.loose_labels:
            scene.loose_labels.remove(label)

    # --- remaining standalone text --------------------------------------
    for label in scene.loose_labels:
        text_cell(label)

    if trunk_endpoints:
        deltas.append(
            f"{trunk_endpoints} connector endpoint(s) rest on another connector's path, not on a "
            "shape — kept as fixed coordinates (an edge-to-edge binding would hand the junction "
            "to the router)"
        )
    if scene.coincident_dropped:
        deltas.append(
            f"{scene.coincident_dropped} coincident node underlay(s) merged — draw.io has one cell per shape"
        )
    if scene.texture_dropped:
        deltas.append(
            f"{scene.texture_dropped} full-canvas texture rect(s) dropped — a draw.io page "
            "has a background colour, not a background pattern"
        )
    if scene.masks:
        # The ledger reports what happened, not what usually happens: a mask
        # whose text found no connector did NOT become a labelBackgroundColor,
        # it became a plain text cell with no backing at all.
        used = sum(
            1
            for mask in scene.masks
            if any(mask.contains(label.x, label.y) for label in consumed_labels)
        )
        if used == len(scene.masks):
            deltas.append(
                f"{len(scene.masks)} label mask rect(s) dropped — replaced by labelBackgroundColor"
            )
        else:
            deltas.append(
                f"{len(scene.masks)} label mask rect(s) dropped — {used} replaced by "
                f"labelBackgroundColor, {len(scene.masks) - used} had no connector to own "
                "their text, which stays a plain text cell with no background"
            )
    if scene.occluded_masks:
        listing = ", ".join(f"'{text}'" for text in scene.occluded_texts) or "(no text)"
        deltas.append(
            f"{len(scene.occluded_masks)} label mask(s) buried under a later-painted opaque "
            f"card dropped with their text ({listing}) — the browser never shows them, and an "
            "export must not resurface what the source render hides"
        )
    if scene.motion_items:
        deltas.append(
            f"{scene.motion_items} animation step group(s) flattened — draw.io has no "
            "timeline, so every step's shapes are emitted simultaneously visible"
        )
    if scene.description:
        deltas.append(
            "SVG <desc> accessibility summary dropped — an mxGraphModel has no description slot"
        )
    if scene.icons_dropped:
        listing = ", ".join(
            f"#{ref} ×{count}" for ref, count in sorted(scene.icons_dropped.items())
        )
        deltas.append(
            f"{sum(scene.icons_dropped.values())} <use> icon instance(s) dropped ({listing}) — "
            "draw.io has no symbol instancing, and a 24px glyph decomposed into cells is noise"
        )

    body = "\n".join(out)
    xml = (
        "<mxfile host=\"automation-design\">\n"
        f'  <diagram id="{esc(name)}" name="{esc(scene.title or name)}">\n'
        f'    <mxGraphModel dx="{scene.width:g}" dy="{scene.height:g}" grid="1" gridSize="10" '
        f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{scene.width:g}" pageHeight="{scene.height:g}" math="0" shadow="0" '
        f'background="{scene.background}" adaptiveColors="auto">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f"{body}\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )
    return xml, deltas


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="diagram HTML with inline SVG")
    parser.add_argument("--out", type=Path, help="output .drawio path")
    parser.add_argument("--report", action="store_true", help="print the delta ledger")
    args = parser.parse_args()

    if not args.source.is_file():
        fail(f"{args.source}: not a file")
    source = args.source.read_text(encoding="utf-8")

    match = re.search(r"<svg\b.*?</svg>", source, re.S)
    if not match:
        fail(f"{args.source}: no <svg> block")

    stylesheet, variables = parse_css(source)
    reject_unsafe_xml(match.group(0), str(args.source))
    try:
        svg = ET.fromstring(quote_boolean_attributes(match.group(0)))
    except ET.ParseError as exc:
        fail(f"{args.source}: inline SVG is not well-formed XML ({exc})")

    scene = build_scene(svg, stylesheet, variables)
    font_link = FONT_LINK_RE.search(source)
    xml, deltas = emit(scene, variables, args.source.stem, font_link.group(1) if font_link else "")

    out = args.out or args.source.with_suffix(".drawio")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8")

    print(f"{out}  ({out.stat().st_size:,} bytes)")
    print(
        f"  {len(scene.nodes)} nodes · {len(scene.edges)} edges · {len(scene.bands)} bands · "
        f"{len(scene.rules)} rules · {len(scene.loose_boxes)} chips · {len(scene.loose_labels)} text"
    )
    if args.report and deltas:
        print("\n  delta ledger:")
        seen: set[str] = set()
        for item in deltas:
            if item not in seen:
                print(f"    - {item}")
                seen.add(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
