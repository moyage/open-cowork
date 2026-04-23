# open-cowork Milestone 2 Handoff Package 设计

## 1. 文档目的

本设计文档用于把 `Milestone 2 / continuity primitives` 的下一段最小能力包正式收口为：

> `handoff package`

它回答的问题不是“再多一份 continuity 文档”，而是：

- 当一个 change 正在推进中，如何给另一个人、另一个 agent、另一个个人域一个低摩擦、低歧义、可直接接手的交接包；
- 如何让交接不依赖完整聊天回放；
- 如何让后续 `owner transfer continuity` 与 `increment package` 复用同一套底层结构。

## 2. 设计目标

本轮目标如下：

1. 为 active change 定义一份最小但正式的 `handoff package` 结构。
2. 让接手方能用最少阅读面理解：
   - 当前在做什么；
   - 已推进到哪里；
   - 当前卡在哪里；
   - 下一步该做什么；
   - 哪些地方必须人工判断。
3. 让这份交接包成为：
   - `owner transfer continuity` 的直接底座；
   - `increment package` 的上游输入之一；
   - 人类默认阅读入口的一部分。
4. 保持 handoff package 只是派生交接层，而不是新的 truth-source。

## 3. 边界

### 3.1 本轮纳入

1. `handoff package` schema
2. 对应的派生规则
3. 最小 CLI 入口设计
4. 与现有 continuity / runtime status / timeline 的衔接规则
5. 最小测试建议

### 3.2 本轮明确不做

1. 完整 `owner transfer continuity`
2. 完整 `increment package`
3. 复杂多人审批流
4. 自动通知或消息分发
5. 组织级交接看板

### 3.3 但必须兼容

本轮 handoff package 必须为后续能力保留兼容空间：

1. `owner transfer continuity`
2. `increment package`
3. closeout / close-loop 阅读入口
4. 外部 agent / 外部只读系统直接消费

## 4. 为什么先做 handoff package

在 continuity primitives 中，`handoff package` 是最适合作为下一段最小能力包的对象，原因有三：

1. 它直接服务多人/多 agent 接力，是 continuity 的核心现实场景。
2. 它能复用现有已落地结构：
   - `continuity launch-input`
   - `round-entry-summary`
   - `runtime/status`
   - `runtime/timeline`
3. 它可以作为：
   - `owner transfer continuity` 的“交接内容层”
   - `increment package` 的“阶段状态层”

一句话说：

> 先把 handoff package 做稳，后面两项 continuity primitive 会更容易标准化。

## 5. 推荐方案

推荐采用：

> `single handoff packet + layered refs`

也就是：

1. 输出一份单一的 handoff package
2. 这份 package 自己只承载最小必需摘要
3. 其余内容通过明确 refs 指向已有 authoritative / machine-readable artifacts

不推荐：

1. 直接把现有 `continuity launch-input` 继续做大  
   - 会把启动输入、接手输入、轮次接续输入混成一个对象。
2. 直接复制大量 markdown / yaml 进 handoff package  
   - 会造成交接层和事实层重复、漂移、维护成本上升。

## 6. 建议结构

建议新增文件：

```text
.governance/changes/<change-id>/handoff-package.yaml
```

它属于：

- change 目录内的派生交接层
- 面向接手方的单一入口

它不替代：

- `manifest.yaml`
- `contract.yaml`
- `verify.yaml`
- `review.yaml`
- `runtime/status/*.yaml`
- `runtime/timeline/events-YYYYMM.yaml`

## 7. 事实来源与派生规则

handoff package 不新增事实权威层，而是从已有结构派生：

### 7.1 核心来源

1. `manifest.yaml`
2. `contract.yaml`
3. `bindings.yaml`
4. `current-change.yaml`
5. `runtime/status/change-status.yaml`
6. `runtime/status/steps-status.yaml`
7. `runtime/status/participants-status.yaml`
8. `review.yaml / verify.yaml`（存在时）

### 7.2 可选增强来源

以下来源不属于 handoff package 的最小成立条件，但在存在时应被复用：

