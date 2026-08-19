#!/usr/bin/env python3
"""Regression tests for the draw.io emitter (mxgraph_emit.py).

Every case here was a real bug found during development or by the multi-agent
audit, so every case is a regression waiting to come back. Each test builds a
minimal HTML document exhibiting one source pattern, emits it, and asserts on
the mxGraphModel — not on the emitter's internals — so a rewrite of the
classification stays free to change how it decides as long as what it decides
survives.
"""

from __future__ import annotations

import glob
import importlib.util
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
EMITTER = ROOT / "scripts/mxgraph_emit.py"
if not EMITTER.exists():
    EMITTER = ROOT / "skills/automation-design/scripts/mxgraph_emit.py"
ASSET_DIR = ROOT / "skills/automation-design/assets"


def load_emitter():
    spec = importlib.util.spec_from_file_location("mxgraph_emit", EMITTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass field resolution looks the module up in sys.modules on 3.14.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SVG_HEAD = (
    '<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" role="img" '
    'aria-labelledby="t-title t-desc">'
    '<title id="t-title">T</title><desc id="t-desc">T.</desc>'
)


def document(body: str, css: str = "") -> str:
    return (
        f"<!DOCTYPE html><html><head><style>{css}</style></head>"
        f"<body>{SVG_HEAD}{body}</svg></body></html>"
    )


def emit(module, source: str) -> ET.Element:
    """Run the emitter on an in-memory document, return the parsed mxfile root."""
    with tempfile.TemporaryDirectory() as scratch:
        candidate = Path(scratch) / "candidate.html"
        out = Path(scratch) / "candidate.drawio"
        candidate.write_text(source, encoding="utf-8")
        argv = sys.argv
        sys.argv = [str(EMITTER), str(candidate), "--out", str(out)]
        try:
            try:
                module.main()
            except SystemExit as stop:  # main() returns via SystemExit(0)
                if stop.code not in (0, None):
                    raise
        finally:
            sys.argv = argv
        return ET.parse(out).getroot()


def cells(root: ET.Element) -> list[ET.Element]:
    return [c for c in root.iter("mxCell") if c.get("id") not in ("0", "1")]


def styles(root: ET.Element) -> str:
    return ";".join(c.get("style") or "" for c in cells(root))


def main() -> int:
    module = load_emitter()
    failures: list[str] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"OK: {label}")
        else:
            failures.append(f"{label}{': ' + detail if detail else ''}")

    node = '<rect x="100" y="60" width="160" height="64" rx="6" fill="#fff" stroke="#333"/>'

    # A marker path inside <defs> must never become an edge; the audit's first
    # run turned three arrowheads into three phantom connectors.
    root = emit(module, document(
        '<defs><marker id="a"><path d="M0 0 L6 3 L0 6 Z" fill="#333"/></marker></defs>' + node
    ))
    check("defs subtree is skipped", not [c for c in cells(root) if c.get("edge")],
          "marker path leaked out of <defs> as an edge")

    # HTML labels live in an XML attribute: escaped exactly once, so the file
    # parses AND the markup survives one unescape (what draw.io does).
    root = emit(module, document(
        node.replace(">", "/>").replace("/>", ">", 1).replace(">", "/>", 1)
        + '<text x="180" y="92" font-size="9">a &amp; b</text>'
    ))
    labelled = [c for c in cells(root) if "a &amp; b" in (c.get("value") or "")]
    check("labels XML-escaped exactly once", bool(labelled),
          "text content lost or double-escaped")

    # A legend caption beside a sample arrow must not become the arrow's label:
    # only text sitting on a paper mask is an annotation.
    root = emit(module, document(
        '<rect width="400" height="200" fill="#f5f5f5"/>'
        '<line x1="40" y1="180" x2="64" y2="180" stroke="#333" marker-end="url(#a)"/>'
        '<text x="70" y="183" font-size="7">Robot handoff</text>'
    ))
    stolen = [c for c in cells(root) if c.get("edge") and "Robot handoff" in (c.get("value") or "")]
    check("legend caption not stolen by its sample arrow", not stolen)

    # An opaque underlay painted under a card must merge into one cell, not
    # ship as an unlabelled twin that separates on first drag.
    twin = '<rect x="100" y="60" width="160" height="64" rx="6" fill="#f5f5f5"/>'
    root = emit(module, document(twin + node))
    boxes = [c for c in cells(root)
             if c.get("vertex") and (c.find("mxGeometry") is not None)
             and c.find("mxGeometry").get("width") == "160"]
    check("coincident node rects collapse to one cell", len(boxes) == 1,
          f"got {len(boxes)} cells for one card")

    # Closed filled paths and circles are shapes, not connectors.
    root = emit(module, document(
        '<path d="M200 40 L240 70 L200 100 L160 70 Z" fill="#fff" stroke="#333"/>'
        '<circle cx="80" cy="80" r="12" fill="#fff" stroke="#333"/>'
    ))
    check("closed 4-point path becomes a rhombus", "rhombus" in styles(root))
    check("circle becomes an ellipse", "ellipse" in styles(root))
    check("shape paths spawn no edges", not [c for c in cells(root) if c.get("edge")])

    # A terminator pill is smaller than a card but stroked — a node, not a badge.
    root = emit(module, document(
        '<rect x="40" y="104" width="56" height="32" rx="16" fill="#fff" stroke="#333"/>'
        '<text x="68" y="124" font-size="9">Start</text>'
    ))
    pills = [c for c in cells(root) if "Start" in (c.get("value") or "")]
    check("stroked pill is a node and owns its label", bool(pills))

    # CSS lengths in rem must not take the file down (they did).
    root = emit(module, document(node, css=".eyebrow { font-size: 0.66rem; }"))
    check("rem lengths parse", bool(cells(root)))

    # Valueless HTML attributes are legal HTML5 and fatal XML.
    root = emit(module, document(f'<g data-motion-item aria-label="s">{node}</g>'))
    check("valueless attributes survive parsing", bool(cells(root)))

    # rgba maps to a separate opacity key rather than flattening to opaque.
    root = emit(module, document(
        '<rect x="100" y="60" width="160" height="64" fill="rgba(45,49,66,0.12)"/>'
    ))
    check("rgba keeps its alpha as fillOpacity", "fillOpacity=12" in styles(root))

    # The audit's biggest cascade: a percentage-sized canvas must be recognised,
    # hoisting the page colour and emitting no degenerate 0x0 cell.
    root = emit(module, document('<rect width="100%" height="100%" fill="#2d3142"/>' + node))
    model = root.find(".//mxGraphModel")
    check("percentage canvas sets the page background",
          model is not None and model.get("background") == "#2d3142")
    ghosts = [c for c in cells(root)
              if c.find("mxGeometry") is not None
              and c.find("mxGeometry").get("width") == "0"]
    check("no 0x0 ghost cells", not ghosts)

    # Class-styled shapes must take their paint from the stylesheet, including
    # descendant selectors, which the first CSS pass dropped entirely.
    root = emit(module, document(
        '<rect class="node" x="100" y="60" width="160" height="64"/>',
        css="svg .node { fill: #eb6c36; }",
    ))
    check("descendant-selector paint reaches shapes", "fillColor=#eb6c36" in styles(root))

    # var() tokens resolve to literals; draw.io has no CSS variables.
    root = emit(module, document(
        '<rect x="100" y="60" width="160" height="64" fill="var(--paper)"/>',
        css=":root { --paper: #f5f5f5; }",
    ))
    check("var() resolves before emission", "var(" not in styles(root))

    # Pill furniture centring: the empirically-measured combination. spacing=0
    # alone leaves ~4px lean and ~6px sag; the probe read dx=dy=-0.08 only with
    # wrap + spacing=0 + spacingLeft=0 + spacingRight=0.
    root = emit(module, document(
        node
        + '<rect x="108" y="68" width="18" height="10" rx="3" fill="#9c6b50"/>'
        + '<text x="117" y="74" font-size="6" fill="#fff">FL</text>'
    ))
    badge_styles = [c.get("style") or "" for c in cells(root) if "FL" in (c.get("value") or "")]
    check("pill furniture carries the centring combination",
          any("spacingLeft=0" in s and "spacingRight=0" in s and "whiteSpace=wrap" in s
              for s in badge_styles),
          f"styles: {badge_styles}")

    # Every shipped example must emit a well-formed mxGraphModel.
    shipped = sorted(glob.glob(str(ASSET_DIR / "example-*.html")))
    broken = []
    for path in shipped:
        try:
            root = emit(module, Path(path).read_text(encoding="utf-8"))
            if root.find(".//mxGraphModel") is None:
                broken.append(f"{Path(path).name}: no mxGraphModel")
        except Exception as exc:  # noqa: BLE001 — any failure is the finding
            broken.append(f"{Path(path).name}: {exc}")
    check(f"all {len(shipped)} shipped examples emit well-formed XML", not broken,
          "; ".join(broken[:5]))

    print()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("all mxgraph-emit tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
