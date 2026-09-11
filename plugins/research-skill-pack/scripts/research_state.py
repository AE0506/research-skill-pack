#!/usr/bin/env python3
"""Canonical local-state mutations for Research Skill Pack.

This module owns the deterministic part of the runtime write gate.  It never
contacts a provider or follows raw-data paths.  The MCP wrapper exposes these
functions to Codex; keeping the core independent makes the safety behaviour
unit-testable without a running model or server.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml

import research_contract


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PLUGIN_ROOT / "shared" / "canonical-mutation-policy-v0.2.yaml"
ROUTE_PATH = PLUGIN_ROOT / "shared" / "canonical-route-map-v0.2.yaml"
RESEARCH_DIR = research_contract.RESEARCH_DIR
RECEIPTS_DIR = "receipts"
TRANSACTIONS_DIR = "transactions"
LOCK_FILE = ".mutation.lock"
REQUEST_KEYS = {
    "request_id",
    "expected_mutation_revision",
    "origin_skill_id",
    "artifact",
    "target_state",
    "state_reason",
}
FORBIDDEN_PAYLOAD_KEYS = {
    "api_key",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "raw_content",
    "raw_rows",
    "secret",
}
RAW_DATA_FORBIDDEN_KEYS = {"content", "excerpt", "participants", "records", "responses", "rows", "tokens"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _yaml_text(value: Any) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)


def _finding(code: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _safe_project_root(project_root: str | Path) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not (root / RESEARCH_DIR).is_dir():
        raise ValueError("project root must contain .research")
    return root


def _load_yaml(path: Path) -> Any:
    return research_contract.load_yaml(path)


def _load_policy() -> dict[str, dict[str, Any]]:
    document = _load_yaml(POLICY_PATH)
    entries = document.get("skills", []) if isinstance(document, dict) else []
    return {
        item["id"]: item
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _load_routes() -> list[dict[str, Any]]:
    document = _load_yaml(ROUTE_PATH)
    routes = document.get("routes", []) if isinstance(document, dict) else []
    return [item for item in routes if isinstance(item, dict)]


def _manifest_path(root: Path) -> Path:
    return root / RESEARCH_DIR / "project.yaml"


def _receipt_dir(root: Path) -> Path:
    return root / RESEARCH_DIR / RECEIPTS_DIR


def _transaction_dir(root: Path) -> Path:
    return root / RESEARCH_DIR / TRANSACTIONS_DIR


def _receipt_path(root: Path, request_id: str) -> Path:
    return _receipt_dir(root) / f"receipt-{request_id}.json"


def _transaction_path(root: Path, request_id: str) -> Path:
    return _transaction_dir(root) / f"transaction-{request_id}.json"


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


@contextmanager
def _mutation_lock(root: Path) -> Iterator[None]:
    """Serialize canonical writes on the supported local macOS/Linux runtime."""
    import fcntl

    lock_path = root / RESEARCH_DIR / LOCK_FILE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _contains_forbidden_payload_key(value: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else str(key)
            key_name = str(key).lower()
            inside_raw_data = prefix == "raw_data" or prefix.startswith("raw_data.")
            if key_name in FORBIDDEN_PAYLOAD_KEYS or (inside_raw_data and key_name in RAW_DATA_FORBIDDEN_KEYS):
                findings.append(location)
            findings.extend(_contains_forbidden_payload_key(child, location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_contains_forbidden_payload_key(child, f"{prefix}[{index}]"))
    return findings


def _artifact_index_item(artifact: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id", "type", "version", "status", "created_at", "created_by",
        "depends_on", "supersedes", "change_reason",
    )
    return {key: artifact.get(key) for key in keys} | {"path": f"artifacts/{artifact.get('id', '')}.yaml"}


def _artifact_inventory(root: Path, project: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index_item in project.get("artifact_index", []):
        if not isinstance(index_item, dict):
            continue
        relative_path = index_item.get("path")
        if not isinstance(relative_path, str) or not research_contract.is_safe_artifact_path(relative_path):
            continue
        path = root / RESEARCH_DIR / relative_path
        if path.is_file():
            items.append({
                "id": str(index_item.get("id", "")),
                "path": relative_path,
                "sha256": _sha256_file(path),
            })
    return sorted(items, key=lambda item: (item["id"], item["path"]))


def _inventory_sha256(inventory: list[dict[str, str]]) -> str:
    return _sha256_text(_canonical_json(inventory))


def _receipt_hash(receipt: dict[str, Any]) -> str:
    return _sha256_text(_canonical_json(receipt))


def _read_receipts(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    receipts: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    directory = _receipt_dir(root)
    if not directory.exists():
        return receipts, findings
    for path in sorted(directory.glob("receipt-*.json")):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(_finding("invalid_receipt", f"cannot read receipt: {exc}", str(path)))
            continue
        if not isinstance(receipt, dict):
            findings.append(_finding("invalid_receipt", "receipt must be a JSON object", str(path)))
            continue
        receipt["_path"] = str(path)
        receipt["_sha256"] = _receipt_hash({key: value for key, value in receipt.items() if not key.startswith("_")})
        receipts.append(receipt)
    receipts.sort(key=lambda item: int(item.get("mutation_revision", {}).get("after", -1)))
    return receipts, findings


def validate_receipt_chain(project_root: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Verify receipt order, hash links, and the current canonical snapshot."""
    try:
        root = _safe_project_root(project_root)
        project = _load_yaml(_manifest_path(root))
    except (ValueError, OSError) as exc:
        return [], [_finding("missing_project", str(exc))]
    if not isinstance(project, dict):
        return [], [_finding("invalid_project", "project.yaml must be a mapping")]
    receipts, findings = _read_receipts(root)
    previous_hash: str | None = None
    previous_revision: int | None = None
    for receipt in receipts:
        revision = receipt.get("mutation_revision")
        if not isinstance(revision, dict) or not isinstance(revision.get("before"), int) or not isinstance(revision.get("after"), int):
            findings.append(_finding("invalid_receipt_revision", "receipt needs integer before/after revisions", receipt.get("_path", "")))
            continue
        if revision["after"] != revision["before"] + 1:
            findings.append(_finding("invalid_receipt_revision", "receipt revision must increase by one", receipt.get("_path", "")))
        if previous_revision is not None and revision["before"] != previous_revision:
            findings.append(_finding("receipt_revision_gap", "receipt revision chain is not contiguous", receipt.get("_path", "")))
        if receipt.get("previous_receipt_sha256") != previous_hash:
            findings.append(_finding("receipt_hash_chain", "receipt previous hash does not match the prior receipt", receipt.get("_path", "")))
        previous_revision = revision["after"]
        previous_hash = receipt.get("_sha256")
    if receipts:
        latest = receipts[-1]
        if latest.get("project_sha256") != _sha256_file(_manifest_path(root)):
            findings.append(_finding("unreceipted_project_change", "current project manifest differs from the latest receipt"))
        inventory = _artifact_inventory(root, project)
        if latest.get("inventory_sha256") != _inventory_sha256(inventory):
            findings.append(_finding("unreceipted_artifact_change", "current artifact inventory differs from the latest receipt"))
        if previous_revision != project.get("mutation_revision"):
            findings.append(_finding("receipt_revision_mismatch", "project mutation_revision differs from the receipt chain"))
    return receipts, findings


