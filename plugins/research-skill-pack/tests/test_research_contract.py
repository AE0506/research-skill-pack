from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
import research_contract as contract  # noqa: E402
import validate_plugin  # noqa: E402


FIXTURE = PLUGIN_ROOT / "fixtures" / "valid-project"
V02_FIXTURE = PLUGIN_ROOT / "fixtures" / "v0.2-project"
PORTFOLIO_FIXTURE = PLUGIN_ROOT / "fixtures" / "portfolio.yaml"


def copied_project(tmp_path: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(FIXTURE, destination)
    return destination


def copied_v02_project(tmp_path: Path) -> Path:
    destination = tmp_path / "v02-project"
    shutil.copytree(V02_FIXTURE, destination)
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


def test_valid_v02_project_has_confirmed_execution_timeline(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    assert contract.validate_project(project) == []


def test_v02_intake_requires_a_confirmed_timeline_baseline(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    manifest["current_state"] = "intake_confirmed"
    manifest["write_sequence"] = 1
    manifest["state_history"] = manifest["state_history"][:2]
    manifest["artifact_index"] = [item for item in manifest["artifact_index"] if item["type"] != "timeline_baseline"]
    write_yaml(manifest_path, manifest)
    assert "missing_gate_artifact" in finding_codes(project)


def test_confirmed_timeline_requires_direct_user_confirmation(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    timeline = project / ".research/artifacts/execution-timeline-001.yaml"
    content = load_yaml(timeline)
    content.pop("confirmation")
    write_yaml(timeline, content)
    assert "missing_user_confirmation" in finding_codes(project)


def test_rebaseline_must_supersede_an_earlier_timeline(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    timeline = project / ".research/artifacts/execution-timeline-001.yaml"
    content = load_yaml(timeline)
    content["type"] = "timeline_rebaseline"
    content["supersedes"] = None
    write_yaml(timeline, content)
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    manifest["artifact_index"][-1]["type"] = "timeline_rebaseline"
    manifest["artifact_index"][-1]["supersedes"] = None
    write_yaml(manifest_path, manifest)
    assert "invalid_rebaseline" in finding_codes(project)


def test_progress_checkin_requires_an_actual_checkin_timestamp(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    artifact = {
        "schema_version": "0.2", "id": "progress-checkin-001", "type": "progress_checkin", "version": 1,
        "created_at": "2026-09-13T08:00:00Z", "created_by": "user", "status": "draft",
        "depends_on": ["execution-timeline-001"], "supersedes": None, "change_reason": "记录本周实际进度",
        "provenance": "user_supplied", "verification_status": "unreviewed", "manuscript_eligibility": "not_eligible",
        "timeline": {"health": "at_risk"},
    }
    artifact_path = project / ".research/artifacts/progress-checkin-001.yaml"
    write_yaml(artifact_path, artifact)
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    manifest["artifact_index"].append({key: artifact[key] for key in ("id", "type", "version", "status", "created_at", "created_by", "depends_on", "supersedes", "change_reason")} | {"path": "artifacts/progress-checkin-001.yaml"})
    write_yaml(manifest_path, manifest)
    assert "progress_checkin_incomplete" in finding_codes(project)


def test_submission_gate_requires_human_checked_ready_report(tmp_path: Path) -> None:
    project = copied_v02_project(tmp_path)
    package = {
        "schema_version": "0.2", "id": "submission-package-001", "type": "submission_package", "version": 1,
        "created_at": "2027-04-20T08:00:00Z", "created_by": "skill", "status": "confirmed",
        "depends_on": [], "supersedes": None, "change_reason": "提交前版本打包",
        "provenance": "project_generated", "verification_status": "human_verified", "manuscript_eligibility": "not_eligible",
        "confirmation": {"confirmed_by": "user", "confirmed_at": "2027-04-20T08:05:00Z"},
    }
    readiness = {
        "schema_version": "0.2", "id": "deadline-readiness-001", "type": "deadline_readiness_report", "version": 1,
        "created_at": "2027-04-20T08:10:00Z", "created_by": "skill", "status": "verified",
        "depends_on": ["submission-package-001"], "supersedes": None, "change_reason": "提交前完整性检查",
        "provenance": "project_generated", "verification_status": "human_verified", "manuscript_eligibility": "not_eligible",
        "timeline": {"ready_for_submission": False, "health": "at_risk"},
    }
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    for artifact in (package, readiness):
        path = project / f".research/artifacts/{artifact['id']}.yaml"
        write_yaml(path, artifact)
        manifest["artifact_index"].append({key: artifact[key] for key in ("id", "type", "version", "status", "created_at", "created_by", "depends_on", "supersedes", "change_reason")} | {"path": f"artifacts/{artifact['id']}.yaml"})
    manifest["current_state"] = "submission_ready"
    manifest["write_sequence"] = 6
    manifest["state_history"].append({"sequence": 6, "state": "submission_ready", "at": "2027-04-20T08:20:00Z", "changed_by": "user", "reason": "测试提交闸门"})
    write_yaml(manifest_path, manifest)
    codes = finding_codes(project)
    assert "deadline_not_ready" in codes


def test_v01_migration_is_metadata_only_and_requires_new_baseline(tmp_path: Path) -> None:
    source = copied_project(tmp_path)
    raw_dir = source / ".research/data"
    raw_dir.mkdir()
    (raw_dir / "never-copy.csv").write_text("secret", encoding="utf-8")
    target = tmp_path / "migrated"
    assert contract.migrate_v01_project(source, target, "2026-09-13T08:00:00Z") == []
    migrated = load_yaml(target / ".research/project.yaml")
    assert migrated["schema_version"] == "0.2"
    assert migrated["migration"]["migration_status"] == "needs_timeline_baseline"
    assert migrated["migration"]["prior_current_state"] == "intake_confirmed"
    assert migrated["current_state"] == "blocked"
    assert not (target / ".research/data").exists()
    assert contract.validate_project(target) == []


def test_portfolio_is_metadata_only_and_rejects_raw_content(tmp_path: Path) -> None:
    portfolio = tmp_path / "portfolio.yaml"
    shutil.copy2(PORTFOLIO_FIXTURE, portfolio)
    assert contract.validate_portfolio(portfolio) == []
    content = load_yaml(portfolio)
    content["projects"][0]["raw_data"] = "forbidden"
    write_yaml(portfolio, content)
    assert "schema" in {item.code for item in contract.validate_portfolio(portfolio)}


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


def test_plugin_package_structure_and_synthetic_fixtures_validate() -> None:
    assert validate_plugin.validate_plugin() == []


def test_plugin_validator_rejects_missing_skill_front_matter(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    (plugin_root / "skills/research-radar/SKILL.md").write_text("# missing metadata\n", encoding="utf-8")
    assert "invalid_skill_front_matter" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}
