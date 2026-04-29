from __future__ import annotations

from pathlib import Path

from .contract import ContractValidationError
from .current_state import sync_current_state
from .index import read_active_changes, read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml
from .simple_yaml import write_yaml
from .step_matrix import STEP_LABELS, render_status_snapshot
from .context_pack import context_read_set
from .lean_state import load_lean_state


LEAN_CONTEXT_DISCIPLINE = [
    "Do not full-scan cold history, archives, session JSONL, or large logs unless a state entry points to a specific path.",
    "Write large outputs to files and cite evidence refs or short summaries in chat.",
    "Keep tool output bounded with targeted reads, filters, and summaries; prefer current-state.md and state.yaml for resume.",
    "After compact failure, recover from the generated handoff and last successful evidence, not the full failed transcript.",
]


def build_project_activation(root: str | Path, change_id: str | None = None, *, list_only: bool = False) -> dict:
    paths = GovernancePaths(Path(root).expanduser().resolve())
    activation = {
        "schema": "project-activation/v1",
        "project_scope": "project-level",
        "root": str(paths.root),
        "protocol_trigger": "command",
        "trigger_command": "ocw resume",
        "governance_state": "missing",
        "recommended_mode": "install-or-initialize",
        "active_change": None,
        "recommended_read_set": [
            ".governance/AGENTS.md",
            _current_state_path(paths),
            ".governance/agent-playbook.md",
        ],
        "agent_instructions": [
            "Install or initialize open-cowork in this project before governing work.",
            "Do not rely on chat history as the source of truth.",
        ],
    }
    if not paths.governance_dir.exists():
        return activation

    activation["governance_state"] = "installed"
    if _is_lean_only(paths):
        return _activation_for_lean_state(paths, activation, list_only=list_only)

    active_changes = _active_changes(paths)
    activation["active_changes"] = active_changes
    if list_only:
        activation.update({
            "recommended_mode": "choose-active-change" if active_changes else "open-new-change",
            "active_change": None,
            "agent_instructions": [
                "List mode only: select the intended work item with ocw resume --change-id <change-id>.",
                "Do not infer the target change from chat history or natural-language keywords.",
            ] if active_changes else [
                "No active changes were found in this project.",
                "Ask the human for the next project intent before opening a new change.",
            ],
        })
        return activation
    if change_id:
        selected = _find_active_change(paths, change_id)
        if not selected:
            activation.update({
                "recommended_mode": "change-not-found",
                "active_change": None,
                "agent_instructions": [
                    f"Requested change '{change_id}' was not found in active changes or .governance/changes.",
                    "Run resume without --change-id to inspect available project work.",
                ],
            })
            _write_activation(paths, activation)
            return activation
        return _activation_for_change(paths, activation, str(change_id), selected)

    current = read_current_change(paths.root)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    change_id = current.get("current_change_id") or nested.get("change_id")
    status = current.get("status") or nested.get("status") or "idle"
    if len(active_changes) > 1:
        activation.update({
            "recommended_mode": "choose-active-change",
            "active_change": None,
            "agent_instructions": [
                "Multiple active changes exist in this project.",
                "Select the intended work item with deterministic resume: ocw resume --change-id <change-id>.",
                "Do not infer the target change from chat history or from another Agent session.",
            ],
        })
        _write_activation(paths, activation)
        return activation
    if len(active_changes) == 1 and (
        not change_id or status in {"idle", "archived", "abandoned", "superseded", "none"}
    ):
        selected = active_changes[0]
        return _activation_for_change(paths, activation, str(selected["change_id"]), selected)
    if not change_id or status in {"idle", "archived", "abandoned", "superseded", "none"}:
        activation.update({
            "recommended_mode": "open-new-change",
            "active_change": None,
            "agent_instructions": [
                "Continue from project governance facts; do not reinstall unless .governance is missing.",
                "Ask the human for the next project intent before opening a new change.",
            ],
        })
        _write_activation(paths, activation)
        return activation

    return _activation_for_change(paths, activation, str(change_id), nested)


