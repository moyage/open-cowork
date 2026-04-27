from __future__ import annotations

from pathlib import Path

from .change_package import update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
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
    bypass_reason: str = "",
    bypass_recorded_by: str = "",
    bypass_evidence_ref: str = "",
    runtime: str = "",
    health_check: str = "",
    invocation_status: str = "",
    failure_reason: str = "",
    fallback_reviewer: str = "",
    review_artifact_ref: str = "",
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
    if warnings and allow_reviewer_mismatch:
        missing = []
        if not bypass_reason.strip():
            missing.append("bypass reason")
        if not bypass_recorded_by.strip():
            missing.append("bypass recorded_by")
        if not bypass_evidence_ref.strip():
            missing.append("bypass evidence_ref")
        if missing:
            raise ValueError(
                "reviewer mismatch bypass requires " + ", ".join(missing)
            )
    if warnings:
        from .human_gates import record_bypass

        record_bypass(
            root,
            change_id=change_id,
            step=8,
            reason=bypass_reason,
            recorded_by=bypass_recorded_by,
            evidence_ref=bypass_evidence_ref,
            note=warnings[0],
        )

    review_path = paths.change_file(change_id, "review.yaml")
    existing = load_yaml(review_path) if review_path.exists() else {}
    payload = {
        "schema": existing.get("schema", "review-decision/v1"),
        "change_id": change_id,
        "reviewers": [{"role": "reviewer", "id": reviewer}],
        "decision": {"status": decision, "rationale": rationale},
        "conditions": existing.get("conditions", {"must_before_next_step": [], "followups": []}),
        "trace": {
            **existing.get("trace", {"evidence_refs": [], "verify_refs": ["verify.yaml"]}),
            "step8_human_acceptance_required": True,
            "step8_approval_ref": f".governance/changes/{change_id}/human-gates.yaml#approvals.8",
            "step8_acceptance_ref": f".governance/changes/{change_id}/human-gates.yaml#approvals.8",
        },
    }
    runtime_evidence = {
        key: value
        for key, value in {
            "runtime": runtime,
            "health_check": health_check,
            "invocation_status": invocation_status,
            "failure_reason": failure_reason,
            "fallback_reviewer": fallback_reviewer,
            "review_artifact_ref": review_artifact_ref,
        }.items()
        if value
    }
    if runtime_evidence:
        payload["runtime_evidence"] = runtime_evidence
    if warnings:
        payload["warnings"] = warnings
        payload["reviewer_mismatch_bypass"] = {
            "reason": bypass_reason,
            "recorded_by": bypass_recorded_by,
            "evidence_ref": bypass_evidence_ref,
        }
    write_yaml(review_path, payload)
    _append_review_lifecycle(
        paths,
        change_id,
        decision=decision,
        reviewer=reviewer,
        rationale=rationale,
        runtime_evidence=runtime_evidence,
        review_artifact_ref=review_artifact_ref,
    )

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
    set_maintenance_status(root, status=manifest.get("status"), current_change_active=manifest.get("status"), current_change_id=change_id)
    return payload


def _append_review_lifecycle(
    paths: GovernancePaths,
    change_id: str,
    *,
    decision: str,
    reviewer: str,
    rationale: str,
    runtime_evidence: dict,
    review_artifact_ref: str,
) -> dict:
    path = paths.change_file(change_id, "review-lifecycle.yaml")
    payload = load_yaml(path) if path.exists() else {
        "schema": "review-lifecycle/v1",
        "change_id": change_id,
        "status": "not-started",
        "rounds": [],
        "rework_rounds": [],
    }
    rounds = payload.setdefault("rounds", [])
    lifecycle_decision = "request_changes" if decision == "revise" else decision
    round_payload = {
        "round": len(rounds) + 1,
        "reviewer": reviewer,
        "decision": lifecycle_decision,
        "rationale": rationale,
        "blocking_findings": _blocking_findings(rationale) if decision == "revise" else [],
        "fix_evidence_required": _fix_evidence_required(rationale) if decision == "revise" else [],
        "runtime_evidence": runtime_evidence,
    }
    if review_artifact_ref:
        round_payload["review_artifact_ref"] = review_artifact_ref
    rounds.append(round_payload)
    payload["status"] = "changes-requested" if decision == "revise" else f"review-{decision}"
    write_yaml(path, payload)
    return payload


def _blocking_findings(rationale: str) -> list[dict]:
    text = (rationale or "").strip()
    if not text:
        return []
    body = text
    lowered = text.lower()
    for prefix in ("blocking:", "request_changes:", "revise:"):
        if lowered.startswith(prefix):
            body = text[len(prefix):].strip()
            break
    return [{"id": "finding-1", "severity": "blocking", "body": body}]


def _fix_evidence_required(rationale: str) -> list[dict]:
    findings = _blocking_findings(rationale)
    if not findings:
        return []
    return [{"id": "fix-evidence-1", "finding_id": findings[0]["id"], "label": "Evidence that the requested review change was addressed."}]


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
