from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .lean_paths import ensure_lean_layout
from .lean_render import render_current_state
from .lean_round import evaluate_closeout_gate
from .lean_state import initial_lean_state
from .simple_yaml import load_yaml, write_yaml


REQUIRED_ROLES = ("sponsor", "owner_agent", "executor", "reviewer")


def start_round(
    root: str | Path,
    *,
    round_id: str,
    goal: str,
    scope_in: list[str] | None = None,
    scope_out: list[str] | None = None,
    acceptance_summary: str = "",
) -> dict:
    state = initial_lean_state(round_id=round_id, goal=goal)
    active_round = state["active_round"]
    active_round["scope"]["in"] = scope_in or []
    active_round["scope"]["out"] = scope_out or []
    active_round["acceptance"]["summary"] = acceptance_summary
    ensure_lean_layout(root, initial_state=state)
    return state


def init_participants(
    root: str | Path,
    *,
    sponsor: str,
    owner_agent: str,
    executor: str,
    reviewer: str,
    orchestrator: str = "",
    advisors: list[str] | None = None,
) -> dict:
    state = _load_state(root)
    active_round = state["active_round"]
    participants = active_round["participants"]
    participants.update({
        "sponsor": sponsor,
        "owner_agent": owner_agent,
        "orchestrator": orchestrator,
        "executor": executor,
        "reviewer": reviewer,
        "advisors": advisors or [],
    })
    missing = [role for role in REQUIRED_ROLES if not participants.get(role)]
    participant_init = active_round["participant_initialization"]
    participant_init["required_roles"] = list(REQUIRED_ROLES)
    participant_init["initialized_roles"] = [role for role in REQUIRED_ROLES if participants.get(role)]
    participant_init["missing_roles"] = missing
    participant_init["status"] = "complete" if not missing else "blocked"
    participant_init["role_bindings"] = [
        _role_binding(role, participants.get(role, "")) for role in REQUIRED_ROLES
    ]
    _write_state(root, state)
    return state


def approve_round_gate(
    root: str | Path,
    *,
    gate: str,
    approved_by: str,
    evidence_ref: str,
    reason: str = "",
    channel: str = "cli",
) -> dict:
    state = _load_state(root)
    gate_payload = state["active_round"]["gates"][gate]
    gate_payload.update({
        "status": "approved",
        "approved_by": approved_by,
        "approval_source": approved_by,
        "approval_channel": channel,
        "approval_evidence_ref": evidence_ref,
        "created_by": approved_by,
        "created_at": _now_utc(),
        "reason": reason,
    })
    _write_state(root, state)
    return state


def add_evidence(
    root: str | Path,
    *,
    evidence_id: str,
    kind: str,
    ref: str,
    summary: str,
    created_by: str,
    round_id: str | None = None,
) -> dict:
    state = _load_state(root)
    active_round = state["active_round"]
    resolved_round_id = round_id or active_round["round_id"]
    entry = {
        "evidence_id": evidence_id,
        "round_id": resolved_round_id,
        "kind": kind,
        "ref": ref,
        "summary": summary,
        "created_by": created_by,
        "created_at": _now_utc(),
    }
    evidence = _load_list(root, "evidence.yaml")
    evidence.append(entry)
    write_yaml(_base(root) / "evidence.yaml", evidence)
    refs = active_round.setdefault("evidence_refs", [])
    if evidence_id not in refs:
        refs.append(evidence_id)
    _write_state(root, state)
    return entry


def add_rule(
    root: str | Path,
    *,
    rule_id: str,
    name: str,
    kind: str,
    failure_impact: str,
    applies_to: list[str],
    command: str = "",
    authorization_ref: str = "",
) -> tuple[bool, dict]:
    if failure_impact == "blocking" and not authorization_ref:
        return False, {"reason": "authorization_required_for_blocking_rule"}
    state = _load_state(root)
    entry = {
        "id": rule_id,
        "name": name,
        "kind": kind,
        "applies_to": applies_to,
        "command": command,
        "failure_impact": failure_impact,
        "status": "active",
        "authorization_ref": authorization_ref,
        "created_at": _now_utc(),
    }
    rules = [item for item in _load_list(root, "rules.yaml") if item.get("id") != rule_id]
    rules.append(entry)
    write_yaml(_base(root) / "rules.yaml", rules)
    active_rules = state["active_round"].setdefault("external_rules", {}).setdefault("active", [])
    active_rules[:] = [item for item in active_rules if item.get("id") != rule_id]
    active_rules.append({"id": rule_id, "failure_impact": failure_impact})
    _write_state(root, state)
    return True, entry