def _recover_pending_locked(root: Path) -> list[dict[str, str]]:
    """Finish a journaled receipt or safely roll back an unindexed new artifact."""
    findings: list[dict[str, str]] = []
    directory = _transaction_dir(root)
    if not directory.exists():
        return findings
    for path in sorted(directory.glob("transaction-*.json")):
        try:
            transaction = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(_finding("invalid_transaction_journal", str(exc), str(path)))
            continue
        if not isinstance(transaction, dict):
            findings.append(_finding("invalid_transaction_journal", "journal must be a JSON object", str(path)))
            continue
        manifest_path = _manifest_path(root)
        expected_manifest = transaction.get("project_sha256")
        artifact = transaction.get("artifact")
        artifact_ok = True
        artifact_path: Path | None = None
        if isinstance(artifact, dict):
            artifact_relative = artifact.get("path")
            if not isinstance(artifact_relative, str) or not research_contract.is_safe_artifact_path(artifact_relative):
                findings.append(_finding("invalid_transaction_journal", "journal artifact path is invalid", str(path)))
                continue
            candidate_path = root / RESEARCH_DIR / artifact_relative
            artifact_path = candidate_path
            artifact_ok = candidate_path.is_file() and _sha256_file(candidate_path) == artifact.get("sha256")
        manifest_ok = manifest_path.is_file() and _sha256_file(manifest_path) == expected_manifest
        receipt_relative = transaction.get("receipt_path")
        receipt_text = transaction.get("receipt_text")
        receipt_candidate = Path(receipt_relative) if isinstance(receipt_relative, str) else None
        receipt_path = root / RESEARCH_DIR / receipt_candidate if receipt_candidate is not None else root / RESEARCH_DIR
        if (
            not isinstance(receipt_text, str)
            or receipt_candidate is None
            or receipt_candidate.is_absolute()
            or ".." in receipt_candidate.parts
            or receipt_candidate.parts[:1] != (RECEIPTS_DIR,)
        ):
            findings.append(_finding("invalid_transaction_journal", "journal receipt payload is invalid", str(path)))
            continue
        receipt_ok = receipt_path.is_file() and _sha256_file(receipt_path) == transaction.get("receipt_sha256")
        if manifest_ok and artifact_ok:
            if not receipt_ok:
                _atomic_write_text(receipt_path, receipt_text)
            path.unlink()
            continue
        if not manifest_ok and artifact_path is not None and artifact_ok:
            artifact_path.unlink()
            path.unlink()
            continue
        if not manifest_ok and artifact_path is None:
            path.unlink()
            continue
        findings.append(_finding("transaction_recovery_blocked", "pending transaction cannot be safely finalized or rolled back", str(path)))
    return findings


