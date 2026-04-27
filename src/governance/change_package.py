from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml

CORE_CHANGE_FILES = (
    "intent.md",
    "requirements.md",
    "design.md",
    "tasks.md",
    "contract.yaml",
    "bindings.yaml",
    "verify.yaml",
    "review.yaml",
    "manifest.yaml",
)


@dataclass(frozen=True)
class ChangePackage:
    change_id: str
    path: Path
    manifest: dict


def create_change_package(root: str | Path, change_id: str, title: str = "", policy_level: str = "standard") -> ChangePackage:
    paths = GovernancePaths(Path(root))
    change_dir = paths.change_dir(change_id)
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
    for name in CORE_CHANGE_FILES:
        file_path = change_dir / name
        if file_path.exists():
            continue
        if name.endswith(".md"):
            file_path.write_text("", encoding="utf-8")
        elif name == "manifest.yaml":
            write_yaml(file_path, _default_manifest(change_id, title, policy_level))
        else:
            write_yaml(file_path, {})
    return read_change_package(root, change_id)


def read_change_package(root: str | Path, change_id: str | None = None) -> ChangePackage:
    paths = GovernancePaths(Path(root))
    resolved_change_id = change_id or _extract_current_change_id(read_current_change(root))
    if not resolved_change_id:
        raise ValueError("no change_id provided and no current change set")
    change_dir = paths.change_dir(str(resolved_change_id))
    manifest_path = change_dir / "manifest.yaml"
    return ChangePackage(change_id=str(resolved_change_id), path=change_dir, manifest=load_yaml(manifest_path))


def update_manifest(root: str | Path, change_id: str, **updates) -> dict:
    package = read_change_package(root, change_id)
    manifest = {**package.manifest, **updates}
    write_yaml(package.path / "manifest.yaml", manifest)
    return manifest


def _default_manifest(change_id: str, title: str, policy_level: str) -> dict:
    return {
        "change_id": change_id,
        "title": title,
        "policy_level": policy_level,
        "status": "drafting",
        "current_step": 1,
        "owner": "orchestrator",
        "files": {"required": list(CORE_CHANGE_FILES), "directories": ["evidence/"]},
        "readiness": {"step6_entry_ready": False, "missing_items": []},
    }


def _extract_current_change_id(payload: dict) -> str | None:
    nested = payload.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    return payload.get("current_change_id") or nested.get("change_id") or nested.get("current_change_id")
