from __future__ import annotations

from dataclasses import dataclass
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

    def status_snapshot_file(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "STATUS_SNAPSHOT.yaml"

    def archived_change_dir(self, change_id: str) -> Path:
        return self.archive_dir / change_id

    def archived_change_file(self, change_id: str, name: str) -> Path:
        return self.archived_change_dir(change_id) / name
