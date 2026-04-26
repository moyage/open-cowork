# V0.3.0 最终复盘与归档前报告

Change: `v0.3-human-participation-closeout-readability`
版本目标：V0.3.0 / 人类参与与收束可读性
报告时间：2026-04-26
当前状态：`review-approved`
当前标准步骤：Step 8 / Review and decide
下一决策：Step 9 / Archive and carry forward

## 1. 结论

V0.3.0 的核心目标已经达到：本轮将 v0.2.9 已经建立的硬 gate，推进为默认对人可见、可讨论、可确认、可审计的协作流程。标准 Step 1-9、传统人视角四阶段映射、human gate、step report、status approval 语义、review trace、archive 前置 gate 和 final consistency summary 已经形成闭环实现与测试覆盖。

本轮尚未执行 archive。原因不是实现未完成，而是 open-cowork 流程要求 Step 9 archive 仍需 human approval。当前正确状态是：Step 8 已通过，review decision 已 approve，等待 Step 9 归档确认。

## 2. 本轮目标对照

### 已达成

- Step 1-9 不再被混称为临时生命周期；标准 Step 号成为唯一流程状态。
- `change prepare` 与 Step 1-5 completion 语义分离，prepare 不再伪造已完成步骤。
- 每一步都具备人类可读的输入、输出、owner、gate、完成标准、下一步进入条件和确认选项。
- `step report` 支持 human-facing 输出，并区分 `framework_controls`、`agent_actions_done`、`agent_actions_expected`。
- status 明确拆分 `gate_type`、`gate_state`、`approval_state`，避免 review-required 步骤显示 misleading approval pending。
- Step 5 / Step 8 / Step 9 的 human gate 路径在 onboarding、status、report、review/archive 中可见。
- Step 8 review trace 已引用 human approval。
- reviewer mismatch bypass 已要求 reason、recorded_by、evidence_ref。
- archive 逻辑已准备 final consistency human gate summary，但尚未执行归档。

### 未归档前仍未完成

- Step 9 human approval 尚未记录。
- archive 尚未执行。
- `FINAL_STATE_CONSISTENCY_CHECK.yaml` 与 archive receipt 只有执行 archive 后才会生成。

## 3. 标准步骤复盘

| Step | 状态 | 说明 |
| --- | --- | --- |
| Step 1 / Clarify the goal | completed | 已完成输入接入、问题定界和人类确认。 |
| Step 2 / Lock the scope | completed | 已确认目标、范围、非目标、优先级、验收标准和复杂度档位。 |
| Step 3 / Shape the approach | completed | 已完成方案塑形，并经过 Hermes review / revise / re-review approve。 |
| Step 4 / Assemble the change | completed | 已组装 requirements / design / tasks / contract，并纳入 consistency items。 |
| Step 5 / Approve the start | completed | 已记录 human approval，允许进入 Step 6。 |
| Step 6 / Execute the change | completed | 已完成实现、文档、测试和 evidence。 |
| Step 7 / Verify the result | completed | 验证通过，`verify.yaml` 为 pass。 |
| Step 8 / Review and decide | review-approved | 独立复审 approve，human approval 已记录，`review.yaml` 已写入 approve。 |
| Step 9 / Archive and carry forward | pending | 等待 human approval 后执行 archive。 |

## 4. 关键变更包

### 运行时与治理逻辑

- `src/governance/change_prepare.py`：修正 prepare-state 与 standard step-state 的关系。
- `src/governance/step_matrix.py`：集中表达 Step 1-9、gate model、status snapshot 和 next decision。
- `src/governance/step_report.py`：生成 human-facing step report，并读取真实 `human-gates.yaml` 计算 gate 状态。
- `src/governance/review.py`：要求 Step 8 approval，写入 `step8_approval_ref`，并强化 reviewer mismatch bypass。
- `src/governance/archive.py`：为 final consistency 增加 human gate summary。
- `src/governance/human_gates.py`：补充 approval / bypass 审计辅助能力。
- `src/governance/current_state.py`：同步中文 current-state，避免影子生命周期。

### 文档与人类可读材料

