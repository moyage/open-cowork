from __future__ import annotations

from pathlib import Path

from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml
from .step_matrix import render_status_snapshot


def sync_current_state(root: str | Path, change_id: str | None = None) -> str:
    paths = GovernancePaths(Path(root))
    paths.governance_dir.mkdir(parents=True, exist_ok=True)
    current = read_current_change(paths.root)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    resolved_change_id = change_id or current.get("current_change_id") or nested.get("change_id")
    status = current.get("status") or nested.get("status")
    if not resolved_change_id or status in {"idle", "archived", "none", None}:
        text = _idle_current_state(paths)
    else:
        text = _active_current_state(paths, str(resolved_change_id))
    target = paths.governance_dir / "current-state.md"
    target.write_text(text, encoding="utf-8")
    return str(target)


def _idle_current_state(paths: GovernancePaths) -> str:
    maintenance = load_yaml(paths.maintenance_status_file()) if paths.maintenance_status_file().exists() else {}
    last_change = maintenance.get("last_archived_change")
    last_archive_at = maintenance.get("last_archive_at")
    return "\n".join([
        "# open-cowork Current State",
        "",
        "Lifecycle: idle",
        f"Last archived change: {last_change}",
        f"Last archive at: {last_archive_at}",
        "Current phase: idle / 等待下一轮意图",
        "Current owner: human-sponsor",
        "Next recommended action: capture the next project intent, participants, scope, and acceptance before opening execution.",
        "Need human decision: decide whether to start a new change or keep the project idle.",
        "",
        "## Read next / 下一步读取",
        "",
        "- `.governance/AGENTS.md`",
        "- `.governance/agent-playbook.md`",
        "- `.governance/index/maintenance-status.yaml`",
        "",
    ])


def _active_current_state(paths: GovernancePaths, change_id: str) -> str:
    snapshot = render_status_snapshot(paths.root, change_id)
    manifest = load_yaml(paths.change_file(change_id, "manifest.yaml"))
    intent_path = paths.change_file(change_id, "intent-confirmation.yaml")
    intent = load_yaml(intent_path) if intent_path.exists() else {}
    return "\n".join([
        "# open-cowork Current State",
        "",
        f"Project goal: {snapshot['project_summary']}",
        f"Active change: {change_id}",
        f"Title: {manifest.get('title') or change_id}",
        f"Lifecycle: {snapshot['current_status']}",
        f"Current phase: {snapshot['current_phase']}",
        f"Current step: Step {snapshot['current_step']} / {snapshot.get('current_status')}",
        f"Current owner: {snapshot['current_owner']}",
        f"Waiting on: {snapshot['waiting_on']}",
        f"Next decision: {snapshot['next_decision']}",
        f"Human intervention required: {str(snapshot['human_intervention_required']).lower()}",
        f"Intent confirmation: {intent.get('status') or 'missing'}",
        "",
        "## Read next / 下一步读取",
        "",
        f"- `.governance/changes/{change_id}/contract.yaml`",
        f"- `.governance/changes/{change_id}/bindings.yaml`",
        f"- `.governance/changes/{change_id}/intent-confirmation.yaml`",
        f"- `.governance/changes/{change_id}/step-reports/`",
        "- `.governance/agent-playbook.md`",
        "",
    ])