1. `continuity-launch-input.yaml`
2. `ROUND_ENTRY_INPUT_SUMMARY.yaml`
3. `runtime/timeline/events-YYYYMM.yaml`

### 7.3 生成原则

1. handoff package 必须是派生摘要层。
2. 所有结论必须能回指到明确 refs。
3. 如果同类信息已存在于 `runtime/status`，不得再造一套平行字段语义。
4. 如果 `continuity launch-input` 已提供 carry-forward 视角，handoff package 只做面向接手的压缩表达。

### 7.4 最小成立条件

handoff package 的最小成立条件应尽量低，避免它变成“只有流程跑到较后阶段才能使用”的能力。

本轮明确约定：

1. 只要目标 change 存在，且能读取其最小 authoritative facts，handoff package 就应可生成。
2. handoff package 的最小成立不依赖：
   - `predecessor_change`
   - `continuity-launch-input.yaml`
   - `ROUND_ENTRY_INPUT_SUMMARY.yaml`
   - `verify.yaml`
   - `review.yaml`
3. `carry_forward` 视角属于可选增强层，而不是强制字段。
4. 如果当前 active change 尚未显式 materialize `runtime/status/*.yaml`，命令可以先按当前 authoritative state 派生并落盘 runtime status，再继续生成 handoff package。
5. 只有在以下情况才应失败：
   - 未提供 `change_id` 且不存在 current change
   - 指定 change 不存在
   - 最小 authoritative inputs 缺失到无法识别当前 change 的基础状态

## 8. 最小 schema

建议最小字段如下：

```yaml
schema: handoff-package/v1
change_id: CHG-20260424-001
handoff_kind: active-change
generated_at: 2026-04-24T12:00:00Z

summary:
  project_summary: "当前 change 的目标摘要"
  current_phase: "Phase 3 / 执行与验证"
  current_step: 7
  current_status: "step7-verified"
  current_owner: "verifier-agent"
  waiting_on: "Step 8 / Review and decide"
  next_decision: "Step 8 / Review and decide"

handoff_need:
  handoff_reason: "session handoff"
  intended_receiver_type: "agent"
  intended_receiver_role: "reviewer"
  human_intervention_required: true

execution_context:
  target_validation_objects:
    - RuntimeStatusSchema
  active_roles:
    executor: executor-agent
    verifier: verifier-agent
    reviewer: reviewer-agent
  current_gate: "review-required"

operator_start_pack:
  - .governance/changes/CHG-20260424-001/manifest.yaml
  - .governance/changes/CHG-20260424-001/contract.yaml
  - .governance/changes/CHG-20260424-001/tasks.md
  - .governance/changes/CHG-20260424-001/bindings.yaml

carry_forward:
  predecessor_change: CHG-20260420-001
  carry_forward_refs:
    - .governance/changes/CHG-20260424-001/continuity-launch-input.yaml
    - .governance/changes/CHG-20260424-001/ROUND_ENTRY_INPUT_SUMMARY.yaml

refs:
  runtime_change_status: .governance/runtime/status/change-status.yaml
  runtime_steps_status: .governance/runtime/status/steps-status.yaml
  runtime_participants_status: .governance/runtime/status/participants-status.yaml
  verify: .governance/changes/CHG-20260424-001/verify.yaml
  review: .governance/changes/CHG-20260424-001/review.yaml
```

说明：

1. `summary.current_phase/current_step/current_status/current_owner/waiting_on/next_decision` 是受控镜像字段，不是新的权威状态层。
2. 这些字段的唯一权威来源应分别来自：
   - `runtime/status/change-status.yaml`
   - `runtime/status/steps-status.yaml`
   - `runtime/status/participants-status.yaml`
3. `execution_context.active_roles/current_gate` 也是面向接手方的压缩表达，其底层来源同样应回指到 `runtime/status` 与 change 内已有 contract/bindings。
4. `carry_forward` 整段为可选字段：
   - 当存在 predecessor baseline 与 continuity 文件时写入；
   - 当不存在时应整体省略，而不是生成空占位结构。

