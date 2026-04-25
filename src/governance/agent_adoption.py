from __future__ import annotations

import re
from pathlib import Path


DEFAULT_RECOMMENDED_READ_SET = [
    ".governance/current-state.md",
    ".governance/index/current-change.yaml",
    ".governance/agent-playbook.md",
]


def build_adoption_plan(
    root: str | Path,
    *,
    target: str | Path,
    goal: str,
    source_docs: list[str] | None = None,
    agent_inventory: list[str] | None = None,
) -> dict:
    from .index import read_current_change

    root_path = Path(root)
    target_path = Path(target).expanduser().resolve()
    current = read_current_change(root_path)
    nested_current = current.get("current_change", {})
    if not isinstance(nested_current, dict):
        nested_current = {}
    active_change_id = current.get("current_change_id") or nested_current.get("change_id")
    active_status = current.get("status") or nested_current.get("status")
    requires_lifecycle_decision = bool(active_change_id and active_status not in {"idle", "archived", "abandoned", "superseded"})
    candidate_change_id = _candidate_change_id(goal)
    source_docs = list(source_docs or [])
    agent_inventory = list(agent_inventory or [])
    recommended_read_set = [
        *DEFAULT_RECOMMENDED_READ_SET,
        f".governance/changes/{active_change_id}/contract.yaml" if active_change_id else ".governance/changes/<change-id>/contract.yaml",
        f".governance/changes/{active_change_id}/bindings.yaml" if active_change_id else ".governance/changes/<change-id>/bindings.yaml",
    ]
    return {
        "schema": "adoption-plan/v1",
        "target": str(target_path),
        "goal": goal,
        "candidate_change": {
            "change_id": candidate_change_id,
            "title": _candidate_title(goal),
            "scope_in": ["src/**", "tests/**", "docs/**"],
            "scope_out": [
                ".governance/index/**",
                ".governance/archive/**",
                ".governance/runtime/**",
            ],
            "verify_commands": ["python3 -m unittest discover -s tests"],
        },
        "source_docs": source_docs,
        "active_change": {
            "change_id": active_change_id,
            "status": active_status,
            "requires_lifecycle_decision": requires_lifecycle_decision,
            "allowed_policies": ["continue", "supersede", "abandon", "archive-first", "force"] if requires_lifecycle_decision else ["prepare"],
        },
        "recommended_read_set": recommended_read_set,
        "role_suggestions": _suggest_roles(agent_inventory),
        "human_decisions_needed": _human_decisions_needed(requires_lifecycle_decision, bool(agent_inventory)),
        "mutation": "none",
    }


def write_agent_adoption_pack(
    root: str | Path,
    *,
    change_id: str,
    title: str,
    goal: str,
    profile: str,
    bindings: dict,
) -> None:
    governance_dir = Path(root) / ".governance"
    governance_dir.mkdir(parents=True, exist_ok=True)
    (governance_dir / "AGENTS.md").write_text(_agent_entry(change_id), encoding="utf-8")
    (governance_dir / "agent-playbook.md").write_text(_agent_playbook(change_id), encoding="utf-8")
    (governance_dir / "current-state.md").write_text(
        _current_state(change_id, title, goal, profile, bindings),
        encoding="utf-8",
    )


def _agent_entry(change_id: str) -> str:
    return "\n".join([
        "# Agent-first open-cowork project",
        "",
        "本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。",
        "",
        "## 优先读取",
        "",
        "1. `.governance/current-state.md`：人和 Agent 都能读的项目状态。",
        "2. `.governance/agent-playbook.md`：Agent 操作规则。",
        f"3. `.governance/changes/{change_id}/contract.yaml`：执行边界。",
        f"4. `.governance/changes/{change_id}/bindings.yaml`：owner 和角色绑定。",
        "",
        "只读取当前 active working set。不要默认全文扫描 `docs/archive/plans/**`；历史文档只在明确需要追溯 source docs 时按路径读取。",
        "",
        "## 操作规则",
        "",
        "Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, archive, and continuity.",
        "",
        "## 硬边界",
        "",
        "- 未经人明确同意，不要在 `scope_in` 之外执行。",
        "- 不要让 executor 自己批准最终 review。",
        "- review 通过前不要 archive。",
        "- 不要在执行过程中暗中改写 contract 或 bindings。",
        "",
    ])


