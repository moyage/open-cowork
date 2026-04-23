# open-cowork Milestone 2 Owner Transfer Continuity 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / continuity primitives` 的下一段最小能力包正式收口为：

> `owner transfer continuity`

它回答的问题不是“handoff 之后再多一份说明文档”，而是：

- 当一个 change 的 owner 需要从一个人、一个 agent、一个个人域切换到另一个时，如何把这件事变成显式、可判断、可追踪的转移行为；
- 如何区分“有人可以接手”和“接手已被正式接受”；
- 如何让后续的角色切换不只是聊天中的口头声称，而是进入 continuity 与审查链。

## 2. 设计目标

本轮目标如下：

1. 为 active change 定义一份最小但正式的 `owner transfer continuity` 结构。
2. 让所有权转移至少回答清楚：
   - 为什么要转；
   - 从谁转给谁；
   - 转的是哪个角色；
   - 是否已被接收方正式接受；
   - 当前 change 在转移时处于什么状态。
3. 让 `owner transfer continuity` 复用已经成立的 `handoff package`，而不是再造一套内容层。
4. 让 owner transfer 成为显式的审计对象，而不是隐式上下文变更。

## 3. 边界

### 3.1 本轮纳入

1. `owner transfer continuity` schema
2. 与 `handoff package` 的组合关系
3. 最小 CLI 设计
4. 最小 acceptance 语义
5. 最小测试建议

### 3.2 本轮明确不做

1. 复杂多人审批流
2. 自动通知或消息发送
3. 多轮 transfer negotiation
4. 组织级角色目录或账号系统
5. 自动修改 contract / bindings 中的正式 owner

### 3.3 但必须兼容

本轮最小结构必须为后续能力保留兼容空间：

1. role reassignment history
2. transfer rejection / fallback
3. increment package
4. closeout / archive 时的 transfer trace

## 4. 为什么它不等于 handoff package

`handoff package` 解决的是：

- 当前 change 的接手入口
- 当前状态、下一判断点、最小阅读面

`owner transfer continuity` 解决的是：

- 所有权为什么变化
- 由谁发起变化
- 由谁接受变化
- 何时正式生效

一句话说：

> `handoff package` 是交接内容层；`owner transfer continuity` 是所有权转移记录层。

所以两者关系应是：

> `owner transfer continuity = handoff package + transfer metadata + acceptance state`

## 5. 推荐方案

推荐采用：

> `single transfer record + handoff ref`

也就是：

1. owner transfer continuity 自己只承载转移语义和 acceptance 结果；
2. 当前 change 的内容层一律引用已有 `handoff-package.yaml`；
3. 不复制 handoff 摘要字段，不形成第三套状态镜像。

不推荐：

1. 把 handoff package 直接扩写成 owner transfer continuity  
   - 会把“接手入口”和“所有权转移记录”混成一个对象。
2. 让 transfer 只存在于 runtime timeline 事件中  
   - 事件能记录发生过，但不适合承载最小 acceptance 状态和后续追踪入口。

## 6. 建议结构

建议新增文件：

```text
.governance/changes/<change-id>/owner-transfer-continuity.yaml
```

它属于：

- change 目录内的 continuity 记录层
- 所有权转移的最小正式记录

它不替代：

- `handoff-package.yaml`
- `bindings.yaml`
- `manifest.yaml`
- `current-change.yaml`

## 7. 事实来源与记录规则

### 7.1 核心来源

1. `handoff-package.yaml`
2. `manifest.yaml`
3. `bindings.yaml`
4. `current-change.yaml`
5. `runtime/status/change-status.yaml`
6. `runtime/status/participants-status.yaml`

### 7.2 关键判断

owner transfer continuity 与 handoff package 不同，它不应该是纯派生对象。

原因是：

1. `transfer_reason`
2. `outgoing_owner`
3. `incoming_owner`
4. `acceptance_status`
5. `accepted_at`

这些都不是已有事实层天然存在的字段，而是一次新的显式治理记录。

因此本轮明确：

1. `owner transfer continuity` 是 continuity 层中的“记录型对象”；
2. 其中状态摘要必须引用 handoff package；
3. 其中 transfer metadata 与 acceptance metadata 由 CLI 输入并持久化。

## 8. 最小 schema

建议最小字段如下：

