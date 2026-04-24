# open-cowork Milestone 2 Sync History Query 设计

## 1. 文档目的

本设计文档用于把 `sync-history` 从“只会 append”推进到“可读、可筛选、可结构化消费”的最小查询层。

当前我们已经有：

1. `sync-packet`
2. `append_sync_history(...)`
3. `export_sync_packet(...)`

这意味着：

- sync 历史已经能被写入；
- 但外部消费方、人、agent 仍缺一个稳定的读取入口；
- 现在如果要消费历史，只能直接读取 `.governance/runtime/sync-history/events-YYYYMM.yaml` 原文件。

本轮要做的，就是在不改动现有 append 语义的前提下，补一个最小只读查询层。

## 2. 设计目标

本轮目标如下：

1. 保持现有 `ocw continuity sync-history` 作为 append 入口不变。
2. 新增一个只读查询入口。
3. 支持最小筛选：
   - month
   - change_id
   - source_kind
   - sync_kind
4. 支持结构化输出：
   - text
   - yaml
   - json
5. 不引入新的 truth-source，只读取现有 `sync-history` 月度文件。

## 3. 边界

### 3.1 本轮纳入

1. `read_sync_history(...)` 或等价只读 helper
2. 新 CLI：`ocw continuity sync-history-query`
3. 结构化输出与最小筛选
4. 对应测试与 Baseline 同步

### 3.2 本轮不纳入

1. 历史跨月聚合
2. 排序规则自定义
3. 全文搜索
4. UI / dashboard
5. 自动上层推送

## 4. 推荐方案

推荐采用：

> `append path unchanged + separate read-only query entry`

也就是：

1. 保留现有：
   - `ocw continuity sync-history --change-id ... --source-kind ...`
2. 新增：
   - `ocw continuity sync-history-query --month ... --format ...`

为什么不把 query 混进现有命令：

1. 现有 `sync-history` 已经承担“写动作”语义；
2. 若继续塞查询模式，命令语义会混杂；
3. 分出只读入口，后续更适合上层只读系统、agent、脚本调用。

## 5. 查询对象与返回结构

查询来源：

```text
.governance/runtime/sync-history/events-YYYYMM.yaml
```

建议最小返回对象：

```yaml
schema: sync-history-query/v1
month: 202604
filters:
  change_id: CHG-20260424-001
  source_kind: closeout
  sync_kind: escalation
summary:
  total_events: 8
  matched_events: 2
events:
  - event_id: CHG-20260424-001-sync-20260424T120000Z
    change_id: CHG-20260424-001
    recorded_at: 2026-04-24T12:00:00Z
    sync_kind: escalation
    source_kind: closeout
    target_layer: sponsor
    target_scope: project-level
    packet_ref: .governance/archive/CHG-20260424-001/sync-packet.yaml
    headline: 需要更高层同步
```

说明：

1. `total_events` 表示该月全部事件数；
2. `matched_events` 表示筛选后剩余事件数；
3. `events` 保持和历史原对象同形，避免新造平行 schema。

## 6. 筛选规则

### 6.1 month

1. 必填，格式 `YYYYMM`
2. 直接对应月度文件名

### 6.2 change_id

1. 可选
2. 仅保留 `event.change_id == change_id`

### 6.3 source_kind

1. 可选
2. 仅保留 `event.source_kind == source_kind`

### 6.4 sync_kind

1. 可选
2. 仅保留 `event.sync_kind == sync_kind`

## 7. 行为约束

1. 查询是只读动作，不得 materialize 新文件。
2. 若月度文件不存在：
   - 返回空 events payload；
   - 不视为错误。
3. `yaml/json` 输出应直接打印结构化对象。
4. `text` 输出应提供：
   - month
   - filters
   - matched count
   - 每条事件的最小摘要行

## 8. 最小 CLI 设计

建议新增：

```bash
ocw continuity sync-history-query \
  --month 202604 \
  --change-id CHG-20260424-001 \
  --source-kind closeout \
  --sync-kind escalation \
  --format json
```

其中：

1. `--month` 必填
2. `--format text|yaml|json`，默认 `text`
3. 其余筛选项可选

## 9. 测试建议

至少新增：

1. `test_read_sync_history_returns_empty_payload_when_month_missing`
2. `test_read_sync_history_filters_by_change_id_and_source_kind`
3. `test_sync_history_query_command_supports_json_output`
4. `test_sync_history_query_command_supports_text_output`

## 10. 退出条件

1. append 入口不变
2. 新增只读 query 入口
3. 支持最小筛选与结构化输出
4. 全量测试通过
