from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package, update_manifest
from .contract import load_contract
from .simple_yaml import load_yaml, write_yaml


def capture_intent(
    root: str | Path,
    *,
    change_id: str,
    project_intent: str | None = None,
    requirements: list[str] | None = None,
    optimizations: list[str] | None = None,
    bugs: list[str] | None = None,
    scope_in: list[str] | None = None,
    scope_out: list[str] | None = None,
    acceptance: list[str] | None = None,
    risks: list[str] | None = None,
    open_questions: list[str] | None = None,
    confirmed_by: str | None = None,
    note: str = "",
) -> dict:
    package = read_change_package(root, change_id)
    contract = _load_contract_if_present(package.path)
    payload = {
        "schema": "intent-confirmation/v1",
        "change_id": change_id,
        "status": "confirmed" if confirmed_by else "captured",
        "project_intent": project_intent or contract.get("objective") or package.manifest.get("title") or change_id,
        "requirements": list(requirements or []),
        "optimizations": list(optimizations or []),
        "bugs": list(bugs or []),
        "scope_in": list(scope_in or contract.get("scope_in", [])),
        "scope_out": list(scope_out or contract.get("scope_out", [])),
        "acceptance_criteria": list(acceptance or contract.get("verification", {}).get("checks", [])),
        "risks": list(risks or []),
        "open_questions": list(open_questions or []),
        "human_confirmation": _confirmation(confirmed_by, note) if confirmed_by else None,
        "captured_at": _now_utc(),
    }
    _write_intent_files(package.path, payload)
    _update_manifest(root, change_id, payload)
    _materialize_intent_step_reports(root, change_id)
    return payload


def confirm_intent(root: str | Path, *, change_id: str, confirmed_by: str, note: str = "") -> dict:
    package = read_change_package(root, change_id)
    path = package.path / "intent-confirmation.yaml"
    if path.exists():
        payload = load_yaml(path)
    else:
        payload = capture_intent(root, change_id=change_id)
    payload["status"] = "confirmed"
    payload["human_confirmation"] = _confirmation(confirmed_by, note)
    _write_intent_files(package.path, payload)
    _update_manifest(root, change_id, payload)
    _materialize_intent_step_reports(root, change_id)
    return payload


def _load_contract_if_present(change_dir: Path) -> dict:
    contract_path = change_dir / "contract.yaml"
    if not contract_path.exists():
        return {}
    try:
        return load_contract(contract_path)
    except Exception:
        return load_yaml(contract_path)


def _write_intent_files(change_dir: Path, payload: dict) -> None:
    write_yaml(change_dir / "intent-confirmation.yaml", payload)
    (change_dir / "INTENT_CONFIRMATION.md").write_text(_format_intent(payload), encoding="utf-8")


def _update_manifest(root: str | Path, change_id: str, payload: dict) -> None:
    confirmed = payload.get("status") == "confirmed"
    update_manifest(
        root,
        change_id,
        intent_confirmation={
            "status": payload.get("status"),
            "ref": f".governance/changes/{change_id}/intent-confirmation.yaml",
            "confirmed_by": (payload.get("human_confirmation") or {}).get("confirmed_by"),
        },
        readiness={"step6_entry_ready": confirmed, "missing_items": [] if confirmed else ["intent_confirmation"]},
    )


def _materialize_intent_step_reports(root: str | Path, change_id: str) -> None:
    from .contract import ContractValidationError
    from .step_report import materialize_step_report

    for step in (1, 2):
        try:
            materialize_step_report(root, change_id=change_id, step=step)
        except ContractValidationError:
            continue


def _confirmation(confirmed_by: str, note: str) -> dict:
    return {
        "confirmed_by": confirmed_by,
        "confirmed_at": _now_utc(),
        "note": note,
    }


def _format_intent(payload: dict) -> str:
    lines = [
        f"# Intent Confirmation: {payload['change_id']}",
        "",
        f"- status: {payload['status']}",
        f"- project_intent: {payload['project_intent']}",
        "",
        "## Requirements",
        *_bullets(payload.get("requirements", []), "No explicit requirements captured."),
        "",
        "## Optimizations",
        *_bullets(payload.get("optimizations", []), "No optimization items captured."),
        "",
        "## Bug fixes",
        *_bullets(payload.get("bugs", []), "No bug fixes captured."),
        "",
        "## Scope in",
        *_bullets(payload.get("scope_in", []), "No scope-in entries captured."),
        "",
        "## Scope out",
        *_bullets(payload.get("scope_out", []), "No scope-out entries captured."),
        "",
        "## Acceptance criteria",
        *_bullets(payload.get("acceptance_criteria", []), "No acceptance criteria captured."),
        "",
        "## Risks",
        *_bullets(payload.get("risks", []), "No risks captured."),
        "",
        "## Open questions",
        *_bullets(payload.get("open_questions", []), "No open questions captured."),
    ]
    confirmation = payload.get("human_confirmation") or {}
    if confirmation:
        lines.extend([
            "",
            "## Human confirmation",
            f"- confirmed_by: {confirmation.get('confirmed_by')}",
            f"- confirmed_at: {confirmation.get('confirmed_at')}",
            f"- note: {confirmation.get('note') or 'none'}",
        ])
    return "\n".join(lines) + "\n"


def _bullets(items: list[str], fallback: str) -> list[str]:
    return [f"- {item}" for item in items] if items else [f"- {fallback}"]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
