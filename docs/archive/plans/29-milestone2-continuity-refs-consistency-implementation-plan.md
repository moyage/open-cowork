# open-cowork Milestone 2 Continuity / Closeout / Sync Refs 一致性实施计划

## 1. 文档目的

本实施计划用于指导 `Milestone 2` 中 `continuity / closeout / sync refs consistency` 的最小实现。

目标不是扩新对象，而是把现有 continuity primitives 中的 `refs` 收紧成更可信的引用层。

## 2. 本轮目标

完成后应具备：

1. continuity 内部统一的 ref helper
2. `closeout-packet` 的 runtime refs 收紧
3. `sync-packet` 的 source-derived refs 重新校验
4. `increment-package` 的 runtime timeline 仅在可解析时写入
5. 对应单元测试与 CLI 回归

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `tests/test_continuity.py`
3. 如有必要，少量 `tests/test_cli.py` 回归调整
4. `docs/README.md`

### 3.2 不纳入

1. runtime status schema 变更
2. sync history/export 结构变更
3. 新 CLI 命令
4. 新 packet schema 版本

## 4. 实现约束

1. 必需 ref 缺失时必须 fail fast。
2. 可选 ref 缺失时应整体省略，而不是输出空占位。
3. source payload 继承 ref 时必须重新解析。
4. 不允许为了让 ref 看起来完整而虚构路径。
5. `runtime_change_status` 只有在 payload `change_id` 匹配目标 change 时才允许写入。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议优先加入：

1. `test_closeout_packet_omits_runtime_change_status_when_active_snapshot_belongs_to_other_change`
2. `test_closeout_packet_omits_runtime_timeline_ref_when_file_missing`
3. `test_sync_packet_omits_runtime_timeline_when_source_ref_target_missing`
4. `test_increment_package_omits_runtime_timeline_when_file_missing`

必须先看到失败，再写生产代码。

### Step 2. 引入统一 helper

在 `continuity.py` 中新增最小 helper：

1. `_ref_path_if_exists(...)`
2. `_append_resolved_payload_ref(...)`
3. `_runtime_change_status_ref_if_matching(...)`

### Step 3. 收紧 increment-package refs

调整 `resolve_increment_package(...)`：

1. `handoff_package` 继续保留为 required
2. `runtime_change_status` 继续保留为 required
3. `runtime_timeline` 改为仅在目标文件存在时写入
4. `verify / owner_transfer` 继续保持 optional

### Step 4. 收紧 closeout-packet refs

调整 `resolve_closeout_packet(...)`：

1. `maintenance_status` 改为 optional
2. `runtime_timeline` 改为 optional
3. `runtime_change_status` 改为 semantic optional
4. 原有 archive required refs 继续保持 fail-fast

### Step 5. 收紧 sync-packet refs

调整 `resolve_sync_packet(...)`：

1. 继续要求 source packet 必须存在
2. 从 source payload 继承 `runtime_timeline` 前先重新解析
3. `owner_transfer` 保持 optional

### Step 6. 跑完整回归

最小命令：

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. 新增失败测试全部转绿
2. 全量测试通过
3. 设计与实施计划文档已接入索引
4. Baseline 已同步
