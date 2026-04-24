# open-cowork Milestone 2 Sync History Query 实施计划

## 1. 文档目的

本实施计划用于指导 `sync-history` 只读查询层的最小实现。

## 2. 本轮目标

完成后应具备：

1. `read_sync_history(...)`
2. `ocw continuity sync-history-query`
3. `text / yaml / json` 输出
4. 最小筛选能力与测试覆盖

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `src/governance/cli.py`
3. `tests/test_continuity.py`
4. `tests/test_cli.py`
5. `docs/README.md`

### 3.2 不纳入

1. 跨月聚合
2. 排序参数
3. export bundle 扩展
4. sync-history 文件结构变更

## 4. 设计约束

1. 保持现有 `sync-history` append 命令不变。
2. query 是只读动作，不得写文件。
3. 不新增新的底层事实源。
4. 月文件缺失应返回空 payload，而不是报错。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_read_sync_history_returns_empty_payload_when_month_missing`
2. `test_read_sync_history_filters_by_change_id_and_source_kind`
3. `test_continuity_sync_history_query_command_supports_json_output`
4. `test_continuity_sync_history_query_command_supports_text_output`

### Step 2. 实现只读 helper

建议新增：

1. `read_sync_history(root, *, month, change_id=None, source_kind=None, sync_kind=None) -> dict`

### Step 3. 实现 CLI

建议新增：

1. `cmd_continuity_sync_history_query(args)`
2. parser 子命令：`continuity sync-history-query`

### Step 4. 回归验证

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. query 能正确返回空月 payload
2. query 能按筛选项收缩事件集合
3. text/yaml/json 三类输出至少覆盖 text/json
4. 全量测试通过
