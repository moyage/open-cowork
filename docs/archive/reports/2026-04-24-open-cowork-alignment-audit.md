# open-cowork 对齐审计报告

日期：2026-04-24 19:41:01 HKT
仓库：`/Users/mlabs/Programs/open-cowork`
审计目的：在继续推进 open-cowork 前，对当前仓库状态、V0.2.6 active change 运行态包、round closeout 规范与现有归档文档进行对齐，明确“现在应该把什么当作 authoritative baseline”。

## 0. 审计范围与方法

本次仅做读取与审计，不做任何修改。

读取对象：
- `.governance/current-state.md`
- `.governance/changes/v0.2.6-agent-first-adoption-closure/*`
- `docs/specs/13-round-close-report-and-closeout-package-spec.md`
- `docs/archive/reports/05-current-iteration-round-close-report.md`
- `docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md`
- `docs/archive/reports/2026-04-24-v026-first-step-personal-agent-dogfood-v027-findings.md`
- `AGENTS.md`
- 当前 `git status`

## 1. 当前仓库状态快照

### 1.1 Git 工作区

当前仓库根目录：`/Users/mlabs/Programs/open-cowork`

未跟踪文件：
- `.governance/AGENTS.md`
- `.governance/agent-playbook.md`
- `.governance/current-state.md`
- `docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md`
- `docs/archive/plans/59-v0.2.7-first-step-personal-agent-dogfood-requirements.md`
- `docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md`
- `docs/archive/reports/2026-04-24-v025-agent-first-dogfood-findings.md`
- `docs/archive/reports/2026-04-24-v026-first-step-personal-agent-dogfood-v027-findings.md`

判断：
- 这些文件已经构成当前 V0.2.6 对齐与推进的重要上下文。
- 但它们仍是 untracked，因此还不能被当作“已进入 Git authoritative history 的已提交基线”。
- 继续推进前，应明确：这些文件目前只是“本地事实层输入 + 运行态准备材料”。

### 1.2 current-state

`.governance/current-state.md` 当前内容显示：
- Active change: `v0.2.6-agent-first-adoption-closure`
- Current phase: `Phase 2 / 方案与准备`
- Current step: `Step 5 / Approve the start`
- Next recommended action: executor 读取 contract 后在 scope_in 内执行

判断：
- 当前仓库已明确把 V0.2.6 视为尚未开工执行的 active change。
- 这意味着：此前反复卡住的 round 5 closeout package 补全，不应再被视为当前阻塞点。
- 当前阻塞点已经切换为：是否批准 V0.2.6 `Step 6` 开始执行。

## 2. V0.2.6 active change 运行态包对齐

运行态目录：
`/Users/mlabs/Programs/open-cowork/.governance/changes/v0.2.6-agent-first-adoption-closure`

已存在文件：
- `intent.md`
- `requirements.md`
- `design.md`
- `tasks.md`
- `contract.yaml`
- `bindings.yaml`
- `manifest.yaml`
- `verify.yaml`
- `review.yaml`
- `STATUS_SNAPSHOT.yaml`

### 2.1 contract.yaml

关键事实：
- `change_id`: `v0.2.6-agent-first-adoption-closure`
- 目标：修复 Agent-first adoption 闭环、状态一致性、contract/runtime 边界、onboard 输出、source doc 绑定、个人域 role binding 与仓库卫生问题
- `scope_in` 包含：`src/**`、`tests/**`、`scripts/**`、`docs/**`、`README.md`、`AGENTS.md`、`.gitignore`、`pyproject.toml`、`CHANGELOG.md`
- `scope_out` 包含：`.governance/index/**`、`.governance/archive/**`、`.governance/runtime/**`
- 禁止项包含：
  - `modify_external_agent_config`
  - `expand_scope_without_review`
  - `no_executor_reviewer_merge`
- 验证命令：`python3 -m unittest discover -s tests`
- 验收要求明确要求复跑第一条指令 dogfood 场景

判断：
- 运行态 contract 已经具备执行门槛，不是空包。
- scope 明确禁止污染 `.governance/index/**`、`.governance/archive/**`、`.governance/runtime/**`。
- 因此后续任何实现推进，都应以 V0.2.6 contract 为唯一边界，而不是再回去修旧 round closeout 包。

### 2.2 manifest.yaml

关键事实：
- `status: step5-prepared`
- `current_step: 5`
- `readiness.step6_entry_ready: true`
- source docs 已绑定：
  - `58-v0.2.6-agent-first-dogfood-requirements.md`
  - `2026-04-24-v025-agent-first-dogfood-findings.md`
  - `2026-04-24-v026-first-step-personal-agent-dogfood-v027-findings.md`
  - `59-v0.2.7-first-step-personal-agent-dogfood-requirements.md`

判断：
- 运行态变更包已经正式把 59 并入 V0.2.6 语境，不再视为未来版本独立推进项。
- 这和 `docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md` 的维护者判定一致。

### 2.3 design.md / tasks.md / bindings.yaml

关键事实：
- `design.md` 已把实现分为三段：
  1. consistency foundation
  2. adoption closure
  3. team-member usability
- `tasks.md` 已拆出测试、实现、验收、review、archive 的待办
- `bindings.yaml` 已把个人域 agent inventory 映射为 orchestrator / executor / verifier / reviewer / maintainer 候选

