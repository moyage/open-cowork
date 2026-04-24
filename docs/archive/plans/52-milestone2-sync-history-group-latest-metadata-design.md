# Milestone 2：Sync History Group Latest Metadata 设计

## 背景

当前 `sync-history-query` 的 grouped summary 已经能表达：
- `group_key`
- `event_count`
- `latest_recorded_at`
- `latest_headline`

但在 `summary-only` 模式下，这还不够完整。阅读者仍然会追问：
- 最近这条同步属于哪个 change？
- 最近这条同步是 `routine-sync` 还是 `escalation`？

## 目标

在 grouped summary 中补两个最小字段：
- `latest_change_id`
- `latest_sync_kind`

并让文本输出也把这两项打出来。

## 非目标

本轮不做：
- 更多统计维度
- 历史趋势分析
- 新的摘要文件
- 改动底层 sync-history 事件结构

## 设计原则

1. 只在 grouped summary 派生层补字段，不动事实层。
2. 这两个字段只反映“该组最新事件”的元信息。
3. 文本输出保持轻量，不变成表格或新格式系统。

## 最小结构

```yaml
grouped_summary:
  group_by: target_layer
  groups:
    - group_key: sponsor
      event_count: 2
      latest_recorded_at: 2026-04-24T13:00:00Z
      latest_headline: B1
      latest_change_id: CHG-B
      latest_sync_kind: routine-sync
```

## 文本输出

```text
- sponsor events=2 latest=B1 latest_change=CHG-B latest_sync_kind=routine-sync
```

## 预期收益

1. 让 `summary-only` 更像一个真正可直接消费的轻量摘要。
2. 让 grouped summary 不必再回跳到原始 events 才能看懂“最近是谁、哪类同步”。
3. 严格保持在 Milestone 2 的 sync-history query 投影层范围内。
