from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import STEP_LABELS


def create_context_pack(root: str | Path, change_id: str, *, level: str = "standard") -> dict:
    paths = GovernancePaths(Path(root))
    change_dir = paths.change_dir(change_id)
    context_dir = change_dir / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_if_exists(change_dir / "manifest.yaml")
    snapshot = _snapshot(paths, change_id, manifest)
    authoritative_reads = _existing([
        change_dir / "manifest.yaml",
        change_dir / "intent-confirmation.yaml",
        change_dir / "contract.yaml",
        change_dir / "bindings.yaml",
        change_dir / "verify.yaml",
        change_dir / "review.yaml",
    ], paths.root)
    source_index = write_source_index(root, change_id)
    compression_checkpoint = write_compression_checkpoint(root, change_id)
    supporting_reads = _existing([
        change_dir / "step-reports" / f"step-{snapshot['current_step']}.md",
        change_dir / "step-reports" / f"step-{snapshot['current_step']}.yaml",
        change_dir / "evidence" / "index.yaml",
        Path(source_index) if source_index else change_dir / "context" / "source-index.yaml",
        Path(compression_checkpoint) if compression_checkpoint else change_dir / "context" / "compression-checkpoint.md",
    ], paths.root)
    optional_deep_reads = _optional_deep_reads(manifest)
    if level == "minimal":
        supporting_reads = []
        optional_deep_reads = []
    elif level == "standard":
        optional_deep_reads = []
    pack = {
        "context_pack_version": "ocw.context-pack.v1",
        "change_id": change_id,
        "created_at": _now_utc(),
        "pack_level": level,
        "purpose": "resume",
        "authoritative_reads": authoritative_reads,
        "supporting_reads": supporting_reads,
        "optional_deep_reads": optional_deep_reads,
        "summary": snapshot,
        "compression_notes": {
            "context_pack_is_authoritative": False,
            "context_pack_points_to_authoritative_facts": True,
            "do_not_read_full_archive_by_default": True,
            "batch_large_references": True,
        },
    }
    write_yaml(context_dir / "context-pack.yaml", pack)
    (context_dir / "context-pack.md").write_text(_format_context_pack(pack), encoding="utf-8")
    return {
        "change_id": change_id,
        "context_pack": f".governance/changes/{change_id}/context/context-pack.yaml",
        "context_pack_md": f".governance/changes/{change_id}/context/context-pack.md",
        "pack": pack,
    }


def read_context_pack(root: str | Path, change_id: str, *, level: str = "standard") -> dict:
    paths = GovernancePaths(Path(root))
    path = paths.change_dir(change_id) / "context" / "context-pack.yaml"
    if not path.exists():
        return create_context_pack(root, change_id, level=level)["pack"]
    pack = load_yaml(path)
    if pack.get("pack_level") != level:
        return create_context_pack(root, change_id, level=level)["pack"]
    return pack


