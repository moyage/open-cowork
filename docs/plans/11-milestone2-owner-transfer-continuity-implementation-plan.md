# Milestone 2 Owner Transfer Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 active change 落地最小 `owner-transfer-continuity.yaml` 记录能力，并通过 `prepare/accept` CLI 显式记录 owner 转移与接收。

**Architecture:** 在现有 `governance.continuity` 中新增 owner transfer continuity 的记录逻辑，复用 handoff package 作为内容层引用。`prepare` 负责建立 transfer 记录，`accept` 负责更新 acceptance 状态，均不自动修改 `bindings.yaml` 或 `contract.yaml`。

**Tech Stack:** Python 3、`unittest`、现有 `governance` YAML 工具链

---

### Task 1: 为 continuity 增加 owner transfer continuity 记录能力

**Files:**
- Modify: `src/governance/continuity.py`
- Modify: `src/governance/paths.py`
- Test: `tests/test_continuity.py`

- [ ] **Step 1: 写失败测试，覆盖 `prepare` 会自动生成 handoff 并落 transfer record**

```python
def test_prepare_owner_transfer_continuity_materializes_transfer_record(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ensure_governance_index(root)
        change_id = "CHG-OT-1"
        # 准备最小 active change
        output_path = Path(prepare_owner_transfer_continuity(
            root,
            change_id=change_id,
            target_role="reviewer",
            outgoing_owner="reviewer-agent-a",
            incoming_owner="reviewer-agent-b",
            reason="session handoff",
            initiated_by="maintainer-agent",
        ))
        payload = load_yaml(output_path)

        self.assertEqual(payload["schema"], "owner-transfer-continuity/v1")
        self.assertEqual(payload["acceptance"]["status"], "pending")
        self.assertTrue((root / f".governance/changes/{change_id}/handoff-package.yaml").exists())
```

- [ ] **Step 2: 跑 continuity 定向测试，确认先红**

Run: `python3 -m unittest discover -s tests -p 'test_continuity.py' -v`

Expected: FAIL，提示 owner transfer continuity 入口或路径尚不存在

- [ ] **Step 3: 最小实现 owner transfer continuity 路径与 prepare 逻辑**

```python
def owner_transfer_continuity_file(self, change_id: str) -> Path:
    return self.change_dir(change_id) / "owner-transfer-continuity.yaml"
```

```python
def prepare_owner_transfer_continuity(...):
    # 若 handoff 不存在，先 materialize_handoff_package(...)
    # 从 handoff/runtime status 派生 state_snapshot
    # 写入 transfer_context / acceptance.pending / refs
    return str(target)
```

- [ ] **Step 4: 再写失败测试，覆盖 `accept` 从 pending 更新为 accepted，且不允许重复 accept**

```python
def test_accept_owner_transfer_continuity_updates_acceptance_state(self):
    payload = accept_owner_transfer_continuity(
        root,
        change_id="CHG-OT-1",
        accepted_by="reviewer-agent-b",
        note="accept handoff",
    )
    self.assertEqual(payload["acceptance"]["status"], "accepted")
    self.assertEqual(payload["acceptance"]["accepted_by"], "reviewer-agent-b")
```

```python
def test_accept_owner_transfer_continuity_rejects_non_pending_state(self):
    with self.assertRaises(ValueError):
        accept_owner_transfer_continuity(
            root,
            change_id="CHG-OT-1",
            accepted_by="reviewer-agent-b",
            note="duplicate accept",
        )
```

- [ ] **Step 5: 用最小实现让 acceptance 行为变绿**

```python
def accept_owner_transfer_continuity(root: str | Path, change_id: str, accepted_by: str, note: str = "") -> dict:
    payload = load_yaml(path)
    if payload["acceptance"]["status"] != "pending":
        raise ValueError("owner transfer continuity is not pending")
    payload["acceptance"].update({
        "status": "accepted",
        "accepted_by": accepted_by,
        "accepted_at": _now_utc(),
        "note": note,
    })
    write_yaml(path, payload)
    return payload
```

- [ ] **Step 6: 跑 continuity 测试文件，确认 owner transfer 与 handoff/launch-input 不回归**

Run: `python3 -m unittest discover -s tests -p 'test_continuity.py' -v`

Expected: PASS

- [ ] **Step 7: 提交这一段**

```bash
git add src/governance/paths.py src/governance/continuity.py tests/test_continuity.py
git commit -m "feat: add owner transfer continuity records"
```

### Task 2: 为 CLI 增加 `continuity owner-transfer prepare/accept` 入口

**Files:**
- Modify: `src/governance/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 `prepare` CLI**

```python
def test_continuity_owner_transfer_prepare_command_writes_record(self):
    exit_code = main([
        "--root", str(root),
        "continuity", "owner-transfer", "prepare",
        "--change-id", "CHG-OT-CLI",
        "--target-role", "reviewer",
        "--outgoing-owner", "reviewer-agent-a",
        "--incoming-owner", "reviewer-agent-b",
        "--reason", "session handoff",
        "--initiated-by", "maintainer-agent",
    ])
    self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: 写失败测试，覆盖 `accept` CLI**

```python
def test_continuity_owner_transfer_accept_command_updates_record(self):
    exit_code = main([
        "--root", str(root),
        "continuity", "owner-transfer", "accept",
        "--change-id", "CHG-OT-CLI",
        "--accepted-by", "reviewer-agent-b",
        "--note", "accept handoff",
    ])
    self.assertEqual(exit_code, 0)
```

- [ ] **Step 3: 最小实现 CLI 子命令**

```python
def cmd_continuity_owner_transfer_prepare(args):
    ...

def cmd_continuity_owner_transfer_accept(args):
    ...
```

```python
p_continuity_owner_transfer = p_continuity_sub.add_parser("owner-transfer", ...)
p_owner_transfer_sub = p_continuity_owner_transfer.add_subparsers(dest="owner_transfer_subcmd")
```

```python
elif args.command == "continuity" and args.subcmd == "owner-transfer" and args.owner_transfer_subcmd == "prepare":
    ...
elif args.command == "continuity" and args.subcmd == "owner-transfer" and args.owner_transfer_subcmd == "accept":
    ...
```

- [ ] **Step 4: 跑 CLI 定向测试**

Run: `python3 -m unittest discover -s tests -p 'test_cli.py' -v`

Expected: PASS

- [ ] **Step 5: 提交这一段**

```bash
git add src/governance/cli.py tests/test_cli.py
git commit -m "feat: add owner transfer continuity commands"
```

### Task 3: 文档索引与全量回归

**Files:**
- Modify: `docs/README.md`
- Add: `docs/plans/11-milestone2-owner-transfer-continuity-implementation-plan.md`

- [ ] **Step 1: 更新文档索引**

```markdown
- `plans/10-milestone2-owner-transfer-continuity-design.md`
- `plans/11-milestone2-owner-transfer-continuity-implementation-plan.md`
```

- [ ] **Step 2: 跑全量回归**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS，总测试数增加

- [ ] **Step 3: 提交这一段**

```bash
git add docs/README.md docs/plans/11-milestone2-owner-transfer-continuity-implementation-plan.md
git commit -m "docs: add owner transfer implementation plan"
```
