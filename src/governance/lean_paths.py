from __future__ import annotations

from pathlib import Path

from .simple_yaml import write_yaml


LEAN_LAYOUT_FILES = (
    "AGENTS.md",
    "agent-entry.md",
    "agent-playbook.md",
    "state.yaml",
    "current-state.md",
    "ledger.yaml",
    "evidence.yaml",
    "rules.yaml",
)

LEAN_LAYOUT_DIRS = ("templates",)

DEFAULT_READ_SET = (
    "AGENTS.md",
    "agent-entry.md",
    "current-state.md",
    "state.yaml",
)

LEGACY_HEAVY_DIRS = (
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


def ensure_lean_layout(root: str | Path, *, initial_state: dict | None = None) -> None:
    from .lean_render import render_current_state
    from .lean_state import initial_lean_state

    base = governance_dir(root)
    base.mkdir(parents=True, exist_ok=True)
    for dirname in LEAN_LAYOUT_DIRS:
        (base / dirname).mkdir(parents=True, exist_ok=True)

    _write_text_if_missing(base / "AGENTS.md", "# open-cowork Agent 入口\n\n本项目使用 open-cowork v0.3.11 lean protocol。\n")
    _write_text_if_missing(base / "agent-entry.md", "# Agent Entry\n\n读取默认读取集后再继续。\n")
    _write_text_if_missing(base / "agent-playbook.md", "# Agent Playbook\n\n按当前 round 的 gate 推进。\n")
    state_path = base / "state.yaml"
    if initial_state is not None or not state_path.exists():
        state = initial_state or initial_lean_state()
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
