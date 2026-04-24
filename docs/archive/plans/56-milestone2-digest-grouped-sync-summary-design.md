# Milestone 2 digest grouped sync summary 设计

## 1. 背景

当前 `continuity digest` 已经具备：

1. `recent_sync_summary`
2. `recent_runtime_events`
3. `projection_sources`

但它仍然只能回答“最近一次同步是什么”，还不能直接回答：

- 最近主要在向哪些 `target_layer` 同步
- 同一层近期大概发生了多少次同步

而这部分信息其实已经存在于 `sync-history-query --summary-by target_layer` 的现有能力里。

## 2. 本次目标

在不新增协议对象、不新增事实文件的前提下，让 `continuity digest` 直接复用现有 `sync-history` 聚合结果，补上一层更接近人类默认阅读入口的 grouped sync 摘要。

## 3. 设计原则

1. 只读派生，不新增 truth-source
2. 只复用现有 `sync-history-query` 的聚合能力
3. 不修改 `sync-history` 写入结构
4. 不新增新的 CLI 命令

## 4. 最小结构

在 `continuity-digest/v1` 中新增可选字段：

```yaml
recent_sync_grouped_summary:
  group_by: target_layer
  groups:
    - group_key: sponsor
      event_count: 2
      distinct_change_count: 1
      latest_change_id: CHG-...
      latest_sync_kind: escalation
      latest_headline: 需要更高层同步
```

## 5. CLI 文本输出

`ocw continuity digest --format text` 在存在该字段时增加：

```text
recent sync groups: target_layer
- sponsor events=2 distinct_changes=1 latest_change=CHG-... latest_sync_kind=escalation
```

## 6. 非目标

本次不做：

1. 新的 grouped summary 维度
2. digest 内嵌完整 sync-history 原始事件
3. digest 的跨 change 聚合
4. 新的导出文件

## 7. 一句话结论

这是一层很小的阅读层压缩：  
让 `digest` 在不扩张协议面的前提下，直接带出“最近同步主要流向哪些层”的最小聚合摘要。
