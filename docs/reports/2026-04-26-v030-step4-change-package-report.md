# V0.3.0 Step 4 变更包组装报告

Change: `v0.3-human-participation-closeout-readability`
Step: `4 / 变更包组装`
Status: `approved-by-human-sponsor`
Owner: `orchestrator-agent`

本文是 V0.3.0 标准 9 步运行流程的 Step 4 报告。它承接 Step 3 已确认的方案基线，将其组装为可执行、可验证、可审计的 change package。本文不是 Step 5 approval，也不是 Step 6 执行许可。

## 1. Step 4 目标

将 Step 3 方案基线整理为正式执行前的 change package，包括：

- requirements
- design baseline
- tasks
- contract
- validation objects
- verification commands
- evidence expectations
- Hermes consistency items

Step 4 的完结条件是：change package 被确认可执行、可验证、可审计，并可进入 Step 5 角色绑定与执行准备。

## 2. Step 4 输入物

- `docs/reports/2026-04-26-v030-step3-solution-shaping-report.md`
- `docs/reports/2026-04-26-v030-step3-hermes-review-result.md`
- `docs/reports/2026-04-26-v030-step3-hermes-rereview-result.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/requirements.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/design.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/tasks.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/contract.yaml`

## 3. 已组装的 change package 内容

### 3.1 Requirements

`requirements.md` 已同步为中文，并纳入：

- R-000：标准流程术语与 prepare 状态分离。
- R-001：adoption / onboarding 完整人类参与路径。
- R-002：标准 9 步每一步边界清晰，且 Step 1 确认可追踪。
- R-003：step report 人类可读格式。
- R-004：`framework_controls` / `agent_actions_done` / `agent_actions_expected`。
- R-005：`gate_type` / `gate_state` / `approval_state` 三层模型。
- R-006 至 R-009：idle closeout、review trace、final consistency、bypass 风险确认。

### 3.2 Design

`design.md` 已同步为中文，并采用 Step 3 修订后的设计基线：

- 标准 Step 号是唯一流程状态。
- prepare-state 与 standard step-state 分离。
- canonical Step Boundary Model 是 report/status/handoff 的事实基础。
- review-required 与 approval-required 分离。
- human report 不形成第二套流程事实源。

### 3.3 Tasks

`tasks.md` 已按标准 9 步重新组织：

- Step 1 / Step 2 / Step 3 已完成并有 human approval。
- Step 4 当前正在组装 change package。
- Step 5 才能进行角色绑定与执行准备审批。
- Step 6 才能开始实现代码修改。

### 3.4 Contract

`contract.yaml` 已纳入：

- Step 3 canonical boundary reference。
- Hermes re-review reference。
- gate_type / gate_state / approval_state 模型。
- `framework_controls` / `agent_actions_done` / `agent_actions_expected` 字段要求。
- R-000 至 R-005 必须进入 final execution contract 的检查要求。
- evidence expectations 增补 `step_report_output` 和 `human_gate_trace`。

## 4. Hermes consistency items 处理状态

### Item 1：current-state 只以标准 Step 号作为唯一流程状态

状态：已纳入。

处理：

- `current-state.md` 已移除 `生命周期` 和 `当前阶段` 作为流程状态的表达。
- 保留 `传统映射说明`，但只作为理解层。

### Item 2：`agent_actions` 拆分

状态：已纳入。

处理：

- requirements / design / contract 已改为 `agent_actions_done` 与 `agent_actions_expected`。
- 若后续需要兼容旧 `agent_actions`，只能作为只读 alias 或迁移映射。

### Item 3：R-005 三层 gate model

状态：已纳入。

处理：

- R-005 已扩展为 `gate_type` / `gate_state` / `approval_state`。
- Step 1/3/4/7 与 Step 2/5/8/9 的差异必须进入测试。

### Item 4：是否同步更新标准流程 spec

状态：纳入 Step 6 执行范围。

决策：

- V0.3.0 应更新 `docs/specs/07-standard-9-step-runtime-flow.md`，补充 gate_type / gate_state / approval_state 语义。
- 不能改变标准 9 步本身。
- 如涉及角色边界，还应同步检查 `docs/specs/08-role-binding-spec.md`。

## 5. 验证命令

Step 7 必须运行：

- `PYTHONPATH=tests python3 -m unittest discover -s tests -v`
- `./scripts/smoke-test.sh`
- `bin/ocw contract validate --change-id v0.3-human-participation-closeout-readability`
- `bin/ocw hygiene --format json`

Step 6 实现期间建议按切片运行目标测试：

- `PYTHONPATH=tests python3 -m unittest tests.test_v030 -v`
- `PYTHONPATH=tests python3 -m unittest tests.test_v029 tests.test_v030 -v`

## 6. 证据要求

Step 6 / Step 7 必须记录：

- changed files manifest
- command output summary
- test output
- step report output
- human gate trace
- reviewer mismatch bypass trace，如发生 bypass
- final consistency gate summary，如进入 archive

## 7. Step 5 进入条件

进入 Step 5 前，human sponsor 需要确认：

1. 当前 change package 是否可执行。
2. 当前 change package 是否可验证。
3. 当前 change package 是否可审计。
4. Hermes consistency items 是否已进入 Step 5/6 执行准备。
5. P0 R-000 至 R-005 是否全部保留在执行合同中。
6. P1 R-006 至 R-009 是否默认纳入 V0.3.0，或是否需要明确延期。

## 8. Step 4 机器侧验收

已执行：

- `git diff --check`：通过。
- `bin/ocw contract validate --change-id v0.3-human-participation-closeout-readability`：通过。
- `bin/ocw hygiene --format json`：`state_consistency.status = pass`，无 issues。
- `bin/ocw status`：当前仍处于 Step 4，Step 5/6/7/8/9 未开始，blockers 为 none。

已修复的 Step 4 断点：

- `manifest.yaml` 的 `target_validation_objects` 曾未包含 Step 1/2/3 报告与 Hermes re-review 报告，导致 status blocker。
- 已与 `contract.yaml` 的 `validation_objects` 对齐，重新检查后 blocker 清除。

已知语义差异：

- `bin/ocw status` 当前将 Step 4 视为 `approval=not-required`，因此显示 `human_intervention_required=false`。
- `current-state.md` 与本报告从协作推进角度仍要求 human sponsor review 后再进入 Step 5。
- 这正是 V0.3.0 R-005 要修复的 status approval / gate 语义问题之一，不能将当前 status 的 false 理解为允许自动进入 Step 5 或 Step 6。

## 9. Step 4 结论

V0.3.0 change package 已组装并经 human sponsor 确认通过，可作为 Step 5 角色绑定与执行准备输入。

Step 5 的职责是角色绑定与执行准备审批，不是执行实现。

## 10. 请求 human sponsor review 的问题

请确认或修订：

1. 是否认可当前 requirements / design / tasks / contract 已足以作为 Step 5 执行准备输入？
2. 是否确认 P0 R-000 至 R-005 全部保留在 final execution contract 中？
3. 是否确认 P1 R-006 至 R-009 默认纳入 V0.3.0，不延期？
4. 是否确认 Step 6 执行前必须先完成 Step 5 human approval？
