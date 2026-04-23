from __future__ import annotations

from pathlib import Path

from .change_package import update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
from .lifecycle import require_transition_state
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .state_consistency import write_state_consistency_result
from .step_matrix import write_step_matrix_view


def write_verify_result(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    require_transition_state(
        root,
        change_id,
        expected_step=6,
        allowed_statuses=["step6-executed-pre-step7"],
        action_label="verify",
    )
    evidence_summary_path = paths.evidence_dir(change_id) / "execution-summary.yaml"
    if not evidence_summary_path.exists():
        raise ValueError(f"change '{change_id}' has no execution evidence; run step 6 before verify")

    state_consistency_path = write_state_consistency_result(root, change_id)
    step_matrix_path = write_step_matrix_view(root, change_id)
    state_consistency = load_yaml(state_consistency_path)
    summary_status = "pass" if state_consistency.get("status") == "pass" else "blocker"

    verify_path = paths.change_file(change_id, "verify.yaml")
    payload = {
        "schema": "verify-result/v1",
        "change_id": change_id,
        "summary": {
            "status": summary_status,
            "blocker_count": state_consistency.get("summary", {}).get("blocker_count", 0),
        },
        "checks": [
            {
                "name": "state-consistency",
                "status": state_consistency.get("status"),
                "ref": str(Path(state_consistency_path).relative_to(paths.root)),
            },
            {
                "name": "step-matrix-view",
                "status": "pass",
                "ref": str(Path(step_matrix_path).relative_to(paths.root)),
            },
        ],
        "issues": [
            check["detail"]
            for check in state_consistency.get("checks", [])
            if check.get("status") == "blocker"
        ],
    }
    write_yaml(verify_path, payload)

    next_status = "step7-verified" if summary_status == "pass" else "step7-blocked"
    manifest = update_manifest(root, change_id, status=next_status, current_step=7)
    current = read_current_change(root)
    current_change = current.get("current_change") or {}
    if (current.get("current_change_id") or current_change.get("change_id")) == change_id:
        set_current_change(root, {
            **current_change,
            "change_id": change_id,
            "status": next_status,
            "current_step": 7,
        })
    upsert_change_entry(root, {
        "change_id": change_id,
        "path": str(paths.change_dir(change_id).relative_to(paths.root)),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
    })
    set_maintenance_status(
        root,
        status=manifest.get("status"),
        current_change_active=manifest.get("status"),
        current_change_id=change_id,
    )
    return payload
