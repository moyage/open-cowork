from __future__ import annotations

from pathlib import Path

from .simple_yaml import write_yaml


PROJECT_LAYOUT_FILES = (
    "AGENTS.md",
    "agent-entry.md",
    "agent-playbook.md",
    "state.yaml",
    "current-state.md",
    "ledger.yaml",
    "evidence.yaml",
    "rules.yaml",
)

PROJECT_LAYOUT_DIRS = ("templates",)

DEFAULT_READ_SET = (
    "AGENTS.md",
    "agent-entry.md",
    "current-state.md",
    "state.yaml",
)

LEGACY_PROJECT_DIRS = (
    "changes",
    "archive",
    "runtime",
    "index",
    "local",
)


def governance_dir(root: str | Path) -> Path:
    return Path(root) / ".governance"


def default_read_set_paths(root: str | Path) -> list[Path]:
    base = governance_dir(root)
    return [base / name for name in DEFAULT_READ_SET]


def ensure_project_layout(root: str | Path, *, initial_state: dict | None = None) -> None:
    from .project_render import render_current_state
    from .project_state import initial_project_state

    base = governance_dir(root)
    base.mkdir(parents=True, exist_ok=True)
    for dirname in PROJECT_LAYOUT_DIRS:
        (base / dirname).mkdir(parents=True, exist_ok=True)

    _write_text_if_missing(
        base / "AGENTS.md",
        "# open-cowork Agent 入口\n\n本项目使用 open-cowork 管理协作事实。收到开发、接手、审查或验证请求时，先读取 `.governance/agent-entry.md`，再修改项目文件。\n",
    )
    _write_text_if_missing(
        base / "agent-entry.md",
        "# open-cowork Agent Entry\n\nopen-cowork 是项目级协作方式，不是平台 Skill 名称。若当前 Agent 环境提示找不到 `open-cowork` skill，请直接读取本文件和 `.governance/current-state.md`，并在内部运行项目接手入口后继续。\n",
    )
    _write_text_if_missing(
        base / "agent-playbook.md",
        "# open-cowork Agent Playbook\n\n按当前 round 的范围、协作者确认、外部规则确认、执行批准、验证和独立审查推进。\n",
    )
    state_path = base / "state.yaml"
    if initial_state is not None or not state_path.exists():
        state = initial_state or initial_project_state()
        write_yaml(state_path, state)
    else:
        from .simple_yaml import load_yaml

        state = load_yaml(state_path)
    _write_yaml_list_if_missing(base / "ledger.yaml")
    _write_yaml_list_if_missing(base / "evidence.yaml")
    _write_yaml_list_if_missing(base / "rules.yaml")
    (base / "current-state.md").write_text(render_current_state(state), encoding="utf-8")


def _write_text_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _write_yaml_list_if_missing(path: Path) -> None:
    if not path.exists():
        write_yaml(path, [])
