from __future__ import annotations

import re
from pathlib import Path

from .defaults import DEFAULT_SCOPE_OUT
from .step_matrix import STEP_LABELS


DEFAULT_RECOMMENDED_READ_SET = [
    ".governance/agent-playbook.md",
    ".governance/agent-entry.md",
    ".governance/current-state.md",
    ".governance/state.yaml",
]


def build_adoption_plan(
    root: str | Path,
    *,
    target: str | Path,
    goal: str,
    source_docs: list[str] | None = None,
    agent_inventory: list[str] | None = None,
) -> dict:
    root_path = Path(root)
    target_path = Path(target).expanduser().resolve()
    active = _current_work(root_path)
    active_change_id = active.get("id")
    active_status = active.get("status")
    requires_lifecycle_decision = bool(active_change_id and active_status not in {"idle", "archived", "abandoned", "superseded"})
    candidate_change_id = _candidate_change_id(goal)
    source_docs = list(source_docs or [])
    agent_inventory = list(agent_inventory or [])
    recommended_read_set = _recommended_read_set(active)
    return {
        "schema": "adoption-plan/v1",
        "target": str(target_path),
        "goal": goal,
        "candidate_change": {
            "change_id": candidate_change_id,
            "title": _candidate_title(goal),
            "scope_in": ["src/**", "tests/**", "docs/**"],
            "scope_out": list(DEFAULT_SCOPE_OUT),
            "verify_commands": ["python3 -m unittest discover -s tests"],
        },
        "source_docs": source_docs,
        "active_change": {
            "change_id": active_change_id,
            "status": active_status,
            "kind": active.get("kind"),
            "requires_lifecycle_decision": requires_lifecycle_decision,
            "allowed_policies": ["continue", "supersede", "abandon", "archive-first", "force"] if requires_lifecycle_decision else ["prepare"],
        },
        "recommended_read_set": recommended_read_set,
        "human_control_baseline_next_actions": [
            "Configure participants and explicit step owner/reviewer mappings.",
            "Start at Step 1: clarify inputs and problem boundaries with the human sponsor.",
            "Step 5 approval is required before Step 6 execution begins.",
            "Agent records Step 5 approval internally with step approve after the human chooses approve.",
            "Step 8 review decision requires the configured independent reviewer and human-visible approval trace.",
            "Step 9 archive requires human approval and an archive receipt before the round is closed.",
        ],
        "role_suggestions": _suggest_roles(agent_inventory),
        "human_decisions_needed": _human_decisions_needed(requires_lifecycle_decision, bool(agent_inventory)),
        "mutation": "none",
    }


def _current_work(root_path: Path) -> dict:
    state_path = root_path / ".governance" / "state.yaml"
    current_change_path = root_path / ".governance" / "index" / "current-change.yaml"
    if state_path.exists() and not current_change_path.exists():
        from .project_state import load_project_state

        state = load_project_state(root_path)
        active_round = state.get("active_round") or {}
        return {
            "kind": "round",
            "id": active_round.get("round_id"),
            "status": active_round.get("phase"),
        }

    if current_change_path.exists():
        from .index import read_current_change

        current = read_current_change(root_path)
        nested_current = current.get("current_change", {})
        if not isinstance(nested_current, dict):
            nested_current = {}
        return {
            "kind": "change",
            "id": current.get("current_change_id") or nested_current.get("change_id"),
            "status": current.get("status") or nested_current.get("status"),
        }

    return {"kind": "none", "id": None, "status": "idle"}


def _recommended_read_set(active: dict) -> list[str]:
    items = list(DEFAULT_RECOMMENDED_READ_SET)
    if active.get("kind") == "change":
        change_id = active.get("id")
        items.extend([
            f".governance/changes/{change_id}/contract.yaml" if change_id else ".governance/changes/<change-id>/contract.yaml",
            f".governance/changes/{change_id}/bindings.yaml" if change_id else ".governance/changes/<change-id>/bindings.yaml",
        ])
    return items


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
    local_dir = governance_dir / "local"
    governance_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)
    _write_governance_gitignore(governance_dir)
    (governance_dir / "AGENTS.md").write_text(_agent_entry(), encoding="utf-8")
    (governance_dir / "agent-playbook.md").write_text(_agent_playbook(), encoding="utf-8")
    (governance_dir / "agent-entry.md").write_text(_agent_runtime_entry(), encoding="utf-8")
    (local_dir / "current-state.md").write_text(
        _current_state(change_id, title, goal, profile, bindings),
        encoding="utf-8",
    )


