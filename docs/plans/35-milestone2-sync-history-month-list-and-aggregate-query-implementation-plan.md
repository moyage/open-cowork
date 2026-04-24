# open-cowork Milestone 2 Sync History 月份列表与跨月聚合查询实施计划

## 1. 文档目的

本实施计划用于指导 `sync-history` 的月份列表与跨月聚合查询最小实现。

## 2. 本轮目标

完成后应具备：

1. `list_sync_history_months(...)`
2. `read_sync_history_across_months(...)` 或等价实现
3. `ocw continuity sync-history-months`
4. `ocw continuity sync-history-query --all-months`

## 3. 范围

### 3.1 纳入

1. `src/governance/continuity.py`
2. `src/governance/cli.py`
3. `tests/test_continuity.py`
4. `tests/test_cli.py`
5. `docs/README.md`

### 3.2 不纳入

1. 时间范围参数
2. 分页
3. 历史统计指标
4. 新导出格式

## 4. 设计约束

1. 所有新能力都必须只读。
2. 现有 `sync-history` append 命令不变。
3. `--month` 与 `--all-months` 不可同时出现。
4. 空目录/空月份不报错，返回空结果。

## 5. 推荐实现步骤

### Step 1. 先写失败测试

建议新增：

1. `test_list_sync_history_months_returns_sorted_month_keys`
2. `test_read_sync_history_across_all_months_applies_filters`
3. `test_continuity_sync_history_months_command_supports_json_output`
4. `test_continuity_sync_history_query_command_supports_all_months_json_output`

### Step 2. 实现 helper

建议新增：

1. `list_sync_history_months(root) -> list[str]`
2. `read_sync_history_across_months(...) -> dict`

### Step 3. 扩 CLI

新增：

1. `cmd_continuity_sync_history_months(args)`
2. `sync-history-months` parser
3. `sync-history-query --all-months`

### Step 4. 全量回归

```bash
python3 -m unittest discover -s tests -v
```

## 6. 退出条件

1. 能列月
2. 能跨月查
3. 单月查询仍兼容
4. 全量测试通过
