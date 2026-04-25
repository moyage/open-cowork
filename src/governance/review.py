from __future__ import annotations

from pathlib import Path

from .change_package import update_manifest
from .index import read_current_change, set_current_change, upsert_change_entry
from .lifecycle import require_transition_state
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def write_review_decision(
    root: str | Path,
    change_id: str,
    *,
    decision: str,
    reviewer: str,
    rationale: str = "",
    allow_reviewer_mismatch: bool = False,
) -> dict:
    paths = GovernancePaths(Path(root))
    require_transition_state(
        root,
        change_id,
        expected_step=7,
        allowed_statuses=["step7-verified"],
        action_label="review",
    )
    verify_path = paths.change_file(change_id, "verify.yaml")
    verify_payload = load_yaml(verify_path) if verify_path.exists() else {}
    if verify_payload.get("summary", {}).get("status") != "pass":
        raise ValueError(f"change '{change_id}' must have a passing verify result before review")
    warnings = _reviewer_warnings(paths, change_id, reviewer)
    if warnings and not allow_reviewer_mismatch:
        raise ValueError(warnings[0])
    from .human_gates import require_step_approval

    require_step_approval(root, change_id=change_id, step=8)
    if warnings:
        from .human_gates import record_bypass

        record_bypass(
            root,
            change_id=change_id,
            step=8,
            reason="reviewer_mismatch",
            recorded_by=reviewer,
            note=warnings[0],
        )

    review_path = paths.change_file(change_id, "review.yaml")
    existing = load_yaml(review_path) if review_path.exists() else {}
    payload = {
        **existing,
        "schema": existing.get("schema", "review-decision/v1"),
        "change_id": change_id,
        "reviewers": [{"role": "reviewer", "id": reviewer}],
        "decision": {"status": decision, "rationale": rationale},
        "conditions": existing.get("conditions", {"must_before_next_step": [], "followups": []}),
        "trace": existing.get("trace", {"evidence_refs": [], "verify_refs": ["verify.yaml"]}),
    }
    if warnings:
        payload["warnings"] = warnings
    write_yaml(review_path, payload)

    next_status = _status_for_decision(decision)
    manifest = update_manifest(root, change_id, status=next_status, current_step=8)
    current = read_current_change(root)
    current_change = current.get("current_change") or {}
    if (current.get("current_change_id") or current_change.get("change_id")) == change_id:
        set_current_change(root, {
            **current_change,
            "change_id": change_id,
            "status": next_status,
            "current_step": 8,
        })
    upsert_change_entry(root, {
        "change_id": change_id,
        "path": str(paths.change_dir(change_id).relative_to(paths.root)),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
    })
    return payload


def _status_for_decision(decision: str) -> str:
    if decision == "approve":
        return "review-approved"
    if decision == "reject":
        return "review-rejected"
    return "review-revise"


def _reviewer_warnings(paths: GovernancePaths, change_id: str, reviewer: str) -> list[str]:
    bindings_path = paths.change_file(change_id, "bindings.yaml")
    if not bindings_path.exists():
        return []
    bindings = load_yaml(bindings_path)
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    step8 = steps.get(8) or steps.get("8") or steps.get("'8'") or {}
    expected = step8.get("reviewer") or step8.get("owner")
    if expected and expected != reviewer:
        return [f"reviewer does not match Step 8 binding: expected {expected}, got {reviewer}"]
    return []
