#!/usr/bin/env python3
"""Regression tests for docs links and profile-surface verification."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "scripts" / "verify-docs-sync.py"


def load_verify_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("automation_design_verify_docs", VERIFY)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load verify-docs-sync.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    verify = load_verify_module()
    with tempfile.TemporaryDirectory(prefix="verify-docs-sync-") as temp_dir:
        skill = Path(temp_dir)
        references = skill / "references"
        references.mkdir()
        (references / "present.md").write_text("# Present\n", encoding="utf-8")

        errors: list[str] = []
        verify.check_skill_reference_links(
            errors,
            "See [present](references/present.md) and [section](references/present.md#part).",
            skill,
        )
        if errors:
            raise AssertionError(f"valid reference link failed: {errors}")

        errors = []
        verify.check_skill_reference_links(
            errors,
            "See [missing](references/missing.md).",
            skill,
        )
        expected = "SKILL.md links to missing reference 'references/missing.md'"
        if errors != [expected]:
            raise AssertionError(f"broken reference was not reported: {errors}")

        errors = []
        verify.check_skill_reference_links(
            errors,
            "See [README](../../README.md), [asset](assets/example.html), and https://example.com.",
            skill,
        )
        if errors:
            raise AssertionError(f"non-reference links should be ignored: {errors}")

        # Links *between* reference files are bare siblings, so they resolve
        # against the linking file's own directory - not against SKILL.md's.
        (references / "sibling.md").write_text(
            "See [present](present.md), [asset](../assets/example.html), "
            "[anchor](#part), [style](present.md#deep) and https://example.com.\n",
            encoding="utf-8",
        )
        assets = skill / "assets"
        assets.mkdir()
        (assets / "example.html").write_text("<!DOCTYPE html>\n", encoding="utf-8")

        errors = []
        verify.check_reference_cross_links(errors, references)
        if errors:
            raise AssertionError(f"resolving reference cross-links failed: {errors}")

        # The seven links left pointing at deleted type references shipped
        # because nothing resolved a bare sibling. This is that gate.
        (references / "sibling.md").write_text(
            "Redraw as a [data model](type-er.md).\n", encoding="utf-8"
        )
        errors = []
        verify.check_reference_cross_links(errors, references)
        expected = "references/sibling.md links to missing 'type-er.md'"
        if errors != [expected]:
            raise AssertionError(f"broken reference cross-link was not reported: {errors}")

        (references / "sibling.md").unlink()

        root = Path(temp_dir) / "repo"
        profile_reference = root / "skills/automation-design/references/profiles.md"
        command = root / "commands/profile.md"
        prompt = root / "prompts/profile.md"
        for path in (profile_reference, command, prompt):
            path.parent.mkdir(parents=True, exist_ok=True)
        profile_reference.write_text("# Profiles\n", encoding="utf-8")
        command.write_text("Follow references/profiles.md.\n", encoding="utf-8")
        prompt.write_text("Follow references/profiles.md.\n", encoding="utf-8")

        errors = []
        verify.check_profile_surfaces(errors, root)
        if errors:
            raise AssertionError(f"valid profile surfaces failed: {errors}")

        prompt.unlink()
        errors = []
        verify.check_profile_surfaces(errors, root)
        expected = "profile surface is missing: prompts/profile.md"
        if errors != [expected]:
            raise AssertionError(f"missing Pi prompt was not reported: {errors}")

        prompt.write_text("Stale standalone instructions.\n", encoding="utf-8")
        errors = []
        verify.check_profile_surfaces(errors, root)
        expected = (
            "profile surface does not route to references/profiles.md: prompts/profile.md"
        )
        if errors != [expected]:
            raise AssertionError(f"stale Pi prompt was not reported: {errors}")

        errors = []
        patterns = "# Patterns\n\n## 1. One\n\n## 2. Two\n"
        verify.check_pattern_counts(errors, "2 semantic patterns. 2 routed patterns.", patterns)
        if errors:
            raise AssertionError(f"valid pattern counts failed: {errors}")

        errors = []
        verify.check_pattern_counts(errors, "3 semantic patterns.", patterns)
        expected = "README declares 3 semantic patterns; catalog contains 2"
        if errors != [expected]:
            raise AssertionError(f"stale pattern count was not reported: {errors}")

        errors = []
        verify.check_pattern_counts(
            errors,
            "2 semantic patterns.",
            patterns,
            expected_count=3,
        )
        expected = "semantic-patterns.md contains 2 patterns; taxonomy.json contains 3"
        if errors != [expected]:
            raise AssertionError(f"taxonomy pattern drift was not reported: {errors}")

        original_taxonomy = verify.TAXONOMY
        taxonomy = Path(temp_dir) / "taxonomy.json"
        try:
            verify.TAXONOMY = taxonomy
            taxonomy.write_text(
                json.dumps(
                    {
                        "visual_types": [{"label": "Architecture"}],
                        "semantic_patterns": [{"label": "Agent with tools"}],
                    }
                ),
                encoding="utf-8",
            )
            errors = []
            projection = verify.taxonomy_projection(errors)
            if errors or projection != (["Architecture"], 1):
                raise AssertionError(
                    f"valid taxonomy projection failed: {projection}, {errors}"
                )

            taxonomy.write_text("{broken", encoding="utf-8")
            errors = []
            if verify.taxonomy_projection(errors) != ([], 0) or not any(
                "could not load taxonomy.json" in error for error in errors
            ):
                raise AssertionError(f"invalid taxonomy JSON was not reported: {errors}")

            taxonomy.write_text(json.dumps({"visual_types": []}), encoding="utf-8")
            errors = []
            verify.taxonomy_projection(errors)
            expected = "taxonomy.json must contain visual_types and semantic_patterns arrays"
            if errors != [expected]:
                raise AssertionError(f"missing taxonomy catalog was not reported: {errors}")

            taxonomy.write_text(
                json.dumps(
                    {
                        "visual_types": [{"label": 42}],
                        "semantic_patterns": [],
                    }
                ),
                encoding="utf-8",
            )
            errors = []
            verify.taxonomy_projection(errors)
            expected = "every taxonomy visual type must have a string label"
            if errors != [expected]:
                raise AssertionError(f"invalid taxonomy label was not reported: {errors}")
        finally:
            verify.TAXONOMY = original_taxonomy

        original_skill = verify.SKILL
        projected_skill = Path(temp_dir) / "projected-skill.md"
        projected_skill.write_text(
            "---\ndescription: Architecture and Sequence diagrams.\n---\n"
            "### Visual-type guide (1)\n\n"
            "| If you're showing… | Use | Reference |\n"
            "|---|---|---|\n"
            "| Components | **Architecture** | [Architecture](references/present.md) |\n"
            "Rules of thumb:\n",
            encoding="utf-8",
        )
        try:
            verify.SKILL = projected_skill
            errors = []
            verify.check_description(errors, ["Sequence"])
        finally:
            verify.SKILL = original_skill
        if not any("selection table does not match taxonomy.json" in error for error in errors):
            raise AssertionError(f"taxonomy selection drift was not reported: {errors}")

        skill_version = verify.skill_metadata_version(
            '---\nname: example\nmetadata:\n  version: "1.2.3"\n---\n'
        )
        if skill_version != "1.2.3":
            raise AssertionError(f"skill metadata version was not parsed: {skill_version!r}")

        palette_markdown = "\n".join(
            f"| `{role}` | use | `#{index:06x}` | dark |"
            for index, role in enumerate(verify.PALETTE_ROLES, start=1)
        )
        palette_css = ":root { " + " ".join(
            f"--{role}: #{index:06x};"
            for index, role in enumerate(verify.PALETTE_ROLES, start=1)
        ) + " }"
        if verify.style_guide_palette(palette_markdown) != verify.gallery_palette(palette_css):
            raise AssertionError("gallery and style-guide palette parsers disagree")

    print(
        "PASS: docs sync checks taxonomy projections, reference links, references/ "
        "cross-links, Claude/Pi profile-surface parity, semantic counts, versions, "
        "and palette parsing"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
