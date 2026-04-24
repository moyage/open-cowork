# Milestone 2：Sync History Grouped Summary 实施计划

## 范围

本次只实现：
- `sync-history-query` 的可选 `summary_by`
- `grouped_summary` machine-readable 输出
- 文本模式下的最小 grouped summary 渲染

## 实施步骤

1. 先补失败测试
- continuity 层：跨月查询返回 grouped summary
- CLI 层：文本输出显示 grouped summary

2. 实现 continuity 聚合 helper
- 在查询结果的过滤事件集上做分组
- 返回：
  - `group_key`
  - `event_count`
  - `latest_recorded_at`
  - `latest_headline`

3. 接入 CLI 参数
- `--summary-by change_id|source_kind|sync_kind`

4. 接入文本输出
- 先渲染 grouped summary
- 再保留原始事件列表

5. 回归验证
- 目标测试：`test_continuity.py`、`test_cli.py`
- 最终验证：全量 `unittest discover`

## 风险控制

1. 不改变历史事件文件结构。
2. 不改变默认查询返回结构，只有显式指定时才增加 grouped summary。
3. 不让 grouped summary 取代原始 `events`，避免外部消费断裂。
