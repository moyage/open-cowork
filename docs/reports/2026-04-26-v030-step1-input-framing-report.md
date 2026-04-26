# V0.3.0 Step 1 输入接入与问题定界报告

Change: `v0.3-human-participation-closeout-readability`
Step: `1 / 输入接入与问题定界`
Status: `confirmed`
Owner: `human-sponsor`
Prepared by: `orchestrator-agent`

本文是 V0.3.0 标准 9 步运行流程的 Step 1 报告草案，用于让人补充、讨论和确认输入边界。它不是 Step 2 scope，不是 Step 3 design，也不是 Step 5 execution contract。

## 1. Step 1 目标

接入 V0.3.0 的多源输入，并形成问题边界、初始约束池和待澄清问题，使后续 Step 2 可以在清楚的输入基础上定义目标、范围、非目标和复杂度档位。

## 2. 已接入输入

### 2.1 主要反馈输入

- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V029_DOGFOOD_REPORT_ZH.md`
- 本轮对 V0.2.9 验收不严谨的复盘和纠偏讨论
- 当前会话中关于 Step 1-9 与传统四阶段映射被混淆的反馈

### 2.2 仓库内规范输入

- `docs/specs/07-standard-9-step-runtime-flow.md`
- `docs/specs/08-role-binding-spec.md`
- `docs/specs/04-change-package-spec.md`
- `docs/specs/13-round-close-report-and-closeout-package-spec.md`

### 2.3 当前准备材料

- `docs/reports/2026-04-26-v030-context-compression.md`
- `docs/plans/2026-04-26-v030-human-participation-candidate-input.md`
- `docs/plans/2026-04-26-v030-human-participation-implementation-plan.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/intent-confirmation.yaml`

## 3. 已识别问题原始清单

### 3.1 流程语义和规范执行混乱

- `change prepare` 生成治理材料后，当前工具容易把状态投影为 `step5-prepared`，让人误以为 Step 1-5 已完成。
- Agent 可能把“传统人视角四阶段映射”和标准 9 步运行流程混用。
- “9-step human flow”这类非规范表达会制造影子生命周期，削弱框架可信度。
- 如果 Agent 自己都不能稳定区分 Step 1、Step 2、Step 5、Step 6，团队使用时会更混乱。

### 3.2 人类参与体验不足

- Agent 可以在后台跑完大量 CLI，人只看到最终结果或分散文件。
- 初始化和 adoption 阶段没有自然提示人确认参与 Agent、owner、reviewer、human gate 和 final decision owner。
- 每个关键 gate 前缺少默认的人类可读摘要和暂停确认。

### 3.3 Step 1 没有真正成为输入接入与问题定界

- 现有 `intent capture` 更像记录需求字段，不足以支撑“多源输入接入、问题边界、约束池、待讨论问题”。
- 人没有被明确邀请补充输入、纠正问题理解、确认问题边界。
- Step 1 与 Step 2 容易混在一起：还没完成问题定界，就开始写 scope、contract 或 tasks。

### 3.4 Step reports 仍不够适合作为人的主界面

- 报告文件存在，但默认 CLI 输出仍偏 Agent 工具输出。
- 缺少 `framework_controls` 与 `agent_actions` 的清晰分离。
- 带 human gate 的步骤没有默认生成“正在批准什么”的确认摘要。

### 3.5 status 和 closeout 可读性不足

- active status 中 approval 语义仍可能误导，例如非真实 gating 步骤显示 pending。
- idle 状态缺少最近归档轮次的 9-step closeout 摘要。
- 人要验证上一轮是否闭合，仍需要跨多个归档文件。

### 3.6 review / archive 审计链分散

- `review.yaml` 未直接引用 Step 8 approval。
- `FINAL_STATE_CONSISTENCY_CHECK.yaml` 对 Step 5/8/9 gate summary 不集中。
- reviewer mismatch bypass 需要更强的人类可读理由、记录者和证据引用。

## 4. 初始问题分组

### A. 标准流程语义修正

核心问题：open-cowork 必须稳定表达唯一规范流程，即标准 9 步运行流程，并正确映射传统人视角阶段。

初始边界：

- 必须修正 prepare-state 与 standard step-state 的混淆。
- 必须统一术语，避免非规范 lifecycle 名称。
- 必须让 status/current-state/handoff 不再暗示 Step 1-5 已自动完成。

### B. 标准 9 步边界清晰化

核心问题：标准 9 步中的每一步都必须边界清晰。Step 1/2 的混淆只是当前最先暴露的问题；如果 Step 3/4、Step 4/5、Step 5/6、Step 7/8、Step 8/9 的输入、输出、gate 和完结动作同样模糊，执行流程仍会混乱。

初始边界：

- Step 1 产出 framed input、初始约束池、问题范围。
- Step 2 才产出目标、边界、非目标、复杂度档位。
- V0.3.0 必须让 Step 1-9 每一步在工具输出、Agent 操作、报告模板、status 和 handoff 中边界清楚。

### C. 人类参与和确认体验

核心问题：Agent-first 不能变成 Agent-only。

初始边界：

- CLI 仍是 Agent 内部工具。
- 人看到的是摘要、问题、风险、决策点、确认项，而不是命令清单。
- human gate 前必须默认暂停并展示可确认内容。

### D. 审计可读性和归档信任

核心问题：人和审计者应能低成本确认每个关键 gate 和 closeout 是否真实完成。

初始边界：

- review、final consistency、status、archive receipt 需要减少跨文件追踪。
- bypass 必须显式、可解释、可审计。

## 5. 初始约束池

- 标准 9 步运行流程固定，不得删除或另造替代流程。
- 传统人视角四阶段映射只能作为理解层，不能替代 Step 1-9。
- Step 1 未完结前，不得声称进入 Step 2。
- Step 2 未明确 scope / non-goals / policy level 前，不得生成最终执行 contract 的完成语义。
- Step 5 未完成角色绑定与执行准备审批前，不得进入 Step 6。
- Executor 不得担任最终独立 Reviewer。
- CLI 不应成为人的主界面；Agent 应把 CLI 事实转述为人能理解的状态、问题和决策。
- `.governance/archive/**` 在当前实施前不应修改。

## 6. 当前 Step 1 待补充问题

请重点补充或修正以下问题：

1. V0.3.0 是否应把“prepare-state 与 standard step-state 分离”列为最高优先级 P0？
2. 除 dogfood 报告和本轮纠偏反馈外，是否还有其他输入源必须纳入 Step 1？
3. 当前问题分组 A-D 是否覆盖了你认为最关键的 V0.3.0 方向？
4. 是否需要把“标准 9 步运行流程 + 传统四阶段映射”的术语纠偏写入 AGENTS / playbook 的硬规则？
5. V0.3.0 是否应该先修状态语义，再修 human report；还是二者同一切片推进？
6. 哪些内容明确不应进入 V0.3.0，避免范围继续膨胀？

## 7. Human sponsor 反馈与确认

Human sponsor 已确认：

1. “prepare-state 与 standard step-state 分离”应列为 V0.3.0 最高优先级 P0。
2. 除 dogfood 报告和本轮纠偏反馈外，暂无其他必须纳入 Step 1 的输入源。
3. 当前 A-D 四类问题分组覆盖关键方向。
4. 需要把“标准 9 步运行流程 + 传统四阶段映射”的术语纠偏写入 AGENTS / playbook 硬规则；优先固化，再优化，后续再模板化或定制化。
5. 状态语义修正应与 human report 同一切片推进。
6. 当前没有明确排除在 V0.3.0 外的补充内容。

Human sponsor 补充：不应只做 “Step 1 / Step 2 边界清晰化”，而应确保每一步都边界清晰，否则执行流程仍会混乱。

## 8. Step 1 确认结论

当前输入已足以形成 Step 2 的输入边界：

V0.3.0 应优先解决 open-cowork 在标准流程语义、每一步边界清晰度、人类参与入口、human-facing step report、status/closeout 可读性、review/archive 审计集中度上的混乱和缺口。

Step 1 的输入来源、问题边界、初始约束池和待带入 Step 2 的问题已获得 human sponsor 确认。可以进入 Step 2：意图澄清与范围定义。

## 9. Step 1 完结动作

Step 1 完结动作：

1. Human sponsor 已阅读本报告。
2. Human sponsor 已补充并修正问题边界。
3. Orchestrator 已根据反馈修订本报告。
4. Human sponsor 已明确确认 Step 1 输出：
   - 输入来源完整或足够推进；
   - 问题边界清楚；
   - 初始约束池可接受；
   - 待澄清问题可以带入 Step 2。
5. Step 1 确认痕迹应记录到治理证据。
6. 状态可以推进到 Step 2：意图澄清与范围定义。

## 10. Step 2 输入物

Step 2 的输入物为：

- 本 Step 1 确认报告；
- dogfood 反馈报告；
- V0.3.0 context compression；
- V0.3.0 candidate input；
- V0.3.0 implementation plan 草案；
- 标准 9 步运行流程规格；
- 角色绑定规格；
- change package 规格。

Step 2 应产出目标、边界、非目标、复杂度档位和进入 Step 3 的澄清结论。