判断：
- V0.2.6 的“下一步推进对象”已经成型。
- 当前并不缺 Step 5 运行态包本身；缺的是人类是否批准 Step 6 执行。

### 2.4 verify.yaml / review.yaml

现状：
- `verify.yaml` 当前仅为 `{}`
- `review.yaml` 未在本次审计中展开，但文件已存在

判断：
- 这符合 Step 5 prepared 状态：verify/review 结果尚未产生。
- 不应把“结果文件未填充”误判为“运行态包未补全”。

## 3. round closeout 规范与当前推进关系

### 3.1 closeout 规范本身

`docs/specs/13-round-close-report-and-closeout-package-spec.md` 明确规定：
- closeout package 只适用于已完成 Step 9 archive 的 round
- 标准 closeout package 固定输出 5 份文档
- 它的用途是 close 后归档、回顾、下一轮输入
- 它不是未 archive 轮次的执行合同替代物

### 3.2 与当前 V0.2.6 的关系

当前 `.governance/current-state.md` 与运行态包都表明：
- V0.2.6 还处于 `Step 5 / Approve the start`
- 尚未进入 Step 6 execution
- 更未到 Step 9 archive

因此判断：
- round closeout package 在当前时点不是主线执行对象。
- 即使历史上曾反复卡在 round 5 closeout package 补全，也不应再把它当成当前推进 gating item。
- 现在应把 closeout package 视为“历史轮次归档材料/规范参考”，而不是“当前 V0.2.6 必须先补完才能动”的阻塞项。

## 4. 历史 round close report 的定位

`docs/archive/reports/05-current-iteration-round-close-report.md` 显示：
- 这是围绕更早的 `Milestone 1 + Milestone 2` 的收口报告
- 它总结的是早前主链：change create -> contract validate -> run -> verify -> review -> archive
- 它在复盘中也承认：旧式 closeout 文档包与新式 continuity/sync/digest 之间存在认知并存

判断：
- 该文档应被视为“历史闭环报告”。
- 它提供背景与演化脉络，但不应覆盖当前 V0.2.6 active change contract。
- 当前推进必须以 V0.2.6 运行态包和 current-state 为准，而不是以历史 close report 为准。

## 5. V0.2.6 authoritative baseline 判定

综合 current-state、contract、manifest、change-package 基线文档后，可得当前 authoritative baseline：

### 5.1 当前主推进对象

当前主推进对象是：
- Active change: `v0.2.6-agent-first-adoption-closure`

不是：
- round 5 closeout package 补全
- 历史 Milestone 1/2 closeout 文档收口
- 新开一个 V0.2.7 change

### 5.2 当前 authoritative 输入层

应优先读取：
1. `.governance/current-state.md`
2. `.governance/changes/v0.2.6-agent-first-adoption-closure/contract.yaml`
3. `.governance/changes/v0.2.6-agent-first-adoption-closure/manifest.yaml`
4. `.governance/changes/v0.2.6-agent-first-adoption-closure/design.md`
5. `.governance/changes/v0.2.6-agent-first-adoption-closure/tasks.md`
6. `docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md`
7. 58 / v025 findings / v026 findings / 59 这些 source docs

### 5.3 当前非主线但可参考输入

以下对象只应作为背景参考，不应覆盖当前 contract：
- `docs/specs/13-round-close-report-and-closeout-package-spec.md`
- `docs/archive/reports/05-current-iteration-round-close-report.md`
- 更早的 round closeout / milestone closeout 文档

## 6. 对齐结论

结论 1：之前反复卡住的 “round 5 closeout package 补全” 已不应视为当前执行主线。

结论 2：本地另一个 agent 完成该项后，当前仓库事实上已经把推进重心切换到 `v0.2.6-agent-first-adoption-closure`。

结论 3：当前 Step 5 运行态包已经齐备，缺的不是包，而是 Step 6 开始执行的批准。

结论 4：如果后续继续推进 open-cowork，应以 V0.2.6 contract 作为唯一执行边界，禁止再次漂回历史 closeout package 补全文档循环。

## 7. 建议的后续动作（仅建议，不执行）

### 方案 A：做“对齐确认”后进入预执行声明
适用：如果你要我重新作为 PM/orchestrator 接手推进。

动作：
- 先由我输出一份简洁的 Pre-Execution Declaration
- 明确：目标、范围、风险、边界、 reviewer separation、不会修改外部 agent config
- 等你明确批准后，再 dispatch L3 executor/verifier/reviewer 流程

### 方案 B：先做 current-state / dispatch 对齐复核
适用：如果你担心仓库还有 state drift。

动作：
- 仅读取 `.governance/index/**`、`dispatch`、`iteration-state`、相关 status 投影
- 做一次“现在事实是否完全一致”的审计
- 不做实现

### 方案 C：仅确认接管口径
适用：你现在只想完成职责切换。

动作：
- 由你确认“以后 open-cowork 当前主线以 V0.2.6 为准”
- 我后续只围绕该 active change 工作

## 8. 审计产物路径

本报告已写入：
`/Users/mlabs/Programs/open-cowork/docs/archive/reports/2026-04-24-open-cowork-alignment-audit.md`
