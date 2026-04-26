from __future__ import annotations

from pathlib import Path

from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml
from .step_matrix import STEP_LABELS, render_status_snapshot


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
        "lifecycle: idle",
        "当前状态：idle / 等待下一轮意图",
        f"最近归档变更：{last_change}",
        f"最近归档时间：{last_archive_at}",
        "当前 owner：human-sponsor",
        "下一步建议：捕获下一轮项目意图、参与者、范围和验收标准后再打开执行。",
        "需要人类决策：决定是否开启新 change，或继续保持 idle。",
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
    current_step = snapshot["current_step"]
    step_label = STEP_LABELS.get(current_step, str(current_step))
    return "\n".join([
        "# open-cowork Current State",
        "",
        f"项目目标：{snapshot['project_summary']}",
        f"当前变更：{change_id}",
        f"标题：{manifest.get('title') or change_id}",
        f"当前步骤：Step {current_step} / {step_label}",
        f"传统映射说明：{snapshot['current_phase']}",
        f"当前 owner：{snapshot['current_owner']}",
        f"当前等待：{snapshot['waiting_on']}",
        f"下一项决策：{snapshot['next_decision']}",
        f"是否需要人类介入：{'是' if snapshot['human_intervention_required'] else '否'}",
        f"Intent confirmation：{intent.get('status') or 'missing'}",
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
