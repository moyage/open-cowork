# V0.2.7 External Dogfood Feedback: Human-control Baseline

日期：2026-04-25
反馈来源：

- `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V027_DOGFOOD_REPORT_ZH.md`

本文是 v0.2.7 发布后的外部 dogfood 反馈归档报告，不是已批准的实现计划。它记录个人域多 Agent 场景中对 v0.2.7 human-control baseline 的实测结果、体验改善和仍未闭合的问题，并为 v0.2.8 候选输入提供事实材料。

## 1. 背景

v0.2.7 的目标是基于 v0.2.6 暴露的定位落差，先做一轮“人的控制基线”：

- 参与者矩阵：`ocw participants setup`
- 意图捕获与确认：`ocw intent capture` / `ocw intent confirm`
- 步骤报告：`ocw step report`
- 归档后 human-readable state 同步：`ocw status --sync-current-state` 与 archive-time sync

本轮外部 dogfood 复跑了 v0.2.6 的安装、配置、实施、验收闭环，并重点验证 v0.2.7 是否让人更能看见和控制个人域多 Agent 协作。

## 2. 已验证的改善

### 2.1 技术闭环成立

反馈报告确认以下链路可完成：

1. `ocw version` 显示 `open-cowork 0.2.7`。
2. `./scripts/smoke-test.sh` 通过，测试集通过。
3. `ocw onboard` / `ocw adopt --dry-run` 可生成 adoption plan。
4. `ocw change create` / `ocw change prepare` 可建立 change package。
5. `ocw participants setup` / `ocw intent capture` / `ocw intent confirm` / `ocw step report` 可生成 v0.2.7 新增人类控制基线产物。
6. `ocw run` / `ocw verify` / `ocw review` / `ocw archive` 可完成执行、验证、审查和归档闭环。

### 2.2 人类可见性较 v0.2.6 明显提升

反馈者认为 v0.2.7 已经比 v0.2.6 更接近“人能看见流程”：

- participants matrix 让人可以看到 owner、assistants、reviewer 和 human gate。
- intent confirmation 让本轮目标、范围、验收标准和风险进入结构化记录。
- step report 的内容质量明显提升，能展示 owner、inputs、outputs、done criteria、next-entry criteria、blockers、human decisions required 和 recommended next action。
- `change prepare` 已显式提示 Step 6 前需要补齐 participants、intent、step report。
- 归档后 `.governance/current-state.md` 已能同步 idle 状态，修复 v0.2.6 的误导性状态问题。

## 3. 核心结论

v0.2.7 证明了“人的控制基线”方向正确，但当前实现仍主要是**可记录**，还没有成为**默认可见、默认受控、默认不可绕过**的协作体验。

从 Agent 侧看，命令链路已经完整；从人的协作治理体验看，4 阶段 / 9 步仍没有自然呈现为逐步执行、逐步确认、逐步汇报的流程。人需要主动打开文件或依赖 Agent 主动总结，才能感知 open-cowork 正在如何约束多 Agent 协作。

这意味着 v0.2.8 不应泛化扩展功能，而应把 v0.2.7 的控制基线从“生成产物”推进到“默认流程约束”。

## 4. 关键问题归档

### F-027-001：4 阶段 / 9 步没有形成默认逐步汇报

现象：本轮只在 Step 5-9 手动生成 step reports，Step 1-4 缺失；即使生成报告，也只是落在文件系统中，没有在执行过程中自动向人展示。

影响：4 阶段 / 9 步没有真正成为人的实时体验，仍像 Agent 内部命令链。

候选方向：`pilot` / `change prepare` / `run` / `verify` / `review` / `archive` 默认生成并输出当前 step report 摘要；进入下一步前展示上一环节 close criteria 和下一环节 entry criteria。

### F-027-002：自定义参与者不会自动映射到 9 步 owner matrix

现象：传入 `coding-agent`、`verification-agent`、`review-agent` 后，它们出现在 participants 列表中，但 Step 6/7/8 owner 仍是默认 `executor-agent`、`verifier-agent`、`independent-reviewer`。

影响：人和 Agent 容易误以为真实参与者已经被绑定到执行矩阵，实际仍在使用默认占位角色。

候选方向：支持 `--step-owner 6=coding-agent`、`--step-reviewer 8=review-agent` 等显式映射；如果自定义参与者未分配到任何 step，应在输出中 warning。

### F-027-003：`change prepare` 会覆盖先前写入的 participants bindings

现象：先执行 `participants setup --change-id ...`，再执行 `change prepare`，`bindings.yaml` 回到默认角色绑定。

影响：只要 Agent 执行顺序稍有偏差，就可能丢失人的角色配置。

候选方向：`change prepare` 应保留已有 `participants_profile_ref` 和 step matrix；若需要覆盖，必须显式提示并要求确认或 force。

### F-027-004：draft contract 阶段的 `step report` 会输出 Python traceback

现象：`change create` 后、`change prepare` 前执行 `step report`，因 contract 缺字段而输出完整 traceback。

