# open-cowork Milestone 2 Sync History Summary in Digest 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> 在 `continuity digest` 中补一个最小 `sync-history` 聚合摘要。

上一轮我们已经具备：

1. `sync-history` 的写入、单月查询、跨月聚合查询与月份列表
2. `continuity digest` 的 active / archived 默认阅读入口

但当前仍有一个体验缺口：

- `digest` 已经能告诉人“先看哪个 packet”；
- 但还不能快速告诉人“最近有没有发生对上同步、最近一次同步是什么、同步的语气和目标层是什么”。

本轮要做的，是把 `sync-history` 的最近摘要压进 `digest`，让它更像人的默认入口。

## 2. 设计目标

1. 不新增新的事实文件。
2. 不新增独立查询命令。
3. 只在 `continuity digest` 中补一个最小 `recent_sync_summary`。
4. 若目标 change 没有 sync history，则整体省略该段。
5. 仅复用现有 `sync-history` 数据，不修改其 schema。

## 3. 边界

### 3.1 本轮纳入

1. `resolve_continuity_digest(...)` 增补 `recent_sync_summary`
2. `continuity digest` 文本输出补最小同步摘要
3. 最小测试覆盖

### 3.2 本轮不纳入

1. 新增 `sync-history-summary` 独立命令
2. 趋势分析
3. 图表或 dashboard
4. 多 change 批量摘要

## 4. 推荐方案

推荐采用：

> `digest embeds latest sync summary`

也就是：

1. `digest` 在内部读取当前 change 对应的 sync history
2. 只提取最有价值的最小摘要字段
3. 如果没有事件，就完全省略该段

不推荐：

1. 单独再长一个 `sync-history-summary` 命令
   - 会让命令面继续变厚
2. 直接把完整 events 列表塞进 `digest`
   - 会让 digest 重新变重

## 5. recent_sync_summary 结构

建议最小结构：

```yaml
recent_sync_summary:
  total_events: 2
  latest_recorded_at: 2026-04-24T12:00:00Z
  latest_source_kind: closeout
  latest_sync_kind: escalation
  latest_target_layer: sponsor
  latest_headline: 需要更高层同步
```

### 5.1 字段说明

1. `total_events`
   - 当前 change 在全部月份中的匹配事件数量
2. `latest_recorded_at`
   - 最近一条匹配事件时间
3. `latest_source_kind`
   - 最近一条事件的 `source_kind`
4. `latest_sync_kind`
   - 最近一条事件的 `sync_kind`
5. `latest_target_layer`
   - 最近一条事件的 `target_layer`
6. `latest_headline`
   - 最近一条事件的 `headline`

## 6. 生成规则

1. 仅按当前 digest 的 `change_id` 过滤
2. 从 `read_sync_history_across_months(...)` 或等价内部逻辑获得事件集
3. 以 `recorded_at` 排序后取最后一条为 `latest`
4. 若事件为空，则不输出 `recent_sync_summary`

## 7. CLI 文本输出

在现有 `continuity digest --format text` 基础上，补一行：

```text
recent sync: 2 events / escalation -> sponsor / 需要更高层同步
```

若没有同步记录，则不输出这行。

## 8. 测试建议

至少新增：

1. `test_resolve_continuity_digest_includes_recent_sync_summary_when_history_exists`
2. `test_continuity_digest_text_output_includes_recent_sync_summary`

## 9. 退出条件

1. digest 在存在 sync history 时能输出最小同步摘要
2. 无 sync history 时不报错，且不输出该段
3. 文本输出和结构化输出都可用
4. 全量测试通过
