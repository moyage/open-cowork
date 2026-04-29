from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .simple_yaml import load_yaml


PROTOCOL_VERSION = "0.3.11"

PHASES = (
    "intent-scope",
    "plan-contract",
    "execute-evidence",
    "verify-review",
    "closeout",
)

GATE_STATUSES = ("pending", "approved", "blocked")
REVIEW_STATUSES = ("not-requested", "requested", "completed", "blocked")
REVIEW_DECISIONS = ("", "approve", "revise", "reject")
RULE_FAILURE_IMPACTS = ("blocking", "warning", "advisory")

REVIEW_DECISION_BY_STATUS = {
    "not-requested": {""},
    "requested": {""},
    "completed": {"approve", "revise", "reject"},
    "blocked": {"", "revise"},
}


def initial_project_state(*, round_id: str = "R-00000000-001", goal: str = "") -> dict:
    return {
        "protocol": {"name": "open-cowork", "version": PROTOCOL_VERSION},
        "layout": "current-state",
        "default_read_set": [
            ".governance/AGENTS.md",
            ".governance/agent-entry.md",
            ".governance/current-state.md",
            ".governance/state.yaml",
        ],
        "active_round": {
            "round_id": round_id,
            "goal": goal,
            "phase": "intent-scope",
            "scope": {"in": [], "out": []},
            "acceptance": {"summary": "", "done_definition": "full-scope"},
            "plan": {"summary": "", "steps": [], "risks": [], "assumptions": []},
            "verification_plan": {"commands": [], "external_rules": [], "reviewer_required": True},
            "participants": {
                "sponsor": "",
                "owner_agent": "",
                "orchestrator": "",
                "executor": "",
                "reviewer": "",
                "advisors": [],
            },
            "participant_initialization": {
                "status": "pending",
                "required_roles": ["sponsor", "owner_agent", "executor", "reviewer"],
                "initialized_roles": [],
                "missing_roles": ["sponsor", "owner_agent", "executor", "reviewer"],
                "role_bindings": [_empty_role_binding("owner_agent")],
                "bypass": {
                    "allowed": False,
                    "requested_by": "",
                    "approved_by": "",
                    "approval_source": "",
                    "approval_channel": "",
                    "approval_evidence_ref": "",
                    "approved_at": "",
                    "reason": "",
                    "impact_scope": "",
                },
            },
            "participant_confirmation": {
                "status": "pending",
                "confirmed_by": "",
                "confirmed_at": "",
                "evidence_ref": "",
                "summary": "",
            },
            "gates": {
                "execution": _empty_gate(),
                "closeout": _empty_gate(),
            },
            "external_rules": {
                "active": [],
                "suspended": [],
                "confirmation": {
                    "status": "pending",
                    "confirmed_by": "",
                    "confirmed_at": "",
                    "evidence_ref": "",
                    "summary": "",
                },
            },
            "step_outputs": {
                "base_dir": "",
                "required_before_execution": [
                    {"step": 1, "name": "intent", "file": "intent.md"},
                    {"step": 2, "name": "requirements", "file": "requirements.md"},
                    {"step": 3, "name": "design", "file": "design.md"},
                    {"step": 4, "name": "tasks", "file": "tasks.md"},
                ],
            },
            "evidence_refs": [],
            "verify": {"status": "not-run", "summary": "", "rule_results": []},
            "review": {"status": "not-requested", "decision": "", "reviewer": "", "independent": True, "summary": ""},
            "implementation_commitment": {
                "mode": "full-scope",
                "downgrade_allowed": False,
                "downgrade_approval": None,
            },
            "closeout": {"status": "open", "summary": "", "remaining_risks": [], "completed": [], "not_completed": []},
            "carry_forward": [],
        },
        "decision_needed": [],
        "context_budget": {"current_state_target_lines": 200, "state_target_lines": 400},
        "updated_at": _now_utc(),
    }


def load_project_state(root: str | Path) -> dict:
    return load_yaml(Path(root) / ".governance" / "state.yaml")


