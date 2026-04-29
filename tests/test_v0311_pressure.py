from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.lean_paths import LEGACY_HEAVY_DIRS, default_read_set_paths, ensure_lean_layout
from governance.lean_round import evaluate_execution_gate, status_gate_decision
from governance.lean_state import initial_lean_state
from governance.simple_yaml import write_yaml


class V0311PressureTests(unittest.TestCase):
    def test_default_read_set_stays_fixed_after_100_rounds_of_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root, initial_state=initial_lean_state(round_id="R-PRESSURE-001", goal="压力测试"))
            _write_compact_history(root, rounds=100)

            paths = default_read_set_paths(root)
            total_bytes = sum(path.stat().st_size for path in paths)

            self.assertEqual([path.name for path in paths], [
                "AGENTS.md",
                "agent-entry.md",
                "current-state.md",
                "state.yaml",
            ])
            self.assertLess(total_bytes, 24000)
            self.assertLessEqual(_line_count(root / ".governance/current-state.md"), 200)
            self.assertLessEqual(_line_count(root / ".governance/state.yaml"), 400)

    def test_cold_history_is_not_part_of_default_read_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root)
            cold = root / ".governance/cold/legacy/archive"
            cold.mkdir(parents=True)
            (cold / "large-history.md").write_text("历史摘要\n" * 1000, encoding="utf-8")

            default_paths = [str(path.relative_to(root)) for path in default_read_set_paths(root)]

            self.assertNotIn(".governance/cold/legacy/archive/large-history.md", default_paths)
            self.assertFalse(any("/cold/" in path for path in default_paths))

    def test_lean_init_and_status_do_not_create_legacy_heavy_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--root", str(root), "init"]), 0)
                self.assertEqual(main(["--root", str(root), "status"]), 0)

            for dirname in LEGACY_HEAVY_DIRS:
                self.assertFalse((root / ".governance" / dirname).exists(), dirname)

    def test_gate_decision_is_consistent_across_execution_and_status_entrypoints(self):
        state = initial_lean_state(round_id="R-GATE-001", goal="入口一致性")

        direct = evaluate_execution_gate(state)
        status = status_gate_decision(state, "execution")

        self.assertEqual(direct, status)
        self.assertFalse(direct["allowed"])
        self.assertEqual(direct["reason"], "participant_initialization_required")


def _write_compact_history(root: Path, *, rounds: int) -> None:
    ledger = []
    evidence = []
    for index in range(rounds):
        round_id = f"R-HIST-{index:03d}"
        ledger.append({
            "round_id": round_id,
            "goal": f"历史轮次 {index}",
            "final_status": "closed",
            "closeout_summary": "已完成并压缩为 ledger 摘要。",
        })
        evidence.append({
            "evidence_id": f"E-{index:03d}",
            "round_id": round_id,
            "kind": "test",
            "ref": f"logs/{round_id}.txt",
            "summary": "测试通过摘要。",
            "created_by": "test",
            "created_at": "2026-04-29T00:00:00+00:00",
        })
    write_yaml(root / ".governance/ledger.yaml", ledger)
    write_yaml(root / ".governance/evidence.yaml", evidence)


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


if __name__ == "__main__":
    unittest.main()
