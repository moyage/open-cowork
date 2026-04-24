# Milestone 2：Sync History Target Layer Summary 设计

## 背景

`sync-history-query` 目前已经支持：
- 按 `change_id` 聚合
- 按 `source_kind` 聚合
- 按 `sync_kind` 聚合
- `summary-only` 轻量摘要模式

但从上层消费视角看，另一个很自然的问题是：

> 最近都在向哪些上层对象或协作层进行同步？

这个问题更接近 `target_layer`，而不是 `change_id` 或 `source_kind`。

## 目标

为 `sync-history-query --summary-by` 增加 `target_layer`，让查询可以直接输出：
- 每个目标层的事件数量
- 该目标层最近一次同步的 headline

## 非目标

本轮不做：
- 更复杂的层级拓扑模型
- `target_scope` 联合聚合
- 新的 sync-history 文件结构
- 新的独立命令

## 设计原则

1. 继续复用现有 grouped summary 机制，不新增平行摘要对象。
2. `target_layer` 只是新增一个聚合维度，不改变默认行为。
3. 文本 / JSON / YAML 都沿用现有 query 输出通道。

## 最小接口

```bash
ocw continuity sync-history-query --month 202604 --summary-by target_layer
ocw continuity sync-history-query --all-months --summary-by target_layer --summary-only --format json
```

返回结构保持不变，只是 `group_by` 可新增：

```yaml
grouped_summary:
  group_by: target_layer
  groups:
    - group_key: sponsor
      event_count: 2
      latest_recorded_at: 2026-04-24T13:00:00Z
      latest_headline: B1
```

## 预期收益

1. 让 sync-history 更适合“向上同步面”的读取。 
2. 保持在 Milestone 2 的 continuity / sync / query 范围内。
3. 为后续 digest 或更轻量阅读层提供稳定上游摘要。
