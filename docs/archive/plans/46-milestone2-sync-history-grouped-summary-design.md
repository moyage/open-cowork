# Milestone 2：Sync History Grouped Summary 设计

## 背景

当前 `sync-history-query` 已支持：
- 单月查询
- 跨月聚合查询
- 文本 / YAML / JSON 输出

但它仍主要返回原始事件列表。对于人和外部只读消费方来说，很多时候更需要的是“按某个维度压缩后”的最小摘要，而不是直接逐条遍历事件。

这次迭代只补一个很小的只读聚合层：
- 不新增事实源
- 不新增存储文件
- 不改变已有 `sync-history` 事件结构
- 只在查询结果中增加可选 `grouped_summary`

## 目标

为 `sync-history-query` 增加可选的 grouped summary 视图，用于把当前查询结果按以下维度之一进行压缩：
- `change_id`
- `source_kind`
- `sync_kind`

## 非目标

本轮不做：
- 新的 runtime / continuity 文件
- dashboard / TUI / 可视化看板
- 更复杂的统计指标（成功率、跨度、趋势图等）
- 多级嵌套聚合

## 设计原则

1. 聚合必须建立在当前查询结果之上，而不是重新读取另一套事实源。
2. 聚合是派生阅读层，不是新的权威状态层。
3. 默认行为不变；只有显式要求 `summary_by` 时才返回 grouped summary。
4. 文本输出只补最小可读摘要，不替代原始事件列表。

## 最小接口

### Continuity 层

- `read_sync_history(..., summary_by=None)`
- `read_sync_history_across_months(..., summary_by=None)`

当 `summary_by` 非空时，返回 payload 增加：

```yaml
grouped_summary:
  group_by: change_id
  groups:
    - group_key: CHG-001
      event_count: 2
      latest_recorded_at: 2026-04-24T13:00:00Z
      latest_headline: 二次同步
```

### CLI 层

新增可选参数：

```bash
ocw continuity sync-history-query --month 202604 --summary-by change_id
ocw continuity sync-history-query --all-months --summary-by sync_kind --format json
```

## 文本输出策略

当存在 `grouped_summary` 时，在原始事件列表前增加一段压缩摘要：

```text
grouped summary by: change_id
- CHG-CLI-SUMMARY events=2 latest=二次同步
```

随后仍保留原始事件列表，避免信息丢失。

## 预期收益

1. 让 `sync-history-query` 从“能查原始事件”进一步变成“能直接读摘要”。
2. 为后续更轻量的人类阅读入口提供稳定中间层。
3. 保持范围严格受控，仍在 Milestone 2 的 continuity / sync 只读面之内。