```yaml
schema: owner-transfer-continuity/v1
change_id: CHG-20260424-001
generated_at: 2026-04-24T12:00:00Z

transfer_context:
  transfer_reason: "session handoff"
  target_role: "reviewer"
  outgoing_owner: "reviewer-agent-a"
  incoming_owner: "reviewer-agent-b"
  initiated_by: "maintainer-agent"

state_snapshot:
  current_status: "step7-verified"
  current_step: 7
  current_phase: "Phase 3 / 执行与验证"
  human_intervention_required: true

acceptance:
  status: "pending"
  accepted_by: null
  accepted_at: null
  note: ""

effects:
  current_change_pointer_update_required: false
  bindings_update_required: true
  contract_update_required: false

refs:
  handoff_package: .governance/changes/CHG-20260424-001/handoff-package.yaml
  runtime_change_status: .governance/runtime/status/change-status.yaml
  runtime_participants_status: .governance/runtime/status/participants-status.yaml
  current_change: .governance/index/current-change.yaml
  bindings: .governance/changes/CHG-20260424-001/bindings.yaml
```

说明：

1. `state_snapshot` 是受控镜像字段，唯一用于标记“转移发生时”的 change 状态。
2. 其唯一权威来源应来自：
   - `handoff-package.yaml`
   - `runtime/status/change-status.yaml`
3. `acceptance` 是 owner transfer continuity 新增的记录层，不来自已有派生对象。
4. `effects` 只表达后续是否需要更新，不在本轮自动执行更新。

## 9. 最小生命周期

本轮建议最小生命周期只有两步：

1. `prepare`
   - 生成 `owner-transfer-continuity.yaml`
   - 记录 transfer reason / outgoing / incoming / target role
   - 默认 `acceptance.status = pending`
2. `accept`
   - 由接手方显式接受
   - 更新 `acceptance.status = accepted`
   - 记录 `accepted_by / accepted_at / note`

本轮明确不做：

1. `reject`
2. `reassign`
3. 自动回滚

## 10. 最小 CLI 设计

建议新增两条命令：

```bash
ocw continuity owner-transfer prepare \
  --change-id CHG-20260424-001 \
  --target-role reviewer \
  --outgoing-owner reviewer-agent-a \
  --incoming-owner reviewer-agent-b \
  --reason "session handoff" \
  --initiated-by maintainer-agent
```

```bash
ocw continuity owner-transfer accept \
  --change-id CHG-20260424-001 \
  --accepted-by reviewer-agent-b \
  --note "accept handoff"
```

### 10.1 命令职责

`prepare`：

1. 若 `handoff-package.yaml` 不存在，先 materialize handoff package
2. 生成 `owner-transfer-continuity.yaml`
3. 只写最小 transfer metadata 与 `pending` acceptance

`accept`：

1. 读取现有 `owner-transfer-continuity.yaml`
2. 将 `acceptance.status` 从 `pending` 更新为 `accepted`
3. 写入 `accepted_by / accepted_at / note`

### 10.2 本轮失败规则

1. `prepare` 失败条件：
   - change 不存在
   - handoff package 无法生成
   - 缺少 `target_role / outgoing_owner / incoming_owner / reason / initiated_by`
2. `accept` 失败条件：
   - transfer file 不存在
   - 当前 `acceptance.status` 不是 `pending`
   - 缺少 `accepted_by`

## 11. 与后续能力的关系

### 11.1 与 handoff package

handoff package 仍是默认阅读入口。  
owner transfer continuity 只是在其之上增加：

1. ownership transfer reason
2. transfer participants
3. acceptance status

### 11.2 与 increment package

后续 increment package 可以引用：

1. 最近一次 handoff package
2. 最近一次 owner transfer continuity

这样能看清楚：

- 状态如何接续
- owner 是否发生过变化

## 12. 最小测试建议

本轮最小测试至少覆盖：

1. `prepare` 能生成 `owner-transfer-continuity.yaml`
2. `prepare` 会自动 materialize handoff package（若不存在）
3. transfer file 不复制 handoff 摘要主体，只引用 handoff ref
4. `accept` 能把 `pending` 更新为 `accepted`
5. `accept` 不允许重复接受
6. change 不存在时应失败

## 13. 一句话结论

`owner transfer continuity` 的最小成立，不在于“让别人可读”，而在于“让所有权变化被正式记录、被正式接受、被后续 continuity 与审查链追踪”。  
