from __future__ import annotations

from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml


def require_transition_state(
    root: str | Path,
    change_id: str,
    *,
    expected_step: int,
    allowed_statuses: list[str],
    action_label: str,
) -> dict:
    manifest_path = GovernancePaths(Path(root)).change_file(change_id, "manifest.yaml")
    manifest = load_yaml(manifest_path)
    actual_step = manifest.get("current_step")
    actual_status = manifest.get("status")
    if actual_step != expected_step or actual_status not in allowed_statuses:
        allowed_text = ", ".join(allowed_statuses)
        raise ValueError(
            f"change '{change_id}' must be in step {expected_step} with status in [{allowed_text}] before {action_label}"
        )
    return manifest
