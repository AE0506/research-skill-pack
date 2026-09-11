from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
import research_contract as contract  # noqa: E402
import research_state  # noqa: E402
import validate_plugin  # noqa: E402


V02_FIXTURE = PLUGIN_ROOT / "fixtures" / "v0.2-project"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def empty_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    shutil.copytree(V02_FIXTURE, project)
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    manifest["current_state"] = "intake_draft"
    manifest["write_sequence"] = 0
    manifest["mutation_revision"] = 0
    manifest["state_history"] = [manifest["state_history"][0]]
    manifest["artifact_index"] = []
    manifest["timeline"] = {
        "contract_status": "needs_baseline",
        "last_checked_at": "2026-09-10T08:00:00Z",
        "active_timeline_artifact_id": None,
        "timeline_health": "unknown",
    }
    write_yaml(manifest_path, manifest)
    for path in (project / ".research/artifacts").glob("*.yaml"):
        path.unlink()
    assert contract.validate_project(project) == []
    return project


def artifact(artifact_id: str, artifact_type: str, *, status: str = "draft", depends_on: list[str] | None = None, **extra: object) -> dict:
    return {
        "schema_version": "0.2",
        "id": artifact_id,
        "type": artifact_type,
        "version": 1,
        "created_at": "2026-09-10T08:20:00Z",
        "created_by": "skill",
        "status": status,
        "depends_on": depends_on or [],
        "supersedes": None,
        "change_reason": "受控写入测试",
        "provenance": "project_generated",
        "verification_status": "ai_extracted",
        "manuscript_eligibility": "not_eligible",
    } | extra


def change(request_id: str, revision: int, origin: str, *, artifact_value: dict | None = None, target_state: str | None = None) -> dict:
    value: dict = {
        "request_id": request_id,
        "expected_mutation_revision": revision,
        "origin_skill_id": origin,
    }
    if artifact_value is not None:
        value["artifact"] = artifact_value
    if target_state is not None:
        value["target_state"] = target_state
        value["state_reason"] = "受控状态迁移测试"
    return value


def commit_context_and_timeline(project: Path) -> int:
    context = artifact(
        "context-brief-001", "context_brief", status="confirmed",
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T08:21:00Z"},
    )
    assert research_state.commit_canonical_change(project, change("context-write-001", 0, "context-brief-generator", artifact_value=context))["status"] == "committed"
    timeline = artifact(
        "timeline-baseline-001", "timeline_baseline", status="confirmed", depends_on=["context-brief-001"],
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T08:25:00Z"},
        timeline={
            "final_submission_date": "2026-12-20",
            "hard_deadlines": [{"id": "final-submission", "label": "最终提交", "date": "2026-12-20", "kind": "final_submission"}],
            "weekly_capacity_hours": 10,
        },
    )
    assert research_state.commit_canonical_change(project, change("timeline-write-001", 1, "timeline-baseline-builder", artifact_value=timeline))["status"] == "committed"
    return 2


def advance_to_board(project: Path) -> None:
    revision = commit_context_and_timeline(project)
    assert research_state.commit_canonical_change(project, change("confirm-intake-001", revision, "context-confirmation-gate", target_state="intake_confirmed"))["status"] == "committed"
    topic = artifact("topic-assessment-001", "topic_assessment", depends_on=["context-brief-001"])
    assert research_state.commit_canonical_change(project, change("topic-assess-001", 3, "topic-feasibility-analyzer", artifact_value=topic, target_state="topic_assessed"))["status"] == "committed"
    gap = artifact("gap-card-001", "gap_card", depends_on=["topic-assessment-001"])
    assert research_state.commit_canonical_change(project, change("gap-card-001", 4, "gap-card-builder", artifact_value=gap, target_state="gap_ready"))["status"] == "committed"
    board = artifact(
        "board-decision-001", "board_decision", status="confirmed", depends_on=["gap-card-001"],
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T10:00:00Z"}, decision="GO",
    )
    assert research_state.commit_canonical_change(project, change("board-decision-001", 5, "review-board-decision", artifact_value=board, target_state="board_decided"))["status"] == "committed"


