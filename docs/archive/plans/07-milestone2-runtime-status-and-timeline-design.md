# open-cowork Milestone 2 Runtime Status / Timeline 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / Workstream B` 的第一段工作正式收口为一个可实施的最小设计。

本轮只解决一个问题：

> 如何把 `Milestone 1` 已经成立的状态面与连续性能力，推进成稳定的 machine-readable 协议输出，以便被外部 agent、工具和后续展示层消费。

本设计不追求一步做到完整可视化或完整平台化，而是优先建立一层稳定、可测试、可扩展的协议输出面。

## 2. 设计目标

本轮设计目标如下：

1. 为当前 active change 提供 machine-readable runtime status 输出。
2. 为关键状态变化提供 append-only timeline 输出。
3. 保持事实层、派生状态层、展示层的边界清晰。
4. 让后续 dashboard / TUI / 外部可视化 / 多 adapter 展示能够直接复用本轮协议层，而不是重新定义状态语义。

## 3. 设计边界

### 3.1 本轮纳入

1. `.governance/runtime/status/` 最小快照层
2. `.governance/runtime/timeline/` 最小事件流层
3. `ocw runtime-status`
4. `ocw timeline`
5. 对应 schema 与测试

### 3.2 本轮明确不做

1. 图形化 dashboard
2. TUI 展示层
3. 实时监听或推送
4. 外部系统写入能力
5. 多 adapter 可视化编排
6. 面向组织级/平台级的状态汇聚服务

### 3.3 但必须保留扩展考虑

虽然以上内容本轮不做，但本轮设计必须为它们保留兼容空间，避免后续出现以下返工：

1. dashboard 需要重新解释状态字段
2. 多 adapter 接入时需要重做 participant / actor 抽象
3. timeline 无法支持更丰富的事件类型
4. TUI / 可视化壳层不得不直接解析人类阅读文档

因此，本轮的 schema、目录与 CLI 输出都必须从一开始就站在“后续可扩展消费”的角度设计。

## 4. 推荐方案

推荐采用：

> `snapshot + append-only timeline`

也就是同时建立两层输出：

1. 当前状态快照层
2. 事件时间线层

不采用以下做法：

1. 只在现有 `index/` 与 change 目录旁边零散追加 machine-readable 字段  
   - 原因：容易继续混淆导航层、事实层和派生层。
2. 一步做成 event-sourced 全驱动模型  
   - 原因：当前过重，会把 `Milestone 2` 第一段拉大。

## 5. 目录设计

建议新增：

```text
.governance/
  runtime/
    status/
      change-status.yaml
      steps-status.yaml
      participants-status.yaml
    timeline/
      events-YYYYMM.yaml
```

说明：

1. `runtime/status/` 用于保存当前快照。
2. `runtime/timeline/` 用于保存 append-only 事件流。
3. 它们都属于派生状态层，不替代 `.governance/index/`、change package 或 archive 中的事实源。

## 6. 事实来源与派生规则

本轮不新增新的事实权威层，而是从现有结构派生：

### 6.1 `change-status.yaml` 来源

来源：

1. `manifest.yaml`
2. `current-change.yaml`
3. `changes-index.yaml`
4. `maintenance-status.yaml`
5. `verify.yaml`
6. `review.yaml`
7. `archive-receipt.yaml`（如果已归档）

用途：

1. 输出 active change 的 machine-readable 当前状态
2. 输出当前 phase / step / status / gate posture
3. 输出对外只读消费所需的统一字段

### 6.2 `steps-status.yaml` 来源

来源：

1. `manifest.yaml`
2. `bindings.yaml`
3. `verify.yaml`
4. `review.yaml`
5. state consistency 结果

用途：

1. 输出 Step 1-9 当前状态
2. 输出每一步 owner / gate / human intervention 要点
3. 输出 `current_step / next_step / completed_steps / blocked_steps`

### 6.3 `participants-status.yaml` 来源

来源：

1. `bindings.yaml`
2. `manifest.roles`
3. 当前 step / status / review / verify 结果

用途：

1. 输出当前参与者视图
2. 抽象 `actor_id / actor_type / role / step / status`
3. 为后续多 agent / 多 adapter / 人工参与者展示保留统一抽象

### 6.4 `events-YYYYMM.yaml` 来源

来源不是额外人工录入，而是由关键状态落盘动作派生生成。

本轮至少纳入这些事件：

1. change 创建
2. contract validate 通过/失败
3. run 完成
4. verify 完成
5. review 完成
6. archive 完成
7. status gate 阻断暴露

## 7. Schema 设计

### 7.1 change-status schema

建议最小字段：

```yaml
schema: runtime-change-status/v1
change_id: CHG-20260424-001
phase: "Phase 3 / 执行与验证"
current_step: 7
current_status: step7-verified
overall_progress:
  completed_steps: [1, 2, 3, 4, 5, 6, 7]
  remaining_steps: [8, 9]
gate_posture:
  waiting_on: "Step 8 / Review and decide"
  next_decision: "Step 8 / Review and decide"
  human_intervention_required: true
refs:
  manifest: .governance/changes/CHG-20260424-001/manifest.yaml
  current_change: .governance/index/current-change.yaml
```

### 7.2 steps-status schema

建议最小字段：

```yaml
schema: runtime-steps-status/v1
change_id: CHG-20260424-001
steps:
  - step: 6
    label: "Execute the change"
    owner: executor-agent
    status: completed
    gate: auto-pass
  - step: 7
    label: "Verify the result"
    owner: verifier-agent
    status: completed
    gate: review-required
  - step: 8
    label: "Review and decide"
    owner: reviewer-agent
    status: waiting_gate
    gate: approval-required
```