## 9. 核心语义

### 9.1 handoff package 是“接手入口”

它的作用不是替代所有原始文件，而是让接手方快速完成三个动作：

1. 判断当前 change 在哪里；
2. 判断我是否就是下一步的合适接手者；
3. 找到下一步所需的最小 authoritative 输入集合。

### 9.2 handoff package 是“中间态交接物”

它主要面向：

1. session 中断后的恢复
2. 同一 change 在不同 agent 间切换
3. 人接人 / 人接 agent / agent 接人的交接

它不是：

1. round closeout package
2. archive 后的最终收束包
3. 组织级项目周报

### 9.3 handoff package 与 round-entry 的区别

`continuity launch-input` 和 `round-entry-summary` 偏向：

- 新一轮启动前的输入压缩
- carry-forward 基线

`handoff package` 偏向：

- 当前 change 正在推进时的接手
- 当前状态、当前阻塞、当前判断点

所以三者关系应是：

1. `launch-input`：上一轮到这一轮的 continuity
2. `round-entry-summary`：新一轮最小阅读面
3. `handoff-package`：本轮进行中的接手入口

## 10. 最小 CLI 设计

建议新增：

```bash
ocw continuity handoff-package --change-id CHG-20260424-001
```

职责：

1. 生成 `.governance/changes/<change-id>/handoff-package.yaml`
2. 默认输出文件路径
3. 后续可考虑支持：
   - `--format yaml`
   - `--format json`

本轮建议先只落最小生成能力，不急着一开始就做更复杂的格式选项。

### 10.1 依赖缺失时的行为

为了让 handoff package 真正服务“进行中的接手”，命令行为需要明确：

1. 如果 `runtime/status/*.yaml` 尚未生成：
   - 命令应先从当前 authoritative state materialize 最小 runtime status；
   - 然后再生成 handoff package。
2. 如果 `verify.yaml` 或 `review.yaml` 不存在：
   - 不应失败；
   - 只是不写入对应 refs。
3. 如果 `continuity-launch-input.yaml` / `ROUND_ENTRY_INPUT_SUMMARY.yaml` 不存在，或 change 没有 predecessor baseline：
   - 不应失败；
   - 只是不写入 `carry_forward`。
4. 如果当前 change 仍处在较早阶段：
   - handoff package 仍应生成；
   - 其 `waiting_on / next_decision / current_gate` 由当前 runtime status 派生。
5. 只有最小 authoritative state 无法识别时，命令才应失败并返回明确错误。

## 11. 与后续能力的关系

### 11.1 与 owner transfer continuity

后续 `owner transfer continuity` 可在 handoff package 之上补：

1. transfer reason
2. outgoing owner
3. incoming owner
4. transfer acceptance
5. transfer timestamp

也就是说：

> `owner transfer continuity = handoff package + owner transfer metadata`

### 11.2 与 increment package

后续 `increment package` 可复用 handoff package 中的：

1. 当前状态摘要
2. 当前阻塞
3. 下一判断点
4. carry-forward refs

也就是说：

> `increment package = handoff package + 本段新增结论/失效假设/新增风险`

## 12. 测试建议

本轮最小测试至少覆盖：

1. 能生成 `handoff-package.yaml`
2. handoff package 只引用现有事实层，不自造平行 truth-source
3. 能正确带出：
   - `current_phase`
   - `current_step`
   - `current_status`
   - `current_owner`
   - `waiting_on`
   - `next_decision`
4. 能带出最小 `operator_start_pack`
5. 存在 continuity 输入时，能带出 `carry_forward_refs`
6. 不存在 predecessor baseline 时，仍能生成不含 `carry_forward` 的 handoff package
7. `runtime/status` 未预生成时，命令可先 materialize 再生成
8. active change 不存在时应失败

## 13. 一句话结论

`handoff package` 是 continuity primitives 最适合作为下一段最小能力包的对象，因为它既直接服务多人/多 agent 接力，又能成为 `owner transfer continuity` 和 `increment package` 的共同底座。