def _activation_for_change(paths: GovernancePaths, activation: dict, change_id: str, selected: dict) -> dict:
    try:
        snapshot = render_status_snapshot(paths.root, str(change_id))
        sync_current_state(paths.root, str(change_id))
        current_step = snapshot.get("current_step")
    except ContractValidationError as exc:
        current_step = selected.get("current_step") or 1
        activation.update({
            "recommended_mode": "continue-draft-change",
            "active_change": {
                "change_id": str(change_id),
                "status": selected.get("status") or "drafting",
                "current_step": current_step,
                "current_step_name": STEP_LABELS.get(current_step, str(current_step)),
                "current_phase": "Phase 1 / 定义与对齐",
                "current_owner": selected.get("owner") or "orchestrator",
                "waiting_on": "contract.yaml and bindings.yaml",
                "next_decision": f"Step {current_step} / {STEP_LABELS.get(current_step, current_step)}",
            },
            "execution_preflight": _execution_preflight(paths.root, str(change_id)),
            "recommended_read_set": [
                ".governance/AGENTS.md",
                _current_state_path(paths),
                ".governance/agent-playbook.md",
                _agent_entry_path(paths),
                f".governance/changes/{change_id}/manifest.yaml",
                f".governance/changes/{change_id}/contract.yaml",
                f".governance/changes/{change_id}/bindings.yaml",
            ],
            "agent_instructions": [
                "Continue the selected draft change; do not reinstall unless .governance is missing.",
                "Complete contract.yaml and bindings.yaml before execution.",
                f"Draft activation detail: {exc}",
            ],
        })
        _write_activation(paths, activation)
        return activation
    context_reads = context_read_set(paths.root, str(change_id))
    active_read_set = [
        ".governance/AGENTS.md",
        _current_state_path(paths),
        ".governance/agent-playbook.md",
        _agent_entry_path(paths),
        *context_reads,
        f".governance/changes/{change_id}/contract.yaml",
        f".governance/changes/{change_id}/bindings.yaml",
        f".governance/changes/{change_id}/step-reports/step-{current_step}.md",
    ]
    activation.update({
        "recommended_mode": "continue-active-change",
        "active_change": {
            "change_id": str(change_id),
            "status": snapshot.get("current_status"),
            "current_step": current_step,
            "current_step_name": STEP_LABELS.get(current_step, str(current_step)),
            "current_phase": snapshot.get("current_phase"),
            "current_owner": snapshot.get("current_owner"),
            "waiting_on": snapshot.get("waiting_on"),
            "next_decision": snapshot.get("next_decision"),
        },
        "execution_preflight": _execution_preflight(paths.root, str(change_id)),
        "recommended_read_set": active_read_set,
        "agent_instructions": [
            "continue the active change; do not reinstall unless .governance is missing.",
            "Read the recommended set before acting.",
            *(
                ["Context pack is a pointer to authoritative governance facts."]
                if context_reads else []
            ),
            "Respect the active contract scope and the current single-step gate.",
            "Run execution preflight before modifying project files; do not treat open-cowork evidence as optional backfill.",
            "Report goal, current step, owner, blockers, next action, and human decision needed.",
        ],
    })
    _write_activation(paths, activation)
    return activation


