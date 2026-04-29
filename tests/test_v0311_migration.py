from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.lean_paths import LEGACY_HEAVY_DIRS, ensure_lean_layout
from governance.lean_migration import detect_legacy_layout, migrate_legacy_to_lean, uninstall_governance


class V0311MigrationTests(unittest.TestCase):
    def test_detect_report_lists_legacy_heavy_directories_and_active_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)

            report = detect_legacy_layout(root)

            self.assertTrue(report["legacy_dirs"]["changes"]["exists"])
            self.assertTrue(report["legacy_dirs"]["archive"]["exists"])
            self.assertEqual(report["active_legacy_change"], "CHG-OLD")
            self.assertIn(".governance/changes", report["cleanup_candidates"])

    def test_migrate_dry_run_does_not_move_legacy_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)

            result = migrate_legacy_to_lean(root, dry_run=True, confirm=False)

            self.assertTrue(result["dry_run"])
            self.assertFalse((root / ".governance/state.yaml").exists())
            self.assertTrue((root / ".governance/changes").exists())
            self.assertFalse((root / ".governance/cold/legacy/changes").exists())

    def test_migrate_confirm_moves_legacy_directories_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)

            result = migrate_legacy_to_lean(root, dry_run=False, confirm=True)

            self.assertFalse(result["dry_run"])
            self.assertTrue((root / ".governance/state.yaml").exists())
            self.assertFalse((root / ".governance/changes").exists())
            self.assertTrue((root / ".governance/cold/legacy/changes").exists())
            receipt_path = root / ".governance/cold/legacy/migration-receipt.yaml"
            self.assertTrue(receipt_path.exists())
            receipt_text = receipt_path.read_text(encoding="utf-8")
            self.assertIn("CHG-OLD", receipt_text)
            self.assertIn(".gitignore", receipt_text)
            self.assertIn(".governance/runtime/", (root / ".gitignore").read_text(encoding="utf-8"))

    def test_migration_verify_rejects_receipt_that_does_not_match_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)
            migrate_legacy_to_lean(root, dry_run=False, confirm=True)
            (root / ".governance/changes").mkdir()

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                verify_exit = main(["--root", str(root), "migrate", "verify"])

            self.assertEqual(verify_exit, 1)
            self.assertIn("live legacy directory still exists", stdout.getvalue())

    def test_cli_migrate_and_verify_use_human_readable_chinese_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                detect_exit = main(["--root", str(root), "migrate", "detect"])
                dry_exit = main(["--root", str(root), "migrate", "lean", "--dry-run"])
                migrate_exit = main(["--root", str(root), "migrate", "lean", "--confirm"])
                verify_exit = main(["--root", str(root), "migrate", "verify"])

            output = stdout.getvalue()
            self.assertEqual((detect_exit, dry_exit, migrate_exit, verify_exit), (0, 0, 0, 0))
            self.assertIn("旧版治理目录检测", output)
            self.assertIn("迁移预览", output)
            self.assertIn("迁移完成", output)
            self.assertIn("迁移验证通过", output)

    def test_uninstall_requires_confirm_and_writes_receipt_next_to_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root)

            dry_run = uninstall_governance(root, dry_run=True, confirm=False)
            blocked = uninstall_governance(root, dry_run=False, confirm=False)

            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(blocked["removed"])
            self.assertTrue((root / ".governance").exists())

            removed = uninstall_governance(root, dry_run=False, confirm=True)

            self.assertTrue(removed["removed"])
            self.assertFalse((root / ".governance").exists())
            receipt = root / ".open-cowork-uninstall-receipt.yaml"
            self.assertTrue(receipt.exists())
            receipt_text = receipt.read_text(encoding="utf-8")
            self.assertIn(".governance", receipt_text)
            self.assertIn("pre_uninstall_detect_report", receipt_text)
            self.assertIn("protocol_version", receipt_text)

    def test_cli_hygiene_cleanup_writes_receipt_after_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_legacy_layout(root)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "migrate", "lean", "--confirm"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                dry_exit = main(["--root", str(root), "hygiene", "--cleanup", "--dry-run"])
                cleanup_exit = main(["--root", str(root), "hygiene", "--cleanup", "--confirm"])

            self.assertEqual((dry_exit, cleanup_exit), (0, 0))
            self.assertIn("清理预览", stdout.getvalue())
            self.assertIn("清理确认已记录，未执行物理删除", stdout.getvalue())
            self.assertTrue((root / ".governance/cold/legacy/cleanup-receipt.yaml").exists())


def _make_legacy_layout(root: Path) -> None:
    base = root / ".governance"
    for dirname in LEGACY_HEAVY_DIRS:
        (base / dirname).mkdir(parents=True, exist_ok=True)
    (base / "index/current-change.yaml").write_text(
        "current_change_id: CHG-OLD\n"
        "status: approved\n",
        encoding="utf-8",
    )
    (base / "changes/CHG-OLD/manifest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (base / "changes/CHG-OLD/manifest.yaml").write_text(
        "change_id: CHG-OLD\n"
        "title: 旧版任务\n"
        "status: approved\n",
        encoding="utf-8",
    )
    (base / "archive/CHG-DONE/receipt.yaml").parent.mkdir(parents=True, exist_ok=True)
    (base / "archive/CHG-DONE/receipt.yaml").write_text(
        "change_id: CHG-DONE\n"
        "summary: 已归档旧任务\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