def recover_pending(project_root: str | Path) -> dict[str, Any]:
    try:
        root = _safe_project_root(project_root)
        with _mutation_lock(root):
            findings = _recover_pending_locked(root)
    except (ValueError, OSError) as exc:
        findings = [_finding("recovery_failed", str(exc))]
    return {"status": "ready" if not findings else "blocked", "findings": findings}


def _normalize_request(change: Any) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not isinstance(change, dict):
        return None, [_finding("invalid_change", "change must be an object")]
    findings: list[dict[str, str]] = []
    unexpected = sorted(set(change) - REQUEST_KEYS)
    if unexpected:
        findings.append(_finding("unexpected_change_field", f"unsupported change fields: {', '.join(unexpected)}"))
    request_id = change.get("request_id")
    if not isinstance(request_id, str) or re.fullmatch(r"[a-z][a-z0-9-]{2,95}", request_id) is None:
        findings.append(_finding("invalid_request_id", "request_id must be a lowercase canonical id"))
    if not isinstance(change.get("expected_mutation_revision"), int) or change["expected_mutation_revision"] < 0:
        findings.append(_finding("invalid_expected_revision", "expected_mutation_revision must be a non-negative integer"))
    if not isinstance(change.get("origin_skill_id"), str):
        findings.append(_finding("invalid_origin_skill", "origin_skill_id must be a Skill id"))
    artifact = change.get("artifact")
    target_state = change.get("target_state")
    if artifact is not None and not isinstance(artifact, dict):
        findings.append(_finding("invalid_artifact", "artifact must be an object when supplied"))
    if target_state is not None and not isinstance(target_state, str):
        findings.append(_finding("invalid_target_state", "target_state must be a state string when supplied"))
    if artifact is None and target_state is None:
        findings.append(_finding("empty_change", "a canonical change needs an artifact and/or target_state"))
    if target_state is not None and not isinstance(change.get("state_reason"), str):
        findings.append(_finding("missing_state_reason", "state_reason is required for a state transition"))
    if isinstance(artifact, dict):
        forbidden = _contains_forbidden_payload_key(artifact)
        if forbidden:
            findings.append(_finding("sensitive_payload", f"artifact payload contains forbidden metadata keys: {', '.join(forbidden)}"))
    return copy.deepcopy(change), findings


