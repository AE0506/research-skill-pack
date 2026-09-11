#!/usr/bin/env python3
"""Audit a deidentified, local-only Beta pilot without publishing project content.

The auditor reads only local project metadata.  It never follows raw-data paths,
contacts a provider, calls a model, or writes into the project being audited.
Its optional report intentionally contains only artifact identifiers, statuses,
hashes, command exit codes, and month-level confirmation timestamps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import research_contract
import research_state


REQUIRED_STEPS = {
    "constraints_capture",
    "context_brief",
    "timeline_baseline",
    "gap_card",
    "review_board",
    "review_board_confirmation",
}
REQUIRED_ARTIFACTS = {
    "context_brief": "confirmed",
    "timeline_baseline": "confirmed",
    "gap_card": None,
    "board_decision": "confirmed",
}
ATTESTATION_KEYS = {
    "schema_version",
    "authorization",
    "deidentification",
    "public_report_consent",
    "pilot_steps",
    "commands",
    "human_confirmations",
}
COMMAND_KEYS = {"name", "exit_code"}
CONFIRMATION_KEYS = {"artifact_id", "confirmed_at"}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(str(exc)) from exc


def _month(value: Any) -> str | None:
    return value[:7] if isinstance(value, str) and len(value) >= 7 else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _attestation_findings(attestation: Any) -> list[Finding]:
    if not isinstance(attestation, dict):
        return [Finding("invalid_attestation", "attestation must be a YAML mapping")]
    findings: list[Finding] = []
    unexpected = sorted(set(attestation) - ATTESTATION_KEYS)
    if unexpected:
        findings.append(Finding("sensitive_attestation_field", f"attestation may not include unredacted fields: {', '.join(unexpected)}"))
    for key in ("authorization", "deidentification", "public_report_consent"):
        if attestation.get(key) != "confirmed":
            findings.append(Finding(f"{key}_missing", f"{key} must be confirmed"))
    steps = attestation.get("pilot_steps")
    if not isinstance(steps, list) or not all(isinstance(step, str) for step in steps):
        findings.append(Finding("invalid_pilot_steps", "pilot_steps must be a list of step names"))
    else:
        missing_steps = sorted(REQUIRED_STEPS - set(steps))
        if missing_steps:
            findings.append(Finding("missing_pilot_steps", f"pilot record is missing steps: {', '.join(missing_steps)}"))
    commands = attestation.get("commands")
    if not isinstance(commands, list) or not commands:
        findings.append(Finding("missing_command_evidence", "commands must record local validation exit codes"))
    else:
        for command in commands:
            if not isinstance(command, dict) or set(command) - COMMAND_KEYS:
                findings.append(Finding("sensitive_command_evidence", "command evidence may contain only name and exit_code"))
                continue
            if not isinstance(command.get("name"), str) or command.get("exit_code") != 0:
                findings.append(Finding("failed_command_evidence", "each recorded validation command must have exit_code 0"))
    confirmations = attestation.get("human_confirmations")
    if not isinstance(confirmations, list) or not confirmations:
        findings.append(Finding("missing_human_confirmation", "human_confirmations must record at least one confirmed artifact"))
    else:
        for confirmation in confirmations:
            if not isinstance(confirmation, dict) or set(confirmation) - CONFIRMATION_KEYS:
                findings.append(Finding("sensitive_confirmation_evidence", "confirmation entries may contain only artifact_id and confirmed_at"))
                continue
            if not isinstance(confirmation.get("artifact_id"), str) or not _month(confirmation.get("confirmed_at")):
                findings.append(Finding("invalid_human_confirmation", "confirmation requires artifact_id and a timestamp"))
    return findings


def audit_pilot(project_root: Path, attestation_path: Path) -> tuple[dict[str, Any], list[Finding]]:
    """Return a redacted report and its findings; never mutate the pilot project."""
    findings: list[Finding] = []
    try:
        attestation = _load_yaml(attestation_path)
    except ValueError as exc:
        attestation = {}
        findings.append(Finding("invalid_attestation", str(exc)))
    findings.extend(_attestation_findings(attestation))
    contract_findings = research_contract.validate_project(project_root)
    findings.extend(Finding(f"contract_{item.code}", item.message) for item in contract_findings)
    receipts, receipt_findings = research_state.validate_receipt_chain(project_root)
    findings.extend(Finding(f"receipt_{item['code']}", item["message"]) for item in receipt_findings)

    project_path = project_root / ".research/project.yaml"
    artifacts: list[dict[str, Any]] = []
    if project_path.is_file():
        try:
            project = research_contract.load_yaml(project_path)
        except ValueError as exc:
            project = {}
            findings.append(Finding("invalid_project", str(exc)))
        if isinstance(project, dict):
            for index_entry in project.get("artifact_index", []):
                if not isinstance(index_entry, dict):
                    continue
                relative_path = index_entry.get("path")
                if not isinstance(relative_path, str) or not research_contract.is_safe_artifact_path(relative_path):
                    continue
                artifact_path = project_root / ".research" / relative_path
                if not artifact_path.is_file():
                    continue
                try:
                    artifact = research_contract.load_yaml(artifact_path)
                except ValueError:
                    continue
                if not isinstance(artifact, dict):
                    continue
                artifacts.append({
                    "id": artifact.get("id"),
                    "type": artifact.get("type"),
                    "status": artifact.get("status"),
                    "depends_on": artifact.get("depends_on", []),
                    "confirmation_month": _month(artifact.get("confirmation", {}).get("confirmed_at")) if isinstance(artifact.get("confirmation"), dict) else None,
                    "sha256": _sha256(artifact_path),
                })
    else:
        findings.append(Finding("missing_project", "missing .research/project.yaml"))

    for artifact_type, required_status in REQUIRED_ARTIFACTS.items():
        matches = [artifact for artifact in artifacts if artifact.get("type") == artifact_type]
        if not matches or (required_status and not any(artifact.get("status") == required_status for artifact in matches)):
            findings.append(Finding("missing_required_artifact", f"pilot requires a{(' ' + required_status) if required_status else ''} {artifact_type} artifact"))
    confirmed_ids = {
        entry.get("artifact_id")
        for entry in attestation.get("human_confirmations", [])
        if isinstance(entry, dict) and isinstance(entry.get("artifact_id"), str)
    }
    actual_confirmed_ids = {artifact["id"] for artifact in artifacts if artifact.get("confirmation_month")}
    if not confirmed_ids.intersection(actual_confirmed_ids):
        findings.append(Finding("confirmation_not_traceable", "at least one attested confirmation must match a confirmed project artifact"))

    if not receipts:
        findings.append(Finding("missing_receipt_chain", "pilot requires MCP receipts for its canonical workflow"))
    receipt_artifact_ids = {
        receipt.get("artifact", {}).get("id")
        for receipt in receipts
        if isinstance(receipt.get("artifact"), dict) and isinstance(receipt["artifact"].get("id"), str)
    }
    required_artifact_ids = {
        artifact["id"]
        for artifact in artifacts
        if artifact.get("type") in REQUIRED_ARTIFACTS
    }
    missing_receipts = sorted(required_artifact_ids - receipt_artifact_ids)
    if missing_receipts:
        findings.append(Finding("missing_artifact_receipt", f"pilot required artifacts lack MCP receipts: {', '.join(missing_receipts)}"))

    command_evidence = [
        {"name": entry.get("name"), "exit_code": entry.get("exit_code")}
        for entry in attestation.get("commands", [])
        if isinstance(entry, dict) and set(entry).issubset(COMMAND_KEYS)
    ]
    confirmation_evidence = [
        {"artifact_id": entry.get("artifact_id"), "confirmed_month": _month(entry.get("confirmed_at"))}
        for entry in attestation.get("human_confirmations", [])
        if isinstance(entry, dict) and set(entry).issubset(CONFIRMATION_KEYS)
    ]
    receipt_evidence = [
        {
            "receipt_id": receipt.get("receipt_id"),
            "artifact_id": receipt.get("artifact", {}).get("id") if isinstance(receipt.get("artifact"), dict) else None,
            "origin_skill_id": receipt.get("origin_skill_id"),
            "mutation_revision": receipt.get("mutation_revision"),
        }
        for receipt in receipts
    ]
    report = {
        "report_schema_version": "0.2",
        "status": "completed_limited" if not findings else "blocked",
        "redacted": True,
        "scope": "One local, deidentified workflow audit. It does not verify research results, external source truth, or LLM response quality.",
        "artifacts": artifacts,
        "command_evidence": command_evidence,
        "human_confirmations": confirmation_evidence,
        "receipts": receipt_evidence,
        "finding_codes": sorted({finding.code for finding in findings}),
    }
    return report, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a deidentified Beta pilot without reading raw-data paths or contacting external systems.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--attestation", type=Path, required=True, help="deidentified YAML attestation outside the repository")
    parser.add_argument("--report", type=Path, required=True, help="new path for the redacted report")
    parser.add_argument("--json", action="store_true", help="also print the redacted report")
    args = parser.parse_args(argv)
    if args.report.exists():
        parser.error("--report must name a new file; existing reports are never overwritten")
    report, findings = audit_pilot(args.project_root, args.attestation)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status'].upper()}: wrote redacted report to {args.report}")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