def format_project_activation(payload: dict) -> str:
    active = payload.get("active_change") or {}
    lines = [
        "open-cowork project activation",
        "",
        f"- project_scope: {payload.get('project_scope')}",
        f"- protocol_trigger: {payload.get('protocol_trigger')}",
        f"- governance_state: {payload.get('governance_state')}",
        f"- recommended_mode: {payload.get('recommended_mode')}",
    ]
    if active:
        lines.extend([
            f"- active_change_id: {active.get('change_id')}",
            f"- current_status: {active.get('status')}",
            f"- current_step: {active.get('current_step')}",
            f"- current_step_name: {active.get('current_step_name')}",
            f"- current_owner: {active.get('current_owner')}",
            f"- waiting_on: {active.get('waiting_on')}",
            f"- next_decision: {active.get('next_decision')}",
        ])
    active_round = payload.get("active_round") or {}
    if active_round:
        lines.extend([
            f"- active_round_id: {active_round.get('round_id')}",
            f"- current_phase: {active_round.get('phase')}",
            f"- current_owner: {active_round.get('owner_agent')}",
            f"- waiting_on: {active_round.get('waiting_on')}",
            f"- next_decision: {active_round.get('next_decision')}",
        ])
    preflight = payload.get("execution_preflight") or {}
    if preflight:
        lines.extend([
            "",
            "Execution preflight:",
            f"- can_modify_project_files: {str(preflight.get('can_execute')).lower()}",
            f"- reason: {preflight.get('reason')}",
            f"- required_action: {preflight.get('required_action')}",
        ])
    active_changes = payload.get("active_changes") or []
    if active_changes:
        lines.extend(["", "Active changes:"])
        for item in active_changes:
            lines.append(
                "- "
                f"{item.get('change_id')} "
                f"status={item.get('status')} "
                f"step={item.get('current_step')} "
                f"title={item.get('title') or ''}".rstrip()
            )
    lines.extend(["", "Recommended read set:"])
    for item in payload.get("recommended_read_set", []):
        lines.append(f"- {item}")
    context_discipline = payload.get("context_discipline") or []
    if context_discipline:
        lines.extend(["", "Context discipline:"])
        for item in context_discipline:
            lines.append(f"- {item}")
    lines.extend(["", "Agent instructions:"])
    for item in payload.get("agent_instructions", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_activation(paths: GovernancePaths, payload: dict) -> None:
    paths.local_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(paths.project_activation_file(), payload)


def _is_lean_only(paths: GovernancePaths) -> bool:
    return (paths.governance_dir / "state.yaml").exists() and not paths.current_change_file().exists()


def _activation_for_lean_state(paths: GovernancePaths, activation: dict, *, list_only: bool) -> dict:
    state = load_lean_state(paths.root)
    active_round = state.get("active_round") or {}
    round_id = active_round.get("round_id") or ""
    participants = active_round.get("participants") or {}
    review = active_round.get("review") or {}
    verify = active_round.get("verify") or {}
    closeout = active_round.get("closeout") or {}
    recommended_mode = "choose-active-round" if list_only else "continue-active-round"
    activation.update({
        "recommended_mode": recommended_mode,
        "active_change": None,
        "active_round": {
            "round_id": round_id,
            "goal": active_round.get("goal") or "",
            "phase": active_round.get("phase") or "",
            "owner_agent": participants.get("owner_agent") or participants.get("executor") or "",
            "review_status": review.get("status") or "",
            "review_decision": review.get("decision") or "",
            "verify_status": verify.get("status") or "",
            "closeout_status": closeout.get("status") or "",
            "waiting_on": _lean_waiting_on(active_round),
            "next_decision": _lean_next_decision(active_round),
        },
        "recommended_read_set": [
            ".governance/AGENTS.md",
            ".governance/agent-entry.md",
            ".governance/agent-playbook.md",
            ".governance/current-state.md",
            ".governance/state.yaml",
        ],
        "context_discipline": LEAN_CONTEXT_DISCIPLINE,
        "agent_instructions": [
            "Continue from lean project governance facts; do not reinstall unless .governance is missing.",
            "Read the recommended set before acting.",
            "Respect active_round scope, gates, review independence, and evidence refs.",
            "Do not create or rely on legacy .governance/index/current-change.yaml for lean-only projects.",
            "Report goal, phase, owner, blockers, next action, and human decision needed.",
        ],
    })
    if list_only:
        activation["active_rounds"] = [activation["active_round"]] if round_id else []
    return activation


def _lean_waiting_on(active_round: dict) -> str:
    gates = active_round.get("gates") or {}
    execution_gate = gates.get("execution") or {}
    closeout_gate = gates.get("closeout") or {}
    review = active_round.get("review") or {}
    verify = active_round.get("verify") or {}
    closeout = active_round.get("closeout") or {}
    if execution_gate.get("status") != "approved":
        return "execution gate"
    if verify.get("status") not in {"passed", "complete", "completed"}:
        return "verification"
    if review.get("status") != "completed":
        return "independent review"
    if closeout_gate.get("status") != "approved" and closeout.get("status") != "closed":
        return "closeout gate"
    return "none"


def _lean_next_decision(active_round: dict) -> str:
    waiting_on = _lean_waiting_on(active_round)
    if waiting_on == "none":
        return "open next round or release preparation"
    return f"resolve {waiting_on}"


def _execution_preflight(root: str | Path, change_id: str) -> dict:
    try:
        from .preflight import check_execution_preflight

        return check_execution_preflight(root, change_id)
    except Exception as exc:
        return {
            "schema": "execution-preflight/v1",
            "can_execute": False,
            "reason": "preflight_unavailable",
            "required_action": f"resolve preflight error before modifying project files: {exc}",
        }


def _current_state_path(paths: GovernancePaths) -> str:
    if paths.current_state_file().exists():
        return ".governance/local/current-state.md"
    if paths.legacy_current_state_file().exists():
        return ".governance/current-state.md"
    return ".governance/local/current-state.md"


def _agent_entry_path(paths: GovernancePaths) -> str:
    if (paths.governance_dir / "agent-entry.md").exists():
        return ".governance/agent-entry.md"
    if (paths.governance_dir / "open-cowork-skill.md").exists():
        return ".governance/open-cowork-skill.md"
    return ".governance/agent-entry.md"


def _active_changes(paths: GovernancePaths) -> list[dict]:
    indexed = read_active_changes(paths.root).get("changes", [])
    if indexed:
        return indexed
    current = read_current_change(paths.root)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    change_id = current.get("current_change_id") or nested.get("change_id")
    status = current.get("status") or nested.get("status")
    if not change_id or status in {"idle", "archived", "abandoned", "superseded", "none", None}:
        return []
    return [{
        "change_id": str(change_id),
        "path": nested.get("path") or f".governance/changes/{change_id}",
        "status": status,
        "current_step": current.get("current_step") or nested.get("current_step"),
        "title": nested.get("title"),
        "owner": nested.get("owner"),
    }]


def _find_active_change(paths: GovernancePaths, change_id: str) -> dict:
    for item in _active_changes(paths):
        if str(item.get("change_id")) == str(change_id):
            return item
    manifest_path = paths.change_file(change_id, "manifest.yaml")
    if not manifest_path.exists():
        return {}
    manifest = load_yaml(manifest_path)
    if manifest.get("status") in {"idle", "archived", "abandoned", "superseded", "none", None}:
        return {}
    return {
        "change_id": change_id,
        "path": f".governance/changes/{change_id}",
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
        "title": manifest.get("title"),
        "owner": manifest.get("owner"),
    }
