from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.change_package import CORE_CHANGE_FILES, create_change_package, read_change_package, update_manifest
from governance.index import ensure_governance_index, set_current_change
from governance.simple_yaml import write_yaml


class ChangePackageTests(unittest.TestCase):
    def test_create_read_and_update_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            package = create_change_package(root, "CHG-2", title="Demo")
            for name in CORE_CHANGE_FILES:
                self.assertTrue((package.path / name).exists(), name)
            self.assertTrue((package.path / "evidence").is_dir())
            set_current_change(root, {"change_id": "CHG-2", "path": ".governance/changes/CHG-2", "status": "drafting", "current_step": 5})
            self.assertEqual(read_change_package(root).change_id, "CHG-2")
            manifest = update_manifest(root, "CHG-2", status="step6-ready")
            self.assertEqual(manifest["status"], "step6-ready")

    def test_read_change_package_supports_flat_current_change_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-2", title="Demo")
            write_yaml(root / ".governance/index/current-change.yaml", {
                "current_change_id": "CHG-2",
                "status": "architect-drafted",
                "formal_dispatch_status": "pending",
            })

            self.assertEqual(read_change_package(root).change_id, "CHG-2")


if __name__ == "__main__":
    unittest.main()