def _build_candidate(root: Path, change: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    project_path = _manifest_path(root)
    try:
        project = _load_yaml(project_path)
    except ValueError as exc:
        return None, [_finding("invalid_project", str(exc), str(project_path))]
    if not isinstance(project, dict):
        return None, [_finding("invalid_project", "project.yaml must be a mapping", str(project_path))]
    if project.get("schema_version") != "0.2":
        return None, [_finding("migration_required", "canonical mutations require a migrated schema_version 0.2 project")]
    if not isinstance(project.get("mutation_revision"), int):
        return None, [_finding("missing_mutation_revision", "run migration before using the runtime write gate")]
    expected_revision = change["expected_mutation_revision"]
    if expected_revision != project["mutation_revision"]:
        return None, [_finding("stale_mutation_revision", "expected_mutation_revision does not match current project state")]
    policy = _load_policy().get(change["origin_skill_id"])
    if policy is None:
        return None, [_finding("unknown_policy_skill", "origin_skill_id is not in the canonical mutation policy")]
    artifact = change.get("artifact")
    target_state = change.get("target_state")
    allowed_artifacts = policy.get("artifact_types", [])
    allowed_transitions = {(entry.get("from"), entry.get("to")) for entry in policy.get("transitions", []) if isinstance(entry, dict)}
    if artifact is not None:
        artifact_type = artifact.get("type")
        if artifact_type not in allowed_artifacts:
            findings.append(_finding("policy_artifact_denied", f"{change['origin_skill_id']} may not write artifact type {artifact_type!r}"))
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str):
            findings.append(_finding("invalid_artifact_id", "artifact requires an id"))
        indexed_ids = {item.get("id") for item in project.get("artifact_index", []) if isinstance(item, dict)}
        if artifact_id in indexed_ids:
            findings.append(_finding("artifact_overwrite_denied", "canonical artifacts are immutable; create a new id with supersedes instead"))
        artifact_path = root / RESEARCH_DIR / "artifacts" / f"{artifact_id}.yaml"
        if artifact_path.exists():
            findings.append(_finding("artifact_path_exists", "artifact path already exists and cannot be overwritten", str(artifact_path)))
        schema_findings = research_contract.schema_findings(artifact, "artifact-schema.json", "candidate_artifact")
        findings.extend(_finding(item.code, item.message, item.path) for item in schema_findings)
        findings.extend(_finding(item.code, item.message, item.path) for item in research_contract.check_raw_data_safety(artifact, "candidate_artifact"))
        findings.extend(_finding(item.code, item.message, item.path) for item in research_contract.check_confirmation(artifact, "candidate_artifact"))
    current_state = project.get("current_state")
    if target_state is not None:
        findings.extend(_finding(item.code, item.message, item.path) for item in research_contract.transition_findings(str(current_state), target_state))
        if (current_state, target_state) not in allowed_transitions:
            findings.append(_finding("policy_transition_denied", f"{change['origin_skill_id']} may not transition {current_state} → {target_state}"))
    if findings:
        return None, findings

    candidate_project = copy.deepcopy(project)
    if artifact is not None:
        candidate_project.setdefault("artifact_index", []).append(_artifact_index_item(artifact))
    if target_state is not None:
        candidate_project["write_sequence"] = int(candidate_project.get("write_sequence", 0)) + 1
        candidate_project["current_state"] = target_state
        candidate_project.setdefault("state_history", []).append({
            "sequence": candidate_project["write_sequence"],
            "state": target_state,
            "at": _now(),
            "changed_by": "skill",
            "reason": change["state_reason"],
        })
    candidate_project["mutation_revision"] = project["mutation_revision"] + 1

    with tempfile.TemporaryDirectory(prefix="research-state-preflight-") as temporary:
        staged_root = Path(temporary)
        staged_research = staged_root / RESEARCH_DIR
        staged_artifacts = staged_research / "artifacts"
        staged_artifacts.mkdir(parents=True)
        for index_item in project.get("artifact_index", []):
            if not isinstance(index_item, dict):
                continue
            relative_path = index_item.get("path")
            if not isinstance(relative_path, str) or not research_contract.is_safe_artifact_path(relative_path):
                continue
            source = root / RESEARCH_DIR / relative_path
            target = staged_research / relative_path
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        if artifact is not None:
            (staged_artifacts / f"{artifact['id']}.yaml").write_text(_yaml_text(artifact), encoding="utf-8")
        (staged_research / "project.yaml").write_text(_yaml_text(candidate_project), encoding="utf-8")
        findings.extend(_finding(item.code, item.message, item.path) for item in research_contract.validate_project(staged_root))
    if findings:
        return None, findings
    return {
        "project_before": project,
        "project_after": candidate_project,
        "artifact": artifact,
        "artifact_path": f"artifacts/{artifact['id']}.yaml" if artifact is not None else None,
    }, []


