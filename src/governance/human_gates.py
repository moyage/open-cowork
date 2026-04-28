from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package, update_manifest
from .simple_yaml import load_yaml, write_yaml


def approve_step(
    root: str | Path,
    *,
    change_id: str,
    step: int,
    approved_by: str,
    note: str = "",
    recorded_by: str = "",
    evidence_ref: str = "",
    approval_token: str = "",
) -> dict:
    if step < 1 or step > 9:
        raise ValueError("step must be an integer from 1 to 9")
    package = read_change_package(root, change_id)
    path = package.path / "human-gates.yaml"
    payload = load_yaml(path) if path.exists() else {"schema": "human-gates/v1", "change_id": change_id, "approvals": {}}
    bindings = _load_yaml(package.path / "bindings.yaml")
    if not _step_binding(bindings, step).get("human_gate"):
        _record_acknowledgement(payload, step, approved_by, note, recorded_by, evidence_ref)
        write_yaml(path, payload)
        _refresh_step_report_if_possible(root, change_id, step)
        return payload
    _require_strict_step_gate(package, payload, step)
    _require_trusted_approval(package, payload, step, approved_by, recorded_by, approval_token)
    approvals = payload.setdefault("approvals", {})
    payload["writer"] = {
        "tool": "ocw step approve",
        "source": "governance.human_gates.approve_step",
    }
    approvals[step] = {
        "status": "approved",
        "approved_by": approved_by,
        "approved_at": _now_utc(),
        "note": note,
    }
    if recorded_by:
        approvals[step]["recorded_by"] = recorded_by
    if evidence_ref:
        approvals[step]["evidence_ref"] = evidence_ref
    write_yaml(path, payload)
    _clean_readiness_after_approval(root, package, step)
    _refresh_step_report_if_possible(root, change_id, step)
    return payload


def record_intent_confirmation_approval(
    root: str | Path,
    *,
    change_id: str,
    confirmed_by: str,
    note: str = "",
) -> dict:
    package = read_change_package(root, change_id)
    path = package.path / "human-gates.yaml"
    payload = load_yaml(path) if path.exists() else {"schema": "human-gates/v1", "change_id": change_id, "approvals": {}}
    approvals = payload.setdefault("approvals", {})
    existing = approvals.get(1) or approvals.get("1")
    if existing and existing.get("status") == "approved":
        return payload
    payload["writer"] = {
        "tool": "ocw intent confirm",
        "source": "governance.human_gates.record_intent_confirmation_approval",
    }
    approvals[1] = {
        "status": "approved",
        "approved_by": confirmed_by,
        "approved_at": _now_utc(),
        "note": note,
        "source": "intent-confirm",
    }
    write_yaml(path, payload)
    _clean_readiness_after_approval(root, package, 1)
    _refresh_step_report_if_possible(root, change_id, 1)
    return payload


def record_bypass(
    root: str | Path,
    *,
    change_id: str,
    step: int,
    reason: str,
    recorded_by: str,
    note: str = "",
    evidence_ref: str = "",
) -> dict:
    package = read_change_package(root, change_id)
    path = package.path / "human-gates.yaml"
    payload = load_yaml(path) if path.exists() else {"schema": "human-gates/v1", "change_id": change_id, "approvals": {}}
    bypasses = payload.setdefault("bypasses", [])
    payload["writer"] = {
        "tool": "ocw review",
        "source": "governance.human_gates.record_bypass",
    }
    bypasses.append({
        "step": step,
        "reason": reason,
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
        "note": note,
    })
    if evidence_ref:
        bypasses[-1]["evidence_ref"] = evidence_ref
    write_yaml(path, payload)
    return payload


def _record_acknowledgement(
    payload: dict,
    step: int,
    acknowledged_by: str,
    note: str,
    recorded_by: str,
    evidence_ref: str,
) -> None:
    acknowledgements = payload.setdefault("acknowledgements", [])
    item = {
        "step": step,
        "status": "acknowledged",
        "acknowledged_by": acknowledged_by,
        "acknowledged_at": _now_utc(),
        "note": note,
    }
    if recorded_by:
        item["recorded_by"] = recorded_by
    if evidence_ref:
        item["evidence_ref"] = evidence_ref
    acknowledgements.append(item)


