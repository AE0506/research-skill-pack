#!/usr/bin/env python3
"""Validate and safely migrate local Research Skill Pack project metadata.

Validation never contacts providers, reads registered raw-data paths, or mutates
a project. Migration creates a separate metadata-only v0.2 copy and deliberately
does not copy ``.research/data`` or any raw data.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
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
V01_GATES: dict[str, tuple[tuple[str, str | None], ...]] = {
    "intake_confirmed": (("context_brief", "confirmed"),),
    "topic_assessed": (("topic_assessment", None),),
    "gap_ready": (("gap_card", None),),
    "board_decided": (("board_decision", "confirmed"),),
    "design_ready": (("research_protocol", None),),
    "evidence_ready": (("verified_evidence_package", "verified"),),
    "blueprint_ready": (("manuscript_blueprint", None),),
    "manuscript_audited": (("citation_audit", None), ("originality_report", None)),
    "review_ready": (("review_report", None),),
    "venue_ready": (("venue_assessment", None),),
    "submission_ready": (("submission_package", "confirmed"),),
    "archived": (("archive_manifest", None),),
}
V02_GATES = {
    **V01_GATES,
    "intake_confirmed": (("context_brief", "confirmed"), ("timeline_baseline", "confirmed")),
    "design_ready": (("research_protocol", None), ("execution_timeline", "confirmed")),
    "submission_ready": (("submission_package", "confirmed"), ("deadline_readiness_report", "verified")),
}
CONFIRMATION_TYPES = {"context_brief", "timeline_baseline", "execution_timeline", "timeline_rebaseline", "board_decision", "submission_package"}
TIMELINE_TYPES = {"timeline_baseline", "execution_timeline", "timeline_rebaseline"}


class ContractLoader(yaml.SafeLoader):
    """Safe YAML loader that keeps ISO date/time values as strings."""


ContractLoader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, resolvers in list(ContractLoader.yaml_implicit_resolvers.items()):
    ContractLoader.yaml_implicit_resolvers[key] = [item for item in resolvers if item[0] != "tag:yaml.org,2002:timestamp"]


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


def dump_yaml(path: Path, value: Any) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


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


def _matches(artifacts: list[dict[str, Any]], artifact_type: str, status: str | None) -> list[dict[str, Any]]:
    return [artifact for artifact in artifacts if artifact.get("type") == artifact_type and (status is None or artifact.get("status") == status)]


def _legacy_timeline_pending(project: dict[str, Any]) -> bool:
    migration = project.get("migration")
    return isinstance(migration, dict) and migration.get("migration_status") == "needs_timeline_baseline"


def required_gate_findings(project: dict[str, Any], artifacts: list[dict[str, Any]]) -> list[Finding]:
    state = project.get("current_state", "")
    schema_version = project.get("schema_version")
    gates = V02_GATES if schema_version == "0.2" else V01_GATES
    requirements = gates.get(state, ())
    findings: list[Finding] = []
    for artifact_type, required_status in requirements:
        if artifact_type == "timeline_baseline" and _legacy_timeline_pending(project):
            continue
        matches = _matches(artifacts, artifact_type, required_status)
        if not matches and required_status and _matches(artifacts, artifact_type, None):
            findings.append(Finding("unconfirmed_gate", f"state {state} requires a {required_status} {artifact_type}"))
        elif not matches:
            status_text = f" {required_status}" if required_status else ""
            findings.append(Finding("missing_gate_artifact", f"state {state} requires a{status_text} {artifact_type} artifact"))
    if state == "board_decided":
        decisions = [artifact.get("decision") for artifact in _matches(artifacts, "board_decision", "confirmed")]
        if not any(decision in {"GO", "CONDITIONAL_GO"} for decision in decisions):
            findings.append(Finding("board_not_approved", "design is blocked until a confirmed GO or CONDITIONAL_GO decision"))
    if state == "submission_ready":
        reports = _matches(artifacts, "deadline_readiness_report", "verified")
        if reports and not any(
            report.get("timeline", {}).get("ready_for_submission") is True
            and report.get("verification_status") == "human_verified"
            for report in reports
        ):
            findings.append(Finding("deadline_not_ready", "submission_ready requires a human-verified readiness report with ready_for_submission: true"))
    return findings


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
        if not isinstance(windows, list) or len(windows) != 2 or any(not isinstance(window, dict) or window.get("months") != 24 or not isinstance(window.get("independent_record_count"), int) or window["independent_record_count"] < 5 for window in windows):
            return [Finding("growth_momentum_windows", "Growth Momentum needs two adjacent 24-month windows with at least five dated independent records each", artifact_path)]
    if name == "Semantic Repetition Rate" and rating != "insufficient_evidence":
        if not isinstance(metric.get("independent_record_count"), int) or metric["independent_record_count"] < 20:
            return [Finding("srr_minimum_records", "SRR needs at least 20 independent records before calculation", artifact_path)]
    if name == "Citation Coverage":
        needed, fully_supported = metric.get("citation_needed_claims"), metric.get("fully_supported_claims")
        if not isinstance(needed, int) or not isinstance(fully_supported, int) or needed < 0 or fully_supported < 0 or fully_supported > needed:
            return [Finding("citation_coverage_counts", "Citation Coverage requires non-negative supported and needed claim counts", artifact_path)]
    return []


def downstream_artifact_ids(artifacts: list[dict[str, Any]], root_id: str) -> set[str]:
    dependants: dict[str, set[str]] = {}
    for artifact in artifacts:
        for dependency in artifact.get("depends_on", []):
            dependants.setdefault(dependency, set()).add(artifact.get("id", ""))
    pending, result = list(dependants.get(root_id, set())), set()
    while pending:
        current = pending.pop()
        if current not in result:
            result.add(current)
            pending.extend(dependants.get(current, set()))
    return result


def check_confirmation(artifact: dict[str, Any], artifact_path: str) -> list[Finding]:
    if artifact.get("type") not in CONFIRMATION_TYPES or artifact.get("status") != "confirmed":
        return []
    confirmation = artifact.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("confirmed_by") != "user" or not confirmation.get("confirmed_at"):
        return [Finding("missing_user_confirmation", "confirmed artifact requires a direct user confirmation record", artifact_path)]
    return []


def check_timeline_artifact(artifact: dict[str, Any], artifact_path: str, known: dict[str, dict[str, Any]]) -> list[Finding]:
    artifact_type = artifact.get("type")
    if artifact_type not in {"timeline_baseline", "execution_timeline", "progress_checkin", "timeline_rebaseline", "deadline_readiness_report"}:
        return []
    timeline = artifact.get("timeline")
    if not isinstance(timeline, dict):
        return [Finding("timeline_missing", f"{artifact_type} requires a timeline object", artifact_path)]
    findings: list[Finding] = []
    if artifact_type == "timeline_baseline":
        if not timeline.get("final_submission_date") or not timeline.get("hard_deadlines") or not timeline.get("weekly_capacity_hours"):
            findings.append(Finding("timeline_baseline_incomplete", "timeline_baseline needs final submission, hard deadlines, and weekly capacity", artifact_path))
        elif not any(deadline.get("kind") == "final_submission" for deadline in timeline.get("hard_deadlines", []) if isinstance(deadline, dict)):
            findings.append(Finding("timeline_final_deadline", "timeline_baseline hard deadlines must include final_submission", artifact_path))
    if artifact_type == "execution_timeline" and not timeline.get("milestones"):
        findings.append(Finding("execution_timeline_incomplete", "execution_timeline requires milestones", artifact_path))
    if artifact_type == "progress_checkin" and not timeline.get("checkin_at"):
        findings.append(Finding("progress_checkin_incomplete", "progress_checkin requires timeline.checkin_at", artifact_path))
    if artifact_type == "timeline_rebaseline":
        predecessor = artifact.get("supersedes")
        previous = known.get(predecessor) if isinstance(predecessor, str) else None
        if not previous or previous.get("type") not in TIMELINE_TYPES:
            findings.append(Finding("invalid_rebaseline", "timeline_rebaseline must supersede a timeline baseline or execution timeline", artifact_path))
    if artifact_type == "deadline_readiness_report" and artifact.get("status") == "verified" and timeline.get("ready_for_submission") is not True:
        findings.append(Finding("deadline_not_ready", "a verified deadline readiness report must explicitly set ready_for_submission: true", artifact_path))
    return findings


def validate_project(project_root: Path) -> list[Finding]:
    research_root, project_path = project_root / RESEARCH_DIR, project_root / RESEARCH_DIR / "project.yaml"
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
        findings.extend(check_confirmation(artifact, str(artifact_file)))
        artifacts.append(artifact)
    known = {artifact.get("id"): artifact for artifact in artifacts}
    for artifact in artifacts:
        for dependency in artifact.get("depends_on", []):
            if dependency not in known:
                findings.append(Finding("unknown_dependency", f"artifact depends_on unknown id {dependency!r}", artifact.get("id", "")))
        supersedes = artifact.get("supersedes")
        if supersedes is not None and supersedes not in known:
            findings.append(Finding("unknown_supersedes", f"artifact supersedes unknown id {supersedes!r}", artifact.get("id", "")))
        findings.extend(check_timeline_artifact(artifact, artifact.get("id", ""), known))
        if artifact.get("type") in {"source", "evidence", "claim"} and artifact.get("manuscript_eligibility") == "claim_eligible" and artifact.get("verification_status") != "human_verified":
            findings.append(Finding("unverified_claim_evidence", "claim-eligible source/evidence/claim requires human_verified status", artifact.get("id", "")))
        if artifact.get("provenance") == "project_generated" and artifact.get("manuscript_eligibility") == "claim_eligible":
            findings.append(Finding("self_verified_generation", "project-generated artifacts cannot make themselves claim-eligible", artifact.get("id", "")))
    timeline_meta = project.get("timeline", {})
    if project.get("schema_version") == "0.2" and isinstance(timeline_meta, dict):
        active_id = timeline_meta.get("active_timeline_artifact_id")
        if active_id is not None and (active_id not in known or known[active_id].get("type") not in TIMELINE_TYPES):
            findings.append(Finding("invalid_active_timeline", "active_timeline_artifact_id must reference an indexed timeline artifact"))
        if timeline_meta.get("contract_status") == "execution_active" and not _matches(artifacts, "execution_timeline", "confirmed") and not _matches(artifacts, "timeline_rebaseline", "confirmed"):
            findings.append(Finding("missing_execution_timeline", "execution_active requires a confirmed execution timeline or confirmed rebaseline"))
    for override in project.get("user_overrides", []):
        if isinstance(override, dict) and override.get("target_artifact_id") not in known:
            findings.append(Finding("override_target", "user override must target an indexed artifact", override.get("id", "")))
        elif isinstance(override, dict):
            for downstream_id in downstream_artifact_ids(artifacts, override["target_artifact_id"]):
                if known[downstream_id].get("status") != "advisory_only":
                    findings.append(Finding("override_not_propagated", "artifacts downstream of a user override must be advisory_only", downstream_id))
    findings.extend(required_gate_findings(project, artifacts))
    return findings


def validate_portfolio(portfolio_path: Path) -> list[Finding]:
    try:
        portfolio = load_yaml(portfolio_path)
    except ValueError as exc:
        return [Finding("invalid_yaml", str(exc), str(portfolio_path))]
    findings = schema_findings(portfolio, "portfolio-schema.json", str(portfolio_path))
    if not isinstance(portfolio, dict):
        return findings + [Finding("portfolio_type", "portfolio must be a mapping", str(portfolio_path))]
    project_ids = [entry.get("project_id") for entry in portfolio.get("projects", []) if isinstance(entry, dict)]
    if len(project_ids) != len(set(project_ids)):
        findings.append(Finding("duplicate_portfolio_project", "portfolio project_id values must be unique", str(portfolio_path)))
    return findings


def migrate_v01_project(source_root: Path, output_root: Path, migrated_at: str | None = None) -> list[Finding]:
    """Create a metadata-only v0.2 copy; source remains untouched."""
    findings = validate_project(source_root)
    if findings:
        return [Finding("migration_source_invalid", "source project must validate before migration")] + findings
    source_project = load_yaml(source_root / RESEARCH_DIR / "project.yaml")
    if source_project.get("schema_version") != "0.1":
        return [Finding("migration_source_version", "only a v0.1 project can be migrated")]
    if output_root.exists():
        return [Finding("migration_output_exists", "migration output directory must not already exist", str(output_root))]
    stamp = migrated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target_research = output_root / RESEARCH_DIR
    target_artifacts = target_research / "artifacts"
    target_artifacts.mkdir(parents=True)
    migrated = copy.deepcopy(source_project)
    prior_state = migrated["current_state"]
    migrated["schema_version"] = "0.2"
    migrated["timeline"] = {"contract_status": "needs_baseline", "last_checked_at": stamp, "active_timeline_artifact_id": None, "timeline_health": "unknown"}
    migrated["migration"] = {"source_schema_version": "0.1", "migrated_at": stamp, "migration_status": "needs_timeline_baseline", "prior_current_state": prior_state}
    migrated["mutation_revision"] = 0
    migrated["write_sequence"] = migrated.get("write_sequence", 0) + 1
    migrated["current_state"] = "blocked"
    migrated["state_history"].append({"sequence": migrated["write_sequence"], "state": "blocked", "at": stamp, "changed_by": "migration", "reason": "v0.2 requires a confirmed Timeline Baseline before work can continue"})
    dump_yaml(target_research / "project.yaml", migrated)
    for index_item in source_project.get("artifact_index", []):
        relative_path = index_item.get("path") if isinstance(index_item, dict) else None
        if not isinstance(relative_path, str) or not is_safe_artifact_path(relative_path):
            continue
        source_file = source_root / RESEARCH_DIR / relative_path
        target_file = target_research / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
    return []


def _print_findings(findings: list[Finding], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"valid": not findings, "findings": [item.as_dict() for item in findings]}, ensure_ascii=False, indent=2))
    elif findings:
        for finding in findings:
            detail = f" [{finding.path}]" if finding.path else ""
            print(f"ERROR {finding.code}{detail}: {finding.message}")
    else:
        print("VALID")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Research Skill Pack metadata without reading raw data.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate <project-root>")
    validate_parser.add_argument("project_root", type=Path)
    validate_parser.add_argument("--json", action="store_true")
    transition_parser = subparsers.add_parser("transition", help="validate a state transition")
    transition_parser.add_argument("current")
    transition_parser.add_argument("target")
    transition_parser.add_argument("--json", action="store_true")
    portfolio_parser = subparsers.add_parser("validate-portfolio", help="validate a metadata-only portfolio registry")
    portfolio_parser.add_argument("portfolio_path", type=Path)
    portfolio_parser.add_argument("--json", action="store_true")
    migration_parser = subparsers.add_parser("migrate", help="copy a v0.1 project metadata contract to a new v0.2 directory")
    migration_parser.add_argument("source_root", type=Path)
    migration_parser.add_argument("--output", type=Path, required=True)
    migration_parser.add_argument("--at", dest="migrated_at")
    migration_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "validate":
        findings = validate_project(args.project_root)
    elif args.command == "transition":
        findings = transition_findings(args.current, args.target)
    elif args.command == "validate-portfolio":
        findings = validate_portfolio(args.portfolio_path)
    else:
        findings = migrate_v01_project(args.source_root, args.output, args.migrated_at)
    _print_findings(findings, args.json)
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
