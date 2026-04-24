# Milestone 2：Sync History Summary Only 设计

## 背景

上一轮我们已经为 `sync-history-query` 增加了 `grouped_summary`，可以按：
- `change_id`
- `source_kind`
- `sync_kind`

做最小聚合。

但当前返回仍默认带完整 `events` 列表。对于很多人类阅读场景和外部只读消费场景来说，如果目标只是“看摘要”，完整事件流反而会让输出变重。

## 目标

为 `sync-history-query` 增加 `--summary-only`：
- 仍保留 `summary` 和 `grouped_summary`
- 隐藏原始 `events`
- 不改任何 sync-history 事实文件
- 不改现有事件写入逻辑

## 非目标

本轮不做：
- 新的摘要文件
- digest 与 sync-history 的自动融合
- 更复杂的统计指标
- 默认行为变更

## 设计原则

1. `summary-only` 只影响查询投影，不影响底层数据。
2. 只有显式传入时才隐藏 `events`，避免破坏现有消费方。
3. 文本输出也遵循同一原则：显示 grouped summary，但不再逐条打印事件。

## 最小接口

### Continuity 层

- `read_sync_history(..., summary_only=False)`
- `read_sync_history_across_months(..., summary_only=False)`

当 `summary_only=True` 时：
- `summary` 保留
- `grouped_summary` 保留
- `events` 返回空列表

### CLI 层

```bash
ocw continuity sync-history-query --month 202604 --summary-by change_id --summary-only --format text
ocw continuity sync-history-query --all-months --summary-by sync_kind --summary-only --format json
```

## 预期收益

1. 让 `sync-history-query` 更适合直接做摘要消费。
2. 为后续人类默认阅读层继续“做薄”提供更稳的中间层。
3. 严格保持在 Milestone 2 的 query / summary 范围内，不开新主线。
