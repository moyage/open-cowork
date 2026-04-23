# open-cowork Milestone 2 Archive Receipt / Archived Refs Consistency 实施计划

## 1. 文档目的

本实施计划用于指导 archived continuity 对象与 `archive-map / archive-receipt` 的最小一致性实现。

## 2. 本轮目标

完成后应具备：

1. `closeout-packet` 在生成前会验证 archive anchor
2. `sync-packet(source=closeout)` 在生成前会验证 archive anchor
3. 对应失败测试、正常路径测试与全量回归

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `tests/test_continuity.py`
3. 视需要少量 `tests/test_cli.py` fixture 对齐
4. `docs/README.md`

### 3.2 不纳入

1. archive_change 主链重写
2. archive-map 自动修复
3. sync-history/export 行为变更
4. increment source 额外归档约束

## 4. 设计约束

1. archived continuity 的一致性必须 fail fast。
2. 不应把 archive-map 缺陷静默降级成 optional。
3. 只校验当前 target change 的 archived anchor，不做全量扫描。
4. 错误信息必须能区分：
   - archive-map 缺 entry
   - archive_path 不匹配
   - receipt 不匹配
   - archived_at 不匹配

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_closeout_packet_rejects_when_archive_map_entry_missing`
2. `test_closeout_packet_rejects_when_archive_map_receipt_mismatches_archived_change`
3. `test_closeout_packet_rejects_when_archive_map_archived_at_mismatches_receipt`
4. `test_sync_packet_from_closeout_rejects_when_archive_anchor_is_inconsistent`

### Step 2. 补正常 fixture

更新已有正常路径测试，让它们显式创建：

1. `archive-map.yaml`
2. 对应 archived entry
3. 合法 `archive-receipt.yaml`

### Step 3. 实现最小 helper

在 `continuity.py` 中新增：

1. `_resolve_archived_change_anchor(...)`

### Step 4. 接入 closeout / sync

1. `resolve_closeout_packet(...)` 在读取 archived files 后调用 helper
2. `resolve_sync_packet(..., source_kind="closeout")` 在读取 source packet 前或后调用 helper

### Step 5. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. archived continuity 对象无法再绕过 archive-map / archive-receipt anchor
2. 新失败测试转绿
3. 全量测试通过
4. 文档索引与 Baseline 已同步
