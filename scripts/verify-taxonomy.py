#!/usr/bin/env python3
"""Verify the machine-readable automation-design taxonomy and its projections."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills/automation-design"
TAXONOMY = SKILL_DIR / "taxonomy.json"
SKILL = SKILL_DIR / "SKILL.md"
SEMANTIC_PATTERNS = SKILL_DIR / "references/semantic-patterns.md"
AUTOMATION_PRIMITIVES = SKILL_DIR / "references/automation-primitives.md"
GALLERY = SKILL_DIR / "assets/index.html"
README = ROOT / "README.md"
ID = re.compile(r"^[a-z][a-z0-9-]*$")
TAG = re.compile(r"^[A-Z][A-Z0-9 ]*$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"could not read {path}: {exc}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path} must contain a JSON object")
        return None
    return payload


def _catalog(
    payload: dict[str, Any], key: str, required: tuple[str, ...], errors: list[str]
) -> list[dict[str, Any]]:
    raw = payload.get(key)
    if not isinstance(raw, list) or not raw:
        errors.append(f"taxonomy {key!r} must be a non-empty array")
        return []
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw):
        label = f"{key}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or ID.fullmatch(entry_id) is None:
            errors.append(f"{label}.id must be a stable kebab-case identifier")
        elif entry_id in seen:
            errors.append(f"taxonomy {key!r} has duplicate id {entry_id!r}")
        else:
            seen.add(entry_id)
        for field in required:
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        entries.append(entry)
    return entries


def _check_aliases(
    catalog_name: str, entries: list[dict[str, Any]], errors: list[str]
) -> None:
    owners: dict[str, str] = {}
    for entry in entries:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str):
            continue
        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list) or not all(
            isinstance(alias, str) and alias.strip() for alias in aliases
        ):
            errors.append(f"{catalog_name} {entry_id!r} aliases must be non-empty strings")
            continue
        terms = [entry_id, entry.get("label", ""), *aliases]
        for term in terms:
            normalized = re.sub(r"\s+", " ", str(term).casefold()).strip()
            previous = owners.get(normalized)
            if previous is not None and previous != entry_id:
                errors.append(
                    f"{catalog_name} routing term {term!r} is ambiguous between "
                    f"{previous!r} and {entry_id!r}"
                )
            owners[normalized] = entry_id


def _section(source: str, start: str, end: str | None = None) -> str:
    start_index = source.find(start)
    if start_index < 0:
        return ""
    if end is None:
        return source[start_index:]
    end_index = source.find(end, start_index + len(start))
    return source[start_index:] if end_index < 0 else source[start_index:end_index]


def _visual_guide(source: str) -> list[tuple[str, str]]:
    section = _section(source, "### Visual-type guide", "Rules of thumb")
    return [
        (label.strip(), reference.strip())
        for label, reference in re.findall(
            r"^\|[^|]*\|\s*\*\*([^*]+)\*\*\s*\|\s*\[[^]]+\]\((references/[^)#]+)(?:#[^)]*)?\)\s*\|",
            section,
            re.MULTILINE,
        )
    ]


def _pattern_routing(source: str, skill: bool = False) -> list[tuple[str, str]]:
    if skill:
        section = _section(source, "| Behavioral trigger", "The pattern owns")
        expression = (
            r"^\|[^|]*\|\s*\*\*([^*]+)\*\*\s*→\s*([^|]+?)\s*\|$"
        )
    else:
        section = _section(source, "## Routing table", "## 1.")
        expression = (
            r"^\|[^|]*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+?)\s*\|$"
        )
    return [
        (label.strip(), visual.strip())
        for label, visual in re.findall(
            expression,
            section,
            re.MULTILINE,
        )
    ]


def _pattern_headings(source: str) -> list[str]:
    return [
        label.strip()
        for label in re.findall(r"^##\s+\d+\.\s+(.+?)\s*$", source, re.MULTILINE)
    ]


def _gallery_visual_types(source: str) -> list[tuple[str, str]]:
    section = _section(source, 'data-group="Visual types"', "</section>")
    return [
        (slug, re.sub(r"<[^>]+>", "", label).strip())
        for slug, label in re.findall(
            r'<button\s+class="example-option"\s+data-type="([^"]+)"[^>]*>.*?'
            r'<span\s+class="option-name">(.*?)</span>',
            section,
            re.DOTALL,
        )
    ]


def _activity_tag_mappings(source: str) -> list[tuple[str, str, str]]:
    section = _section(source, "## Activity tags", "## Badge convention")
    return [
        (tag.strip(), kind.strip(), behavior.strip())
        for tag, kind, behavior in re.findall(
            r"^\|\s*`([^`]+)`\s*\|[^|]*\|\s*`kind\.([^`]+)`\s*·\s*"
            r"`behavior\.([^`]+)`\s*\|$",
            section,
            re.MULTILINE,
        )
    ]


def _stable_id_table(
    source: str,
    heading: str,
    next_heading: str,
    prefix: str,
) -> list[str]:
    section = _section(source, heading, next_heading)
    return re.findall(
        rf"^\|\s*`{re.escape(prefix)}\.([a-z][a-z0-9-]*)`\s*\|",
        section,
        re.MULTILINE,
    )


def _check_declared_counts(
    root: Path,
    visual_count: int,
    pattern_count: int,
    automation_pattern_count: int,
    errors: list[str],
) -> None:
    paths = (
        root / "README.md",
        root / "CONTRIBUTING.md",
        root / "skills/automation-design/SKILL.md",
        root / "skills/automation-design/references/import-drawio.md",
        root / "skills/automation-design/references/import-mermaid.md",
        root / "skills/automation-design/references/semantic-patterns.md",
    )
    for path in paths:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        for raw in re.findall(r"\b(\d+)(?:-type|\s+(?:visual\s+)?types)\b", source, re.IGNORECASE):
            if int(raw) != visual_count:
                errors.append(
                    f"{path.relative_to(root)} declares {raw} visual types; "
                    f"taxonomy contains {visual_count}"
                )
        for raw in re.findall(r"\b(\d+)\s+(?:semantic|routed) patterns\b", source, re.IGNORECASE):
            if int(raw) != pattern_count:
                errors.append(
                    f"{path.relative_to(root)} declares {raw} semantic patterns; "
                    f"taxonomy contains {pattern_count}"
                )
        automation_declarations = re.findall(
            r"\b(\d+)\s+(?:automation patterns|of them automation-specific)\b",
            source,
            re.IGNORECASE,
        )
        for raw in automation_declarations:
            if int(raw) != automation_pattern_count:
                errors.append(
                    f"{path.relative_to(root)} declares {raw} automation patterns; "
                    f"taxonomy contains {automation_pattern_count}"
                )


def verify_taxonomy(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    skill_dir = root / "skills/automation-design"
    payload = _load_json(skill_dir / "taxonomy.json", errors)
    if payload is None:
        return errors
    taxonomy_version = payload.get("taxonomy_version")
    if not isinstance(taxonomy_version, str) or SEMVER.fullmatch(taxonomy_version) is None:
        errors.append("taxonomy_version must be a semantic version (MAJOR.MINOR.PATCH)")

    visuals = _catalog(
        payload,
        "visual_types",
        ("label", "reference", "gallery_slug"),
        errors,
    )
    patterns = _catalog(
        payload,
        "semantic_patterns",
        ("label", "category", "nearest_visual_type"),
        errors,
    )
    kinds = _catalog(payload, "node_kinds", ("label", "description"), errors)
    behaviors = _catalog(payload, "behavior_classes", ("label", "description"), errors)
    tags = _catalog(
        payload,
        "activity_tags",
        ("tag", "kind", "behavior", "description"),
        errors,
    )
    _check_aliases("visual_types", visuals, errors)
    _check_aliases("semantic_patterns", patterns, errors)

    visual_ids = {entry.get("id") for entry in visuals if isinstance(entry.get("id"), str)}
    visual_labels = {
        entry.get("id"): entry.get("label")
        for entry in visuals
        if isinstance(entry.get("id"), str) and isinstance(entry.get("label"), str)
    }
    gallery_slugs: set[str] = set()
    for entry in visuals:
        reference = entry.get("reference")
        if isinstance(reference, str) and not (skill_dir / reference).is_file():
            errors.append(f"visual type {entry.get('id')!r} references missing {reference!r}")
        slug = entry.get("gallery_slug")
        if isinstance(slug, str):
            if slug in gallery_slugs:
                errors.append(f"visual types have duplicate gallery_slug {slug!r}")
            gallery_slugs.add(slug)
            if not (skill_dir / "assets" / f"example-{slug}.html").is_file():
                errors.append(f"visual type {entry.get('id')!r} has no example-{slug}.html")

    for entry in patterns:
        nearest = entry.get("nearest_visual_type")
        if isinstance(nearest, str) and nearest not in visual_ids:
            errors.append(
                f"semantic pattern {entry.get('id')!r} references unknown visual type {nearest!r}"
            )
        if entry.get("category") not in {"general", "automation"}:
            errors.append(
                f"semantic pattern {entry.get('id')!r} category must be general or automation"
            )

    kind_ids = {entry.get("id") for entry in kinds if isinstance(entry.get("id"), str)}
    behavior_ids = {
        entry.get("id") for entry in behaviors if isinstance(entry.get("id"), str)
    }
    seen_tags: set[str] = set()
    for entry in tags:
        value = entry.get("tag")
        if not isinstance(value, str) or TAG.fullmatch(value) is None:
            errors.append(f"activity tag {entry.get('id')!r} must be uppercase words")
        elif value in seen_tags:
            errors.append(f"activity_tags has duplicate tag {value!r}")
        else:
            seen_tags.add(value)
        kind = entry.get("kind")
        if isinstance(kind, str) and kind not in kind_ids:
            errors.append(
                f"activity tag {entry.get('id')!r} references unknown kind {kind!r}"
            )
        behavior = entry.get("behavior")
        if isinstance(behavior, str) and behavior not in behavior_ids:
            errors.append(
                f"activity tag {entry.get('id')!r} references unknown behavior "
                f"{behavior!r}"
            )

    expected_visual_guide = [
        (str(entry.get("label")), str(entry.get("reference"))) for entry in visuals
    ]
    skill_source = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    actual_visual_guide = _visual_guide(skill_source)
    if actual_visual_guide != expected_visual_guide:
        errors.append("SKILL.md visual-type guide does not match taxonomy visual_types")

    expected_routing = [
        (
            str(entry.get("label")),
            str(
                visual_labels.get(entry.get("nearest_visual_type"))
                if isinstance(entry.get("nearest_visual_type"), str)
                else None
            ),
        )
        for entry in patterns
    ]
    if _pattern_routing(skill_source, skill=True) != expected_routing:
        errors.append("SKILL.md semantic routing table does not match taxonomy")

    semantic_source = (skill_dir / "references/semantic-patterns.md").read_text(
        encoding="utf-8"
    )
    if _pattern_routing(semantic_source) != expected_routing:
        errors.append("semantic-patterns.md routing table does not match taxonomy")
    expected_pattern_labels = [str(entry.get("label")) for entry in patterns]
    if _pattern_headings(semantic_source) != expected_pattern_labels:
        errors.append("semantic-patterns.md numbered headings do not match taxonomy")

    gallery_source = (skill_dir / "assets/index.html").read_text(encoding="utf-8")
    expected_gallery = [
        (str(entry.get("gallery_slug")), str(entry.get("label"))) for entry in visuals
    ]
    if dict(_gallery_visual_types(gallery_source)) != dict(expected_gallery):
        errors.append("gallery Visual types group does not match taxonomy")

    primitives_source = (skill_dir / "references/automation-primitives.md").read_text(
        encoding="utf-8"
    )
    expected_kinds = [str(entry.get("id")) for entry in kinds]
    expected_behaviors = [str(entry.get("id")) for entry in behaviors]
    actual_kinds = _stable_id_table(
        primitives_source,
        "| Stable kind ID | Meaning |",
        "| Stable behavior ID | Meaning |",
        "kind",
    )
    actual_behaviors = _stable_id_table(
        primitives_source,
        "| Stable behavior ID | Meaning |",
        "Do not infer kind",
        "behavior",
    )
    if actual_kinds != expected_kinds:
        errors.append("automation-primitives.md stable-kind table does not match taxonomy")
    if actual_behaviors != expected_behaviors:
        errors.append("automation-primitives.md stable-behavior table does not match taxonomy")
    expected_tag_mappings = [
        (
            str(entry.get("tag")),
            str(entry.get("kind")),
            str(entry.get("behavior")),
        )
        for entry in tags
    ]
    if _activity_tag_mappings(primitives_source) != expected_tag_mappings:
        errors.append(
            "automation-primitives.md activity-tag mappings do not match taxonomy"
        )

    automation_pattern_count = sum(
        1 for entry in patterns if entry.get("category") == "automation"
    )
    _check_declared_counts(
        root,
        len(visuals),
        len(patterns),
        automation_pattern_count,
        errors,
    )
    return errors


def main() -> int:
    errors = verify_taxonomy(ROOT)
    if errors:
        print("FAIL taxonomy")
        for error in errors:
            print(f"  - {error}")
        return 1
    payload = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    print(
        "OK taxonomy: "
        f"{len(payload['visual_types'])} visual types, "
        f"{len(payload['semantic_patterns'])} semantic patterns, "
        f"{len(payload['node_kinds'])} node kinds, "
        f"{len(payload['behavior_classes'])} behavior classes, "
        f"{len(payload['activity_tags'])} activity tags"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
