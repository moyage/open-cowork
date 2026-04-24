# Milestone 2 Handoff Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 active change 落地最小 `handoff-package.yaml` 派生能力，并通过 CLI 暴露一个稳定入口。

**Architecture:** 在现有 `governance.continuity` 中新增 handoff package 的解析与物化逻辑，复用 current change、manifest、contract、bindings、runtime status 等已有事实层。CLI 只负责触发生成与输出结果，所有字段保持“受控镜像 + refs”模型，不新增平行 truth-source。

**Tech Stack:** Python 3、`unittest`、现有 `governance` YAML 工具链

---

### Task 1: 为 continuity 增加 handoff package 解析与物化能力

**Files:**
- Modify: `src/governance/continuity.py`
- Modify: `src/governance/paths.py`
- Test: `tests/test_continuity.py`

- [ ] **Step 1: 写第一个失败测试，覆盖“无 predecessor 也能生成 handoff package”**

```python
def test_materialize_handoff_package_without_predecessor_baseline(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_governance_index(root)
        change_id = "CHG-HO-1"
        change_dir = root / f".governance/changes/{change_id}"
        change_dir.mkdir(parents=True, exist_ok=True)
        set_current_change(root, {
            "change_id": change_id,
            "path": f".governance/changes/{change_id}",
            "status": "step6-executed-pre-step7",
            "current_step": 6,
        })
        upsert_change_entry(root, {
            "change_id": change_id,
            "path": f".governance/changes/{change_id}",
            "status": "step6-executed-pre-step7",
            "current_step": 6,
        })
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": "handoff package test",
            "status": "step6-executed-pre-step7",
            "current_step": 6,
            "roles": {
                "executor": "executor-agent",
                "verifier": "verifier-agent",
                "reviewer": "reviewer-agent",
            },
        })
        write_yaml(change_dir / "contract.yaml", {
            "objective": "handoff package generation",
            "validation_objects": ["HandoffPackageSchema"],
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "6": {"owner": "executor-agent", "gate": "auto-pass"},
                "7": {"owner": "verifier-agent", "gate": "review-required"},
                "8": {"owner": "reviewer-agent", "gate": "approval-required"},
            },
        })
        (change_dir / "tasks.md").write_text("# Tasks\\n\\nGenerate handoff package.\\n", encoding="utf-8")

        output_path = Path(materialize_handoff_package(root, change_id))
        payload = load_yaml(output_path)

        self.assertEqual(payload["schema"], "handoff-package/v1")
        self.assertEqual(payload["change_id"], change_id)
        self.assertEqual(payload["summary"]["current_status"], "step6-executed-pre-step7")
        self.assertNotIn("carry_forward", payload)
```

- [ ] **Step 2: 运行单测，确认它因能力缺失而失败**

Run: `python3 -m unittest tests.test_continuity.ContinuityTests.test_materialize_handoff_package_without_predecessor_baseline -v`

Expected: FAIL，提示 `materialize_handoff_package` 或相关路径/字段尚不存在

- [ ] **Step 3: 最小实现 paths 与 continuity 入口**

```python
def handoff_package_file(self, change_id: str) -> Path:
    return self.change_dir(change_id) / "handoff-package.yaml"


def resolve_handoff_package(root: str | Path, change_id: str | None = None) -> dict:
    # 解析 active change
    # 如 runtime/status 未生成，先 materialize_runtime_status(...)
    # 从 manifest / contract / bindings / runtime status 派生 handoff payload
    return payload


def materialize_handoff_package(root: str | Path, change_id: str | None = None) -> str:
    payload = resolve_handoff_package(root, change_id)
    target = GovernancePaths(Path(root)).handoff_package_file(payload["change_id"])
    write_yaml(target, payload)
    return str(target)
```

- [ ] **Step 4: 再加一个失败测试，覆盖“runtime/status 未预生成时可自动 materialize”**

```python
def test_handoff_package_materializes_runtime_status_when_missing(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_governance_index(root)
        change_id = "CHG-HO-2"
        # 准备 manifest / contract / bindings / current-change
        output_path = Path(materialize_handoff_package(root, change_id))
        payload = load_yaml(output_path)

        self.assertTrue((root / ".governance/runtime/status/change-status.yaml").exists())
        self.assertEqual(payload["refs"]["runtime_change_status"], ".governance/runtime/status/change-status.yaml")
```

- [ ] **Step 5: 用最小实现让第二个测试通过**

```python
from .runtime_status import materialize_runtime_status


def _ensure_runtime_status(root: Path, change_id: str) -> dict:
    paths = GovernancePaths(root)
    if not paths.runtime_change_status_file().exists():
        return materialize_runtime_status(root, change_id)
    return {
        "change_status": load_yaml(paths.runtime_change_status_file()),
        "steps_status": load_yaml(paths.runtime_steps_status_file()),
        "participants_status": load_yaml(paths.runtime_participants_status_file()),
    }
```

- [ ] **Step 6: 运行 continuity 测试文件，确认新增与既有 continuity 都通过**