def _fingerprint(change: dict[str, Any]) -> str:
    return _sha256_text(_canonical_json(change))


def _existing_receipt(root: Path, request_id: str) -> dict[str, Any] | None:
    path = _receipt_path(root, request_id)
    if not path.is_file():
        return None
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return receipt if isinstance(receipt, dict) else None


def _prepare(root: Path, change: Any) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    normalized, findings = _normalize_request(change)
    if findings or normalized is None:
        return None, findings
    recovery = _recover_pending_locked(root)
    if recovery:
        return None, recovery
    existing = _existing_receipt(root, normalized["request_id"])
    fingerprint = _fingerprint(normalized)
    if existing is not None:
        if existing.get("change_fingerprint") == fingerprint:
            return {"idempotent_receipt": existing, "change_fingerprint": fingerprint}, []
        return None, [_finding("request_id_conflict", "request_id was already committed with a different change")]
    candidate, candidate_findings = _build_candidate(root, normalized)
    if candidate is None:
        return None, candidate_findings
    candidate["change"] = normalized
    candidate["change_fingerprint"] = fingerprint
    return candidate, []


def validate_canonical_change(project_root: str | Path, change: Any) -> dict[str, Any]:
    try:
        root = _safe_project_root(project_root)
        with _mutation_lock(root):
            prepared, findings = _prepare(root, change)
    except (ValueError, OSError) as exc:
        prepared, findings = None, [_finding("preflight_failed", str(exc))]
    if findings:
        return {"status": "blocked", "findings": findings}
    if prepared is not None and "idempotent_receipt" in prepared:
        receipt = prepared["idempotent_receipt"]
        return {
            "status": "already_committed",
            "receipt_id": receipt.get("receipt_id"),
            "change_fingerprint": prepared["change_fingerprint"],
            "findings": [],
        }
    assert prepared is not None
    before = prepared["project_before"]
    after = prepared["project_after"]
    artifact = prepared.get("artifact")
    return {
        "status": "ready",
        "request_id": prepared["change"]["request_id"],
        "change_fingerprint": prepared["change_fingerprint"],
        "mutation_revision": {"before": before["mutation_revision"], "after": after["mutation_revision"]},
        "state": {"before": before["current_state"], "after": after["current_state"]},
        "artifact": {key: artifact.get(key) for key in ("id", "type", "status")} if isinstance(artifact, dict) else None,
        "findings": [],
    }


def _receipt_for(root: Path, prepared: dict[str, Any]) -> dict[str, Any]:
    before = prepared["project_before"]
    after = prepared["project_after"]
    artifact = prepared.get("artifact")
    receipts, receipt_findings = _read_receipts(root)
    if receipt_findings:
        raise ValueError("cannot append to an invalid receipt chain")
    previous_hash = receipts[-1].get("_sha256") if receipts else None
    artifact_entry: dict[str, Any] | None = None
    if isinstance(artifact, dict):
        artifact_entry = {
            "id": artifact["id"],
            "type": artifact["type"],
            "status": artifact["status"],
            "path": prepared["artifact_path"],
            "sha256": _sha256_text(_yaml_text(artifact)),
        }
    inventory = _artifact_inventory(root, before)
    if artifact_entry is not None:
        inventory.append({"id": artifact_entry["id"], "path": artifact_entry["path"], "sha256": artifact_entry["sha256"]})
        inventory.sort(key=lambda item: (item["id"], item["path"]))
    project_text = _yaml_text(after)
    return {
        "receipt_schema_version": "0.2",
        "receipt_id": f"receipt-{prepared['change']['request_id']}",
        "request_id": prepared["change"]["request_id"],
        "origin_skill_id": prepared["change"]["origin_skill_id"],
        "change_fingerprint": prepared["change_fingerprint"],
        "mutation_revision": {"before": before["mutation_revision"], "after": after["mutation_revision"]},
        "state": {"before": before["current_state"], "after": after["current_state"]},
        "artifact": artifact_entry,
        "project_sha256": _sha256_text(project_text),
        "inventory_sha256": _inventory_sha256(inventory),
        "previous_receipt_sha256": previous_hash,
        "validation": {"status": "valid", "finding_count": 0},
        "created_at": _now(),
    }


