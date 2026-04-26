# V0.3.0 Step 3 方案塑形报告

Change: `v0.3-human-participation-closeout-readability`
Step: `3 / 方案塑形`
Status: `revised-for-hermes-rereview`
Owner: `architect-agent`

本文是 V0.3.0 标准 9 步运行流程的 Step 3 方案塑形报告。它承接 Step 2 已确认的目标、范围、非目标、优先级、验收标准和复杂度档位，用于形成设计基线与方案方向。它不是 Step 4 变更包组装，也不是 Step 5 执行准备，更不是 Step 6 实现执行。

## 1. Step 3 目标

形成 V0.3.0 的设计基线，说明如何修复当前流程语义混乱、人类参与不足、步骤边界不清、状态与报告可读性不足、审计链分散等问题。

Step 3 只回答“准备怎么做”和“设计边界是什么”，不直接修改实现代码。

## 2. 设计原则

### 2.1 以标准 Step 号作为唯一流程状态

open-cowork 的规范生命周期只有标准 9 步运行流程。传统人视角阶段映射只能作为解释层，例如“Step 3 对应架构 / 方案设计”，不能替代 Step 号，也不能成为新的流程状态。

### 2.2 先固化标准流程，再优化体验

任何 human-facing 输出、模板、report、handoff 都必须建立在标准 9 步之上，而不是引入新的影子流程名。

### 2.3 prepare-state 与 standard step-state 分离

`ocw change prepare` 可以创建材料，但不能把状态投影为 Step 1-5 已完成。

设计方向：

- prepare 输出说明“已生成进入 Step 1 前的输入材料 / change package draft”。
- Step 4 会基于已有 draft artifacts 进行 reconcile / finalize，不把 pre-step draft 视为已完成 Step 4。
- status/current-state 不应把 prepare 结果显示为 completed steps。
- Step 1-5 的完成必须来自对应 step report、gate 或人类确认记录。

### 2.4 每一步都必须边界清晰

标准 9 步每一步都应明确：

- 输入
- 输出
- owner
- gate_type
- gate_state
- 完结动作
- 下一步进入条件
- human decision / review requirement

Step 1/2 的边界清晰只是第一处修复点，V0.3.0 要把这个模型推广到 Step 1-9。

### 2.5 人类主界面不是 CLI 命令

CLI 仍是 Agent 内部工具。给人的默认界面应是：

- 当前标准 Step
- 传统映射说明
- 本步目标
- owner 和参与者
- 输入与输出
- 框架强制了什么
- Agent 已做什么 / 接下来预计做什么
- 阻断和风险
- 需要人确认的问题
- 下一步进入条件

## 3. Canonical Step Boundary Table

以下表格是 Step 4 组装 change package 时必须采用的边界基线。

| Step | 标准名称 | 传统映射 | 主要输入 | 主要输出 | Owner | gate_type | 完结动作 | 下一步进入条件 | 人类决策 / review 要求 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 输入接入与问题定界 | 需求接收与澄清 | 原始需求、参考资料、约束、历史反馈 | framed input、初始约束池、问题范围 | Human Sponsor / Orchestrator | review-required | Human sponsor review 并确认输入来源、问题边界、约束池 | Step 2 可基于 framed input 定义目标与范围 | 需要 review；确认不是 scope approval |
| 2 | 意图澄清与范围定义 | 需求接收与澄清 | Step 1 输出 | 目标、边界、非目标、复杂度档位、验收标准 | Analyst / Architect | approval-required | Human sponsor approval 目标、范围、非目标、优先级、复杂度 | Step 3 可基于确认范围塑形方案 | 需要 approval |
| 3 | 方案塑形 | 架构 / 方案设计 | Step 2 输出、参考分析、约束池 | design baseline、能力边界、方案方向、测试策略 | Analyst / Architect | review-required | Human sponsor 或 reviewer review 设计基线 | Step 4 可基于确认设计组装 change package | 需要 review；不是执行 approval |
| 4 | 变更包组装 | 实施包准备与角色分工 | Step 3 输出、已有 draft artifacts | change package 初稿、交付清单、contract 草案、tasks 草案 | Orchestrator | review-required | Review change package 是否可执行、可验证、可审计 | Step 5 可绑定角色、gate、isolation 和最终 contract | 需要 review |
| 5 | 角色绑定与执行准备 | 实施包准备与角色分工 | change package 初稿、contract 草案、bindings 草案 | final bindings、gate policy、isolation strategy、contract ready | Human Sponsor / Orchestrator | approval-required | Human sponsor approval 执行准备 | Step 6 可以在 contract 内隔离执行 | 需要 approval；这是进入执行的门 |
| 6 | 隔离执行 | 受控开发 / 执行 | final contract、bindings、scope_in、Step 5 approval | 目标产物、execution evidence、changed files manifest | Executor | auto-pass-to-step7 | Executor 完成受控执行并记录 evidence | Step 7 可基于 evidence 验证 | 不需要 approval；不得自批 review |
| 7 | 验证与纠偏 | 测试验证 | 产物、evidence、验证计划 | verify result、issues、修正建议 | Verifier | review-required | Verifier review 结果并分级问题 | Step 8 可基于 verify/evidence 做 decision | 需要 review；不是 final approval |
| 8 | 审查与决策 | 评审验收 | verify result、evidence、change package、顶层约束 | approve / revise / reject decision | Reviewer / Sponsor | approval-required | Independent reviewer decision，必要时 human sponsor approval | Step 9 可在 approve 后归档 | 需要 approval；executor 不得自审自批 |
| 9 | 归档与维护状态更新 | 归档与维护交接 | approved outputs、review decision、Step 9 approval | archive、stable updates、index refresh、next-iteration context | Maintainer / Governance | approval-required | Maintainer archive 并刷新维护上下文 | 当前 change closeout 完成 | 需要 approval；不得只归档不刷新状态 |