- `.governance/AGENTS.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`
- `.governance/participants.yaml`
- `.governance/participants-matrix.md`
- `docs/specs/07-standard-9-step-runtime-flow.md`
- `docs/agent-adoption.md`
- `docs/getting-started.md`
- Step 1-9 reports
- Step 6 execution report
- Step 7 verification report
- Step 8 revise fix report
- Step 8 independent re-review result

## 5. 验证与审查

### 验证命令

- `PYTHONPATH=tests python3 -m unittest discover -s tests -v`：通过，172 tests OK。
- `./scripts/smoke-test.sh`：通过。
- `bin/ocw contract validate --change-id v0.3-human-participation-closeout-readability`：通过。
- `bin/ocw hygiene --format json`：`state_consistency.status = pass`。
- `git diff --check`：通过。

### 独立 Review

- 初次 Step 8 independent review：`revise`。
- Revise findings：
  - Step report 未读取真实 `human-gates.yaml`。
  - Step 7 后投影证据仍停留在 Step 6。
  - Step 6 report 和 Step 1-4 新字段证据不完整。
- 修复后 re-review：`approve`。
- 正式 review decision：`approve`，已写入 `review.yaml`。

## 6. 本轮复盘

### 做得正确的部分

- 人类反馈中的“Step 1-9 是框架规范，不是临时 flow”被提升为硬规则和测试语义。
- 每一步边界清晰化没有只做 Step 1 / Step 2，而是扩展到完整 Step 1-9。
- Step 8 独立 review 没有流于形式；reviewer 提出的阻断项被转成回归测试、代码修复和证据刷新。
- approval / review / archive 的人类动作从长句式改为短选项，降低了人为输入歧义。
- “命令成功”没有被用来掩盖流程事实；Step 9 未批准前没有 archive。

### 暴露的问题

- 初始自验不够严格，未及时发现 Step Report 使用空 approval dict 的事实源缺陷。
- 状态投影刷新链路不够自动，导致一度出现 Step 6 / Step 7 证据视角不一致。
- `next_decision` 在 Step 8 approval 后仍指回 Step 8，说明 status snapshot 的 human gate 语义需要更多后置状态测试。
- tasks 与 report 的状态同步仍依赖人工维护，容易在 review / revise / approve 流程中出现陈旧文案。

### 已采取的纠偏

- 新增 Step 8 / Step 9 approval report 回归测试。
- 新增 Step 8 approval 后 `next_decision` 指向 Step 9 的回归测试。
- 刷新 Step 1-9 reports、STEP_MATRIX_VIEW、STATUS_SNAPSHOT、STATE_CONSISTENCY_CHECK 和 current-state。
- 将 Step 8 revise fix 与 independent re-review 形成独立报告。
- 将测试数量和 evidence 更新到 172 tests，避免验证事实陈旧。

## 7. 剩余风险与后续建议

### Step 9 前必须处理

- 需要 human sponsor 明确 Step 9 approval。
- archive 执行后必须检查：
  - archive receipt 存在。
  - `FINAL_STATE_CONSISTENCY_CHECK.yaml` 包含 Step 5 / Step 8 / Step 9 gate summary。
  - idle status 能展示或指向最近归档 closeout。
  - `.governance/current-state.md` 进入归档后维护态。

### 后续迭代建议

- 将 step boundary model 进一步集中，减少 report/status/tasks 中重复事实源。
- 为 evidence / projections 增加 stale detection，避免状态文件陈旧但 hygiene 仍 pass。
- 将 Step approval / review / archive 的确认选项进一步产品化为 Agent-facing 固定交互模板。
- 拆分 executor scope 与 stable index/runtime 写权限，解决 `ocw run` 在当前 contract 下被 `no_executor_stable_write_authority` 拦截的问题。

## 8. 最终判断

V0.3.0 已达到本轮迭代预期，可以进入 Step 9 归档确认。当前不应再追加实现型改动，除非 Step 9 前发现新的阻断问题。

推荐 human sponsor 下一步选择：

1. `approve`：确认 Step 9 archive，允许正式归档 V0.3.0。
2. `revise`：暂不归档，先修订归档/收束材料。
3. `reject`：拒绝归档，停止或重定向。