def commit_canonical_change(project_root: str | Path, change: Any) -> dict[str, Any]:
    try:
        root = _safe_project_root(project_root)
        with _mutation_lock(root):
            prepared, findings = _prepare(root, change)
            if findings:
                return {"status": "blocked", "findings": findings}
            assert prepared is not None
            if "idempotent_receipt" in prepared:
                receipt = prepared["idempotent_receipt"]
                return {"status": "committed", "idempotent": True, "receipt_id": receipt.get("receipt_id"), "findings": []}
            receipt = _receipt_for(root, prepared)
            artifact = prepared.get("artifact")
            artifact_text = _yaml_text(artifact) if isinstance(artifact, dict) else None
            project_text = _yaml_text(prepared["project_after"])
            receipt_text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
            journal = {
                "journal_schema_version": "0.2",
                "request_id": prepared["change"]["request_id"],
                "artifact": ({"path": prepared["artifact_path"], "sha256": _sha256_text(artifact_text)} if artifact_text else None),
                "project_sha256": _sha256_text(project_text),
                "receipt_path": f"{RECEIPTS_DIR}/receipt-{prepared['change']['request_id']}.json",
                "receipt_sha256": _sha256_text(receipt_text),
                "receipt_text": receipt_text,
            }
            journal_path = _transaction_path(root, prepared["change"]["request_id"])
            _atomic_write_text(journal_path, json.dumps(journal, ensure_ascii=False, indent=2) + "\n")
            if artifact_text is not None:
                _atomic_write_text(root / RESEARCH_DIR / str(prepared["artifact_path"]), artifact_text)
            _atomic_write_text(_manifest_path(root), project_text)
            _atomic_write_text(_receipt_path(root, prepared["change"]["request_id"]), receipt_text)
            journal_path.unlink(missing_ok=True)
    except (ValueError, OSError) as exc:
        return {"status": "blocked", "findings": [_finding("commit_failed", str(exc))]}
    return {"status": "committed", "idempotent": False, "receipt_id": receipt["receipt_id"], "findings": []}


def inspect_research_project(project_root: str | Path) -> dict[str, Any]:
    try:
        root = _safe_project_root(project_root)
        recovery = recover_pending(root)
        if recovery["status"] != "ready":
            return recovery
        project = _load_yaml(_manifest_path(root))
        if not isinstance(project, dict):
            return {"status": "blocked", "findings": [_finding("invalid_project", "project.yaml must be a mapping")]}
        contract_findings = research_contract.validate_project(root)
        receipts, receipt_findings = validate_receipt_chain(root)
        next_routes = [
            {
                "id": route.get("id"),
                "to_state": route.get("to_state"),
                "required_skill_ids": route.get("required_skill_ids", []),
                "transition_owner": route.get("transition_owner"),
            }
            for route in _load_routes()
            if route.get("from_state") == project.get("current_state")
        ]
        artifacts = []
        for item in project.get("artifact_index", []):
            if isinstance(item, dict):
                artifacts.append({key: item.get(key) for key in ("id", "type", "status", "version")})
        findings = [_finding(item.code, item.message, item.path) for item in contract_findings] + receipt_findings
        return {
            "status": "ready" if not findings else "blocked",
            "project_id": project.get("project_id"),
            "current_state": project.get("current_state"),
            "mutation_revision": project.get("mutation_revision"),
            "artifacts": artifacts,
            "next_routes": next_routes,
            "receipt_count": len(receipts),
            "findings": findings,
            "evidence_boundary": "Local metadata and receipts only; this does not verify model adherence, research conclusions, or external facts.",
        }
    except (ValueError, OSError) as exc:
        return {"status": "blocked", "findings": [_finding("inspect_failed", str(exc))]}
