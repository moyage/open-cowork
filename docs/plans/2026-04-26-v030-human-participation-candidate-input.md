# V0.3 Candidate Input: Human Participation and Closeout Readability

候选版本：`v0.3`
输入来源：

- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V029_DOGFOOD_REPORT_ZH.md`
- `docs/reports/2026-04-26-v030-context-compression.md`
- `docs/archive/plans/63-v0.2.9-review-archive-gates-candidate-input.md`
- `docs/archive/reports/2026-04-25-v029-release-and-next-dogfood.md`

本文是 V0.3 候选输入和迭代准备，不是完成声明。正式实施前必须通过 active change contract、Step 5 approval、执行证据、verify、独立 review 和 archive。

## 1. 候选主题

**Human Participation and Closeout Readability**

目标：把 v0.2.7-v0.2.9 已经建立的 gate、status、review 和 archive 能力，升级为默认可被人理解、参与、确认和审计的协作体验。V0.3 的核心不是新增更多治理文件，也不是重命名或另造流程，而是让人沿着规范定义的标准 9 步运行流程及其传统四阶段映射，看懂自己正在批准什么、Agent 做了什么、框架强制了什么。

规范锚点：

- 标准 9 步运行流程以 `docs/specs/07-standard-9-step-runtime-flow.md` 为准。
- 传统人视角四阶段映射应保持清晰：需求接收与澄清、方案设计、实施与验证、评审归档。
- V0.3 的“人类参与体验”是标准流程的可见性和确认体验增强，不是另一个 `9-step human flow`。

## 2. 问题陈述

V0.2.9 证明了硬 gate 可以工作，但 dogfood 反馈显示体验仍偏后台：

- Agent 可以一路调用 CLI 推进标准 9 步流程，人只看到最终结果或散落文件。
- `onboard` / `adopt` 没有自然引导人确认参与 Agent、owner matrix、reviewer 和 human gate。
- Step 1 仍像记录 intent，而不是需求澄清、讨论、确认。
- Step reports 存在，但默认输出和推进过程没有让人自然参与。
- `status` active 状态可读性提升，但 approval 语义仍误导，idle 状态缺少上一轮 closeout 概览。
- 审计证据分散在 `human-gates.yaml`、`review.yaml`、`archive-receipt.yaml`、`FINAL_STATE_CONSISTENCY_CHECK.yaml`。
- `--allow-reviewer-mismatch` 仍需要更强的人类确认和风险可见性。

因此 V0.3 必须把“人类参与体验”作为主流程，而不是报告文件的副产物。

## 3. V0.3 范围

### R-001：Adoption and onboarding human participation prompts

优先级：P0

`ocw onboard` 和 `ocw adopt --dry-run` 必须展示人类可读的参与配置入口。

候选改动：

- adoption plan 的 `human_control_baseline_next_actions` 增加 Step 8 / Step 9 gate 提示。
- onboarding next actions 显示 9-step owner / assistant / reviewer / human gate / final decision owner matrix。
- 输出要求 Agent 向人确认参与者与职责，而不是只给 CLI 参数。

验收标准：

- 新项目初始化后，人能看到“有哪些 Agent / 谁负责哪一步 / 哪些步骤需要 human gate / review 和 archive 前还会暂停”。
- Agent 只读 adoption/onboard 输出也不会遗漏 Step 8/9 approval。
- 输出必须使用“标准 9 步运行流程”和“传统四阶段映射”等规范术语，不能引入会误导团队的替代生命周期名称。

### R-002：Standard step boundary clarity and Step 1 confirmation

优先级：P0

标准 9 步中的每一步都必须边界清晰。Step 1 必须遵守规范定义的“输入接入与问题定界”；Step 2 必须遵守“意图澄清与范围定义”；后续每一步也必须明确输入、输出、gate、owner、完结动作和下一步进入条件。V0.3 可以增强人类可读摘要和确认体验，但不能把 `change prepare` 误叙述为 Step 1-5 已经完成，也不能把任一步偷换为相邻步骤。

候选改动：

- Step 1 report / intent capture 输出包含需求来源、需求列表、优化项、bug 项、非目标、风险、验收标准、开放问题。
- Step 1 到 Step 2 前必须展示确认摘要。
- intent confirmation 增加 `recorded_by`、`evidence_ref`、`confirmation_mode`。

验收标准：

- 人能在 Step 1 明确看到“本轮要做什么、不做什么、怎么验收、还有什么没定”。
- 审计记录能区分谁确认、谁记录、证据在哪里。
- 人能在每一步报告中看出该步与前后步骤的输入/输出边界。

### R-003：Human step report format and default summary

优先级：P0

`ocw step report` 应成为 Agent 可直接转述给人的主界面。

候选改动：

- 增加 `--format human`，或让 text 输出满足 human format。
- human format 包含：当前阶段、步骤、owner、参与者、输入、框架约束、Agent 动作、产出、完成标准、下一步进入标准、风险、需要人确认的问题。
- 带 human gate 的步骤输出明确暂停语句和建议确认文本。

验收标准：

- Agent 可以直接把命令输出作为人类汇报，不需要人打开 YAML 或 markdown。
- Step 5/8/9 输出明确说明“正在批准什么”。

### R-004：Framework controls vs Agent actions

优先级：P0

每一步必须区分 open-cowork 强制的治理约束与当前 Agent 实际完成的动作。

候选改动：

- Step report schema 增加 `framework_controls` 和 `agent_actions`。
- framework_controls 描述该步由协议强制的产物、gate、review、approval、archive 或证据要求。
- agent_actions 描述当前 Agent 执行的命令、修改、测试、判断和汇报。

验收标准：

- 人能判断 open-cowork 的价值边界，而不是把框架和 Agent 行为混在一起。

### R-005：Status approval semantics

优先级：P0

修正 `ocw status` 中 completed Step 1/2/3 仍显示 `approval=pending` 的歧义。

候选改动：

- approval state 至少区分：
  - `not-required`
  - `required-pending`
  - `approved`
  - `bypassed`
- 只有真实 gating steps 显示 pending。
- status table 的文本和 JSON/YAML 投影保持一致。

验收标准：

- 已完成且无需审批的步骤不再显示 pending。
- 人能一眼看出真正阻塞的是哪个 human gate。

### R-006：Idle last-archive closeout summary

优先级：P1

archive 后的 idle 状态应保留上一轮 9-step closeout 摘要。

候选改动：

- `ocw status` idle 状态显示 last archived change 的 closeout table。
- 或增加 `ocw status --last-archive`，并在默认 idle 输出中提示该入口。
- closeout table 包含 Step 1-9 final status、approval summary、review decision、archive receipt。

验收标准：

- 人在归档后无需打开归档目录，也能确认上一轮完整闭合。

### R-007：Review approval trace

优先级：P1

`review.yaml` 应直接引用 Step 8 human gate approval。

候选改动：

- review trace 增加 `step8_approval_ref` 或 `human_gate_ref`。
- 当 Step 8 approval 缺失或 bypass 时，review 输出必须显式说明。

验收标准：

- 审计者打开 `review.yaml` 即可看到 review 由哪个 Step 8 approval 放行。

### R-008：Final consistency gate summary

优先级：P1

`FINAL_STATE_CONSISTENCY_CHECK.yaml` 不能只做存在性检查，应包含 gate summary。

候选改动：

- final consistency 增加 Step 5/8/9 approval actor、recorded_by、evidence_ref、approval status、bypass status。
- archive receipt 引用该 summary。

验收标准：

- 最终归档审计不需要跨多个文件才能判断 gate 是否被满足。

### R-009：Reviewer mismatch bypass hardening

优先级：P1

`--allow-reviewer-mismatch` 必须是显式、可解释、可审计的人类接受风险路径。

候选改动：

- bypass 参数必须配套 `--reason`、`--recorded-by`、`--evidence-ref`。
- bypass 写入 `human-gates.yaml` 与 `review.yaml` trace / warnings。
- status 和 review 输出高亮 bypass。

验收标准：

- Agent 不能只靠一个技术开关绕过 reviewer mismatch。
- 人能在 status、review、archive closeout 中看到 bypass 风险。

## 4. 非目标

V0.3 不默认包含：

- Dashboard / TUI / Web UI；
- 云端多人审批系统；
- 企业 RBAC；
- 跨仓库团队协作平台；
- 完整自然语言交互引擎。

这些可以在 V0.3 后基于稳定的 human-facing protocol 再推进。

## 5. 推荐切片

### Slice A：Entry participation

覆盖 R-001、R-002。

价值：从一开始把人和参与 Agent 带入流程。

### Slice B：Step-level human interface

覆盖 R-003、R-004。

价值：让每一步都能被人读懂和确认。

### Slice C：Status and closeout readability

覆盖 R-005、R-006。

价值：修复状态歧义，并让归档后仍可快速验收。

### Slice D：Audit trace consolidation

覆盖 R-007、R-008、R-009。

价值：减少审计跳转，强化 bypass 风险控制。

## 6. 推荐完成定义

V0.3 至少应满足：

1. CLI 与文档统一使用标准 9 步运行流程和传统四阶段映射，不再把内部 prepare 状态误投影成 Step 5 已完成。
1. `onboard` / `adopt --dry-run` 显示 owner matrix 与 Step 5/8/9 gate 提醒。
2. Step 1 输出人类可确认的需求澄清摘要，并记录 confirmation provenance。
3. `step report --format human` 可直接作为人类汇报。
4. Step reports 包含 `framework_controls` 与 `agent_actions`。
5. `status` approval 语义不再误导。
6. idle 状态可查看上一轮 closeout。
7. `review.yaml` 直接引用 Step 8 approval。
8. final consistency 汇总 Step 5/8/9 gate 状态。
9. reviewer mismatch bypass 需要 reason、recorded_by、evidence_ref。
10. 全量单测、smoke test、dogfood script 或等效手工 dogfood 通过。

## 7. 待维护者确认的问题

1. V0.3 是否命名为 `Human Participation and Closeout Readability`？
2. Step 1 confirmation provenance 是否必须与 `step approve` 使用同一字段模型？
3. `step report --format human` 是否作为新格式，还是把默认 `text` 升级为 human format？
4. idle closeout 默认展示最近 archive，还是只在 `--last-archive` 下展示？
5. reviewer mismatch bypass 是否必须引用人类批准证据，还是允许独立 reviewer 说明理由？
