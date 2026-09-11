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
import re
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
VERIFICATION_MATRIX_PATH = Path("shared/verification-matrix-v0.2.yaml")
PROFILE_REGISTRY_PATH = Path("shared/profile-registry-v0.2.json")
PROJECT_SCHEMA_PATH = Path("shared/project-schema.json")
VALIDATION_LEVELS = {"structural", "deterministic_contract", "manual_pilot"}
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


def _catalog_skill_records(plugin_root: Path) -> list[dict[str, Any]]:
    try:
        catalog = _read_yaml(plugin_root / CATALOG_PATH)
    except ValueError:
        return []
    return [skill for skill, _ in _catalog_entries(catalog) if isinstance(skill, dict)] if isinstance(catalog, dict) else []


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


def validate_profile_registry(plugin_root: Path = PLUGIN_ROOT) -> list[Finding]:
    """Keep the supported-profile inventory and project schema in sync."""
    registry_path = plugin_root / PROFILE_REGISTRY_PATH
    schema_path = plugin_root / PROJECT_SCHEMA_PATH
    try:
        registry = _read_json(registry_path)
        schema = _read_json(schema_path)
    except ValueError as exc:
        return [Finding("invalid_profile_registry", str(exc), str(registry_path))]
    if not isinstance(registry, dict) or not isinstance(registry.get("profiles"), list):
        return [Finding("invalid_profile_registry", "profile registry requires a profiles list", str(registry_path))]
    findings: list[Finding] = []
    profile_ids: list[str] = []
    for index, profile in enumerate(registry["profiles"]):
        location = f"{registry_path}:profiles.{index}"
        if not isinstance(profile, dict):
            findings.append(Finding("invalid_profile_entry", "each profile must be an object", location))
            continue
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or not profile_id:
            findings.append(Finding("profile_id", "each profile needs a non-empty id", location))
            continue
        if profile_id in profile_ids:
            findings.append(Finding("duplicate_profile_id", f"duplicate profile id {profile_id!r}", location))
        profile_ids.append(profile_id)
        for key in ("version", "status", "display_name", "migration_policy"):
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                findings.append(Finding("profile_required_field", f"profile requires non-empty {key!r}", location))
        if profile.get("status") != "active":
            findings.append(Finding("unsupported_profile_status", "v0.2 registry entries must be active", location))
        if not isinstance(profile.get("schema_versions"), list) or not profile["schema_versions"]:
            findings.append(Finding("profile_schema_versions", "profile requires non-empty schema_versions", location))
    schema_profiles = schema.get("properties", {}).get("profile", {}).get("enum") if isinstance(schema, dict) else None
    if not isinstance(schema_profiles, list) or set(schema_profiles) != set(profile_ids):
        findings.append(Finding(
            "profile_registry_schema_drift",
            "project-schema profile enum must exactly match the active profile registry",
            str(schema_path),
        ))
    return findings


