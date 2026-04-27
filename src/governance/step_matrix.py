from __future__ import annotations

from pathlib import Path

from .contract import load_contract
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .state_consistency import evaluate_state_consistency

STEP_MATRIX_TOTAL_STEPS = 9
STEP_LABELS = {
    1: "明确意图 / Clarify intent",
    2: "确定范围 / Lock scope",
    3: "方案设计 / Shape approach",
    4: "组装变更包 / Assemble change package",
    5: "批准开工 / Approve execution",
    6: "执行变更 / Execute change",
    7: "验证结果 / Verify result",
    8: "独立审查 / Independent review",
    9: "归档接续 / Archive and handoff",
}
FLOW_SECTIONS = {
    1: "Define goal",
    2: "Define goal",
    3: "Shape plan",
    4: "Shape plan",
    5: "Shape plan",
    6: "Execute and verify",
    7: "Execute and verify",
    8: "Close out",
    9: "Close out",
}
ACTION_PURPOSES = {
    1: "Frame the problem and collect the active inputs.",
    2: "Make scope, boundaries, and non-goals explicit.",
    3: "Choose the bounded implementation direction.",
    4: "Assemble the active change package and delivery path.",
    5: "Bind roles, gates, and execution readiness.",
    6: "Produce the bounded implementation outputs and evidence.",
    7: "Check bounded correctness, evidence, and defects.",
    8: "Make an explicit accept / revise / reject decision.",
    9: "Archive approved outputs and refresh maintenance state.",
}
DEFAULT_HUMAN_INTERVENTION_STEPS = {1, 2, 3, 5, 8, 9}
APPROVAL_REQUIRED_STEPS = {2, 5, 8, 9}
REVIEW_REQUIRED_STEPS = {1, 3, 4, 7}
PHASE_LABELS = {
    1: "Phase 1 / 定义与对齐",
    2: "Phase 2 / 方案与准备",
    3: "Phase 3 / 执行与验证",
    4: "Phase 4 / 审查与收束",
}


