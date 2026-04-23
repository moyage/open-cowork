# Milestone 2 Increment Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 active change 落地最小 `increment-package.yaml` 生成能力，并通过 CLI 记录本段新增/失效/残留的结构化增量。

**Architecture:** 在现有 `governance.continuity` 中新增 increment package 的生成逻辑，复用 handoff package 与 runtime status 作为状态锚点，并通过 CLI 输入写入 `delta` 中的显式增量内容。实现保持“状态派生 + 增量记录”模型，不新增平行 truth-source。

**Tech Stack:** Python 3、`unittest`、现有 `governance` YAML 工具链

---

### Task 1: 为 continuity 增加 increment package 生成能力

**Files:**
- Modify: `src/governance/continuity.py`
- Modify: `src/governance/paths.py`
- Test: `tests/test_continuity.py`

- [ ] **Step 1: 写失败测试，覆盖生成 increment package 会自动 materialize handoff**

```python
def test_materialize_increment_package_records_delta_and_handoff_ref(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_governance_index(root)
        change_id = "CHG-INCR-1"
        # 准备最小 active change
        output_path = Path(materialize_increment_package(
            root,
            change_id=change_id,
            reason="post-verify update",
            segment_owner="verifier-agent",
            segment_label="verify-to-review",
            new_findings=["runtime status schema 已稳定"],
            invalidated_assumptions=["timeline 可以只靠生成式补写"],
            new_risks=["owner transfer 尚未进入 review trace"],
            blockers=["review gate still pending"],
            next_followups=["prepare review decision"],
        ))
        payload = load_yaml(output_path)

        self.assertEqual(payload["schema"], "increment-package/v1")
        self.assertEqual(payload["increment_context"]["segment_owner"], "verifier-agent")
        self.assertIn("handoff_package", payload["refs"])
        self.assertTrue((root / f".governance/changes/{change_id}/handoff-package.yaml").exists())
```

- [ ] **Step 2: 跑 continuity 定向测试，确认先红**

Run: `python3 -m unittest discover -s tests -p 'test_continuity.py' -v`

Expected: FAIL，提示 increment package 入口或路径尚不存在

- [ ] **Step 3: 最小实现 increment package 路径与 materialize 逻辑**

```python
def increment_package_file(self, change_id: str) -> Path:
    return self.change_dir(change_id) / "increment-package.yaml"
```

```python
def materialize_increment_package(...):
    # 若 handoff 不存在，先 materialize_handoff_package(...)
    # 从 handoff/runtime status 派生 state_anchor
    # 写入 increment_context / delta / refs
    return str(target)
```

- [ ] **Step 4: 再写失败测试，覆盖 owner transfer 缺失时不失败、delta 全空时失败**

```python
def test_increment_package_omits_owner_transfer_ref_when_missing(self):
    payload = resolve_increment_package(...)
    self.assertNotIn("owner_transfer", payload["refs"])
```

```python
def test_increment_package_requires_non_empty_delta(self):
    with self.assertRaises(ValueError):
        materialize_increment_package(
            root,
            change_id="CHG-INCR-1",
            reason="empty delta",
            segment_owner="verifier-agent",
            segment_label="verify-to-review",
            new_findings=[],
            invalidated_assumptions=[],
            new_risks=[],
            blockers=[],
            next_followups=[],
        )
```

- [ ] **Step 5: 用最小实现让第二组测试通过**

```python
if not any([new_findings, invalidated_assumptions, new_risks, blockers, next_followups]):
    raise ValueError("increment package requires at least one delta item")
```

- [ ] **Step 6: 跑 continuity 测试文件，确认 increment 与 handoff/owner transfer 不回归**

Run: `python3 -m unittest discover -s tests -p 'test_continuity.py' -v`

Expected: PASS

- [ ] **Step 7: 提交这一段**

```bash
git add src/governance/paths.py src/governance/continuity.py tests/test_continuity.py
git commit -m "feat: add increment package continuity primitive"
```

### Task 2: 为 CLI 增加 `continuity increment-package` 入口

**Files:**
- Modify: `src/governance/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 CLI 入口**

```python
def test_continuity_increment_package_command_materializes_output(self):
    exit_code = main([
        "--root", str(root),
        "continuity", "increment-package",
        "--change-id", "CHG-INCR-CLI",
        "--reason", "post-verify update",
        "--segment-owner", "verifier-agent",
        "--segment-label", "verify-to-review",
        "--new-finding", "runtime status schema 已稳定",
        "--invalidated-assumption", "timeline 可以只靠生成式补写",
        "--new-risk", "owner transfer 尚未进入 review trace",
        "--blocker", "review gate still pending",
        "--next-followup", "prepare review decision",
    ])
    self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: 跑 CLI 定向测试，确认先红**

Run: `python3 -m unittest discover -s tests -p 'test_cli.py' -v`

Expected: FAIL，提示 `increment-package` 子命令尚未实现

- [ ] **Step 3: 最小实现 CLI 子命令**

```python
def cmd_continuity_increment_package(args):
    from governance.continuity import materialize_increment_package

    output_path = materialize_increment_package(
        args.root,
        change_id=args.change_id,
        reason=args.reason,
        segment_owner=args.segment_owner,
        segment_label=args.segment_label,
        new_findings=list(args.new_finding or []),
        invalidated_assumptions=list(args.invalidated_assumption or []),
        new_risks=list(args.new_risk or []),
        blockers=list(args.blocker or []),
        next_followups=list(args.next_followup or []),
    )
    print(f"Increment package written: {output_path}")
    return 0
```

- [ ] **Step 4: 跑 CLI 定向测试**

Run: `python3 -m unittest discover -s tests -p 'test_cli.py' -v`

Expected: PASS

- [ ] **Step 5: 提交这一段**

```bash
git add src/governance/cli.py tests/test_cli.py
git commit -m "feat: add increment package command"
```

### Task 3: 文档索引与全量回归

**Files:**
- Modify: `docs/README.md`
- Add: `docs/plans/13-milestone2-increment-package-implementation-plan.md`

- [ ] **Step 1: 更新文档索引**

```markdown
- `plans/12-milestone2-increment-package-design.md`
- `plans/13-milestone2-increment-package-implementation-plan.md`
```

- [ ] **Step 2: 跑全量回归**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS，总测试数增加

- [ ] **Step 3: 提交这一段**

```bash
git add docs/README.md docs/plans/13-milestone2-increment-package-implementation-plan.md
git commit -m "docs: add increment package implementation plan"
```