def _agent_playbook(change_id: str) -> str:
    return "\n".join([
        "# open-cowork Agent Playbook",
        "",
        "## 触发语句",
        "",
        "当人说 `安装 open-cowork，并在当前项目中实施这套协同治理框架`，或要求用 open-cowork 推进当前任务时，请按本手册执行。",
        "",
        "## Agent 职责",
        "",
        "1. 行动前先理解项目目标。",
        "2. 保持 `.governance/current-state.md` 与 active change 对齐。",
        f"3. 使用 `.governance/changes/{change_id}/contract.yaml` 作为执行边界。",
        f"4. 使用 `.governance/changes/{change_id}/bindings.yaml` 作为 owner 映射。",
        "5. Step 6 前先确认 participants profile、intent confirmation 和当前 step report。",
        "6. verify、review 或 archive 前先记录客观 evidence。",
        "7. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。",
        "8. 上下文预算优先：先读 recommended read set，不要把归档计划整包加载进会话。",
        "",
        "## Human update template",
        "",
        "当前项目推进状态",
        "",
        "- Project goal:",
        "- Current phase:",
        "- Current step:",
        "- Current owner:",
        "- Completed:",
        "- Current blocker:",
        "- Next recommended action:",
        "- Need human decision:",
        "- Agent next action:",
        "",
        "不要把命令执行当成汇报标题。优先汇报项目进展、owner、阻断、下一步和需要人决策的事项。",
        "",
    ])


def _current_state(change_id: str, title: str, goal: str, profile: str, bindings: dict) -> str:
    global_bindings = bindings.get("global", {}) if isinstance(bindings, dict) else {}
    return "\n".join([
        "# open-cowork Current State",
        "",
        f"Project goal: {goal}",
        f"Active change: {change_id}",
        f"Title: {title}",
        f"Profile: {profile}",
        "Current phase: Phase 2 / 方案与准备",
        "Current step: Step 5 / Approve the start",
        "Current owner: orchestrator-agent",
        "Next recommended action: executor-agent reads the contract and executes only inside scope_in, then records evidence.",
        "Need human decision: confirm participants, intent, scope, risk, and reviewer separation before execution if uncertain.",
        "",
        "## Owners / 角色绑定",
        "",
        f"Sponsor: {global_bindings.get('sponsor', 'human-sponsor')}",
        f"Orchestrator: {global_bindings.get('orchestrator', 'orchestrator-agent')}",
        f"Executor: {global_bindings.get('default_executor', 'executor-agent')}",
        f"Verifier: {global_bindings.get('default_verifier', 'verifier-agent')}",
        f"Reviewer: {global_bindings.get('default_reviewer', 'independent-reviewer')}",
        f"Maintainer: {global_bindings.get('default_maintainer', 'maintainer-agent')}",
        "",
        "## Read next / 下一步读取",
        "",
        f"- `.governance/changes/{change_id}/contract.yaml`",
        f"- `.governance/changes/{change_id}/bindings.yaml`",
        f"- `.governance/changes/{change_id}/intent-confirmation.yaml`",
        f"- `.governance/changes/{change_id}/step-reports/`",
        "- `.governance/agent-playbook.md`",
        "",
        "## Context budget / 上下文预算",
        "",
        "- 默认只读取 active working set。",
        "- 不要批量读取 `docs/archive/plans/**`。",
        "- source docs 先作为路径引用，需要核实时再单独读取。",
        "",
    ])


def _candidate_change_id(goal: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", goal.lower()).strip("-")
    return slug[:72] or "agent-first-adoption"


def _candidate_title(goal: str) -> str:
    return goal.strip()[:80] or "Agent-first adoption"


def _suggest_roles(agent_inventory: list[str]) -> dict[str, list[str]]:
    suggestions: dict[str, list[str]] = {}
    for agent in agent_inventory:
        normalized = agent.strip()
        lowered = normalized.lower()
        if not normalized:
            continue
        if "openclaw" in lowered or "hermes" in lowered:
            suggestions[normalized] = ["orchestrator"]
        elif "codex" in lowered:
            suggestions[normalized] = ["executor", "verifier"]
        elif "ooso" in lowered:
            suggestions[normalized] = ["reviewer", "verification_assistant"]
        else:
            suggestions[normalized] = ["participant"]
    return suggestions


def _human_decisions_needed(requires_lifecycle_decision: bool, has_agent_inventory: bool) -> list[str]:
    decisions = []
    if requires_lifecycle_decision:
        decisions.append("Choose active change policy before mutating governance state.")
    if has_agent_inventory:
        decisions.append("Confirm role bindings before writing bindings.yaml.")
    decisions.append("Confirm scope and verification command before Step 6 execution.")
    return decisions
