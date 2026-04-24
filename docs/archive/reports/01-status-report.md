# open-cowork 状态报告（Milestone 1 已成立，Milestone 2 已进入收口阶段）

## 1. 当前总体判断

截至当前主线，`open-cowork` 已经不再只是“有顶层定义的框架草案”，而是已经形成了一条可运行、可验证、可交接、可同步、可查询的项目级复杂协作协议基线。

如果按本轮 `Milestone 1 + Milestone 2` 的实际推进结果看，当前状态可以概括为：

1. `Milestone 1` 已完整成立  
   - 主链闭环成立  
   - 最小边界硬化成立  
   - 最小 continuity 成立  
   - 最小人类状态面成立
2. `Milestone 2` 的核心子线已经大面积落地  
   - 边界与状态硬化第二轮已落地  
   - continuity primitives 已形成完整最小链  
   - machine-readable runtime / timeline 协议层已落地  
   - sync / closeout / export / query / digest 的最小读写消费面已落地
3. 当前阶段不再主要缺“新主链能力”，而主要进入“收口、对齐、压缩默认阅读入口”的阶段。

## 2. 已完成能力

### 2.1 Milestone 1：复杂协作闭环主链

已实现：

1. `change create`
2. `contract validate`
3. `run`
4. `verify`
5. `review`
6. `archive`

并且以下最小约束已经成立：

1. `review` 需要 `verify=pass`
2. `archive` 需要 `review=approve`
3. `verify / review / archive` 状态迁移门已存在
4. `executor / verifier / reviewer` 最小分离已存在

### 2.2 Milestone 1：最小状态面与诊断恢复

已实现：

1. `status` 默认 4 阶段视图
2. `STATUS_SNAPSHOT.yaml`
3. `diagnose-session`
4. `session-recovery-packet`
5. 会话压缩 / 断连诊断与恢复包机制

默认状态面当前已可见：

1. `current_phase`
2. `current_owner`
3. `waiting_on`
4. `next_decision`
5. `project_summary`

## 3. Milestone 2 已完成能力

### 3.1 边界与状态硬化

已实现：

1. `.governance/index/**` 治理保留区阻断
2. `.governance/runtime/**` 治理保留区阻断
3. `.governance/archive/**` 治理保留区阻断
4. `.governance/changes/**` 包体保留区阻断
5. `current-change / changes-index` 最小不可回退保护
6. `maintenance-status` 最小不可回退保护
7. `archive-map` 与 `maintenance-status` 最近归档锚点一致性
8. archived continuity refs 与 `archive-map / archive-receipt` 一致性
9. continuity / closeout / sync refs 的存在性与目标匹配约束

### 3.2 runtime / timeline 协议层

已实现：

1. `runtime-status`
2. `timeline`
3. `change-status.yaml`
4. `steps-status.yaml`
5. `participants-status.yaml`
6. 月度 append-only `events-YYYYMM.yaml`
7. 关键动作事件落盘：
   - `contract_validate_pass`
   - `contract_validate_fail`
   - `run_completed`
   - `verify_completed`
   - `review_completed`
   - `archive_completed`
   - `gate_blocked`
8. 查询输出支持：
   - `text`
   - `yaml`
   - `json`
9. `runtime/status` 与 `timeline` 的 `projection_sources`

### 3.3 continuity primitives

已实现：

1. `continuity launch-input`
2. `round-entry-summary`
3. `handoff-package`
4. `owner-transfer-continuity`
5. `increment-package`
6. `closeout-packet`
7. `sync-packet`

### 3.4 sync / export / history / digest

已实现：

1. `sync-history`
2. `export-sync-packet`
3. `sync-history-query`
4. `sync-history-months`
5. `sync-history-query --all-months`
6. `sync-history-query --summary-by ...`
7. `sync-history-query --summary-only`
8. grouped summary 支持：
   - `change_id`
   - `source_kind`
   - `sync_kind`
   - `target_layer`
9. grouped summary 已带：
   - `event_count`
   - `distinct_change_count`
   - `latest_headline`
   - `latest_change_id`
   - `latest_sync_kind`
10. `continuity digest`
11. `digest` 中的：
   - `recent_sync_summary`
   - `recent_runtime_events`
   - `projection_sources`

## 4. 当前验证状态

当前主线完整测试结果：

- `124/124` 通过

这意味着当前主线已经具备：

1. 一个可运行的复杂协作闭环
2. 一个可读取的 runtime / timeline 协议层
3. 一组可接续、可转移、可收束、可同步的 continuity primitives
4. 一层正在收口中的人类默认阅读入口

## 5. 当前仍未收口的部分

如果严格按“本轮最终收口”来看，当前剩余项已经不多，且不应再扩成新主线。

仍建议完成的事项主要是这 3 类：

1. 状态与计划口径收口  
   - 把当前主线进展同步到公开状态报告与 closeout 摘要
2. 本轮迭代收束文档  
   - 明确当前轮哪些已完成、哪些留待下一轮
3. 非扩张式阅读层小压缩  
   - 只允许在现有 `digest / sync-history / query` 上继续做很小的摘要压缩

## 6. 当前不建议再做的事

为了遵守本轮 `Milestone 1 / Milestone 2` 边界，当前不建议继续扩张到以下方向：

1. 新的协议对象
2. 新的 adapter 生态面
3. 平台化 UI / Dashboard / TUI
4. 生态级治理与项目组合层
5. 重型企业控制台

## 7. 一句话结论

当前 `open-cowork` 已经完成了本轮最重要的目标：  
它不再只是一个“复杂协作框架概念”，而已经成为一个具备闭环、约束、交接、同步、查询和轻量摘要入口的项目级复杂协作协议基线。

接下来的重点不是“继续长更多对象”，而是把这轮已经长出来的协议面和阅读面稳稳收口。
