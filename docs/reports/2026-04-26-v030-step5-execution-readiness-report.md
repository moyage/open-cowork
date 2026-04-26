# V0.3.0 Step 5 角色绑定与执行准备报告

Change: `v0.3-human-participation-closeout-readability`
Step: `5 / 角色绑定与执行准备`
Status: `approved-by-human-sponsor`
Owner: `human-sponsor`

本文是 V0.3.0 标准 9 步运行流程的 Step 5 报告。它确认执行角色、执行范围、验证命令、证据要求和进入 Step 6 的审批条件。本文不是 Step 6 实现记录。

## 1. Step 5 输入

- Step 4 已通过的 requirements / design / tasks / contract。
- Step 3 Hermes re-review approve。
- Step 4 human sponsor approval。
- `.governance/changes/v0.3-human-participation-closeout-readability/bindings.yaml`
- `.governance/changes/v0.3-human-participation-closeout-readability/contract.yaml`

## 2. 角色绑定

- Sponsor：`human-sponsor`
- Orchestrator：`orchestrator-agent`
- Executor：`executor-agent`
- Verifier：`verifier-agent`
- Independent reviewer：`hermes-agent` / `independent-reviewer`
- Maintainer：`maintainer-agent`
- Final decision owner：`human-sponsor`

约束：

- Executor 不得作为 Step 8 最终 reviewer。
- Step 6 不得在 Step 5 approval 前开始。
- Step 9 archive 必须等待 Step 8 review decision 与 Step 9 human approval。

## 3. 执行范围

范围内：

- `src/**`
- `tests/**`
- `docs/**`
- `.governance/AGENTS.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`
- `.governance/participants.yaml`
- `.governance/participants-matrix.md`
- `.governance/changes/v0.3-human-participation-closeout-readability/**`
- `.governance/index/**`
- `.governance/runtime/**`

范围外：

- `.governance/archive/**`，直到 Step 9 archive。
- 外部仓库 `/Users/mlabs/Programs/xsearch/**`。
- Dashboard / TUI / Web UI。

## 4. Step 6 必须保留的需求

P0 必须全部保留：

- R-000：标准流程术语与 prepare 状态分离。
- R-001：adoption / onboarding 完整人类参与路径。
- R-002：标准 9 步每一步边界清晰，且 Step 1 确认可追踪。
- R-003：step report human format，并支持简短确认选项或低歧义确认句。
- R-004：framework_controls / agent_actions_done / agent_actions_expected。
- R-005：gate_type / gate_state / approval_state 三层模型。

P1 默认纳入 V0.3.0：

- R-006：idle last archive closeout。
- R-007：review trace 引用 Step 8 approval。
- R-008：final consistency 汇总 human gates。
- R-009：reviewer mismatch bypass 风险接受。

## 5. 验证命令

Step 7 必须运行：

- `PYTHONPATH=tests python3 -m unittest discover -s tests -v`
- `./scripts/smoke-test.sh`
- `bin/ocw contract validate --change-id v0.3-human-participation-closeout-readability`
- `bin/ocw hygiene --format json`

Step 6 实现期间建议按切片运行：

- `PYTHONPATH=tests python3 -m unittest tests.test_v030 -v`
- `PYTHONPATH=tests python3 -m unittest tests.test_v029 tests.test_v030 -v`

## 6. 证据要求

- changed files manifest
- command output summary
- test output
- step report output
- human gate trace
- reviewer mismatch bypass trace，如发生 bypass
- final consistency gate summary，如进入 archive

## 7. 已知风险

- 当前 `ocw status` 仍存在 approval / human_intervention_required 语义表达不足，这是 V0.3.0 的 R-005 修复对象。
- 当前 `ocw status` 在 Step 5 下仍将 `next_decision` 投影为 Step 8，而不是 Step 6 entry approval；这必须在 Step 6 通过 R-005 测试驱动修复，不能解释为可跳过 Step 5 或 Step 6。
- Human gate 过去依赖长句确认，容易引入人为输入歧义；已纳入 R-003，Step 6 必须实现短选项或低歧义确认文本。

## 8. Step 5 确认结果

Human sponsor 已选择：

- `approve`：确认 Step 5 通过，允许进入 Step 6。

Approval ref: `.governance/changes/v0.3-human-participation-closeout-readability/human-gates.yaml`
