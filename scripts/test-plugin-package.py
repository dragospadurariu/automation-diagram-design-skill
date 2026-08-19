#!/usr/bin/env python3
"""Regression tests for plugin versioning and marketplace package verification."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent
VERIFY_SCRIPT = ROOT / "scripts/verify-plugin-package.py"
BUMP_SCRIPT = ROOT / "scripts/bump-plugin-version.py"
PLUGIN_NAME = "automation-design"


def load_module(name: str, path: Path) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module("verify_plugin_package", VERIFY_SCRIPT)
BUMP = load_module("bump_plugin_version", BUMP_SCRIPT)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def manifest(version: str, codex: bool = False) -> dict:
    payload = {
        "name": PLUGIN_NAME,
        "description": "Create editorial diagrams.",
        "version": version,
        "author": {"name": "Cathryn Lavery"},
    }
    if codex:
        payload["skills"] = "./skills/"
    return payload


def seed_package(root: Path, version: str = "1.2.3") -> None:
    write_json(root / ".claude-plugin/plugin.json", manifest(version))
    write_json(root / ".codex-plugin/plugin.json", manifest(version, codex=True))
    write_json(
        root / ".claude-plugin/marketplace.json",
        {
            "name": PLUGIN_NAME,
            "plugins": [{"name": PLUGIN_NAME, "source": "./"}],
        },
    )
    write_json(
        root / ".agents/plugins/marketplace.json",
        {
            "name": PLUGIN_NAME,
            "plugins": [
                {
                    "name": PLUGIN_NAME,
                    "source": {"source": "local", "path": "./"},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        },
    )
    skill = root / "skills" / PLUGIN_NAME / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(f"---\nname: {PLUGIN_NAME}\n---\n", encoding="utf-8")


@contextmanager
def package_repo() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        seed_package(root)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Package Test"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "package-test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base package"], cwd=root, check=True)
        yield root


def set_versions(root: Path, claude: str, codex: str) -> None:
    for relative, version in (
        (Path(".claude-plugin/plugin.json"), claude),
        (Path(".codex-plugin/plugin.json"), codex),
    ):
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        payload["version"] = version
        write_json(root / relative, payload)


def rename_base_plugin(root: Path, old_name: str, old_version: str = "2.5.0") -> None:
    """Commit a base ref that carries a different plugin name, as a fork does.

    Only the committed manifests change identity; the working tree keeps the
    current name so the identity and marketplace checks still apply to it.
    """
    relatives = list(VERIFY.MANIFEST_PATHS.values())
    current = {
        relative: json.loads((root / relative).read_text(encoding="utf-8"))
        for relative in relatives
    }
    for relative in relatives:
        base_payload = dict(current[relative])
        base_payload["name"] = old_name
        base_payload["version"] = old_version
        write_json(root / relative, base_payload)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", f"base package as {old_name}"], cwd=root, check=True)
    for relative in relatives:
        write_json(root / relative, current[relative])


def expect_failure(label: str, errors: list[str], needle: str) -> None:
    if not any(needle in error for error in errors):
        raise AssertionError(f"{label}: expected {needle!r}, got {errors}")
    print(f"OK: {label} rejected")


def test_verifier() -> None:
    with package_repo() as root:
        set_versions(root, "1.2.4", "1.2.4")
        errors = VERIFY.verify_package(root, "HEAD")
        if errors:
            raise AssertionError(f"valid bump failed: {errors}")
        print("OK: valid synchronized bump accepted")

    with package_repo() as root:
        expect_failure(
            "missing bump",
            VERIFY.verify_package(root, "HEAD"),
            "must increase",
        )

    with package_repo() as root:
        set_versions(root, "1.2.4", "1.2.5")
        expect_failure(
            "mismatched manifests",
            VERIFY.verify_package(root, "HEAD"),
            "versions must match",
        )

    # The rename/fork boundary: version lineage is per plugin identity, so a base
    # ref carrying a different plugin name legitimately allows 2.5.0 -> 0.1.0.
    # The waiver must be announced, and it must not swallow anything else.
    with package_repo() as root:
        rename_base_plugin(root, "diagram-design")
        set_versions(root, "0.1.0", "0.1.0")
        waivers: list[str] = []
        errors = VERIFY.verify_package(root, "HEAD", waivers)
        if errors:
            raise AssertionError(f"fork-boundary reset rejected: {errors}")
        if len(waivers) != len(VERIFY.MANIFEST_PATHS):
            raise AssertionError(
                f"fork boundary must announce one waiver per manifest; got {waivers}"
            )
        if not all("WAIVED" in w or "waived" in w.lower() for w in waivers):
            raise AssertionError(f"waiver text must say it was waived: {waivers}")
        print("OK: fork-boundary version reset accepted and announced")

    # The waiver is scoped to the version-increase check only — a genuinely broken
    # manifest at a fork boundary must still fail.
    with package_repo() as root:
        rename_base_plugin(root, "diagram-design")
        set_versions(root, "0.1", "0.1")
        expect_failure(
            "non-semver at a fork boundary",
            VERIFY.verify_package(root, "HEAD", []),
            "semver",
        )

    # Once the rename has landed on the base ref, the check must protect again.
    with package_repo() as root:
        set_versions(root, "0.1.0", "0.1.0")
        waivers = []
        expect_failure(
            "version regression after the rename landed",
            VERIFY.verify_package(root, "HEAD", waivers),
            "must increase",
        )
        if waivers:
            raise AssertionError(f"no waiver expected once names match; got {waivers}")

    with package_repo() as root:
        set_versions(root, "1.2", "1.2")
        expect_failure(
            "malformed versions",
            VERIFY.verify_package(root, "HEAD"),
            "strict MAJOR.MINOR.PATCH",
        )

    with package_repo() as root:
        set_versions(root, "1.2.4", "1.2.4")
        marketplace_path = root / ".agents/plugins/marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        marketplace["plugins"][0]["source"]["path"] = "./missing"
        write_json(marketplace_path, marketplace)
        expect_failure(
            "missing marketplace target",
            VERIFY.verify_package(root, "HEAD"),
            "target does not exist",
        )


def test_bumper() -> None:
    cases = (("patch", "1.2.4"), ("minor", "1.3.0"), ("major", "2.0.0"))
    for part, expected in cases:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            seed_package(root)
            actual = BUMP.bump(root, part)
            versions = {
                json.loads((root / relative).read_text(encoding="utf-8"))["version"]
                for relative in BUMP.MANIFEST_PATHS
            }
            if actual != expected or versions != {expected}:
                raise AssertionError(
                    f"{part} bump: expected {expected}, got {actual} and {versions}"
                )
            print(f"OK: {part} bump produced {expected}")

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        seed_package(root)
        set_versions(root, "1.2.3", "1.2.4")
        try:
            BUMP.bump(root)
        except BUMP.PackageVersionError as exc:
            if "not synchronized" not in str(exc):
                raise AssertionError(f"unexpected mismatch error: {exc}") from exc
        else:
            raise AssertionError("version bumper accepted mismatched manifests")
        print("OK: version bumper rejects mismatched manifests")


def main() -> int:
    test_verifier()
    test_bumper()
    print("All plugin package tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
