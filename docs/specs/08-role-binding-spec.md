# open-cowork 角色与绑定规则规格

## 1. 目标
定义抽象角色、双层角色绑定机制、有限前置审查与角色冲突约束。

## 2. 抽象角色
- Human Sponsor：发起与审批责任。
- Orchestrator：编排、边界治理、状态推进。
- Analyst / Architect：分析、澄清、方案塑形。
- Executor：按 contract 执行。
- Verifier：验证结果与缺陷分级。
- Reviewer：独立审查并给出 decision。
- Maintainer / Governance Layer：归档、stable facts、维护上下文更新。

## 3. 角色冲突规则
- 同一主体可承担多个角色，但 Executor 不得兼任最终独立 Reviewer。
- 执行层不得拥有 stable facts 最终写入权。
- Verifier 与 Reviewer 可在 Lite 下部分重合，但 Strict 下不建议重合。

## 4. 双层绑定机制
### 第一层：全局核心角色绑定
面向 change 或阶段，定义：
- sponsor
- orchestrator
- analyst/architect
- default reviewer
- default maintainer
- default executor type

### 第二层：步骤级/阶段级绑定
面向具体步骤，定义：
- step owner
- executor
- verifier
- reviewer
- approver
- gate mode
- isolation strategy

## 5. bindings.yaml 建议结构
```yaml
change_id: CHG-20260420-001
global:
  sponsor: human-sponsor
  orchestrator: orchestrator-1
  analyst: analyst-1
  default_reviewer: reviewer-1
  default_maintainer: maintainer-1
  default_executor_type: adapter
steps:
  '5':
    owner: orchestrator-1
    approver: human-sponsor
    gate: approval-required
  '6':
    owner: executor-1
    verifier: verifier-1
    gate: auto-pass
    isolation: sandbox
  '8':
    owner: reviewer-1
    approver: human-sponsor
    gate: approval-required
```

## 6. 有限前置审查
### 定义
在关键交接前，允许后续关键角色从自身职责出发做有限范围审查，以降低返工风险。

### 触发点
- Step 4 结束前
- Step 5 开始前
- 高风险 design/contract 定稿前

### 审查类型
- 可执行性审查
- 可验证性审查
- 可审计性审查
- 可维护性审查

### 边界
- 不是重新打开顶层目标争论。
- 不是把所有角色提前拉入重型同步评审。
- 只看交接可行性，不替代正式 review。

## 7. 个人域 / 团队场景差异
### 个人域
- 可由同一人承担 Sponsor + Orchestrator + Analyst。
- 仍需保留 verify/review 的结构化分离。
- 默认更强调低侵入与旁路接入。

### 团队场景
- Sponsor、Reviewer、Maintainer 通常与 Executor 分离。
- 更适合 Standard / Strict。
- 对审批痕迹与归档责任要求更高。

## 8. 阻断条件
- Step 5 未绑定角色即进入执行。
- 最终 review 由 executor 自审自批。
- stable facts 更新责任落在 executor。
