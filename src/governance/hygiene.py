from __future__ import annotations

from pathlib import Path


IGNORED_ARTIFACT_PATTERNS = [
    ".governance/index/**",
    ".governance/changes/**",
    ".governance/archive/**",
    ".governance/runtime/**",
]

AGENT_HANDOFF_FILES = [
    ".governance/AGENTS.md",
    ".governance/current-state.md",
    ".governance/agent-playbook.md",
]


def build_hygiene_report(root: str | Path) -> dict:
    root_path = Path(root)
    runtime_generated = _existing(root_path, [
        ".governance/index/current-change.yaml",
        ".governance/index/changes-index.yaml",
        ".governance/index/maintenance-status.yaml",
        ".governance/runtime/status/change-status.yaml",
        ".governance/runtime/status/steps-status.yaml",
        ".governance/runtime/status/participants-status.yaml",
    ])
    agent_handoff_files = _existing(root_path, AGENT_HANDOFF_FILES)
    pending_docs = _pending_docs(root_path)
    cold_archive_docs = _cold_archive_docs(root_path)
    return {
        "schema": "hygiene-report/v1",
        "runtime_generated": runtime_generated,
        "agent_handoff_files": agent_handoff_files,
        "pending_docs": pending_docs,
        "cold_archive_docs": cold_archive_docs,
        "tracked_truth_sources": _existing(root_path, ["README.md", "AGENTS.md", "CHANGELOG.md", "pyproject.toml"]),
        "ignored_artifact_patterns": IGNORED_ARTIFACT_PATTERNS,
        "suggested_commit": [*agent_handoff_files, *pending_docs],
        "suggested_ignore": IGNORED_ARTIFACT_PATTERNS,
        "suggested_cleanup": ["Keep docs/archive/** out of default Agent context; reference specific source docs by path."],
        "recommendations": _recommendations(agent_handoff_files, pending_docs),
    }


def _existing(root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if (root / path).exists()]


def _pending_docs(root: Path) -> list[str]:
    docs_root = root / "docs"
    if not docs_root.exists():
        return []
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in docs_root.rglob("*.md")
        if path.is_file() and "docs/archive/" not in str(path.relative_to(root)).replace("\\", "/")
    )


def _cold_archive_docs(root: Path) -> list[str]:
    archive_root = root / "docs/archive"
    if not archive_root.exists():
        return []
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in archive_root.rglob("*.md")
        if path.is_file()
    )


def _recommendations(agent_handoff_files: list[str], pending_docs: list[str]) -> list[str]:
    recommendations = [
        "Keep runtime generated files ignored unless a specific evidence artifact is intentionally allowed by contract.",
        "Treat docs/archive/** as cold history; do not load it into Agent context by default.",
    ]
    if agent_handoff_files:
        recommendations.append("Commit or deliberately carry .governance/AGENTS.md, current-state.md, and agent-playbook.md as Agent handoff files.")
    if pending_docs:
        recommendations.append("Review pending docs and decide which are source documents for the active change.")
    return recommendations