def validate_project_documents(root: str | Path) -> list[str]:
    base = Path(root) / ".governance"
    errors = validate_project_state(load_yaml(base / "state.yaml"))
    errors.extend(_validate_ledger(load_yaml(base / "ledger.yaml")))
    errors.extend(_validate_evidence(load_yaml(base / "evidence.yaml")))
    errors.extend(_validate_rules(load_yaml(base / "rules.yaml")))
    return errors


def validate_project_state(state: dict) -> list[str]:
    errors: list[str] = []
    protocol = state.get("protocol", {})
    if protocol.get("version") != PROTOCOL_VERSION:
        errors.append("protocol version must be 0.3.11")
    active_round = _dict(state.get("active_round"))
    phase = active_round.get("phase")
    if phase not in PHASES:
        errors.append("active_round phase is invalid")
    for key in ("plan", "verification_plan"):
        if key not in active_round:
            errors.append(f"active_round {key} is required")
    _validate_participant_initialization(active_round, errors)
    _validate_review(active_round, errors)
    _validate_decisions(state, errors)
    return errors


def _validate_participant_initialization(active_round: dict, errors: list[str]) -> None:
    participant_init = _dict(active_round.get("participant_initialization"))
    bypass = _dict(participant_init.get("bypass"))
    if "approval_evidence_ref" not in bypass:
        errors.append("participant bypass approval_evidence_ref is required")
    for index, binding in enumerate(participant_init.get("role_bindings") or []):
        item = _dict(binding)
        for key in (
            "role",
            "actor",
            "responsibility",
            "authority_scope",
            "output_responsibility",
            "independence_requirement",
            "evidence_ref",
        ):
            if key not in item:
                errors.append(f"role binding {index} missing {key}")


def _validate_review(active_round: dict, errors: list[str]) -> None:
    review = _dict(active_round.get("review"))
    status = review.get("status")
    decision = review.get("decision", "")
    if status not in REVIEW_STATUSES:
        errors.append("review status is invalid")
        return
    if decision not in REVIEW_DECISIONS:
        errors.append("review decision is invalid")
        return
    if decision not in REVIEW_DECISION_BY_STATUS[status]:
        if status == "completed" and decision == "":
            errors.append("review decision is required when review status is completed")
        else:
            errors.append("review status and decision combination is invalid")


def _validate_decisions(state: dict, errors: list[str]) -> None:
    for index, item in enumerate(state.get("decision_needed") or []):
        decision = _dict(item)
        for key in (
            "id",
            "status",
            "summary",
            "requested_by",
            "created_at",
            "blocking",
            "resolved_by",
            "resolved_at",
            "resolution_summary",
            "evidence_ref",
        ):
            if key not in decision:
                errors.append(f"decision_needed {index} missing {key}")


def _validate_ledger(payload) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, list):
        return ["ledger.yaml must be a list"]
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"ledger.yaml item {index} must be a mapping")
            continue
        for key in ("round_id", "goal", "final_status", "closeout_summary"):
            if key not in item:
                errors.append(f"ledger.yaml item {index} missing {key}")
    return errors


def _validate_evidence(payload) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, list):
        return ["evidence.yaml must be a list"]
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"evidence.yaml item {index} must be a mapping")
            continue
        for key in ("evidence_id", "round_id", "kind", "ref", "summary", "created_by", "created_at"):
            if key not in item:
                errors.append(f"evidence.yaml item {index} missing {key}")
    return errors


def _validate_rules(payload) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, list):
        return ["rules.yaml must be a list"]
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"rules.yaml item {index} must be a mapping")
            continue
        impact = item.get("failure_impact")
        if impact is not None and impact not in RULE_FAILURE_IMPACTS:
            errors.append(f"rules.yaml item {index} failure_impact is invalid")
    return errors


def _empty_gate() -> dict:
    return {
        "status": "pending",
        "requested_by": "",
        "approved_by": "",
        "approval_source": "",
        "approval_channel": "",
        "approval_evidence_ref": "",
        "created_by": "",
        "created_at": "",
        "reason": "",
    }


def _empty_role_binding(role: str) -> dict:
    return {
        "role": role,
        "actor": "",
        "responsibility": "",
        "authority_scope": [],
        "output_responsibility": [],
        "independence_requirement": "",
        "evidence_ref": "",
    }


def _dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clone_state(state: dict) -> dict:
    return deepcopy(state)
