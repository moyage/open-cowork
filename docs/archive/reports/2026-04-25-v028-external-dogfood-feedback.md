# V0.2.8 External Dogfood Feedback: Enforceable Human Gates

日期：2026-04-25
反馈来源：

- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V028_DOGFOOD_REPORT_ZH.md`

本文是 v0.2.8 发布后的外部 dogfood 反馈归档报告，不是已批准的实现计划。它记录个人域多 Agent 场景中对 v0.2.8 default-visible and enforceable human gates 的实测结果、已闭合问题、仍未闭合的体验缺口，并为下一轮候选输入提供事实材料。

## 1. 背景

v0.2.8 的目标是在 v0.2.7 human-control baseline 之上，把参与者映射、意图确认、步骤报告和 human gate 从“可记录”推进到“默认可见、默认接入命令流、默认不可静默绕过”。

本轮外部 dogfood 复跑 v0.2.7 流程，重点验证：

- 9 步报告是否默认生成；
- 显式 owner / reviewer / assistant 映射是否可用；
- Step 5 human gate approval 是否能阻止执行；
- draft contract、intent readiness、archive consistency 等 v0.2.7 反馈是否闭合；
- 人类团队成员是否感受到黑盒感降低。

## 2. 已验证的改善

### 2.1 技术闭环成立

反馈报告确认以下链路可完成：

1. `ocw version` 显示 `open-cowork 0.2.8`。
2. `./scripts/smoke-test.sh` 通过，测试集通过。
3. `onboard` / `adopt --dry-run` 可完成初始化和 adoption plan。
4. `change create` 后、`change prepare` 前执行 `step report`，已输出人类可读恢复建议，不再输出 Python traceback。
5. `participants setup` 支持 `--step-owner`、`--step-reviewer`、`--step-assistant` 并能把实际 Agent 映射到 Step 5-8。
6. 未确认 intent 时，`run` 被 `step6_entry_ready is not True` 阻止。
7. 已确认 intent 但未 Step 5 approval 时，`run` 被 Step 5 human gate 阻止。
8. Step 5 approval 后，`run` / `verify` / `review` / `archive` 可完成闭环。
9. `archive` 生成最终一致性快照。

### 2.2 对 v0.2.6 / v0.2.7 反馈的闭合情况

已闭合：

- 归档后 `current-state.md` 同步 idle / archived。
- Step 1-9 reports 可完整生成并进入归档包。
- 自定义参与者可进入 step matrix。
- 先配置 participants 后再 `change prepare` 不再覆盖 bindings。
- draft contract 阶段 `step report` 不再 traceback。
- intent 未确认不会允许 Step 6 readiness。
- Step 5 human gate 已接入 `run`。
- archive 包含最终状态一致性快照。

部分闭合：

- human gate 已从展示型约束推进到执行型约束，但目前只强制到 Step 5 -> run。
- step report 已默认生成并输出路径，但 CLI 默认摘要仍偏短。
- reviewer 与 bindings 一致性已有 warning，但错误 reviewer 仍可 approve。

## 3. 核心结论

v0.2.8 已经把 v0.2.6 / v0.2.7 暴露的核心结构性缺口推进到可 dogfood 的状态：人能看到 9 步报告，能把实际 Agent 映射到步骤，Step 5 gate 能真正阻止执行。

但 v0.2.8 也暴露出下一层信任问题：

1. **Step 8 / Step 9 gate 尚未执行化。** 人看到 Step 8 / Step 9 `human_gate=true`，会期待 review 决策和归档关闭也需要明确 approval；当前仍可绕过。
2. **reviewer mismatch 风险偏高。** 工具已 warning，但仍允许错误 reviewer approve，且 approve 后状态进入 `review-approved`。
3. **归档后的 Step 9 report 状态不一致。** archive 成功后，归档包内 Step 9 report 仍可能显示 `pending` 和过时 blocker。
4. **默认人类摘要还不够直接。** status 与 step report CLI 输出仍偏 Agent/文件索引友好，人要理解全貌仍依赖 Agent 主动打开文件并转述。
5. **approval 记录仍无法区分谁批准与谁代记录。** `approved_by` / `confirmed_by` 有审计记录，但没有 `recorded_by` 或 evidence ref，无法表达“Agent 观察到人类确认”。

因此，下一轮不应重新扩大主题，而应继续沿着 v0.2.8 的主线，把 Step 8/9 gate、reviewer enforcement、状态回看一致性和人类摘要面补齐。

## 4. 关键问题归档

### F-028-001：Step 8 reviewer mismatch 仍然只是 warning

现象：Step 8 reviewer 配置为 `review-agent`，但执行 `review --reviewer wrong-reviewer` 仍会记录 approve，只输出 warning。

影响：错误 reviewer 可以把 change 推入 `review-approved`，之后无法自然用正确 reviewer 重新 review。

候选方向：reviewer mismatch 默认失败；如需允许，必须显式 `--allow-reviewer-mismatch` 或 `--force-reviewer-mismatch`，并写入风险记录。

### F-028-002：Step 8 human gate 未被 review 强制消费

现象：Step 8 report 显示 `human_gate=true`，但 `review` 不需要 Step 8 approval。

影响：Step 8 “Review and decide” 是人的关键决策点，但工具仍允许 Agent 直接完成。

候选方向：如果 Step 8 配置 human gate，`review` 前或 review approve 后进入 archive 前必须存在 Step 8 approval record。

### F-028-003：Step 9 human gate 未被 archive 强制消费

现象：Step 9 report 显示 `human_gate=true`，但没有 Step 9 approval 时 `archive` 仍成功。

影响：归档关闭仍可绕过人的最终确认。

候选方向：archive 默认检查 Step 9 approval；如无 approval，要求显式 force 并写入 risk / bypass record。

### F-028-004：archive 后 Step 9 report 仍显示 pending

现象：归档包内 Step 9 report 显示 `status: pending`，同时 archive receipt 和 final consistency 显示成功。

影响：人回看归档包会困惑 Step 9 到底是完成、pending，还是存在 blocker。

候选方向：archive 成功后重写 Step 9 report 为 `completed` / `archived` 状态，并清理已过时 blocker。

### F-028-005：`change prepare` 输出未提示 Step 5 approval

现象：`change prepare` handoff 提示 participants、intent、step report，但没有提示 `step approve --step 5`。

影响：Agent 可能按提示完成后，在 `run` 才发现缺 approval。

候选方向：把 Step 5 approval 加入 human-control baseline handoff。

### F-028-006：status human summary 仍偏粗

现象：`status` 能显示 phase、current owner、human intervention required，但没有直接展示 Step 1-9 report 索引、approval 状态、当前 gate 是否满足。

影响：人仍需要 Agent 读取多个文件才能理解 9 步推进全貌。

候选方向：`status` 增加 concise 9-step progress table，包含 step、owner、gate、approval、report ref、next action。

### F-028-007：step report CLI 输出仍过短

现象：CLI 只输出 `Step report written`、owner、human_gate、recommended_next_action。

影响：对 Agent 足够，对人不够；人要打开 markdown 才能看到 inputs、outputs、done criteria、next-entry criteria 和 participant responsibilities。

候选方向：增加 `--format human` 或扩展默认 text 输出，直接显示核心摘要。

### F-028-008：human confirmation / approval 仍可由 Agent 代填

现象：`intent confirm --confirmed-by human-sponsor` 与 `step approve --approved-by human-sponsor` 均可由 Agent 执行。

影响：审计上有记录，但不能区分真实人类确认与 Agent 代填。

候选方向：增加 `recorded_by`、`evidence_ref`、`confirmation_mode`，表达“谁批准”和“谁记录/观察到批准”。

## 5. 人类体验视角

### H-028-001：黑盒感明显降低

Step 1-9 reports 进入归档包后，人可以回看每一步 owner、输入、输出、完成标准和参与者职责。

### H-028-002：实时体验仍依赖 Agent 主动汇报

文件已经完整，但执行过程中人没有自然看到每一步摘要。如果 Agent 不主动读给人，体验仍可能退回“命令跑完了”。

### H-028-003：Owner 设置有进步，但仍不像向导

`--step-owner 6=coding-agent` 很明确，但对人来说仍是 CLI 参数，不是“在表格里设置每一步 owner / participant”。

### H-028-004：Step 5 gate 符合心理预期

未批准不能 `run`，让人第一次感到 human gate 真正有用。

### H-028-005：Step 8/9 gate 与心理预期不一致

人看到 Step 8/9 `human_gate=true` 会以为 review 决策和归档关闭都需要确认，但实际仍可绕过。

## 6. 对下一轮的输入

建议下一轮主题收敛为：

**Review/archive gate closure and human-facing status**

优先级顺序：

1. reviewer mismatch 默认阻止，force 时写风险记录。
2. Step 8 / Step 9 human gate 接入 `review` / `archive`。
3. archive 后重写 Step 9 report，确保归档回看一致。
4. `change prepare` handoff 加入 Step 5 approval。
5. `status` 增加 9-step progress table。
6. step report text 输出增加人类摘要。
7. approval / confirmation 增加 `recorded_by` 与 evidence ref。

这轮仍不建议优先做 Dashboard / TUI / 云端团队系统。当前最重要的是把 v0.2.8 已经验证有效的 gate model 闭合到 review/archive，并让人不用打开多个文件也能读懂当前状态。
