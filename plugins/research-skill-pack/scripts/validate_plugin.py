#!/usr/bin/env python3
"""Validate the distributable structure of Research Skill Pack.

This checker is intentionally local-only.  It verifies the plugin manifest,
discoverable Skill front matter, and the bundled synthetic project fixtures;
it does not install the plugin, call a model, contact a provider, or read raw
research data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import research_contract


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(".codex-plugin/plugin.json")
SKILLS_PATH = Path("skills")
FIXTURE_PATHS = (
    Path("fixtures/valid-project"),
    Path("fixtures/v0.2-project"),
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(str(exc)) from exc


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(str(exc)) from exc


def _front_matter(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    closing = text.find("\n---\n", 4)
    if closing == -1:
        return None
    try:
        data = yaml.safe_load(text[4:closing])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def validate_catalog(plugin_root: Path = PLUGIN_ROOT) -> list[Finding]:
    """Validate the Catalog as a requirements artifact, not an execution log."""
    catalog_path = plugin_root / "shared/skill-catalog-v0.2.yaml"
    try:
        catalog = _read_yaml(catalog_path)
    except ValueError as exc:
        return [Finding("invalid_catalog", str(exc), str(catalog_path))]
    if not isinstance(catalog, dict) or not isinstance(catalog.get("packs"), list):
        return [Finding("invalid_catalog", "catalog requires a top-level packs list", str(catalog_path))]
    findings: list[Finding] = []
    seen_ids: set[str] = set()
    for pack_index, pack in enumerate(catalog["packs"]):
        if not isinstance(pack, dict) or not isinstance(pack.get("id"), str) or not isinstance(pack.get("skills"), list):
            findings.append(Finding("invalid_catalog_pack", "each pack requires id and skills", f"{catalog_path}:packs.{pack_index}"))
            continue
        for skill_index, skill in enumerate(pack["skills"]):
            location = f"{catalog_path}:packs.{pack_index}.skills.{skill_index}"
            if not isinstance(skill, dict):
                findings.append(Finding("invalid_catalog_skill", "each catalog skill must be an object", location))
                continue
            skill_id = skill.get("id")
            if not isinstance(skill_id, str) or not skill_id:
                findings.append(Finding("catalog_skill_id", "each catalog skill needs an id", location))
            elif skill_id in seen_ids:
                findings.append(Finding("duplicate_catalog_skill_id", f"duplicate catalog skill id {skill_id!r}", location))
            else:
                seen_ids.add(skill_id)
            for key in ("inputs", "outputs", "gates", "safety", "acceptance_ids"):
                if not isinstance(skill.get(key), list) or not skill[key]:
                    findings.append(Finding("catalog_required_list", f"catalog skill requires a non-empty {key!r} list", location))
    return findings


def validate_plugin(plugin_root: Path = PLUGIN_ROOT) -> list[Finding]:
    """Return structural errors for a checked-out plugin package."""
    findings: list[Finding] = []
    manifest_path = plugin_root / MANIFEST_PATH
    try:
        manifest = _read_json(manifest_path)
    except ValueError as exc:
        return [Finding("invalid_manifest", str(exc), str(manifest_path))]
    if not isinstance(manifest, dict):
        return [Finding("invalid_manifest", "plugin manifest must be an object", str(manifest_path))]
    for key in ("name", "version", "description", "skills"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            findings.append(Finding("manifest_field", f"manifest requires a non-empty {key!r}", str(manifest_path)))
    if manifest.get("name") != "research-skill-pack":
        findings.append(Finding("manifest_name", "manifest name must be research-skill-pack", str(manifest_path)))
    if manifest.get("skills") != "./skills/":
        findings.append(Finding("manifest_skills_path", "manifest skills path must be ./skills/", str(manifest_path)))

    skills_root = plugin_root / SKILLS_PATH
    if not skills_root.is_dir():
        findings.append(Finding("missing_skills_directory", "skills directory is missing", str(skills_root)))
    else:
        for skill_dir in sorted(item for item in skills_root.iterdir() if item.is_dir()):
            skill_path = skill_dir / "SKILL.md"
            metadata = _front_matter(skill_path)
            if metadata is None:
                findings.append(Finding("invalid_skill_front_matter", "SKILL.md needs YAML front matter", str(skill_path)))
                continue
            if metadata.get("name") != skill_dir.name:
                findings.append(Finding("skill_name_mismatch", "front-matter name must equal its directory", str(skill_path)))
            if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
                findings.append(Finding("missing_skill_description", "front matter requires a non-empty description", str(skill_path)))

    for fixture_relative in FIXTURE_PATHS:
        fixture_path = plugin_root / fixture_relative
        fixture_findings = research_contract.validate_project(fixture_path)
        findings.extend(
            Finding(f"fixture_{item.code}", item.message, item.path)
            for item in fixture_findings
        )
    findings.extend(validate_catalog(plugin_root))
    return findings


def catalog_report(plugin_root: Path = PLUGIN_ROOT) -> dict[str, Any]:
    """Report, without conflating it with executable test coverage, catalog drift."""
    catalog_path = plugin_root / "shared/skill-catalog-v0.2.yaml"
    catalog = _read_yaml(catalog_path)
    entries = catalog.get("packs", []) if isinstance(catalog, dict) else []
    catalog_ids = {
        item["id"]
        for pack in entries if isinstance(pack, dict)
        for item in pack.get("skills", []) if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    implementation_ids = {
        item.name for item in (plugin_root / SKILLS_PATH).iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    }
    return {
        "catalog_skill_count": len(catalog_ids),
        "implemented_skill_count": len(implementation_ids),
        "catalog_only": sorted(catalog_ids - implementation_ids),
        "implementation_only": sorted(implementation_ids - catalog_ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local Research Skill Pack package without network or model calls.")
    parser.add_argument("--root", type=Path, default=PLUGIN_ROOT, help="plugin root to validate")
    parser.add_argument("--catalog-report", action="store_true", help="print catalog-to-implementation drift; does not change validation status")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)
    findings = validate_plugin(args.root)
    report = catalog_report(args.root) if args.catalog_report else None
    if args.json:
        print(json.dumps({"valid": not findings, "findings": [item.as_dict() for item in findings], "catalog_report": report}, ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            location = f" [{item.path}]" if item.path else ""
            print(f"ERROR {item.code}{location}: {item.message}")
    else:
        print("VALID: manifest, Skill front matter, and synthetic fixtures")
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
