#!/usr/bin/env python3
"""Validate the local, versioned Research Skill Pack project contract.

This tool never contacts providers, reads registered raw-data paths, or mutates a
project. It only reads YAML files already inside ``<project>/.research``.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SHARED = PLUGIN_ROOT / "shared"
RESEARCH_DIR = ".research"
NORMAL_STATES = [
    "intake_draft", "intake_confirmed", "topic_assessed", "gap_ready",
    "board_decided", "design_ready", "evidence_ready", "blueprint_ready",
    "manuscript_audited", "review_ready", "venue_ready", "submission_ready",
    "archived",
]
SPECIAL_STATES = {"PIVOT", "KILL", "blocked"}
GATES: dict[str, tuple[str, str | None]] = {
    "intake_confirmed": ("context_brief", "confirmed"),
    "topic_assessed": ("topic_assessment", None),
    "gap_ready": ("gap_card", None),
    "board_decided": ("board_decision", "confirmed"),
    "design_ready": ("research_protocol", None),
    "evidence_ready": ("verified_evidence_package", "verified"),
    "blueprint_ready": ("manuscript_blueprint", None),
    "manuscript_audited": ("citation_audit", None),
    "review_ready": ("review_report", None),
    "venue_ready": ("venue_assessment", None),
    "submission_ready": ("submission_package", "confirmed"),
    "archived": ("archive_manifest", None),
}
FATAL_FLAWS = {
    "core_data_unavailable",
    "key_result_not_measurable",
    "method_cannot_answer_question",
    "unresolved_ethics_barrier",
}


class ContractLoader(yaml.SafeLoader):
    """Safe YAML loader that preserves ISO timestamps as strings for the schema."""


ContractLoader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, resolvers in list(ContractLoader.yaml_implicit_resolvers.items()):
    ContractLoader.yaml_implicit_resolvers[key] = [
        item for item in resolvers if item[0] != "tag:yaml.org,2002:timestamp"
    ]


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def load_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return yaml.load(stream, Loader=ContractLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read YAML: {exc}") from exc


def load_schema(name: str) -> dict[str, Any]:
    with (SHARED / name).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def schema_findings(data: Any, schema_name: str, path: str) -> list[Finding]:
    validator = Draft202012Validator(load_schema(schema_name), format_checker=FormatChecker())
    findings: list[Finding] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path)
        findings.append(Finding("schema", error.message, f"{path}:{location}".rstrip(":")))
    return findings


def is_safe_artifact_path(relative_path: str) -> bool:
    candidate = Path(relative_path)
    return not candidate.is_absolute() and ".." not in candidate.parts and candidate.parts[:1] == ("artifacts",)


def artifact_header_matches(index_item: dict[str, Any], artifact: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for key in ("id", "type", "version", "status", "created_at", "created_by", "depends_on", "supersedes", "change_reason"):
        if index_item.get(key) != artifact.get(key):
            findings.append(Finding("index_mismatch", f"index {key!r} differs from artifact header", index_item.get("path", "")))
    return findings


def required_gate_findings(state: str, artifacts: list[dict[str, Any]]) -> list[Finding]:
    requirement = GATES.get(state)
    if not requirement:
        return []
    artifact_type, required_status = requirement
    matches = [artifact for artifact in artifacts if artifact.get("type") == artifact_type]
    if not matches:
        return [Finding("missing_gate_artifact", f"state {state} requires a {artifact_type} artifact")]
    if required_status and not any(artifact.get("status") == required_status for artifact in matches):
        return [Finding("unconfirmed_gate", f"state {state} requires a {required_status} {artifact_type}")]
    if state == "board_decided":
        decisions = [artifact.get("decision") for artifact in matches if artifact.get("status") == "confirmed"]
        if not any(decision in {"GO", "CONDITIONAL_GO"} for decision in decisions):
            return [Finding("board_not_approved", "design is blocked until a confirmed GO or CONDITIONAL_GO decision")]
    if state == "manuscript_audited" and not any(a.get("type") == "originality_report" for a in artifacts):
        return [Finding("missing_gate_artifact", "manuscript_audited also requires an originality_report")]
    return []


def state_history_findings(project: dict[str, Any]) -> list[Finding]:
    history = project.get("state_history", [])
    if not history:
        return [Finding("missing_state_history", "at least one state history entry is required")]
    findings: list[Finding] = []
    sequences = [entry.get("sequence") for entry in history]
    if sequences != sorted(sequences) or len(set(sequences)) != len(sequences):
        findings.append(Finding("state_history_order", "state_history sequence must be strictly increasing"))
    if history[-1].get("state") != project.get("current_state"):
        findings.append(Finding("state_history_current", "last state_history state must equal current_state"))
    if sequences and max(sequences) > project.get("write_sequence", -1):
        findings.append(Finding("write_sequence", "write_sequence must be at least the latest state sequence"))
    return findings


def transition_findings(current: str, target: str) -> list[Finding]:
    if current == target:
        return []
    if current == "KILL":
        return [Finding("illegal_transition", "KILL requires a new Context Brief before a project can resume")]
    if target in SPECIAL_STATES:
        return []
    if current == "PIVOT":
        if target in {"intake_draft", "intake_confirmed", "topic_assessed", "gap_ready"}:
            return []
        return [Finding("illegal_transition", "PIVOT may resume only at intake, topic, or gap work")]
    if current == "blocked":
        return []
    if current not in NORMAL_STATES or target not in NORMAL_STATES:
        return [Finding("illegal_transition", f"unknown state transition {current} → {target}")]
    if NORMAL_STATES.index(target) != NORMAL_STATES.index(current) + 1:
        return [Finding("illegal_transition", f"normal flow permits only the next state, not {current} → {target}")]
    return []


def check_raw_data_safety(artifact: dict[str, Any], artifact_path: str) -> list[Finding]:
    if artifact.get("type") != "raw_data_register":
        return []
    raw_data = artifact.get("raw_data")
    if not isinstance(raw_data, dict):
        return [Finding("raw_data_register", "raw_data_register requires raw_data metadata only", artifact_path)]
    forbidden = {"records", "rows", "content", "excerpt", "participants", "responses", "tokens", "password", "api_key"}
    present = forbidden.intersection(raw_data)
    if present:
        return [Finding("raw_data_exposure", f"raw_data_register may not contain raw data fields: {', '.join(sorted(present))}", artifact_path)]
    return []


def check_metrics(artifact: dict[str, Any], artifact_path: str) -> list[Finding]:
    metric = artifact.get("metric")
    if metric is None:
        return []
    if not isinstance(metric, dict):
        return [Finding("metric", "metric must be an object", artifact_path)]
    rating = metric.get("rating")
    if rating not in {"Low", "Medium", "High", "insufficient_evidence"}:
        return [Finding("metric_rating", "metric rating must be Low, Medium, High, or insufficient_evidence", artifact_path)]
    evidence_ids = metric.get("evidence_ids")
    if not isinstance(evidence_ids, list) or (rating != "insufficient_evidence" and not evidence_ids):
        return [Finding("metric_evidence", "metric requires evidence_ids unless evidence is insufficient", artifact_path)]
    name = metric.get("name")
    if name == "Growth Momentum" and rating != "insufficient_evidence":
        windows = metric.get("windows")
        if not isinstance(windows, list) or len(windows) != 2 or any(
            not isinstance(window, dict)
            or window.get("months") != 24
            or not isinstance(window.get("independent_record_count"), int)
            or window["independent_record_count"] < 5
            for window in windows
        ):
            return [Finding("growth_momentum_windows", "Growth Momentum needs two adjacent 24-month windows with at least five dated independent records each", artifact_path)]
    if name == "Semantic Repetition Rate" and rating != "insufficient_evidence":
        if not isinstance(metric.get("independent_record_count"), int) or metric["independent_record_count"] < 20:
            return [Finding("srr_minimum_records", "SRR needs at least 20 independent records before calculation", artifact_path)]
    if name == "Citation Coverage":
        needed = metric.get("citation_needed_claims")
        fully_supported = metric.get("fully_supported_claims")
        if not isinstance(needed, int) or not isinstance(fully_supported, int) or needed < 0 or fully_supported < 0 or fully_supported > needed:
            return [Finding("citation_coverage_counts", "Citation Coverage requires non-negative supported and needed claim counts", artifact_path)]
    return []


def downstream_artifact_ids(artifacts: list[dict[str, Any]], root_id: str) -> set[str]:
    """Return direct and transitive dependants of an overridden artifact."""
    dependants: dict[str, set[str]] = {}
    for artifact in artifacts:
        for dependency in artifact.get("depends_on", []):
            dependants.setdefault(dependency, set()).add(artifact.get("id", ""))
    pending = list(dependants.get(root_id, set()))
    result: set[str] = set()
    while pending:
        current = pending.pop()
        if current in result:
            continue
        result.add(current)
        pending.extend(dependants.get(current, set()))
    return result


def validate_project(project_root: Path) -> list[Finding]:
    research_root = project_root / RESEARCH_DIR
    project_path = research_root / "project.yaml"
    if not project_path.is_file():
        return [Finding("missing_project", "missing .research/project.yaml", str(project_path))]
    try:
        project = load_yaml(project_path)
    except ValueError as exc:
        return [Finding("invalid_yaml", str(exc), str(project_path))]
    findings = schema_findings(project, "project-schema.json", str(project_path))
    if not isinstance(project, dict):
        return findings + [Finding("project_type", "project.yaml must be a mapping", str(project_path))]
    findings.extend(state_history_findings(project))
    artifacts: list[dict[str, Any]] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index_item in project.get("artifact_index", []):
        if not isinstance(index_item, dict):
            continue
        artifact_id = index_item.get("id")
        if artifact_id in ids:
            findings.append(Finding("duplicate_artifact_id", f"duplicate artifact id {artifact_id!r}"))
        ids.add(artifact_id)
        relative_path = index_item.get("path", "")
        if relative_path in paths:
            findings.append(Finding("duplicate_artifact_path", f"duplicate artifact path {relative_path!r}"))
        paths.add(relative_path)
        if not isinstance(relative_path, str) or not is_safe_artifact_path(relative_path):
            findings.append(Finding("unsafe_artifact_path", "artifact path must be a relative artifacts/*.yaml path", str(relative_path)))
            continue
        artifact_file = research_root / relative_path
        if not artifact_file.is_file():
            findings.append(Finding("missing_artifact", "indexed artifact file does not exist", str(artifact_file)))
            continue
        try:
            artifact = load_yaml(artifact_file)
        except ValueError as exc:
            findings.append(Finding("invalid_yaml", str(exc), str(artifact_file)))
            continue
        findings.extend(schema_findings(artifact, "artifact-schema.json", str(artifact_file)))
        if not isinstance(artifact, dict):
            findings.append(Finding("artifact_type", "artifact YAML must be a mapping", str(artifact_file)))
            continue
        findings.extend(artifact_header_matches(index_item, artifact))
        findings.extend(check_raw_data_safety(artifact, str(artifact_file)))
        findings.extend(check_metrics(artifact, str(artifact_file)))
        artifacts.append(artifact)
    known_ids = {artifact.get("id") for artifact in artifacts}
    for artifact in artifacts:
        for dependency in artifact.get("depends_on", []):
            if dependency not in known_ids:
                findings.append(Finding("unknown_dependency", f"artifact depends_on unknown id {dependency!r}", artifact.get("id", "")))
        supersedes = artifact.get("supersedes")
        if supersedes is not None and supersedes not in known_ids:
            findings.append(Finding("unknown_supersedes", f"artifact supersedes unknown id {supersedes!r}", artifact.get("id", "")))
        if artifact.get("type") in {"source", "evidence", "claim"} and artifact.get("manuscript_eligibility") == "claim_eligible":
            if artifact.get("verification_status") != "human_verified":
                findings.append(Finding("unverified_claim_evidence", "claim-eligible source/evidence/claim requires human_verified status", artifact.get("id", "")))
        if artifact.get("provenance") == "project_generated" and artifact.get("manuscript_eligibility") == "claim_eligible":
            findings.append(Finding("self_verified_generation", "project-generated artifacts cannot make themselves claim-eligible", artifact.get("id", "")))
    for override in project.get("user_overrides", []):
        if isinstance(override, dict) and override.get("target_artifact_id") not in known_ids:
            findings.append(Finding("override_target", "user override must target an indexed artifact", override.get("id", "")))
        elif isinstance(override, dict):
            by_id = {artifact.get("id"): artifact for artifact in artifacts}
            for downstream_id in downstream_artifact_ids(artifacts, override["target_artifact_id"]):
                if by_id[downstream_id].get("status") != "advisory_only":
                    findings.append(Finding("override_not_propagated", "artifacts downstream of a user override must be advisory_only", downstream_id))
    findings.extend(required_gate_findings(project.get("current_state", ""), artifacts))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Research Skill Pack project without reading raw data.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate <project-root>")
    validate_parser.add_argument("project_root", type=Path)
    validate_parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    transition_parser = subparsers.add_parser("transition", help="validate a state transition")
    transition_parser.add_argument("current")
    transition_parser.add_argument("target")
    transition_parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    args = parser.parse_args(argv)
    findings = validate_project(args.project_root) if args.command == "validate" else transition_findings(args.current, args.target)
    if args.json:
        print(json.dumps({"valid": not findings, "findings": [item.as_dict() for item in findings]}, ensure_ascii=False, indent=2))
    elif findings:
        for finding in findings:
            detail = f" [{finding.path}]" if finding.path else ""
            print(f"ERROR {finding.code}{detail}: {finding.message}")
    else:
        print("VALID")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