def validate_verification_matrix(plugin_root: Path = PLUGIN_ROOT) -> list[Finding]:
    """Require every acceptance id to state its actual, limited evidence type."""
    matrix_path = plugin_root / VERIFICATION_MATRIX_PATH
    try:
        matrix = _read_yaml(matrix_path)
    except ValueError as exc:
        return [Finding("invalid_verification_matrix", str(exc), str(matrix_path))]
    if not isinstance(matrix, dict) or not isinstance(matrix.get("cases"), list):
        return [Finding("invalid_verification_matrix", "verification matrix requires a cases list", str(matrix_path))]
    catalog_records = _catalog_skill_records(plugin_root)
    expected: dict[str, dict[str, Any]] = {}
    for skill in catalog_records:
        for acceptance_id in skill.get("acceptance_ids", []):
            if isinstance(acceptance_id, str):
                expected[acceptance_id] = skill
    findings: list[Finding] = []
    seen_acceptance_ids: set[str] = set()
    seen_verification_ids: set[str] = set()
    for index, case in enumerate(matrix["cases"]):
        location = f"{matrix_path}:cases.{index}"
        if not isinstance(case, dict):
            findings.append(Finding("invalid_verification_case", "each verification case must be an object", location))
            continue
        required = ("verification_id", "acceptance_id", "skill_id", "kind", "evidence_boundary")
        if any(not isinstance(case.get(key), str) or not case[key].strip() for key in required):
            findings.append(Finding("verification_required_field", "verification case has missing required string fields", location))
            continue
        acceptance_id, verification_id = case["acceptance_id"], case["verification_id"]
        if acceptance_id in seen_acceptance_ids:
            findings.append(Finding("duplicate_verification_acceptance", f"duplicate acceptance id {acceptance_id!r}", location))
        seen_acceptance_ids.add(acceptance_id)
        if verification_id in seen_verification_ids:
            findings.append(Finding("duplicate_verification_id", f"duplicate verification id {verification_id!r}", location))
        seen_verification_ids.add(verification_id)
        catalog_skill = expected.get(acceptance_id)
        if catalog_skill is None:
            findings.append(Finding("verification_unknown_acceptance", f"unknown acceptance id {acceptance_id!r}", location))
            continue
        if case["skill_id"] != catalog_skill.get("id"):
            findings.append(Finding("verification_skill_mismatch", f"acceptance id {acceptance_id!r} maps to a different Skill", location))
        validation = catalog_skill.get("validation", {})
        if case["kind"] not in VALIDATION_LEVELS or validation.get("level") != case["kind"]:
            findings.append(Finding("verification_kind_mismatch", "verification kind must match the Catalog validation level", location))
        if validation.get("refs") != [verification_id]:
            findings.append(Finding("verification_reference_mismatch", "Catalog validation.refs must contain this case's verification id", location))
        if case["kind"] == "manual_pilot":
            if not isinstance(case.get("pilot_step"), str) or not case["pilot_step"].strip():
                findings.append(Finding("verification_pilot_step", "manual pilot cases require pilot_step", location))
            continue
        test_file = case.get("test_file")
        test_case = case.get("test_case")
        if not isinstance(test_file, str) or not isinstance(test_case, str):
            findings.append(Finding("verification_test_reference", "automated cases require test_file and test_case", location))
            continue
        resolved_test_file = (plugin_root / test_file).resolve()
        try:
            resolved_test_file.relative_to(plugin_root.resolve())
        except ValueError:
            findings.append(Finding("unsafe_verification_test_path", "test_file must remain inside the plugin root", location))
            continue
        if not resolved_test_file.is_file():
            findings.append(Finding("verification_test_file_missing", f"missing test file {test_file!r}", location))
            continue
        test_text = resolved_test_file.read_text(encoding="utf-8")
        if not re.search(rf"^def {re.escape(test_case)}\(", test_text, flags=re.MULTILINE):
            findings.append(Finding("verification_test_case_missing", f"missing test case {test_case!r}", location))
    missing = sorted(set(expected) - seen_acceptance_ids)
    unexpected = sorted(seen_acceptance_ids - set(expected))
    if missing:
        findings.append(Finding("verification_matrix_missing_acceptance", f"verification matrix is missing acceptance ids: {', '.join(missing)}", str(matrix_path)))
    if unexpected:
        findings.append(Finding("verification_matrix_unexpected_acceptance", f"verification matrix has unknown acceptance ids: {', '.join(unexpected)}", str(matrix_path)))
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
    findings.extend(validate_profile_registry(plugin_root))
    findings.extend(validate_verification_matrix(plugin_root))
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


def verification_report(plugin_root: Path = PLUGIN_ROOT) -> dict[str, Any]:
    """Report acceptance coverage and evidence categories without overstating behavior tests."""
    catalog_records = _catalog_skill_records(plugin_root)
    catalog_acceptance = {
        acceptance_id
        for skill in catalog_records
        for acceptance_id in skill.get("acceptance_ids", [])
        if isinstance(acceptance_id, str)
    }
    try:
        matrix = _read_yaml(plugin_root / VERIFICATION_MATRIX_PATH)
    except ValueError:
        matrix = {}
    cases = matrix.get("cases", []) if isinstance(matrix, dict) and isinstance(matrix.get("cases"), list) else []
    matrix_acceptance = {
        case.get("acceptance_id")
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("acceptance_id"), str)
    }
    kinds = {kind: 0 for kind in sorted(VALIDATION_LEVELS)}
    for case in cases:
        if isinstance(case, dict) and case.get("kind") in kinds:
            kinds[case["kind"]] += 1
    return {
        "catalog_acceptance_count": len(catalog_acceptance),
        "matrix_case_count": len(cases),
        "coverage_complete": catalog_acceptance == matrix_acceptance,
        "kind_counts": kinds,
        "missing_acceptance_ids": sorted(catalog_acceptance - matrix_acceptance),
        "unexpected_acceptance_ids": sorted(matrix_acceptance - catalog_acceptance),
        "evidence_boundary": "Structural and deterministic-contract checks do not evaluate LLM responses or verify external research facts.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the local Research Skill Pack package without network or model calls.")
    parser.add_argument("--root", type=Path, default=PLUGIN_ROOT, help="plugin root to validate")
    parser.add_argument("--catalog-report", action="store_true", help="print catalog-to-implementation drift; does not change validation status")
    parser.add_argument("--verification-report", action="store_true", help="print acceptance-to-verification coverage without claiming model behavior coverage")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)
    findings = validate_plugin(args.root)
    report = catalog_report(args.root) if args.catalog_report else None
    matrix_report = verification_report(args.root) if args.verification_report else None
    if args.json:
        print(json.dumps({"valid": not findings, "findings": [item.as_dict() for item in findings], "catalog_report": report, "verification_report": matrix_report}, ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            location = f" [{item.path}]" if item.path else ""
            print(f"ERROR {item.code}{location}: {item.message}")
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        if matrix_report is not None:
            print(json.dumps(matrix_report, ensure_ascii=False, indent=2))
    else:
        print("VALID: manifest, Skill front matter, Catalog inventory, verification mapping, profile registry, and synthetic fixtures")
        if report is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        if matrix_report is not None:
            print(json.dumps(matrix_report, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
