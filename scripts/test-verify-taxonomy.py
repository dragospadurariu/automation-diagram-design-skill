#!/usr/bin/env python3
"""Adversarial regression tests for the taxonomy verification gate."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
VERIFY_SCRIPT = ROOT / "scripts/verify-taxonomy.py"


def load_module() -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("automation_design_taxonomy", VERIFY_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load verify-taxonomy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def seed(root: Path) -> dict:
    skill = root / "skills/automation-design"
    references = skill / "references"
    assets = skill / "assets"
    references.mkdir(parents=True)
    assets.mkdir(parents=True)
    payload = {
        "taxonomy_version": "1.0.0",
        "visual_types": [
            {
                "id": "architecture",
                "label": "Architecture",
                "reference": "references/type-architecture.md",
                "gallery_slug": "architecture",
                "aliases": ["topology"],
            }
        ],
        "semantic_patterns": [
            {
                "id": "agent-with-tools",
                "label": "Agent with tools",
                "category": "automation",
                "nearest_visual_type": "architecture",
                "aliases": ["tool using agent"],
            }
        ],
        "process_profiles": [
            {
                "id": "as-is",
                "label": "AS-IS",
                "description": "Observed current execution.",
            }
        ],
        "node_kinds": [
            {"id": "agent", "label": "Agent", "description": "Chooses actions."},
            {
                "id": "workflow",
                "label": "Workflow",
                "description": "Runs deterministic steps.",
            },
        ],
        "behavior_classes": [
            {
                "id": "agentic",
                "label": "Agentic",
                "description": "Reasons over a goal.",
            },
            {
                "id": "deterministic",
                "label": "Deterministic",
                "description": "Runs prescribed steps.",
            },
        ],
        "activity_tags": [
            {
                "id": "agent",
                "tag": "AGENT",
                "kind": "agent",
                "behavior": "agentic",
                "description": "Agent reasoning step.",
            }
        ],
    }
    write_json(skill / "taxonomy.json", payload)
    (references / "type-architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (assets / "example-architecture.html").write_text(
        "<!DOCTYPE html><title>Architecture</title>\n", encoding="utf-8"
    )
    (assets / "example-process-as-is.html").write_text(
        """<!DOCTYPE html><title>AS-IS</title>
<svg data-process-profile="as-is">
  <g data-profile-evidence>
    <text data-profile-field="status">DRAFT</text>
    <text data-profile-field="source">WALKTHROUGH</text>
    <text data-profile-field="scope">REQUEST TO OUTCOME</text>
    <text data-profile-field="measures" data-measure-state="unknown">UNKNOWN</text>
  </g>
  <g data-lane-axis="performer"></g>
  <rect data-node-kind="action" data-manual-handoff></rect>
  <polygon data-node-kind="decision"></polygon>
  <circle data-outcome="responded"></circle>
  <circle data-outcome="escalated"></circle>
</svg>
""",
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        """# Skill

| Behavioral trigger | Semantic pattern → nearest type |
|---|---|
| Agent selects a tool | **Agent with tools** → Architecture |

The pattern owns behavior.

### Visual-type guide (1)

| If you're showing… | Use | Reference |
|---|---|---|
| Components | **Architecture** | [Architecture](references/type-architecture.md) |

Rules of thumb:
""",
        encoding="utf-8",
    )
    (references / "semantic-patterns.md").write_text(
        """# Semantic patterns

## Routing table

| The reader must understand… | Semantic pattern | Nearest visual type |
|---|---|---|
| Tool selection | **Agent with tools** | Architecture |

## 1. Agent with tools
""",
        encoding="utf-8",
    )
    (references / "automation-primitives.md").write_text(
        """# Automation primitives

| Stable kind ID | Meaning |
|---|---|
| `kind.agent` | Chooses actions |
| `kind.workflow` | Runs deterministic steps |

| Stable behavior ID | Meaning |
|---|---|
| `behavior.agentic` | Reasons over a goal |
| `behavior.deterministic` | Runs prescribed steps |

Do not infer kind from implementation details.

## Activity tags

| Activity tag | Meaning | Default kind · behavior |
|---|---|---|
| `AGENT` | Agent reasoning | `kind.agent` · `behavior.agentic` |

## Badge convention
""",
        encoding="utf-8",
    )
    (references / "process-profiles.md").write_text(
        """# Process-state profiles

## Stable profiles

| Stable profile ID | Label | Meaning |
|---|---|---|
| `profile.as-is` | `AS-IS` | Observed current execution. |

## Input contract
""",
        encoding="utf-8",
    )
    (assets / "index.html").write_text(
        """<section class="catalog-group" data-group="Visual types">
