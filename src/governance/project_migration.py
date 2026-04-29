from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .project_paths import LEGACY_PROJECT_DIRS, ensure_project_layout, governance_dir
from .project_state import PROTOCOL_VERSION, initial_project_state, validate_project_documents
from .simple_yaml import load_yaml, write_yaml


def detect_legacy_layout(root: str | Path) -> dict:
    root_path = Path(root)
    base = governance_dir(root_path)
    legacy_dirs = {}
    removal_candidates = []
    for dirname in LEGACY_PROJECT_DIRS:
        path = base / dirname
        exists = path.exists()
        legacy_dirs[dirname] = {
            "path": f".governance/{dirname}",
            "exists": exists,
            "entry_count": _entry_count(path) if exists else 0,
        }
        if exists:
            removal_candidates.append(f".governance/{dirname}")

    return {
        "layout": "legacy-governance" if removal_candidates else "current-state-or-empty",
        "protocol_version": _project_protocol_version(base),
        "legacy_dirs": legacy_dirs,
        "active_legacy_change": _active_legacy_change(base),
        "unmigrated_archives": _unmigrated_archives(base),
        "tracked_legacy_runtime_artifacts": _tracked_legacy_runtime_artifacts(root_path),
        "removal_candidates": removal_candidates,
    }


def install_or_upgrade_project(root: str | Path) -> dict:
    """Initialize current-state governance, automatically migrating older layouts when present."""
    root_path = Path(root)
    base = governance_dir(root_path)
    report = detect_legacy_layout(root_path)
    actions: list[str] = []
    receipt = None

    if report["removal_candidates"]:
        migrated = migrate_legacy_to_current_state(root_path, dry_run=False, confirm=True)
        actions.append("migrated-legacy-governance-layout")
        receipt = migrated.get("receipt")
    else:
        ensure_project_layout(root_path)
        actions.append("ensured-current-state-layout")

    upgraded_protocol = _upgrade_existing_project_state(base)
    if upgraded_protocol:
        actions.append("upgraded-current-state-protocol-version")
        ensure_project_layout(root_path)

    verification = verify_migration(root_path)
    return {
        "layout_before": report["layout"],
        "protocol_before": report["protocol_version"],
        "actions": actions,
        "receipt": receipt,
        "verification": verification,
    }


def migrate_legacy_to_current_state(root: str | Path, *, dry_run: bool, confirm: bool) -> dict:
    root_path = Path(root)
    base = governance_dir(root_path)
    report = detect_legacy_layout(root_path)
    move_plan = [
        {"from": f".governance/{dirname}", "to": f".governance/cold/legacy/{dirname}"}
        for dirname, meta in report["legacy_dirs"].items()
        if meta["exists"]
    ]
    result = {
        "dry_run": dry_run,
        "confirmed": confirm,
        "active_legacy_change": report["active_legacy_change"],
        "move_plan": move_plan,
        "receipt": None,
        "blocked": False,
    }
    if dry_run:
        return result
    if not confirm:
        result["blocked"] = True
        result["reason"] = "confirm_required"
        return result

    state = initial_project_state(
        round_id=_round_id_from_legacy(report["active_legacy_change"]),
        goal=_legacy_goal(base, report["active_legacy_change"]),
    )
    ensure_project_layout(root_path, initial_state=state)
    cold = base / "cold" / "legacy"
    cold.mkdir(parents=True, exist_ok=True)
    moved = []
    for item in move_plan:
        source = root_path / item["from"]
        target = root_path / item["to"]
        if not source.exists():
            continue
        if target.exists():
            target = _unique_path(target)
            item["to"] = str(target.relative_to(root_path))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        moved.append(item)

    gitignore_updates = _ensure_gitignore(root_path)
    receipt = {
        "receipt_type": "migration",
        "protocol_version": "0.3.11",
        "created_at": _now_utc(),
        "active_legacy_change": report["active_legacy_change"],
        "unmigrated_archives": report["unmigrated_archives"],
        "tracked_legacy_runtime_artifacts": report["tracked_legacy_runtime_artifacts"],
        "moved": moved,
        "gitignore_updates": gitignore_updates,
        "summary": "旧版 governance 目录已移入 cold/legacy，当前状态已转换为 v0.3.11 state。",
    }
    receipt_path = cold / "migration-receipt.yaml"
    write_yaml(receipt_path, receipt)
    result["receipt"] = str(receipt_path.relative_to(root_path))
    result["moved"] = moved
    return result


def verify_migration(root: str | Path) -> dict:
    root_path = Path(root)
    base = governance_dir(root_path)
    errors = []
    if not (base / "state.yaml").exists():
        errors.append(".governance/state.yaml missing")
    else:
        errors.extend(validate_project_documents(root_path))
    receipt_path = base / "cold/legacy/migration-receipt.yaml"
    live_legacy_dirs = [dirname for dirname in LEGACY_PROJECT_DIRS if (base / dirname).exists()]
    if not receipt_path.exists() and not live_legacy_dirs:
        return {"ok": not errors, "errors": errors}
    if not receipt_path.exists():
        errors.append("migration receipt missing")
    else:
        try:
            receipt = load_yaml(receipt_path)
        except Exception as exc:
            receipt = {}
            errors.append(f"migration receipt unreadable: {exc}")
        for dirname in live_legacy_dirs:
            errors.append(f"live legacy directory still exists: .governance/{dirname}")
        for index, item in enumerate(receipt.get("moved") or []):
            source = item.get("from")
            target = item.get("to")
            if not source or not target:
                errors.append(f"migration receipt moved item {index} is incomplete")
                continue
            if (root_path / source).exists():
                errors.append(f"migration receipt source still exists: {source}")
            if not (root_path / target).exists():
                errors.append(f"migration receipt target missing: {target}")
    return {"ok": not errors, "errors": errors}