## 4. Gate Type / Gate State Model

V0.3.0 必须区分 gate 类型与 gate 状态，避免把 review 和 approval 混成一个 `approval=pending`。

### 4.1 gate_type

- `review-required`：需要 review 或 human sponsor 确认设计 / 包 / 验证结果，但不是执行批准。
- `approval-required`：需要明确 human approval 或 reviewer decision 才能进入下一关键状态。
- `auto-pass-to-step7`：Step 6 执行完成后进入 Step 7 验证，不代表无需 evidence。

### 4.2 gate_state

- `not-started`
- `waiting-review`
- `reviewed`
- `waiting-approval`
- `approved`
- `bypassed`
- `blocked`
- `not-required`

### 4.3 approval_state

`approval_state` 只用于 `approval-required` gate：

- `required-pending`
- `approved`
- `bypassed`
- `not-required`

对于 `review-required` gate，status 应展示 `gate_type=review-required` 与 `gate_state=waiting-review/reviewed`，不应误写为 `approval=pending`。

## 5. Human Report Model

`ocw step report --format human` 应生成可直接转述给人的摘要：

- 当前标准 Step
- 传统映射说明
- 为什么做这一步
- 本步输入
- 本步输出
- gate_type 与 gate_state
- framework_controls
- agent_actions_done
- agent_actions_expected
- blockers / risks
- 需要人确认的问题
- 下一步进入条件

## 6. Framework Controls / Agent Actions Model

Step report 应包含稳定字段：

```yaml
framework_controls:
  - 本步必须产出清晰输入/输出/gate/owner/下一步进入条件。
  - 带 approval-required gate 的步骤必须等待 human approval 或 reviewer decision。
agent_actions_done:
  - Agent 已汇总 source docs。
  - Agent 已生成人类可读报告。
agent_actions_expected:
  - Agent 下一步应等待 human review。
  - Agent 不得把命令成功当成人类确认。
```

`agent_actions_done` 只记录已经发生的动作。`agent_actions_expected` 记录本步后续预期动作，避免混淆“已做”和“应该做”。

## 7. Closeout Trace Model

archive 后的 closeout 至少应集中展示：

- final status
- Step 1-9 final state
- Step 5/8/9 approval summary
- review decision
- archive receipt
- final consistency ref

## 8. 模块边界

### 8.1 运行逻辑模块

- `src/governance/change_prepare.py`：调整 prepare 语义，避免把准备材料等同于 Step 5 完成。
- `src/governance/current_state.py`：current-state 根据真实 step 和 gate facts 表达当前状态。
- `src/governance/step_matrix.py`：统一 Step 1-9 边界、gate_type/gate_state 和 status snapshot。
- `src/governance/step_report.py`：增加 human format、step boundary、framework_controls、agent_actions_done/expected。
- `src/governance/agent_adoption.py`：adoption plan 显示 owner matrix 和 Step 5/8/9 gate。
- `src/governance/cli.py`：暴露 human report、调整 onboard/setup/change prepare/status 输出、强化 bypass 参数。
- `src/governance/review.py`：review trace 直接引用 Step 8 approval，记录 bypass 风险接受。
- `src/governance/archive.py`：final consistency 汇总 Step 5/8/9 gate summary。
- `src/governance/human_gates.py`：提供 approval / bypass reference 和 summary helper。

### 8.2 治理文档与规范

- `.governance/AGENTS.md`：写入标准 9 步运行流程和传统映射硬规则。
- `.governance/agent-playbook.md`：写入 Agent 不得发明影子生命周期、不得把 prepare 当 Step 5 完成。
- `.governance/current-state.md`：中文 human-facing 状态，标准 Step 为唯一当前流程状态。
- `.governance/participants.yaml` / `.governance/participants-matrix.md`：保持 owner / reviewer / human gate 矩阵可读。
- `docs/specs/07-standard-9-step-runtime-flow.md`：必要时补充 gate_type / gate_state 语义，不能改变标准 9 步。
- `docs/specs/08-role-binding-spec.md`：必要时补充 approval / review 边界。
- 当前 change package artifacts：requirements、design、tasks、contract、step reports 必须与 Step 1-9 边界一致。