<button class="example-option" data-type="architecture"><span class="option-name">Architecture</span></button>
</section>
""",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "1 visual types, 1 semantic patterns.\n", encoding="utf-8"
    )
    return payload


def expect_failure(label: str, errors: list[str], needle: str) -> None:
    if not any(needle in error for error in errors):
        raise AssertionError(f"{label}: expected {needle!r}, got {errors}")
    print(f"OK: {label} rejected")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="taxonomy-valid-") as scratch:
        root = Path(scratch)
        seed(root)
        errors = VERIFY.verify_taxonomy(root)
        if errors:
            raise AssertionError(f"valid taxonomy failed: {errors}")
        print("OK: valid taxonomy accepted")

    with tempfile.TemporaryDirectory(prefix="taxonomy-duplicate-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        duplicate = dict(payload["visual_types"][0])
        duplicate["gallery_slug"] = "architecture-copy"
        payload["visual_types"].append(duplicate)
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "duplicate stable ID",
            VERIFY.verify_taxonomy(root),
            "duplicate id 'architecture'",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-route-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        payload["semantic_patterns"][0]["nearest_visual_type"] = "missing"
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "unknown visual route",
            VERIFY.verify_taxonomy(root),
            "references unknown visual type 'missing'",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-behavior-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        payload["activity_tags"][0]["behavior"] = "missing"
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "unknown activity behavior",
            VERIFY.verify_taxonomy(root),
            "references unknown behavior 'missing'",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-docs-") as scratch:
        root = Path(scratch)
        seed(root)
        patterns = root / "skills/automation-design/references/semantic-patterns.md"
        patterns.write_text(
            patterns.read_text(encoding="utf-8").replace(
                "## 1. Agent with tools", "## 1. Different pattern"
            ),
            encoding="utf-8",
        )
        expect_failure(
            "documentation drift",
            VERIFY.verify_taxonomy(root),
            "numbered headings do not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-primitives-") as scratch:
        root = Path(scratch)
        seed(root)
        primitives = root / "skills/automation-design/references/automation-primitives.md"
        primitives.write_text(
            primitives.read_text(encoding="utf-8").replace(
                "| `kind.agent` | Chooses actions |",
                "| `kind.workflow` | Chooses actions |",
            ),
            encoding="utf-8",
        )
        expect_failure(
            "primitive ID drift",
            VERIFY.verify_taxonomy(root),
            "stable-kind table does not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-kind-row-") as scratch:
        root = Path(scratch)
        seed(root)
        primitives = root / "skills/automation-design/references/automation-primitives.md"
        primitives.write_text(
            primitives.read_text(encoding="utf-8").replace(
                "| `kind.agent` | Chooses actions |\n", ""
            ),
            encoding="utf-8",
        )
        expect_failure(
            "missing stable-kind row despite later ID mentions",
            VERIFY.verify_taxonomy(root),
            "stable-kind table does not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-tag-doc-map-") as scratch:
        root = Path(scratch)
        seed(root)
        primitives = root / "skills/automation-design/references/automation-primitives.md"
        primitives.write_text(
            primitives.read_text(encoding="utf-8").replace(
                "`kind.agent` · `behavior.agentic`",
                "`kind.agent` · `behavior.human`",
            ),
            encoding="utf-8",
        )
        expect_failure(
            "activity-tag documentation mapping drift",
            VERIFY.verify_taxonomy(root),
            "activity-tag mappings do not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-tag-json-map-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        payload["activity_tags"][0]["kind"] = "workflow"
        payload["activity_tags"][0]["behavior"] = "deterministic"
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "activity-tag taxonomy mapping drift",
            VERIFY.verify_taxonomy(root),
            "activity-tag mappings do not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-profile-map-") as scratch:
        root = Path(scratch)
        seed(root)
        profiles = root / "skills/automation-design/references/process-profiles.md"
        profiles.write_text(
            profiles.read_text(encoding="utf-8").replace(
                "Observed current execution.",
                "Invented future execution.",
            ),
            encoding="utf-8",
        )
        expect_failure(
            "process-profile documentation drift",
            VERIFY.verify_taxonomy(root),
            "stable-profile table does not match taxonomy",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-profile-example-") as scratch:
        root = Path(scratch)
        seed(root)
        example = root / "skills/automation-design/assets/example-process-as-is.html"
        example.write_text(
            example.read_text(encoding="utf-8").replace(
                'data-measure-state="unknown"',
                'data-measure-state="estimated"',
            ),
            encoding="utf-8",
        )
        expect_failure(
            "implicit AS-IS unknown measure",
            VERIFY.verify_taxonomy(root),
            "keep at least one unknown measure explicit",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-unhashable-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        payload["semantic_patterns"][0]["nearest_visual_type"] = ["architecture"]
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "non-string visual route",
            VERIFY.verify_taxonomy(root),
            "nearest_visual_type must be a non-empty string",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-version-") as scratch:
        root = Path(scratch)
        payload = seed(root)
        payload["taxonomy_version"] = "v1"
        write_json(root / "skills/automation-design/taxonomy.json", payload)
        expect_failure(
            "invalid taxonomy version",
            VERIFY.verify_taxonomy(root),
            "taxonomy_version must be a semantic version",
        )

    with tempfile.TemporaryDirectory(prefix="taxonomy-contributing-count-") as scratch:
        root = Path(scratch)
        seed(root)
        (root / "CONTRIBUTING.md").write_text(
            "This repository supports 2 visual types.\n", encoding="utf-8"
        )
        expect_failure(
            "stale contributing visual count",
            VERIFY.verify_taxonomy(root),
            "CONTRIBUTING.md declares 2 visual types",
        )

    print("All taxonomy verification tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
