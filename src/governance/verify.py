from __future__ import annotations

from pathlib import Path
import subprocess

from .change_package import update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .state_consistency import write_state_consistency_result
from .step_matrix import write_step_matrix_view


def write_verify_result(root: str | Path, change_id: str, *, run_commands: bool = False, timeout_seconds: int = 120) -> dict:
    paths = GovernancePaths(Path(root))
    manifest_before = load_yaml(paths.change_file(change_id, "manifest.yaml"))
    allowed_retry = manifest_before.get("current_step") == 7 and manifest_before.get("status") in {"step7-blocked", "step7-verified"}
    allowed_first_verify = manifest_before.get("current_step") == 6 and manifest_before.get("status") == "step6-executed-pre-step7"
    if not (allowed_first_verify or allowed_retry):
        raise ValueError(
            f"change '{change_id}' must be in step 6 with status step6-executed-pre-step7 "
            "or in step 7 with status step7-blocked/step7-verified before verify"
        )
    evidence_summary_path = paths.evidence_dir(change_id) / "execution-summary.yaml"
    if not evidence_summary_path.exists():
        raise ValueError(f"change '{change_id}' has no execution evidence; run step 6 before verify")

    state_consistency_path = write_state_consistency_result(root, change_id)
    step_matrix_path = write_step_matrix_view(root, change_id)
    state_consistency = load_yaml(state_consistency_path)
    summary_status = "pass" if state_consistency.get("status") == "pass" else "blocker"
    contract = load_yaml(paths.change_file(change_id, "contract.yaml"))
    product_verification = _product_verification(
        paths.root,
        commands=(contract.get("verification") or {}).get("commands", []),
        run_commands=run_commands,
        timeout_seconds=timeout_seconds,
    )
    if run_commands and any(item.get("status") != "pass" for item in product_verification["commands"]):
        summary_status = "blocker"

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
        "product_verification": product_verification,
        "issues": [
            check["detail"]
            for check in state_consistency.get("checks", [])
            if check.get("status") == "blocker"
        ] + [
            f"verification command failed: {item.get('command')}"
            for item in product_verification["commands"]
            if item.get("status") == "fail"
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


def _product_verification(root: Path, *, commands: list[str], run_commands: bool, timeout_seconds: int) -> dict:
    if not commands:
        return {"mode": "no-commands", "commands": []}
    if not run_commands:
        return {
            "mode": "state-only",
            "commands": [
                {
                    "command": command,
                    "status": "not-run",
                    "note": "ocw verify checked governance state only; product command evidence must come from Step 6 or rerun verify with --run-commands.",
                }
                for command in commands
            ],
        }
    results = []
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
            results.append({
                "command": command,
                "status": "pass" if completed.returncode == 0 else "fail",
                "exit_code": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            })
        except subprocess.TimeoutExpired as exc:
            results.append({
                "command": command,
                "status": "timeout",
                "timeout_seconds": timeout_seconds,
                "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            })
    return {"mode": "commands-executed", "commands": results}