### 8.3 测试与脚本

- `tests/test_v030.py`：新增 V0.3.0 回归测试主入口。
- `tests/test_v029.py`：确保 v0.2.9 hard gate 行为不回退。
- `scripts/smoke-test.sh`：覆盖 gate summary、bypass、archive closeout。

## 9. 测试策略

### 9.1 R-000 流程语义测试

必须证明：

- `change prepare` 不会把 Step 1-5 标记为 completed。
- prepare 后 status 指向 Step 1 输入接入与问题定界。
- 输出不包含非规范 lifecycle 名称。
- current-state 使用标准 Step 作为唯一当前流程状态。

### 9.2 R-001 adoption / onboarding 测试

必须证明：

- `adopt --dry-run` 提示 Step 5、Step 8、Step 9 gate。
- `onboard` / `setup` 展示或指向 owner matrix。
- 输出要求 Agent 向人确认参与者、owner、reviewer、human gate 和 final decision owner。

### 9.3 R-002 步骤边界与 Step 1 provenance 测试

必须证明：

- Step 1 report 包含输入来源、问题清单、优化项、bug 项、非目标、风险、验收标准、开放问题。
- intent confirmation 记录 confirmed_by、recorded_by、evidence_ref、confirmation_mode。
- 每一步 report/status 可展示输入、输出、gate_type、gate_state、owner、完结动作和下一步进入条件。

### 9.4 R-003 / R-004 human report 测试

必须证明：

- `step report --format human` 可用。
- human report 包含 framework_controls、agent_actions_done、agent_actions_expected。
- 带 approval-required gate 的步骤明确暂停并要求确认。

### 9.5 R-005 status gate 语义测试

必须证明：

- review-required step 不显示 misleading `approval=pending`。
- approval-required step 正确显示 `required-pending / approved / bypassed`。
- Step 1/3/4/7 与 Step 2/5/8/9 gate 语义不同。

### 9.6 R-006 至 R-009 审计链测试

必须证明：

- idle status 展示或指向最近 archive closeout。
- review.yaml 引用 Step 8 approval。
- final consistency 汇总 Step 5/8/9 gate。
- reviewer mismatch bypass 缺少 reason / recorded_by / evidence_ref 时失败。

## 10. 推荐实施切片

### Slice A：流程语义 + 全步骤边界 + human report/status 基础

包含 P0：

- R-000
- R-002
- R-003
- R-004
- R-005

说明：Slice A 是底座，但不是 P0 全部。完成 Slice A 不能代表 V0.3.0 P0 完成。

### Slice B：adoption / onboard 入口

包含 P0：

- R-001
- AGENTS / playbook 术语硬规则

说明：Slice B 与 Slice A 可以按顺序执行，但 R-001 仍是 P0，必须进入 final contract；除非 human sponsor 显式批准延期，否则不得在 R-001 未完成时通过最终验收。

### Slice C：closeout 与审计集中

包含 P1：

- R-006
- R-007
- R-008
- R-009

说明：Slice C 依赖前面状态和 report 语义稳定，但仍属于 V0.3.0 默认范围。

## 11. 风险与防护

### 风险 1：再次把准备态当成标准步骤完成态

防护：

- R-000 测试先行。
- current-state/status 输出以真实 step evidence 为准。

### 风险 2：human report 变成另一套不受控文案

防护：

- human report 从 canonical step boundary table 渲染。
- 不单独维护第二套流程含义。

### 风险 3：任务范围膨胀到产品化 UI

防护：

- V0.3.0 不包含 Dashboard / TUI / Web UI。
- 只做 CLI/Agent 输出和文件协议层。

### 风险 4：审计字段分散但看似完整

防护：

- review 和 final consistency 必须直接引用或汇总 gate facts。
- smoke test 检查归档后的集中视图。

## 12. Step 3 修订结论

V0.3.0 的设计基线应是：

1. 先修标准流程语义和 prepare-state 分离。
2. 用 canonical Step 1-9 boundary table 支撑每一步边界清晰。
3. 用 gate_type / gate_state / approval_state 区分 review 与 approval。
4. 基于 step boundary 渲染 human report 和 status。
5. 把 `framework_controls`、`agent_actions_done`、`agent_actions_expected` 作为报告事实层字段。
6. 将 review/archive/gate facts 集中到审计链中。
7. 通过 R-000 至 R-009 对应测试锁住行为。

该修订用于回应 Hermes Step 3 review 的 `revise` 结论。修订后仍需 Hermes re-review。确认前不应进入 Step 4。

## 13. 请求 Hermes re-review 的问题

请确认或继续指出问题：

1. canonical Step 1-9 boundary table 是否足以支撑 Step 4 组装 change package？
2. gate_type / gate_state / approval_state 是否已消除 review 与 approval 混淆？
3. R-001 / R-002 是否已纳入测试策略和模块边界？
4. 治理文档、spec、current-state、change package artifacts 是否已纳入模块边界？
5. Slice A/B/C 是否已明确为执行顺序而不是 scope 降级？
