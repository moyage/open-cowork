# open-cowork Milestone 2 Continuity / Sync Digest 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2` 下一段最小工作包正式收口为：

> `continuity / sync digest`

上一轮我们已经有了：

1. continuity primitives：
   - `handoff-package`
   - `owner-transfer-continuity`
   - `increment-package`
   - `closeout-packet`
   - `sync-packet`
2. runtime 状态与 timeline
3. `sync-history` 的：
   - append
   - 单月查询
   - 月份列表
   - 跨月聚合查询

但从“人和团队的默认阅读入口”看，仍然有一个明显缺口：

- 现在的信息都在，但人要自己决定先看哪个 packet；
- 当前 active change 与最近 archived change 的“默认阅读入口”还没有统一摘要层；
- 上层 agent 要快速理解当前 continuity / sync 状态，也需要一个更短、更聚焦的入口。

本轮要做的，就是给这条 continuity / sync 主线补一个轻量 `digest`。

## 2. 设计目标

1. 新增一个单独的只读入口：`continuity digest`。
2. 为一个目标 change 输出最小人类摘要与结构化摘要。
3. 默认选择策略：
   - 若有 current active change，则摘要它；
   - 否则摘要最近 archived change。
4. 不新增任何 truth-source。
5. 只复用现有：
   - runtime status
   - handoff / increment / owner-transfer
   - closeout / sync packet
   - maintenance-status

## 3. 边界

### 3.1 本轮纳入

1. `resolve_continuity_digest(...)`
2. `ocw continuity digest`
3. `text / yaml / json` 输出
4. 当前 active / 最近 archived 的自动选择逻辑
5. 最小测试覆盖

### 3.2 本轮不纳入

1. dashboard / TUI
2. 实时刷新
3. 多 change 批量 digest
4. 跨项目 digest
5. 复杂统计与趋势分析

## 4. 推荐方案

推荐采用：

> `single digest command + target auto-selection + derived reading summary`

也就是：

1. 单独提供 `continuity digest`
2. 默认自动选择目标 change
3. 只输出：
   - 当前最重要状态
   - 当前最推荐先读的对象
   - 当前下一关注点
   - 关键 refs

不推荐：

1. 把 digest 塞进 `status` 或 `sync-history-query`
   - 会让现有命令职责变混。
2. 一上来做重的 dashboard
   - 现在太重，而且会把本轮从协议层拉向产品壳层。

## 5. 目标选择规则

### 5.1 显式 change_id

若 CLI 提供 `--change-id`，则直接摘要该 change。

### 5.2 默认回退顺序

若未提供 `--change-id`：

1. 先读取 `current-change.yaml`
2. 若当前存在 active change，则摘要它
3. 否则读取 `maintenance-status.last_archived_change`
4. 若存在最近 archived change，则摘要它
5. 若两者都没有，则报错

## 6. digest 结构

建议最小结构：

```yaml
schema: continuity-digest/v1
change_id: CHG-20260424-001
digest_kind: active
selected_by: current-change
summary:
  title: "当前 change 标题"
  status: step7-verified
  phase: 执行与验证
  step: 7
  headline: "当前正在等待 review decision"
  next_attention: "Step 8 / Review and decide"
  human_intervention_required: true
recommended_reading:
  primary_ref: .governance/changes/CHG-.../handoff-package.yaml
  secondary_refs:
    - .governance/changes/CHG-.../increment-package.yaml
    - .governance/runtime/status/change-status.yaml
sync_view:
  latest_sync_kind: escalation
  latest_sync_headline: "需要更高层同步"
  latest_target_layer: sponsor
refs:
  handoff_package: ...
  increment_package: ...
  owner_transfer: ...
  closeout_packet: ...
  sync_packet: ...
```

### 6.1 active change

优先信息来源：

1. `runtime/status/change-status.yaml`
2. `handoff-package.yaml`
3. `increment-package.yaml`
4. `owner-transfer-continuity.yaml`（存在时）

### 6.2 archived change

优先信息来源：

1. `closeout-packet.yaml`
2. `sync-packet.yaml`（若 source=closeout）
3. `maintenance-status`

## 7. recommended_reading 规则

### 7.1 active

active change 的 `primary_ref` 优先顺序：

1. `handoff-package`
2. 否则 `increment-package`
3. 否则 `runtime/status/change-status.yaml`

### 7.2 archived

archived change 的 `primary_ref` 优先顺序：

1. `closeout-packet`
2. 否则 archived `review.yaml`
3. 否则 archived `manifest.yaml`

## 8. sync_view 规则

1. 若对应 `sync-packet` 存在，则摘要：
   - `sync_kind`
   - `headline`
   - `target_layer`
2. 若不存在，则整体省略 `sync_view`

## 9. CLI 设计

建议新增：

```bash
ocw continuity digest [--change-id CHG-...] [--format text|yaml|json]
```

默认 `text` 输出示例：

```text
Continuity digest: CHG-20260424-001 (active)
status: step7-verified / 执行与验证 / step 7
headline: 当前正在等待 review decision
next attention: Step 8 / Review and decide
recommended reading: .governance/changes/CHG-.../handoff-package.yaml
sync: escalation -> sponsor / 需要更高层同步
```

## 10. 测试建议

至少新增：

1. `test_resolve_continuity_digest_prefers_current_active_change`
2. `test_resolve_continuity_digest_falls_back_to_last_archived_change`
3. `test_continuity_digest_command_supports_json_output`
4. `test_continuity_digest_command_supports_text_output`

## 11. 退出条件

1. 可对 active change 生成 digest
2. 可对 archived change 生成 digest
3. 未传 `change_id` 时自动选择正常
4. `text / yaml / json` 输出可用
5. 全量测试通过
