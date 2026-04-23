from __future__ import annotations

import re
from pathlib import Path

from .contract import validate_contract
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml

STATE_CONSISTENCY_SCHEMA = "governance/state-consistency-check/v1"


def evaluate_state_consistency(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    current_change = load_yaml(paths.current_change_file())
    nested_current = current_change.get("current_change", {})
    if not isinstance(nested_current, dict):
        nested_current = {}
    resolved_change_id = change_id or _extract_current_change_id(current_change)
    if not resolved_change_id:
        raise ValueError("no change_id provided and no current change set")

    manifest_path = paths.change_file(str(resolved_change_id), "manifest.yaml")
    manifest = load_yaml(manifest_path)
    contract_path = paths.change_file(str(resolved_change_id), "contract.yaml")
    contract = load_yaml(contract_path) if contract_path.exists() else {}
    changes_index = load_yaml(paths.changes_index_file())
    maintenance_status = load_yaml(paths.maintenance_status_file())
    index_entry = _find_change_entry(changes_index, str(resolved_change_id))
    bindings_path = paths.change_file(str(resolved_change_id), "bindings.yaml")
    bindings = load_yaml(bindings_path) if bindings_path.exists() else {}

    checks: list[dict] = []
    _append_check(
        checks,
        check_id="C1",
        name="change_identifier_alignment",
        expected=str(resolved_change_id),
        actual={
            "manifest": manifest.get("id") or manifest.get("change_id"),
            "current_change": _extract_current_change_id(current_change),
            "changes_index": _entry_change_id(index_entry),
            "maintenance_status": maintenance_status.get("current_change_id"),
        },
        passed=(manifest.get("id") or manifest.get("change_id")) == str(resolved_change_id)
        and _extract_current_change_id(current_change) == str(resolved_change_id)
        and _entry_change_id(index_entry) == str(resolved_change_id)
        and maintenance_status.get("current_change_id") == str(resolved_change_id),
        failure_severity="blocker",
        detail="Canonical change identifier must align across manifest, current-change, changes-index, and maintenance-status.",
    )
    _append_check(
        checks,
        check_id="C2",
        name="lifecycle_status_alignment",
        expected=manifest.get("status"),
        actual={
            "current_change": current_change.get("status") or nested_current.get("status"),
            "changes_index": index_entry.get("status"),
        },
        passed=(current_change.get("status") or nested_current.get("status")) == manifest.get("status")
        and index_entry.get("status") == manifest.get("status"),
        failure_severity="blocker",
        detail="Active lifecycle status must align across manifest, current-change, and changes-index.",
    )
    _append_check(
        checks,
        check_id="C3",
        name="formal_dispatch_alignment",
        expected=manifest.get("formal_dispatch_status"),
        actual={
            "current_change": current_change.get("formal_dispatch_status") or nested_current.get("formal_dispatch_status"),
            "changes_index": index_entry.get("formal_dispatch_status"),
        },
        passed=(current_change.get("formal_dispatch_status") or nested_current.get("formal_dispatch_status")) == manifest.get("formal_dispatch_status")
        and index_entry.get("formal_dispatch_status") == manifest.get("formal_dispatch_status"),
        failure_severity="blocker",
        detail="Formal dispatch status must align across the active governance records.",
    )
    _append_check(
        checks,
        check_id="C4",
        name="stage_mode_alignment",
        expected=manifest.get("stage_mode"),
        actual=maintenance_status.get("current_change_active"),
        passed=_semantic_posture_match(manifest.get("stage_mode"), maintenance_status.get("current_change_active")),
        failure_severity="observation",
        detail="Manifest stage_mode and maintenance current_change_active should describe the same effective posture.",
    )
    _append_check(
        checks,
        check_id="C5",
        name="maintenance_posture_compatibility",
        expected=manifest.get("status"),
        actual=maintenance_status.get("status"),
        passed=_semantic_posture_match(manifest.get("status"), maintenance_status.get("status")),
        failure_severity="observation",
        detail="Maintenance posture should remain semantically compatible with the active change lifecycle state.",
    )

    manifest_validation_objects = list(manifest.get("target_validation_objects", []))
    contract_validation_objects = list(contract.get("validation_objects", []))
    validation_expected = contract_validation_objects or manifest_validation_objects
    validation_passed = bool(manifest_validation_objects)
    validation_detail = "Manifest target_validation_objects must exist and remain explicit."
    if contract_validation_objects:
        validation_passed = manifest_validation_objects == contract_validation_objects
        validation_detail = "Manifest target_validation_objects must align with contract validation_objects for the active change."

    _append_check(
        checks,
        check_id="C6",
        name="validation_object_set",
        expected=validation_expected,
        actual=manifest_validation_objects,
        passed=validation_passed,
        failure_severity="blocker",
        detail=validation_detail,
    )

    contract_errors = validate_contract(contract) if contract else ["missing contract.yaml"]
    _append_check(
        checks,
        check_id="C7",
        name="contract_governance_completeness",
        expected="valid implementation contract with governance guards",
        actual=contract_errors or "valid",
        passed=not contract_errors,
        failure_severity="blocker",
        detail="Active change contract must be execution-ready and include required governance guardrails.",
    )

    execution_owner = _step_owner(bindings, manifest, 6)
    verification_owner = _step_owner(bindings, manifest, 7)
    review_owner = _step_owner(bindings, manifest, 8)
    owner_separation_passed = bool(
        execution_owner
        and verification_owner
        and review_owner
        and execution_owner != verification_owner
        and execution_owner != review_owner
    )
    _append_check(
        checks,
        check_id="C8",
        name="execution_verify_review_owner_separation",
        expected="step6 owner must differ from both step7 verifier owner and step8 reviewer owner",
        actual={
            "step6_owner": execution_owner,
            "step7_owner": verification_owner,
            "step8_owner": review_owner,
        },
        passed=owner_separation_passed,
        failure_severity="blocker",
        detail="Execution, verification, and review ownership must remain separated for the active change.",
    )

    blocker_count = sum(1 for check in checks if check["status"] == "blocker")
    observation_count = sum(1 for check in checks if check["status"] == "observation")
    checked_files = [
        str(manifest_path.relative_to(paths.root)),
        str(paths.current_change_file().relative_to(paths.root)),
        str(paths.changes_index_file().relative_to(paths.root)),
        str(paths.maintenance_status_file().relative_to(paths.root)),
    ]
    if contract_path.exists():
        checked_files.append(str(contract_path.relative_to(paths.root)))
    if bindings_path.exists():
        checked_files.append(str(bindings_path.relative_to(paths.root)))
    return {
        "schema": STATE_CONSISTENCY_SCHEMA,
        "change_id": str(resolved_change_id),
        "status": "pass" if blocker_count == 0 else "blocker",
        "checked_files": checked_files,
        "summary": {
            "blocker_count": blocker_count,
            "observation_count": observation_count,
            "aligned": blocker_count == 0,
        },
        "checks": checks,
    }


def write_state_consistency_result(root: str | Path, change_id: str | None = None, output_path: str | Path | None = None) -> str:
    result = evaluate_state_consistency(root, change_id)
    paths = GovernancePaths(Path(root))
    target = Path(output_path) if output_path else paths.change_file(result["change_id"], "STATE_CONSISTENCY_CHECK.yaml")
    write_yaml(target, result)
    return str(target)


def _append_check(
    checks: list[dict],
    *,
    check_id: str,
    name: str,
    expected,
    actual,
    passed: bool,
    failure_severity: str,
    detail: str,
) -> None:
    checks.append({
        "id": check_id,
        "name": name,
        "status": "pass" if passed else failure_severity,
        "expected": expected,
        "actual": actual,
        "detail": detail,
    })


def _extract_current_change_id(payload: dict) -> str | None:
    nested = payload.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    return payload.get("current_change_id") or nested.get("change_id") or nested.get("current_change_id")


def _entry_change_id(entry: dict) -> str | None:
    return entry.get("id") or entry.get("change_id")


def _find_change_entry(changes_index: dict, change_id: str) -> dict:
    for entry in changes_index.get("changes", []):
        if _entry_change_id(entry) == change_id:
            return entry
    return {}


def _semantic_posture_match(left, right) -> bool:
    if left == right:
        return True
    if left is None or right is None:
        return False
    if isinstance(left, bool) or isinstance(right, bool):
        return _is_active_posture(left) == _is_active_posture(right)
    left_tokens = set(_tokenize(str(left)))
    right_tokens = set(_tokenize(str(right)))
    if left_tokens == right_tokens:
        return True
    shared = left_tokens & right_tokens
    if {"draft"} <= shared:
        return True
    if {"step6", "executed"} <= shared:
        return True
    if {"dispatch", "pending"} <= shared:
        return True
    return str(left) in str(right) or str(right) in str(left)


def _is_active_posture(value) -> bool:
    if isinstance(value, bool):
        return value
    tokens = set(_tokenize(str(value)))
    if not tokens:
        return False
    if {"archived"} <= tokens or {"inactive"} <= tokens:
        return False
    return bool(tokens & {"draft", "step", "dispatch", "pending", "active", "executed", "review"})


def _tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _step_owner(bindings: dict, manifest: dict, step: int) -> str | None:
    steps = bindings.get("steps", {})
    binding = steps.get(step) or steps.get(str(step)) or {}
    if binding.get("owner"):
        return binding.get("owner")
    roles = manifest.get("roles", {})
    if step == 6:
        return roles.get("executor")
    if step in {7, 8}:
        return roles.get("reviewer") or roles.get("verifier")
    return None
