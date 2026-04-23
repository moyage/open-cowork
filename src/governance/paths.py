from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class GovernancePaths:
    root: Path

    @property
    def governance_dir(self) -> Path:
        return self.root / ".governance"

    @property
    def index_dir(self) -> Path:
        return self.governance_dir / "index"

    @property
    def changes_dir(self) -> Path:
        return self.governance_dir / "changes"

    @property
    def archive_dir(self) -> Path:
        return self.governance_dir / "archive"

    @property
    def runtime_dir(self) -> Path:
        return self.governance_dir / "runtime"

    @property
    def runtime_status_dir(self) -> Path:
        return self.runtime_dir / "status"

    @property
    def runtime_timeline_dir(self) -> Path:
        return self.runtime_dir / "timeline"

    def current_change_file(self) -> Path:
        return self.index_dir / "current-change.yaml"

    def changes_index_file(self) -> Path:
        return self.index_dir / "changes-index.yaml"

    def maintenance_status_file(self) -> Path:
        return self.index_dir / "maintenance-status.yaml"

    def archive_map_file(self) -> Path:
        return self.index_dir / "archive-map.yaml"

    def change_dir(self, change_id: str) -> Path:
        return self.changes_dir / change_id

    def change_file(self, change_id: str, name: str) -> Path:
        return self.change_dir(change_id) / name

    def evidence_dir(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "evidence"

    def continuity_launch_input_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "continuity-launch-input.yaml"

    def round_entry_input_summary_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "ROUND_ENTRY_INPUT_SUMMARY.yaml"

    def handoff_package_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "handoff-package.yaml"

    def owner_transfer_continuity_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "owner-transfer-continuity.yaml"

    def increment_package_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "increment-package.yaml"

    def status_snapshot_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "STATUS_SNAPSHOT.yaml"

    def runtime_change_status_file(self) -> Path:
        return self.runtime_status_dir / "change-status.yaml"

    def runtime_steps_status_file(self) -> Path:
        return self.runtime_status_dir / "steps-status.yaml"

    def runtime_participants_status_file(self) -> Path:
        return self.runtime_status_dir / "participants-status.yaml"

    def runtime_timeline_month_file(self, month_key: str | None = None) -> Path:
        resolved_month = month_key or datetime.now(timezone.utc).strftime("%Y%m")
        return self.runtime_timeline_dir / f"events-{resolved_month}.yaml"

    def archived_change_dir(self, change_id: str) -> Path:
        return self.archive_dir / change_id

    def archived_change_file(self, change_id: str, name: str) -> Path:
        return self.archived_change_dir(change_id) / name
