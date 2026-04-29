from __future__ import annotations

from pathlib import Path

from .project_state import validate_project_state


def evaluate_gate_decision(state: dict, gate: str) -> dict:
    if gate == "execution":
        return evaluate_execution_gate(state)
    if gate == "closeout":
        return evaluate_closeout_gate(state)
    return {"allowed": False, "reason": "unknown_gate"}


def status_gate_decision(state: dict, gate: str) -> dict:
    return evaluate_gate_decision(state, gate)


def evaluate_execution_gate(state: dict) -> dict:
    return evaluate_execution_gate_for_root(state, None)


def evaluate_execution_gate_for_root(state: dict, root: str | Path | None) -> dict:
    return _evaluate_execution(state, root, require_gate=True)


def evaluate_execution_prerequisites(state: dict, root: str | Path | None) -> dict:
    return _evaluate_execution(state, root, require_gate=False)


def _evaluate_execution(state: dict, root: str | Path | None, *, require_gate: bool) -> dict:
    errors = validate_project_state(state)
    if errors:
        return {"allowed": False, "reason": "state_schema_invalid", "errors": errors}
    active_round = state["active_round"]
    participant_init = active_round["participant_initialization"]
    if participant_init.get("status") != "complete" or participant_init.get("missing_roles"):
        return {"allowed": False, "reason": "participant_initialization_required"}

    participants = active_round["participants"]
    for role in participant_init.get("required_roles") or []:
        if role in participants and not participants.get(role):
            return {"allowed": False, "reason": "participant_role_required", "role": role}

    executor = participants.get("executor")
    reviewer = participants.get("reviewer")
    bypass = participant_init.get("bypass") or {}
    if executor and reviewer and executor == reviewer and not _has_bypass_evidence(bypass):
        return {"allowed": False, "reason": "independent_reviewer_required"}

    confirmation = active_round.get("participant_confirmation") or {}
    if confirmation.get("status") != "human-confirmed" or not confirmation.get("evidence_ref"):
        return {"allowed": False, "reason": "participant_confirmation_required"}

    external_confirmation = (active_round.get("external_rules") or {}).get("confirmation") or {}
    if external_confirmation.get("status") not in {"confirmed", "selected"} or not external_confirmation.get("evidence_ref"):
        return {"allowed": False, "reason": "external_rules_confirmation_required"}

    missing_outputs = _missing_required_step_outputs(active_round, root)
    if missing_outputs:
        return {
            "allowed": False,
            "reason": "step_outputs_required",
            "missing_outputs": missing_outputs,
        }

    if require_gate:
        gate = active_round["gates"]["execution"]
        if gate.get("status") != "approved":
            return {"allowed": False, "reason": "execution_approval_required"}
        if not gate.get("approval_evidence_ref"):
            return {"allowed": False, "reason": "approval_evidence_required"}
    return {"allowed": True, "reason": "execution_ready"}


def evaluate_closeout_gate(state: dict) -> dict:
    errors = validate_project_state(state)
    if errors:
        return {"allowed": False, "reason": "state_schema_invalid", "errors": errors}

    active_round = state["active_round"]
    for item in state.get("decision_needed") or []:
        if item.get("status") == "open" and item.get("blocking") is True:
            return {"allowed": False, "reason": "blocking_decision_open"}

    verify = active_round["verify"]
    if verify.get("status") not in {"pass", "passed"}:
        return {"allowed": False, "reason": "verify_pass_required"}
    failed_blocking_rule = _failed_blocking_external_rule(active_round)
    if failed_blocking_rule:
        return {
            "allowed": False,
            "reason": "blocking_rule_failed",
            "rule_id": failed_blocking_rule,
        }

    review = active_round["review"]
    if review.get("status") != "completed" or review.get("decision") != "approve":
        return {"allowed": False, "reason": "review_approval_required"}

    participants = active_round["participants"]
    reviewer = review.get("reviewer") or participants.get("reviewer")
    bypass = active_round["participant_initialization"].get("bypass") or {}
    if reviewer and reviewer == participants.get("executor") and not _has_bypass_evidence(bypass):
        return {"allowed": False, "reason": "independent_reviewer_required"}

    gate = active_round["gates"]["closeout"]
    if gate.get("status") != "approved":
        return {"allowed": False, "reason": "closeout_approval_required"}
    if not gate.get("approval_evidence_ref"):
        return {"allowed": False, "reason": "approval_evidence_required"}
    if not active_round["closeout"].get("summary"):
        return {"allowed": False, "reason": "closeout_summary_required"}
    return {"allowed": True, "reason": "closeout_ready"}


def _has_bypass_evidence(bypass: dict) -> bool:
    return (
        bypass.get("allowed") is True
        and bool(bypass.get("approved_by"))
        and bool(bypass.get("approved_at"))
        and bool(bypass.get("reason"))
        and bool(bypass.get("impact_scope"))
        and bool(bypass.get("approval_evidence_ref"))
    )


def _missing_required_step_outputs(active_round: dict, root: str | Path | None) -> list[str]:
    if root is None:
        return []
    step_outputs = active_round.get("step_outputs") or {}
    base_dir = step_outputs.get("base_dir") or f"docs/open-cowork/rounds/{active_round.get('round_id', '')}"
    base = Path(root) / base_dir
    missing: list[str] = []
    for item in step_outputs.get("required_before_execution") or []:
        filename = item.get("file")
        if filename and not _substantive_file(base / filename):
            missing.append(str((Path(base_dir) / filename).as_posix()))
    return missing


def _substantive_file(path: Path) -> bool:
    try:
        return path.exists() and bool(path.read_text(encoding="utf-8").strip())
    except OSError:
        return False


def _failed_blocking_external_rule(active_round: dict) -> str:
    blocking_rule_ids = {
        _rule_id(item)
        for item in (active_round.get("external_rules", {}).get("active") or [])
        if _rule_is_blocking(item) and _rule_id(item)
    }
    for item in active_round.get("verify", {}).get("rule_results") or []:
        rule_id = item.get("rule_id") or item.get("id")
        if rule_id in blocking_rule_ids and item.get("status") in {"fail", "failed", "error"}:
            return rule_id
    return ""


def _rule_id(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("id", "")
    return ""


def _rule_is_blocking(item) -> bool:
    if isinstance(item, str):
        return False
    if isinstance(item, dict):
        return item.get("failure_impact") == "blocking"
    return False
