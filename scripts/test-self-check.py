#!/usr/bin/env python3
"""Adversarial tests for the packaged skill self-check (self_check.py)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF_CHECK = ROOT / "skills/automation-design/scripts/self_check.py"
ASSET_DIR = ROOT / "skills/automation-design/assets"
TEMPLATE = ASSET_DIR / "template-motion.html"
EXAMPLE = ASSET_DIR / "example-policy-trace-animated.html"
STATIC_EXAMPLE = ASSET_DIR / "example-architecture.html"


def load_self_check():
    spec = importlib.util.spec_from_file_location("self_check", SELF_CHECK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_self_check()
    failures: list[str] = []

    def check_pass(label: str, path: Path) -> None:
        errors = module.verify(path)
        if errors:
            failures.append(f"{label}: expected pass, got {errors}")
        else:
            print(f"OK: {label} passes")

    def check_fail(label: str, source: str, needle: str) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            candidate = Path(scratch) / "candidate.html"
            candidate.write_text(source, encoding="utf-8")
            errors = module.verify(candidate)
        if not any(needle in error for error in errors):
            failures.append(f"{label}: expected an error containing {needle!r}, got {errors}")
        else:
            print(f"OK: {label} rejected")

    check_pass("shipped template", TEMPLATE)
    check_pass("shipped animated example", EXAMPLE)
    check_pass("shipped static example", STATIC_EXAMPLE)

    static = STATIC_EXAMPLE.read_text(encoding="utf-8")
    animated = EXAMPLE.read_text(encoding="utf-8")

    check_fail(
        "executable attribute",
        static.replace("<body>", '<body onload="fetch(1)">', 1),
        "executable attribute",
    )
    check_fail(
        "remote image",
        static.replace("<body>", '<body><img src="https://tracker.example/p.gif">', 1),
        "remote reference",
    )
    check_fail(
        "lookalike fonts host",
        static.replace(
            "https://fonts.googleapis.com/css2",
            "https://fonts.googleapis.com.evil.tld/css2",
            1,
        ),
        "approved Google Fonts",
    )
    check_fail(
        "javascript URL",
        static.replace("<body>", '<body><a href="javascript:alert(1)">x</a>', 1),
        "executable URL",
    )
    check_fail(
        "data html URL",
        static.replace("<body>", '<body><a href="data:text/html,x">x</a>', 1),
        "executable URL",
    )
    check_fail(
        "iframe injection",
        static.replace("<body>", "<body><iframe></iframe>", 1),
        "not allowed",
    )
    check_fail(
        "arbitrary script",
        static.replace("</body>", "<script>alert(1)</script></body>", 1),
        "canonical data-diagram-controls attribute",
    )
    check_fail(
        "missing svg role",
        static.replace('role="img"', 'role="presentation"', 1),
        "role=img",
    )
    check_fail(
        "modified controller",
        animated.replace("'motion-ready'", "'motion-ready' /* patched */", 1),
        "exactly match the controller",
    )
    check_fail(
        "second script",
        animated.replace("</body>", "<script data-x></script></body>", 1),
        "at most one script",
    )
    check_fail(
        "hidden motion item",
        animated.replace(
            '<g data-motion-item data-step="1"',
            '<g style="opacity:0" data-motion-item data-step="1"',
            1,
        ),
        "hidden in source",
    )
    check_fail(
        "missing noscript",
        animated.replace("<noscript>", "<div>", 1).replace("</noscript>", "</div>", 1),
        "<noscript>",
    )
    check_fail(
        "non-decimal step count",
        animated.replace('data-step-count="5"', 'data-step-count="٥"', 1),
        "ASCII decimal",
    )

    # ---- set-scoped link verification (--set mode) ----

    def minimal_page(slug: str, body_svg: str, footer: str = "") -> str:
        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
            f"<title>{slug}</title>\n</head>\n<body>\n"
            f"<svg viewBox=\"0 0 96 48\" xmlns=\"http://www.w3.org/2000/svg\" role=\"img\" "
            f"aria-labelledby=\"{slug}-title {slug}-desc\">\n"
            f"<title id=\"{slug}-title\">{slug}</title>\n"
            f"<desc id=\"{slug}-desc\">Test fixture page.</desc>\n"
            f"{body_svg}\n</svg>\n{footer}\n</body>\n</html>\n"
        )

    def check_set(label: str, files: dict[str, str], overview: str, needle: str | None) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name, source in files.items():
                (root / name).write_text(source, encoding="utf-8")
            errors = module.verify_set(root / overview)
        if needle is None:
            if errors:
                failures.append(f"{label}: expected clean set, got {errors}")
            else:
                print(f"OK: {label} passes")
        elif not any(needle in error for error in errors):
            failures.append(f"{label}: expected an error containing {needle!r}, got {errors}")
        else:
            print(f"OK: {label} rejected")

    check_set(
        "valid linked set",
        {
            "mini-overview.html": minimal_page(
                "ov",
                '<a href="mini-p2-catch.html"><rect width="96" height="48" id="ov-n1"/></a>',
            ),
            "mini-p2-catch.html": minimal_page(
                "p2",
                '<a href="mini-p2.2.1-readsheet.html#p21-start"><rect width="96" height="48"/></a>',
                '<footer><a href="mini-overview.html">parent</a></footer>',
            ),
            "mini-p2.2.1-readsheet.html": minimal_page(
                "p21",
                '<rect id="p21-start" width="96" height="48"/>',
                '<footer><a href="mini-p2-catch.html">parent</a></footer>',
            ),
        },
        "mini-overview.html",
        None,
    )
    check_set(
        "missing link target",
        {
            "mini-overview.html": minimal_page(
                "ov", '<a href="mini-p9-ghost.html"><rect width="96" height="48"/></a>'
            ),
        },
        "mini-overview.html",
        "does not exist",
    )
    check_set(
        "missing fragment",
        {
            "mini-overview.html": minimal_page(
                "ov", '<a href="mini-p2-catch.html#no-such-id"><rect width="96" height="48"/></a>'
            ),
            "mini-p2-catch.html": minimal_page("p2", '<rect width="96" height="48"/>'),
        },
        "mini-overview.html",
        "fragment",
    )
    check_set(
        "duplicate canonical number",
        {
            "mini-overview.html": minimal_page(
                "ov",
                '<a href="mini-p2-catch.html"><rect width="96" height="48"/></a>'
                '<a href="mini-p2-other.html"><rect y="0" width="96" height="48"/></a>',
            ),
            "mini-p2-catch.html": minimal_page("p2", '<rect width="96" height="48"/>'),
            "mini-p2-other.html": minimal_page("p2b", '<rect width="96" height="48"/>'),
        },
        "mini-overview.html",
        "canonical number",
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("All self-check tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
