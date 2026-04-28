from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

from .index import read_active_changes, read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def check_execution_preflight(root: str | Path, change_id: str | None = None, paths_to_modify: list[str] | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    payload = {
        "schema": "execution-preflight/v1",
        "can_execute": False,
        "reason": "",
        "required_action": "",
        "change_id": None,
        "current_step": None,
        "current_status": None,
        "contract_ref": None,
        "evidence_ref": None,
        "checked_paths": list(paths_to_modify or []),
    }
    if not paths.governance_dir.exists():
        return {
            **payload,
            "reason": "governance_missing",
            "required_action": "initialize open-cowork before modifying project files",
        }

    selected = _select_active_change(paths, change_id)
    if not selected:
        reason = "change_not_found" if change_id else "no_active_change"
        action = (
            f"select an existing active change or create change '{change_id}' before modifying project files"
            if change_id else
            "create or confirm a change package before modifying project files"
        )
        return {**payload, "reason": reason, "required_action": action}
    if selected.get("ambiguous"):
        return {
            **payload,
            "reason": "multiple_active_changes",
            "required_action": "select the intended active change before modifying project files",
        }

    resolved_change_id = str(selected["change_id"])
    change_dir = paths.change_dir(resolved_change_id)
    manifest = _load_optional(change_dir / "manifest.yaml")
    current_step = manifest.get("current_step") or selected.get("current_step")
    current_status = manifest.get("status") or selected.get("status")
    base = {
        **payload,
        "change_id": resolved_change_id,
        "current_step": current_step,
        "current_status": current_status,
        "contract_ref": f".governance/changes/{resolved_change_id}/contract.yaml",
        "evidence_ref": f".governance/changes/{resolved_change_id}/evidence/",
    }
    contract_path = change_dir / "contract.yaml"
    if not contract_path.exists():
        return {**base, "reason": "contract_required", "required_action": "complete contract.yaml before modifying project files"}
    if not (change_dir / "bindings.yaml").exists():
        return {**base, "reason": "bindings_required", "required_action": "complete bindings.yaml before modifying project files"}
    if current_step not in {5, 6}:
        return {
            **base,
            "reason": "not_at_execution_gate",
            "required_action": f"continue the current Step {current_step} flow before modifying project files",
        }
    if not _step5_is_approved(change_dir):
        return {
            **base,
            "reason": "step5_approval_required",
            "required_action": "Step 5 human gate approval is required before modifying project files",
        }
    readiness = manifest.get("readiness", {}) if isinstance(manifest, dict) else {}
    if readiness.get("step6_entry_ready") is not True:
        return {
            **base,
            "reason": "step6_readiness_required",
            "required_action": "mark Step 6 readiness from the approved change package before modifying project files",
        }
    from .audit import audit_failures_for_gate, run_governance_audit

    audit = run_governance_audit(paths.root, resolved_change_id)
    audit_failures = audit_failures_for_gate(audit, "preflight")
    if audit_failures:
        return {
            **base,
            "reason": "governance_audit_required",
            "required_action": "resolve fail-level governance audit findings before modifying project files",
            "audit_ref": f".governance/changes/{resolved_change_id}/",
            "audit_failures": _audit_failures(audit_failures),
        }
    scope_result = _scope_check(contract_path, list(paths_to_modify or []))
    if not scope_result["allowed"]:
        return {
            **base,
            "checked_paths": list(paths_to_modify or []),
            "reason": scope_result["reason"],
            "required_action": scope_result["required_action"],
            "scope_violations": scope_result["violations"],
        }
    return {
        **base,
        "checked_paths": list(paths_to_modify or []),
        "can_execute": True,
        "reason": "ready_for_step6",
        "required_action": "record execution evidence under the active change package",
    }


def record_flow_bypass_recovery(
    root: str | Path,
    *,
    change_id: str,
    reason: str,
    modified_files: list[str],
    missing_items: list[str],
    recovery_actions: list[str],
    recorded_by: str,
) -> dict:
    paths = GovernancePaths(Path(root))
    recovery_dir = paths.change_dir(change_id) / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    path = recovery_dir / "bypass-records.yaml"
    payload = load_yaml(path) if path.exists() else {
        "schema": "flow-bypass-recovery/v1",
        "change_id": change_id,
        "records": [],
    }
    record = {
        "classification": "flow_bypass_recovery",
        "normal_evidence": False,
        "reason": reason,
        "modified_files": list(modified_files),
        "missing_governance_items": list(missing_items),
        "recovery_actions": list(recovery_actions),
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
        "note": "This is an exception recovery record and must not be treated as normal Step 6 evidence.",
    }
    payload.setdefault("records", []).append(record)
    write_yaml(path, payload)
    return payload


def format_execution_preflight(payload: dict) -> str:
    lines = [
        "# open-cowork execution preflight",
        "",
        f"- can_execute: {str(payload.get('can_execute')).lower()}",
        f"- reason: {payload.get('reason')}",
        f"- required_action: {payload.get('required_action')}",
    ]
    if payload.get("change_id"):
        lines.extend([
            f"- change_id: {payload.get('change_id')}",
            f"- current_step: {payload.get('current_step')}",
            f"- current_status: {payload.get('current_status')}",
            f"- contract_ref: {payload.get('contract_ref')}",
            f"- evidence_ref: {payload.get('evidence_ref')}",
        ])
    if payload.get("checked_paths"):
        lines.append(f"- checked_paths: {', '.join(payload.get('checked_paths') or [])}")
    if payload.get("scope_violations"):
        lines.append("- scope_violations:")
        for item in payload.get("scope_violations") or []:
            lines.append(f"  - path={item.get('path')} reason={item.get('reason')}")
    return "\n".join(lines) + "\n"


def _scope_check(contract_path: Path, paths_to_modify: list[str]) -> dict:
    if not paths_to_modify:
        return {"allowed": True, "reason": "", "required_action": "", "violations": []}
    contract = load_yaml(contract_path)
    scope_in = list(contract.get("scope_in") or [])
    scope_out = list(contract.get("scope_out") or [])
    violations = []
    for path in paths_to_modify:
        normalized = str(path).strip().lstrip("./")
        if not normalized:
            continue
        if _matches_any(normalized, scope_out):
            violations.append({"path": normalized, "reason": "matches_scope_out"})
            continue
        if scope_in and not _matches_any(normalized, scope_in):
            violations.append({"path": normalized, "reason": "outside_scope_in"})
    if violations:
        return {
            "allowed": False,
            "reason": "scope_violation",
            "required_action": "adjust the active contract scope or choose paths within scope before modifying project files",
            "violations": violations,
        }
    return {"allowed": True, "reason": "", "required_action": "", "violations": []}


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        normalized = str(pattern).strip().lstrip("./")
        if not normalized:
            continue
        if fnmatch(path, normalized) or fnmatch(path, normalized.rstrip("/")):
            return True
        if normalized.endswith("/**"):
            prefix = normalized[:-3].rstrip("/")
            if path == prefix or path.startswith(prefix + "/"):
                return True
    return False


def _select_active_change(paths: GovernancePaths, change_id: str | None) -> dict:
    active = [item for item in read_active_changes(paths.root).get("changes", []) if _is_active(item)]
    if change_id:
        for item in active:
            if str(item.get("change_id")) == str(change_id):
                return item
        manifest_path = paths.change_file(change_id, "manifest.yaml")
        if manifest_path.exists():
            manifest = load_yaml(manifest_path)
            if _is_active(manifest):
                return {"change_id": change_id, "status": manifest.get("status"), "current_step": manifest.get("current_step")}
        return {}
    if len(active) > 1:
        return {"ambiguous": True}
    if len(active) == 1:
        return active[0]
    current = _load_current_change(paths)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    resolved_change_id = current.get("current_change_id") or nested.get("change_id")
    status = current.get("status") or nested.get("status")
    if resolved_change_id and status not in {"idle", "archived", "abandoned", "superseded", "none", None}:
        return {"change_id": resolved_change_id, "status": status, "current_step": current.get("current_step") or nested.get("current_step")}
    return {}


def _load_current_change(paths: GovernancePaths) -> dict:
    try:
        return read_current_change(paths.root)
    except Exception:
        return {}


def _load_optional(path: Path) -> dict:
    return load_yaml(path) if path.exists() else {}


def _is_active(item: dict) -> bool:
    return bool(item.get("change_id")) and item.get("status") not in {"idle", "archived", "abandoned", "superseded", "none", None}


def _step5_is_approved(change_dir: Path) -> bool:
    gates = _load_optional(change_dir / "human-gates.yaml")
    approvals = gates.get("approvals", {}) if isinstance(gates, dict) else {}
    approval = approvals.get(5) or approvals.get("5") or approvals.get("'5'")
    return isinstance(approval, dict) and approval.get("status") == "approved"


def _audit_failures(failures: list[dict]) -> list[dict]:
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "message": item.get("message"),
            "required_action": item.get("required_action"),
        }
        for item in failures
    ]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