def prune_legacy(root: str | Path, *, dry_run: bool, confirm: bool) -> dict:
    root_path = Path(root)
    base = governance_dir(root_path)
    cold = base / "cold" / "legacy"
    candidates = []
    for dirname in LEGACY_PROJECT_DIRS:
        live = base / dirname
        archived = cold / dirname
        if live.exists():
            candidates.append(str(live.relative_to(root_path)))
        if archived.exists():
            candidates.append(str(archived.relative_to(root_path)))
    result = {"dry_run": dry_run, "confirmed": confirm, "candidates": candidates, "receipt": None, "blocked": False}
    if dry_run:
        return result
    if not confirm:
        result["blocked"] = True
        result["reason"] = "confirm_required"
        return result
    cold.mkdir(parents=True, exist_ok=True)
    receipt_path = cold / "prune-receipt.yaml"
    write_yaml(receipt_path, {
        "receipt_type": "prune",
        "created_at": _now_utc(),
        "candidates": candidates,
        "removed": [],
        "retained": candidates,
        "summary": "prune已确认；为避免默认破坏审计历史，本实现保留 cold legacy 文件并写入prune receipt。",
    })
    result["receipt"] = str(receipt_path.relative_to(root_path))
    return result


def uninstall_governance(root: str | Path, *, dry_run: bool, confirm: bool) -> dict:
    root_path = Path(root)
    base = governance_dir(root_path)
    targets = [".governance"] if base.exists() else []
    result = {"dry_run": dry_run, "confirmed": confirm, "targets": targets, "removed": False, "blocked": False}
    if dry_run:
        return result
    if not confirm:
        result["blocked"] = True
        result["reason"] = "confirm_required"
        return result
    detect_report = detect_legacy_layout(root_path)
    receipt_path = root_path / ".open-cowork-uninstall-receipt.yaml"
    write_yaml(receipt_path, {
        "receipt_type": "uninstall",
        "created_at": _now_utc(),
        "removed": targets,
        "pre_uninstall_detect_report": detect_report,
        "summary": "已按显式确认移除 open-cowork governance 文件。",
    })
    if base.exists():
        shutil.rmtree(base)
    result["removed"] = True
    result["receipt"] = str(receipt_path.relative_to(root_path))
    return result


def _project_protocol_version(base: Path) -> str:
    state_path = base / "state.yaml"
    if not state_path.exists():
        return ""
    try:
        payload = load_yaml(state_path)
    except Exception:
        return "unreadable"
    return str((payload.get("protocol") or {}).get("version") or "")


def _active_legacy_change(base: Path) -> str:
    current_path = base / "index" / "current-change.yaml"
    if not current_path.exists():
        return ""
    try:
        payload = load_yaml(current_path)
    except Exception:
        return ""
    nested = payload.get("current_change")
    if isinstance(nested, dict) and nested.get("change_id"):
        return str(nested.get("change_id"))
    return str(payload.get("current_change_id") or "")


def _legacy_goal(base: Path, change_id: str) -> str:
    if not change_id:
        return "迁移旧版 open-cowork 治理状态"
    manifest_path = base / "changes" / change_id / "manifest.yaml"
    if not manifest_path.exists():
        return f"迁移旧版任务 {change_id}"
    try:
        manifest = load_yaml(manifest_path)
    except Exception:
        return f"迁移旧版任务 {change_id}"
    return str(manifest.get("title") or manifest.get("goal") or f"迁移旧版任务 {change_id}")


def _unmigrated_archives(base: Path) -> list[str]:
    archive = base / "archive"
    if not archive.exists():
        return []
    return sorted(path.name for path in archive.iterdir() if path.is_dir())


def _tracked_legacy_runtime_artifacts(root: Path) -> list[str]:
    paths = [f".governance/{dirname}" for dirname in LEGACY_PROJECT_DIRS]
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", *paths],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return sorted(line for line in completed.stdout.splitlines() if line.strip())


def _round_id_from_legacy(change_id: str) -> str:
    if not change_id:
        return "R-MIGRATED-001"
    normalized = "".join(ch if ch.isalnum() else "-" for ch in change_id.upper()).strip("-")
    return f"R-MIGRATED-{normalized}"


def _entry_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("*"))


def _ensure_gitignore(root: Path) -> list[str]:
    path = root / ".gitignore"
    lines = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    additions = [".governance/runtime/", ".governance/local/"]
    applied = []
    changed = False
    for item in additions:
        if item not in lines:
            lines.append(item)
            applied.append(item)
            changed = True
    if changed:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return [f".gitignore:{item}" for item in applied]


def _upgrade_existing_project_state(base: Path) -> bool:
    state_path = base / "state.yaml"
    if not state_path.exists():
        return False
    try:
        payload = load_yaml(state_path)
    except Exception:
        return False
    protocol = payload.setdefault("protocol", {})
    if protocol.get("version") == PROTOCOL_VERSION:
        return False
    protocol["name"] = protocol.get("name") or "open-cowork"
    protocol["version"] = PROTOCOL_VERSION
    payload.setdefault("layout", "current-state")
    write_yaml(state_path, payload)
    return True


def _unique_path(path: Path) -> Path:
    index = 2
    while True:
        candidate = path.with_name(f"{path.name}-{index}")
        if not candidate.exists():
            return candidate
        index += 1


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