### 7.3 participants-status schema

建议最小字段：

```yaml
schema: runtime-participants-status/v1
change_id: CHG-20260424-001
participants:
  - actor_id: executor-agent
    actor_type: agent
    role: executor
    step: 6
    status: completed
  - actor_id: verifier-agent
    actor_type: agent
    role: verifier
    step: 7
    status: completed
  - actor_id: reviewer-agent
    actor_type: agent
    role: reviewer
    step: 8
    status: waiting_input
```

### 7.4 timeline event schema

建议最小字段：

```yaml
- schema: runtime-event/v1
  event_id: EVT-20260424-001
  change_id: CHG-20260424-001
  entity_type: change
  event_type: verify_completed
  step: 7
  from_status: step6-executed-pre-step7
  to_status: step7-verified
  actor_id: verifier-agent
  timestamp: 2026-04-24T10:30:00Z
  refs:
    files:
      - .governance/changes/CHG-20260424-001/verify.yaml
```

## 8. CLI 设计

### 8.1 `ocw runtime-status`

职责：

1. 生成/刷新 `runtime/status/*.yaml`
2. 默认输出 `change-status.yaml` 的简要摘要
3. 支持外部系统只读消费

当前已落地的最小参数：

```bash
ocw runtime-status --change-id CHG-20260424-001
ocw runtime-status --change-id CHG-20260424-001 --format yaml
ocw runtime-status --change-id CHG-20260424-001 --format json
```

说明：

1. `text` 为默认输出，保持人类可读摘要行为。
2. `yaml/json` 直接输出当前 `change-status` payload，不另立新事实层。
3. `runtime-status` 当前只允许对 active change 生成和查询。

### 8.2 `ocw timeline`

职责：

1. 生成/追加 `runtime/timeline/events-YYYYMM.yaml`
2. 支持读取 active change 的关键事件列表
3. 为后续 dashboard / TUI / 外部系统保留 append-only 事件来源

当前已落地的最小参数：

```bash
ocw timeline --change-id CHG-20260424-001
ocw timeline --change-id CHG-20260424-001 --format yaml
ocw timeline --change-id CHG-20260424-001 --format json
```

说明：

1. `text` 为默认输出，保持人类可读提示。
2. `yaml/json` 直接输出当前 month timeline payload。
3. `timeline` 文件为 append-only 合并，后续同类事件会保留为独立实例。

## 9. 设计约束

### 9.1 只读消费优先

本轮所有 machine-readable 输出都默认是只读消费面，不允许外部系统直接把它们当作事实源回写。

### 9.2 不新增新的权威事实

运行时状态层必须从已有事实源派生，而不是另立一套事实权威层。

### 9.3 snapshot 与 timeline 分层

1. snapshot 负责“当前是什么”
2. timeline 负责“发生过什么”

两者不能混成一个文件。

### 9.4 为后续扩展保留抽象

本轮虽然不做 dashboard / TUI / 实时监听 / 多 adapter 展示，但字段命名与 actor 抽象必须兼容这些后续扩展。

## 10. 这轮不做但要兼容的后续扩展

为响应本轮讨论中达成的共识，本设计对以下后续方向保留兼容性：

1. dashboard / TUI  
   - 通过 `runtime/status/*.yaml` 和 `runtime/timeline/*.yaml` 直接消费
2. 多 adapter / 多 agent 展示  
   - 通过 `participants-status.yaml` 的 `actor_type / role / actor_id` 抽象兼容
3. 更丰富的事件流  
   - 通过 `runtime-event/v1` 的 `event_type / refs / entity_type` 扩展
4. 实时监听  
   - 未来可以在不改变 schema 的情况下添加文件监听或推送层

## 11. 测试建议

本轮最小测试至少覆盖：

1. 能生成 `change-status.yaml`
2. 能生成 `steps-status.yaml`
3. 能生成 `participants-status.yaml`
4. `runtime-status` 只允许 active change
5. `timeline` 不覆盖已有月度事件
6. `timeline` 事件优先绑定真实源文件时间戳
7. 同类事件多次发生时能够保留多次实例
8. `runtime-status` 与 `timeline` 支持 `text / yaml / json` 查询输出

## 12. 当前实现对齐状态

截至当前 `Workstream B` 分支，这份设计已经形成以下已落地能力：

1. `runtime/status/` 三份 machine-readable 快照
   - `change-status.yaml`
   - `steps-status.yaml`
   - `participants-status.yaml`
2. `steps-status.yaml` 已显式输出：
   - `current_step`
   - `next_step`
   - `completed_steps`
   - `blocked_steps`
3. `runtime/timeline/` 已具备 append-only 月度事件流
4. 当前已落地事件类型：
   - `change_created`
   - `contract_validate_pass`
   - `contract_validate_fail`
   - `run_completed`
   - `verify_completed`
   - `review_completed`
   - `archive_completed`
   - `gate_blocked`
5. 同类事件已按实例级 `event_id` 保留，不再压成单条摘要
6. 查询输出层已支持：
   - `--format text`
   - `--format yaml`
   - `--format json`

一句话说，这一段已不再是“设计草案”，而是“已落地的最小协议切片”。
3. 能生成 `participants-status.yaml`
4. 能生成/追加 `events-YYYYMM.yaml`
5. 当前状态字段与现有 `manifest/current-change/index` 对齐
6. timeline 至少包含 `run/verify/review/archive` 等关键事件

## 12. 一句话结论

`Milestone 2 / Workstream B` 的第一步，不是做展示层，而是先把展示层、外部系统和后续多 agent 协作都可以稳定消费的 machine-readable 协议输出面建立起来。