def _agent_entry() -> str:
    return "\n".join([
        "# Agent-first open-cowork project",
        "",
        "本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。",
        "",
        "## 优先读取",
        "",
        "1. `.governance/agent-entry.md`：任意 Agent 接手项目时的固定入口。",
        "2. `.governance/agent-playbook.md`：Agent 操作规则。",
        "3. `.governance/current-state.md`：当前可读状态摘要。",
        "4. `.governance/state.yaml`：current-state compact 权威状态。",
        "5. `ocw resume` 输出的 recommended read set：当前 round 的权威事实。",
        "",
        "只读取当前 active working set。不要默认全文扫描 `docs/archive/plans/**`；历史文档只在明确需要追溯 source docs 时按路径读取。",
        "",
        "## 操作规则",
        "",
        "Deterministic project entry: run `ocw resume` before continuing project work. Natural language is only a request to run the entry, not a platform Skill name.",
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


def _agent_runtime_entry() -> str:
    return "\n".join([
        "# open-cowork Agent Entry",
        "",
        "Use this project entry whenever a human asks any local Agent to continue, review, verify, or implement work in this project.",
        "",
        "This file is the project-scoped source of truth for Agent handoff. open-cowork is not a required platform Skill name; if a runtime says the Skill is unavailable, read this file as project instructions and continue from project facts.",
        "",
        "## Deterministic project entry",
        "",
        "- Reliable trigger: run `ocw resume` in the project root.",
        "- List work: run `ocw resume --list`.",
        "- Continue explicit work: run `ocw resume --change-id <change-id>`.",
        "- Natural-language phrasing is only a request to use the project entry; do not treat `open-cowork` as a missing platform Skill or reconstruct state from chat history.",
        "- `.governance/local/**` is a local projection, not team-authoritative truth.",
        "",
        "## Activation rule",
        "",
        "1. Treat open-cowork as project-scoped, not Agent-scoped.",
        "2. Run deterministic project resume internally before acting.",
        "3. If multiple active changes exist, select the explicit change requested by the human; otherwise ask for the change_id before execution.",
        "4. Read only the recommended read set from resume.",
        "5. Never reconstruct project state from chat history when `.governance/` facts exist.",
        "",
        "## Default internal activation",
        "",
        "- Use `ocw resume` to discover whether the project has one active change, multiple active changes, or no active change.",
        "- Use `ocw resume --change-id <change-id>` when the human has selected a specific work item.",
        "",
        "## Human-facing report",
        "",
        "Report in this shape, without exposing command lists:",
        "",
        "```text",
        "当前项目推进状态",
        "",
        "- 项目目标：",
        "- 当前 change：",
        "- 当前步骤：",
        "- 当前 Owner：",
        "- 已完成：",
        "- 当前阻断：",
        "- 下一步建议：",
        "- 需要你决策：",
        "- Agent 后续动作：",
        "```",
        "",
        "## Hard boundaries",
        "",
        "- Do not execute outside the active contract scope.",
        "- Do not let the executor approve its own final review.",
        "- Do not archive before review approval and Step 9 human approval.",
        "- Do not ask the human to memorize open-cowork CLI commands.",
        "",
    ])


def _agent_playbook() -> str:
    return "\n".join([
        "# open-cowork Agent Playbook",
        "",
        "## 触发语句",
        "",
        "当人要求继续、接手、审查、验证或发布本项目工作时，先运行项目入口 `ocw resume`。自然语言只是请求入口，不是平台 Skill 名称。",
        "",
        "## Agent 职责",
        "",
        "1. 行动前先理解项目目标。",
        "2. 先做项目级 resume；多 active round 时必须显式选择 round_id。",
        "3. 保持 `.governance/current-state.md` 与 active round 对齐。",
        "4. 使用 `ocw resume` recommended read set 中的 state.yaml / round scope 作为执行边界。",
        "5. 使用 role bindings 作为 owner / reviewer 映射。",
        "6. Step 6 前必须完成 Step 1-5 的真实确认链，不能把 prepare 当成 Step 5 完成。",
        "7. verify、review 或 archive 前先记录客观 evidence。",
        "8. 只有目标、边界、风险、取舍或最终决策需要判断时，才让人介入。",
        "9. 上下文预算优先：先读 recommended read set，不要把归档计划整包加载进会话。",
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


def _write_governance_gitignore(governance_dir: Path) -> None:
    target = governance_dir / ".gitignore"
    required = ["/local/", "/PROJECT_ACTIVATION.yaml", "/current-state.md", "/runtime/status/"]
    existing = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    merged = list(existing)
    for item in required:
        if item not in merged:
            merged.append(item)
    target.write_text("\n".join(merged).rstrip() + "\n", encoding="utf-8")


def _current_state(change_id: str, title: str, goal: str, profile: str, bindings: dict) -> str:
    global_bindings = bindings.get("global", {}) if isinstance(bindings, dict) else {}
    return "\n".join([
        "# open-cowork Current State",
        "",
        f"Project goal: {goal}",
        f"Active change: {change_id}",
        f"Title: {title}",
        f"Profile: {profile}",
        "Current phase: Phase 1 / 定义与对齐",
        f"Current step: Step 1 / {STEP_LABELS[1]}",
        "Current owner: human-sponsor",
        "Next recommended action: discuss and confirm the input sources, problem boundary, risks, and open questions before Step 2.",
        "Need human decision: confirm or revise Step 1 input framing before scope is locked.",
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
        "- `.governance/index/active-changes.yaml`",
        "- `.governance/agent-entry.md`",
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