def test_canonical_commit_writes_receipt_and_increments_mutation_revision(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    revision = commit_context_and_timeline(project)
    committed = research_state.commit_canonical_change(project, change("confirm-intake-001", revision, "context-confirmation-gate", target_state="intake_confirmed"))
    assert committed == {"status": "committed", "idempotent": False, "receipt_id": "receipt-confirm-intake-001", "findings": []}
    manifest = load_yaml(project / ".research/project.yaml")
    assert manifest["mutation_revision"] == 3
    assert manifest["current_state"] == "intake_confirmed"
    receipts, findings = research_state.validate_receipt_chain(project)
    assert findings == []
    assert [receipt["receipt_id"] for receipt in receipts] == ["receipt-context-write-001", "receipt-timeline-write-001", "receipt-confirm-intake-001"]
    assert contract.validate_project(project) == []


def test_preflight_rejects_missing_gate_without_writing_files(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    context = artifact(
        "context-brief-001", "context_brief", status="confirmed",
        confirmation={"confirmed_by": "user", "confirmed_at": "2026-09-10T08:21:00Z"},
    )
    assert research_state.commit_canonical_change(project, change("context-write-001", 0, "context-brief-generator", artifact_value=context))["status"] == "committed"
    before = (project / ".research/project.yaml").read_bytes()
    result = research_state.validate_canonical_change(project, change("confirm-intake-001", 1, "context-confirmation-gate", target_state="intake_confirmed"))
    assert result["status"] == "blocked"
    assert {item["code"] for item in result["findings"]} == {"missing_gate_artifact"}
    assert (project / ".research/project.yaml").read_bytes() == before
    assert not (project / ".research/receipts/receipt-confirm-intake-001.json").exists()


def test_policy_stale_revision_and_idempotency_are_enforced(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    context = artifact("context-brief-001", "context_brief", status="draft")
    first = change("context-write-001", 0, "context-brief-generator", artifact_value=context)
    assert research_state.commit_canonical_change(project, first)["status"] == "committed"
    assert research_state.commit_canonical_change(project, first) == {"status": "committed", "idempotent": True, "receipt_id": "receipt-context-write-001", "findings": []}
    denied = research_state.commit_canonical_change(project, change("radar-write-001", 1, "research-radar", artifact_value=artifact("source-001", "source")))
    assert denied["status"] == "blocked"
    assert "policy_artifact_denied" in {item["code"] for item in denied["findings"]}
    stale = research_state.commit_canonical_change(project, change("timeline-write-001", 0, "timeline-baseline-builder", artifact_value=artifact("timeline-baseline-001", "timeline_baseline")))
    assert "stale_mutation_revision" in {item["code"] for item in stale["findings"]}


def test_sensitive_raw_payload_and_direct_change_are_detected(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    unsafe = artifact(
        "raw-register-001", "raw_data_register",
        raw_data={
            "path": "/private/raw.csv", "sha256": "a" * 64, "access": "restricted",
            "truthfulness_declaration": "真实登记", "model_access": "forbidden_by_default", "records": [{"id": "p1"}],
        },
    )
    result = research_state.validate_canonical_change(project, change("raw-write-001", 0, "raw-data-registrar", artifact_value=unsafe))
    assert result["status"] == "blocked"
    assert "sensitive_payload" in {item["code"] for item in result["findings"]}

    context = artifact("context-brief-001", "context_brief")
    assert research_state.commit_canonical_change(project, change("context-write-001", 0, "context-brief-generator", artifact_value=context))["status"] == "committed"
    manifest_path = project / ".research/project.yaml"
    manifest = load_yaml(manifest_path)
    manifest["title"] = "out-of-band change"
    write_yaml(manifest_path, manifest)
    _, receipt_findings = research_state.validate_receipt_chain(project)
    assert "unreceipted_project_change" in {item["code"] for item in receipt_findings}


def test_recovery_rolls_back_a_new_unindexed_artifact(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    artifact_path = project / ".research/artifacts/recovery-artifact-001.yaml"
    artifact_text = "schema_version: '0.2'\n"
    artifact_path.write_text(artifact_text, encoding="utf-8")
    transaction_dir = project / ".research/transactions"
    transaction_dir.mkdir()
    journal = {
        "journal_schema_version": "0.2",
        "request_id": "recovery-001",
        "artifact": {"path": "artifacts/recovery-artifact-001.yaml", "sha256": research_state._sha256_text(artifact_text)},
        "project_sha256": "not-the-current-project",
        "receipt_path": "receipts/receipt-recovery-001.json",
        "receipt_sha256": research_state._sha256_text("{}\n"),
        "receipt_text": "{}\n",
    }
    (transaction_dir / "transaction-recovery-001.json").write_text(json.dumps(journal), encoding="utf-8")
    assert research_state.recover_pending(project)["status"] == "ready"
    assert not artifact_path.exists()
    assert not (transaction_dir / "transaction-recovery-001.json").exists()


def test_policy_and_route_reports_are_complete() -> None:
    assert validate_plugin.validate_mutation_policy() == []
    report = validate_plugin.mutation_policy_report()
    assert report["policy_skill_count"] == 175
    assert report["canonical_artifact_type_coverage"] is True
    assert report["normal_route_coverage"] is True


def test_board_lifecycle_has_continuous_receipts(tmp_path: Path) -> None:
    project = empty_project(tmp_path)
    advance_to_board(project)
    summary = research_state.inspect_research_project(project)
    assert summary["status"] == "ready"
    assert summary["current_state"] == "board_decided"
    assert summary["receipt_count"] == 6
