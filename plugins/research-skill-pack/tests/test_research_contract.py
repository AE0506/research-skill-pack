from __future__ import annotations

import shutil
import sys
import json
from pathlib import Path

import pytest
import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
import research_contract as contract  # noqa: E402
import validate_plugin  # noqa: E402
import pilot_audit  # noqa: E402
import research_state  # noqa: E402


FIXTURE = PLUGIN_ROOT / "fixtures" / "valid-project"
V02_FIXTURE = PLUGIN_ROOT / "fixtures" / "v0.2-project"
PORTFOLIO_FIXTURE = PLUGIN_ROOT / "fixtures" / "portfolio.yaml"


def catalog_records() -> list[dict]:
    catalog = load_yaml(PLUGIN_ROOT / "shared/skill-catalog-v0.2.yaml")
    return [skill for pack in catalog["packs"] for skill in pack["skills"]]


def verification_cases() -> list[dict]:
    return load_yaml(PLUGIN_ROOT / "shared/verification-matrix-v0.2.yaml")["cases"]


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


STRUCTURAL_SKILL_IDS = [
    case["skill_id"] for case in verification_cases() if case["kind"] == "structural"
]


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


def test_beta_profile_remains_explicitly_scoped() -> None:
    schema = json.loads((PLUGIN_ROOT / "shared/project-schema.json").read_text(encoding="utf-8"))
    registry = json.loads((PLUGIN_ROOT / "shared/profile-registry-v0.2.json").read_text(encoding="utf-8"))
    profile_ids = [profile["id"] for profile in registry["profiles"]]
    assert schema["properties"]["profile"]["enum"] == profile_ids
    assert profile_ids == ["zh-undergrad-information-management-empirical"]


@pytest.mark.parametrize("skill_id", STRUCTURAL_SKILL_IDS)
def test_catalog_skill_structural_contract(skill_id: str) -> None:
    skill = next(item for item in catalog_records() if item["id"] == skill_id)
    metadata = validate_plugin._front_matter(PLUGIN_ROOT / "skills" / skill_id / "SKILL.md")
    assert metadata is not None
    assert metadata["name"] == skill_id
    assert all(skill[key] for key in ("inputs", "outputs", "gates", "safety", "acceptance_ids"))
    assert skill["validation"]["level"] == "structural"
    assert skill["validation"]["refs"] == [f"STR-SKILL-{skill_id}"]


def test_verification_matrix_covers_every_acceptance_id_once() -> None:
    catalog_by_acceptance = {
        acceptance_id: skill["id"]
        for skill in catalog_records()
        for acceptance_id in skill["acceptance_ids"]
    }
    matrix = verification_cases()
    assert len(matrix) == 175
    assert {case["acceptance_id"] for case in matrix} == set(catalog_by_acceptance)
    assert len({case["verification_id"] for case in matrix}) == 175
    assert all(case["skill_id"] == catalog_by_acceptance[case["acceptance_id"]] for case in matrix)


