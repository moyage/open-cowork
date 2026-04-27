from __future__ import annotations

from pathlib import Path

from .current_state import sync_current_state
from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import write_yaml
from .step_matrix import STEP_LABELS, render_status_snapshot


def build_project_activation(root: str | Path) -> dict:
    paths = GovernancePaths(Path(root).expanduser().resolve())
    activation = {
        "schema": "project-activation/v1",
        "project_scope": "project-level",
        "root": str(paths.root),
        "governance_state": "missing",
        "recommended_mode": "install-or-initialize",
        "active_change": None,
        "recommended_read_set": [
            ".governance/AGENTS.md",
            ".governance/current-state.md",
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
    current = read_current_change(paths.root)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    change_id = current.get("current_change_id") or nested.get("change_id")
    status = current.get("status") or nested.get("status") or "idle"
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

    snapshot = render_status_snapshot(paths.root, str(change_id))
    sync_current_state(paths.root, str(change_id))
    current_step = snapshot.get("current_step")
    active_read_set = [
        ".governance/AGENTS.md",
        ".governance/current-state.md",
        ".governance/agent-playbook.md",
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
        "recommended_read_set": active_read_set,
        "agent_instructions": [
            "continue the active change; do not reinstall unless .governance is missing.",
            "Read the recommended set before acting.",
            "Respect the active contract scope and the current single-step gate.",
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
    lines.extend(["", "Recommended read set:"])
    for item in payload.get("recommended_read_set", []):
        lines.append(f"- {item}")
    lines.extend(["", "Agent instructions:"])
    for item in payload.get("agent_instructions", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_activation(paths: GovernancePaths, payload: dict) -> None:
    paths.governance_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(paths.governance_dir / "PROJECT_ACTIVATION.yaml", payload)
