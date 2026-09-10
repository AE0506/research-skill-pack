from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
import research_contract as contract  # noqa: E402


FIXTURE = PLUGIN_ROOT / "fixtures" / "valid-project"


def copied_project(tmp_path: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(FIXTURE, destination)
    return destination


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, content: dict) -> None:
    path.write_text(yaml.safe_dump(content, allow_unicode=True, sort_keys=False), encoding="utf-8")


def finding_codes(project: Path) -> set[str]:
    return {finding.code for finding in contract.validate_project(project)}


def test_valid_synthetic_project_passes_without_reading_raw_data(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    assert contract.validate_project(project) == []


def test_confirmed_intake_requires_confirmed_context_brief(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    context = project / ".research/artifacts/context-brief-001.yaml"
    content = load_yaml(context)
    content["status"] = "draft"
    write_yaml(context, content)
    assert "index_mismatch" in finding_codes(project)
    assert "unconfirmed_gate" in finding_codes(project)


def test_claim_eligibility_requires_human_verification(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    context = project / ".research/artifacts/context-brief-001.yaml"
    content = load_yaml(context)
    content["type"] = "evidence"
    content["manuscript_eligibility"] = "claim_eligible"
    content["verification_status"] = "ai_extracted"
    write_yaml(context, content)
    project_file = project / ".research/project.yaml"
    manifest = load_yaml(project_file)
    manifest["artifact_index"][0]["type"] = "evidence"
    write_yaml(project_file, manifest)
    assert "unverified_claim_evidence" in finding_codes(project)


def test_raw_data_register_rejects_embedded_records(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    raw = project / ".research/artifacts/raw-register-001.yaml"
    content = load_yaml(raw)
    content["raw_data"]["records"] = [{"participant_id": "p-1"}]
    write_yaml(raw, content)
    codes = finding_codes(project)
    assert "schema" in codes
    assert "raw_data_exposure" in codes


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    project_file = project / ".research/project.yaml"
    manifest = load_yaml(project_file)
    manifest["artifact_index"][0]["path"] = "artifacts/../../outside.yaml"
    write_yaml(project_file, manifest)
    assert "unsafe_artifact_path" in finding_codes(project)


def test_design_state_requires_protocol(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    project_file = project / ".research/project.yaml"
    manifest = load_yaml(project_file)
    manifest["current_state"] = "design_ready"
    manifest["write_sequence"] = 2
    manifest["state_history"].append({
        "sequence": 2,
        "state": "design_ready",
        "at": "2026-09-10T09:00:00Z",
        "changed_by": "skill",
        "reason": "测试状态闸门",
    })
    write_yaml(project_file, manifest)
    assert "missing_gate_artifact" in finding_codes(project)


def test_state_transition_rules_prevent_skipping_and_kill_resume() -> None:
    assert {item.code for item in contract.transition_findings("intake_confirmed", "gap_ready")} == {"illegal_transition"}
    assert {item.code for item in contract.transition_findings("KILL", "intake_draft")} == {"illegal_transition"}
    assert contract.transition_findings("PIVOT", "gap_ready") == []


def test_metric_requires_evidence_for_real_rating(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    context = project / ".research/artifacts/context-brief-001.yaml"
    content = load_yaml(context)
    content["metric"] = {"name": "Field Sweet Spot", "rating": "High", "evidence_ids": []}
    write_yaml(context, content)
    assert "metric_evidence" in finding_codes(project)


def test_growth_momentum_requires_two_qualified_windows(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    context = project / ".research/artifacts/context-brief-001.yaml"
    content = load_yaml(context)
    content["metric"] = {
        "name": "Growth Momentum",
        "rating": "High",
        "evidence_ids": ["context-brief-001"],
        "windows": [{"months": 24, "independent_record_count": 4}],
    }
    write_yaml(context, content)
    assert "growth_momentum_windows" in finding_codes(project)


def test_user_override_marks_dependent_artifacts_advisory_only(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    project_file = project / ".research/project.yaml"
    manifest = load_yaml(project_file)
    manifest["user_overrides"] = [{
        "id": "override-001",
        "at": "2026-09-10T08:40:00Z",
        "reason": "用户决定保留另一个研究方向",
        "target_artifact_id": "context-brief-001",
        "effect": "downstream_advisory_only",
    }]
    write_yaml(project_file, manifest)
    assert "override_not_propagated" in finding_codes(project)


def test_project_generated_artifact_cannot_self_authorize_claim(tmp_path: Path) -> None:
    project = copied_project(tmp_path)
    context = project / ".research/artifacts/context-brief-001.yaml"
    content = load_yaml(context)
    content["manuscript_eligibility"] = "claim_eligible"
    write_yaml(context, content)
    assert "self_verified_generation" in finding_codes(project)
