# Milestone 2：Sync History Distinct Change Count 设计

## 背景

目前 grouped summary 已经可以表达：
- `event_count`
- `latest_headline`
- `latest_change_id`
- `latest_sync_kind`

但仅看 `event_count` 仍然不能判断：
- 这组事件是不是都来自同一个 change
- 还是已经覆盖了多个不同 change

对人类阅读和上层只读消费来说，这个差异很重要。

## 目标

给 grouped summary 增加：
- `distinct_change_count`

并在文本输出中同步显示。

## 非目标

本轮不做：
- 更复杂的 distinct 统计
- 历史趋势分析
- 额外的新文件
- 新的查询命令

## 设计原则

1. 只在 grouped summary 的派生层增加字段。
2. `distinct_change_count` 表示该组内去重后的 `change_id` 数量。
3. 默认事件写入、查询、summary-only 行为都不改变。

## 最小结构

```yaml
grouped_summary:
  group_by: target_layer
  groups:
    - group_key: sponsor
      event_count: 3
      distinct_change_count: 2
      latest_recorded_at: 2026-04-24T14:00:00Z
      latest_headline: B1
      latest_change_id: CHG-B
      latest_sync_kind: routine-sync
```

## 文本输出

```text
- sponsor events=3 distinct_changes=2 latest=B1 latest_change=CHG-B latest_sync_kind=routine-sync
```

## 预期收益

1. 让 grouped summary 更能表达“覆盖面”而不只是“发生次数”。
2. 让 `summary-only` 模式下的信息密度再高一点，但仍保持轻量。
3. 严格留在 Milestone 2 的 sync-history query 投影层范围内。