def write_compact_handoff(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    pack_info = create_context_pack(root, change_id)
    pack = pack_info["pack"]
    context_dir = paths.change_dir(change_id) / "context"
    handoff_path = context_dir / "handoff-compact.md"
    handoff_path.write_text(_format_handoff(pack), encoding="utf-8")
    _enforce_handoff_length(handoff_path, max_lines=120)
    return {
        "change_id": change_id,
        "handoff": f".governance/changes/{change_id}/context/handoff-compact.md",
        "context_pack": pack_info["context_pack"],
    }


def context_read_set(root: str | Path, change_id: str) -> list[str]:
    paths = GovernancePaths(Path(root))
    context_dir = paths.change_dir(change_id) / "context"
    read_set = []
    for name in ("context-pack.yaml", "handoff-compact.md", "context-pack.md"):
        path = context_dir / name
        if path.exists():
            read_set.append(str(path.relative_to(paths.root)))
    return read_set


def _snapshot(paths: GovernancePaths, change_id: str, manifest: dict) -> dict:
    current_step = manifest.get("current_step") or 1
    verify = _load_if_exists(paths.change_dir(change_id) / "verify.yaml")
    return {
        "current_step": current_step,
        "current_step_name": STEP_LABELS.get(current_step, str(current_step)),
        "status": manifest.get("status") or "unknown",
        "owner": manifest.get("owner") or "unassigned",
        "blocked": _is_blocked(manifest, verify),
        "next_decision": f"Step {current_step} / {STEP_LABELS.get(current_step, current_step)}",
    }


def _is_blocked(manifest: dict, verify: dict) -> bool:
    status = str(manifest.get("status") or "")
    if "blocked" in status:
        return True
    if manifest.get("readiness", {}).get("missing_items"):
        return True
    return int(verify.get("summary", {}).get("blocker_count") or 0) > 0


def _optional_deep_reads(manifest: dict) -> list[str]:
    return [str(item) for item in manifest.get("source_docs", [])]


def _existing(paths: list[Path], root: Path) -> list[str]:
    return [str(path.relative_to(root)) for path in paths if path.exists()]


def _load_if_exists(path: Path) -> dict:
    return load_yaml(path) if path.exists() else {}


def _format_context_pack(pack: dict) -> str:
    lines = [
        f"# 接手资料索引: {pack['change_id']}",
        "",
        "Context pack points to authoritative facts; it does not replace them.",
        "",
        "## Authoritative Reads",
        *[f"- {item}" for item in pack.get("authoritative_reads", [])],
        "",
        "## Supporting Reads",
        *[f"- {item}" for item in pack.get("supporting_reads", [])],
        "",
        "## Optional Deep Reads",
        *[f"- {item}" for item in pack.get("optional_deep_reads", [])],
    ]
    return "\n".join(lines) + "\n"


def _format_handoff(pack: dict) -> str:
    summary = pack.get("summary", {})
    reads = [
        f".governance/changes/{pack['change_id']}/context/context-pack.yaml",
        f".governance/changes/{pack['change_id']}/context/handoff-compact.md",
        *pack.get("authoritative_reads", []),
        *pack.get("supporting_reads", []),
    ]
    lines = [
        f"# 接手摘要: {pack['change_id']}",
        "",
        "Context pack points to authoritative facts; it does not replace them.",
        "",
        "## Status",
        f"- current_step: {summary.get('current_step')}",
        f"- current_step_name: {summary.get('current_step_name')}",
        f"- status: {summary.get('status')}",
        f"- owner: {summary.get('owner')}",
        f"- blocked: {summary.get('blocked')}",
        f"- next_decision: {summary.get('next_decision')}",
        "",
        "## Recommended Read Set",
        *[f"- {item}" for item in reads],
        "",
        "## Length Guard",
        "- max_lines: 120",
        "- do_not_copy_full_history: true",
    ]
    return "\n".join(lines) + "\n"


def write_source_index(root: str | Path, change_id: str) -> str:
    paths = GovernancePaths(Path(root))
    change_dir = paths.change_dir(change_id)
    context_dir = change_dir / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_if_exists(change_dir / "manifest.yaml")
    source_docs = [str(item) for item in manifest.get("source_docs", [])]
    entries = []
    for idx, source in enumerate(source_docs, start=1):
        entries.append({
            "source_ref": source,
            "batch": idx,
            "read_status": "pending-deep-read",
            "summary_ref": f".governance/changes/{change_id}/context/source-summaries/batch-{idx}.md",
            "deep_read_required": True,
        })
    target = context_dir / "source-index.yaml"
    write_yaml(target, {
        "schema": "source-index/v1",
        "change_id": change_id,
        "sources": entries,
    })
    summaries = context_dir / "source-summaries"
    summaries.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        summary_path = paths.root / entry["summary_ref"]
        if not summary_path.exists():
            summary_path.write_text(
                f"# Batch {entry['batch']} source summary\n\n- source: {entry['source_ref']}\n- status: pending-deep-read\n",
                encoding="utf-8",
            )
    return str(target)


def write_compression_checkpoint(root: str | Path, change_id: str) -> str:
    paths = GovernancePaths(Path(root))
    context_dir = paths.change_dir(change_id) / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    source_index = context_dir / "source-index.yaml"
    target = context_dir / "compression-checkpoint.md"
    target.write_text(
        "\n".join([
            f"# 压缩检查点: {change_id}",
            "",
            "- 本文件只记录分批阅读的短摘要入口，不替代权威事实。",
            f"- source_index: {source_index.relative_to(paths.root) if source_index.exists() else 'not_recorded'}",
            "- compact_handoff_max_lines: 120",
            "",
        ]),
        encoding="utf-8",
    )
    return str(target)


def _enforce_handoff_length(path: Path, *, max_lines: int) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= max_lines:
        return
    trimmed = lines[: max_lines - 2] + ["", "- truncated_by_length_guard: true"]
    path.write_text("\n".join(trimmed) + "\n", encoding="utf-8")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
