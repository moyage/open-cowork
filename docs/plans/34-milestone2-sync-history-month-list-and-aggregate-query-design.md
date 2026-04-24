# open-cowork Milestone 2 Sync History 月份列表与跨月聚合查询设计

## 1. 文档目的

本设计文档用于把 `sync-history` 查询层从“单月查询”继续推进到：

1. 月份列表
2. 可选跨月聚合查询

上一轮我们已经完成：

- `sync-history` append
- `sync-history-query --month ...`
- `text / yaml / json` 输出

现在最自然的缺口是：

- 用户和外部 agent 还不知道“当前有哪些月份可查”；
- 如果要跨月看某个 `change_id` 的历史，还得手工一个月一个月读；
- 但我们又不希望一下子做成复杂报表层。

本轮目标就是在不改动底层 `sync-history` 月文件结构的前提下，补一个很轻量的可发现与可聚合读取层。

## 2. 设计目标

1. 列出已有 `sync-history` 月份。
2. 在现有 `sync-history-query` 上支持 `--all-months`。
3. 保持现有 `--month` 单月查询行为不变。
4. 不引入新的事实源或缓存层。

## 3. 边界

### 3.1 本轮纳入

1. `list_sync_history_months(...)`
2. `read_sync_history(..., month=..., ...)` 保持不变
3. 新增跨月读取 helper
4. CLI：
   - `ocw continuity sync-history-months`
   - `ocw continuity sync-history-query --all-months`

### 3.2 本轮不纳入

1. 时间范围查询
2. 分页
3. 多维聚合报表
4. 趋势统计图
5. 外部 export 直接消费历史集合

## 4. 推荐方案

推荐采用：

> `list months separately + extend query with all-months flag`

也就是：

1. 单独提供月份列表命令，解决“可发现性”；
2. 在现有 `sync-history-query` 上增加 `--all-months`，解决“最小跨月读取”；
3. 不新增新的跨月 query 命名对象。

## 5. 月份列表

建议新增只读 helper：

- `list_sync_history_months(root) -> list[str]`

规则：

1. 从 `.governance/runtime/sync-history/` 下扫描 `events-YYYYMM.yaml`
2. 提取月份 key
3. 返回升序或时间序序列

建议 CLI：

```bash
ocw continuity sync-history-months --format text|yaml|json
```

最小 text 输出：

```text
Sync history months: 202604, 202605
```

## 6. 跨月查询

建议在现有：

```bash
ocw continuity sync-history-query --month 202604
```

基础上新增：

```bash
ocw continuity sync-history-query --all-months
```

约束：

1. `--month` 与 `--all-months` 二选一；
2. 若 `--all-months`：
   - 遍历所有月文件
   - 合并所有 events
   - 再应用现有筛选：`change_id / source_kind / sync_kind`

## 7. 返回结构

### 7.1 单月查询保持不变

继续返回：

```yaml
schema: sync-history-query/v1
month: 202604
filters: ...
summary: ...
events: ...
```

### 7.2 跨月查询

建议最小返回：

```yaml
schema: sync-history-query/v1
month: all
months:
  - 202604
  - 202605
filters:
  change_id: CHG-1
  source_kind: closeout
  sync_kind: escalation
summary:
  total_events: 8
  matched_events: 2
events: [...]
```

## 8. 行为约束

1. 月份列表与跨月查询都必须是只读动作。
2. 若无月文件：
   - 月份列表返回空列表
   - 跨月查询返回空 events payload
3. 不改变现有月文件命名与内容。
4. 聚合顺序建议按 `recorded_at` 升序。

## 9. 测试建议

至少新增：

1. `test_list_sync_history_months_returns_sorted_month_keys`
2. `test_read_sync_history_across_all_months_applies_filters`
3. `test_sync_history_months_command_supports_json_output`
4. `test_sync_history_query_command_supports_all_months_json_output`

## 10. 退出条件

1. 可列出已有月份
2. 可跨月聚合查询
3. 单月查询行为不变
4. 全量测试通过
