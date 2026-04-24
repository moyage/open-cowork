# open-cowork Milestone 2 Digest Recent Runtime Events 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> 在 `continuity digest` 中补一段最近关键运行事件压缩视图。

上一轮我们已经具备：

1. `recent_sync_summary`
2. `projection_sources`

但从人和团队的默认阅读入口看，还缺一个很实用的层：

- 现在 digest 能告诉我们当前状态与最近同步；
- 但还不能快速告诉我们“最近这轮实际发生了什么关键运行动作”，比如：
  - 最近是否完成 verify
  - 最近是否被 review 卡住
  - 最近是否 archive 完成

本轮要做的，就是把 runtime timeline 压成一个很薄的最近事件摘要，不扩命令面，不扩事实层。

## 2. 设计目标

1. 在 `digest` 中增加 `recent_runtime_events`
2. 默认只保留最近 3 条与当前 change 相关的关键事件
3. 不新增新的 truth-source 文件
4. 不新增新的查询命令

## 3. 边界

### 3.1 本轮纳入

1. `resolve_continuity_digest(...)` 增补 `recent_runtime_events`
2. `continuity digest --format text` 输出最近关键事件压缩行
3. 最小测试覆盖

### 3.2 本轮不纳入

1. 独立 runtime events summary 命令
2. 跨月 timeline 历史回放
3. 图形化事件流
4. 批量多 change 压缩视图

## 4. 推荐方案

推荐采用：

> `digest embeds latest runtime event list`

也就是：

1. 复用已有 `.governance/runtime/timeline/events-YYYYMM.yaml`
2. 只按当前 digest 的 `change_id` 过滤
3. 保留最近 3 条
4. 不输出完整事件对象，只输出最关键字段

## 5. 建议结构

```yaml
recent_runtime_events:
  - event_type: review_completed
    step: 8
    to_status: review-approved
    timestamp: 2026-04-24T12:00:00Z
  - event_type: verify_completed
    step: 7
    to_status: step7-verified
    timestamp: 2026-04-24T11:30:00Z
```

## 6. 生成规则

1. 只读取当前月份的 runtime timeline 文件
2. 只保留当前 `change_id` 的事件
3. 按 `timestamp` 升序后取最后 3 条
4. 若当前没有 timeline 文件或没有匹配事件，则整体省略 `recent_runtime_events`

## 7. 文本输出

在 `continuity digest --format text` 基础上增加：

```text
recent events:
- review_completed -> review-approved
- verify_completed -> step7-verified
```

没有事件时不输出这段。

## 8. 测试建议

至少新增：

1. `test_resolve_continuity_digest_includes_recent_runtime_events_when_timeline_exists`
2. `test_continuity_digest_text_output_includes_recent_runtime_events`

## 9. 退出条件

1. digest 在存在 runtime timeline 时能输出最近事件摘要
2. 没有 timeline 时保持静默省略
3. 全量测试通过
