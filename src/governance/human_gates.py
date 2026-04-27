from __future__ import annotations

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
) -> dict:
    if step < 1 or step > 9:
        raise ValueError("step must be an integer from 1 to 9")
    package = read_change_package(root, change_id)
    path = package.path / "human-gates.yaml"
    payload = load_yaml(path) if path.exists() else {"schema": "human-gates/v1", "change_id": change_id, "approvals": {}}
    approvals = payload.setdefault("approvals", {})
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
