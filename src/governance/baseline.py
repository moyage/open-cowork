from __future__ import annotations

import subprocess
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def materialize_baseline(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    maintenance = load_yaml(paths.maintenance_status_file()) if paths.maintenance_status_file().exists() else {}
    status = _git_status(paths.root)
    payload = {
        "schema": "baseline-separation/v1",
        "change_id": change_id,
        "parent_change_id": maintenance.get("last_archived_change"),
        "parent_archive_at": maintenance.get("last_archive_at"),
        "git_available": status["git_available"],
        "git_status_available": status["git_status_available"],
        "dirty": bool(status["entries"]),
        "git_status_entries": status["entries"],
        "review_guidance": [
            "Treat these entries as pre-existing baseline noise unless Step 6 evidence claims them as current delta.",
            "Reviewers should distinguish parent archived work, unrelated dirty artifacts, and current change outputs.",
        ],
    }
    write_yaml(paths.change_file(change_id, "baseline.yaml"), payload)
    return payload


def _git_status(root: Path) -> dict:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
    except Exception as exc:
        return {"git_available": False, "git_status_available": False, "entries": [f"git status unavailable: {exc}"]}
    if completed.returncode != 0:
        return {"git_available": True, "git_status_available": False, "entries": []}
    return {
        "git_available": True,
        "git_status_available": True,
        "entries": [line for line in completed.stdout.splitlines() if line.strip()],
    }