def test_plugin_validator_rejects_missing_skill_front_matter(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    (plugin_root / "skills/research-radar/SKILL.md").write_text("# missing metadata\n", encoding="utf-8")
    assert "invalid_skill_front_matter" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_catalog_matches_every_installed_skill_and_preserves_legacy_design_ids() -> None:
    report = validate_plugin.catalog_report()
    assert report["catalog_skill_count"] == 175
    assert report["implemented_skill_count"] == 175
    assert report["legacy_design_id_count"] == 172
    assert report["bounded_workflow_skill_count"] == 31
    assert report["strict_match"] is True
    assert report["catalog_only"] == []
    assert report["implementation_only"] == []
    assert report["missing_legacy_mappings"] == []
    assert report["unexpected_legacy_mappings"] == []
    assert report["misdirected_legacy_mappings"] == []
    assert report["duplicate_legacy_mapping_targets"] == []


def test_every_installed_skill_has_an_operational_work_card() -> None:
    report = validate_plugin.skill_depth_report()
    assert report["skill_count"] == 175
    assert report["operational_skill_count"] == 175
    assert report["minimum_body_lines"] >= validate_plugin.MIN_OPERATIONAL_BODY_LINES
    assert validate_plugin.validate_skill_workflows() == []
    assert "not model adherence" in report["evidence_boundary"]


def test_plugin_validator_rejects_catalog_mapping_drift(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    mapping_path = plugin_root / "shared/legacy-skill-map-v0.2.yaml"
    mapping = load_yaml(mapping_path)
    mapping["legacy_to_canonical"].pop("analysis-run-register")
    write_yaml(mapping_path, mapping)
    assert "legacy_mapping_coverage" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_missing_catalog_validation_reference(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    catalog_path = plugin_root / "shared/skill-catalog-v0.2.yaml"
    catalog = load_yaml(catalog_path)
    catalog["packs"][0]["skills"][0].pop("validation")
    write_yaml(catalog_path, catalog)
    assert "catalog_validation_level" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_verification_matrix_coverage_gap(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    matrix_path = plugin_root / "shared/verification-matrix-v0.2.yaml"
    matrix = load_yaml(matrix_path)
    matrix["cases"].pop()
    write_yaml(matrix_path, matrix)
    assert "verification_matrix_missing_acceptance" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_stale_verification_test_reference(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    matrix_path = plugin_root / "shared/verification-matrix-v0.2.yaml"
    matrix = load_yaml(matrix_path)
    structural_case = next(case for case in matrix["cases"] if case["kind"] == "structural")
    structural_case["test_case"] = "test_that_does_not_exist"
    write_yaml(matrix_path, matrix)
    assert "verification_test_case_missing" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_profile_registry_schema_drift(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    schema_path = plugin_root / "shared/project-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["profile"]["enum"] = []
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    assert "profile_registry_schema_drift" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_incomplete_bounded_beta_workflow(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    skill_path = plugin_root / "skills/article-pattern-fit/SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace("## 安全边界", "## 约束"),
        encoding="utf-8",
    )
    assert "incomplete_beta_workflow" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_missing_operational_workflow_section(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    skill_path = plugin_root / "skills/topic-feasibility-analyzer/SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace("## 执行协议", "## 被删除的执行协议", 1),
        encoding="utf-8",
    )
    assert "incomplete_operational_workflow" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def test_plugin_validator_rejects_skill_work_card_that_omits_its_catalog_output(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    shutil.copytree(PLUGIN_ROOT, plugin_root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    skill_path = plugin_root / "skills/research-orchestrator/SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace("`route_advice`", "route advice"),
        encoding="utf-8",
    )
    assert "operational_workflow_contract_gap" in {item.code for item in validate_plugin.validate_plugin(plugin_root)}


def completed_pilot_attestation() -> dict:
    return {
        "schema_version": "0.2",
        "authorization": "confirmed",
        "deidentification": "confirmed",
        "public_report_consent": "confirmed",
        "pilot_steps": sorted(pilot_audit.REQUIRED_STEPS),
        "commands": [{"name": "research_contract_validate", "exit_code": 0}],
        "human_confirmations": [{"artifact_id": "context-brief-001", "confirmed_at": "2026-09-10T08:30:00Z"}],
    }


def pilot_project_with_gap_card(tmp_path: Path) -> Path:
    project = copied_v02_project(tmp_path)
    project_path = project / ".research/project.yaml"
    manifest = load_yaml(project_path)
    manifest.update({
        "current_state": "intake_draft",
        "write_sequence": 0,
        "mutation_revision": 0,
        "state_history": [manifest["state_history"][0]],
        "artifact_index": [],
        "timeline": {
            "contract_status": "needs_baseline",
            "last_checked_at": "2026-09-10T08:00:00Z",
            "active_timeline_artifact_id": None,
            "timeline_health": "unknown",
        },
    })
    write_yaml(project_path, manifest)
    for path in (project / ".research/artifacts").glob("*.yaml"):
        path.unlink()

    def artifact(artifact_id: str, artifact_type: str, *, status: str = "draft", depends_on: list[str] | None = None, **extra: object) -> dict:
        return {
            "schema_version": "0.2", "id": artifact_id, "type": artifact_type, "version": 1,
            "created_at": "2026-09-10T08:20:00Z", "created_by": "skill", "status": status,
            "depends_on": depends_on or [], "supersedes": None, "change_reason": "试跑审计测试",
            "provenance": "project_generated", "verification_status": "ai_extracted", "manuscript_eligibility": "not_eligible",
        } | extra

    def commit(request_id: str, revision: int, origin: str, artifact_value: dict | None = None, target: str | None = None) -> None:
        request: dict = {"request_id": request_id, "expected_mutation_revision": revision, "origin_skill_id": origin}
        if artifact_value is not None:
            request["artifact"] = artifact_value
        if target is not None:
            request.update({"target_state": target, "state_reason": "试跑状态迁移"})
        assert research_state.commit_canonical_change(project, request)["status"] == "committed"

    commit("pilot-context-001", 0, "context-brief-generator", artifact(
        "context-brief-001", "context_brief", status="confirmed",
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T08:30:00Z"},
    ))
    commit("pilot-timeline-001", 1, "timeline-baseline-builder", artifact(
        "timeline-baseline-001", "timeline_baseline", status="confirmed", depends_on=["context-brief-001"],
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T08:31:00Z"},
        timeline={
            "final_submission_date": "2026-12-20",
            "hard_deadlines": [{"id": "final-submission", "label": "最终提交", "date": "2026-12-20", "kind": "final_submission"}],
            "weekly_capacity_hours": 10,
        },
    ))
    commit("pilot-confirm-intake-001", 2, "context-confirmation-gate", target="intake_confirmed")
    commit("pilot-topic-001", 3, "topic-feasibility-analyzer", artifact(
        "topic-assessment-001", "topic_assessment", depends_on=["context-brief-001"],
    ), "topic_assessed")
    commit("pilot-gap-001", 4, "gap-card-builder", artifact(
        "gap-card-001", "gap_card", depends_on=["topic-assessment-001"],
    ), "gap_ready")
    commit("pilot-board-001", 5, "review-board-decision", artifact(
        "board-decision-001", "board_decision", status="confirmed", depends_on=["gap-card-001"], decision="GO",
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T10:00:00Z"},
    ), "board_decided")
    assert contract.validate_project(project) == []
    return project


def test_pilot_audit_outputs_only_redacted_completed_report(tmp_path: Path) -> None:
    project = pilot_project_with_gap_card(tmp_path)
    attestation_path = tmp_path / "attestation.yaml"
    write_yaml(attestation_path, completed_pilot_attestation())
    report, findings = pilot_audit.audit_pilot(project, attestation_path)
    assert findings == []
    assert report["status"] == "completed_limited"
    assert report["redacted"] is True
    assert "title" not in report
    assert len(report["receipts"]) == 6
    assert {artifact["type"] for artifact in report["artifacts"]}.issuperset({"context_brief", "timeline_baseline", "gap_card", "board_decision"})


def test_pilot_audit_blocks_sensitive_or_unconfirmed_attestation(tmp_path: Path) -> None:
    project = pilot_project_with_gap_card(tmp_path)
    attestation = completed_pilot_attestation() | {"title": "must not be published"}
    attestation["authorization"] = "not_confirmed"
    attestation_path = tmp_path / "attestation.yaml"
    write_yaml(attestation_path, attestation)
    report, findings = pilot_audit.audit_pilot(project, attestation_path)
    assert report["status"] == "blocked"
    assert {item.code for item in findings}.issuperset({"sensitive_attestation_field", "authorization_missing"})


def test_pilot_audit_blocks_a_required_artifact_without_a_receipt(tmp_path: Path) -> None:
    project = pilot_project_with_gap_card(tmp_path)
    (project / ".research/receipts/receipt-pilot-gap-001.json").unlink()
    attestation_path = tmp_path / "attestation.yaml"
    write_yaml(attestation_path, completed_pilot_attestation())
    report, findings = pilot_audit.audit_pilot(project, attestation_path)
    assert report["status"] == "blocked"
    assert {item.code for item in findings}.issuperset({"receipt_receipt_revision_gap", "missing_artifact_receipt"})


def test_pilot_audit_cli_writes_new_redacted_report(tmp_path: Path) -> None:
    project = pilot_project_with_gap_card(tmp_path)
    attestation_path = tmp_path / "attestation.yaml"
    report_path = tmp_path / "redacted-report.yaml"
    write_yaml(attestation_path, completed_pilot_attestation())
    assert pilot_audit.main([str(project), "--attestation", str(attestation_path), "--report", str(report_path)]) == 0
    report = load_yaml(report_path)
    assert report["status"] == "completed_limited"
    assert report["redacted"] is True