影响：对人和普通 Agent 都不友好，也削弱“Agent-first 但人可理解”的体验。

候选方向：捕获 `ContractValidationError`，输出“请先运行 change prepare 或补齐 contract”的人类可读错误，并指向下一步建议。

### F-027-005：intent 与 contract scope 没有自动对齐或冲突提示

现象：`intent capture` 可记录一组 scope，`change prepare` / contract 可记录另一组 scope；二者不一致时没有提示。

影响：人确认的意图范围和实际执行契约可能分叉。

候选方向：`contract validate`、`change prepare` 或 `step report` 增加 intent scope 与 contract scope 差异检查。

### F-027-006：intent 未确认时 Step 6 readiness 仍可为 true

现象：`intent_confirmation.status=captured` 时，manifest 仍显示 `readiness.step6_entry_ready: true`。

影响：执行器可能在真实人类确认前进入 Step 6。

候选方向：未 confirmed 时 Step 6 readiness 至少 warning；严格模式下应 false。

### F-027-007：human gate 仍是展示型约束

现象：Step 5 报告显示 `human_gate=true` 且建议暂停，但 `ocw run` 仍可直接执行。

影响：Agent 可绕过人的确认，治理仍依赖 Agent 自律。

候选方向：增加 `ocw step approve` 或 `--ack-human-gate <actor>`，并让 `run` / `review` / `archive` 校验 gate approval record。

### F-027-008：review 命令未校验 reviewer 与 bindings 一致性

现象：Step 8 owner/reviewer 是默认 `independent-reviewer`，但 `ocw review --reviewer review-agent` 仍可 approve。

影响：审查者身份可能偏离 participants matrix，削弱 independent review 约束。

候选方向：不一致时 warning；严格模式下要求 reviewer 在 bindings 或 participants profile 中拥有 Step 8 权限。

### F-027-009：`adopt --dry-run` 尚未突出 v0.2.7 新流程

现象：adoption plan 仍主要输出 recommended read set，没有提示 participants、intent、step report 是 v0.2.7 人类控制基线。

影响：Agent 可能按旧流程从 adoption 直接走 prepare/run。

候选方向：在 adoption plan 中加入 `human_control_baseline_next_actions`。

### F-027-010：归档包内状态一致性快照生命周期语义偏早

现象：归档后 manifest/status 已 archived，但归档包内 `STATE_CONSISTENCY_CHECK.yaml` 仍记录运行阶段的 `step6-executed-pre-step7` 语义。

影响：审计时需要人工理解该文件是早前阶段快照。

候选方向：状态快照增加 `generated_at`、`lifecycle_at_generation`；archive 时生成最终一致性快照。

## 5. 人类体验视角

### H-027-001：流程更可见，但仍像黑盒

人能看到更多文件和矩阵，但在执行过程中没有自然看到“当前是 4 阶段 / 9 步中的哪一步、谁负责、在做什么、输入和产出是什么、完成标准是什么、下一步进入标准是什么”。

### H-027-002：自定义参与者体验会造成误解

人输入自己的 Agent 名称后，会期待这些 Agent 出现在 9 步 owner matrix 中。实际只是被添加到 participants 列表，会让人误判治理关系已经生效。

### H-027-003：确认仍可被 Agent 代填

`intent confirm --confirmed-by human-sponsor` 可以由 Agent 直接执行。对人来说，这不是强确认，只是一条记录。

### H-027-004：human gate 的心理预期与实际行为不一致

报告显示 Step 5 / Step 8 / Step 9 需要 human gate，但工具仍允许继续 run、review、archive。人的感受会是“看起来需要我批准，但系统没有真的等我”。

### H-027-005：人不知道在哪里配置每一步 owner 和职责

`participants setup` 当前更像“生成默认矩阵 + 添加参与者列表”，还不是“配置每一步 owner / assistants / reviewer / human gate”的向导或明确表格。

### H-027-006：人不知道每个 Agent 在本 step 的具体职责

矩阵有 owner 和 assistants，但缺少每个参与者在当前 step 的职责、交付物和边界说明。

候选方向：step report 增加 `participant_responsibilities` 小节，用人类语言说明 owner 做什么、assistant 做什么、reviewer 看什么、人需要判断什么。

## 6. 对 v0.2.8 的输入

建议将 v0.2.8 主题收敛为：

**Default-visible and enforceable human gates**

核心目标不是引入更大的团队协作系统，而是把 v0.2.7 的 human-control baseline 接入默认命令流：

1. 9 步报告默认生成、默认摘要输出。
2. 自定义参与者必须能显式映射到 step owner / reviewer / assistants。
3. human gate 必须有 approval record，并被 `run` / `review` / `archive` 消费。
4. intent 与 contract 必须能校验一致性。
5. draft / misordered command 必须给出人类可读错误和下一步建议。
6. archive 必须生成最终状态一致性快照。

v0.2.8 仍不建议优先做 Dashboard、TUI、云端协作或企业审批流。当前最重要的是让个人域多 Agent 协作从“文件可追踪”变成“执行时可感知、推进时受约束”。
