from __future__ import annotations

from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml

RETROSPECTIVE_SCHEMA = "governance/post-round-retrospective-and-iteration-synthesis/v1"


def build_post_round_retrospective(root: str | Path, change_id: str | None = None, archived_change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    maintenance_status = load_yaml(paths.maintenance_status_file())
    current_change = load_yaml(paths.current_change_file())
    target_change_id = change_id or maintenance_status.get("current_change_id") or current_change.get("current_change_id")
    if not target_change_id:
        raise ValueError("no change_id provided and no current change set")
    source_change_id = archived_change_id or maintenance_status.get("last_archived_change")
    if not source_change_id:
        raise ValueError("no archived change available for retrospective synthesis")

    archive_receipt_path = paths.archived_change_file(str(source_change_id), "archive-receipt.yaml")
    archived_manifest_path = paths.archived_change_file(str(source_change_id), "manifest.yaml")
    archived_review_path = paths.archived_change_file(str(source_change_id), "review.yaml")
    target_manifest_path = paths.change_file(str(target_change_id), "manifest.yaml")
    target_contract_path = paths.change_file(str(target_change_id), "contract.yaml")

    archive_receipt = load_yaml(archive_receipt_path)
    archived_manifest = load_yaml(archived_manifest_path)
    archived_review = load_yaml(archived_review_path)
    target_manifest = load_yaml(target_manifest_path)
    target_contract = load_yaml(target_contract_path)

    residuals = _collect_residuals(archive_receipt, archived_review, maintenance_status)
    return {
        "schema": RETROSPECTIVE_SCHEMA,
        "generated_for_change_id": str(target_change_id),
        "source_archived_change_id": str(source_change_id),
        "source_archive": {
            "archive_receipt": str(archive_receipt_path.relative_to(paths.root)),
            "archived_manifest": str(archived_manifest_path.relative_to(paths.root)),
            "archived_review": str(archived_review_path.relative_to(paths.root)),
            "archive_executed": archive_receipt.get("archive_executed"),
            "archived_at": archive_receipt.get("archived_at"),
            "review_decision": archived_review.get("decision", {}).get("status"),
        },
        "round_summary": {
            "title": archived_manifest.get("title"),
            "status": archived_manifest.get("status"),
            "step9_status": archived_manifest.get("lifecycle", {}).get("step9", {}).get("status"),
            "receipt_traceability": archive_receipt.get("traceability", {}),
        },
        "residual_carry_forward": residuals,
        "next_round_prep_pointers": [
            str(target_manifest_path.relative_to(paths.root)),
            str(target_contract_path.relative_to(paths.root)),
            ".governance/index/maintenance-status.yaml",
        ],
        "iteration_synthesis": {
            "candidate_requirements": list(target_manifest.get("target_validation_objects", [])),
            "candidate_optimizations": [
                "Keep runtime additions additive and bounded to existing governance file shapes.",
                "Preserve explicit machine-readable outputs for dispatch, execution, and archive-adjacent synthesis.",
            ],
            "candidate_defects": [item["summary"] for item in residuals],
            "recommended_bounded_scope": list(target_contract.get("scope_in", [])),
            "deferred_or_non_goal_items": list(target_contract.get("scope_out", [])),
        },
    }


def format_post_round_retrospective(payload: dict) -> str:
    lines = [
        f"# Post-Round Retrospective: {payload['source_archived_change_id']}",
        "",
        f"- Generated for change: {payload['generated_for_change_id']}",
        f"- Archive executed: {payload['source_archive']['archive_executed']}",
        f"- Review decision: {payload['source_archive']['review_decision']}",
        f"- Archived at: {payload['source_archive']['archived_at']}",
        "",
        "## Residual carry-forward",
    ]
    if payload["residual_carry_forward"]:
        for item in payload["residual_carry_forward"]:
            lines.append(f"- {item['summary']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Iteration synthesis"])
    for key in [
        "candidate_requirements",
        "candidate_optimizations",
        "candidate_defects",
        "recommended_bounded_scope",
        "deferred_or_non_goal_items",
    ]:
        lines.append(f"### {key.replace('_', ' ').title()}")
        for item in payload["iteration_synthesis"][key]:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def materialize_post_round_retrospective(root: str | Path, change_id: str | None = None, archived_change_id: str | None = None) -> dict:
    payload = build_post_round_retrospective(root, change_id, archived_change_id)
    paths = GovernancePaths(Path(root))
    yaml_path = paths.change_file(payload["generated_for_change_id"], "POST_ROUND_RETROSPECTIVE_AND_ITERATION_SYNTHESIS.yaml")
    markdown_path = paths.change_file(payload["generated_for_change_id"], "POST_ROUND_RETROSPECTIVE_AND_ITERATION_SYNTHESIS.md")
    write_yaml(yaml_path, payload)
    markdown_path.write_text(format_post_round_retrospective(payload), encoding="utf-8")
    return {"yaml": str(yaml_path), "markdown": str(markdown_path)}


def _collect_residuals(archive_receipt: dict, archived_review: dict, maintenance_status: dict) -> list[dict]:
    residuals = []
    for item in archive_receipt.get("residual_followups", []):
        residuals.append({
            "source": "archive-receipt",
            "id": item.get("id"),
            "summary": item.get("note"),
        })
    for item in archived_review.get("conditions", {}).get("followups", []):
        residuals.append({
            "source": "review-followup",
            "id": item,
            "summary": item,
        })
    for item in maintenance_status.get("residual_followups", []):
        residuals.append({
            "source": "maintenance-status",
            "id": item.get("id"),
            "summary": item.get("note"),
        })
    deduped = []
    seen = set()
    for item in residuals:
        key = (item.get("source"), item.get("id"), item.get("summary"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
