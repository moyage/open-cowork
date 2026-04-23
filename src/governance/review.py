from __future__ import annotations

from pathlib import Path

from .change_package import update_manifest
from .index import read_current_change, set_current_change, upsert_change_entry
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def write_review_decision(
    root: str | Path,
    change_id: str,
    *,
    decision: str,
    reviewer: str,
    rationale: str = "",
) -> dict:
    paths = GovernancePaths(Path(root))
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
