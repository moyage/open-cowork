from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def add_runtime_profile(
    root: str | Path,
    *,
    runtime_id: str,
    runtime_type: str,
    owner: str,
    capabilities: list[str],
    risks: list[str],
    evidence: list[str],
    constraints: list[str] | None = None,
) -> dict:
    if not runtime_id.strip():
        raise ValueError("runtime_id is required")
    paths = GovernancePaths(Path(root))
    target_dir = paths.governance_dir / "runtime-profiles"
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "runtime-profile/v1",
        "runtime_id": runtime_id,
        "runtime_type": runtime_type or "unknown",
        "owner": owner or "unassigned",
        "capability_boundaries": capabilities,
        "risk_surface": risks,
        "evidence_support": evidence,
        "governance_constraints": constraints or [
            "必须遵守 active contract",
            "不能绕过 Step 5 / Step 8 / Step 9",
            "不能自审",
        ],
        "authority": "capability_description_only",
        "generated_at": _now_utc(),
    }
    write_yaml(target_dir / f"{runtime_id}.yaml", payload)
    return payload


def list_runtime_profiles(root: str | Path) -> list[dict]:
    paths = GovernancePaths(Path(root))
    target_dir = paths.governance_dir / "runtime-profiles"
    if not target_dir.exists():
        return []
    profiles = []
    for path in sorted(target_dir.glob("*.yaml")):
        payload = load_yaml(path)
        profiles.append({
            "runtime_id": payload.get("runtime_id") or path.stem,
            "runtime_type": payload.get("runtime_type"),
            "owner": payload.get("owner"),
            "path": str(path.relative_to(paths.root)),
        })
    return profiles


def show_runtime_profile(root: str | Path, runtime_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    path = paths.governance_dir / "runtime-profiles" / f"{runtime_id}.yaml"
    if not path.exists():
        raise ValueError(f"runtime profile not found: {runtime_id}")
    return load_yaml(path)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