Run: `python3 -m unittest tests.test_continuity -v`

Expected: PASS，且既有 `launch-input / round-entry-summary` 测试不回归

- [ ] **Step 7: 提交这一段**

```bash
git add src/governance/paths.py src/governance/continuity.py tests/test_continuity.py
git commit -m "feat: add handoff package continuity primitive"
```

### Task 2: 为 CLI 增加 `continuity handoff-package` 入口

**Files:**
- Modify: `src/governance/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 CLI 入口生成 handoff package**

```python
def test_continuity_handoff_package_command_materializes_output(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # 准备一个最小 active change
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main([
                "--root", str(root),
                "continuity", "handoff-package",
                "--change-id", "CHG-HO-CLI",
            ])

        self.assertEqual(exit_code, 0)
        self.assertIn("Handoff package written:", stdout.getvalue())
        self.assertTrue((root / ".governance/changes/CHG-HO-CLI/handoff-package.yaml").exists())
```

- [ ] **Step 2: 运行单测，确认 CLI 子命令尚未实现**

Run: `python3 -m unittest tests.test_cli.CliTests.test_continuity_handoff_package_command_materializes_output -v`

Expected: FAIL，提示子命令不存在或未分发

- [ ] **Step 3: 最小实现 CLI 子命令**

```python
def cmd_continuity_handoff_package(args):
    from governance.continuity import materialize_handoff_package

    output_path = materialize_handoff_package(args.root, args.change_id)
    print(f"Handoff package written: {output_path}")
    return 0
```

```python
p_continuity_handoff = p_continuity_sub.add_parser("handoff-package", help="Write handoff package yaml")
p_continuity_handoff.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
```

```python
elif args.command == "continuity" and args.subcmd == "handoff-package":
    return cmd_continuity_handoff_package(args)
```

- [ ] **Step 4: 运行 CLI 相关测试**

Run: `python3 -m unittest tests.test_cli -v`

Expected: PASS，且既有 continuity / runtime / lifecycle CLI 测试不回归

- [ ] **Step 5: 提交这一段**

```bash
git add src/governance/cli.py tests/test_cli.py
git commit -m "feat: add continuity handoff package command"
```

### Task 3: 补齐可选 refs、错误边界与文档索引

**Files:**
- Modify: `src/governance/continuity.py`
- Modify: `tests/test_continuity.py`
- Modify: `docs/README.md`

- [ ] **Step 1: 写失败测试，覆盖 verify/review 缺失时不失败、存在 continuity 文件时带出 carry_forward**

```python
def test_handoff_package_uses_optional_refs_when_available(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        change_id = "CHG-HO-3"
        # 准备 continuity-launch-input.yaml 与 ROUND_ENTRY_INPUT_SUMMARY.yaml
        payload = resolve_handoff_package(root, change_id)

        self.assertIn("carry_forward", payload)
        self.assertIn("verify", payload["refs"])
        self.assertIn("review", payload["refs"])
```
```
def test_handoff_package_fails_without_active_change_context(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_governance_index(root)
        with self.assertRaises(ValueError):
            resolve_handoff_package(root)
```

- [ ] **Step 2: 运行单测，确认它们先红**

Run: `python3 -m unittest tests.test_continuity.ContinuityTests.test_handoff_package_uses_optional_refs_when_available tests.test_continuity.ContinuityTests.test_handoff_package_fails_without_active_change_context -v`

Expected: FAIL，提示可选 refs / 错误边界尚未齐备

- [ ] **Step 3: 最小实现可选 refs 与错误边界**

```python
def _optional_ref(path: Path, root: Path) -> str | None:
    return str(path.relative_to(root)) if path.exists() else None


def _build_handoff_refs(paths: GovernancePaths, change_id: str) -> dict:
    refs = {
        "runtime_change_status": str(paths.runtime_change_status_file().relative_to(paths.root)),
        "runtime_steps_status": str(paths.runtime_steps_status_file().relative_to(paths.root)),
        "runtime_participants_status": str(paths.runtime_participants_status_file().relative_to(paths.root)),
    }
    verify_ref = _optional_ref(paths.change_file(change_id, "verify.yaml"), paths.root)
    review_ref = _optional_ref(paths.change_file(change_id, "review.yaml"), paths.root)
    if verify_ref:
        refs["verify"] = verify_ref
    if review_ref:
        refs["review"] = review_ref
    return refs
```

- [ ] **Step 4: 更新文档索引，让实现计划与设计稿一起可发现**

```markdown
- `plans/08-milestone2-handoff-package-design.md`
- `plans/09-milestone2-handoff-package-implementation-plan.md`
```

- [ ] **Step 5: 跑全量回归**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS，新增 handoff tests 通过，总测试数增加

- [ ] **Step 6: 提交这一段**

```bash
git add src/governance/continuity.py tests/test_continuity.py docs/README.md docs/plans/09-milestone2-handoff-package-implementation-plan.md
git commit -m "feat: finalize handoff package continuity flow"
```