def render_step_matrix(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    current_change = load_yaml(paths.current_change_file())
    nested_current = current_change.get("current_change", {})
    if not isinstance(nested_current, dict):
        nested_current = {}
    resolved_change_id = change_id or current_change.get("current_change_id") or nested_current.get("change_id")
    if not resolved_change_id:
        raise ValueError("no change_id provided and no current change set")

    manifest = load_yaml(paths.change_file(str(resolved_change_id), "manifest.yaml"))
    contract = load_contract(paths.change_file(str(resolved_change_id), "contract.yaml"))
    tasks_path = paths.change_file(str(resolved_change_id), "tasks.md")
    tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
    bindings = _load_bindings(paths, str(resolved_change_id))
    consistency = evaluate_state_consistency(root, str(resolved_change_id))
    current_step = _normalize_step(current_change.get("current_step") or nested_current.get("current_step") or manifest.get("current_step") or "draft")
    current_status = current_change.get("status") or nested_current.get("status") or manifest.get("status")
    owner_or_stage_actor = _resolve_step_owner(current_step, bindings, manifest, current_status)
    blockers = [check["detail"] for check in consistency["checks"] if check["status"] == "blocker"]
    expected_outputs = _expected_outputs_for_step(current_step, str(resolved_change_id), contract)
    next_step = _next_step(current_step)
    human_intervention_points = _human_intervention_points(bindings, manifest, current_status)

    return {
        "change_id": str(resolved_change_id),
        "total_steps": STEP_MATRIX_TOTAL_STEPS,
        "current_step": current_step,
        "current_status": current_status,
        "current_flow_section": FLOW_SECTIONS.get(current_step, "Unknown"),
        "current_action_label": STEP_LABELS.get(current_step, str(current_step)),
        "owner_or_stage_actor": owner_or_stage_actor,
        "current_owner_or_stage_actor": owner_or_stage_actor,
        "next_step": next_step,
        "next_action_label": STEP_LABELS.get(next_step) if next_step else None,
        "next_owner_or_stage_actor": _resolve_step_owner(next_step, bindings, manifest, current_status) if next_step else None,
        "goal_summary": _goal_summary(tasks_text, contract),
        "validation_objects": list(contract.get("validation_objects", [])) or list(manifest.get("target_validation_objects", [])),
        "expected_outputs": expected_outputs,
        "blockers": blockers,
        "human_intervention_points": human_intervention_points,
        "action_guide": _action_guide(bindings, manifest, current_status),
        "step_labels": STEP_LABELS,
    }


def render_status_snapshot(root: str | Path, change_id: str | None = None) -> dict:
    matrix = render_step_matrix(root, change_id)
    paths = GovernancePaths(Path(root))
    gates = _load_human_gates(paths, matrix["change_id"])
    bindings = _load_bindings(paths, matrix["change_id"])
    current_step = matrix["current_step"]
    current_phase_index = _phase_index_for_step(current_step)
    next_decision_step = _next_human_decision_step(current_step, gates)
    blockers = matrix["blockers"]
    return {
        "schema": "status-snapshot/v1",
        "change_id": matrix["change_id"],
        "current_phase": PHASE_LABELS[current_phase_index],
        "current_step": current_step,
        "completed_steps": [step for step in range(1, STEP_MATRIX_TOTAL_STEPS + 1) if step < current_step],
        "remaining_steps": [step for step in range(1, STEP_MATRIX_TOTAL_STEPS + 1) if step > current_step],
        "current_owner": matrix["current_owner_or_stage_actor"],
        "waiting_on": _resolve_waiting_on(current_step, blockers),
        "next_decision": _resolve_next_decision(next_decision_step),
        "human_intervention_required": bool(blockers) or _current_step_requires_human(current_step, matrix["human_intervention_points"]),
        "project_summary": matrix["goal_summary"],
        "current_status": matrix["current_status"],
        "blockers": blockers,
        "step_progress": _step_progress(paths, matrix["change_id"], current_step, gates, bindings),
    }


def format_status_snapshot_view(snapshot: dict) -> str:
    lines = [
        "# open-cowork status",
        "",
        "## Human status snapshot",
        f"- current_phase: {snapshot['current_phase']}",
        f"- current_step: {snapshot['current_step']}",
        f"- current_owner: {snapshot['current_owner']}",
        f"- waiting_on: {snapshot['waiting_on']}",
        f"- next_decision: {snapshot['next_decision']}",
        f"- human_intervention_required: {str(snapshot['human_intervention_required']).lower()}",
        f"- project_summary: {snapshot['project_summary']}",
    ]
    lines.extend(["", "## Progress"])
    lines.append(f"- completed_steps: {', '.join(str(step) for step in snapshot['completed_steps']) or 'none'}")
    lines.append(f"- remaining_steps: {', '.join(str(step) for step in snapshot['remaining_steps']) or 'none'}")
    lines.extend(["", "## 9-step progress"])
    for item in snapshot.get("step_progress", []):
        lines.append(
            f"- Step {item['step']}: {item['label']} | status={item['status']} "
            f"| gate_type={item.get('gate_type')} | gate_state={item.get('gate_state')} "
            f"| approval_state={item.get('approval_state')} | approval={item['approval']} "
            f"| report={item['report']}"
        )
    lines.extend(["", "## Blockers"])
    if snapshot["blockers"]:
        for blocker in snapshot["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_status_snapshot(root: str | Path, change_id: str | None = None, output_path: str | Path | None = None) -> str:
    snapshot = render_status_snapshot(root, change_id)
    paths = GovernancePaths(Path(root))
    target = Path(output_path) if output_path else paths.status_snapshot_file(snapshot["change_id"])
    write_yaml(target, snapshot)
    return str(target)


def format_step_matrix_view(matrix: dict) -> str:
    lines = [
        f"# Step Matrix View: {matrix['change_id']}",
        "",
        "## Current position",
        f"- Flow section: {matrix['current_flow_section']}",
        f"- Current step: {matrix['current_step']}",
        f"- Current action: {matrix['current_action_label']}",
        f"- Current status: {matrix['current_status']}",
        f"- Current owner / stage actor: {matrix['owner_or_stage_actor']}",
        f"- Goal summary: {matrix['goal_summary']}",
    ]
    if matrix.get("next_step"):
        lines.extend([
            "",
            "## Next",
            f"- Next step: {matrix['next_step']}",
            f"- Next action: {matrix['next_action_label']}",
            f"- Next owner / stage actor: {matrix['next_owner_or_stage_actor']}",
        ])
    lines.extend(["", "## Validation objects"])
    for item in matrix["validation_objects"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Expected outputs"])
    for output in matrix["expected_outputs"]:
        lines.append(f"- {output}")
    lines.extend(["", "## Human intervention points"])
    for point in matrix["human_intervention_points"]:
        lines.append(
            f"- Step {point['step']}: {point['action']} | gate={point['gate']} | owner={point['owner']}"
        )
    lines.extend(["", "## Action guide"])
    for action in matrix["action_guide"]:
        lines.append(
            f"- Step {action['step']}: {action['label']} | section={action['flow_section']} | owner={action['owner']} | human_intervention={action['requires_human_intervention']}"
        )
        lines.append(f"  - purpose: {action['purpose']}")
    lines.extend(["", "## Blockers"])
    if matrix["blockers"]:
        for blocker in matrix["blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_step_matrix_view(root: str | Path, change_id: str | None = None, output_path: str | Path | None = None) -> str:
    matrix = render_step_matrix(root, change_id)
    paths = GovernancePaths(Path(root))
    target = Path(output_path) if output_path else paths.change_file(matrix["change_id"], "STEP_MATRIX_VIEW.md")
    target.write_text(format_step_matrix_view(matrix), encoding="utf-8")
    return str(target)


def _goal_summary(tasks_text: str, contract: dict) -> str:
    for line in tasks_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("- [ ]"):
            return stripped
    return contract.get("objective") or "bounded governance execution"


def _load_bindings(paths: GovernancePaths, change_id: str) -> dict:
    bindings_path = paths.change_file(change_id, "bindings.yaml")
    if not bindings_path.exists():
        return {}
    return load_yaml(bindings_path)


def _normalize_step(step) -> int | str:
    if isinstance(step, int):
        return step
    if isinstance(step, str) and step.isdigit():
        return int(step)
    return step


def _next_step(current_step: int | str) -> int | None:
    if isinstance(current_step, int) and current_step < STEP_MATRIX_TOTAL_STEPS:
        return current_step + 1
    return None


def _resolve_step_owner(current_step, bindings: dict, manifest: dict, current_status: str | None) -> str:
    roles = manifest.get("roles", {})
    step_binding = _step_binding(bindings, current_step)
    if step_binding.get("owner"):
        return step_binding["owner"]
    if current_step == 6 or str(current_status).startswith("step6"):
        return roles.get("executor") or "executor"
    if current_step == 5 or str(current_status).startswith("dispatch"):
        return roles.get("formal_orchestrator") or roles.get("reviewer") or "dispatch-prep"
    if current_step == 7:
        return roles.get("reviewer") or roles.get("verifier") or "verifier"
    if current_step in {8, 9}:
        return roles.get("reviewer") or roles.get("formal_orchestrator") or "governance"
    return roles.get("formal_orchestrator") or roles.get("executor") or "governance"


def _expected_outputs_for_step(current_step, change_id: str, contract: dict) -> list[str]:
    validation_objects = list(contract.get("validation_objects", []))
    if current_step == 6:
        outputs = [
            f".governance/changes/{change_id}/STATE_CONSISTENCY_CHECK.yaml",
            f".governance/changes/{change_id}/STEP_MATRIX_VIEW.md",
            f".governance/changes/{change_id}/ROUND_ENTRY_INPUT_SUMMARY.yaml",
            f".governance/changes/{change_id}/STEP6_EXECUTION_SUMMARY.yaml",
        ]
        outputs.extend([f"validation_object:{item}" for item in validation_objects])
        return outputs
    if validation_objects:
        return [f"validation_object:{item}" for item in validation_objects]
    return [f"step {current_step} outputs remain bounded to the active change package"]


def _action_guide(bindings: dict, manifest: dict, current_status: str | None) -> list[dict]:
    actions = []
    for step in range(1, STEP_MATRIX_TOTAL_STEPS + 1):
        step_binding = _step_binding(bindings, step)
        actions.append({
            "step": step,
            "label": STEP_LABELS[step],
            "flow_section": FLOW_SECTIONS[step],
            "owner": _resolve_step_owner(step, bindings, manifest, current_status),
            "gate": step_binding.get("gate") or _default_gate(step),
            "requires_human_intervention": _requires_human_intervention(step, step_binding),
            "purpose": ACTION_PURPOSES[step],
        })
    return actions


def _human_intervention_points(bindings: dict, manifest: dict, current_status: str | None) -> list[dict]:
    points = []
    for step in range(1, STEP_MATRIX_TOTAL_STEPS + 1):
        step_binding = _step_binding(bindings, step)
        if _requires_human_intervention(step, step_binding):
            points.append({
                "step": step,
                "action": STEP_LABELS[step],
                "gate": step_binding.get("gate") or _default_gate(step),
                "owner": _resolve_step_owner(step, bindings, manifest, current_status),
            })
    return points


def _requires_human_intervention(step: int, step_binding: dict) -> bool:
    gate = str(step_binding.get("gate") or _default_gate(step))
    if gate in {"approval-required", "review-required"}:
        return True
    return step in DEFAULT_HUMAN_INTERVENTION_STEPS


def _step_binding(bindings: dict, step: int | str) -> dict:
    steps = bindings.get("steps", {})
    return steps.get(step) or steps.get(str(step)) or steps.get(int(step)) or {}


def _default_gate(step: int) -> str:
    if step in APPROVAL_REQUIRED_STEPS:
        return "approval-required"
    if step in REVIEW_REQUIRED_STEPS:
        return "review-required"
    if step == 6:
        return "auto-pass-to-step7"
    return "guided"


def _phase_index_for_step(current_step: int | str) -> int:
    if not isinstance(current_step, int):
        return 1
    if current_step <= 2:
        return 1
    if current_step <= 5:
        return 2
    if current_step <= 7:
        return 3
    return 4


def _next_human_decision_step(current_step: int | str, gates: dict | None = None) -> int | None:
    if not isinstance(current_step, int):
        return None
    approvals = gates.get("approvals", {}) if isinstance(gates, dict) else {}
    if not isinstance(approvals, dict):
        approvals = {}
    for step in range(current_step, STEP_MATRIX_TOTAL_STEPS + 1):
        approval = approvals.get(step) or approvals.get(str(step)) or approvals.get(f"'{step}'") or {}
        if step in APPROVAL_REQUIRED_STEPS and approval.get("status") != "approved":
            return step
    return None


def _resolve_waiting_on(current_step: int | str, blockers: list[str]) -> str:
    if blockers:
        return blockers[0]
    if current_step == 5:
        return "Step 6 entry readiness and dispatch confirmation"
    if current_step == 6:
        return "Step 7 verify outputs and review-ready decision"
    if current_step == 7:
        return "Verification closure and review entry readiness"
    if current_step == 8:
        return "Review decision closure and archive entry readiness"
    if current_step == 9:
        return "Archive receipt and maintenance baseline refresh"
    return "Current phase completion and next-step readiness"


def _resolve_next_decision(step: int | None) -> str:
    if not step:
        return "none"
    return f"Step {step} / {STEP_LABELS[step]}"


def _current_step_requires_human(current_step: int | str, points: list[dict]) -> bool:
    if not isinstance(current_step, int):
        return False
    return any(point["step"] == current_step for point in points)


def _load_human_gates(paths: GovernancePaths, change_id: str) -> dict:
    path = paths.change_file(change_id, "human-gates.yaml")
    return load_yaml(path) if path.exists() else {}


def _step_progress(paths: GovernancePaths, change_id: str, current_step: int | str, gates: dict, bindings: dict) -> list[dict]:
    approvals = gates.get("approvals") or {}
    items = []
    for step in range(1, STEP_MATRIX_TOTAL_STEPS + 1):
        approval = approvals.get(step) or approvals.get(str(step)) or {}
        binding = _step_binding(bindings, step)
        gate_type = _gate_type_for_step(step, binding)
        gate_state = _gate_state_for_step(step, current_step, gate_type, approval)
        approval_state = _approval_state_for_step(gate_type, approval)
        items.append({
            "step": step,
            "label": STEP_LABELS[step],
            "status": _progress_status(step, current_step),
            "gate_type": gate_type,
            "gate_state": gate_state,
            "approval_state": approval_state,
            "approval": _legacy_approval_for_step(gate_type, approval_state),
            "report": f".governance/changes/{change_id}/step-reports/step-{step}.md",
        })
    return items


def _legacy_approval_for_step(gate_type: str, approval_state: str) -> str:
    if gate_type != "approval-required":
        return "not-required"
    if approval_state == "required-pending":
        return "pending"
    return approval_state


def _gate_type_for_step(step: int, binding: dict) -> str:
    gate = str(binding.get("gate") or _default_gate(step))
    if gate == "auto-pass":
        return "auto-pass-to-step7"
    if gate in {"approval-required", "review-required", "auto-pass-to-step7"}:
        return gate
    if step in APPROVAL_REQUIRED_STEPS:
        return "approval-required"
    if step in REVIEW_REQUIRED_STEPS:
        return "review-required"
    if step == 6:
        return "auto-pass-to-step7"
    return "not-required"


def _gate_state_for_step(step: int, current_step: int | str, gate_type: str, approval: dict) -> str:
    if approval.get("status") == "bypassed":
        return "bypassed"
    if approval.get("status") == "approved" and gate_type == "review-required":
        return "reviewed"
    if approval.get("status") == "approved":
        return "approved"
    progress_status = _progress_status(step, current_step)
    if gate_type == "approval-required":
        if progress_status == "current":
            return "waiting-approval"
        if progress_status == "completed":
            return "blocked"
        return "not-started"
    if gate_type == "review-required":
        if progress_status == "current":
            return "waiting-review"
        if progress_status == "completed":
            return "reviewed"
        return "not-started"
    if gate_type == "auto-pass-to-step7":
        if progress_status == "completed":
            return "approved"
        if progress_status == "current":
            return "not-required"
        return "not-started"
    return "not-required"


def _approval_state_for_step(gate_type: str, approval: dict) -> str:
    if gate_type != "approval-required":
        return "not-required"
    if approval.get("status") == "approved":
        return "approved"
    if approval.get("status") == "bypassed":
        return "bypassed"
    return "required-pending"


def _progress_status(step: int, current_step: int | str) -> str:
    if not isinstance(current_step, int):
        return "pending"
    if step < current_step:
        return "completed"
    if step == current_step:
        return "current"
    return "pending"