def update_rule_status(
    root: str | Path,
    *,
    rule_id: str,
    status: str,
    actor: str,
    reason: str,
    authorization_ref: str = "",
) -> tuple[bool, dict]:
    state = _load_state(root)
    rules = _load_list(root, "rules.yaml")
    target = next((item for item in rules if item.get("id") == rule_id), None)
    if target is None:
        return False, {"reason": "rule_not_found"}
    if target.get("failure_impact") == "blocking" and status in {"suspended", "removed"} and not authorization_ref:
        return False, {"reason": "authorization_required_for_blocking_rule_change"}
    target.update({
        "status": status,
        "updated_by": actor,
        "updated_at": _now_utc(),
        "update_reason": reason,
        "authorization_ref": authorization_ref or target.get("authorization_ref", ""),
    })
    write_yaml(_base(root) / "rules.yaml", rules)
    external_rules = state["active_round"].setdefault("external_rules", {})
    active = [item for item in external_rules.get("active", []) if item.get("id") != rule_id]
    suspended = [item for item in external_rules.get("suspended", []) if item.get("id") != rule_id]
    if status == "active":
        active.append({"id": rule_id, "failure_impact": target.get("failure_impact", "")})
    elif status == "suspended":
        suspended.append({"id": rule_id, "failure_impact": target.get("failure_impact", "")})
    external_rules["active"] = active
    external_rules["suspended"] = suspended
    _write_state(root, state)
    return True, target


def close_round(
    root: str | Path,
    *,
    final_status: str,
    closed_by: str,
    summary: str = "",
    evidence_ref: str = "",
) -> tuple[bool, dict]:
    state = _load_state(root)
    decision = evaluate_closeout_gate(state)
    if not decision.get("allowed"):
        return False, decision

    active_round = state["active_round"]
    closeout = active_round["closeout"]
    closeout_status = closeout.get("status") or "open"
    if closeout_status != "open":
        return False, {"reason": "round_already_closed", "status": closeout_status}
    closeout_summary = summary or closeout.get("summary", "")
    closeout.update({
        "status": final_status,
        "summary": closeout_summary,
        "closed_by": closed_by,
        "closed_at": _now_utc(),
        "evidence_ref": evidence_ref or active_round["gates"]["closeout"].get("approval_evidence_ref", ""),
    })
    active_round["phase"] = "closeout"

    entry = {
        "round_id": active_round["round_id"],
        "goal": active_round.get("goal", ""),
        "final_status": final_status,
        "closeout_summary": closeout_summary,
        "closed_by": closed_by,
        "closed_at": closeout["closed_at"],
        "evidence_ref": closeout["evidence_ref"],
    }
    ledger = _load_list(root, "ledger.yaml")
    ledger.append(entry)
    write_yaml(_base(root) / "ledger.yaml", ledger)
    _write_state(root, state)
    return True, entry


def _load_state(root: str | Path) -> dict:
    ensure_lean_layout(root)
    return load_yaml(_base(root) / "state.yaml")


def _load_list(root: str | Path, filename: str) -> list:
    path = _base(root) / filename
    payload = load_yaml(path)
    return payload if isinstance(payload, list) else []


def _write_state(root: str | Path, state: dict) -> None:
    state["updated_at"] = _now_utc()
    base = _base(root)
    write_yaml(base / "state.yaml", state)
    (base / "current-state.md").write_text(render_current_state(state), encoding="utf-8")


def _base(root: str | Path) -> Path:
    return Path(root) / ".governance"


def _role_binding(role: str, actor: str) -> dict:
    return {
        "role": role,
        "actor": actor,
        "responsibility": f"{role} responsibility for current round",
        "authority_scope": [],
        "output_responsibility": [],
        "independence_requirement": "reviewer must be independent from executor" if role == "reviewer" else "",
        "evidence_ref": "",
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