def require_step_approval(root: str | Path, *, change_id: str, step: int) -> None:
    package = read_change_package(root, change_id)
    bindings = _load_yaml(package.path / "bindings.yaml")
    step_binding = _step_binding(bindings, step)
    if not step_binding.get("human_gate"):
        return
    gates = _load_yaml(package.path / "human-gates.yaml")
    approval = (gates.get("approvals") or {}).get(step) or (gates.get("approvals") or {}).get(str(step))
    if not approval or approval.get("status") != "approved":
        raise ValueError(f"Step {step} human gate approval is required before continuing")


def _require_strict_step_gate(package, gates: dict, step: int) -> None:
    current_step = package.manifest.get("current_step")
    if isinstance(current_step, int) and step <= current_step:
        return
    bindings = _load_yaml(package.path / "bindings.yaml")
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    human_steps = sorted(
        int(str(key).strip("'")) for key, binding in steps.items()
        if str(key).strip("'").isdigit() and isinstance(binding, dict) and binding.get("human_gate")
    )
    approvals = gates.get("approvals") or {}
    for gate_step in human_steps:
        if isinstance(current_step, int) and gate_step < current_step:
            continue
        approval = approvals.get(gate_step) or approvals.get(str(gate_step))
        if not approval or approval.get("status") != "approved":
            if gate_step == step:
                return
            raise ValueError(
                f"Step {step} cannot be approved yet; next required human gate is Step {gate_step}."
            )
    if isinstance(current_step, int) and step > current_step:
        raise ValueError(f"Step {step} cannot be approved yet; current step is Step {current_step}.")


def _require_trusted_approval(package, gates: dict, step: int, approved_by: str, recorded_by: str, approval_token: str) -> None:
    policy_path = package.path / "approval-policy.yaml"
    if not policy_path.exists():
        return
    policy = load_yaml(policy_path)
    if not policy.get("required"):
        return
    expected = str(policy.get("token_sha256") or "").strip()
    actual = hashlib.sha256(approval_token.encode("utf-8")).hexdigest() if approval_token else ""
    if expected and actual == expected:
        return
    attempts = gates.setdefault("untrusted_attempts", [])
    attempts.append({
        "step": step,
        "approved_by": approved_by,
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
        "reason": "trusted approval token is required",
    })
    write_yaml(package.path / "human-gates.yaml", gates)
    raise ValueError("trusted approval token is required for this human gate approval")


def _step_binding(bindings: dict, step: int) -> dict:
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    return steps.get(step) or steps.get(str(step)) or steps.get(f"'{step}'") or {}


def _load_yaml(path: Path) -> dict:
    return load_yaml(path) if path.exists() else {}


def _clean_readiness_after_approval(root: str | Path, package, step: int) -> None:
    readiness = dict(package.manifest.get("readiness") or {})
    missing_items = list(readiness.get("missing_items") or [])
    remove = {f"step{step}_approval", f"step{step}_confirmation"}
    if step == 1 and _intent_is_confirmed(package.path):
        remove.add("intent_confirmation")
    cleaned = [item for item in missing_items if item not in remove]
    if cleaned != missing_items:
        readiness["missing_items"] = cleaned
        update_manifest(root, package.change_id, readiness=readiness)


def _intent_is_confirmed(change_dir: Path) -> bool:
    intent = _load_yaml(change_dir / "intent-confirmation.yaml")
    return intent.get("status") == "confirmed"


def _refresh_step_report_if_possible(root: str | Path, change_id: str, step: int) -> None:
    try:
        from .step_report import materialize_step_report

        materialize_step_report(root, change_id=change_id, step=step)
    except Exception:
        # Approval is the canonical truth; report materialization can still be
        # blocked before a change has enough files for the requested step.
        return


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
