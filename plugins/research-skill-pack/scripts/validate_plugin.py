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
CATALOG_PATH = Path("shared/skill-catalog-v0.2.yaml")
LEGACY_MAP_PATH = Path("shared/legacy-skill-map-v0.2.yaml")
VALIDATION_LEVELS = {"structural", "behavior", "manual_pilot"}
BETA_WORKFLOW_MARKERS = (
    "## 前置输入",
    "## 执行步骤",
    "## 输出与异常",
    "## 安全边界",
    "## 参考",
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


def _catalog_entries(catalog: dict[str, Any]) -> list[tuple[dict[str, Any], str]]:
    entries: list[tuple[dict[str, Any], str]] = []
    for pack_index, pack in enumerate(catalog.get("packs", [])):
        if not isinstance(pack, dict) or not isinstance(pack.get("skills"), list):
            continue
        for skill_index, skill in enumerate(pack["skills"]):
            if isinstance(skill, dict):
                entries.append((skill, f"packs.{pack_index}.skills.{skill_index}"))
    return entries


def _implementation_ids(plugin_root: Path) -> set[str]:
    skills_root = plugin_root / SKILLS_PATH
    if not skills_root.is_dir():
        return set()
    return {
        item.name for item in skills_root.iterdir()
        if item.is_dir() and (item / "SKILL.md").is_file()
    }


def validate_catalog(plugin_root: Path = PLUGIN_ROOT) -> list[Finding]:
    """Validate the Catalog, legacy mapping, and installed Skill inventory together."""
    catalog_path = plugin_root / CATALOG_PATH
    mapping_path = plugin_root / LEGACY_MAP_PATH
    try:
        catalog = _read_yaml(catalog_path)
    except ValueError as exc:
        return [Finding("invalid_catalog", str(exc), str(catalog_path))]
    if not isinstance(catalog, dict) or not isinstance(catalog.get("packs"), list):
        return [Finding("invalid_catalog", "catalog requires a top-level packs list", str(catalog_path))]
    try:
        mapping_document = _read_yaml(mapping_path)
    except ValueError as exc:
        return [Finding("invalid_legacy_mapping", str(exc), str(mapping_path))]
    legacy_map = mapping_document.get("legacy_to_canonical") if isinstance(mapping_document, dict) else None
    if not isinstance(legacy_map, dict) or not legacy_map:
        return [Finding("invalid_legacy_mapping", "mapping requires a non-empty legacy_to_canonical object", str(mapping_path))]
    findings: list[Finding] = []
    seen_ids: set[str] = set()
    declared_legacy_ids: dict[str, str] = {}
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
            validation = skill.get("validation")
            if not isinstance(validation, dict) or validation.get("level") not in VALIDATION_LEVELS:
                findings.append(Finding("catalog_validation_level", "catalog skill requires a supported validation level", location))
            elif not isinstance(validation.get("refs"), list) or not all(isinstance(ref, str) and ref for ref in validation["refs"]):
                findings.append(Finding("catalog_validation_refs", "catalog skill validation requires non-empty string refs", location))
            legacy_ids = skill.get("legacy_design_ids", [])
            if not isinstance(legacy_ids, list) or not all(isinstance(legacy_id, str) and legacy_id for legacy_id in legacy_ids):
                findings.append(Finding("catalog_legacy_ids", "legacy_design_ids must be a list of non-empty strings", location))
            else:
                for legacy_id in legacy_ids:
                    if legacy_id in declared_legacy_ids:
                        findings.append(Finding("duplicate_legacy_design_id", f"duplicate legacy design id {legacy_id!r}", location))
                    else:
                        declared_legacy_ids[legacy_id] = skill_id if isinstance(skill_id, str) else ""

    mapping_keys = set(legacy_map)
    mapping_targets = set(legacy_map.values()) if all(isinstance(value, str) for value in legacy_map.values()) else set()
    if mapping_keys != set(declared_legacy_ids):
        findings.append(Finding("legacy_mapping_coverage", "legacy mapping keys must exactly match Catalog legacy_design_ids", str(mapping_path)))
    for legacy_id, canonical_id in declared_legacy_ids.items():
        if legacy_map.get(legacy_id) != canonical_id:
            findings.append(Finding("legacy_mapping_target", f"legacy id {legacy_id!r} must map to catalog id {canonical_id!r}", str(mapping_path)))
    if len(mapping_targets) != len(legacy_map):
        findings.append(Finding("legacy_mapping_not_one_to_one", "each legacy design id must map to a distinct canonical Skill", str(mapping_path)))
    if not mapping_targets.issubset(seen_ids):
        findings.append(Finding("legacy_mapping_unknown_target", "legacy mapping references a missing Catalog Skill", str(mapping_path)))

    implementation_ids = _implementation_ids(plugin_root)
    if seen_ids != implementation_ids:
        findings.append(Finding("catalog_implementation_drift", "Catalog Skill ids must exactly equal installed SKILL.md directory names", str(catalog_path)))
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
            beta_workflow = metadata.get("beta_workflow")
            if beta_workflow not in (None, "bounded"):
                findings.append(Finding("invalid_beta_workflow", "beta_workflow must be bounded when present", str(skill_path)))
            if beta_workflow == "bounded":
                try:
                    skill_text = skill_path.read_text(encoding="utf-8")
                except OSError:
                    skill_text = ""
                missing_markers = [marker for marker in BETA_WORKFLOW_MARKERS if marker not in skill_text]
                if missing_markers:
                    findings.append(Finding(
                        "incomplete_beta_workflow",
                        f"bounded beta workflow is missing sections: {', '.join(missing_markers)}",
                        str(skill_path),
                    ))

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
    """Report Catalog completeness without conflating it with behavioral coverage."""
    catalog_path = plugin_root / CATALOG_PATH
    catalog = _read_yaml(catalog_path)
    entries = _catalog_entries(catalog) if isinstance(catalog, dict) else []
    catalog_ids = {item["id"] for item, _ in entries if isinstance(item.get("id"), str)}
    declared_legacy_ids = {
        legacy_id: item["id"]
        for item, _ in entries
        if isinstance(item.get("id"), str) and isinstance(item.get("legacy_design_ids", []), list)
        for legacy_id in item.get("legacy_design_ids", [])
        if isinstance(legacy_id, str)
    }
    implementation_ids = _implementation_ids(plugin_root)
    mapping_document = _read_yaml(plugin_root / LEGACY_MAP_PATH)
    legacy_map = mapping_document.get("legacy_to_canonical", {}) if isinstance(mapping_document, dict) else {}
    mapping_keys = set(legacy_map) if isinstance(legacy_map, dict) else set()
    mapping_values = list(legacy_map.values()) if isinstance(legacy_map, dict) else []
    missing_legacy_mappings = sorted(set(declared_legacy_ids) - mapping_keys)
    unexpected_legacy_mappings = sorted(mapping_keys - set(declared_legacy_ids))
    misdirected_legacy_mappings = sorted(
        legacy_id
        for legacy_id, canonical_id in declared_legacy_ids.items()
        if not isinstance(legacy_map, dict) or legacy_map.get(legacy_id) != canonical_id
    )
    duplicate_targets = sorted({target for target in mapping_values if mapping_values.count(target) > 1})
    mapping_matches = not (
        missing_legacy_mappings
        or unexpected_legacy_mappings
        or misdirected_legacy_mappings
        or duplicate_targets
        or any(target not in catalog_ids for target in mapping_values)
    )
    return {
        "catalog_skill_count": len(catalog_ids),
        "implemented_skill_count": len(implementation_ids),
        "legacy_design_id_count": len(legacy_map) if isinstance(legacy_map, dict) else 0,
        "bounded_workflow_skill_count": sum(
            1
            for skill_id in implementation_ids
            if (_front_matter(plugin_root / SKILLS_PATH / skill_id / "SKILL.md") or {}).get("beta_workflow") == "bounded"
        ),
        "strict_match": catalog_ids == implementation_ids and mapping_matches,
        "catalog_only": sorted(catalog_ids - implementation_ids),
        "implementation_only": sorted(implementation_ids - catalog_ids),
        "missing_legacy_mappings": missing_legacy_mappings,
        "unexpected_legacy_mappings": unexpected_legacy_mappings,
        "misdirected_legacy_mappings": misdirected_legacy_mappings,
        "duplicate_legacy_mapping_targets": duplicate_targets,
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
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("VALID: manifest, Skill front matter, Catalog inventory, and synthetic fixtures")
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
