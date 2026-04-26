# V0.3.0 Step 3 Continuation Compression

Date: 2026-04-26
Change: `v0.3-human-participation-closeout-readability`
Current standard step: `Step 3 / 方案塑形`
Current owner: `architect-agent`

This file is a continuation artifact created before Step 3 solution shaping because the conversation context is near threshold. It preserves the minimum facts needed to continue without re-reading the whole thread.

## 当前状态

- 当前处于标准 9 步运行流程的 `Step 3 / 方案塑形`。
- `ocw status` 显示：
  - current_step: 3
  - completed_steps: 1, 2
  - Step 1 approval: approved
  - Step 2 approval: approved
- 不得跳到 Step 4、Step 5 或 Step 6。
- 下一步必须产出 Step 3 方案基线和方案方向，交给 human sponsor review。

## 已完成确认

### Step 1 / 输入接入与问题定界

Step 1 已确认。

证据：

- `docs/reports/2026-04-26-v030-step1-input-framing-report.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/human-gates.yaml`

Human sponsor 关键确认：

- `prepare-state` 与 `standard step-state` 分离是 V0.3.0 最高优先级 P0。
- 除 dogfood 报告和本轮纠偏反馈外，暂无其他必须纳入 Step 1 的输入源。
- A-D 四类问题分组覆盖关键方向。
- 标准 9 步运行流程和传统四阶段映射需要写入 AGENTS / playbook 硬规则；先固化，再优化，后续再模板化或定制化。
- status 语义修正应与 human report 同一切片推进。
- 当前没有明确排除在 V0.3.0 外的补充内容。
- 补充：不只是 Step 1 / Step 2 边界清晰化，而是标准 9 步每一步都必须边界清晰。

### Step 2 / 意图澄清与范围定义

Step 2 已确认。

证据：

- `docs/reports/2026-04-26-v030-step2-scope-confirmation-report.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/human-gates.yaml`

Human sponsor 明确确认：

> 确认 Step 2 通过：V0.3.0 的目标、范围、非目标、优先级、验收标准和复杂度档位可以作为 Step 3 方案塑形输入。允许进入 Step 3。

## V0.3.0 目标

固化标准 9 步运行流程和传统人视角阶段映射，明确每一步的输入、输出、gate、owner、完结动作和下一步进入条件；同时把 step report、status、review、archive 和 bypass trace 做成人能理解、能确认、能审计的协作界面。

## 范围内

- 标准流程术语与 prepare 状态分离。
- adoption / onboarding 的人类参与入口。
- 标准 9 步每一步边界清晰。
- Step report 人类可读格式。
- `framework_controls` / `agent_actions` 分离。
- status approval 语义修正。
- idle closeout 可读性。
- review / archive 审计链集中。
- reviewer mismatch bypass 风险确认。

## 范围外

- Dashboard / TUI / Web UI。
- 云端多人审批系统。
- 企业 RBAC。
- 跨仓库团队协作平台产品化。
- 对外部 `/Users/mlabs/Programs/xsearch/**` 仓库的修改。
- 未进入 Step 6 前不得进行实现代码修改。
- 未通过 review approve 和 Step 9 human approval 前不得归档。

## 优先级

P0：

- R-000：标准流程术语与 prepare 状态分离。
- R-001：adoption / onboarding 展示完整人类参与路径。
- R-002：标准 9 步每一步边界清晰，且 Step 1 确认可追踪。
- R-003：step report 提供人类可读格式。
- R-004：step report 区分 `framework_controls` 与 `agent_actions`。
- R-005：status approval 语义无歧义。

P1：

- R-006：idle status 支持最近归档轮次 closeout。
- R-007：review trace 引用 Step 8 approval。
- R-008：final consistency 汇总 human gates。
- R-009：reviewer mismatch bypass 要求人类可读风险接受。

## 复杂度档位

`standard`

原因：

- 涉及 CLI 输出、状态语义、step report schema、review/archive trace、文档和测试，多模块联动，不适合 Lite。
- 不包含 Dashboard、云端系统或企业 RBAC，因此不需要 Strict。

## Step 3 应产出什么

Step 3 必须产出设计基线和方案方向，不应写实现代码。

Step 3 报告应包含：

- 方案原则：先固化标准流程语义，再优化 human-facing 输出。
- 流程边界模型：每一步都暴露输入、输出、gate、owner、完结动作、下一步进入条件。
- 模块边界：
  - `src/governance/change_prepare.py`
  - `src/governance/current_state.py`
  - `src/governance/step_matrix.py`
  - `src/governance/step_report.py`
  - `src/governance/agent_adoption.py`
  - `src/governance/cli.py`
  - `src/governance/review.py`
  - `src/governance/archive.py`
  - `src/governance/human_gates.py`
  - tests and docs
- 测试策略：先写 R-000 测试，再覆盖 human report/status/review/archive/bypass。
- 切片建议：语义固化与 human report/status 同切片推进。
- 风险：再次把 prepare 态误投影为 Step 5、把 Step report 当执行完成、把审批当命令成功。

## 当前文件状态提醒

这些文档是当前 change 的 source / validation objects，仍处于未提交工作树：

- `docs/plans/2026-04-26-v030-human-participation-candidate-input.md`
- `docs/plans/2026-04-26-v030-human-participation-implementation-plan.md`
- `docs/reports/2026-04-26-v030-context-compression.md`
- `docs/reports/2026-04-26-v030-step1-input-framing-report.md`
- `docs/reports/2026-04-26-v030-step2-scope-confirmation-report.md`
- `docs/reports/2026-04-26-v030-step3-continuation-compression.md`

Ignored governance runtime files also changed under `.governance/changes/**`, `.governance/index/**`, and `.governance/runtime/**`.

## 下一步

继续执行 Step 3：产出 `docs/reports/2026-04-26-v030-step3-solution-shaping-report.md`，等待 human sponsor review。确认前不得进入 Step 4。
